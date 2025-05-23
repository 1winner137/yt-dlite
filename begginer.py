import contextlib
import copy
import hashlib
import json
import os
import queue
import re
import sys
import time
import threading
import types
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
        self.stop_event = threading.Event()
        
        # Configure styles
        self.style = ttk.Style()
        self.style.configure('Separator.TFrame', background='#e0e0e0')
        
        # Main Frame Content start here
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Enable responsive layout
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # Search Bar Section (Horizontal)
        search_frame = ttk.Frame(self.main_frame)
        search_frame.grid(row=0, column=0, sticky="ew", pady=5)
        search_frame.columnconfigure(1, weight=1)
        
        # Search buttons
        search_label = ttk.Label(search_frame, text="Search here:", font=("Helvetica", 9, "bold"))
        search_label.grid(row=0, column=0, padx=5, sticky="w")
        
        # Create Entry with placeholder
        placeholder = "Search anything or paste link (URL)"

        self.search_entry = ttk.Entry(search_frame, foreground="gray")
        self.search_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.search_entry.insert(0, placeholder)

        self.search_entry.bind("<FocusIn>", lambda e: (self.search_entry.delete(0, tk.END), self.search_entry.config(foreground="black")) if self.search_entry.get() == placeholder else None)
        self.search_entry.bind("<FocusOut>", lambda e: (self.search_entry.insert(0, placeholder), self.search_entry.config(foreground="gray")) if not self.search_entry.get() else None)
        self.search_entry.bind("<Return>", lambda event: self.search_engine())
        
        # Buttons in search frame
        button_frame = ttk.Frame(search_frame)
        button_frame.grid(row=0, column=2, sticky="e")
        
        self.paste_button = ttk.Button(button_frame, text="Paste", command=self.paste_from_clipboard)
        self.paste_button.pack(side=tk.LEFT, padx=2)

        self.search_button = ttk.Button(button_frame, text="🔍Search", command=self.search_engine)
        self.search_button.pack(side=tk.LEFT, padx=2)

        self.cancel_buttonn = ttk.Button(button_frame, text="X Cancel", command=self.cancel_search)
        self.cancel_buttonn.pack(side=tk.LEFT, padx=2)
        self.cancel_buttonn.config(state=tk.DISABLED)

        # Set default download state path
        self.download_state_path = os.path.join(
            os.path.expanduser("~"),
            "Downloads",
            "yt-dlite",
            ".download_state"
        )

        # Scrollable Frame for Results from searching
        self.result_frame = ttk.Frame(self.main_frame)
        self.result_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        self.result_frame.columnconfigure(0, weight=1)
        self.result_frame.rowconfigure(0, weight=1)

        self.scrollable_canvas = tk.Canvas(self.result_frame, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.scrollable_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.scrollable_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.scrollable_canvas.configure(scrollregion=self.scrollable_canvas.bbox("all"))
        )

        self.canvas_window = self.scrollable_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="n")
        self.scrollable_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Make scrollable frame expand
        self.scrollable_canvas.bind("<Configure>", self.configure_scrollable_frame)
        self.scrollable_frame.columnconfigure(0, weight=1)

        # Welcome frame
        welcome_frame = ttk.Frame(self.scrollable_frame)
        welcome_frame.grid(row=0, column=0, padx=60, pady=(10, 40), sticky="n")
        welcome_frame.columnconfigure(0, weight=1)
        welcome_title = ttk.Label(
            welcome_frame,
            text="Welcome to YT-DLITE",
            font=("Arial", 40, "bold"),
            foreground="red",
            anchor="center",
            justify="center"
        )
        welcome_title.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        arrow_text = [
            "EXPLORE   DISCOVER   DOWNLOAD",
            "  CONVERT   MANAGE   ENJOY  ",
            "     TRANSFORM   CREATE     ",
            "        SIMPLIFY           ",
            "          SHARE           ",
            "           ↑↑↑           ",
            "↑↑  Type anything or paste link in search bar ↑↑ ",
        ]

        self.arrow_labels = []

        for i, line in enumerate(arrow_text):
            arrow_line = ttk.Label(
                welcome_frame,
                text=line,
                font=("Courier New", 16, "bold"),
                foreground=self.blend_colors("#ffffff", "#3a7ca5", 0),  # Start "invisible"
                anchor="center",
                justify="center"
            )
            arrow_line.grid(row=i + 1, column=0, sticky="ew", pady=2)
            self.arrow_labels.append(arrow_line)

        # Animate
        self.animate_arrows()

        # Display tips in black color
        def open_website(event):
            webbrowser.open("https://youtube.com/@proginsight?si=_wYmdecn0aHWIst_")

        # Create the label with new text
        tips_text = ttk.Label(
            welcome_frame, 
            text="Tips: For Help & Usage click here",
            font=("Arial", 9, "italic"),
            foreground="green",
            anchor="w",
            justify="right",
            cursor="hand2"  # Changes cursor to hand when hovering over the link
        )
        tips_text.grid(row=25, column=0, sticky="ew", pady=(0, 0))

        # Bind the click event to the label
        tips_text.bind("<Button-1>", open_website)

        # just to be shure scrollable frame expands even full screen
        self.scrollable_frame.rowconfigure(0, weight=1)

        # Bottom section for download controls, progress, etc...
        bottom_frame = ttk.Frame(self.main_frame)
        bottom_frame.grid(row=2, column=0, sticky="ew", pady=5)
        bottom_frame.columnconfigure(0, weight=1)

        # Add incomplete downloads section
        self.init_incomplete_downloads_section(bottom_frame)

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

        # The buttons
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(fill=tk.X, pady=0.1)
        
        # Cancel button
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel_download)
        self.cancel_button.pack(side=tk.LEFT, padx=1)
        self.cancel_button.config(state=tk.DISABLED)
        
        # Initialize resume and restart buttons (initially disabled)
        self.init_recovery_buttons(button_frame)
        
        # Check for incomplete downloads when starting
        self.after(1000, self.check_incomplete_downloads)

    # Create a collapsible frame for incomplete downloads, tose appear when application startup
    def init_incomplete_downloads_section(self, parent_frame):
        incomplete_frame = ttk.LabelFrame(parent_frame, text="Incomplete Downloads")
        incomplete_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Add a treeview to display incomplete downloads
        columns = ("title","url", "date")
        self.incomplete_tree = ttk.Treeview(incomplete_frame, columns=columns, show="headings", height=3)
        
        # Configure column headings
        self.incomplete_tree.heading("title", text="Title")
        self.incomplete_tree.heading("url", text="URL")
        self.incomplete_tree.heading("date", text="Date")
        #self.incomplete_tree.heading("format", text="Format")
        
        # Configure column widths
        self.incomplete_tree.column("title", width=150)
        self.incomplete_tree.column("url", width=150)
        self.incomplete_tree.column("date", width=150)
        #self.incomplete_tree.column("format", width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(incomplete_frame, orient=tk.VERTICAL, command=self.incomplete_tree.yview)
        self.incomplete_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.incomplete_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add a button frame for actions
        action_frame = ttk.Frame(incomplete_frame)
        action_frame.pack(fill=tk.X, pady=5)

        # Resume button
        resume_button = ttk.Button(action_frame, text="Resume Selected", command=self.resume_selected_download)
        resume_button.pack(side=tk.LEFT, padx=5)

        # Remove button
        remove_button = ttk.Button(action_frame, text="Remove Selected", command=self.remove_selected_download)
        remove_button.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_frame = ttk.Frame(incomplete_frame)
        cancel_frame.pack(fill=tk.X, pady=(0, 5))
        cancel_button = ttk.Button(cancel_frame, text="Ignore for now", command=self.cancel_incomplete_downloads_section)
        cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Double-click to resume
        self.incomplete_tree.bind("<Double-1>", lambda event: self.resume_selected_download())
        
        # But i initially hide the incomplete downloads sectionm until the incompletes are present.
        incomplete_frame.pack_forget()
        self.incomplete_frame = incomplete_frame
    
    def cancel_incomplete_downloads_section(self):
        if hasattr(self, 'incomplete_frame') and self.incomplete_frame.winfo_ismapped():
            self.incomplete_frame.pack_forget()

    # Get all incomplete downloads
    def check_incomplete_downloads(self):
        incomplete_downloads = self.get_incomplete_downloads()
        if incomplete_downloads:
            # Clear existing items
            for item in self.incomplete_tree.get_children():
                self.incomplete_tree.delete(item)            
            # Add new items
            for download in incomplete_downloads:
                title = download.get('title', 'Unknown Title')
                url = download.get('url', 'Unknown URL')
                date = download.get('date', 'Unknown Date')
                # Truncate URL if too long, just for brevity
                display_url = url[:50] + "..." if len(url) > 50 else url
                item_id = self.incomplete_tree.insert("", tk.END, values=(title, display_url, date))

                # Store the full download state as a tag (optional)
                self.incomplete_tree.item(item_id, tags=(json.dumps(download),))
            
            # Show the incomplete downloads section
            self.incomplete_frame.pack(fill=tk.X, pady=5, padx=5, before=self.incomplete_frame.master.winfo_children()[1])
        else:
            # Hide the section if no incomplete downloads
            self.incomplete_frame.pack_forget()

    def resume_selected_download(self):
        selected_items = self.incomplete_tree.selection()# Get selected item
        if not selected_items:
            return
            
        selected_item = selected_items[0]
        
        # Get the download state from the item tags
        tags = self.incomplete_tree.item(selected_item, "tags")
        if not tags:
            return
            
        try:
            # Parse the download state
            download_state = json.loads(tags[0])
            
            # Extract the necessary information
            url = download_state.get('url')
            format_string = download_state.get('format_string')
            output_path = download_state.get('output_path')
            
            if not url or not format_string or not output_path:
                self.status_label.config(text="Invalid download state information", foreground="red")
                return
                
            # Update status
            self.status_label.config(text=f"Resuming download: {url}")
            
            # Delete the JSON state file before starting the download, to avoid multiple json for same file
            url_hash = hashlib.md5(url.encode()).hexdigest()
            state_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download_state")
            state_file = os.path.join(state_dir, f"{url_hash}.json")
            
            if os.path.exists(state_file):
                os.remove(state_file)
                print(f"Deleted state file: {state_file}")
            
            # Set the current URL for reference
            self.current_url = url
            
            # Call the existing download thread with resume=True
            download_thread = threading.Thread(
                target=self.download_thread,
                args=(url, format_string, output_path, True)  # True for resume
            )
            download_thread.daemon = True
            download_thread.start()
            
            # Remove from the tree view after starting the download, just to be clean
            self.incomplete_tree.delete(selected_item)
            
            # Hide the section if empty
            if not self.incomplete_tree.get_children():
                self.incomplete_frame.pack_forget()
                
        except Exception as e:
            print(f"Error resuming download: {str(e)}")
            self.status_label.config(text=f"Error resuming download: {str(e)}", foreground="red")

    def remove_selected_download(self):
        #when user remove incomplete download, it have to remove the incomplete downloads too.
        selected_items = self.incomplete_tree.selection()#Get selected item
        if not selected_items:
            return
            
        selected_item = selected_items[0]
        
        # Get the download state from the item tags
        tags = self.incomplete_tree.item(selected_item, "tags")
        if not tags:
            return
        
        try:
            # Parse the download state
            download_state = json.loads(tags[0])
            
            # Get URL and title for state file deletion
            url = download_state.get('url')
            title = download_state.get('title', 'Unknown Title')
            output_path = download_state.get('output_path')
            
            # Show confirmation dialog with title
            if not messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove the download:\n\n{title}?"):
                return
            
            if url:
                # Delete state file
                url_hash = hashlib.md5(url.encode()).hexdigest()
                state_file = os.path.join(
                    self.download_state_path,
                    f"{url_hash}.json"
                )
                
                if os.path.exists(state_file):
                    try:
                        os.remove(state_file)
                        print(f"Deleted state file: {state_file}")
                    except Exception as e:
                        print(f"Error deleting state file: {str(e)}")
                
                # Get the download directory
                if output_path:
                    download_dir = os.path.join(
                        os.path.expanduser("~"),
                        "Downloads",
                        "yt-dlite"
                    )
                    
                    # I'm using string distance algorithm for better matching, we can improve in future if we need to
                    # And this is when removing downloaded state and even the related files, like *.part or *.ytdl
                    try:
                        if os.path.exists(download_dir):
                            # Extract base filename without extension from output_path if available
                            base_name = os.path.basename(output_path) if output_path else None
                            base_name_no_ext = os.path.splitext(base_name)[0] if base_name else None
                            #just for debugging
                            print(f"Looking for files related to: {title}")
                            print(f"Base output filename: {base_name_no_ext}")
                            
                            files_deleted = 0
                            
                            for file in os.listdir(download_dir):
                                if file.endswith(".part") or file.endswith(".ytdl"):
                                    should_delete = False
                                    if base_name_no_ext and base_name_no_ext in file:
                                        should_delete = True
                                    clean_filename = re.sub(r'\.(part|ytdl|mp4|webm|mkv).*$', '', file)
                                    
                                    # Calculate similarity using longest common substring approach
                                    # Normalize both strings for comparison
                                    norm_title = re.sub(r'[^\w\s]', '', title).lower()
                                    norm_filename = re.sub(r'[^\w\s]', '', clean_filename).lower()
                                    
                                    # Use longest common substring as a similarity metric
                                    lcs_length = self.longest_common_substring_length(norm_title, norm_filename)
                                    title_length = len(norm_title)
                                    filename_length = len(norm_filename)
                                    
                                    # Calculate similarity ratio (0-1)
                                    similarity = lcs_length / min(title_length, filename_length) if min(title_length, filename_length) > 0 else 0
                                    
                                    print(f"File: {file}, Similarity: {similarity:.2f}")
                                    
                                    # If similarity is above threshold, mark for deletion
                                    if similarity >= 0.7:  # 70% similarity threshold
                                        should_delete = True
                                    
                                    if should_delete:
                                        file_path = os.path.join(download_dir, file)
                                        try:
                                            os.remove(file_path)
                                            files_deleted += 1
                                            print(f"Deleted file: {file_path}")
                                        except Exception as e:
                                            print(f"Error deleting file {file_path}: {str(e)}")
                            
                            print(f"Total files deleted: {files_deleted}")
                    except Exception as e:
                        print(f"Error accessing download directory: {str(e)}")
            
            # Remove from the tree view
            self.incomplete_tree.delete(selected_item)
            
            # Hide the section if empty
            if not self.incomplete_tree.get_children():
                self.incomplete_frame.pack_forget()
                
            # Update status to confirm removal
            self.status_label.config(text="Download removed", foreground="green")
            
            # Show success message
            messagebox.showinfo("Success", "Download removed and temporary files cleaned up.")
                
        except Exception as e:
            print(f"Error removing download: {str(e)}")
            self.status_label.config(text=f"Error removing download: {str(e)}", foreground="red")
            messagebox.showerror("Error", f"Error removing download: {str(e)}")
    #Calculate the lenght of the name(substrings) in json against the incomplete download names
    def longest_common_substring_length(self, s1, s2):
        # Create a table to store lengths of longest common substrings
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # To store the length of the longest common substring
        result = 0
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                    result = max(result, dp[i][j])
        
        return result

    #For welcome animation      
    def blend_colors(self, color1, color2, ratio):
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        return f"#{r:02x}{g:02x}{b:02x}"

    def animate_arrows(self):
        step = 0
        
        # Define multiple colors for cycling
        colors = [
            "#1a2a6c", "#b21f1f", "#fdbb2d",  # Sunset gradient
            "#00b09b", "#96c93d",             # Green meadow
            "#ff758c", "#ff7eb3",             # Pink love
            "#7f7fd5", "#86a8e7", "#91eae4",  # Aqua marine
            "#4568dc", "#b06ab3",             # Purple love
            "#43cea2", "#185a9d",             # Endless river
            "#ff512f", "#f09819",             # Orange fun
            "#8e2de2", "#4a00e0"              # Purple dream
        ]
        color_index = 0
        
        def update_animation():
            nonlocal step, color_index
            
            # First check if widget still exists and window hasn't been closed
            if not hasattr(self, 'arrow_labels') or not self.winfo_exists():
                return  # Stop animation if widget is destroyed
            
            # Calculate which colors to use based on current color_index
            from_color = colors[color_index]
            to_color = colors[(color_index + 1) % len(colors)]
            
            for i, label in enumerate(self.arrow_labels):
                # Check if each individual label still exists
                try:
                    # Staggered animation - each line starts a bit later
                    delay = i * 1000
                    if step * 500 >= delay:  # 500ms per step
                        progress = min(1.0, (step * 500 - delay) / 500)
                        color = self.blend_colors(from_color, to_color, progress)
                        label.configure(foreground=color)
                except (tk.TclError, AttributeError):
                    # Skip this label if it no longer exists 
                    continue
            
            step += 1
            
            # If animation cycle completes
            if step >= 20:
                step = 0  # Reset step counter
                color_index = (color_index + 1) % (len(colors) - 1)  # Move to next color pair
            
            # Continue animation loop if widget still exists
            if hasattr(self, 'arrow_labels') and self.winfo_exists():
                self.after(400, update_animation)
        
        # Start the animation
        update_animation()

    def configure_scrollable_frame(self, event):
        canvas_width = event.width
        self.scrollable_canvas.itemconfig(self.canvas_window, width=canvas_width)
        for child in self.scrollable_frame.winfo_children():
            if hasattr(child, 'configure_width'):
                child.configure_width(canvas_width - 20)  # 20 pixels margin

    def paste_from_clipboard(self):
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
        self.cancel_incomplete_downloads_section()
        self.cancel_buttonn.config(state=tk.NORMAL)
        query = self.search_entry.get().strip()
        if not query:
            # Show message to enter a link if query is empty
            self.status_label.config(text="Please enter a search term or URL", foreground="red")
            self.parent.after(0, lambda: messagebox.showerror("Error", "Please enter a search term or URL"))
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
        if not self._search_active:  
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
            self.status_label.config(text="Video ready for download!", foreground="green")
            self.open_format_selection_popup(url)

    def process_playlist(self, url):
        if not self._search_active:  
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
        self.parent.config(cursor="watch")  
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
                'playlistend': 50,  # Increase the number of results (adjust as needed)
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
                    search_results = ydl.extract_info(f"ytsearch50:{query}", download=False)

                    # Restore original stdout and output methods
                    sys.stdout = original_stdout
                    ydl.to_screen = original_to_screen
                    ydl.to_stderr = original_to_stderr

                    if not search_results or 'entries' not in search_results:
                        if self._search_active:  
                            self.parent.after(0, lambda: self.status_label.config(
                                text="No results found", 
                                foreground="red"
                            ))
                            self.cancel_buttonn.config(state=tk.DISABLED)
                        return
                    
                    self.parent.after(0, lambda: self.status_label.config(text=""))

                    # Display a count of found videos
                    self.parent.config(cursor="")
                    video_count = len(search_results['entries'])
                    if video_count > 0 and self._search_active:
                        self.parent.after(0, lambda: self.status_label.config(
                            text=f"Found {video_count} videos", 
                            foreground="green"
                        ))
                        self.cancel_buttonn.config(state=tk.DISABLED)

                    for i, video in enumerate(search_results['entries']):
                        if not video or not self._search_active:  
                            self.parent.after(0, lambda: self.status_label.config(
                                text="Search Canceled", foreground="red"
                            )) 
                            return
                        
                        # Schedule UI updates in main thread
                        self.parent.after(0, self.create_video_item, video, i)
                        

            except Exception as e:
                if self._search_active:  
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
        self._search_active = True
        self.search_thread = threading.Thread(target=search, daemon=True)
        self.search_thread.start()

    #Display a network error popup
    def show_network_error_popup(self, _):
        import tkinter.messagebox as messagebox
        messagebox.showerror("Network Error", "Failed to connect. Check your internet and try again.")
        self.parent.config(cursor="")
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
    #Thumbanail, or bunner of the video, lets try to be faster when fetching
    def download_thumbnail(self, thumbnail_url, label=None):
        if label is None:
            label = self.thumbnail_label            
        if not thumbnail_url:
            self.parent.after(0, lambda: label.config(text="No thumbnail or unstable network", image=''))
            return
            
        # Try medium quality format
        if "hqdefault" in thumbnail_url:
            thumbnail_url = thumbnail_url.replace("hqdefault", "mqdefault")
                
        if not thumbnail_url.startswith(('http://', 'https://')):
            self.parent.after(0, lambda: label.config(text="Invalid URL", image=''))
            return            
        
        # Use a shorter timeout for faster response
        timeout = 5
        img_data = None
        
        # First attempt with requests usually it is much faster
        try:
            response = requests.get(thumbnail_url, stream=True, timeout=timeout)
            if response.status_code == 200:
                img_data = response.content
        except:
            pass
        
        # Only try the backup method if the first one failed
        if img_data is None:
            try:
                with urllib.request.urlopen(thumbnail_url, timeout=timeout) as response:
                    img_data = response.read()
            except:
                # If both methods fail with the medium quality, try the original URL
                if "mqdefault" in thumbnail_url:
                    original_url = thumbnail_url.replace("mqdefault", "hqdefault")
                    try:
                        response = requests.get(original_url, stream=True, timeout=timeout)
                        if response.status_code == 200:
                            img_data = response.content
                    except:
                        pass
        
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
            except:
                pass
        
        # If we get here, we couldn't load the thumbnail
        self.parent.after(0, lambda: label.config(text="No thumbnail or unstable network", image=''))
        return False

    #Hook to handle yt-dlp errors
    def yt_dlp_hook(self, d):
        if d['status'] == 'error':
            print(f"yt-dlp error: {d['error']}")
                      
    def create_download_button(self, url):
        self.status_label.config(text="Preparing download options...", foreground="blue")
        print(f"Creating download options for: {url}")
        title = None
        if isinstance(url, dict):
            valid_url = url.get('url', '')
            title = url.get('title', 'Download')
            print(f"Extracted valid URL: {valid_url}")
            url = valid_url
        self.current_title = title #populating this for download_save state
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
        
        # Flag to track if the popup is still active
        format_popup.is_active = True
        
        # Handle window close event
        def on_popup_close():
            format_popup.is_active = False
            format_popup.destroy()
        
        format_popup.protocol("WM_DELETE_WINDOW", on_popup_close)
        
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
                        
                        # Update title label in main thread only if popup is still active
                        #This affect download state title when saving in json, but let's ignore it for now.
                        def update_title():
                            if format_popup.is_active and format_popup.winfo_exists():
                                title_text = fetched_title if len(fetched_title) <= 55 else fetched_title[:52] + "..."
                                title_label.config(text=f"Title: {title_text}")
                        self.current_titled = fetched_title  # populate for save download state
                        format_popup.after(0, update_title)
                except Exception as e:
                    # If there's an error, just show a generic title
                    def update_error():
                        if format_popup.is_active and format_popup.winfo_exists():
                            title_label.config(text="Title: Unable to retrieve")
                    
                    format_popup.after(0, update_error)
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
            ("MP4 - Best Quality(Auto)", "bestvideo[ext=mp4]+bestaudio[ext=mp4]/best[ext=mp4]/best --merge-output-format mp4 --embed-thumbnail --add-metadata"),
            ("MP4 - 4K (Ultra HD)", "bestvideo[ext=mp4][height<=2160]+bestaudio[ext=mp4]/best[ext=mp4][height<=2160]/best --merge-output-format mp4 --embed-thumbnail --add-metadata"),
            ("MP4 - 1440p(Crisp Details)", "bestvideo[ext=mp4][height<=1440]+bestaudio[ext=mp4]/best[ext=mp4][height<=1440]/best --merge-output-format mp4 --embed-thumbnail --add-metadata"),
            ("MP4 - 1080p(HD quality)", "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=mp4]/best[ext=mp4][height<=1080]/best --merge-output-format mp4 --embed-thumbnail --add-metadata"),
            ("MP4 - 720p(Balanced quality)", "bestvideo[ext=mp4][height<=720]+bestaudio[ext=mp4]/best[ext=mp4][height<=720]/best --merge-output-format mp4 --embed-thumbnail --add-metadata"),
            ("MP4 - 480p(Good for small screen)", "bestvideo[ext=mp4][height<=480]+bestaudio[ext=mp4]/best[ext=mp4][height<=480]/best --merge-output-format mp4 --embed-thumbnail --add-metadata"),
            ("MP4 - 360p(Mobile friendly)", "bestvideo[ext=mp4][height<=360]+bestaudio[ext=mp4]/best[ext=mp4][height<=360]/best --merge-output-format mp4 --embed-thumbnail --add-metadata"),
            ("MP4 - 240p(Lower data usage)", "bestvideo[ext=mp4][height<=240]+bestaudio[ext=mp4]/best[ext=mp4][height<=240]/best --merge-output-format mp4 --embed-thumbnail --add-metadata"),
            ("MP4 - Smallest Size", "worstvideo[ext=mp4]+worstaudio[ext=mp4]/worst[ext=mp4]/worst --merge-output-format mp4 --embed-thumbnail --add-metadata"),
            ("WebM - Best Quality", "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best --merge-output-format webm --embed-thumbnail --add-metadata"),
            ("WebM - 1080p", "bestvideo[ext=webm][height<=1080]+bestaudio[ext=webm]/best[ext=webm][height<=1080]/best --merge-output-format webm --embed-thumbnail --add-metadata"),
            ("WebM - 720p", "bestvideo[ext=webm][height<=720]+bestaudio[ext=webm]/best[ext=webm][height<=720]/best --merge-output-format webm --embed-thumbnail --add-metadata"),
            ("WebM - 480p", "bestvideo[ext=webm][height<=480]+bestaudio[ext=webm]/best[ext=webm][height<=480]/best --merge-output-format webm --embed-thumbnail --add-metadata"),
            ("MKV - Best Quality", "bestvideo+bestaudio --merge-output-format mkv --embed-thumbnail --add-metadata"),
            ("AVI - Best Quality", "bestvideo+bestaudio --merge-output-format avi --embed-thumbnail --add-metadata"),
            ("FLV - Best Quality", "bestvideo+bestaudio --merge-output-format flv --embed-thumbnail --add-metadata"),
            ("3GP - Mobile", "worst[ext=3gp]/worst --recode-video 3gp --embed-thumbnail --add-metadata"),
            ("MP4 - Video Only", "bestvideo[ext=mp4]-bestaudio/bestvideo[ext=mp4] --merge-output-format mp4 --embed-thumbnail --add-metadata"),
            ("WebM - Video Only", "bestvideo[ext=webm]-bestaudio/bestvideo[ext=webm] --merge-output-format webm --embed-thumbnail --add-metadata")
        ]

        audio_format_options = [
            ("MP3 - 320kbps(Best quality)", "bestaudio/best -x --audio-format mp3 --audio-quality 320K --embed-thumbnail --add-metadata"),
            ("MP3 - 256kbps(High quality)", "bestaudio/best -x --audio-format mp3 --audio-quality 256K --embed-thumbnail --add-metadata"),
            ("MP3 - 192kbps(Standard quality)", "bestaudio/best -x --audio-format mp3 --audio-quality 192K --embed-thumbnail --add-metadata"),
            ("MP3 - 128kbps(Good for mobile)", "bestaudio/best -x --audio-format mp3 --audio-quality 128K --embed-thumbnail --add-metadata"),
            ("MP3 - 96kbps(low data usage)", "bestaudio/best -x --audio-format mp3 --audio-quality 96K --embed-thumbnail --add-metadata"),
            ("M4A - Best Quality", "bestaudio/best -x --audio-format m4a --audio-quality 0 --embed-thumbnail --add-metadata"),
            ("M4A - Medium Quality", "bestaudio/best -x --audio-format m4a --audio-quality 2 --embed-thumbnail --add-metadata"),
            ("OGG - Best Quality", "bestaudio/best -x --audio-format vorbis --audio-quality 0 --embed-thumbnail --add-metadata"),
            ("OGG - Medium Quality", "bestaudio/best -x --audio-format vorbis --audio-quality 3 --embed-thumbnail --add-metadata"),
            ("OPUS - Best Quality", "bestaudio/best -x --audio-format opus --audio-quality 0 --embed-thumbnail --add-metadata"),
            ("FLAC - Lossless", "bestaudio/best -x --audio-format flac --embed-thumbnail --add-metadata"),
            ("WAV - Uncompressed", "bestaudio/best -x --audio-format wav --embed-thumbnail --add-metadata"),
            ("AAC - High Quality", "bestaudio/best -x --audio-format aac --audio-quality 0 --embed-thumbnail --add-metadata"),
            ("AIFF - Uncompressed", "bestaudio/best -x --audio-format aiff --embed-thumbnail --add-metadata"),
            ("WMA - High Quality", "bestaudio/best -x --audio-format wma --audio-quality 0 --embed-thumbnail --add-metadata")
        ]
        
        # Subtitle language options
        subtitle_language_options = [
            ("Auto-generated (English)", "en-auto"),
            ("Arabic", "ar"),            
            ("Chinese", "zh"),
            ("Dutch", "nl"),
            ("English", "en"),
            ("French", "fr"),
            ("German", "de"),
            ("Hindi", "hi"),
            ("Italian", "it"),
            ("Japanese", "ja"),
            ("Korean", "ko"),
            ("Polish", "pl"),
            ("Portuguese", "pt"),
            ("Russian", "ru"),
            ("Spanish", "es"),
            ("Swahili", "sw"),
            ("Swedish", "sv"),
            ("Thai", "th"),
            ("Turkish", "tr"),
            ("Vietnamese", "vi")
        ]
        
        # Variables for selections
        media_type_var = tk.StringVar(value="video")
        video_format_var = tk.StringVar(value=video_format_options[0][0])
        audio_format_var = tk.StringVar(value=audio_format_options[0][0])
        subtitle_var = tk.BooleanVar(value=False)  #subtitle checkbox
        subtitle_lang_var = tk.StringVar(value=subtitle_language_options[0][0])  #Language selection
        
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
        
        # Debugging prints
        print(f"start_download: URL = {url}")
        print(f"start_download: Selected format string = {format_string}")
        print(f"start_download: Output path = {output_path}")
        self.status_label.config(text="Starting download...", foreground="blue")
        self.progress['value'] = 0

        # Store current download parameters
        self.current_url = url
        self.current_format_string = format_string
        self.current_output_path = output_path

        # Reset flags
        self.cancel_requested = False
        self.download_cancelled = False

        # Reset stop event before starting new download
        self.stop_event.clear()

        # Enable/Disable buttons
        if hasattr(self, 'cancel_button'):
            self.cancel_button.config(state=tk.NORMAL)
        if hasattr(self, 'resume_button') and hasattr(self, 'restart_button'):
            self.resume_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.DISABLED)

        # Start download thread
        download_thread = threading.Thread(
            target=self.download_thread,
            args=(url, format_string, output_path, False)
        )
        download_thread.daemon = True
        download_thread.start()


    #Update the progress bar and status label with download progress
    def update_download_progress(self, d):
        if hasattr(self, 'cancel_requested') and self.cancel_requested:
            raise Exception("Download cancelled by user")
        
        # Initialize download tracker if doesn't exist
        if not hasattr(self, 'download_tracker'):
            self.download_tracker = {
                'total_steps': 3,  # Video download, audio download, merge
                'current_step': 1,
                'phase_name': 'Video',
                'format_type': None
            }
            
        # Detect format type from first download
        if self.download_tracker['format_type'] is None:
            format_id = d.get('info_dict', {}).get('format_id', '')
            if 'video' in format_id and 'audio' not in format_id:
                self.download_tracker['format_type'] = 'separate'  # Separate video+audio
            else:
                self.download_tracker['format_type'] = 'combined'  # Single download
                self.download_tracker['total_steps'] = 1
        
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            
            # Get filename information
            filename = d.get('filename', '').split('/')[-1].split('\\')[-1]  # Extract just the filename
            if len(filename) > 30:  # Truncate if too long
                filename = filename[:27] + "..."
            
            # Calculate percentage if total size is known, there is bug here, to be fixed next version
            if total > 0:
                # Calculate current file percentage
                file_percentage = (downloaded / total) * 100
                
                # Calculate overall percentage based on steps
                if self.download_tracker['format_type'] == 'separate':
                    # For separate video+audio: video=0-40%, audio=40-80%, merge=80-100%
                    step_size = 40
                    overall_progress = ((self.download_tracker['current_step'] - 1) * step_size) + (file_percentage * step_size / 100)
                else:
                    # For single file download: 0-90%, processing=90-100%
                    overall_progress = file_percentage * 0.9
                
                self.progress['value'] = overall_progress
                
                # Format size information
                downloaded_mb = downloaded / 1024 / 1024
                total_mb = total / 1024 / 1024
                size_text = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB"
                
                # Add download speed
                download_speed = d.get('speed', 0)
                if download_speed:
                    speed_text = f"{download_speed / 1024 / 1024:.2f} MB/s"
                else:
                    speed_text = "calculating..."
                
                # Prepare status text with phase indicator
                if self.download_tracker['format_type'] == 'separate':
                    phase_name = self.download_tracker['phase_name']
                    status_text = f"Downloading {phase_name} ({self.download_tracker['current_step']}/{self.download_tracker['total_steps']-1}): {filename} - {file_percentage:.1f}% ({size_text}) at {speed_text}"
                else:
                    status_text = f"Downloading: {filename} - {file_percentage:.1f}% ({size_text}) at {speed_text}"
                
                # Update the status label
                self.status_label.config(text=status_text)
                
                # Force update of the UI
                self.status_label.update_idletasks()
                self.progress.update_idletasks()
            else:
                # Unknown total size
                downloaded_mb = downloaded / 1024 / 1024
                self.status_label.config(text=f"Downloading: {filename} - {downloaded_mb:.1f} MB (size unknown)")
        
        elif d['status'] == 'finished':
            # Get filename information
            filename = d.get('filename', '').split('/')[-1].split('\\')[-1]
            
            if self.download_tracker['format_type'] == 'separate':
                if self.download_tracker['current_step'] == 1:
                    # Video finished, now downloading audio
                    self.download_tracker['current_step'] = 2
                    self.download_tracker['phase_name'] = 'Audio'
                    self.status_label.config(text="Video downloaded. Starting audio download...", foreground="blue")
                elif self.download_tracker['current_step'] == 2:
                    # Audio finished, now merging
                    self.download_tracker['current_step'] = 3
                    self.status_label.config(text="Audio downloaded. Merging video and audio...", foreground="blue")
                    self.progress['value'] = 80
                # Note: The merge completion will be handled by on_download_complete
            else:
                # Single format - just show processing
                self.status_label.config(text=f"Download finished. Processing file...", foreground="blue")
                self.progress['value'] = 90
            
            self.progress.update_idletasks()

    def download_thread(self, url, format_string, output_path, resume=False):
        self.cancel_button.config(state=tk.NORMAL)
        try:
            # Use queues for thread-safe communication with UI
            if not hasattr(self, 'ui_update_queue'):
                self.ui_update_queue = queue.Queue()
                # Start the UI updater in the main thread
                self.start_ui_updater()
            
            # Setup initialization timer
            self.init_start_time = time.time()
            self.download_started = False
            self.init_timer = threading.Timer(5.0, self.show_init_status, args=["Preparing engine..."])
            self.init_timer.daemon = True
            self.init_timer.start()
            
            # Setup second status timer
            self.almost_there_timer = threading.Timer(10.0, self.show_init_status, args=["Almost there..."])
            self.almost_there_timer.daemon = True
            self.almost_there_timer.start()
            
            # Setup network check timer
            self.network_check_timer = threading.Timer(15.0, self.show_init_status, args=["Checking network..."])
            self.network_check_timer.daemon = True
            self.network_check_timer.start()
            
            # Queue initial status update
            self.ui_update_queue.put({
                'type': 'status',
                'text': f"Preparing to download from {url}...",
                'color': "black"
            })
            
            # Limit update frequency
            self.update_interval = 0.5  # seconds between UI updates
            self.last_update_time = time.time()
            
            # Save current download info in case we need to resume later
            self.save_download_state(url, format_string, output_path)
            
            # Throttled progress hook with queue-based updates
            def throttled_progress_hook(d):
                # Check for stop event first
                if hasattr(self, 'stop_event') and self.stop_event.is_set():
                    raise Exception("Download cancelled by user")
                    
                # Mark download as started to cancel initialization timers
                if not self.download_started:
                    self.download_started = True
                    self.cancel_init_timers()
                    
                current_time = time.time()
                if current_time - getattr(self, 'last_update_time', 0) > self.update_interval:
                    self.last_update_time = current_time
                    
                    # Queue the update instead of directly modifying UI
                    self.ui_update_queue.put({
                        'type': 'download_progress',
                        'data': copy.deepcopy(d)  # Create a copy to avoid reference issues
                    })
            
            # Enhanced processing hook with throttling
            def throttled_processing_hook(d):
                # Mark download as started to cancel initialization timers
                if not self.download_started:
                    self.download_started = True
                    self.cancel_init_timers()
                    
                current_time = time.time()
                if current_time - getattr(self, 'last_update_time', 0) > self.update_interval:
                    self.last_update_time = current_time
                    
                    # Queue the update
                    self.ui_update_queue.put({
                        'type': 'processing_progress',
                        'data': copy.deepcopy(d)
                    })
            
            # Base options for yt-dlp - optimized configuration
            ydl_opts = {
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'verbose': True,
                'progress_hooks': [throttled_progress_hook],
                'postprocessor_hooks': [throttled_processing_hook],
                'noprogress': False,
                'quiet': False,
                'buffersize': 4096,  # Larger buffer for better performance
            }
            
            # Handle resume option
            if resume:
                ydl_opts['continue'] = True
            
            print(f"Download thread: Resume mode: {resume}")
            
            # Set format-specific options with cleaner approach
            if 'audio' in format_string:
                # Extract the format specification
                if format_string.startswith('-f '):
                    format_spec = format_string[3:].split(' --')[0].strip()
                else:
                    format_spec = format_string.split(' --')[0].strip()
                
                ydl_opts['format'] = format_spec
                
                # Configure audio extraction based on format
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
                # For video formats
                if format_string.startswith('-f '):
                    ydl_opts['format'] = format_string[3:].strip()
                else:
                    ydl_opts['format'] = format_string.strip()
            
            print("Download thread: Final yt-dlp options:")
            print(ydl_opts)
            
            # Get video information with better error handling
            video_title = "Unknown Title"
            try:
                # Create a separate YoutubeDL instance just for info extraction
                with contextlib.closing(yt_dlp.YoutubeDL({'quiet': True, 'socket_timeout': 30})) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                    video_title = info_dict.get('title', 'Unknown Title')
                    
                    # Mark download as started to cancel initialization timers
                    self.download_started = True
                    self.cancel_init_timers()
                    
                    # Queue title update
                    self.ui_update_queue.put({
                        'type': 'status',
                        'text': f"Starting download: {video_title}",
                        'color': "black"
                    })
            except Exception as info_error:
                print(f"Info extraction error: {str(info_error)}")
                
                # Queue generic status update
                self.ui_update_queue.put({
                    'type': 'status',
                    'text': f"Starting download from {url}",
                    'color': "black"
                })
            
            # Check for cancellation
            if hasattr(self, 'cancel_requested') and self.cancel_requested:
                self.cancel_init_timers()
                self.ui_update_queue.put({
                    'type': 'cancelled',
                    'text': "Download cancelled by user."
                })
                return
            
            # For audio downloads, update UI about processing stage
            if 'audio' in format_string:
                self.ui_update_queue.put({
                    'type': 'status',
                    'text': f"Downloading '{video_title}' - Processing will follow",
                    'color': "black"
                })
            
            # Execute the download with a separate yt-dlp instance
            try:
                # Check cancellation before starting
                if hasattr(self, 'cancel_requested') and self.cancel_requested:
                    self.cancel_init_timers()
                    raise Exception("Download cancelled by user")
                
                # Create a cancellable context for yt-dlp
                with contextlib.closing(yt_dlp.YoutubeDL(ydl_opts)) as ydl:
                    # Add cancellation check
                    original_report_error = ydl.report_error
                    
                    def cancellable_report_error(self, *args, **kwargs):
                        # Check for cancellation during long operations
                        if hasattr(self.params['_downloader'], 'cancel_requested') and self.params['_downloader'].cancel_requested:
                            raise Exception("Download cancelled by user")
                        return original_report_error(self, *args, **kwargs)
                    
                    # Monkey patch the report_error method to enable cancellation
                    ydl.report_error = types.MethodType(cancellable_report_error, ydl)
                    ydl.params['_downloader'] = self
                    
                    # Execute download
                    download_result = ydl.download([url])
                
                # Handle the download result
                if download_result == 0:
                    # Success - queue completion notification
                    self.ui_update_queue.put({
                        'type': 'complete'
                    })
                    # Clear saved download state as it completed successfully
                    self.clear_download_state()
                else:
                    raise Exception(f"yt-dlp returned error code: {download_result}")
                    
            except Exception as download_error:
                # Handle download errors
                self.cancel_init_timers()
                if str(download_error) == "Download cancelled by user":
                    self.ui_update_queue.put({
                        'type': 'cancelled',
                        'text': "Download cancelled by user."
                    })
                else:
                    error_msg = f"Error: {str(download_error)}"
                    print(f"Download error: {str(download_error)}")
                    
                    self.ui_update_queue.put({
                        'type': 'error',
                        'text': error_msg
                    })
                    
        except Exception as e:
            # Handle thread-level exceptions
            self.cancel_init_timers()
            error_msg = f"Thread error: {str(e)}"
            print(error_msg)
            
            self.ui_update_queue.put({
                'type': 'error',
                'text': error_msg
            })

    #Display initialization status messages if download hasn't started yet
    def show_init_status(self, message):
        if not hasattr(self, 'download_started') or not self.download_started:
            self.ui_update_queue.put({
                'type': 'status',
                'text': message,
                'color': "blue"
            })

    #Cancel all initialization timers when no longer needed
    def cancel_init_timers(self):
        for timer_name in ['init_timer', 'almost_there_timer', 'network_check_timer']:
            if hasattr(self, timer_name):
                timer = getattr(self, timer_name)
                if timer and timer.is_alive():
                    timer.cancel()

    def start_ui_updater(self):
        if not hasattr(self, 'ui_updater_running'):
            self.ui_updater_running = True
            
            def process_ui_updates():
                try:
                    # Process all pending updates
                    while not self.ui_update_queue.empty():
                        update = self.ui_update_queue.get_nowait()
                        
                        # Handle different types of updates
                        if update['type'] == 'status':
                            self.status_label.config(text=update['text'], foreground=update.get('color', 'black'))
                        
                        elif update['type'] == 'download_progress':
                            self.update_download_progress(update['data'])
                        
                        elif update['type'] == 'processing_progress':
                            self.update_processing_progress(update['data'])
                        
                        elif update['type'] == 'complete':
                            self.on_download_complete()
                        
                        elif update['type'] == 'cancelled':
                            self.status_label.config(text=update['text'], foreground="red")
                            self.progress.config(value=0)
                            if hasattr(self, 'cancel_button'):
                                self.cancel_button.config(state=tk.DISABLED)
                            self.cancel_requested = False
                        
                        elif update['type'] == 'error':
                            self.status_label.config(text=update['text'], foreground="red")
                            self.activate_recovery_buttons()
                        
                        # Mark this update as processed
                        self.ui_update_queue.task_done()
                    
                    # Continue processing if updater is still running
                    if hasattr(self, 'ui_updater_running') and self.ui_updater_running:
                        self.parent.after(100, process_ui_updates)
                    
                except Exception as e:
                    print(f"UI update error: {str(e)}")
                    # Reschedule even after error
                    if hasattr(self, 'ui_updater_running') and self.ui_updater_running:
                        self.parent.after(100, process_ui_updates)
            
            # Start the update processor
            self.parent.after(0, process_ui_updates)

    def save_download_state(self, url, format_string, output_path):
        try:
            state_dir = self.download_state_path
            os.makedirs(state_dir, exist_ok=True)
            url_hash = hashlib.md5(url.encode()).hexdigest()
            state_file = os.path.join(state_dir, f"{url_hash}.json")

            download_state = {                
                'title': getattr(self, 'current_title', None) or getattr(self, 'current_titled', None) or 'Unknown Title',
                'url': url,
                'format_string': format_string,
                'output_path': output_path,
                'timestamp': time.time(),
                'completed': False
            }

            with open(state_file, 'w') as f:
                json.dump(download_state, f)
            print(f"Download state saved to {state_file}")

        except Exception as e:
            print(f"Error saving download state: {str(e)}")

    def clear_download_state(self):
        try:
            if hasattr(self, 'current_url'):
                url_hash = hashlib.md5(self.current_url.encode()).hexdigest()
                state_dir = self.download_state_path
                state_file = os.path.join(state_dir, f"{url_hash}.json")

                if os.path.exists(state_file):
                    os.remove(state_file)
                    print(f"Removed completed download state: {state_file}")

        except Exception as e:
            print(f"Error clearing download state: {str(e)}")


    def get_incomplete_downloads(self):
        try:
            state_dir = self.download_state_path
            if not os.path.exists(state_dir):
                return []

            incomplete_downloads = []
            state_files = [f for f in os.listdir(state_dir) if f.endswith('.json')]

            for state_file in state_files:
                try:
                    with open(os.path.join(state_dir, state_file), 'r') as f:
                        download_state = json.load(f)
                        if not download_state.get('completed', False):
                            if 'timestamp' in download_state:
                                download_state['date'] = time.strftime(
                                    '%Y-%m-%d %H:%M:%S',
                                    time.localtime(download_state['timestamp'])
                                )
                            incomplete_downloads.append(download_state)
                except Exception as e:
                    print(f"Error reading state file {state_file}: {str(e)}")

            return incomplete_downloads

        except Exception as e:
            print(f"Error getting incomplete downloads: {str(e)}")
            return []


    def cleanup(self):
        # Stop the UI updater
        if hasattr(self, 'ui_updater_running'):
            self.ui_updater_running = False
        
        # Clear any queues
        if hasattr(self, 'ui_update_queue'):
            while not self.ui_update_queue.empty():
                try:
                    self.ui_update_queue.get_nowait()
                    self.ui_update_queue.task_done()
                except:
                    pass

    def update_processing_progress(self, d):
        if d['status'] == 'started':
            action = d.get('postprocessor', 'Processing')
            self.parent.after(0, lambda: self.status_label.config(
                text=f"{action} in progress...", foreground="black"))
            # Set progress to indeterminate or at 95% to indicate processing
            self.parent.after(0, lambda: self.progress.config(value=95))
        elif d['status'] == 'finished':
            self.parent.after(0, lambda: self.status_label.config(
                text="Finalizing download...", foreground="black"))
            self.parent.after(0, lambda: self.progress.config(value=98))
            
            # Set a 5-second timeout to force completion if it gets stuck
            self.finalize_timer = self.parent.after(5000, self.on_download_complete)

    def init_recovery_buttons(self, button_frame):
        self.resume_button = ttk.Button(button_frame, text="▶️ Resume", command=self.resume_download, state=tk.DISABLED)
        self.resume_button.pack(side=tk.LEFT, padx=1)
        
        self.restart_button = ttk.Button(button_frame, text="🔄 Restart", command=self.restart_download, state=tk.DISABLED)
        self.restart_button.pack(side=tk.LEFT, padx=1)

    def activate_recovery_buttons(self):
        if hasattr(self, 'resume_button') and hasattr(self, 'restart_button'):
            self.resume_button.config(state=tk.NORMAL)
            self.restart_button.config(state=tk.NORMAL)
            # Disable cancel button since download is already interrupted
            if hasattr(self, 'cancel_button'):
                self.cancel_button.config(state=tk.DISABLED)

    def deactivate_recovery_buttons(self):
        if hasattr(self, 'resume_button') and hasattr(self, 'restart_button'):
            self.resume_button.config(state=tk.DISABLED)
            self.restart_button.config(state=tk.DISABLED)

    def resume_download(self):
        if hasattr(self, 'current_url') and hasattr(self, 'current_format_string') and hasattr(self, 'current_output_path'):
            self.status_label.config(text="Resuming download...", foreground="blue")
            self.progress['value'] = 0
            
            # Disable resume/restart buttons and enable cancel button
            self.deactivate_recovery_buttons()
            if hasattr(self, 'cancel_button'):
                self.cancel_button.config(state=tk.NORMAL)
            
            # Reset cancel flags
            self.cancel_requested = False
            self.download_cancelled = False
            
            # Start download thread with resume=True
            download_thread = threading.Thread(
                target=self.download_thread,
                args=(self.current_url, self.current_format_string, self.current_output_path, True)
            )
            download_thread.daemon = True
            download_thread.start()

    def restart_download(self):
        if hasattr(self, 'current_url') and hasattr(self, 'current_format_string') and hasattr(self, 'current_output_path'):
            self.status_label.config(text="Restarting download...", foreground="blue")
            self.progress['value'] = 0
            
            # Disable resume/restart buttons and enable cancel button
            self.deactivate_recovery_buttons()
            if hasattr(self, 'cancel_button'):
                self.cancel_button.config(state=tk.NORMAL)
            
            # Reset cancel flags
            self.cancel_requested = False
            self.download_cancelled = False
            
            # Start download thread with resume=False (restart from beginning)
            download_thread = threading.Thread(
                target=self.download_thread,
                args=(self.current_url, self.current_format_string, self.current_output_path, False)
            )
            download_thread.daemon = True
            download_thread.start()

    def cancel_download(self):
        print("Cancel download requested")       
        # Determine what phase we're in for a more specific message
        if hasattr(self, 'download_tracker') and self.download_tracker.get('current_step', 0) > 1:
            # We're either downloading audio or merging
            if self.download_tracker['current_step'] == 2:
                message = "You're currently downloading the audio component which will be automatically merged with the video. Cancelling now will lose both downloads.\n\nAre you sure you want to cancel?"
            else:  # Step 3 - merging
                message = "The download is complete and files are being merged. Cancelling now might result in corrupted files.\n\nAre you sure you want to cancel?"
        else:
            # We're in the first step or single download
            message = "Download is in progress. Are you sure you want to cancel?"        
        confirm = messagebox.askyesno("Confirm Cancellation", message)
        if not confirm:
            return
        
        # Proceed with cancellation
        self.cancel_requested = True
        
        # Make sure stop_event exists before setting it
        if not hasattr(self, 'stop_event'):
            self.stop_event = threading.Event()
        self.stop_event.set()
        
        self.download_cancelled = True
        
        # Check if status_label exists before updating it
        if hasattr(self, 'status_label'):
            self.status_label.config(text="Cancelling download...", foreground="red")
            
        if hasattr(self, 'cancel_button'):
            self.cancel_button.config(state=tk.DISABLED)  # escaping multiple cancelation
            
        try:
            # Get current download information for file cleanup
            current_url = getattr(self, 'current_url', None)
            current_title = getattr(self, 'current_title', 'Unknown Title')
            current_output_path = getattr(self, 'current_output_path', None)
            
            # Clean up partial files if we have URL information
            if current_url and current_output_path:
                try:
                    download_dir = os.path.join(
                        os.path.expanduser("~"),
                        "Downloads",
                        "yt-dlite"
                    )
                    
                    # Use the same file deletion logic as in remove_selected_download written previoulsy
                    if os.path.exists(download_dir):
                        # Extract base filename if available
                        base_name = os.path.basename(current_output_path)
                        base_name_no_ext = os.path.splitext(base_name)[0] if base_name else None
                        
                        print(f"Looking for files related to cancelled download: {current_title}")
                        print(f"Base output filename: {base_name_no_ext}")
                        
                        files_deleted = 0
                        
                        for file in os.listdir(download_dir):
                            if file.endswith(".part") or file.endswith(".ytdl"):
                                should_delete = False
                                
                                # Check if the file matches the base name
                                if base_name_no_ext and base_name_no_ext in file:
                                    should_delete = True
                                
                                # Use similarity check as fallback
                                if not should_delete:
                                    clean_filename = re.sub(r'\.(part|ytdl|mp4|webm|mkv).*$', '', file)
                                    
                                    # Normalize both strings for comparison
                                    norm_title = re.sub(r'[^\w\s]', '', current_title).lower()
                                    norm_filename = re.sub(r'[^\w\s]', '', clean_filename).lower()
                                    
                                    # Use the similarity calculation
                                    lcs_length = self.longest_common_substring_length(norm_title, norm_filename)
                                    similarity = lcs_length / min(len(norm_title), len(norm_filename)) if min(len(norm_title), len(norm_filename)) > 0 else 0
                                    
                                    print(f"File: {file}, Similarity: {similarity:.2f}")
                                    
                                    # If similarity is above threshold, mark for deletion
                                    if similarity >= 0.7:  # 70% similarity threshold
                                        should_delete = True
                                
                                if should_delete:
                                    file_path = os.path.join(download_dir, file)
                                    retries = 3
                                    delay = 1
                                    for attempt in range(retries):
                                        try:
                                            os.remove(file_path)
                                            files_deleted += 1
                                            print(f"Deleted canceled file: {file_path}")
                                            break
                                        except PermissionError as e:
                                            if attempt < retries - 1:
                                                print(f"File in use. Retrying ({attempt + 1}/{retries})...")
                                                time.sleep(delay)
                                            else:
                                                print(f"Error deleting file {file_path}: {e}")
                                                break
                                        except Exception as e:
                                            print(f"Unexpected error deleting file {file_path}: {str(e)}")
                                            break
                        
                        print(f"Total files deleted during cancellation: {files_deleted}")
                        
                        # Delete state file if it exists
                        if current_url:
                            url_hash = hashlib.md5(current_url.encode()).hexdigest()
                            state_file = os.path.join(
                                self.download_state_path,
                                f"{url_hash}.json"
                            )
                            
                            if os.path.exists(state_file):
                                try:
                                    os.remove(state_file)
                                    print(f"Deleted state file: {state_file}")
                                except Exception as e:
                                    print(f"Error deleting state file: {str(e)}")
                
                except Exception as e:
                    print(f"Error cleaning up partial files: {str(e)}")
            
            # Clear the download state
            if hasattr(self, 'clear_download_state'):
                self.clear_download_state()
            
            # Update UI with safety checks
            if hasattr(self, 'progress_bar'):
                self.progress_bar.config(value=0)
                
            if hasattr(self, 'status_label'):
                self.status_label.config(text="Download cancelled", foreground="red")
            
            # Re-enable the download button if needed
            if hasattr(self, 'download_button'):
                self.download_button.config(state=tk.NORMAL)
            
            print("Download cancelled successfully")
        
        except Exception as e:
            print(f"Unexpected error during cancellation: {str(e)}")
            if hasattr(self, 'status_label'):
                self.status_label.config(text=f"Error during cancellation: {str(e)}", foreground="red")

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
