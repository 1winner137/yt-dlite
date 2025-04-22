import os
import sys
import time
import queue
import threading
import platform
import datetime
import functools
import subprocess
import webbrowser
import urllib.request
import yt_dlp
import io  
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
from misc import PlaylistHandler
from expert import ExpertGui, RedirectText
from begginer import HomeGui

class YouTubeDownloaderGUI: 
    def __init__(self, root): 
        self.root = root 
        self.root.title("Yt-dlite Downloader") 
        self.root.geometry("850x580") 
        self.root.resizable(True, True) 
        self.root.minsize(800, 550) 
        self.fetch_cancelled = False 
         
        # Tab mode state 
        self.expert_mode = True  # Start with proffesional mode (Main tab) 
         
        # Theme state 
        self.dark_mode = False 
 
        self.sort_state = { 
            "format_tree": {"column": "resolution", "direction": "asc"}, 
            "downloads_tree": {"column": "date", "direction": "desc"} 
        } 
         
        # Create notebook for tabs 
        self.notebook = ttk.Notebook(self.root) 
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10) 
         
        # Create tabs 
        self.main_tab = ttk.Frame(self.notebook) 
        self.verbose_tab = ttk.Frame(self.notebook) 
        self.downloads_tab = ttk.Frame(self.notebook) 
        self.beginner_tab = HomeGui(self.notebook)  # Attach HomeGui as a tab 
 
        self.notebook.add(self.beginner_tab, text="Home")          
        self.notebook.add(self.main_tab, text="Main") 
        self.notebook.add(self.verbose_tab, text="Log") 
        self.notebook.add(self.downloads_tab, text="Downloads") 
         
        # Initial theme setup
        self.setup_theme(dark_mode=False) 
                 
        self.theme_button = ttk.Button( 
            root,  
            text="🌙 Dark Mode",  
            command=self.toggle_theme, 
            style="Theme.TButton" 
        ) 
        self.theme_button.place(relx=1.0, y=5, anchor="ne", x=-10) 
         
        self.main_content_frame = ttk.Frame(self.main_tab)
        self.main_content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.container_frame = ttk.Frame(self.main_content_frame)
        self.container_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.switch_button = ttk.Button(
            self.root, 
            text="Switch to Expert mode",
            command=self.switch_ui,
            style="Theme.TButton"
        )
        self.switch_button.place(relx=0.5, rely=1, anchor="e", x=10)
               
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # Setup all tabs
        self.load_main_ui()
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
        self.log("Application started", "INFO")
        
        # Now that all attributes are initialized, update button visibility
        self.on_tab_changed(None)

    def setup_theme(self, dark_mode=False):
        self.dark_mode = dark_mode
        self.style = ttk.Style()
        self.style.theme_use("clam") 
        # Define colors based on theme
        if dark_mode:
            # Dark theme colors
            bg_color = "#1E1E1E"  # Dark background
            fg_color = "#E0E0E0"  # Light text
            accent_color = "#0098FF"  # Lighter blue on hover #008000 #0098FF
            accent_hover = "#007ACC"  # Blue accent on hover
            tree_bg = "#2D2D2D"  # Slightly lighter than main bg
            tab_bg = "#333333"  # Dark gray for inactive tabs
            entry_bg = "#3C3C3C"  # Dark input fields
            button_fg = "white"
        else:
            # Light theme colors
            bg_color = "#F8F9FA"  # Soft light gray
            fg_color = "#333333"  # Dark text
            accent_color = "#C70039"  # Dark red
            accent_hover = "#0098FF"  # Lighter blue on hover
            tree_bg = "white"
            tab_bg = "#E0E0E0"  # Light gray for inactive tabs
            entry_bg = "white"
            button_fg = "white"
        
        # Update root background
        self.root.configure(background=bg_color)
        
        # Theme toggle button style
        self.style.configure("Theme.TButton",
                         background=accent_color,
                         foreground=button_fg,
                         font=("Arial", 9, "bold"),
                         padding=5,
                         relief="flat")
        self.style.map("Theme.TButton",
                   background=[("active", accent_hover)],
                   relief=[("pressed", "ridge")])
        
        # Buttons
        self.style.configure("TButton",
                         background=accent_color,
                         foreground=button_fg,
                         font=("Arial", 9, "bold"),
                         borderwidth=0,
                         padding=5,
                         relief="flat")
        self.style.map("TButton",
                   background=[("active", accent_hover)],
                   relief=[("pressed", "ridge")])
        
        # Labels
        self.style.configure("TLabel",
                         background=bg_color,
                         foreground=fg_color,
                         font=("Arial", 9, "bold"))
        
        # Notebook (Tabs)
        self.style.configure("TNotebook",
                         background=bg_color,
                         borderwidth=0)
        self.style.configure("TNotebook.Tab",
                         background=tab_bg,
                         foreground=fg_color,
                         font=("Arial", 9, "bold"),
                         padding=[8, 3])
        self.style.map("TNotebook.Tab",
                   background=[("selected", accent_color)],
                   foreground=[("selected", "white")])
        
        # Treeview (Table)
        self.style.configure("Treeview",
                         background=tree_bg,
                         fieldbackground=tree_bg,
                         foreground=fg_color,
                         font=("Arial", 9))
        self.style.configure("Treeview.Heading",
                         font=("Arial", 9, "bold"),
                         background=accent_color,
                         foreground="white")
        
        # Progressbar
        self.style.configure("TProgressbar",
                         background="#4CAF50")
        
        # Entries
        self.style.configure("TEntry",
                         background=entry_bg,
                         foreground=fg_color,
                         padding=5,
                         font=("Arial", 9),
                         relief="solid",
                         borderwidth=1)
        
        # Frames
        self.style.configure("TFrame",
                         background=bg_color)
        
        # Radiobuttons
        self.style.configure("TRadiobutton",
                         background=bg_color,
                         foreground=fg_color,
                         font=("Arial", 9))
                         
        # LabelFrame
        self.style.configure("TLabelframe",
                         background=bg_color)
        self.style.configure("TLabelframe.Label",
                         background=bg_color,
                         foreground=fg_color,
                         font=("Arial", 9, "bold"))

    #Toggle between dark and light mode
    def toggle_theme(self):
        new_mode = not self.dark_mode
        self.setup_theme(dark_mode=new_mode)
        if new_mode:
            self.theme_button.configure(text="☀️ Light Mode")
        else:
            self.theme_button.configure(text="🌙 Dark Mode")
        theme_name = "Dark" if new_mode else "Light"
        self.log(f"Switched to {theme_name} mode", "INFO")
    #main tab
    #switch UI destroy everything no remembering at all, in the future we can fix this
    def switch_ui(self):
        # Show warning popup before proceeding
        import tkinter as tk
        from tkinter import messagebox
        
        result = messagebox.showwarning(
            "Warning: Data Loss",
            "You are advised to finish all jobs before switching between Expert and professional UI modes.\n\nPending jobs in Expert and Professional modes will be forgotten and may get out of control.\n\nDo you want to continue?",
            type=messagebox.OKCANCEL
        )
        
        # If user cancels, abort the switch
        if result == "cancel":
            if hasattr(self, "log"):
                self.log("UI switch cancelled by user", "INFO")
            return
        
        # Toggle expert mode
        new_mode = not self.expert_mode if hasattr(self, "expert_mode") else True
        self.expert_mode = new_mode
        
        # Log debug information about widget loss
        if hasattr(self, "log"):
            self.log("DEBUG: UI switch initiated - Widget data will be lost", "DEBUG")
            try:
                widget_count = len(self.container_frame.winfo_children())
                self.log(f"DEBUG: About to forget {widget_count} widgets", "DEBUG")
            except Exception as e:
                self.log(f"Error counting widgets: {e}", "ERROR")
        
        # Clear the container frame
        for widget in self.container_frame.winfo_children():
            widget.destroy()
        
        # Load appropriate UI
        if new_mode:
            self.load_main_ui()
            self.switch_button.config(text="Switch to Expert mode")
        else:
            self.load_hello()
            self.switch_button.config(text="Switch to Professional Mode")
        
        ui_name = "Professional" if new_mode else "Expert"
        if hasattr(self, "log"):
            self.log(f"Switched to {ui_name} UI", "INFO")
            self.log("WARNING: Previous UI data has been lost due to tkinter limitations", "WARNING")
    
    #Update button visibility based on active tab
    def on_tab_changed(self, event):
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 1:  # Main tab
            self.switch_button.place(relx=1.0, y=10, anchor="ne", x=-10)
        else:
            self.switch_button.place_forget() #Hide it in other tabs

    #Set up the main tab container and switch UI between Main and Expert Mode        
    def setup_main_tab(self):
        self.container_frame = ttk.Frame(self.main_tab, padding="5")
        self.container_frame.pack(fill=tk.BOTH, expand=True)
        self.load_main_ui()
        self.switch_button = ttk.Button(self.main_tab, text="Switch to Expert Mode", command=self.switch_ui)
        self.switch_button.pack(pady=5)

    #Importing expert.py so that it adapt this frame
    def load_hello(self):
        class FrameYTDLPGui(ExpertGui):
            def __init__(self, frame):
                # Set basic attributes before calling any methods
                self.parent = frame
                self.terminal_queue = queue.Queue()
                self.download_in_progress = False
                self.conversion_in_progress = False
                self.current_process = None
                self.process_lock = threading.Lock()
                self.cancellation_requested = False
                self.download_thread = None
                
                # Custom initialization
                self.download_folder = os.path.join(os.path.expanduser("~"), "Downloads", "yt-dlite")
                os.makedirs(self.download_folder, exist_ok=True)
                
                # Create UI components
                self.create_downloader_section(self.parent)
                ttk.Separator(self.parent, orient='horizontal').pack(fill='x', pady=3)
                self.create_converter_section(self.parent)
                ttk.Separator(self.parent, orient='horizontal').pack(fill='x', pady=3)
                self.create_terminal_section(self.parent)
                self.setup_stdout_redirection()
                self.update_terminal()
                self.create_save_progress_section(self.parent)
        
        # Create an instance of our wrapper class
        self.ytdl_gui = FrameYTDLPGui(self.container_frame)
        
        # Ensure the container frame expands properly
        self.container_frame.pack(fill='both', expand=True)

    #Professional mode
    def load_main_ui(self):
        main_frame = ttk.Frame(self.container_frame, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 5), ipady=5)
        
        # Just paste button
        url_frame = ttk.Frame(top_frame)
        url_frame.pack(fill=tk.X, pady=(0, 5))
        url_frame.columnconfigure(1, weight=1)
        
        ttk.Label(url_frame, text="Video URL:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=5)

        self.url_entry = ttk.Entry(url_frame, width=70, font=("Helvetica", 10))
        self.url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        # Bind Enter key to fetch_video_info function
        self.url_entry.bind("<Return>", lambda event: self.fetch_video_info())

        paste_button = ttk.Button(url_frame, text="Paste", width=5, command=self.paste_from_clipboard)
        paste_button.pack(side=tk.LEFT, padx=2)

        fetch_button = ttk.Button(url_frame, text="Fetch Info", command=self.fetch_video_info)
        fetch_button.pack(side=tk.LEFT, padx=5)

        cancel_button = ttk.Button(url_frame, text="X", width=2, command=self.cancel_fetch)
        cancel_button.pack(side=tk.LEFT, padx=2)

        # Setting placeholder
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

        # Add subtitle option not yet programmed for this version
        subtitle_frame = ttk.Frame(info_grid)
        subtitle_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        self.subtitle_var = tk.BooleanVar(value=False)
        subtitle_label = ttk.Label(subtitle_frame, text="Subtitles:")
        subtitle_label.pack(side=tk.LEFT, padx=(0, 5))
        subtitle_radio = ttk.Checkbutton(subtitle_frame, variable=self.subtitle_var)
        subtitle_radio.pack(side=tk.LEFT)
        #video information
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
        row_height = 5
        header_height = 5
        treeview_height = (row_height * 1) + header_height
        
        # Create a container frame with fixed height
        fixed_height_frame = ttk.Frame(tree_frame, height=treeview_height)
        fixed_height_frame.grid(row=0, column=0, sticky="nsew")
        fixed_height_frame.grid_propagate(False)  # This prevents the frame from resizing to its children
        fixed_height_frame.columnconfigure(0, weight=1)
        fixed_height_frame.rowconfigure(0, weight=1)
        
        #Scrollbarr
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        #Treeview for formats
        self.format_tree = ttk.Treeview(fixed_height_frame, columns=("format_id", "extension", "resolution", "filesize", "note"), 
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
        
        # Enabling Double-click to select and download things
        self.format_tree.bind("<Double-1>", lambda e: self.start_download())
        
        #Bottom section. Here goes download controls, progress, etc...
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=1)
        
        #Download path section
        download_frame = ttk.Frame(bottom_frame)
        download_frame.pack(fill=tk.X, pady=5)
        download_frame.columnconfigure(1, weight=1)        
        ttk.Label(download_frame, text="Save to:", font=("Helvetica", 9, "bold")).grid(row=0, column=0, padx=5, sticky=tk.W)
        self.save_path_entry = ttk.Entry(download_frame, font=("Helvetica", 9))
        self.save_path_entry.grid(row=0, column=1, padx=5, sticky=tk.EW)
        
        # Set default save path to Downloads/yt-dlite folder
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        yt_dlite_path = os.path.join(downloads_path, "yt-dlite")
        
        # Create the yt-dlite folder inside Downloads if it doesn't exist
        if not os.path.exists(yt_dlite_path):
            os.makedirs(yt_dlite_path)
        
        self.save_path_entry.insert(0, yt_dlite_path)
        browse_button = ttk.Button(download_frame, text="Browse", command=self.browse_save_location)
        browse_button.grid(row=0, column=2, padx=5)
        
        # Progress bar inspired by windows copy bar.
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
        download_button.pack(side=tk.LEFT, padx=1)        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel_download)
        cancel_button.pack(side=tk.LEFT, padx=1)
        
        self.download_thread = None
        self.cancel_flag = False
    #Verbose tab section goes here!    
    def setup_verbose_tab(self):
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

        # Log area
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
        self.downloads_tree.bind("<Double-1>", lambda event: self.play_selected_file()) #Double click to play files
        
        # Create right-click context menu
        self.context_menu = tk.Menu(self.downloads_tree, tearoff=0)
        self.context_menu.add_command(label="Play", command=self.play_selected_file)
        self.context_menu.add_command(label="Delete", command=self.delete_selected_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Open containing folder", command=self.open_containing_folder)
        self.downloads_tree.bind("<Button-3>", self.show_context_menu) #Right click event
        
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
        
        # Right panel with vertical split pane
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=60)
        
        # Create vertical paned window for the right side
        vertical_paned = ttk.PanedWindow(right_frame, orient=tk.VERTICAL)
        vertical_paned.pack(fill=tk.BOTH, expand=True)
        
        # Top section - File preview
        preview_frame = ttk.LabelFrame(vertical_paned, text="File Preview")
        vertical_paned.add(preview_frame, weight=70)
        
        # File info
        self.preview_info_var = tk.StringVar(value="Select a file to preview")
        ttk.Label(preview_frame, textvariable=self.preview_info_var, wraplength=300).pack(pady=10)
                
        # Bottom section - Creditsfo
        info_frame = ttk.LabelFrame(vertical_paned, text="Credits")
        vertical_paned.add(info_frame, weight=30)

        # Create a frame with padding for the Credits
        info_content_frame = ttk.Frame(info_frame, padding=10)
        info_content_frame.pack(fill=tk.BOTH, expand=True)

        # Credits with normal fields
        ttk.Label(info_content_frame, text="updates & issues:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        github_link = ttk.Label(info_content_frame, text="https://yt-dlite/visit", foreground="blue", cursor="hand2")
        github_link.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        github_link.bind("<Button-1>", lambda e: open_url("https://github.com/1winner137/yt-dlite/releases"))

        ttk.Label(info_content_frame, text="Contact:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        contact_info = ttk.Label(info_content_frame, text="1winner4win@proton.me", foreground="blue")
        contact_info.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(info_content_frame, text="Developed by:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(info_content_frame, text="1winner137").grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(info_content_frame, text="Version:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(info_content_frame, text="yt-dlite v1.0").grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(info_content_frame, text="Notes:").grid(row=4, column=0, sticky=tk.NW, padx=5, pady=2)
        notes_text = "yt-dlp errors can be ignored by restarting app or fetching information again."
        notes_label = ttk.Label(info_content_frame, text=notes_text, wraplength=250)
        notes_label.grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)

        # Full-width about section
        about_frame = ttk.Frame(info_content_frame)
        about_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=10)
        about_text = "By myself I'm not fan of big size programs, limits downloads & annoying ads, I wish it could support all languages, best appealing & more fetures."
        about_label = ttk.Label(about_frame, text=about_text, wraplength=350, justify=tk.LEFT)
        about_label.pack(fill=tk.X, expand=True)

        # Define functions at the module level, not inside the class method
        def copy_to_clipboard(text):
            root.clipboard_clear()
            root.clipboard_append(text)
            messagebox.showinfo("Copied", f"{text} copied to clipboard!")

        def open_url(url):
            webbrowser.open(url)

        # Full-width donate section
        donate_frame = ttk.Frame(info_content_frame)
        donate_frame.grid(row=6, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        donate_text = "Consider donating:"
        donate_label = ttk.Label(donate_frame, text=donate_text, wraplength=350, justify=tk.LEFT)
        donate_label.pack(fill=tk.X)

        # Create clickable links
        btc_link = ttk.Label(donate_frame, text="BTC: bc1qyr88kayp9nqve9u9jpav4kft4ln3rgu7wwqn4h", foreground="green", cursor="hand2")
        btc_link.pack(fill=tk.X)
        btc_link.bind("<Button-1>", lambda e: copy_to_clipboard("bc1qyr88kayp9nqve9u9jpav4kft4ln3rgu7wwqn4h"))

        paypal_link = ttk.Label(donate_frame, text="PayPal: winnernova7@gmail.com", foreground="green", cursor="hand2")
        paypal_link.pack(fill=tk.X)
        paypal_link.bind("<Button-1>", lambda e: open_url("mailto:winnernova7@gmail.com"))

        # Just one donation GitHub link
        donate_github_link = ttk.Label(donate_frame, text="Visit donation page", foreground="green", cursor="hand2")
        donate_github_link.pack(fill=tk.X) #you can put patreon
        donate_github_link.bind("<Button-1>", lambda e: open_url("https://github.com/1winner137/yt-dlite/blob/main/README.md#donation"))
    #Show context mnu on right click    
    def show_context_menu(self, event):
        item = self.downloads_tree.identify_row(event.y)
        if item:
            self.downloads_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    # To keep simple for now. but can be extended to use imported mediaplayer.py so as to have biult in player.
    #Paste from clipboard
    def paste_from_clipboard(self):
        try:
            clipboard_text = self.root.clipboard_get().strip()
            if clipboard_text:
                formatted_url = f'{clipboard_text}'
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, formatted_url)
                self.url_entry.config(foreground="black")  # Reset text color
                self.log(f'Pasted URL from clipboard: {formatted_url}', "DEBUG")
            else:
                self.set_placeholder()  # Restore placeholder if clipboard is empty
        except Exception as e:
            self.log(f"Failed to paste from clipboard: {str(e)}", "ERROR")
            self.set_placeholder()  # Restore placeholder on error
    #Set placeholder text when the entry is empty
    def set_placeholder(self):
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, "Hit Ctrl+V to paste or click the paste button")
        self.url_entry.config(foreground="gray")  # Make it visually distinct
    #Clear placeholder when user focuses on entry
    def clear_placeholder(self, event):        
        if self.url_entry.get() == "Hit Ctrl+V to paste":
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(foreground="black")
    #Restore placeholder if entry is empty when losing focus
    def restore_placeholder(self, event):
        if not self.url_entry.get():
            self.set_placeholder()

    #This are information fetched from video url
    def get_column_title(self, column):
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
    #Sort treeview by column with ascending/descending toggle
    def sort_treeview(self, treeview, column, treeview_key):
        items = [(treeview.set(item, column), item) for item in treeview.get_children('')]
        
        # Update sort state
        if self.sort_state[treeview_key]["column"] == column:
            self.sort_state[treeview_key]["direction"] = "desc" if self.sort_state[treeview_key]["direction"] == "asc" else "asc"
        else:
            self.sort_state[treeview_key]["column"] = column
            self.sort_state[treeview_key]["direction"] = "asc"

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
                # Check if URL is a playlist
                import misc
                if misc.is_playlist(url):
                    self.log("Playlist detected, handling with playlist processor! wait for popup", "INFO")
                    # Process playlist and get user format selection
                    playlist_handler = misc.process_playlist_url(self.root, url, self.log)
                    
                    # If user cancelled or error occurred
                    if not playlist_handler or self.fetch_cancelled:
                        self.log("Playlist processing cancelled or failed", "INFO")
                        self.root.after(0, lambda: self.set_loading_state(False))
                        return
                        
                    # Store playlist information for download
                    self.is_playlist = True
                    self.playlist_items = playlist_handler.get_download_items()
                    self.playlist_format = playlist_handler.selected_format
                    self.playlist_format_type = playlist_handler.selected_format_type
                    
                    # Update UI to show playlist is ready
                    self.root.after(0, lambda: self.status_label.config(
                        #text=f"Playlist ready: {len(self.playlist_items)} videos"))
                        text=f"Playlist downloading in progress"))
                    self.root.after(0, lambda: self.set_loading_state(False))
                else:
                    # Handle single video as normal
                    self.is_playlist = False
                    self._fetch_info_thread(url)
            except Exception as e:
                self.log(f"Error fetching info: {e}", "ERROR")
            finally:
                if not self.is_playlist:  # _fetch_info_thread handles this for single videos
                    self.set_loading_state(False)  # Ensure loading state resets

        # Use a thread to prevent freezing the GUI
        self.fetch_thread = threading.Thread(target=fetch_and_update, daemon=True)
        self.fetch_cancelled = False  # Reset cancellation flag
        self.fetch_thread.start()
        # Start a timer to check for timeouts, so that they can be logged
        self.check_fetch_timeout(self.fetch_thread, 15)
    #cancel fecthing
    def cancel_fetch(self):
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
    #Thread function to fetch video info without blocking UI
    def _fetch_video_info_thread(self, url):
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
    #Background thread for fetching video info.#########################################################

    def _fetch_info_thread(self, url):
        start_time = time.time()
        self.log(f"Starting fetch for URL: {url}", "INFO")
        
        try:
            if self.fetch_cancelled:
                self.log("Fetch cancelled before starting", "INFO")
                return
            
            # Minimal yt-dlp options for maximum speed
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': False,
                'no_color': True,
                'extract_flat': False,
                'socket_timeout': 15,
            }
            
            # Single-pass extraction without format processing
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if self.fetch_cancelled:
                    self.log("Fetch cancelled before extraction", "INFO")
                    return
                
                # Direct extraction without format processing (faster)
                self.log("Extracting basic video info...", "DEBUG")
                info_dict = ydl.extract_info(url, download=False, process=False)
                
                if not info_dict:
                    self.log("No video information returned by yt-dlp", "ERROR")
                    raise ValueError("Failed to extract video information")
                    
                if self.fetch_cancelled:
                    self.log("Fetch cancelled after extraction", "INFO")
                    return
                
                # Store raw info without processing formats
                self.video_info = info_dict
                raw_formats = info_dict.get('formats', [])
                self.log(f"Found {len(raw_formats)} raw formats", "DEBUG")
                
                # Minimal format processing - no filesize fetching or sorting
                self.formats = [
                    {
                        **fmt,
                        'resolution': f"{fmt.get('width', 0)}x{fmt.get('height', 0)}"
                        if fmt.get('width') and fmt.get('height')
                        else None
                    }
                    for fmt in raw_formats
                    if fmt.get('format_id')  # Only include formats with IDs
                ]
                
                if self.fetch_cancelled:
                    self.log("Fetch cancelled before UI update", "INFO")
                    self.video_info = None
                    self.formats = []
                    return
                
                # Fast UI updates
                self.root.after(0, self.update_format_list)
                self.root.after(0, self.update_video_info)
                
                elapsed = time.time() - start_time
                self.log(f"Fetch completed in {elapsed:.2f} seconds", "INFO")
                
        except yt_dlp.utils.DownloadError as e:
            if not self.fetch_cancelled:
                error_msg = str(e).strip() or "Unknown download error"
                self.log(f"Download error: {error_msg}", "ERROR")
                self.root.after(0, lambda: (
                    #messagebox.showerror("Download Error", f"yt-dlp error:\n{error_msg}"),
                    messagebox.showerror("Download Error", f"Not valid URL or Unsupported URL"),
                    self.status_label.config(text="Error: Could not process URL")
                ))
        
        except Exception as e:
            if not self.fetch_cancelled:
                self.log(f"Unexpected error: {type(e).__name__}: {str(e)}", "ERROR")
                self.root.after(0, lambda: (
                    messagebox.showerror("Error", f"Failed to fetch video info: {str(e)}"),
                    self.status_label.config(text="Error fetching information")
                ))
        
        finally:
            if not self.fetch_cancelled:
                self.root.after(0, lambda: self.set_loading_state(False))
    #Update the video information display
    def update_video_info(self):
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
    #Thumbanail download check and preview
    def download_thumbnail(self, thumbnail_url):
        if not thumbnail_url:
            self.root.after(0, self.clear_thumbnail)
            return        
        try:
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
        self.thumbnail_image = None
        self.thumbnail_label.configure(image="", text="No thumbnail available")
        
    #Set the UI state during loading operations    
    def set_loading_state(self, is_loading):
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
        
        # For audio, add MP3 conversion option at the top
        if media_type == 'audio' and filtered_formats:
            # Find the best audio format as a base for MP3 conversion
            best_audio = filtered_formats[0] if filtered_formats else None
            
            if best_audio:
                # Create a virtual MP3 format based on the best audio format
                mp3_format = best_audio.copy()
                mp3_format['format_id'] = 'mp3'
                mp3_format['ext'] = 'mp3'
                mp3_format['format_note'] = 'MP3 conversion'
                
                # Add MP3 as the first option
                item_id = self.format_tree.insert('', 0, values=(
                    'mp3', 
                    'mp3', 
                    f"{mp3_format.get('abr', 'best')} kbps", 
                    'N/A', 
                    'MP3 conversion from best audio'
                ))
                format_items['mp3'] = item_id
        
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
                continue
            
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
            if media_type == 'audio' and 'mp3' in format_items:
                # For audio, auto-select MP3 if available
                mp3_item = format_items['mp3']
                self.format_tree.selection_set(mp3_item)
                self.format_tree.see(mp3_item)
                self.log("Auto-selected MP3 format for audio", "DEBUG")
            elif media_type == 'video' and video_with_audio_formats:
                # For video, select the best format that has both video and audio
                best_format = video_with_audio_formats[0]
                best_format_id = best_format.get('format_id', '')
                
                if best_format_id in format_items:
                    best_item = format_items[best_format_id]
                    self.format_tree.selection_set(best_item)
                    self.format_tree.see(best_item)
                    self.log(f"Auto-selected best format with both video and audio: {best_format_id}", "DEBUG")
                else:
                    # Fallback to first item if something went wrong, for brevity
                    best_item = self.format_tree.get_children()[0]
                    self.format_tree.selection_set(best_item)
                    self.format_tree.see(best_item)
                    self.log(f"Auto-selected format: {self.format_tree.item(best_item, 'values')[0]}", "DEBUG")
            else:
                # For other cases or if no specific formats found, select the first (best) item
                best_item = self.format_tree.get_children()[0]
                self.format_tree.selection_set(best_item)
                self.format_tree.see(best_item)
                self.log(f"Auto-selected format: {self.format_tree.item(best_item, 'values')[0]}", "DEBUG")        

    def format_file_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/(1024*1024):.1f} MB"
        else:
            return f"{size_bytes/(1024*1024*1024):.1f} GB"
    
    def browse_save_location(self):
        directory = filedialog.askdirectory()
        if directory:
            self.save_path_entry.delete(0, tk.END)
            self.save_path_entry.insert(0, directory)
            self.log(f"Save location set to: {directory}", "DEBUG")

    #Download stuff start here! it work in multiple downloads too.
    def start_download(self):
        selected_items = self.format_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select a format to download")
            return            
        if not self.video_info:
            messagebox.showerror("Error", "No video information available")
            return            
        selected_item = selected_items[0]
        format_values = self.format_tree.item(selected_item, 'values')
        format_id = format_values[0]
            
        # Determine if the selected format has audio by checking the actual format data
        selected_format = None
        is_video_only = False
        is_mp3_conversion = (format_id == 'mp3')
        
        # If it's not MP3 conversion, find the selected format details
        if not is_mp3_conversion:
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
            
        self.cancel_flag = False
                
        # Enable cancel button if it exists
        if hasattr(self, 'cancel_button'):
            self.cancel_button.config(state=tk.NORMAL)
            
        if is_mp3_conversion:
            self.log("Starting MP3 download and conversion", "INFO")
            self.download_thread = threading.Thread(
                target=self._download_mp3, 
                args=(save_path,),
                daemon=True
            )
            self.download_thread.start()
            # Switch to log tab to show progress
            self.notebook.select(1)  # Index 1 is the Verbose tab, im staying here
            
        else:
            # Handle video download with potential format combination, at main tab for now
            # Configure the format string for download
            download_format = format_id
            is_combined_format = False
                    
            # If it's a video-only format and we're in video mode, ask user about merging
            media_type = self.media_type.get()
            if media_type == 'video' and is_video_only and selected_format:
                # Ask user if they want to merge with audio
                user_choice = messagebox.askyesnocancel("Video Only Format", 
                                "The selected format doesn't include audio. Do you want to download and combine with audio?\n\n"
                                "• Yes - Download and combine with best audio\n"
                                "• No - Download video only without audio\n"
                                "• Cancel - Abort the download")
                
                if user_choice is None:  # User closed the dialog or clicked Cancel
                    self.log("Download canceled by user", "INFO")
                    return
                    
                elif user_choice:  # User chose to merge with audio
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
                                
                    self.log(f"User selected to combine with audio. Using format string: {download_format}", "INFO")
                else:
                    # User chose not to merge - download video only
                    self.log(f"User selected to download video-only format: {format_id}", "INFO")
            
            self.log(f"Starting download with format specification: {download_format}", "INFO")
            self.download_thread = threading.Thread(
                target=self._download_thread, 
                args=(download_format, save_path, is_combined_format),
                daemon=True
            )
            self.download_thread.start()
            # Switch to log tab to show progress
            self.notebook.select(1)  # Index 1 is the Verbose tab

    def _download_mp3(self, save_path):
        self.root.after(0, lambda: (self.status_label.config(text="Downloading MP3...")))
        self.root.after(0, lambda: (self.progress.__setitem__('value', 0)))
        start_time = time.time()
        self.current_download_path = None
        def progress_hook(d):
            if self.cancel_flag:
                return
            
            if d['status'] == 'downloading':
                if not hasattr(progress_hook, "download_started"):
                    progress_hook.download_started = True
                    self.log(f"MP3 download started: {d.get('filename', 'unknown file')}", "INFO")
            
                # Calculate progress if available
                if d.get('downloaded_bytes') and d.get('total_bytes'):
                    p = int(d['downloaded_bytes'] / d['total_bytes'] * 100)
                    self.root.after(0, lambda: (self.progress.__setitem__('value', p)))
                
                    # Only update status every 1% to reduce GUI overhead
                    if not hasattr(progress_hook, "last_percent") or p != progress_hook.last_percent:
                        progress_hook.last_percent = p
                        self.root.after(0, lambda: (self.status_label.config(
                            text=f"Downloading MP3... {p}% ({self.format_file_size(d['downloaded_bytes'])}/{self.format_file_size(d['total_bytes'])})"
                        )))
                
                    # Log progress at 10% intervals
                    if not hasattr(progress_hook, "last_log_percent") or (p // 10) > (progress_hook.last_log_percent // 10):
                        progress_hook.last_log_percent = p
                        self.log(f"MP3 download progress: {p}%", "DEBUG")
                
                elif d.get('downloaded_bytes') and d.get('total_bytes_estimate'):
                    p = int(d['downloaded_bytes'] / d['total_bytes_estimate'] * 100)
                    self.root.after(0, lambda: (self.progress.__setitem__('value', p)))
                
                    if not hasattr(progress_hook, "last_percent") or p != progress_hook.last_percent:
                        progress_hook.last_percent = p
                        self.root.after(0, lambda: (self.status_label.config(
                            text=f"Downloading MP3... {p}% (estimated)"
                        )))
                
                else:
                    # If it can't calculate percentage, show download speed.
                    if d.get('_speed_str'):
                        self.root.after(0, lambda: (self.status_label.config(
                            text=f"Downloading MP3... ({d.get('_speed_str', 'N/A')})"
                        )))
                    
            elif d['status'] == 'finished':
                self.root.after(0, lambda: (self.progress.__setitem__('value', 100)))
                if d.get('filename'):
                    self.current_download_path = d.get('filename')
                    self.log(f"MP3 download finished: {self.current_download_path}", "INFO")
                    self.root.after(0, lambda: (self.status_label.config(text="Converting to MP3...")))
                    
            elif d['status'] == 'error':
                self.root.after(0, lambda: (self.status_label.config(text=f"Error: {d.get('error', 'Unknown error')}")))
                self.log(f"MP3 download error: {d.get('error', 'Unknown error')}", "ERROR")
        
        try:
            # Function to create a unique filename
            def get_unique_filename(base_path):
                if not os.path.exists(base_path):
                    return base_path                    
                name, ext = os.path.splitext(base_path)
                counter = 1                
                while True:
                    new_path = f"{name}_{counter}{ext}"
                    if not os.path.exists(new_path):
                        return new_path
                    counter += 1
                    
            base_outtmpl = os.path.join(save_path, '%(title)s-%(id)s.%(ext)s')
            
            # Set up yt-dlp options for MP3 conversion
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': base_outtmpl,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [progress_hook],
                'quiet': False,
                'no_warnings': False,
            }
            
            self.log(f"Starting MP3 download with options: {ydl_opts}", "INFO")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if not self.cancel_flag:
                    ydl.download([self.video_info['webpage_url']])
            
            elapsed = time.time() - start_time
            
            if self.cancel_flag:
                self.root.after(0, lambda: self.status_label.config(text="MP3 download cancelled"))
                self.log("MP3 download was cancelled by user", "INFO")
            else:
                self.root.after(0, lambda: self.status_label.config(text=f"MP3 download completed in {elapsed:.1f} seconds!"))
                self.root.after(0, lambda: messagebox.showinfo("Success", "MP3 download completed successfully!"))
                
                # Add the file to our downloads list and refresh the tab
                if self.current_download_path:
                    # Ensure this file isn't already in the list
                    if self.current_download_path not in self.downloaded_files:
                        self.downloaded_files.append(self.current_download_path)                        
                    self.root.after(0, self.refresh_downloads_list)                    
                    # Switch to the downloads tab to show the result
                    self.root.after(0, lambda: self.notebook.select(3))                    
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
                self.root.after(0, lambda: self.status_label.config(text="MP3 download cancelled"))
                self.log("MP3 download was cancelled by user", "INFO")
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", f"MP3 download failed: {str(e)}"))
                self.root.after(0, lambda: self.status_label.config(text="MP3 download failed"))
                self.log(f"MP3 download failed: {str(e)}", "ERROR")
    def cancel_download(self):
        if self.download_thread and self.download_thread.is_alive():
            self.cancel_flag = True
            self.log("Download cancellation requested", "INFO")
            self.status_label.config(text="Cancelling download...")
                
    def _download_thread(self, format_id, save_path, is_combined_format=False):
        self.root.after(0, lambda: (self.status_label.config(text="Downloading...")))
        self.root.after(0, lambda: (self.progress.__setitem__('value', 0)))

        start_time = time.time()
        self.current_download_path = None  # Reset the path
        downloaded_file_reported = False   # Flag to track if the file has been reported

        def progress_hook(d):
            if self.cancel_flag:
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
                    # If it can't calculate percentage, show download speed.
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

        # Add a timeout mechanism
        start_time = time.time()
        max_processing_time = 5  # 5 seconds timeout

        try:
            # Basic template for output filename - no need for unique filenames now
            base_outtmpl = os.path.join(save_path, '%(title)s-%(id)s.%(ext)s')            
            self.log(f"Using format specification: {format_id}", "INFO")

            # Determine the merge output format based on the format_id
            # If it contains 'webm', use webm as merge format, otherwise use mp4
            merge_format = 'webm' if 'webm' in format_id.lower() else 'mp4'
            self.log(f"Using merge format: {merge_format}", "INFO")
            
            ydl_opts = {
                'format': format_id,
                'outtmpl': base_outtmpl,
                'progress_hooks': [progress_hook],
                'postprocessor_hooks': [post_process_hook],
                'quiet': False,
                'no_warnings': False,
                'merge_output_format': merge_format,  # Use the appropriate format
                'overwrites': True, # Allow overwriting of files
            }            
            
            self.log(f"yt-dlp options: {ydl_opts}", "DEBUG")            
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if not self.cancel_flag:
                    ydl.download([self.video_info['webpage_url']])            
            
            elapsed = time.time() - start_time            
            
            # Check if we need to force-complete due to timeout
            force_complete = (time.time() - start_time) > max_processing_time and not self.cancel_flag
            
            if self.cancel_flag:
                self.root.after(0, lambda: self.status_label.config(text="Download cancelled"))
                self.log("Download was cancelled by user", "INFO")
            elif force_complete:
                self.log("Post-processing timeout reached, forcing completion", "WARNING")
                self.root.after(0, lambda: self.status_label.config(text=f"Download completed in {elapsed:.1f} seconds!"))
                self.root.after(0, lambda: messagebox.showinfo("Success", "Download completed successfully!"))
                
                # We may not have the current_download_path set, so try to find it
                if not self.current_download_path:
                    # Try to guess the file path from the template
                    possible_path = ydl.prepare_filename(self.video_info)
                    if os.path.exists(possible_path):
                        self.current_download_path = possible_path
                        self.log(f"Force detected download path: {self.current_download_path}", "INFO")
                    else:
                        # Look for files in the save path that were recently modified
                        recent_files = [f for f in os.listdir(save_path) if 
                                    os.path.isfile(os.path.join(save_path, f)) and 
                                    time.time() - os.path.getmtime(os.path.join(save_path, f)) < elapsed + 2]
                        if recent_files:
                            self.current_download_path = os.path.join(save_path, recent_files[0])
                            self.log(f"Force detected recent file: {self.current_download_path}", "INFO")
                
                # Proceed with the rest of the completion logic
                if self.current_download_path:
                    if self.current_download_path not in self.downloaded_files:
                        self.downloaded_files.append(self.current_download_path)                        
                    self.root.after(0, self.refresh_downloads_list)                    
                    self.root.after(0, lambda: self.notebook.select(3))
                    
                    def select_new_file():
                        for item in self.downloads_tree.get_children():
                            if self.downloads_tree.item(item, 'values')[0] == os.path.basename(self.current_download_path):
                                self.downloads_tree.selection_set(item)
                                self.downloads_tree.see(item)
                                self.on_download_selected(None)                    
                    self.root.after(100, select_new_file)
            else:
                self.root.after(0, lambda: self.status_label.config(text=f"Download completed in {elapsed:.1f} seconds!"))
                self.root.after(0, lambda: messagebox.showinfo("Success", "Download completed successfully!"))
                
                # Add the file to our downloads list and refresh the tab
                if self.current_download_path:
                    # Ensure this file isn't already in the list
                    if self.current_download_path not in self.downloaded_files:
                        self.downloaded_files.append(self.current_download_path)                        
                    self.root.after(0, self.refresh_downloads_list)                    
                    
                    # Switch to the downloads tab to show the result
                    self.root.after(0, lambda: self.notebook.select(3))  # Index 3 is Downloads tab                    
                    
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
    #Refresh the downloads list in the Downloads tab with files organized by folders
    def refresh_downloads_list(self):
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
        
        # Lists to store files with their metadata for sorting
        video_files = []
        audio_files = []
        other_files = []
        
        # First, add any files that are in our tracked downloads list
        for file_path in self.downloaded_files:
            if os.path.exists(file_path):
                all_files_found.add(file_path)
                filename = os.path.basename(file_path)
                
                # Get file info
                try:
                    file_stats = os.stat(file_path)
                    file_size = self.format_file_size(file_stats.st_size)
                    mod_time_str = datetime.datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                    mod_time = file_stats.st_mtime  # Store actual timestamp for sorting
                except:
                    file_size = "Unknown"
                    mod_time_str = "Unknown"
                    mod_time = 0
                
                # Determine the category based on file extension
                ext = os.path.splitext(filename)[1].lower()
                file_info = (filename, mod_time_str, file_size, file_path, mod_time)
                
                if ext in video_extensions:
                    video_files.append(file_info)
                elif ext in audio_extensions:
                    audio_files.append(file_info)
                else:
                    other_files.append(file_info)
        
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
                        # Avoiding scan too deep
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
                                    mod_time_str = datetime.datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                                    mod_time = file_stats.st_mtime  # Store actual timestamp for sorting
                                except:
                                    file_size = "Unknown"
                                    mod_time_str = "Unknown"
                                    mod_time = 0
                                
                                # Add to the appropriate category list
                                file_info = (file, mod_time_str, file_size, file_path, mod_time)
                                
                                if ext in video_extensions:
                                    video_files.append(file_info)
                                else:
                                    audio_files.append(file_info)
                                
                                # Add to our tracked downloads if not already there
                                if file_path not in self.downloaded_files:
                                    self.downloaded_files.append(file_path)
        except Exception as e:
            self.log(f"Error scanning for media files: {str(e)}", "ERROR")
        
        # Sort files by modification time (newest first)
        video_files.sort(key=lambda x: x[4], reverse=True)
        audio_files.sort(key=lambda x: x[4], reverse=True)
        other_files.sort(key=lambda x: x[4], reverse=True)
        
        # Track the latest file's ID to select it later
        latest_file_id = None
        latest_file_time = 0
        
        # Insert sorted video files
        for idx, (filename, mod_time_str, file_size, file_path, mod_time) in enumerate(video_files):
            item_id = self.downloads_tree.insert(video_folder, 'end', values=(filename, mod_time_str, file_size), tags=(file_path,))
            
            # Track the most recent file
            if mod_time > latest_file_time:
                latest_file_time = mod_time
                latest_file_id = item_id
        
        # Insert sorted audio files
        for idx, (filename, mod_time_str, file_size, file_path, mod_time) in enumerate(audio_files):
            item_id = self.downloads_tree.insert(audio_folder, 'end', values=(filename, mod_time_str, file_size), tags=(file_path,))
            
            # Track the most recent file
            if mod_time > latest_file_time:
                latest_file_time = mod_time
                latest_file_id = item_id
        
        # Insert sorted other files
        for idx, (filename, mod_time_str, file_size, file_path, mod_time) in enumerate(other_files):
            item_id = self.downloads_tree.insert(other_folder, 'end', values=(filename, mod_time_str, file_size), tags=(file_path,))
            
            # Track the most recent file
            if mod_time > latest_file_time:
                latest_file_time = mod_time
                latest_file_id = item_id
        
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
        
        # Select the most recently modified file if any were found
        if latest_file_id:
            # First ensure all parent nodes are expanded
            parent_id = self.downloads_tree.parent(latest_file_id)
            if parent_id:
                self.downloads_tree.item(parent_id, open=True)
            
            # Select and see the latest file
            self.downloads_tree.selection_set(latest_file_id)
            self.downloads_tree.see(latest_file_id)  # Ensure the selected item is visible
            self.downloads_tree.focus(latest_file_id)  # Also set keyboard focus to this item
            
            # Update the UI
            self.downloads_tree.update_idletasks()
            
            # Store the latest file path for easy access if needed elsewhere
            if latest_file_id and hasattr(self, 'latest_file_path'):
                file_tags = self.downloads_tree.item(latest_file_id, "tags")
                if file_tags:
                    self.latest_file_path = file_tags[0]
        
        self.log(f"Downloads list refreshed with {len(all_files_found)} files", "DEBUG")

    #Handle when a download is selected in the downloads list
    def on_download_selected(self, event):
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
    #Play the selected file using default system player
    def play_selected_file(self):
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

    #play video both as thumbanail and local video in default browser
    def play_video(self, event=None):
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
            webbrowser.open(video_url)

    def open_containing_folder(self):
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
    #Add a message to the log with timestamp and level
    def log(self, message, level="INFO"):
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
    #Changing logging level
    def set_log_level(self, level):
        if level in ["INFO", "DEBUG", "ERROR"]:
            self.log_level = level
            self.log(f"Log level changed to {level}", "INFO")
    #Clear log text area
    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.log("Log cleared", "INFO")

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    root.mainloop()
