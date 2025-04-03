import tkinter as tk
from tkinter import ttk, messagebox
import yt_dlp
import threading
import time
import os

# Function to determine if URL is a playlist and process
def is_playlist(url):
    return '&list=' in url or '?list=' in url or '/playlist?' in url

def process_playlist_url(root, url, log_func=None):
    handler = PlaylistHandler(root, url, log_func)
    handler.fetch_playlist_info()
    if handler.playlist_info:
        handler.show_format_selection_dialog()
        return handler if handler.selected_format else None
    return None

# Class to handle playlist operations
class PlaylistHandler:
    def __init__(self, root, url, parent=None, log_func=None):
        self.root = root
        self.url = url
        self.log = log_func if log_func else lambda msg, level: None
        self.playlist_info = None
        self.videos = []
        self.selected_format = None
        self.selected_format_type = None  # 'audio' or 'video'
        self.format_dialog = None
        self.fetch_cancelled = False
        self.size_calculation_thread = None
        self.parent = parent
     #setting output directory   
    def get_output_path(self):
        if self.parent and hasattr(self.parent, 'save_path_entry'):
            output_path = self.parent.save_path_entry.get()
            if output_path:
                return output_path
                
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        output_path = os.path.join(downloads_path, "yt-dlite")
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            
        return output_path
        
    # Fetch playlist information
    def fetch_playlist_info(self):
        # Set up yt-dlp options for playlist info extraction
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,  # Prevent download video info for each video
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.playlist_info = ydl.extract_info(self.url, download=False)

                if self.playlist_info and 'entries' in self.playlist_info:
                    self.videos = self.playlist_info['entries']
                    self.log(f"Found {len(self.videos)} videos in playlist", "INFO")
                    return True
                else:
                    self.log("No playlist information found", "ERROR")
                    return False
        except Exception as e:
            self.log(f"Error fetching playlist info: {str(e)}", "ERROR")
            messagebox.showerror("Network Error", "Connection failed. Try again.")
            return False
        
        # Show dialog for format selection and create pop up, u can modify to make it more appealing
    def show_format_selection_dialog(self):
        self.format_dialog = tk.Toplevel(self.root)
        self.format_dialog.title("Playlist Download Options")
        self.format_dialog.geometry("500x450")
        self.format_dialog.resizable(False, False)
        self.format_dialog.transient(self.root)
        self.format_dialog.grab_set()
        
        main_frame = ttk.Frame(self.format_dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Playlist info
        playlist_title = self.playlist_info.get('title', 'Unknown Playlist')
        ttk.Label(main_frame, text=f"Playlist: {playlist_title}", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        ttk.Label(main_frame, text=f"Videos: {len(self.videos)}").pack(anchor=tk.W, pady=(0, 10))
        
        # Video limit selection
        ttk.Label(main_frame, text="Number of videos to download:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        # Create frame for limit controls
        limit_frame = ttk.Frame(main_frame)
        limit_frame.pack(fill=tk.X, pady=(0, 10), anchor=tk.W)
        
        # Radio buttons for all videos selections
        self.limit_type_var = tk.StringVar(value="all")
        ttk.Radiobutton(limit_frame, text="All videos", variable=self.limit_type_var, 
                    value="all", command=self.toggle_limit_entry).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(limit_frame, text="First", variable=self.limit_type_var,
                    value="limited", command=self.toggle_limit_entry).pack(side=tk.LEFT, padx=(0, 5))
        
        self.limit_var = tk.StringVar(value="10")
        self.limit_spinbox = ttk.Spinbox(limit_frame, from_=1, to=min(100, len(self.videos)), 
                                        width=5, textvariable=self.limit_var, state="disabled")
        self.limit_spinbox.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(limit_frame, text="videos").pack(side=tk.LEFT)

        ttk.Label(main_frame, text="Select Download Type:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        # Radio buttons for format type - Set default to audio u can change if u wish
        self.format_type_var = tk.StringVar(value="audio")
        ttk.Radiobutton(main_frame, text="Video", variable=self.format_type_var, value="video", command=self.on_format_type_selected).pack(anchor=tk.W, padx=20)
        ttk.Radiobutton(main_frame, text="Audio Only", variable=self.format_type_var, value="audio", command=self.on_format_type_selected).pack(anchor=tk.W, padx=20, pady=(0, 10))        
        ttk.Label(main_frame, text="Select Format:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        # Format dropdown
        self.format_var = tk.StringVar()
        self.format_dropdown = ttk.Combobox(main_frame, textvariable=self.format_var, state="readonly", width=40)
        self.format_dropdown.pack(anchor=tk.W, pady=(0, 20))        
        # Initialize format dropdown values & size estimation
        self.on_format_type_selected()        
        self.size_label = ttk.Label(main_frame, text="Estimated Size: Calculating...")
        self.size_label.pack(anchor=tk.W, pady=(10, 20))        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        #Download and cancel button
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel_button).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Download Now", command=self.on_download_button).pack(side=tk.RIGHT, padx=5)        
        # Start size calculation in a controlled way, to keeep simple
        self.size_calculation_thread = threading.Thread(target=self.calculate_playlist_size, daemon=True)
        self.size_calculation_thread.start()        
        self.format_dialog.protocol("WM_DELETE_WINDOW", self.on_cancel_button)        
        # Wait for user input, even if he\she wish to do tommorow! Hah funny
        self.root.wait_window(self.format_dialog)
        return self.selected_format is not None

    def toggle_limit_entry(self):
        if self.limit_type_var.get() == "limited":
            self.limit_spinbox.config(state="normal")
        else:
            self.limit_spinbox.config(state="disabled")        
    # Handle format type selection (audio/video)
    def on_format_type_selected(self):
        format_type = self.format_type_var.get()
        
        # Update available formats based on type selection
        if format_type == "video":
            formats = [
                "mp4 (1080p)", 
                "mp4 (720p)", 
                "mp4 (480p)",
                "mp4 (360p)",
                "mp4 (240p)",
                "webm (1080p)",
                "webm (720p)", 
                "webm (480p)",
                "webm (360p)",
                "webm (240p)",
                "mkv (Best Quality)",
                "mp4 (Best Quality)",
                "mp4 (Smallest Size)"
            ]
            format_values = [
                "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best",
                "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best",
                "bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[ext=mp4][height<=480]/best",
                "bestvideo[ext=mp4][height<=360]+bestaudio[ext=m4a]/best[ext=mp4][height<=360]/best",
                "bestvideo[ext=mp4][height<=240]+bestaudio[ext=m4a]/best[ext=mp4][height<=240]/best",
                "bestvideo[ext=webm][height<=1080]+bestaudio[ext=webm]/best[ext=webm][height<=1080]/best",
                "bestvideo[ext=webm][height<=720]+bestaudio[ext=webm]/best[ext=webm][height<=720]/best",
                "bestvideo[ext=webm][height<=480]+bestaudio[ext=webm]/best[ext=webm][height<=480]/best",
                "bestvideo[ext=webm][height<=360]+bestaudio[ext=webm]/best[ext=webm][height<=360]/best",
                "bestvideo[ext=webm][height<=240]+bestaudio[ext=webm]/best[ext=webm][height<=240]/best",
                "bestvideo+bestaudio/best",  # MKV container by default for separate video/audio
                "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/mp4",  # Best quality MP4
                "worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst"  # Smallest file size
            ]
        else:  # audio
            formats = [
                "MP3 (320kbps)",
                "MP3 (192kbps)", 
                "MP3 (128kbps)",
                "M4A (High Quality)", 
                "M4A (Medium Quality)",
                "OGG (High Quality)",
                "OPUS (Best Quality)",
                "FLAC (Lossless)",
                "WAV (Uncompressed)"
            ]
            format_values = [
                "-f ba[ext=m4a]/ba/best --extract-audio --audio-format mp3 --audio-quality 320K --prefer-ffmpeg --embed-thumbnail --add-metadata",
                "-f ba[ext=m4a]/ba/best --extract-audio --audio-format mp3 --audio-quality 192K --prefer-ffmpeg --embed-thumbnail --add-metadata",
                "-f ba[ext=m4a]/ba/best --extract-audio --audio-format mp3 --audio-quality 128K --prefer-ffmpeg --embed-thumbnail --add-metadata",
                "-f ba[ext=m4a]/ba/best --extract-audio --audio-format m4a --audio-quality 0 --embed-thumbnail --add-metadata",
                "-f ba[ext=m4a]/ba/best --extract-audio --audio-format m4a --audio-quality 2 --embed-thumbnail --add-metadata",
                "-f ba[ext=vorbis]/ba/best --extract-audio --audio-format vorbis --audio-quality 0 --embed-thumbnail --add-metadata",
                "-f ba/ba/best --extract-audio --audio-format opus --audio-quality 0 --embed-thumbnail --add-metadata",
                "-f ba/ba/best --extract-audio --audio-format flac --embed-thumbnail --add-metadata",
                "-f ba/ba/best --extract-audio --audio-format wav --embed-thumbnail --add-metadata"
            ]
        
        # Update dropdown options
        self.format_dropdown['values'] = formats
        self.format_dropdown.current(0)
        
        # Store format values for mapping
        self.format_values = dict(zip(formats, format_values))
        
        # Update size estimation if the dialog is still open
        if hasattr(self, 'size_label') and self.size_label.winfo_exists():
            # Cancel previous thread incase it stil running
            if self.size_calculation_thread and self.size_calculation_thread.is_alive():
                self.fetch_cancelled = True
                self.size_calculation_thread.join(0.1)  # Give it a moment to finish
            
            # Reset flag and start new calculation
            self.fetch_cancelled = False
            self.size_calculation_thread = threading.Thread(target=self.calculate_playlist_size, daemon=True)
            self.size_calculation_thread.start()
        
    # Handle Cancel button click
    def on_cancel_button(self):
        self.selected_format = None
        self.selected_format_type = None
        self.fetch_cancelled = True  # Stop any ongoing calculations        
        self.format_dialog.destroy() # Close dialog

    # Handle Download button click
    def on_download_button(self):
        # Storing selected options
        format_display = self.format_var.get()
        self.selected_format = self.format_values.get(format_display)
        self.selected_format_type = self.format_type_var.get()        
        # Get video limit selection
        if self.limit_type_var.get() == "limited":
            try:
                self.video_limit = int(self.limit_var.get())
            except ValueError:
                self.video_limit = len(self.videos)  # Default to all videos if invalid input
        else:
            self.video_limit = len(self.videos)  # All videos
        
        self.fetch_cancelled = True  # Stop any ongoing calculations
        self.format_dialog.destroy() # Close dialog
        self.start_download() # Start download immediately
############################This is start of block which deals with showing progress of each downloaded individual playlist
    #So if you see it bothering edit from this point.
    def show_progress_dialog(self, total_videos):
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Download Progress")
        self.progress_window.geometry("400x150")
        
        # Create frame for progress info
        frame = ttk.Frame(self.progress_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Video info label (current video title)
        self.video_label = ttk.Label(frame, text="")
        self.video_label.pack(fill=tk.X)
        
        # Status label for percentage
        self.status_label = ttk.Label(frame, text="Preparing download...")
        self.status_label.pack(fill=tk.X)
        
        # Current file progress bar
        self.current_progress_bar = ttk.Progressbar(frame, orient="horizontal", length=380, mode="determinate")
        self.current_progress_bar.pack(fill=tk.X, pady=5)
        
        # Overall progress label
        self.overall_label = ttk.Label(frame, text=f"Overall progress: 0/{total_videos}")
        self.overall_label.pack(fill=tk.X)
        
        # Overall progress bar
        self.overall_progress_bar = ttk.Progressbar(frame, orient="horizontal", length=380, mode="determinate")
        self.overall_progress_bar.pack(fill=tk.X, pady=5)
        
        # Cancel button
        cancel_btn = ttk.Button(frame, text="Cancel", command=self.cancel_download)
        cancel_btn.pack()
        
        # Set up progress tracking variables
        self.total_videos = total_videos
        self.completed_videos = 0
        self.download_cancelled = False

    def update_download_progress(self, d):
        # Skip update if download was cancelled
        if hasattr(self, 'download_cancelled') and self.download_cancelled:
            return
        
        # Check if progress window still exists
        if not hasattr(self, 'progress_window') or not self.progress_window.winfo_exists():
            return
        
        try:
            # Get status from yt-dlp dictionary by hookig
            status = d.get('status')
            
            if status == 'downloading':
                # Update video info
                filename = d.get('filename', '').split('/')[-1] if d.get('filename') else 'Unknown'
                self.video_label['text'] = f"Downloading: {filename}"
                
                # Update percentage
                if d.get('downloaded_bytes') is not None and d.get('total_bytes') is not None:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                    speed = d.get('speed', 0)
                    speed_str = f"{speed/1024/1024:.2f} MB/s" if speed else "Unknown speed"
                    eta = d.get('eta', 0)
                    eta_str = f"{eta} sec" if eta else "Unknown"
                    
                    self.status_label['text'] = f"{percent:.1f}% | {speed_str} | ETA: {eta_str}"
                    self.current_progress_bar['value'] = percent
                elif d.get('downloaded_bytes') is not None and d.get('total_bytes_estimate') is not None:
                    percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                    self.status_label['text'] = f"{percent:.1f}% (estimated)"
                    self.current_progress_bar['value'] = percent
            
            elif status == 'finished':
                # Update for completed video
                self.completed_videos += 1
                overall_progress = (self.completed_videos / self.total_videos) * 100
                self.overall_label['text'] = f"Overall progress: {self.completed_videos}/{self.total_videos}"
                self.overall_progress_bar['value'] = overall_progress
                self.current_progress_bar['value'] = 100
                self.status_label['text'] = "Completed current file"
            
            # Force UI update and handling error quitely to avoid breaking operations
            self.progress_window.update()
        except Exception as e:
            self.log(f"Error updating progress: {str(e)}", "ERROR")

    def cancel_download(self):
        self.download_cancelled = True
        if hasattr(self.root, 'cancel_download'):
            self.root.cancel_download()
        self.progress_window.destroy()

    # Download and update progress using hook
    def start_download(self):
        output_path = self.get_output_path()        
        # If empty for some reason, set to default application folder
        if not output_path:
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            output_path = os.path.join(downloads_path, "yt-dlite")
            if not os.path.exists(output_path): #Create directory if does not exist
                os.makedirs(output_path)
        
        # Get download items with applied limit
        items = self.get_download_items_with_limit()
        if items:
            try:
                # Show progress dialog
                self.show_progress_dialog(len(items))
                
                # Start download in a thread to keep UI responsive
                download_thread = threading.Thread(
                    target=self._download_thread,
                    args=(items, output_path)
                )
                download_thread.daemon = True
                download_thread.start()
                
                self.log(f"Started downloading {len(items)} videos from playlist", "INFO")
            except Exception as e:
                self.log(f"Error starting download: {str(e)}", "ERROR")
                messagebox.showerror("Error", f"Failed to start download: {str(e)}")

    def _download_thread(self, items, output_path):
        for i, item in enumerate(items):
            if hasattr(self, 'download_cancelled') and self.download_cancelled:
                break
                
            self.log(f"Downloading ({i+1}/{len(items)}): {item['title']}", "INFO")
            
            try:
                # Get format from the item
                format_string = item.get('format', 'best')
                format_type = item.get('type', 'video')
                
                # Base options
                ydl_opts = {
                    'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [self.update_download_progress],
                }
                
                # Set format-specific options
                if format_type == 'audio':
                    # Parse the format string for audio options
                    format_parts = format_string.split(' --')
                    format_selector = format_parts[0].replace('-f ', '')
                    
                    ydl_opts['format'] = format_selector
                    
                    # Apply audio extraction options based on format
                    if any('mp3' in part for part in format_parts):
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192' if '192K' in format_string else '128',
                        }]
                        ydl_opts['extractaudio'] = True
                        ydl_opts['audioformat'] = 'mp3'
                        if 'prefer-ffmpeg' in format_string:
                            ydl_opts['prefer_ffmpeg'] = True
                            
                    elif any('m4a' in part for part in format_parts):
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'm4a',
                            'preferredquality': '0',
                        }]
                        ydl_opts['extractaudio'] = True
                        ydl_opts['audioformat'] = 'm4a'
                        
                    elif any('vorbis' in part for part in format_parts):
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'vorbis',
                            'preferredquality': '0',
                        }]
                        ydl_opts['extractaudio'] = True
                        ydl_opts['audioformat'] = 'vorbis'
                else:
                    # For video, just use the format string directly
                    ydl_opts['format'] = format_string
                
                # Download the video
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([item['url']])
                    
            except Exception as e:
                self.log(f"Error downloading {item['title']}: {str(e)}", "ERROR")
        
        # On completion, update UI
        if not hasattr(self, 'download_cancelled') or not self.download_cancelled:
            self.on_download_complete()

    def on_download_complete(self):
        if hasattr(self, 'progress_window') and self.progress_window.winfo_exists():
            self.status_label["text"] = "All downloads completed!"
            self.current_progress_bar["value"] = 100
            self.overall_progress_bar["value"] = 100
            
            # Change cancel button to close the pop up
            for widget in self.progress_window.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button):
                            child.configure(text="Close", command=self.progress_window.destroy)
        
        # Call parent's completion handler
        if hasattr(self.root, 'on_download_complete'):
            self.root.on_download_complete()

    #Download according to selected to selected format and download playlist limit
    def get_download_items_with_limit(self):
        if not self.playlist_info or not self.selected_format:
            return []
        
        items = []# Format items for download with the selected format
        
        # Apply the video limit
        video_count = min(self.video_limit, len(self.videos)) if hasattr(self, 'video_limit') else len(self.videos)        
        for i, video in enumerate(self.videos):
            if i >= video_count:
                break
                
            if video.get('id'):
                items.append({
                    'url': f"https://www.youtube.com/watch?v={video['id']}",
                    'title': video.get('title', 'Unknown'),
                    'format': self.selected_format,
                    'type': self.selected_format_type
                })
        return items
        
    def get_download_items(self):
        # Return list of videos with selected format info
        if not self.playlist_info or not self.selected_format:
            return []
            
        # Format items for download with the selected format
        items = []
        for video in self.videos:
            if video.get('id'):
                items.append({
                    'url': f"https://www.youtube.com/watch?v={video['id']}",
                    'title': video.get('title', 'Unknown'),
                    'format': self.selected_format,
                    'type': self.selected_format_type
                })
        return items
