import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import yt_dlp
import os
import threading
import time
import subprocess
import platform
import datetime
import functools

#GUI stuff start here
class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Any Video Downloader")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.root.minsize(920, 450)
        self.fetch_cancelled = False

        self.sort_state = {
            "format_tree": {"column": "resolution", "direction": "asc"},
            "downloads_tree": {"column": "date", "direction": "desc"}
        }

        # putting cool theme
        self.root.configure(background="#F8F9FA")  # Soft light gray

        # Setting theme and styles
        self.style = ttk.Style()
        self.style.theme_use("clam")  # Modern flat theme

        # Buttons - Smaller Size with Teal-Blue Color
        self.style.configure("TButton",
                             background="#009688",  # Teal
                             foreground="white",  
                             font=("Arial", 9, "bold"),  # Smaller font
                             borderwidth=0,
                             padding=5,  # Reduced padding for smaller buttons
                             relief="flat")
        self.style.map("TButton",
                       background=[("active", "#00796B")],  # Darker teal on hover
                       relief=[("pressed", "ridge")])

        # Labels - Minimalist Dark Gray for Cool Look
        self.style.configure("TLabel",
                             background="#F8F9FA",
                             foreground="#333333",  # Dark gray
                             font=("Arial", 9, "bold"))  # font stuff

        # Notebook (Tabs) - Soft Blue with Rounded Tabs
        self.style.configure("TNotebook", background="#F8F9FA", borderwidth=0)
        self.style.configure("TNotebook.Tab",
                             background="#E0E0E0",
                             foreground="#333333",
                             font=("Arial", 9, "bold"),  # Adjusted font size
                             padding=[8, 3])  # Reduced padding for smaller tabs
        self.style.map("TNotebook.Tab",
                       background=[("selected", "#009688")],  # Teal this goes for active tab
                       foreground=[("selected", "white")])

        # Treeview (Table) - White Background with Aqua Headers
        self.style.configure("Treeview",
                             background="white",
                             fieldbackground="white",
                             foreground="#333333",
                             font=("Arial", 9)) 
        self.style.configure("Treeview.Heading",
                             font=("Arial", 9, "bold"),  
                             background="#00796B",  # Dark Teal color
                             foreground="white")

        # Progressbar - Bright Green inspired by windows copying bar
        self.style.configure("TProgressbar", background="#4CAF50")

        # Entries - Compact White Input Fields
        self.style.configure("TEntry",
                             background="white",
                             foreground="#333333",
                             padding=5,  # Reduced padding for smaller input fields
                             font=("Arial", 9),
                             relief="solid",
                             borderwidth=1)

        # Frames - Subtle Light Gray color
        self.style.configure("TFrame", background="#F8F9FA")

        # Radiobuttons - flat style
        self.style.configure("TRadiobutton",
                             background="#F8F9FA",
                             foreground="#333333",
                             font=("Arial", 9))  # Adjusted font size

        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create main tab
        self.main_tab = ttk.Frame(self.notebook)
        self.verbose_tab = ttk.Frame(self.notebook)
        self.downloads_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.main_tab, text="Main")
        self.notebook.add(self.verbose_tab, text="Log")
        self.notebook.add(self.downloads_tab, text="Downloads")
        
        # Set up the main frame
        self.setup_main_tab()
        self.setup_verbose_tab()
        self.setup_downloads_tab()
        
        # Store video info
        self.video_info = None
        self.formats = []
        self.downloaded_files = []
        self.current_download_path = None
        
        # Sorting state for treeviews
        self.sort_state = {
            "format_tree": {"column": None, "direction": None},
            "downloads_tree": {"column": None, "direction": None}
        }
        
        # Logging system
        self.log_level = "INFO"  # Can be INFO, DEBUG, or ERROR
        
        # Log first message
        self.log("Application started", "INFO")

    def setup_main_tab(self):
        """Set up the main tab with all the primary controls"""
        # Create a main container frame with height management
        main_frame = ttk.Frame(self.main_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top frame for URL and media type.
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 5), ipady=5)
        
        # URL input with quick paste button
        # URL input with quick paste button
        # URL input with quick paste button
        url_frame = ttk.Frame(top_frame)
        url_frame.pack(fill=tk.X, pady=(0, 5))
        url_frame.columnconfigure(1, weight=1)

        ttk.Label(url_frame, text="Video URL:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=5)

        self.url_entry = ttk.Entry(url_frame, width=70, font=("Helvetica", 10))
        self.url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        paste_button = ttk.Button(url_frame, text="Paste", width=5, command=self.paste_from_clipboard)
        paste_button.pack(side=tk.LEFT, padx=2)

        fetch_button = ttk.Button(url_frame, text="Fetch Info", command=self.fetch_video_info)
        fetch_button.pack(side=tk.LEFT, padx=5)

        cancel_button = ttk.Button(url_frame, text="X", width=2, command=self.cancel_fetch)
        cancel_button.pack(side=tk.LEFT, padx=2)

        # Set placeholder AFTER self.url_entry is created
        self.set_placeholder()

        # Bind events for placeholder behavior
        self.url_entry.bind("<FocusIn>", self.clear_placeholder)
        self.url_entry.bind("<FocusOut>", self.restore_placeholder)

        
        # Media type selection
        type_frame = ttk.LabelFrame(top_frame, text="Media Type")
        type_frame.pack(fill=tk.X, pady=5)
        
        self.media_type = tk.StringVar(value="video")
        ttk.Radiobutton(type_frame, text="Video", variable=self.media_type, value="video", command=self.update_format_list).pack(side=tk.LEFT, padx=20, pady=5)
        ttk.Radiobutton(type_frame, text="Audio only", variable=self.media_type, value="audio", command=self.update_format_list).pack(side=tk.LEFT, padx=20, pady=5)
        
        # Video info section.
        info_frame = ttk.LabelFrame(main_frame, text="Video Information")
        info_frame.pack(fill=tk.X, pady=1, ipady=5)
        
        # The container to hold info and thumbnail pic side by side.
        container = ttk.Frame(info_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=1)
        
        # Left side - Video info
        info_grid = ttk.Frame(container)
        info_grid.columnconfigure(1, weight=1)
        info_grid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.video_title_var = tk.StringVar(value="")
        self.video_duration_var = tk.StringVar(value="")
        self.video_channel_var = tk.StringVar(value="")
        
        ttk.Label(info_grid, text="Title:", font=("Helvetica", 9, "bold")).grid(row=0, column=0, sticky=tk.W, padx=3, pady=1)
        ttk.Label(info_grid, textvariable=self.video_title_var, wraplength=500).grid(row=0, column=1, sticky=tk.W, padx=3, pady=1)
        
        ttk.Label(info_grid, text="Duration:", font=("Helvetica", 9, "bold")).grid(row=1, column=0, sticky=tk.W, padx=3, pady=1)
        ttk.Label(info_grid, textvariable=self.video_duration_var).grid(row=1, column=1, sticky=tk.W, padx=3, pady=1)
        
        ttk.Label(info_grid, text="Channel:", font=("Helvetica", 9, "bold")).grid(row=2, column=0, sticky=tk.W, padx=3, pady=1)
        ttk.Label(info_grid, textvariable=self.video_channel_var).grid(row=2, column=1, sticky=tk.W, padx=3, pady=1)
        
        # Right side - Video thumbnail (smaller).
        thumbnail_frame = ttk.Frame(container, width=160, height=90)  # Reduced size
        thumbnail_frame.pack(side=tk.RIGHT, padx=(20, 5), pady=1)
        thumbnail_frame.pack_propagate(False)  # Maintain the size
        
        self.thumbnail_label = ttk.Label(thumbnail_frame, text="No thumbnail available")
        self.thumbnail_label.pack(fill=tk.BOTH, expand=True)
        self.thumbnail_label.bind("<Button-1>", self.play_video)
        
        play_button = ttk.Button(container, text="▶ Play", width=8, command=self.play_video)
        play_button.pack(side=tk.RIGHT, padx=3, pady=1, anchor=tk.S)
        
        # Format selection. after loading they all displayed here!
        format_frame = ttk.LabelFrame(main_frame, text="Available Formats")
        format_frame.pack(fill=tk.BOTH, expand=True, pady=1)
        
        # Create a frame for the treeview and scrollbar
        tree_frame = ttk.Frame(format_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=1)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        #Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        #Treeview for formats
        self.format_tree = ttk.Treeview(tree_frame, columns=("format_id", "extension", "resolution", "filesize", "note"), 
                                       show="headings", yscrollcommand=scrollbar.set)
        self.format_tree.grid(row=0, column=0, sticky="nsew")
        
        #Configure scrollbar
        scrollbar.config(command=self.format_tree.yview)
        
        #Configure column headings with sort functionality
        for col in ["format_id", "extension", "resolution", "filesize", "note"]:
            self.format_tree.heading(col, text=self.get_column_title(col), 
                                   command=lambda c=col: self.sort_treeview(self.format_tree, c, "format_tree"))
        
        #Configure column widts
        self.format_tree.column("format_id", width=80, minwidth=60)
        self.format_tree.column("extension", width=80, minwidth=60)
        self.format_tree.column("resolution", width=150, minwidth=100)
        self.format_tree.column("filesize", width=100, minwidth=80)
        self.format_tree.column("note", width=300, minwidth=150)
        
        # Enabling Double-click to select and download
        self.format_tree.bind("<Double-1>", lambda e: self.start_download())
        
        #Bottom section. Here goes download controls, progress, etc.
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=1)
        
        #Download path section
        download_frame = ttk.Frame(bottom_frame)
        download_frame.pack(fill=tk.X, pady=5)
        download_frame.columnconfigure(1, weight=1)
        
        ttk.Label(download_frame, text="Save to:", font=("Helvetica", 9, "bold")).grid(row=0, column=0, padx=5, sticky=tk.W)
        self.save_path_entry = ttk.Entry(download_frame, font=("Helvetica", 9))
        self.save_path_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)
        
        # Set default save path to Downloads folder
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.save_path_entry.insert(0, downloads_path)
        
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
        
        download_button = ttk.Button(button_frame, text="Download", command=self.start_download)
        download_button.pack(side=tk.LEFT, padx=5)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel_download)
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        self.download_thread = None
        self.cancel_flag = False
    #Verbose tab section goes here!    
    def setup_verbose_tab(self):
        """Set up the verbose log tab"""
        log_frame = ttk.Frame(self.verbose_tab, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        #Log level selection
        level_frame = ttk.Frame(log_frame)
        level_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(level_frame, text="Log Level:").pack(side=tk.LEFT, padx=5)
        
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(level_frame, textvariable=self.log_level_var, 
                                     values=["INFO", "DEBUG", "ERROR"], width=10, state="readonly")
        log_level_combo.pack(side=tk.LEFT, padx=5)
        log_level_combo.bind("<<ComboboxSelected>>", lambda e: self.set_log_level(self.log_level_var.get()))
        
        clear_button = ttk.Button(level_frame, text="Clear Log", command=self.clear_log)
        clear_button.pack(side=tk.RIGHT, padx=5)

        # Log text area
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_text_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Configure text tags and color for different log levels.
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("DEBUG", foreground="blue")
        self.log_text.tag_configure("ERROR", foreground="red")
    #Downloads tab start here
    def setup_downloads_tab(self):
        """Set up the downloads history tab with video player"""
        downloads_frame = ttk.Frame(self.downloads_tab, padding="10")
        downloads_frame.pack(fill=tk.BOTH, expand=True)
        
        # Split into two sections - downloads list and preview
        paned_window = ttk.PanedWindow(downloads_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Downloads list
        list_frame = ttk.Frame(paned_window)
        paned_window.add(list_frame, weight=40)
        
        ttk.Label(list_frame, text="Downloaded Files").pack(fill=tk.X, pady=5)
        
        # Treeview for downloads
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.downloads_tree = ttk.Treeview(tree_frame, columns=("filename", "date", "size"), 
                                        show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.downloads_tree.yview)
        
        # Configure column headings with sort functionality
        for col in ["filename", "date", "size"]:
            self.downloads_tree.heading(col, text=self.get_column_title(col), 
                                    command=lambda c=col: self.sort_treeview(self.downloads_tree, c, "downloads_tree"))
        
        self.downloads_tree.column("filename", width=200)
        self.downloads_tree.column("date", width=120)
        self.downloads_tree.column("size", width=80)
        
        self.downloads_tree.pack(fill=tk.BOTH, expand=True)
        self.downloads_tree.bind("<<TreeviewSelect>>", self.on_download_selected)
        
        # Add double-click binding to play files
        self.downloads_tree.bind("<Double-1>", lambda event: self.play_selected_file())
        
        # Create right-click context menu
        self.context_menu = tk.Menu(self.downloads_tree, tearoff=0)
        self.context_menu.add_command(label="Play", command=self.play_selected_file)
        self.context_menu.add_command(label="Delete", command=self.delete_selected_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Open containing folder", command=self.open_containing_folder)
        
        # Bind right-click event
        self.downloads_tree.bind("<Button-3>", self.show_context_menu)
        
        # Buttons for download management
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        open_button = ttk.Button(button_frame, text="Play", command=self.play_selected_file)
        open_button.pack(side=tk.LEFT, padx=5)
        
        open_folder_button = ttk.Button(button_frame, text="Open Folder", command=self.open_containing_folder)
        open_folder_button.pack(side=tk.LEFT, padx=5)
        
        delete_button = ttk.Button(button_frame, text="Delete", command=self.delete_selected_file)
        delete_button.pack(side=tk.LEFT, padx=5)
        
        refresh_button = ttk.Button(button_frame, text="Refresh", command=self.refresh_downloads_list)
        refresh_button.pack(side=tk.RIGHT, padx=5)
        
        # Right panel - Preview
        preview_frame = ttk.LabelFrame(paned_window, text="File Preview")
        paned_window.add(preview_frame, weight=60)
        
        # File info
        self.preview_info_var = tk.StringVar(value="Select a file to preview")
        ttk.Label(preview_frame, textvariable=self.preview_info_var, wraplength=300).pack(pady=10)        
    #adding some
    def show_context_menu(self, event):
        """Show the context menu on right-click"""
        # Select the item under the cursor first
        item = self.downloads_tree.identify_row(event.y)
        if item:
            self.downloads_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    # To keep simple for now. but can be extended to use imported mediaplayer.py so as to have biult in player.
    #Paste from clipboard
    def paste_from_clipboard(self):
        """Paste clipboard content to URL entry with double quotes and handle placeholder"""
        try:
            clipboard_text = self.root.clipboard_get().strip()
            if clipboard_text:
                formatted_url = f'{clipboard_text}'  # Enclose in double quotes
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, formatted_url)
                self.url_entry.config(foreground="black")  # Reset text color
                self.log(f'Pasted URL from clipboard: {formatted_url}', "DEBUG")
            else:
                self.set_placeholder()  # Restore placeholder if clipboard is empty
        except Exception as e:
            self.log(f"Failed to paste from clipboard: {str(e)}", "ERROR")
            self.set_placeholder()  # Restore placeholder on error

    def set_placeholder(self):
        """Set placeholder text when the entry is empty"""
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, "Hit Ctrl+V to paste or click the paste button")
        self.url_entry.config(foreground="gray")  # Make it visually distinct

    def clear_placeholder(self, event):
        """Clear placeholder when user focuses on entry"""
        if self.url_entry.get() == "Hit Ctrl+V to paste":
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(foreground="black")

    def restore_placeholder(self, event):
        """Restore placeholder if entry is empty when losing focus"""
        if not self.url_entry.get():
            self.set_placeholder()

    #This are information fetched from video url
    def get_column_title(self, column):
        """Get column title with sort indicator"""
        titles = {
            "format_id": "Format ID",
            "extension": "Extension",
            "resolution": "Resolution/Quality",
            "filesize": "File Size",
            "note": "Notes",
            "filename": "Filename",
            "date": "Date",
            "size": "Size"
        }
        
        # Check which treeview the column belongs to
        if column in ["format_id", "extension", "resolution", "filesize", "note"]:
            treeview_key = "format_tree"
        else:
            treeview_key = "downloads_tree"
            
        # Add sort indicator if this column is sorted
        if self.sort_state[treeview_key]["column"] == column:
            if self.sort_state[treeview_key]["direction"] == "asc":
                return f"{titles[column]} ↑"
            else:
                return f"{titles[column]} ↓"
        return titles[column]

    def sort_treeview(self, treeview, column, treeview_key):
        """Sort treeview by column with ascending/descending toggle"""
        # Get all items
        items = [(treeview.set(item, column), item) for item in treeview.get_children('')]
        
        # Update sort state
        if self.sort_state[treeview_key]["column"] == column:
            # Toggle direction if already sorting by this column
            self.sort_state[treeview_key]["direction"] = "desc" if self.sort_state[treeview_key]["direction"] == "asc" else "asc"
        else:
            # New column, default to ascending
            self.sort_state[treeview_key]["column"] = column
            self.sort_state[treeview_key]["direction"] = "asc"
        
        # Update all column headings to show sort indicator
        for col in treeview["columns"]:
            treeview.heading(col, text=self.get_column_title(col))
        
        # Determine sort direction
        reverse = self.sort_state[treeview_key]["direction"] == "desc"
        
        # Special case for filesize and size columns
        if column in ["filesize", "size"]:
            # Convert file sizes to comparable numbers
            def parse_filesize(size_str):
                if not size_str:
                    return 0
                
                try:
                    if isinstance(size_str, (int, float)):
                        return float(size_str)
                    
                    size_str = size_str.lower()
                    if 'mb' in size_str:
                        return float(size_str.replace('mb', '').strip()) * 1024 * 1024
                    elif 'kb' in size_str:
                        return float(size_str.replace('kb', '').strip()) * 1024
                    elif 'gb' in size_str:
                        return float(size_str.replace('gb', '').strip()) * 1024 * 1024 * 1024
                    else:
                        return float(size_str.strip())
                except:
                    return 0
            
            items = [(parse_filesize(item[0]), item[1]) for item in items]
        
        # Special case for date column
        elif column == "date":
            # Convert date strings to datetime objects
            def parse_date(date_str):
                try:
                    return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                except:
                    return datetime.datetime.min
            
            items = [(parse_date(item[0]), item[1]) for item in items]
        
        # Sort the items
        items.sort(reverse=reverse)
        
        # Rearrange items in the tree
        for index, (_, item) in enumerate(items):
            treeview.move(item, '', index)
        
        self.log(f"Sorted {treeview_key} by {column} ({self.sort_state[treeview_key]['direction']})", "DEBUG")

    #fetching video information like duration, cahnnel etc.. start here
    def fetch_video_info(self):
        """Fetch video information and thumbnail"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid video URL")
            return

        self.log(f"Fetching info for URL: {url}", "INFO")

        # Clear previous info
        self.video_info = None
        self.formats = []
        self.video_title_var.set("")
        self.video_duration_var.set("")
        self.video_channel_var.set("")
        self.clear_thumbnail()

        # Show loading indicator
        self.set_loading_state(True)

        def fetch_and_update():
            try:
                self._fetch_info_thread(url)
            except Exception as e:
                self.log(f"Error fetching info: {e}", "ERROR")
            finally:
                self.set_loading_state(False)  # Ensure loading state resets

        # Use a thread to prevent freezing the GUI
        self.fetch_thread = threading.Thread(target=fetch_and_update, daemon=True)
        self.fetch_cancelled = False  # Reset cancellation flag
        self.fetch_thread.start()

        # Start a timer to check for timeouts, so that they can be logged
        self.check_fetch_timeout(self.fetch_thread, 15)
    #cancel fecthing
    def cancel_fetch(self):
        """Cancel any ongoing fetch operations"""
        # Set a flag to indicate cancellation
        self.fetch_cancelled = True
        
        # Update the UI
        self.set_loading_state(False)
        self.status_label.config(text="Operation cancelled")
        self.log("Fetch operation cancelled by user", "INFO")
        
        # Clear partial data
        if hasattr(self, 'fetch_thread') and self.fetch_thread.is_alive():
            # Note: Python threads can't be forcibly terminated,
            # but we can use a flag to signal the thread to stop
            self.log("Signaling fetch thread to stop", "DEBUG")
    def check_fetch_timeout(self, thread, timeout):
        """Check if the fetch operation is taking too long"""
        if thread.is_alive() and timeout > 0:
            # Still running, check again in 1 second
            self.root.after(1000, lambda: self.check_fetch_timeout(thread, timeout - 1))
        elif thread.is_alive() and timeout <= 0:
            # Timed out
            self.log("Fetch operation taking longer than expected. Still working...", "INFO")
            # We don't kill the thread, just inform the user it's taking longer
            self.status_label.config(text="Fetching taking longer than expected...")
            # Check again with a longer interval
            self.root.after(5000, lambda: self.check_fetch_timeout(thread, 0))

    def _fetch_video_info_thread(self, url):
        """Thread function to fetch video info without blocking UI"""
        try:
            # Set up yt-dlp options
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Could not retrieve video information"))
                    self.root.after(0, lambda: self.set_loading_state(False))
                    return
                
                self.video_info = info
                
                # Update UI in the main thread
                self.root.after(0, self.update_video_info)
                
                # Download thumbnail in the background
                self.download_thumbnail(info.get('thumbnail'))
        
        except Exception as e:
            self.log(f"Error fetching video info: {str(e)}", "ERROR")
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {str(e)}"))
            self.root.after(0, lambda: self.set_loading_state(False))
    
    def _fetch_info_thread(self, url):
        """Background thread for fetching video info."""
        start_time = time.time()
        try:
            # Check if operation was cancelled before starting
            if self.fetch_cancelled:
                self.log("Fetch cancelled before starting", "INFO")
                return
                
            # Setup yt-dlp options
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            # Create YoutubeDL object with options
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Check cancellation before expensive operation
                if self.fetch_cancelled:
                    self.log("Fetch cancelled before extraction", "INFO")
                    return
                    
                # Extract information about the video
                self.video_info = ydl.extract_info(url, download=False)
                
                # Check cancellation after extraction
                if self.fetch_cancelled:
                    self.log("Fetch cancelled after extraction", "INFO")
                    self.video_info = None
                    return
                
                # Process the formats if we have video info
                if self.video_info:
                    self.formats = self.video_info.get('formats', [])
                    
                    # Check cancellation before UI update
                    if self.fetch_cancelled:
                        self.log("Fetch cancelled before UI update", "INFO")
                        self.video_info = None
                        self.formats = []
                        return
                    
                    # Update the UI in the main thread
                    self.root.after(0, self.update_format_list)
                    self.root.after(0, self.update_video_info)
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"Found {len(self.formats)} formats"))
                    
                    # Log completion time
                    elapsed = time.time() - start_time
                    self.log(f"Fetch completed in {elapsed:.2f} seconds", "DEBUG")
                else:
                    # Handle case where no video info was returned
                    if not self.fetch_cancelled:
                        self.root.after(0, lambda: messagebox.showerror(
                            "Error", "No video information found. Check the URL and try again."))
                        self.root.after(0, lambda: self.status_label.config(
                            text="No video information found"))
                        self.log("No video information returned", "ERROR")
        
        except Exception as e:
            # Only show error if not cancelled
            if not self.fetch_cancelled:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", f"Failed to fetch video info: {str(e)}"))
                self.root.after(0, lambda: self.status_label.config(
                    text="Error fetching information"))
                self.log(f"Error fetching video info: {str(e)}", "ERROR")
        
        finally:
            # Reset loading state if not cancelled (cancelled will handle this itself)
            if not self.fetch_cancelled:
                self.root.after(0, lambda: self.set_loading_state(False))
    def update_video_info(self):
        """Update the video information display"""
        if not self.video_info:
            return
            
        # Set video title
        title = self.video_info.get('title', 'Unknown title')
        self.video_title_var.set(title)
        
        # Format duration
        duration_secs = self.video_info.get('duration', 0)
        if duration_secs:
            minutes, seconds = divmod(int(duration_secs), 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = "Unknown"
        self.video_duration_var.set(duration_str)
        
        # Set channel name
        channel = self.video_info.get('channel', self.video_info.get('uploader', 'Unknown channel'))
        self.video_channel_var.set(channel)
        
        # Update thumbnail if available
        thumbnail_url = self.video_info.get('thumbnail')
        if thumbnail_url:
            threading.Thread(target=self.download_thumbnail, args=(thumbnail_url,), daemon=True).start()
        else:
            self.clear_thumbnail()
       
        self.log(f"Video info updated: {title} ({duration_str})", "DEBUG")

    def download_thumbnail(self, thumbnail_url):
        """Download and display the video thumbnail"""
        if not thumbnail_url:
            self.root.after(0, self.clear_thumbnail)
            return
        
        try:
            # Import required libraries here to avoid import issues
            import urllib.request
            from PIL import Image, ImageTk
            import io
            
            # Download the thumbnail
            with urllib.request.urlopen(thumbnail_url) as response:
                thumbnail_data = response.read()
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(thumbnail_data))
            
            # Resize to fit the frame
            image = image.resize((320, 180), Image.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Update the thumbnail label in the main thread
            self.thumbnail_image = photo  # Keep a reference to prevent garbage collection
            self.root.after(0, lambda: self.thumbnail_label.configure(image=photo, text=""))
            
        except Exception as e:
            self.log(f"Error loading thumbnail: {str(e)}", "ERROR")
            self.root.after(0, self.clear_thumbnail)

    def clear_thumbnail(self):
        """Clear the thumbnail display"""
        self.thumbnail_image = None
        self.thumbnail_label.configure(image="", text="No thumbnail available")

    def set_loading_state(self, is_loading):
        """Set the UI state during loading operations"""
        if is_loading:
            # Disable UI elements during loading
            self.url_entry.configure(state="disabled")
            if hasattr(self, 'fetch_button'):
                self.fetch_button.configure(state="disabled", text="Loading...")
            if hasattr(self, 'download_button'):
                self.download_button.configure(state="disabled")
            
            # Update the cursor to show loading
            self.root.config(cursor="watch")
            
            # Log the loading state
            self.log("Loading video information...", "INFO")
        else:
            # Re-enable UI elements after loading
            self.url_entry.configure(state="normal")
            if hasattr(self, 'fetch_button'):
                self.fetch_button.configure(state="normal", text="Fetch Info")
            if hasattr(self, 'download_button'):
                # Only enable download button if video info is available
                btn_state = "normal" if self.video_info else "disabled"
                self.download_button.configure(state=btn_state)
            
            # Reset cursor
            self.root.config(cursor="")
            
            # Log completion
            if self.video_info:
                self.log("Video information loaded successfully", "INFO")
        #format stuff start here, those which are fetched and let user download.            
    def update_format_list(self):
        """Update the format list based on media type selection."""
        if not self.video_info:
            return
            
        # Clear current items
        self.format_tree.delete(*self.format_tree.get_children())
        
        media_type = self.media_type.get()
        self.log(f"Updating format list for media type: {media_type}", "DEBUG")
        
        # Get filtered formats based on media type
        filtered_formats = []
        video_with_audio_formats = []  # For tracking formats with both video and audio
        
        for fmt in self.formats:
            # For video formats
            if media_type == 'video':
                # Skip audio-only formats
                if fmt.get('vcodec', 'none') == 'none':
                    continue
                
                # For video formats with audio, add to special list
                if fmt.get('acodec', 'none') != 'none':
                    video_with_audio_formats.append(fmt)
                    
            # For audio formats
            else:
                # Skip video-only formats
                if fmt.get('acodec', 'none') == 'none':
                    continue
            
            filtered_formats.append(fmt)
        
        # Sort formats by quality
        def format_sort_key(fmt):
            if media_type == 'video':
                # Get height as primary sort key for videos
                height = fmt.get('height', 0) or 0
                # Use filesize as secondary sort key
                filesize = fmt.get('filesize', 0) or fmt.get('filesize_approx', 0) or 0
                return (-height, -filesize)
            else:
                # Get audio bitrate as primary sort key for audio
                abr = fmt.get('abr', 0) or 0
                # Use filesize as secondary sort key
                filesize = fmt.get('filesize', 0) or fmt.get('filesize_approx', 0) or 0
                return (-abr, -filesize)
        
        # Sort all formats
        filtered_formats.sort(key=format_sort_key)
        video_with_audio_formats.sort(key=format_sort_key)
        
        # Add formats to the tree
        format_items = {}  # To keep track of tree items by format_id
        
        for fmt in filtered_formats:
            format_id = fmt.get('format_id', 'N/A')
            extension = fmt.get('ext', 'N/A')
            
            # For video formats
            if media_type == 'video':
                if fmt.get('resolution') is not None:
                    resolution = fmt.get('resolution')
                elif fmt.get('width') and fmt.get('height'):
                    resolution = f"{fmt.get('width')}x{fmt.get('height')}"
                else:
                    resolution = 'N/A'
            
            # For audio formats
            else:
                if fmt.get('abr'):
                    resolution = f"{fmt.get('abr')} kbps"
                else:
                    resolution = 'N/A'
            
            # Get file size
            if fmt.get('filesize'):
                filesize = self.format_file_size(fmt.get('filesize'))
            elif fmt.get('filesize_approx'):
                filesize = f"~{self.format_file_size(fmt.get('filesize_approx'))}"
            else:
                filesize = 'N/A'
            
            # Notes about the format
            notes = []
            if fmt.get('format_note'):
                notes.append(fmt.get('format_note'))
            if fmt.get('vcodec') and fmt.get('vcodec') != 'none':
                notes.append(f"Video: {fmt.get('vcodec')}")
            if fmt.get('acodec') and fmt.get('acodec') != 'none':
                notes.append(f"Audio: {fmt.get('acodec')}")
            else:
                # Mark video-only formats
                if media_type == 'video':
                    notes.append("No Audio")
            if fmt.get('fps'):
                notes.append(f"{fmt.get('fps')} fps")
            
            note = ', '.join(notes)
            
            # Add to tree
            item_id = self.format_tree.insert('', 'end', values=(format_id, extension, resolution, filesize, note))
            format_items[format_id] = item_id
        
        # Auto-select the best quality format
        if self.format_tree.get_children():
            if media_type == 'video' and video_with_audio_formats:
                # For video, select the best format that has both video and audio
                best_format = video_with_audio_formats[0]
                best_format_id = best_format.get('format_id', '')
                
                if best_format_id in format_items:
                    best_item = format_items[best_format_id]
                    self.format_tree.selection_set(best_item)
                    self.format_tree.see(best_item)
                    self.log(f"Auto-selected best format with both video and audio: {best_format_id}", "DEBUG")
                else:
                    # Fallback to first item if something went wrong
                    best_item = self.format_tree.get_children()[0]
                    self.format_tree.selection_set(best_item)
                    self.format_tree.see(best_item)
                    self.log(f"Auto-selected format: {self.format_tree.item(best_item, 'values')[0]}", "DEBUG")
            else:
                # For audio or if no video+audio formats found, select the first (best) item
                best_item = self.format_tree.get_children()[0]
                self.format_tree.selection_set(best_item)
                self.format_tree.see(best_item)
                self.log(f"Auto-selected format: {self.format_tree.item(best_item, 'values')[0]}", "DEBUG")
        
    def format_file_size(self, size_bytes):
        """Format file size to human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/(1024*1024):.1f} MB"
        else:
            return f"{size_bytes/(1024*1024*1024):.1f} GB"
    
    def browse_save_location(self):
        """Open a dialog to select save location."""
        directory = filedialog.askdirectory()
        if directory:
            self.save_path_entry.delete(0, tk.END)
            self.save_path_entry.insert(0, directory)
            self.log(f"Save location set to: {directory}", "DEBUG")
    #Download stuff start here! it work in single format audio/video choosen ,for multiple downloads not yet supported
    def start_download(self):
        """Start the download process."""
        selected_items = self.format_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select a format to download")
            return
            
        if not self.video_info:
            messagebox.showerror("Error", "No video information available")
            return
            
        # Get selected format ID
        selected_item = selected_items[0]
        format_values = self.format_tree.item(selected_item, 'values')
        format_id = format_values[0]
            
        # Determine if the selected format has audio by checking the actual format data
        selected_format = None
        is_video_only = False
        for fmt in self.formats:
            if fmt.get('format_id') == format_id:
                selected_format = fmt
                # If acodec is 'none', it's a video-only format
                is_video_only = (fmt.get('acodec') == 'none')
                break
                    
        # Get save path
        save_path = self.save_path_entry.get().strip()
        if not save_path:
            messagebox.showerror("Error", "Please specify a save location")
            return
            
        if not os.path.isdir(save_path):
            messagebox.showerror("Error", "Save location is not a valid directory")
            return
            
        # Configure the format string for download
        download_format = format_id
        
        # Track if we're using a combined format
        is_combined_format = False
            
        # If it's a video-only format and we're in video mode, combine with audio
        media_type = self.media_type.get()
        if media_type == 'video' and is_video_only and selected_format:
            is_combined_format = True
            # Get the container format (extension)
            container = selected_format.get('ext', '')
                    
            # Construct format string based on container
            if container == 'mp4':
                # For MP4, prefer mp4/m4a audio
                download_format = f"{format_id}+bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio"
            elif container == 'webm':
                # For WebM, prefer webm audio
                download_format = f"{format_id}+bestaudio[ext=webm]/bestaudio"
            else:
                # For other containers, use any best audio
                download_format = f"{format_id}+bestaudio"
                        
            self.log(f"Selected format {format_id} is video-only. Auto-combining with audio using format string: {download_format}", "INFO")
            messagebox.showinfo("Auto-Combining",
                            "Selected format doesn't include audio. Will automatically download and combine with the best audio track.")
            
        self.log(f"Starting download with format specification: {download_format}", "INFO")
            
        # Reset cancel flag
        self.cancel_flag = False
            
        # Enable cancel button if it exists
        if hasattr(self, 'cancel_button'):
            self.cancel_button.config(state=tk.NORMAL)
            
        # Start download in a separate thread
        self.download_thread = threading.Thread(
            target=self._download_thread, 
            args=(download_format, save_path, is_combined_format),  # Pass the combined format flag
            daemon=True
        )
        self.download_thread.start()
            
        # Switch to log tab to show progress
        self.notebook.select(1)  # Index 1 is the Verbose tab    
    def cancel_download(self):
        """Cancel the current download"""
        if self.download_thread and self.download_thread.is_alive():
            self.cancel_flag = True
            self.log("Download cancellation requested", "INFO")
            self.status_label.config(text="Cancelling download...")
            
    def _download_thread(self, format_id, save_path, is_combined_format=False):
        """Background thread for downloading."""
        # Fixed lambda with parentheses
        self.root.after(0, lambda: (self.status_label.config(text="Downloading...")))
        self.root.after(0, lambda: (self.progress.__setitem__('value', 0)))

        start_time = time.time()
        self.current_download_path = None  # Reset the path
        downloaded_file_reported = False   # Flag to track if the file has been reported

        def progress_hook(d):
            if self.cancel_flag:
                # Signal to yt-dlp to stop the download
                return
            
            if d['status'] == 'downloading':
                # Log the start of download
                if not hasattr(progress_hook, "download_started"):
                    progress_hook.download_started = True
                    self.log(f"Download started: {d.get('filename', 'unknown file')}", "INFO")
            
                # Calculate progress if available
                if d.get('downloaded_bytes') and d.get('total_bytes'):
                    p = int(d['downloaded_bytes'] / d['total_bytes'] * 100)
                    # Fixed lambda with parentheses
                    self.root.after(0, lambda: (self.progress.__setitem__('value', p)))
                
                    # Only update status every 1% to reduce GUI overhead
                    if not hasattr(progress_hook, "last_percent") or p != progress_hook.last_percent:
                        progress_hook.last_percent = p
                        self.root.after(0, lambda: (self.status_label.config(
                            text=f"Downloading... {p}% ({self.format_file_size(d['downloaded_bytes'])}/{self.format_file_size(d['total_bytes'])})"
                        )))
                
                    # Log progress at 10% intervals
                    if not hasattr(progress_hook, "last_log_percent") or (p // 10) > (progress_hook.last_log_percent // 10):
                        progress_hook.last_log_percent = p
                        self.log(f"Download progress: {p}%", "DEBUG")
                
                elif d.get('downloaded_bytes') and d.get('total_bytes_estimate'):
                    p = int(d['downloaded_bytes'] / d['total_bytes_estimate'] * 100)
                    self.root.after(0, lambda: (self.progress.__setitem__('value', p)))
                
                    if not hasattr(progress_hook, "last_percent") or p != progress_hook.last_percent:
                        progress_hook.last_percent = p
                        self.root.after(0, lambda: (self.status_label.config(
                            text=f"Downloading... {p}% (estimated)"
                        )))
                
                else:
                    # If we can't calculate percentage, show download speed.
                    if d.get('_speed_str'):
                        self.root.after(0, lambda: (self.status_label.config(
                            text=f"Downloading... ({d.get('_speed_str', 'N/A')})"
                        )))
                    
            elif d['status'] == 'finished':
                # Fixed lambda with parentheses
                self.root.after(0, lambda: (self.progress.__setitem__('value', 100)))
                
                # For combined formats, this hook might be called multiple times
                if d.get('filename'):
                    # For combined downloads, we only want to track the final merged file
                    if is_combined_format:
                        # Store temp path but don't report yet - wait for the final merged file
                        self.current_download_path = d.get('filename')
                        self.log(f"Component download finished: {self.current_download_path}", "DEBUG")
                        self.root.after(0, lambda: (self.status_label.config(text="Merging audio and video...")))
                    else:
                        # For single format, this is the final file
                        self.current_download_path = d.get('filename')
                        self.log(f"Download finished: {self.current_download_path}", "INFO")
                        self.root.after(0, lambda: (self.status_label.config(text="Processing download...")))
            
            elif d['status'] == 'error':
                self.root.after(0, lambda: (self.status_label.config(text=f"Error: {d.get('error', 'Unknown error')}")))
                self.log(f"Download error: {d.get('error', 'Unknown error')}", "ERROR")
        
        def post_process_hook(d):
            nonlocal downloaded_file_reported
            
            # This hook is specifically for tracking the final merged file in combined downloads
            if d['status'] == 'finished' and is_combined_format:
                if d.get('__postprocessor', '') == 'MoveFiles' and d.get('__files_to_move', {}) and not downloaded_file_reported:
                    # Get the final output file path
                    for _, dest_file in d.get('__files_to_move', {}).items():
                        if dest_file:
                            self.current_download_path = dest_file
                            self.log(f"Combined download finished: {self.current_download_path}", "INFO")
                            downloaded_file_reported = True
                            break
        #
        try:
            # Function to create a unique filename
            def get_unique_filename(base_path):
                """Generate a unique filename by adding numeric suffixes if file exists"""
                if not os.path.exists(base_path):
                    return base_path
                    
                name, ext = os.path.splitext(base_path)
                counter = 1
                
                while True:
                    new_path = f"{name}_{counter}{ext}"
                    if not os.path.exists(new_path):
                        return new_path
                    counter += 1
            
            # Basic template for output filename
            base_outtmpl = os.path.join(save_path, '%(title)s-%(id)s.%(ext)s')
            
            self.log(f"Using format specification: {format_id}", "INFO")
            
            # Custom hook to handle filename conflicts
            original_hooks = progress_hook
            
            def filename_progress_hook(progress):
                # Call the original progress hook
                original_hooks(progress)
                
                # If download is complete, check and rename the file if needed
                if progress['status'] == 'finished':
                    output_file = progress['filename']
                    unique_file = get_unique_filename(output_file)
                    
                    # If the filename changed due to conflict, rename it
                    if unique_file != output_file and not os.path.exists(unique_file):
                        try:
                            os.rename(output_file, unique_file)
                            progress['filename'] = unique_file
                            self.log(f"Renamed output file to avoid conflict: {unique_file}", "INFO")
                        except Exception as rename_err:
                            self.log(f"Error renaming file: {rename_err}", "WARNING")
            
            ydl_opts = {
                'format': format_id,
                'outtmpl': base_outtmpl,
                'progress_hooks': [filename_progress_hook],
                'postprocessor_hooks': [post_process_hook],
                'quiet': False,
                'no_warnings': False,
                'merge_output_format': 'mp4',
            }
            
            self.log(f"yt-dlp options: {ydl_opts}", "DEBUG")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if not self.cancel_flag:
                    ydl.download([self.video_info['webpage_url']])
            
            elapsed = time.time() - start_time
            
            if self.cancel_flag:
                self.root.after(0, lambda: self.status_label.config(text="Download cancelled"))
                self.log("Download was cancelled by user", "INFO")
            else:
                self.root.after(0, lambda: self.status_label.config(text=f"Download completed in {elapsed:.1f} seconds!"))
                self.root.after(0, lambda: messagebox.showinfo("Success", "Download completed successfully!"))
                
                # Add the file to our downloads list and refresh the tab
                if self.current_download_path:
                    # Ensure this file isn't already in the list (could happen with combined formats)
                    if self.current_download_path not in self.downloaded_files:
                        self.downloaded_files.append(self.current_download_path)
                        
                    self.root.after(0, self.refresh_downloads_list)
                    
                    # Switch to the downloads tab to show the result
                    self.root.after(0, lambda: self.notebook.select(2))  # Index 2 is Downloads tab
                    
                    # Auto-select the newly downloaded file
                    def select_new_file():
                        for item in self.downloads_tree.get_children():
                            if self.downloads_tree.item(item, 'values')[0] == os.path.basename(self.current_download_path):
                                self.downloads_tree.selection_set(item)
                                self.downloads_tree.see(item)
                                self.on_download_selected(None)
                    
                    self.root.after(100, select_new_file)

        except Exception as e:
            if self.cancel_flag:
                self.root.after(0, lambda: self.status_label.config(text="Download cancelled"))
                self.log("Download was cancelled by user", "INFO")
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Download failed: {str(e)}"))
                self.root.after(0, lambda: self.status_label.config(text="Download failed"))
                self.log(f"Download failed: {str(e)}", "ERROR")    
    #This is part of Downloads Tab
    def refresh_downloads_list(self):
        """Refresh the downloads list in the Downloads tab with files organized by folders"""
        # Clear the current tree
        self.downloads_tree.delete(*self.downloads_tree.get_children())
        
        # Define media file extensions to look for
        video_extensions = ['.mp4', '.webm', '.mkv', '.avi', '.mov', '.flv']
        audio_extensions = ['.mp3', '.m4a', '.wav', '.ogg', '.aac', '.flac']
        
        # Create main folder categories in the tree
        video_folder = self.downloads_tree.insert('', 'end', text="Videos", open=True)
        audio_folder = self.downloads_tree.insert('', 'end', text="Audio", open=True)
        other_folder = self.downloads_tree.insert('', 'end', text="Other Files", open=True)
        
        # Track all files found to avoid duplicates
        all_files_found = set()
        
        # First, add any files that are in our tracked downloads list
        for file_path in self.downloaded_files:
            if os.path.exists(file_path):
                all_files_found.add(file_path)
                filename = os.path.basename(file_path)
                
                # Get file info
                try:
                    file_stats = os.stat(file_path)
                    file_size = self.format_file_size(file_stats.st_size)
                    mod_time = datetime.datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                except:
                    file_size = "Unknown"
                    mod_time = "Unknown"
                
                # Determine the parent folder based on file extension
                ext = os.path.splitext(filename)[1].lower()
                if ext in video_extensions:
                    parent = video_folder
                elif ext in audio_extensions:
                    parent = audio_folder
                else:
                    parent = other_folder
                
                self.downloads_tree.insert(parent, 'end', values=(filename, mod_time, file_size), tags=(file_path,))
        
        # Scan download directories for additional media files
        try:
            # Use the save path if defined, otherwise default to a downloads folder
            scan_paths = []
            if hasattr(self, 'save_path') and self.save_path:
                scan_paths.append(self.save_path)
            
            # Add default locations to scan
            default_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            if os.path.exists(default_downloads):
                scan_paths.append(default_downloads)
            
            # Add the current directory
            scan_paths.append(os.getcwd())
            
            # Scan each path for media files
            for scan_path in scan_paths:
                if os.path.exists(scan_path):
                    for root, dirs, files in os.walk(scan_path):
                        # Don't scan too deep
                        if root.count(os.sep) > scan_path.count(os.sep) + 2:
                            continue
                        
                        for file in files:
                            file_path = os.path.join(root, file)
                            
                            # Skip if we've already added this file
                            if file_path in all_files_found:
                                continue
                            
                            # Check if it's a media file
                            ext = os.path.splitext(file)[1].lower()
                            if ext in video_extensions or ext in audio_extensions:
                                all_files_found.add(file_path)
                                
                                # Get file info
                                try:
                                    file_stats = os.stat(file_path)
                                    file_size = self.format_file_size(file_stats.st_size)
                                    mod_time = datetime.datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                                except:
                                    file_size = "Unknown"
                                    mod_time = "Unknown"
                                
                                # Add to the appropriate folder
                                if ext in video_extensions:
                                    parent = video_folder
                                else:
                                    parent = audio_folder
                                
                                self.downloads_tree.insert(parent, 'end', values=(file, mod_time, file_size), tags=(file_path,))
                                
                                # Add to our tracked downloads if not already there
                                if file_path not in self.downloaded_files:
                                    self.downloaded_files.append(file_path)
        except Exception as e:
            self.log(f"Error scanning for media files: {str(e)}", "ERROR")
        
        # Update folder labels with counts
        video_count = len(self.downloads_tree.get_children(video_folder))
        audio_count = len(self.downloads_tree.get_children(audio_folder))
        other_count = len(self.downloads_tree.get_children(other_folder))
        
        self.downloads_tree.item(video_folder, text=f"Videos ({video_count})")
        self.downloads_tree.item(audio_folder, text=f"Audio ({audio_count})")
        self.downloads_tree.item(other_folder, text=f"Other Files ({other_count})")
        
        # Remove empty folders
        if video_count == 0:
            self.downloads_tree.delete(video_folder)
        if audio_count == 0:
            self.downloads_tree.delete(audio_folder)
        if other_count == 0:
            self.downloads_tree.delete(other_folder)
        
        self.log(f"Downloads list refreshed with {len(all_files_found)} files", "DEBUG")

    def on_download_selected(self, event):
        """Handle when a download is selected in the downloads list"""
        selected_items = self.downloads_tree.selection()
        if not selected_items:
            self.preview_info_var.set("Select a file to preview")
            return
            
        # Get the file path from the item's tags
        item = selected_items[0]
        item_values = self.downloads_tree.item(item, 'values')
        filename = item_values[0]
        date = item_values[1]
        size = item_values[2]
        
        # Find the full path in our list
        file_path = None
        for path in self.downloaded_files:
            if os.path.basename(path) == filename:
                file_path = path
                break
                
        if not file_path or not os.path.exists(file_path):
            self.preview_info_var.set(f"File not found: {filename}")
            return
            
        # Determine file type
        file_ext = os.path.splitext(file_path)[1].lower()
        is_video = file_ext in ['.mp4', '.webm', '.mkv', '.avi', '.mov', '.flv']
        is_audio = file_ext in ['.mp3', '.m4a', '.wav', '.ogg', '.flac']
        
        # Update the preview info
        file_type = "Video" if is_video else "Audio" if is_audio else "Media"
        info_text = f"{filename}\n\nType: {file_type}\nSize: {size}\nDate: {date}\nLocation: {os.path.dirname(file_path)}"
        self.preview_info_var.set(info_text)
        
        self.log(f"Selected file: {file_path}", "DEBUG")

    #In future we can create separate *.py, use class then pass this to this so that it use its own player.
    def play_selected_file(self):
        """Play the selected file using default system player"""
        selected_items = self.downloads_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a file to play")
            return
            
        # Get the filename
        item = selected_items[0]
        filename = self.downloads_tree.item(item, 'values')[0]
        
        # Find the full path
        file_path = None
        for path in self.downloaded_files:
            if os.path.basename(path) == filename:
                file_path = path
                break
                
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", f"File not found: {filename}")
            return
            
        self.log(f"Playing file: {file_path}", "INFO")
        
        # Launch the system's default media player
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux and others
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            self.log(f"Error playing file: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to play the file: {str(e)}")
    #play video both as thumbanail and local video
    def play_video(self, event=None):
        """Play the video in the default browser or media player"""
        if not self.video_info:
            messagebox.showinfo("Info", "No video loaded")
            return
        
        video_url = self.video_info.get('webpage_url')
        if not video_url:
            messagebox.showerror("Error", "Video URL not available")
            return
        
        try:
            # Determine the best way to play the video based on the platform
            system = platform.system()
            
            if system == "Windows":
                os.startfile(video_url)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", video_url], check=True)
            else:  # Linux and others
                subprocess.run(["xdg-open", video_url], check=True)
                
            self.log(f"Playing video: {video_url}", "INFO")
                
        except Exception as e:
            self.log(f"Error playing video: {str(e)}", "ERROR")
            # Fallback to webbrowser if system methods fail
            import webbrowser
            webbrowser.open(video_url)

    def open_containing_folder(self):
        """Open the folder containing the selected file"""
        selected_items = self.downloads_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a file")
            return
            
        # Get the filename
        item = selected_items[0]
        filename = self.downloads_tree.item(item, 'values')[0]
        
        # Find the full path
        file_path = None
        for path in self.downloaded_files:
            if os.path.basename(path) == filename:
                file_path = path
                break
                
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", f"File not found: {filename}")
            return
            
        folder_path = os.path.dirname(file_path)
        self.log(f"Opening folder: {folder_path}", "DEBUG")
        
        # Open the folder in file explorer
        try:
            if platform.system() == 'Windows':
                os.startfile(folder_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', folder_path])
            else:  # Linux and others
                subprocess.run(['xdg-open', folder_path])
        except Exception as e:
            self.log(f"Error opening folder: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to open the folder: {str(e)}")

    def delete_selected_file(self):
        """Delete the selected file"""
        selected_items = self.downloads_tree.selection()
        if not selected_items:
            messagebox.showinfo("Info", "Please select a file to delete")
            return
            
        # Get the filename
        item = selected_items[0]
        filename = self.downloads_tree.item(item, 'values')[0]
        
        # Find the full path
        file_path = None
        for path in self.downloaded_files:
            if os.path.basename(path) == filename:
                file_path = path
                break
                
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", f"File not found: {filename}")
            # Remove from our list anyway
            if file_path in self.downloaded_files:
                self.downloaded_files.remove(file_path)
            self.refresh_downloads_list()
            return
            
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {filename}?")
        if not confirm:
            return
            
        # Delete the file
        try:
            os.remove(file_path)
            self.log(f"Deleted file: {file_path}", "INFO")
            
            # Remove from our list and refresh
            if file_path in self.downloaded_files:
                self.downloaded_files.remove(file_path)
            self.refresh_downloads_list()
            
            # Clear preview
            self.preview_info_var.set("File has been deleted")
            
        except Exception as e:
            self.log(f"Error deleting file: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to delete the file: {str(e)}")

    def log(self, message, level="INFO"):
        """Add a message to the log with timestamp and level"""
        if level not in ["INFO", "DEBUG", "ERROR"]:
            level = "INFO"
            
        # Skip DEBUG messages if log level is INFO or ERROR
        if level == "DEBUG" and self.log_level == "INFO":
            return
            
        # Skip INFO and DEBUG messages if log level is ERROR
        if level in ["DEBUG", "INFO"] and self.log_level == "ERROR":
            return
            
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_message, level)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def set_log_level(self, level):
        """Change the logging level"""
        if level in ["INFO", "DEBUG", "ERROR"]:
            self.log_level = level
            self.log(f"Log level changed to {level}", "INFO")

    def clear_log(self):
        """Clear the log text area"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log("Log cleared", "INFO")


if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    root.mainloop()
