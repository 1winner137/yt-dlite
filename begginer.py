import os
import re
import sys
import time
import threading
import urllib.request
import webbrowser
import requests
import yt_dlp
import tkinter as tk
from tkinter import filedialog, Toplevel, StringVar, messagebox, ttk, Button
from io import BytesIO
from PIL import Image, ImageTk
from misc import PlaylistHandler
import io
class HomeGui(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.thumbnail_images = []
        self.downloader_thread = None
        self.search_thread = None
        self._search_active = True 
        self.is_downloading = False
        self.cancel_requested = False
        # Configure styles
        self.style = ttk.Style()
        self.style.configure('Separator.TFrame', background='#e0e0e0')
        #Main Frame Content start here
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Search Bar Section (Horizontal)
        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(fill=tk.X, pady=5)
        # Search buttons
        search_label = ttk.Label(search_frame, text="Search here:", font=("Helvetica", 9, "bold"))
        search_label.pack(side=tk.LEFT, padx=5)
        
        # Create Entry with placeholder
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.insert(0, "how to use yt-dlite")
        self.search_entry.bind("<FocusIn>", lambda event: self.search_entry.delete(0, tk.END) if self.search_entry.get() == "how to use yt-dlite" else None)
        self.search_entry.bind("<Return>", lambda event: self.search_engine())
        
        # Automatically run search when initialized
        self.after(500, self.search_engine)  # Run after a short delay to ensure UI is ready

        self.paste_button = ttk.Button(search_frame, text="Paste", command=self.paste_from_clipboard)
        self.paste_button.pack(side=tk.LEFT, padx=5)

        self.search_button = ttk.Button(search_frame, text="Search", command=self.search_engine)
        self.search_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(search_frame, text="X Cancel", command=self.cancel_search)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # Scrollable Frame for Results from searching
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

    def paste_from_clipboard(self):
        """Paste URL from clipboard to search bar using Tkinter's clipboard."""
        clipboard_text = self.parent.clipboard_get()
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, clipboard_text)

    def cancel_search(self):
        print("Search canceled.")
        self._search_active = False
        self.status_label.config(text="Search Canceled", foreground="red")
        self.parent.config(cursor="") #reset flag

    def browse_save_location(self):
        from tkinter.filedialog import askdirectory
        directory = askdirectory()
        if directory:
            self.save_path_entry.delete(0, tk.END)
            self.save_path_entry.insert(0, directory)

    def search_engine(self):
        query = self.search_entry.get().strip()
        if not query:
            # Show message to enter a link if query is empty
            self.status_label.config(text="Please enter a search term or URL", foreground="red")
            return

        # Clear previous results
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.thumbnail_images.clear()

        # Reset search cancellation flag
        self._search_active = True

        # Check if it's a URL
        if query.startswith("http"):
            self.process_url(query)
        else:
            self.search_youtube(query)

    def process_url(self, url):
        if not self._search_active:  # Check flag instead of event
            return

        if not url.strip():
            # Show message if URL is empty after stripping
            self.status_label.config(text="Please enter a URL", foreground="red")
            return

        if "list=" in url:
            self.status_label.config(text="Playlist detected! Processing...", foreground="blue")
            self.parent.config(cursor="watch")  # Change mouse to loading
            threading.Thread(target=self.process_playlist, args=(url,)).start()
        else:
            self.status_label.config(text="Single video detected! Processing...", foreground="blue")
            self.create_download_button(url)
            self.status_label.config(text="Video ready for download!", foreground="green")
            self.open_format_selection_popup(url)

    def process_playlist(self, url):
        if not self._search_active:  # Check flag instead of event
            return
        import misc
        if misc.is_playlist(url):  # Ensuring it's a valid playlist
            playlist_handler = misc.process_playlist_url(self.parent, url)
            self.status_label.config(text="Playlist processed successfully!", foreground="green")
        else:
            self.status_label.config(text="Invalid playlist URL!", foreground="red")

        self.parent.config(cursor="")
   
    def create_widgets(self):
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
        if not query:
            return            
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy() #clear previously results
        self.thumbnail_images.clear()        
        self.status_label.config(text="Searching...", foreground="blue")        
        # Create a list to store captured output messages
        captured_output = []
        
        def custom_output_hook(message):
            captured_output.append(message)
            if "Failed to resolve" in message or "Temporary failure in name resolution" in message or "Failed to connect" in message:
                self.parent.after(0, lambda: self.show_network_error_popup(message))
        
        #configure yt-dlp to use the hook
        def search():
            ydl_opts = {
                'extract_flat': True,
                'quiet': False,  # Need this to be False to get output messages
                'force_generic_extractor': True,
                'progress_hooks': [self.yt_dlp_hook],
                'verbose': True,  # Enable verbose output especially in terminal
            }

            try:
                # Redirect stdout to capture yt-dlp output
                original_stdout = sys.stdout
                sys.stdout = io.StringIO()
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # This is for overriding ytd-lp's output methods to capture network errors
                    original_to_screen = ydl.to_screen
                    original_to_stderr = ydl.to_stderr
                    
                    def capture_output(message, *args, **kwargs):
                        custom_output_hook(message)
                        return original_to_screen(message, *args, **kwargs)
                    
                    def capture_stderr(message, *args, **kwargs):
                        custom_output_hook(message)
                        return original_to_stderr(message, *args, **kwargs)
                    
                    ydl.to_screen = capture_output
                    ydl.to_stderr = capture_stderr
                    
                    search_results = ydl.extract_info(f"ytsearch10:{query}", download=False)

                    # Restore original stdout and output methods
                    sys.stdout = original_stdout
                    ydl.to_screen = original_to_screen
                    ydl.to_stderr = original_to_stderr

                    if not search_results or 'entries' not in search_results:
                        if self._search_active:  # Check flag instead of event
                            self.parent.after(0, lambda: self.status_label.config(
                                text="No results found", 
                                foreground="red"
                            ))
                        return

                    self.parent.after(0, lambda: self.status_label.config(text=""))

                    for i, video in enumerate(search_results['entries']):
                        if not video or not self._search_active:  # Check flag instead of event
                            self.parent.after(0, lambda: self.status_label.config(
                                text="Search Canceled", foreground="red"
                            )) 
                            return
                        
                        # Schedule UI updates in main thread
                        self.parent.after(0, self.create_video_item, video, i)

            except Exception as e:
                if self._search_active:  # Check flag instead of event
                    error_msg = str(e)
                    # Check for specific network error messages
                    if "Failed to resolve" in error_msg or "Failed to connect" in error_msg or "Temporary failure in name resolution" in error_msg:
                        self.parent.after(0, lambda: self.show_network_error_popup(error_msg))
                    else:
                        self.parent.after(0, lambda: self.status_label.config(
                            text=(f"Error: {error_msg}"), 
                            foreground="red"
                        ))

        # Start search in background thread
        self._search_active = True  # Set flag instead of clearing event
        self.search_thread = threading.Thread(target=search, daemon=True)
        self.search_thread.start()

    #Display a network error popup
    def show_network_error_popup(self, _):
        import tkinter.messagebox as messagebox
        messagebox.showerror("Network Error", "Failed to connect. Check your internet and try again.")
        self.status_label.config(text="Network Error", foreground="red")

    #Create a video result item in the UI
    def create_video_item(self, video, index):
        video_frame = ttk.Frame(self.scrollable_frame)
        video_frame.pack(fill=tk.X, padx=5, pady=5)
        if index > 0:
            separator = ttk.Frame(self.scrollable_frame, height=1, relief=tk.SUNKEN, borderwidth=1)
            separator.pack(fill=tk.X, pady=5)

        # Main container (Thumbnail + Buttons + some Info)
        container = ttk.Frame(video_frame)
        container.pack(fill=tk.X, padx=5, pady=5)
        thumbnail_label = ttk.Label(container, text="Loading...", width=15)
        thumbnail_label.pack(side=tk.LEFT, padx=5, pady=5)
        thumbnail_url = (video.get('thumbnail') or
                        next((t['url'] for t in video.get('thumbnails', []) if t.get('url')), '')) #Best thumbnail url accoring to googling

        # Start thumbnail download in background
        threading.Thread(
            target=self.download_thumbnail,
            args=(thumbnail_url, thumbnail_label),
            daemon=True
        ).start()

        # Button sections
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

        # Share button
        def copy_and_notify(url_data):
            if isinstance(url_data, dict):
                url_data = url_data.get('url', '')
                print(f"Extracted valid URL: {url_data}")
            
            # Copy URL to clipboard
            self.parent.clipboard_clear()
            self.parent.clipboard_append(url_data)
            
            # Show notification popup
            notification = tk.Toplevel(self.parent)
            notification.overrideredirect(True)
            notification.attributes('-topmost', True)
            
            # Position the popup near the sharing button
            x = self.parent.winfo_pointerx()
            y = self.parent.winfo_pointery()
            notification.geometry(f"+{x+10}+{y+10}")
            ttk.Label(notification, text="Link copied to clipboard!", padding=10).pack()
            notification.after(2000, notification.destroy) #close after 2 seconds

        share_button = ttk.Button(
            button_frame,
            text="↗ Share",
            command=lambda url=video.get('url') or f"https://youtu.be/{video.get('id', '')}":
                copy_and_notify(url)
        )
        share_button.pack(fill=tk.X, pady=2)

        # Video info section
        info_frame = ttk.Frame(container)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Title section (truncated for long titles)
        title = video.get('title', 'No title')[:60] + ('...' if len(video.get('title', '')) > 60 else '')
        ttk.Label(info_frame, text=f"{title}", font=('Arial', 10, 'bold')).pack(anchor='w')
        #ttk.Label(info_frame, text=f"Title: {title}", font=('Arial', 10, 'bold')).pack(anchor='w')

        # Channel name
        ttk.Label(info_frame, text=f"Channel: {video.get('uploader', 'Unknown channel')}").pack(anchor='w')

        # Format view count with appropriate suffix (k, M, B) to keeo stuff cool! huh
        view_count = video.get('view_count', 0)
        if view_count >= 1_000_000_000:  # Billions
            view_count_str = f"{view_count / 1_000_000_000:.1f}B"
            view_count_str = view_count_str.replace('.0B', 'B')
        elif view_count >= 1_000_000:  # Millions
            view_count_str = f"{view_count / 1_000_000:.1f}M"
            view_count_str = view_count_str.replace('.0M', 'M')
        elif view_count >= 1_000:  # Thousands
            view_count_str = f"{view_count / 1_000:.1f}k"
            view_count_str = view_count_str.replace('.0k', 'k')
        else:
            view_count_str = f"{view_count}" if view_count else 'N/A'

        # Duration section
        duration = int(video.get('duration', 0)) if video.get('duration') else 0
        if duration:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            
            if hours > 0:
                duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = 'N/A'

        ttk.Label(info_frame, text=f"Duration: {duration_str}").pack(anchor='w')
        ttk.Label(info_frame, text=f"Viewers: {view_count_str}").pack(anchor='w')
        video_frame.video_data = video
    #Thumbanail, or bunner of the video
    def download_thumbnail(self, thumbnail_url, label=None):
        if label is None:
            label = self.thumbnail_label            
        if not thumbnail_url:
            self.parent.after(0, lambda: label.config(text="No thumbnail", image=''))
            return            
        if "hqdefault" in thumbnail_url:
            thumbnail_url = thumbnail_url.replace("hqdefault", "maxresdefault")            
        if not thumbnail_url.startswith(('http://', 'https://')):
            self.parent.after(0, lambda: label.config(text="Invalid URL", image=''))
            return            
        img_data = None
        errors = []        
        try:
            response = requests.get(thumbnail_url, stream=True, timeout=10)
            response.raise_for_status()
            img_data = response.content
        except Exception as e:
            errors.append(f"Requests method failed: {str(e)}")            
        if img_data is None:
            try:
                with urllib.request.urlopen(thumbnail_url, timeout=10) as response:
                    img_data = response.read()
            except Exception as e:
                errors.append(f"Urllib method failed: {str(e)}")
        
        if img_data:
            try:
                
                img = Image.open(BytesIO(img_data))
                img.thumbnail((280, 130), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                if hasattr(self, 'thumbnail_images'):
                    self.thumbnail_images.append(photo)
                else:
                    self.thumbnail_image = photo                    
                self.parent.after(0, lambda: label.config(image=photo, text=""))
                return True
            except Exception as e:
                errors.append(f"Image processing failed: {str(e)}")
        
        error_msg = "; ".join(errors)
        self.parent.after(0, lambda: label.config(text="No thumbnail", image=''))
        return False

    #Hook to handle yt-dlp errors
    def yt_dlp_hook(self, d):
        if d['status'] == 'error':
            print(f"yt-dlp error: {d['error']}")
                      
    def create_download_button(self, url):
        self.status_label.config(text="Preparing download options...", foreground="blue")
        print(f"Creating download options for: {url}")
        
        # Extract valid URL and title if url is a dictionary
        title = None
        if isinstance(url, dict):
            valid_url = url.get('url', '')
            title = url.get('title', 'Download')  # Extract title from dictionary
            print(f"Extracted valid URL: {valid_url}")
            url = valid_url
        
        # Open format selection with title information
        self.open_format_selection_popup(url, title)

    def open_format_selection_popup(self, url, title=None):
        format_popup = tk.Toplevel(self.parent)
        format_popup.title("Download Options")
        format_popup.geometry("500x320")
        format_popup.resizable(False, False)
        
        # Make the popup modal (blocks interaction with main window)
        format_popup.transient(self.parent)
        format_popup.grab_set()
        
        # Center popup on parent window
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (500 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (320 // 2)
        format_popup.geometry(f"+{x}+{y}")
        
        # Create heading
        heading_label = ttk.Label(format_popup, text="Select Download Format", font=("Helvetica", 12, "bold"))
        heading_label.pack(pady=(15, 10))
        
        # Create a container frame for the title with left alignment
        title_frame = ttk.Frame(format_popup)
        title_frame.pack(fill=tk.X, padx=20, pady=(0, 10), anchor=tk.W)
        
        # Create title label with placeholder initially
        title_label = ttk.Label(title_frame, text="Title: Loading...", font=("Helvetica", 10))
        title_label.pack(side=tk.LEFT, anchor=tk.W)
        
        # Update title if already available
        if title:
            title_text = title if len(title) <= 55 else title[:52] + "..."
            title_label.config(text=f"Title: {title_text}")
        else:
            # Try to fetch title in background without blocking
            def fetch_title_thread():
                try:
                    ydl_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'skip_download': True,
                        'extract_flat': True,
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        fetched_title = info.get('title', 'Unknown Title')
                        
                        # Update title label in main thread
                        title_text = fetched_title if len(fetched_title) <= 55 else fetched_title[:52] + "..."
                        format_popup.after(0, lambda: title_label.config(text=f"Title: {title_text}"))
                except Exception as e:
                    # If there's an error, just show a generic title
                    format_popup.after(0, lambda: title_label.config(text="Title: Unable to retrieve"))
                    print(f"Error fetching title: {str(e)}")
            
            # Start title fetching in background
            threading.Thread(target=fetch_title_thread, daemon=True).start()
        
        # Create a container frame
        container = ttk.Frame(format_popup)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Media type selection frame
        media_type_frame = ttk.Frame(container)
        media_type_frame.pack(fill=tk.X, pady=5)
        
        video_format_options = [
            ("MP4 - Best Quality", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"),
            ("MP4 - 4K", "bestvideo[ext=mp4][height<=2160]+bestaudio[ext=m4a]/best[ext=mp4][height<=2160]/best"),
            ("MP4 - 1440p", "bestvideo[ext=mp4][height<=1440]+bestaudio[ext=m4a]/best[ext=mp4][height<=1440]/best"),
            ("MP4 - 1080p", "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best"),
            ("MP4 - 720p", "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best"),
            ("MP4 - 480p", "bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[ext=mp4][height<=480]/best"),
            ("MP4 - 360p", "bestvideo[ext=mp4][height<=360]+bestaudio[ext=m4a]/best[ext=mp4][height<=360]/best"),
            ("MP4 - 240p", "bestvideo[ext=mp4][height<=240]+bestaudio[ext=m4a]/best[ext=mp4][height<=240]/best"),
            ("MP4 - Smallest Size", "worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst"),
            ("WebM - Best Quality", "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best"),
            ("WebM - 1080p", "bestvideo[ext=webm][height<=1080]+bestaudio[ext=webm]/best[ext=webm][height<=1080]/best"),
            ("WebM - 720p", "bestvideo[ext=webm][height<=720]+bestaudio[ext=webm]/best[ext=webm][height<=720]/best"),
            ("WebM - 480p", "bestvideo[ext=webm][height<=480]+bestaudio[ext=webm]/best[ext=webm][height<=480]/best"),
            ("MKV - Best Quality", "bestvideo+bestaudio/best"),
            ("AVI - Best Quality", "bestvideo+bestaudio --merge-output-format avi"),
            ("FLV - Best Quality", "bestvideo+bestaudio --merge-output-format flv"),
            ("3GP - Mobile", "worst[ext=3gp]/worst --recode-video 3gp"),
            ("MP4 - Video Only", "bestvideo[ext=mp4]-bestaudio/bestvideo[ext=mp4]"),
            ("WebM - Video Only", "bestvideo[ext=webm]-bestaudio/bestvideo[ext=webm]")
        ]

        audio_format_options = [
            ("MP3 - 320kbps", "bestaudio/best -x --audio-format mp3 --audio-quality 320K"),
            ("MP3 - 256kbps", "bestaudio/best -x --audio-format mp3 --audio-quality 256K"),
            ("MP3 - 192kbps", "bestaudio/best -x --audio-format mp3 --audio-quality 192K"),
            ("MP3 - 128kbps", "bestaudio/best -x --audio-format mp3 --audio-quality 128K"),
            ("MP3 - 96kbps", "bestaudio/best -x --audio-format mp3 --audio-quality 96K"),
            ("M4A - Best Quality", "bestaudio/best -x --audio-format m4a --audio-quality 0"),
            ("M4A - Medium Quality", "bestaudio/best -x --audio-format m4a --audio-quality 2"),
            ("OGG - Best Quality", "bestaudio/best -x --audio-format vorbis --audio-quality 0"),
            ("OGG - Medium Quality", "bestaudio/best -x --audio-format vorbis --audio-quality 3"),
            ("OPUS - Best Quality", "bestaudio/best -x --audio-format opus --audio-quality 0"),
            ("FLAC - Lossless", "bestaudio/best -x --audio-format flac"),
            ("WAV - Uncompressed", "bestaudio/best -x --audio-format wav"),
            ("AAC - High Quality", "bestaudio/best -x --audio-format aac --audio-quality 0"),
            ("AIFF - Uncompressed", "bestaudio/best -x --audio-format aiff"),
            ("WMA - High Quality", "bestaudio/best -x --audio-format wma --audio-quality 0")
        ]
        
        # Subtitle language options
        subtitle_language_options = [
            ("English", "en"),
            ("German", "de"),
            ("Swahili", "sw"),
            ("Auto-generated (English)", "en-auto")
        ]
        
        # Variables for selections
        media_type_var = tk.StringVar(value="video")
        video_format_var = tk.StringVar(value=video_format_options[0][0])
        audio_format_var = tk.StringVar(value=audio_format_options[0][0])
        subtitle_var = tk.BooleanVar(value=False)  # New variable for subtitle checkbox
        subtitle_lang_var = tk.StringVar(value=subtitle_language_options[0][0])  # Language selection
        
        # Function to update dropdown visibility based on media type
        def update_dropdown_visibility():
            if media_type_var.get() == "video":
                video_dropdown.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
                audio_dropdown.pack_forget()
                format_label.config(text="Video Format:")
                subtitle_frame.pack(fill=tk.X, pady=5)  # Show subtitle option for video
            else:
                audio_dropdown.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
                video_dropdown.pack_forget()
                format_label.config(text="Audio Format:")
                subtitle_frame.pack_forget()  # Hide subtitle option for audio
        
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
        
        # Subtitle 
        subtitle_frame = ttk.Frame(container)
        subtitle_check = ttk.Checkbutton(
            subtitle_frame,
            text="Download subtitles:",
            variable=subtitle_var
        )
        subtitle_check.pack(side=tk.LEFT, padx=(0, 10))        
        # Subtitle language dropdown
        subtitle_lang_dropdown = ttk.Combobox(
            subtitle_frame,
            textvariable=subtitle_lang_var,
            values=[x[0] for x in subtitle_language_options],
            state="readonly",
            width=20
        )
        subtitle_lang_dropdown.pack(side=tk.LEFT)
        update_dropdown_visibility()
        path_frame = ttk.Frame(container)
        path_frame.pack(fill=tk.X, pady=10)        
        path_label = ttk.Label(path_frame, text="Save to:")
        path_label.pack(side=tk.LEFT)
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
        
        # Browse Button
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
                    # Get the base format string and add subtitle command if needed for video though
                    video_format_options[[x[0] for x in video_format_options].index(video_format_var.get())][1] + 
                    (f" --write-subs --sub-lang {get_subtitle_lang()}" if media_type_var.get() == 'video' and subtitle_var.get() else "") 
                    if media_type_var.get() == "video"
                    else audio_format_options[[x[0] for x in audio_format_options].index(audio_format_var.get())][1],
                    path_var.get()
                )
            ]
        )
        download_button.pack(side=tk.RIGHT, padx=5)
        
        # Helper function to get subtitle language code based on selection
        def get_subtitle_lang():
            selected_lang = subtitle_lang_var.get()
            for lang_name, lang_code in subtitle_language_options:
                if lang_name == selected_lang:
                    # Special handling for auto-generated
                    if lang_code == "en-auto":
                        return "en --write-auto-sub"
                    return lang_code
            return "en"  # Default to English if other language not found
        
    #Start the download process with the selected format options   
    def start_download(self, url, format_string, output_path):
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        if isinstance(url, dict):
            print("start_download: Received URL as a dict. Extracting string from key 'url'.")
            url_str = url.get('url', '')
            print(f"start_download: Extracted URL: {url_str}")
            url = url_str
        else:
            print("start_download: Received URL as a string.")
        
        # Adding prints, i was confused so just added for debugging
        print(f"start_download: URL = {url}")
        print(f"start_download: Selected format string = {format_string}")
        print(f"start_download: Output path = {output_path}")
        self.status_label.config(text="Starting download...", foreground="blue") #Update in UI
        self.progress['value'] = 0
        
        # Reset cancel flag before starting new download
        self.cancel_requested = False
        self.download_cancelled = False
        
        # Enable cancel button
        if hasattr(self, 'cancel_button'):
            self.cancel_button.config(state=tk.NORMAL)
        
        # Start download in a thread to keep UI responsive
        download_thread = threading.Thread(
            target=self.download_thread,
            args=(url, format_string, output_path)  # Now URL is a string
        )
        download_thread.daemon = True
        download_thread.start()

    #Update the progress bar and status label with download progress
    def update_download_progress(self, d):
        if hasattr(self, 'cancel_requested') and self.cancel_requested:
            raise Exception("Download cancelled by user")
            
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)            
            # Get filename information
            filename = d.get('filename', '').split('/')[-1].split('\\')[-1]  # Extract just the filename
            if len(filename) > 30:  # Truncate if too long
                filename = filename[:27] + "..."
            
            # Calculate percentage if total size is known
            if total > 0:
                percentage = (downloaded / total) * 100
                percent_text = f"{percentage:.1f}%"                
                downloaded_mb = downloaded / 1024 / 1024
                total_mb = total / 1024 / 1024
                size_text = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB"                
                self.progress['value'] = percentage                
                download_speed = d.get('speed', 0)
                if download_speed:
                    speed_text = f"{download_speed / 1024 / 1024:.2f} MB/s"
                    status_text = f"Downloading: {filename} - {percent_text} ({size_text}) at {speed_text}"
                else:
                    status_text = f"Downloading: {filename} - {percent_text} ({size_text})"
                    
                # Update the status label with proper font handling
                self.status_label.config(text=status_text)
                
                # Forcing update of the UI, Hah to show that im serios
                self.status_label.update_idletasks()
                self.progress.update_idletasks()
            else:
                downloaded_mb = downloaded / 1024 / 1024
                self.status_label.config(text=f"Downloading: {filename} - {downloaded_mb:.1f} MB (size unknown)")
        
        elif d['status'] == 'finished':
            # Get filename information for the completed download
            filename = d.get('filename', '').split('/')[-1].split('\\')[-1]
            self.status_label.config(text=f"Download of {filename} finished. Processing file...", foreground="blue")
            self.progress['value'] = 0
            self.progress.update_idletasks()

    def cancel_download(self):
        print("Cancel download requested")
        self.cancel_requested = True
        self.download_cancelled = True
        self.status_label.config(text="Cancelling download...", foreground="orange")
        
        # Disable the cancel button to prevent multiple cancellations
        if hasattr(self, 'cancel_button'):
            self.cancel_button.config(state=tk.DISABLED)

    def download_thread(self, url, format_string, output_path):
        try:
            # Update status to show initial download preparation
            self.parent.after(0, lambda: self.status_label.config(text=f"Preparing to download from {url}...", foreground="black"))
            
            # Base options for yt-dlp
            ydl_opts = {
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.update_download_progress],
                'verbose': True,  # Debug info enabled 
                'quiet': False,   # Debug info enabled ,just similar to explanation above
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
            
            # Extract video info first to get the title
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get('title', 'Unknown Title')
                self.parent.after(0, lambda: self.status_label.config(text=f"Starting download: {video_title}", foreground="black"))
            
            # Check if user cancelled during info extraction
            if hasattr(self, 'cancel_requested') and self.cancel_requested:
                self.parent.after(0, lambda: self.status_label.config(text="Download cancelled by user.", foreground="orange"))
                self.parent.after(0, lambda: self.progress.config(value=0))
                # Disable the cancel button
                if hasattr(self, 'cancel_button'):
                    self.parent.after(0, lambda: self.cancel_button.config(state=tk.DISABLED))
                # Reset the cancel flag
                self.cancel_requested = False
                return  # Exit download_thread without calling on_download_complete
                
            # Execute the download with yt-dlp, passing a list containing the URL string
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            # If we get here, download completed successfully
            self.parent.after(0, self.on_download_complete)
                
        except Exception as e:
            if str(e) == "Download cancelled by user":
                # Handle cancellation gracefully
                self.parent.after(0, lambda: self.status_label.config(text="Download cancelled by user.", foreground="orange"))
                self.parent.after(0, lambda: self.progress.config(value=0))
                # Disable the cancel button
                if hasattr(self, 'cancel_button'):
                    self.parent.after(0, lambda: self.cancel_button.config(state=tk.DISABLED))
                # Reset the cancel flag
                self.cancel_requested = False
            else:
                error_msg = f"Error downloading from {url}: {str(e)}"
                # Use after() to safely update UI from a thread
                self.parent.after(0, lambda: self.status_label.config(text=error_msg, foreground="red"))
                # Call on_download_complete for non-cancellation errors
                self.parent.after(0, self.on_download_complete)
            
            print(f"Download error: {str(e)}")

    def on_download_complete(self):
        if not hasattr(self, 'download_cancelled') or not self.download_cancelled:
            self.status_label.config(text="Download complete! Ready for next download.", foreground="green")
            self.progress['value'] = 100
            self.parent.bell()  # Simple bell sound
        else:
            self.progress['value'] = 0
        
        # Reset the cancel flag
        self.cancel_requested = False
        self.download_cancelled = False
        
        # Disable the cancel button
        if hasattr(self, 'cancel_button'):
            self.cancel_button.config(state=tk.DISABLED)
        
        # Force update of the UI
        self.status_label.update_idletasks()
        self.progress.update_idletasks()
################################################################################33

    def _format_time(self, seconds):
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds//60:.0f}m {seconds%60:.0f}s"
        else:
            return f"{seconds//3600:.0f}h {(seconds%3600)//60:.0f}m"
    #in future we could program its own player!
    def play_video(self, url):
        if url:
            webbrowser.open(url)


if __name__ == "__main__":
    parent = tk.Tk()
    parent.title("Home")
    parent.geometry("800x600")    
    app = HomeGui(parent)
    app.pack(fill=tk.BOTH, expand=True)
    parent.mainloop()