######################End of the block
    # Calculate approximate size of playlist with selected format
    def calculate_playlist_size(self):
        if not hasattr(self, 'size_label') or not self.playlist_info or not self.videos:
            return
            
        # Skip calculation if the dialog is closed
        if not hasattr(self, 'format_dialog') or not self.format_dialog.winfo_exists():
            return
            
        try:
            # Get the first video to estimate size
            if not self.videos[0].get('id') or self.fetch_cancelled:
                return
                
            video_url = f"https://www.youtube.com/watch?v={self.videos[0]['id']}"
            format_type = self.format_type_var.get()
            format_display = self.format_var.get()
            
            if not format_display or self.fetch_cancelled:
                return
                
            # Update label to show we're calculating and we not just quite chilling
            if hasattr(self, 'size_label') and self.size_label.winfo_exists():
                self.size_label.config(text="Estimated Size: Calculating...")
            else:
                return
            
            # Get format string but remove any extra options for info extraction
            format_string = self.format_values.get(format_display, "").split(" --")[0]
            
            # Get info for the first video
            ydl_opts = {
                'quiet': True,
                'format': format_string,
                'no_warnings': True,
            }
            
            # Check if calculation should be cancelled
            if self.fetch_cancelled:
                return                
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                if self.fetch_cancelled or not info:
                    return                    
                # Get filesize from the selected format
                filesize = 0
                for fmt in info.get('formats', []):
                    if fmt.get('format_id') == info.get('format_id'):
                        filesize = fmt.get('filesize', 0)
                        break                
                # If we fail lets try the general filesize
                if not filesize:
                    filesize = info.get('filesize', 0)                
                # If we fail, we can use estimation based on duration
                if not filesize and info.get('duration'):
                    if format_type == "video":
                        if "720p" in format_display:
                            filesize = info.get('duration', 0) * 350000  # ~350KB/s for 720p
                        else:
                            filesize = info.get('duration', 0) * 200000  # ~200KB/s for 360p
                    else:  # audio
                        if "192kbps" in format_display:
                            filesize = info.get('duration', 0) * 24000  # ~24KB/s for 192kbps
                        else:
                            filesize = info.get('duration', 0) * 16000  # ~16KB/s for 128kbps
                
                # Calculate total size for all videos
                total_size = filesize * len(self.videos)
                
                # Update size label if it still exists
                if hasattr(self, 'size_label') and self.size_label.winfo_exists() and not self.fetch_cancelled:
                    self.size_label.config(text=f"Estimated Size: {format_size(total_size)}")
                    
        except Exception as e:
            # Update label if it still exists, i mean if not canceled previusly
            if hasattr(self, 'size_label') and self.size_label.winfo_exists() and not self.fetch_cancelled:
                self.size_label.config(text="Size: Estimation failed")
                self.log(f"Size calculation error: {str(e)}", "ERROR")
