import yt_dlp
import threading
import webbrowser
import requests
from io import BytesIO
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
import re
import time
import os
import urllib.request
from misc import PlaylistHandler

class BeginnerDownloaderGUI(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.thumbnail_images = []
        self.downloader_thread = None
        self.search_thread = None
        self.search_event = threading.Event()  # Event to signal search cancellation
        self.is_downloading = False

        # Configure styles
        self.style = ttk.Style()
        self.style.configure('Separator.TFrame', background='#e0e0e0')

        # Main Frame Content
        self.main_frame = ttk.Frame(self)  # Change parent to self (to make this a tab)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Search Bar Section (Horizontal)
        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(fill=tk.X, pady=5)

        # Search label, entry, buttons
        search_label = ttk.Label(search_frame, text="Search here:", font=("Helvetica", 9, "bold"))
        search_label.pack(side=tk.LEFT, padx=5)

        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        self.paste_button = ttk.Button(search_frame, text="Paste", command=self.paste_from_clipboard)
        self.paste_button.pack(side=tk.LEFT, padx=5)

        self.search_button = ttk.Button(search_frame, text="Search", command=self.search_engine)
        self.search_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(search_frame, text="X Cancel", command=self.cancel_search)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Scrollable Frame for Results
        self.result_frame = ttk.Frame(self.main_frame)
        self.result_frame.pack(fill=tk.BOTH, expand=True)

        self.scrollable_canvas = tk.Canvas(self.result_frame)
        self.scrollbar = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.scrollable_canvas.yview)
        
        self.scrollable_frame = ttk.Frame(self.scrollable_canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.scrollable_canvas.configure(scrollregion=self.scrollable_canvas.bbox("all")))
        
        self.canvas_window = self.scrollable_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollable_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bottom section for download controls, progress, etc...
        bottom_frame = ttk.Frame(self.main_frame)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=1)

        # Download path section
        download_frame = ttk.Frame(bottom_frame)
        download_frame.pack(fill=tk.X, pady=5)
        download_frame.columnconfigure(1, weight=1)
        
        ttk.Label(download_frame, text="Save to:", font=("Helvetica", 9, "bold")).grid(row=0, column=0, padx=5, sticky=tk.W)
        self.save_path_entry = ttk.Entry(download_frame, font=("Helvetica", 9))
        self.save_path_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)
        
        # Set default save path to Downloads/yt-dlite folder
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        yt_dlite_path = os.path.join(downloads_path, "yt-dlite")
        
        if not os.path.exists(yt_dlite_path):
            os.makedirs(yt_dlite_path)
        
        self.save_path_entry.insert(0, yt_dlite_path)
        
        browse_button = ttk.Button(download_frame, text="Browse", command=self.browse_save_location)
        browse_button.grid(row=0, column=2, padx=5)

        # Progress bar
        progress_frame = ttk.Frame(bottom_frame)
        progress_frame.pack(fill=tk.X, pady=1)
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate', style="TProgressbar")
        self.progress.pack(fill=tk.X, padx=5)
        
        self.status_label = ttk.Label(progress_frame, text="Ready", font=("Helvetica", 9))
        self.status_label.pack(pady=1)
        # Download buttons
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(fill=tk.X, pady=0.1)                
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel_download)
        cancel_button.pack(side=tk.LEFT, padx=1)

    import threading

    def search_engine(self):
        query = self.search_entry.get().strip()
        if not query or self.search_event.is_set():  # Stop if the event is set
            return

        # Clear previous results
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.thumbnail_images.clear()

        # Check if it's a URL using a fast method
        if query.startswith("http"):
            self.process_url(query)
        else:
            self.search_youtube(query)

    def process_url(self, url):
        """Detect if the URL is a playlist or a single video and process accordingly."""
        #if self.search_event.is_set():  # Stop if the event is set
            #return

        if "list=" in url:
            # Update GUI to show playlist detection and set loading cursor
            self.status_label.config(text="Playlist detected! Processing...", foreground="blue")
            self.parent.config(cursor="watch")  # Change mouse to loading

            # Start a new thread to process the playlist so the UI remains responsive
            threading.Thread(target=self.process_playlist, args=(url,)).start()

        else:
            # It's a single video, process it for download
            self.status_label.config(text="Single video detected! Processing...", foreground="blue")
            self.create_download_button(url)
            self.status_label.config(text="Video ready for download!", foreground="green")

    def process_playlist(self, url):
        """Process playlist in a background thread."""
        if self.search_event.is_set():  # Stop if the event is set
            return

        import misc
        if misc.is_playlist(url):  # Ensuring it's a valid playlist
            # Call the playlist handler function
            playlist_handler = misc.process_playlist_url(self.parent, url)
            # After processing, update GUI
            self.status_label.config(text="Playlist processed successfully!", foreground="green")
        else:
            self.status_label.config(text="Invalid playlist URL!", foreground="red")

        # Reset mouse cursor after processing
        self.parent.config(cursor="")  # Reset to default cursor
   
    def create_widgets(self):
        # Search frame
        self.search_frame = ttk.Frame(self.parent)
        self.search_frame.pack(pady=10)
        
        self.search_entry = ttk.Entry(self.search_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        
        self.search_button = ttk.Button(
            self.search_frame, 
            text="Search", 
            command=lambda: self.search_youtube(self.search_entry.get())
        )
        self.search_button.pack(side=tk.LEFT)
        
        # Status label
        self.status_label = ttk.Label(self.parent, text="", foreground="blue")
        self.status_label.pack()
        
        # Results canvas with scrollbar
        self.results_canvas = tk.Canvas(self.parent)
        self.scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.results_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.results_canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all"))
        )
        
        self.results_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.results_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.results_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
    
    def search_youtube(self, query):
        """Search YouTube for videos in a separate thread."""
        if not query:
            return
            
        # Clear previous results
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.thumbnail_images.clear()
        
        # Show searching status
        self.status_label.config(text="Searching...", foreground="blue")
        
        def search():
            ydl_opts = {
                'extract_flat': True,
                'quiet': True,
                'force_generic_extractor': True,
                'progress_hooks': [self.yt_dlp_hook]
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    search_results = ydl.extract_info(f"ytsearch10:{query}", download=False)

                    if not search_results or 'entries' not in search_results:
                        if not self.search_event.is_set():
                            self.parent.after(0, lambda: self.status_label.config(
                                text="No results found", 
                                foreground="red"
                            ))
                        return

                    self.parent.after(0, lambda: self.status_label.config(text=""))

                    for i, video in enumerate(search_results['entries']):
                        if not video or self.search_event.is_set():  # Check if search is canceled
                            self.parent.after(0, lambda: self.status_label.config(
                                text="Search Canceled", foreground="red"
                            ))  # Update GUI safely
                            return
                        
                        # Schedule UI updates in main thread
                        self.parent.after(0, self.create_video_item, video, i)

            except Exception as e:
                if not self.search_event.is_set():  # Only show error if search was not canceled
                    self.parent.after(0, lambda: self.status_label.config(
                        text=f"Error: {str(e)}", 
                        foreground="red"
                    ))

        # Start search in background thread
        self.search_event.clear()  # Clear the event before starting the search
        self.search_thread = threading.Thread(target=search, daemon=True)
        self.search_thread.start()



    def create_video_item(self, video, index):
        """Create a video result item in the UI."""
        video_frame = ttk.Frame(self.scrollable_frame)
        video_frame.pack(fill=tk.X, padx=5, pady=5)

        # Add separator if not the first item
        if index > 0:
            separator = ttk.Frame(self.scrollable_frame, height=1, relief=tk.SUNKEN, borderwidth=1)
            separator.pack(fill=tk.X, pady=5)

        # Main container (Thumbnail + Buttons + Info)
        container = ttk.Frame(video_frame)
        container.pack(fill=tk.X, padx=5, pady=5)

        # Thumbnail placeholder (scaled to fit)
        thumbnail_label = ttk.Label(container, text="Loading...", width=15)
        thumbnail_label.pack(side=tk.LEFT, padx=5, pady=5)

        # Get best available thumbnail URL
        thumbnail_url = (video.get('thumbnail') or
                        next((t['url'] for t in video.get('thumbnails', []) if t.get('url')), ''))

        # Start thumbnail download in background
        threading.Thread(
            target=self.download_thumbnail,
            args=(thumbnail_url, thumbnail_label),
            daemon=True
        ).start()

        # Button section (right of thumbnail)
        button_frame = ttk.Frame(container)
        button_frame.pack(side=tk.LEFT, padx=10, pady=5)

        # Play button
        play_button = ttk.Button(
            button_frame,
            text="▶ Play",
            command=lambda url=video.get('url') or f"https://youtu.be/{video.get('id', '')}":
                webbrowser.open(url)
        )
        play_button.pack(fill=tk.X, pady=2)

        # Download button
        download_button = ttk.Button(
            button_frame,
            text="↓ Download",
            command=lambda v=video: self.create_download_button(v)
        )
        download_button.pack(fill=tk.X, pady=2)

        # Video info section (to the right of buttons)
        info_frame = ttk.Frame(container)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Title (truncated for long titles)
        title = video.get('title', 'No title')[:60] + ('...' if len(video.get('title', '')) > 60 else '')
        ttk.Label(info_frame, text=title, font=('Arial', 10, 'bold')).pack(anchor='w')

        # Channel name
        ttk.Label(info_frame, text=video.get('uploader', 'Unknown channel')).pack(anchor='w')

        # Duration fix: Convert float to int before formatting
        duration = int(video.get('duration', 0)) if video.get('duration') else 0
        duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else 'N/A'
        ttk.Label(info_frame, text=duration_str).pack(anchor='w')

        # Store video data
        video_frame.video_data = video


    def download_thumbnail(self, thumbnail_url, label):
        """Download and display video thumbnail with fallback."""
        try:
            if not thumbnail_url.startswith(('http://', 'https://')):
                raise ValueError("Invalid thumbnail URL")

            # Try to get a higher resolution thumbnail if available
            if "hqdefault" in thumbnail_url:
                thumbnail_url = thumbnail_url.replace("hqdefault", "maxresdefault")

            img_data = None

            try:
                response = requests.get(thumbnail_url, stream=True, timeout=10)
                response.raise_for_status()
                img_data = response.content
            except Exception:
                print("Requests failed, falling back to urllib.")
                try:
                    with urllib.request.urlopen(thumbnail_url) as response:
                        img_data = response.read()
                except Exception as e:
                    print(f"Fallback also failed: {e}")
                    img_data = None

            if img_data:
                img = Image.open(BytesIO(img_data))
                img.thumbnail((240, 170), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                # Keep reference and update UI
                self.thumbnail_images.append(photo)
                self.parent.after(0, lambda: label.config(image=photo, text=""))
                label.image = photo  # Keep reference
            else:
                raise ValueError("Failed to retrieve thumbnail")

        except Exception as e:
            print(f"Error loading thumbnail: {e}")
            self.parent.after(0, lambda: label.config(
                text="No thumbnail", 
                image=''
            ))
    
    def yt_dlp_hook(self, d):
        """Hook to handle yt-dlp errors."""
        if d['status'] == 'error':
            print(f"yt-dlp error: {d['error']}")
                
    from tkinter import Toplevel, StringVar, messagebox, ttk, Button
    import threading
    import yt_dlp

    def create_download_button(self, url):
        """Create a download button for the video with format options."""
        # Update GUI to indicate that download options are being prepared
        self.status_label.config(text="Preparing download options...", foreground="blue")
        print(f"Creating download options for: {url}")
        
        # If url is a dictionary, extract the valid video URL.
        # We assume that the valid video URL is stored in the top-level key "url"
        if isinstance(url, dict):
            valid_url = url.get('url', '')
            print(f"Extracted valid URL: {valid_url}")
            url = valid_url  # Now 'url' contains just the valid video link.
        
        # Continue to create the download button using the extracted URL
            self.open_format_selection_popup(url)


    def open_format_selection_popup(self, url):
        """Open a single popup window for selecting video or audio formats with dropdowns."""
        # Create a new top-level window (popup)
        format_popup = tk.Toplevel(self.parent)
        format_popup.title("Download Options")
        format_popup.geometry("500x280")
        format_popup.resizable(False, False)
        
        # Make the popup modal (blocks interaction with main window)
        format_popup.transient(self.parent)
        format_popup.grab_set()
        
        # Center popup on parent window
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (500 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (280 // 2)
        format_popup.geometry(f"+{x}+{y}")
        
        # Create a heading
        heading_label = ttk.Label(format_popup, text="Select Download Format", font=("Helvetica", 12, "bold"))
        heading_label.pack(pady=(15, 10))
        
        # Create a container frame
        container = ttk.Frame(format_popup)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Media type selection frame
        media_type_frame = ttk.Frame(container)
        media_type_frame.pack(fill=tk.X, pady=5)
        
        # Format options dictionaries
        video_format_options = [
            ("MP4 - Best Quality", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"),
            ("MP4 - 1080p", "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best"),
            ("MP4 - 720p", "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best"),
            ("MP4 - 480p", "bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[ext=mp4][height<=480]/best"),
            ("MP4 - 360p", "bestvideo[ext=mp4][height<=360]+bestaudio[ext=m4a]/best[ext=mp4][height<=360]/best"),
            ("WebM - Best Quality", "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best")
        ]
        
        audio_format_options = [
            ("MP3 - 320kbps", "bestaudio/best -x --audio-format mp3 --audio-quality 320K"),
            ("MP3 - 192kbps", "bestaudio/best -x --audio-format mp3 --audio-quality 192K"),
            ("MP3 - 128kbps", "bestaudio/best -x --audio-format mp3 --audio-quality 128K"),
            ("M4A - Best Quality", "bestaudio/best -x --audio-format m4a --audio-quality 0"),
            ("OGG - Best Quality", "bestaudio/best -x --audio-format vorbis --audio-quality 0")
        ]
        
        # Variables for selections
        media_type_var = tk.StringVar(value="video")
        video_format_var = tk.StringVar(value=video_format_options[0][0])
        audio_format_var = tk.StringVar(value=audio_format_options[0][0])
        
        # Function to update dropdown visibility based on media type
        def update_dropdown_visibility():
            if media_type_var.get() == "video":
                video_dropdown.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
                audio_dropdown.pack_forget()
                format_label.config(text="Video Format:")
            else:
                audio_dropdown.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
                video_dropdown.pack_forget()
                format_label.config(text="Audio Format:")
        
        # Video radio button
        video_radio = ttk.Radiobutton(
            media_type_frame, 
            text="Video", 
            variable=media_type_var, 
            value="video",
            command=update_dropdown_visibility
        )
        video_radio.pack(side=tk.LEFT, padx=5)
        
        # Audio radio button
        audio_radio = ttk.Radiobutton(
            media_type_frame, 
            text="Audio", 
            variable=media_type_var, 
            value="audio",
            command=update_dropdown_visibility
        )
        audio_radio.pack(side=tk.LEFT, padx=20)
        
        # Format selection frame
        format_frame = ttk.Frame(container)
        format_frame.pack(fill=tk.X, pady=10)
        
        # Format label
        format_label = ttk.Label(format_frame, text="Video Format:")
        format_label.pack(side=tk.LEFT)
        
        # Video dropdown
        video_dropdown = ttk.Combobox(
            format_frame, 
            textvariable=video_format_var, 
            values=[x[0] for x in video_format_options],
            state="readonly",
            width=30
        )
        
        # Audio dropdown
        audio_dropdown = ttk.Combobox(
            format_frame, 
            textvariable=audio_format_var, 
            values=[x[0] for x in audio_format_options],
            state="readonly",
            width=30
        )
        
        # Initial dropdown setup
        update_dropdown_visibility()
        
        # Save path section
        path_frame = ttk.Frame(container)
        path_frame.pack(fill=tk.X, pady=10)
        
        path_label = ttk.Label(path_frame, text="Save to:")
        path_label.pack(side=tk.LEFT)
        
        # Get default save path from entry
        default_path = self.save_path_entry.get() if hasattr(self, 'save_path_entry') else os.path.expanduser("~/Downloads")
        
        path_var = tk.StringVar(value=default_path)
        path_entry = ttk.Entry(path_frame, textvariable=path_var)
        path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Browse button
        browse_button = ttk.Button(
            path_frame,
            text="Browse",
            command=lambda: path_var.set(filedialog.askdirectory() or path_var.get())
        )
        browse_button.pack(side=tk.RIGHT)
        
        # Button frame
        button_frame = ttk.Frame(format_popup)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=15)
        
        # Cancel button
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=format_popup.destroy
        )
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Download button
        download_button = ttk.Button(
            button_frame, 
            text="Download", 
            command=lambda: [
                format_popup.destroy(),
                self.start_download(
                    # If url is a dict, let start_download handle it.
                    url, 
                    video_format_options[[x[0] for x in video_format_options].index(video_format_var.get())][1] 
                        if media_type_var.get() == "video" 
                        else audio_format_options[[x[0] for x in audio_format_options].index(audio_format_var.get())][1], 
                    path_var.get()
                )
            ]
        )
        download_button.pack(side=tk.RIGHT, padx=5)
###########################holy###########################################        
    def start_download(self, url, format_string, output_path):
        """Start the download process with the selected format options."""
        # Ensure the output directory exists
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # Check if the provided url is a dictionary (as seen in debug prints)
        if isinstance(url, dict):
            print("start_download: Received URL as a dict. Extracting string from key 'url'.")
            url_str = url.get('url', '')
            print(f"start_download: Extracted URL: {url_str}")
            url = url_str
        else:
            print("start_download: Received URL as a string.")
        
        # Debug prints for download settings
        print(f"start_download: URL = {url}")
        print(f"start_download: Selected format string = {format_string}")
        print(f"start_download: Output path = {output_path}")
        
        # Update status in the UI
        self.status_label.config(text="Starting download...", foreground="blue")
        self.progress['value'] = 0
        
        # Start download in a thread to keep UI responsive
        download_thread = threading.Thread(
            target=self._download_thread,
            args=(url, format_string, output_path)  # Now URL is a string
        )
        download_thread.daemon = True
        download_thread.start()

    def _download_thread(self, url, format_string, output_path):
        """Download thread that handles the actual downloading process."""
        try:
            # Base options for yt-dlp
            ydl_opts = {
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.update_download_progress],
                'verbose': True,   # Debug info enabled
                'quiet': False,    # Debug info enabled
            }
            
            print("Download thread: yt-dlp options before format handling:")
            print(ydl_opts)
            
            # Set format-specific options for audio or video
            if 'audio' in format_string:
                # For audio, split by ' --' and use the first part as the selector
                ydl_opts['format'] = format_string.split(' --')[0].strip()
                if 'mp3' in format_string:
                    quality = '320' if '320K' in format_string else '192' if '192K' in format_string else '128'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': quality,
                    }]
                    ydl_opts['extractaudio'] = True
                elif 'm4a' in format_string:
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'm4a',
                        'preferredquality': '0',
                    }]
                    ydl_opts['extractaudio'] = True
                elif 'vorbis' in format_string or 'ogg' in format_string.lower():
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'vorbis',
                        'preferredquality': '0',
                    }]
                    ydl_opts['extractaudio'] = True
            else:
                # For video, if the format string has a '-f ' prefix, remove it.
                if format_string.startswith('-f '):
                    format_string = format_string[3:]
                ydl_opts['format'] = format_string
            
            print("Download thread: Final yt-dlp options:")
            print(ydl_opts)
            print(f"Download thread: Executing yt-dlp for URL: {url}")
            print(f"Download thread: With format: {format_string}")
            
            # Execute the download with yt-dlp, passing a list containing the URL string
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
        except Exception as e:
            error_msg = f"Error downloading from {url}: {str(e)}"
            self.status_label.config(text=error_msg, foreground="red")
            print(error_msg)
            time.sleep(2)
        
        # On completion, update UI
        self.on_download_complete()

    def on_download_complete(self):
        """Update UI when download is complete."""
        self.status_label.config(text="Download complete!", foreground="green")
        self.progress['value'] = 100
