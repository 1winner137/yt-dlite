import argparse
import sys
import subprocess
import yt_dlp
import os
import re

def sanitize_filename(filename):
    #Sanitize filename to remove or replace problematic characters
    #like emojis,symbols, unicode  and keep alphanumeric characters, spaces, dots, hyphens, and underscores
    # This is to enable deleting after combining files, when processing downloading, similar to when passing -k in yt-dlp, stuff like that
    
    sanitized = re.sub(r'[^\w\-_\. ]', '_', filename)
    
    # Limit filename length
    max_length = 255
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Ensure filename is not empty
    if not sanitized.strip():
        sanitized = 'downloaded_media'
    
    return sanitized

def download_media(video_url=None, audio_url=None, video_format='mp4', audio_format='mp3', output_path=None, resume=False):
    #It download video similar to yt-dlp but keep it super duper simple
    # Default yt-dlp options
    ydl_opts = {
        'quiet': False,
        'no_warnings': False,
        # Use custom filename sanitization
        'outtmpl': {
            'default': '%(title)s.%(ext)s',
        },
        # Add filename sanitization
        'restrictfilenames': True,  # Replace unsafe characters
    }

    # Enable resume functionality if requested
    if resume:
        ydl_opts['continuedl'] = True
        print("Resume mode enabled - will try to continue partial downloads")

    # Set output path
    if output_path:
        ydl_opts['outtmpl'] = {
            'default': os.path.join(output_path, '%(title)s.%(ext)s')
        }

    # Handle video download
    if video_url:
        # Customize video format selection
        if video_format == 'mp4':
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'
        elif video_format == 'webm':
            ydl_opts['format'] = 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]'
        else:
            ydl_opts['format'] = 'best'

        # Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                if resume:
                    print(f"Attempting to resume video download in {video_format} format...")
                else:
                    print(f"Downloading video in {video_format} format...")
                ydl.download([video_url])
                print(f"Video downloaded to {'current directory' if not output_path else output_path}")
            except Exception as e:
                print(f"Error downloading video: {e}")

    # Handle audio download
    if audio_url:
        # Reset ydl_opts for audio
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': '192',
            }]
        })

        # Keep resume setting
        if resume:
            ydl_opts['continuedl'] = True

        # Set output path for audio
        if output_path:
            ydl_opts['outtmpl'] = {
                'default': os.path.join(output_path, '%(title)s.%(ext)s')
            }

        # Download audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                if resume:
                    print(f"Attempting to resume audio download in {audio_format} format...")
                else:
                    print(f"Downloading audio in {audio_format} format...")
                ydl.download([audio_url])
                print(f"Audio downloaded to {'current directory' if not output_path else output_path}")
            except Exception as e:
                print(f"Error downloading audio: {e}")

def list_formats(url):
    """List available formats for a given URL"""
    try:
        options = {'quiet': True}
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            print("Available formats:")
            for fmt in formats:
                print(f"ID: {fmt['format_id']} | Ext: {fmt['ext']} | Resolution: {fmt.get('resolution', 'N/A')} | Note: {fmt.get('format_note', '')}")
            return info
    except Exception as e:
        print(f"Error listing formats: {e}")
        sys.exit(1)

def main():
    # First, check for --gui flag directly in sys.argv before any argument parsing
    # This ensures --gui takes priority over all other arguments including --help
    if '--gui' in sys.argv:
        print("Launching GUI mode...")
        try:
            subprocess.run(["python", "yt-liteg.py"])
        except Exception as e:
            print(f"Error launching GUI: {e}")
        sys.exit(0)
    
    # Normal argument parsing for other cases
    parser = argparse.ArgumentParser(
        description="""
        -----------------------------------------------------------------------------
        YouTube Video & Audio Downloader using yt-dlp
        Developed by Winner_Nova.
        -----------------------------------------------------------------------------
        """,
        epilog=(
            "Examples:\n"
            "  python script.py --video <URL>             # Download video (default: mp4)\n"
            "  python script.py --audio <URL>             # Download audio (default: mp3)\n"
            "  python script.py --video <URL> --format webm   # Download video in WebM format\n"
            "  python script.py --list-formats <URL>      # List available formats\n"
            "  python script.py --resume --video <URL>    # Resume interrupted video download\n"
            "  python script.py --gui                     # Launch GUI mode (ignores all other arguments)\n\n"
            "Notes:\n"
            "  '--gui' should be run alone, as script(.py or exe) --gui.\n"
            "  '--list-formats' requires a valid URL.\n"
            "  '--resume' will attempt to continue partially downloaded files.\n"
            "  Supported formats include: mp4, webm, mp3, m4a, and more."
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('--video', help='YouTube video URL to download')
    parser.add_argument('--audio', help='YouTube audio URL to download')
    parser.add_argument('--format', help='Specify format for video or audio (e.g., mp4, webm, mp3)')
    parser.add_argument('--output', help='Specify custom output directory')
    parser.add_argument('--list-formats', help='List available formats for the given YouTube URL')
    parser.add_argument('--gui', action='store_true', help='Launch yt-liteg.py or some.exe which are GUI mode')
    parser.add_argument('--resume', action='store_true', help='Resume partially downloaded files')

    args, _ = parser.parse_known_args()

    # Handle --list-formats
    if args.list_formats:
        list_formats(args.list_formats)
        sys.exit(0)

    # Ensure at least one of --video or --audio is provided
    if not (args.video or args.audio):
        parser.error("At least one of --video or --audio must be provided")

    # Determine format based on context
    video_format = 'mp4'
    audio_format = 'mp3'

    # Override formats if specified
    if args.format:
        if args.video:
            video_format = args.format
        elif args.audio:
            audio_format = args.format

    # Call download function with parsed arguments
    download_media(
        video_url=args.video,
        audio_url=args.audio,
        video_format=video_format,
        audio_format=audio_format,
        output_path=args.output,
        resume=args.resume
    )

if __name__ == '__main__':
    main()