###########im just confused,so i take a nap
# Function to format file size in human-readable form
def format_size(bytes_size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

# Helper function to perform the download process
def download_item(item, output_path=None, progress_callback=None, log_func=None):
    # Set default output path if None is provided
    if output_path is None:
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        output_path = os.path.join(downloads_path, "yt-dlite")        
        # Create the directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)
    
    url = item.get('url')
    format_string = item.get('format', 'best')
    item_type = item.get('type', 'video')
    
    # Set up output template
    output_template = f"{output_path}/%(title)s.%(ext)s"
    
    # Base options
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'outtmpl': output_template,
    }
        
        # For audio downloads, ensure we're extracting and converting properly
    # For audio downloads, ensure we're extracting and converting properly
    if item_type == 'audio':
        # Parse the format string to extract options
        format_parts = format_string.split(' --')
        
        # Get just the format selector (remove -f if present)
        format_selector = format_parts[0].replace('-f ', '')
        
        # Set up base options for audio download
        ydl_opts['format'] = format_selector
        
        # Apply specific audio format and quality if specified
        if any('mp3' in part for part in format_parts):
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192' if '192K' in format_string else '128',
            }]
            ydl_opts['extractaudio'] = True
            ydl_opts['audioformat'] = 'mp3'
            if 'prefer-ffmpeg' in format_string:
                ydl_opts['prefer_ffmpeg'] = True
                
        elif any('m4a' in part for part in format_parts):
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': '0',
            }]
            ydl_opts['extractaudio'] = True
            ydl_opts['audioformat'] = 'm4a'
            
        elif any('vorbis' in part for part in format_parts):
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'vorbis',
                'preferredquality': '0',
            }]
            ydl_opts['extractaudio'] = True
            ydl_opts['audioformat'] = 'vorbis'
    else:
        # For video downloads, just use the format string
        ydl_opts['format'] = format_string
    
    # Add progress hooks if callback provided
    if progress_callback:
        ydl_opts['progress_hooks'] = [
            lambda d: progress_callback(d)
        ]
    
    # Logging function
    log = log_func if log_func else lambda msg, level: None
    
    try:
        # Download the video/audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            log(f"Download completed: {info.get('title', 'Unknown')}", "INFO")
            return {
                'success': True,
                'title': info.get('title', 'Unknown'),
                'filename': ydl.prepare_filename(info),
                'info': info
            }
    except Exception as e:
        error_msg = str(e)
        log(f"Download error: {error_msg}", "ERROR")
        
        # Try fallback options for common errors
        if "Requested format is not available" in error_msg and item_type == 'audio':
            log("Trying fallback format for audio download", "INFO")
            # Fallback to simpler format string
            ydl_opts['format'] = 'bestaudio/best'
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    log(f"Download completed with fallback format: {info.get('title', 'Unknown')}", "INFO")
                    return {
                        'success': True,
                        'title': info.get('title', 'Unknown'),
                        'filename': ydl.prepare_filename(info),
                        'info': info
                    }
            except Exception as e2:
                log(f"Fallback download failed: {str(e2)}", "ERROR")
                return {
                    'success': False,
                    'error': str(e2)
                }
        
        return {
            'success': False,
            'error': error_msg
        }

# Function to handle downloading a list of items, this is incomplete but it send update to the main GUI,like playlist it supposed to show download progress etc
def download_items(items, output_path=".", progress_callback=None, completion_callback=None, log_func=None):
    # Create a thread to handle downloads
    def download_thread():
        results = []
        total = len(items)
        
        for i, item in enumerate(items):
            # Update progress
            if progress_callback:
                progress_callback(i, total, "Preparing...")
            
            # Download the item
            result = download_item(item, output_path, 
                                  lambda d: progress_callback(i, total, d.get('status', 'downloading'), d) if progress_callback else None,
                                  log_func)
            
            results.append(result)
        
        # Call completion callback
        if completion_callback:
            completion_callback(results)
    
    # Start the download thread
    thread = threading.Thread(target=download_thread, daemon=True)
    thread.start()
    return thread