################################################################################33
    def update_download_progress(self, d):
        """Update the UI with download progress information."""
        if d['status'] == 'downloading':
            # Extract progress information
            percent = d.get('_percent_str', '0%')
            speed = d.get('_speed_str', 'N/A')
            eta = d.get('_eta_str', 'N/A')
            
            # Update progress bar if percentage is available
            if '_percent_str' in d and d['_percent_str'].endswith('%'):
                try:
                    percent_value = float(d['_percent_str'].replace('%', ''))
                    self.progress['value'] = percent_value
                except ValueError:
                    # If conversion fails, don't update the progress bar
                    pass
            
            # Update status label with progress information
            progress_text = f"Downloading: {percent} complete (Speed: {speed}, ETA: {eta})"
            self.status_label.config(text=progress_text, foreground="blue")
        
        elif d['status'] == 'finished':
            self.status_label.config(text="Download finished, processing file...", foreground="green")
            self.progress['value'] = 100

    def update_progress_hook(self, d):
        """Hook function for yt-dlp to update progress bar."""
        if self.download_cancelled:
            return
        
        # Handle different status messages
        if d['status'] == 'downloading':
            try:
                # Calculate percentage if total bytes are known
                if d.get('total_bytes'):
                    percent = d['downloaded_bytes'] / d['total_bytes'] * 100
                # Use estimated total bytes if available
                elif d.get('total_bytes_estimate'):
                    percent = d['downloaded_bytes'] / d['total_bytes_estimate'] * 100
                else:
                    # If we can't calculate percentage, just show indeterminate progress
                    percent = -1
                
                # Get download speed
                speed = d.get('speed', 0)
                if speed:
                    speed_str = f"{speed/1024/1024:.2f} MB/s"
                else:
                    speed_str = "-- MB/s"
                
                # Get ETA
                eta = d.get('eta', 0)
                if eta:
                    eta_str = f"ETA: {eta//60}m {eta%60}s"
                else:
                    eta_str = "ETA: --"
                
                # Format status message
                status_msg = f"Downloading: {speed_str} {eta_str}"
                
                # Update progress bar and status in main thread
                if percent >= 0:
                    self.parent.after(0, lambda: self.progress.config(value=percent))
                self.parent.after(0, lambda: self.status_label.config(
                    text=status_msg, 
                    foreground="blue"
                ))
                
            except Exception as e:
                # If something goes wrong with progress calculation, show generic message
                self.parent.after(0, lambda: self.status_label.config(
                    text=f"Downloading...", 
                    foreground="blue"
                ))
        
        elif d['status'] == 'finished':
            # Update UI to show processing state
            self.parent.after(0, lambda: self.progress.config(value=100))
            self.parent.after(0, lambda: self.status_label.config(
                text="Download complete, processing file...", 
                foreground="green"
            ))
        
        elif d['status'] == 'error':
            # Show error message
            self.parent.after(0, lambda: self.status_label.config(
                text=f"Error: {d.get('error', 'Unknown error')}", 
                foreground="red"
            ))

    def cancel_download(self):
        """Cancel the current download."""
        if self.is_downloading:
            # Set cancellation flag
            self.download_cancelled = True
            
            # Update UI
            self.status_label.config(text="Cancelling download...", foreground="red")
            
            # Reset progress bar
            self.progress['value'] = 0
            
            # Re-enable search button
            if hasattr(self, 'search_button'):
                self.search_button.config(state=tk.NORMAL)

    def onn_download_complete(self, info=None):
        """Handle actions when download is complete."""
        if self.download_cancelled:
            self.status_label.config(text="Download cancelled", foreground="red")
            self.progress['value'] = 0
        else:
            # Set progress to 100%
            self.progress['value'] = 100
            
            # Get filename and title
            title = info.get('title', 'Unknown') if info else 'Unknown'
            filename = info.get('_filename', '') if info else ''
            
            # Update status with success message
            self.status_label.config(
                text=f"Download complete: {title[:30]}{'...' if len(title) > 30 else ''}", 
                foreground="green"
            )
            
            # Show a notification (optional)
            try:
                from tkinter import messagebox
                messagebox.showinfo(
                    "Download Complete", 
                    f"Successfully downloaded:\n{title}"
                )
            except:
                pass  # Skip notification if messagebox fails
        
        # Re-enable search button
        if hasattr(self, 'search_button'):
            self.search_button.config(state=tk.NORMAL)
        
        # Reset download flags
        self.is_downloading = False
        self.download_cancelled = False

    def _format_size(self, bytes):
        """Format bytes to human-readable size."""
        if bytes < 1024:
            return f"{bytes} B"
        elif bytes < 1024 * 1024:
            return f"{bytes/1024:.1f} KB"
        elif bytes < 1024 * 1024 * 1024:
            return f"{bytes/(1024*1024):.1f} MB"
        else:
            return f"{bytes/(1024*1024*1024):.1f} GB"

    def _format_time(self, seconds):
        """Format seconds to human-readable time."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds//60:.0f}m {seconds%60:.0f}s"
        else:
            return f"{seconds//3600:.0f}h {(seconds%3600)//60:.0f}m"

    def cancel_download(self):
        """Cancel the current download."""
        if self.is_downloading:
            # Set flag to tell download thread to stop
            self.is_downloading = False
            
            # Update UI
            self.status_label.config(text="Cancelling download...", foreground="red")
            
            # Note: yt-dlp doesn't have a direct way to cancel downloads,
            # so we rely on the download thread checking is_downloading
            # at various points to stop the process.
        else:
            self.status_label.config(text="No active download to cancel", foreground="blue")

    def on_download_complete(self):
        """Handle actions when download is complete."""
        # Update UI
        self.status_label.config(text="Download complete!", foreground="green")
        self.progress["value"] = 100
        
        # Reset download flag
        self.is_downloading = False
        
        # Re-enable any download buttons
        if hasattr(self, 'download_button'):
            self.download_button.config(state=tk.NORMAL)
        
        # Optional: Play a sound or show a notification
        # self.parent.bell()  # Simple bell sound
        
        # Optional: Show the file in explorer/finder
        # if sys.platform == 'win32':
        #     os.startfile(self.save_path_entry.get())
        # elif sys.platform == 'darwin':  # macOS
        #     subprocess.call(['open', self.save_path_entry.get()])
        # else:  # Linux
        #     subprocess.call(['xdg-open', self.save_path_entry.get()])


    def paste_from_clipboard(self):
        """Paste URL from clipboard to search bar using Tkinter's clipboard."""
        clipboard_text = self.parent.clipboard_get()
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, clipboard_text)

    def browse_save_location(self):
        """Open a file dialog to choose the save location."""
        from tkinter.filedialog import askdirectory
        directory = askdirectory()
        if directory:
            self.save_path_entry.delete(0, tk.END)
            self.save_path_entry.insert(0, directory)

    def play_video(self, url):
        """Open the video URL in a browser."""
        if url:
            webbrowser.open(url)

    def cancel_search(self):
        """Cancel the ongoing search operation and update the GUI."""
        print("Search canceled.")  # This still prints to the terminal
        
        # Set the event to signal the search thread to stop
        self.search_event.set()

        # Ensure the GUI updates in the main thread
        self.master.after(0, lambda: self.status_label.config(text="Search Canceled", foreground="red"))

if __name__ == "__main__":
    parent = tk.Tk()
    parent.title("Beginner Downloader")
    parent.geometry("800x600")
    
    app = BeginnerDownloaderGUI(parent)
    app.pack(fill=tk.BOTH, expand=True)
    parent.mainloop()
