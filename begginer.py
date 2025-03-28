import yt_dlp
import threading
import webbrowser
import requests
from io import BytesIO
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
import re
import os
import pyperclip  # Make sure you have this installed with `pip install pyperclip`
import urllib.request

class BeginnerDownloaderGUI(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.thumbnail_images = []
        self.downloader_thread = None
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

        self.cancel_button = ttk.Button(search_frame, text="X Cancel", command=self.cancel_download, state=tk.DISABLED)
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

    def search_engine(self):
        query = self.search_entry.get().strip()
        if not query:
            return

        # Clear previous results
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.thumbnail_images.clear()

        # Check if it's a URL
        if re.match(r'https?://', query):
            self.process_url(query)
        else:
            self.search_youtube(query)
    
    def process_url(self, url):
        """Detect if the URL is a playlist and process accordingly."""
        if "list=" in url:
            print("Playlist detected! Processing as a playlist...")
            # You can integrate your `fetch_and_update` function here
        else:
            print("Single video detected! Processing...")
            self.fetch_video_info(url)
            self.create_download_button(url)
    
    def fetch_video_info(self, url):
        """Fetch video information for a single video."""
        try:
            ydl_opts = {'quiet': True, 'noplaylist': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                print(f"Title: {info.get('title', 'Unknown')}")
                print(f"Uploader: {info.get('uploader', 'Unknown')}")
        except Exception as e:
            print(f"Error fetching video info: {e}")

    
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
                        self.parent.after(0, lambda: self.status_label.config(
                            text="No results found", 
                            foreground="red"
                        ))
                        return

                    self.parent.after(0, lambda: self.status_label.config(text=""))
                    
                    for i, video in enumerate(search_results['entries']):
                        if not video:
                            continue
                            
                        # Schedule UI updates in main thread
                        self.parent.after(0, self.create_video_item, video, i)

            except Exception as e:
                self.parent.after(0, lambda: self.status_label.config(
                    text=f"Error: {str(e)}", 
                    foreground="red"
                ))

        # Start search in background thread
        threading.Thread(target=search, daemon=True).start()

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
                
    def create_download_button(self, url):
        """Create a download button for the video with format options."""
        print("Create download options for URL:", url)
        # Placeholder function to add download options for video formats (MP3, MP4, WebM)
        # You would need to add logic for fetching the available formats for download.

    def paste_from_clipboard(self):
        """Paste URL from clipboard to search bar."""
        clipboard_text = pyperclip.paste()
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

    def update_progress(self, current, total):
        """Update the progress bar based on the download progress."""
        progress = (current / total) * 100
        self.progress['value'] = progress
        self.status_label.config(text=f"Downloading... {progress:.2f}%")
        self.parent.update_idletasks()

    def complete_download(self):
        """Called when the download completes."""
        self.status_label.config(text="Download Complete")
        self.progress['value'] = 100

    def cancel_download(self):
        """Cancel the ongoing download."""
        if self.downloader_thread:
            print("Download canceled")
            self.downloader_thread.cancel()
            self.cancel_button.config(state=tk.DISABLED)
            self.status_label.config(text="Download Canceled")
            self.progress['value'] = 0

if __name__ == "__main__":
    parent = tk.Tk()
    parent.title("Beginner Downloader")
    parent.geometry("800x600")
    
    app = BeginnerDownloaderGUI(parent)
    app.pack(fill=tk.BOTH, expand=True)
    parent.mainloop()
