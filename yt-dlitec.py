import argparse
import sys
import subprocess
import yt_dlp
import os
import re

def sanitize_filename(filename):
    #Sanitize filename to remove or replace problematic characters
    #like emojis,symbols, unicode  and keep alphanumeric characters, spaces, dots, hyphens, and underscores
    # This is to enable deleting after combining files, when processing downloading, similar to when passing -k in yt-dlp, stuff like that.
    
    sanitized = re.sub(r'[^\w\-_\. ]', '_', filename)
    
    # Limit filename length
    max_length = 255
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Ensure filename is not empty
    if not sanitized.strip():
        sanitized = 'downloaded_media'
    
    return sanitized

def parse_yt_dlp_args(args):
    """Parse command line arguments into yt-dlp options dictionary"""
    ydl_opts = {}
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        # Handle arguments in the format --option=value
        if '=' in arg and arg.startswith('--'):
            key, value = arg.split('=', 1)
            key = key[2:]  # Remove leading --
            if key == 'no-playlist':
                ydl_opts['noplaylist'] = True
            elif key.startswith('no-'):
                ydl_opts[key[3:]] = False
            else:
                ydl_opts[key] = value
        
        # Handle arguments in the format --option value
        elif arg.startswith('--') and i + 1 < len(args) and not args[i+1].startswith('--'):
            key = arg[2:]  # Remove leading --
            value = args[i+1]
            if key == 'no-playlist':
                ydl_opts['noplaylist'] = True
            elif key.startswith('no-'):
                ydl_opts[key[3:]] = False
            else:
                ydl_opts[key] = value
            i += 1  # Skip next arg as it's the value
        
        # Handle flags like --no-playlist
        elif arg.startswith('--'):
            key = arg[2:]  # Remove leading --
            if key == 'no-playlist':
                ydl_opts['noplaylist'] = True
            elif key.startswith('no-'):
                ydl_opts[key[3:]] = False
            else:
                ydl_opts[key] = True
        
        # Handle short flags like -x
        elif arg.startswith('-') and len(arg) == 2:
            # Map common short options to their long form
            short_opts_map = {
                'f': 'format',
                'o': 'output',
                'x': 'extract-audio',
                'i': 'ignore-errors',
                'v': 'verbose',
                'q': 'quiet'
            }
            if arg[1] in short_opts_map:
                key = short_opts_map[arg[1]]
                if arg[1] in ['x', 'i', 'v', 'q']:  # Flags without values
                    ydl_opts[key] = True
                elif i + 1 < len(args) and not args[i+1].startswith('-'):
                    ydl_opts[key] = args[i+1]
                    i += 1  # Skip next arg as it's the value
        
        i += 1
    
    return ydl_opts

def download_media(video_url=None, audio_url=None, video_format='mp4', audio_format='mp3', output_path=None, resume=False, extra_args=None):
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
    
    # Add any extra options from command line arguments
    if extra_args:
        extra_opts = parse_yt_dlp_args(extra_args)
        ydl_opts.update(extra_opts)

    # Handle video download
    if video_url:
        # Customize video format selection (don't override if format already specified in extra_args)
        if 'format' not in ydl_opts:
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

def list_formats(url, extra_args=None):
    """List available formats for a given URL"""
    try:
        options = {'quiet': True}
        
        # Add any extra options from command line arguments
        if extra_args:
            extra_opts = parse_yt_dlp_args(extra_args)
            options.update(extra_opts)
            
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

def direct_yt_dlp_download(urls, extra_args=None):
    """Use yt-dlp library with user arguments directly"""
    print("Using direct yt-dlp library download...")
    
    # Parse command-line arguments to yt-dlp options
    ydl_opts = {}
    if extra_args:
        ydl_opts = parse_yt_dlp_args(extra_args)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(urls)
        return True
    except Exception as e:
        print(f"Error using yt-dlp library: {e}")
        return False

def main():
    # First, check for --gui flag directly in sys.argv before any argument parsing
    if '--gui' in sys.argv:
        print("Launching GUI mode...")
        gui_launched = False
        
        # First try Python script
        try:
            result = subprocess.run(["python", "yt-dlite.py"], check=True)
            if result.returncode == 0:
                print("GUI launched successfully")
                gui_launched = True
        except Exception as e:
            print("Failed to launch Python GUI script, Trying yt-dlite.exe")
            
        # Try executable only if Python script failed
        if not gui_launched:
            try:
                result = subprocess.run(["yt-dlite.exe"], check=True)
                #result = subprocess.run(["./yt-dlite"], check=True) - uncheck this if you want to compile for linux
                if result.returncode == 0:
                    print("GUI executable launched successfully")
                    gui_launched = True
            except Exception as e2:
                # Only show error if both methods failed
                if not gui_launched:
                    print("ERROR: Could not launch GUI")
                    print("Please ensure that either yt-dlite.py or yt-dlite.exe exists in the same directory")
        
        sys.exit(0)
    
    # Create parser to handle the special cases
    parser = argparse.ArgumentParser(
        description="""
        -----------------------------------------------------------------------------
        Video & Audio Downloader using yt-dlp
        Developed by Winner_Nova.
        -----------------------------------------------------------------------------
        """,
        epilog=(
            "Examples:\n"
            "  python yt-dlitec.py --video <URL>             # Download video (default: mp4)\n"
            "  python yt-dlitec.py --audio <URL>             # Download audio (default: mp3)\n"
            "  python yt-dlitec.py --video <URL> --format webm   # Download video in WebM format\n"
            "  python yt-dlitec.py --list-formats <URL>      # List available formats\n"
            "  python yt-dlitec.py --resume --video <URL>    # Resume interrupted video download\n"
            "  python yt-dlitec.py --no-playlist --video <URL> # Skip playlist, download single video\n"
            "  python yt-dlitec.py --gui                     # Launch GUI mode (ignores all other arguments)\n"
            "  python yt-dlitec.py <URL>                     # Pass directly to yt-dlp\n\n"
            "Notes:\n"
            "  '--gui' should be run alone, as script(.py or exe) --gui.\n"
            "  '--list-formats' requires a valid URL.\n"
            "  '--resume' will attempt to continue partially downloaded files.\n"
            "  Supported formats include: mp4, webm, mp3, m4a, and more.\n"
            "  Any yt-dlp options like --no-playlist and other similar are supported and passed through."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False  # Don't exit on help flag to catch it ourselves
    )

    # Add arguments without making them required
    parser.add_argument('--video', help='YouTube video URL to download')
    parser.add_argument('--audio', help='YouTube audio URL to download')
    parser.add_argument('--format', help='Specify format for video or audio (e.g., mp4, webm, mp3)')
    parser.add_argument('--output', help='Specify custom output directory')
    parser.add_argument('--list-formats', help='List available formats for the given YouTube URL')
    parser.add_argument('--gui', action='store_true', help='Launch yt-dlite.exe or some.exe which are GUI mode')
    parser.add_argument('--resume', action='store_true', help='Resume partially downloaded files')
    parser.add_argument('--help', action='store_true', help='Show this help message')
    parser.add_argument('urls', nargs='*', help='URLs to download')

    # Parse known arguments
    args, unknown = parser.parse_known_args()

    # Show help if requested
    if args.help and not unknown:
        parser.print_help()
        sys.exit(0)
        
    # Handle --list-formats
    if args.list_formats:
        list_formats(args.list_formats, unknown)
        sys.exit(0)

    # Collect all arguments for passing to yt-dlp options
    all_args = sys.argv[1:]
    
    # Handle special cases with --video or --audio flags
    if args.video or args.audio:
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
            resume=args.resume,
            extra_args=all_args  # Pass all arguments to apply global options
        )
    # If URLs are provided directly or with unknown args, use yt-dlp library directly
    elif args.urls or unknown:
        # Collect all URLs
        urls = args.urls
        
        # Check if there are any URLs in the unknown args
        # (simple URL detection - just looking for strings not starting with '-')
        url_args = [arg for arg in unknown if not arg.startswith('-')]
        urls.extend(url_args)
        
        if urls:
            direct_yt_dlp_download(urls, all_args)
        else:
            print("No URLs provided. Pass a URL to download or use --help to see available options.")
            sys.exit(1)
    else:
        # No recognized arguments
        print("No URLs or recognized arguments provided. Pass a URL or use --help to see available options.")
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
