import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import subprocess
import signal
import shlex
import re
import yt_dlp
import queue
import time
import platform
import sys
from io import StringIO

class RedirectText:
    def __init__(self, text_widget, queue):
        self.queue = queue
        self.text_widget = text_widget
        try:
            self.original_stdout = sys.stdout
            self.original_stderr = sys.stderr
        except AttributeError:
            self.original_stdout = None
            self.original_stderr = None
        self.process = None
        self.startupinfo = None
        # Configure to hide window (Windows-specific)
        if os.name == 'nt':
            import subprocess
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.startupinfo.wShowWindow = 0  # SW_HIDE

    def write(self, string):
        if self.original_stdout is not None:
            try:
                self.original_stdout.write(string)
            except (AttributeError, IOError):
                pass
        self.queue.put(string)
        
    def flush(self):
        # Only flush original stdout if it exists and has a flush method
        if self.original_stdout is not None:
            try:
                self.original_stdout.flush()
            except (AttributeError, IOError):
                pass

    #Execute command in hidden window and redirect output to queue
    def execute_command(self, command):
        def run_process():
            try:
                self.process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    universal_newlines=True,
                    startupinfo=self.startupinfo
                )
                
                # Read and redirect output
                for line in self.process.stdout:
                    self.write(line)
                
                for line in self.process.stderr:
                    self.write(f"ERROR: {line}")
                
                # Wait for process to complete
                return_code = self.process.wait()
                self.write(f"\nProcess completed with return code: {return_code}\n")
                
            except Exception as e:
                self.write(f"Error executing command: {str(e)}\n")
        
        # Run in thread to not block main application
        threading.Thread(target=run_process, daemon=True).start()
        
    def terminate_process(self):
        if self.process is not None:
            try:
                self.process.terminate()
                self.write("\nProcess terminated.\n")
            except Exception as e:
                self.write(f"Error terminating process: {str(e)}\n")

class ExpertGui:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title("YT-DLP GUI")
        self.parent.geometry("750x540")
        
        # Queue for terminal output
        self.terminal_queue = queue.Queue()
        
        # Download state variables
        self.download_in_progress = False
        self.conversion_in_progress = False
        self.current_process = None
        
        # Thread-safe lock
        self.process_lock = threading.Lock()
        
        # Flag for cancellation
        self.cancellation_requested = False
        
        # Initialize download thread as None
        self.download_thread = None
        
        # Setup protocol handler for window close
        self.parent.protocol("WM_DELETE_WINDOW", self.on_close)
####non holy#####################################
        
        # Set default download folder
        self.download_folder = os.path.join(os.path.expanduser("~"), "Downloads", "yt-dlite")
        os.makedirs(self.download_folder, exist_ok=True)
        
        # Create main frame
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Create downloader section
        self.create_downloader_section(main_frame)
        
        # Create separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=5)
        
        # Create converter section
        self.create_converter_section(main_frame)
        
        # Create separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=5)
        
        
        # Add terminal output section
        self.create_terminal_section(main_frame)
        
        # Set up output redirection
        self.setup_stdout_redirection()
        
        # Start terminal update loop
        self.update_terminal()

        # Create save location and progress section
        self.create_save_progress_section(main_frame)
        
        # Download and conversion flags
        self.download_in_progress = False
        self.conversion_in_progress = False
        
    def create_downloader_section(self, parent):
        ttk.Label(parent, text="yt-dlp", font=('', 12, 'bold')).pack(anchor='w')
        
        # Command entry frame
        cmd_frame = ttk.Frame(parent)
        cmd_frame.pack(fill='x', pady=5)
        
        self.cmd_entry = ttk.Entry(cmd_frame)
        self.cmd_entry.pack(side='left', fill='x', expand=True)
        
        # Set placeholder text
        self.placeholder_text = "paste or write yt-dlp command here"
        self.cmd_entry.insert(0, self.placeholder_text)
        self.cmd_entry.config(foreground='gray')
        
        # Bind focus events to handle placeholder behavior
        self.cmd_entry.bind("<FocusIn>", self.on_entry_focus_in)
        self.cmd_entry.bind("<FocusOut>", self.on_entry_focus_out)
        
        # ADD PASTE BUTTON HERE
        paste_btn = ttk.Button(cmd_frame, text="Paste command", command=self.paste_clipboard)
        paste_btn.pack(side='left', padx=5)
        
        execute_btn = ttk.Button(cmd_frame, text="Execute", command=self.execute_command)
        execute_btn.pack(side='left', padx=5)

    def on_entry_focus_in(self, event):
        if self.cmd_entry.get() == self.placeholder_text:
            self.cmd_entry.delete(0, "end")
            self.cmd_entry.config(foreground='black')

    def on_entry_focus_out(self, event):
        if not self.cmd_entry.get():
            self.cmd_entry.insert(0, self.placeholder_text)
            self.cmd_entry.config(foreground='gray')
            
    def create_converter_section(self, parent):
        ttk.Label(parent, text="Converter", font=('', 12, 'bold')).pack(anchor='w')        
        # Converter frame - single line
        conv_frame = ttk.Frame(parent)
        conv_frame.pack(fill='x', pady=5)        
        # File input
        ttk.Label(conv_frame, text="Input File:").pack(side='left', padx=(0, 5))
        self.file_entry = ttk.Entry(conv_frame)
        self.file_entry.pack(side='left', fill='x', expand=True)        
        browse_btn = ttk.Button(conv_frame, text="Browse", command=self.browse_file)
        browse_btn.pack(side='left', padx=5)        
        # Format section - inline
        ttk.Label(conv_frame, text="Format:").pack(side='left', padx=(10, 5))        
        # Audio formats
        audio_formats = ["mp3", "m4a", "aac", "opus", "ogg", "flac", "wav"]
        # Video formats
        video_formats = ["mp4", "mkv", "mov", "webm", "avi", "gif"]
        # Combined list
        all_formats = video_formats + audio_formats
        
        self.output_format = tk.StringVar(value="mp4")
        self.format_combobox = ttk.Combobox(conv_frame, textvariable=self.output_format, 
                                    values=all_formats, state="readonly", width=10)
        self.format_combobox.pack(side='left', padx=5)
        
        # Quality presets - inline
        ttk.Label(conv_frame, text="Quality:").pack(side='left', padx=(10, 5))
        
        self.quality_preset = tk.StringVar(value="Medium")
        quality_options = ttk.Combobox(conv_frame, textvariable=self.quality_preset,
                                    values=["High", "Medium", "Low"], state="readonly", width=10)
        quality_options.pack(side='left', padx=5)
        
        # Convert button - inline
        convert_btn = ttk.Button(conv_frame, text="Convert", command=self.start_conversion)
        convert_btn.pack(side='left', padx=(15, 5))
                
    #browse for input files
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select media file",
            filetypes=[
                ("Media files", "*.mp4 *.avi *.mkv *.mov *.webm *.mp3 *.wav *.flac *.m4a *.ogg *.opus"),
                ("Video files", "*.mp4 *.avi *.mkv *.mov *.webm"),
                ("Audio files", "*.mp3 *.wav *.flac *.m4a *.ogg *.opus"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)
            self.update_format_options()

    #Update format options based on the input file type
    def update_format_options(self, event=None):
        input_file = self.file_entry.get()
        if not input_file or not os.path.exists(input_file):
            return
        
        try:
            # Detect file type
            probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', 
                    '-of', 'default=noprint_wrappers=1:nokey=1', input_file]
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            streams = result.stdout.strip().split('\n')
            
            has_video = 'video' in streams
            
            # Detect input file format
            format_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=format_name', 
                    '-of', 'default=noprint_wrappers=1:nokey=1', input_file]
            format_result = subprocess.run(format_cmd, capture_output=True, text=True)
            input_format = format_result.stdout.strip().lower()
            
            # Use the direct reference to the format dropdown that was saved during initialization
            format_dropdown = self.format_combobox  # Use the reference created in create_converter_section
            
            if not format_dropdown:
                print("Could not find format dropdown widget")
                return
                
            # Prepare format lists
            audio_formats = ["mp3", "m4a", "aac", "opus", "ogg", "flac", "wav"]
            video_formats = ["mp4", "mkv", "mov", "webm", "avi", "gif"]
            
            # Store current format selection
            current_format = self.output_format.get()
            
            # Filter formats to exclude the input format to prevent self-destruction
            if has_video:
                all_formats = [fmt for fmt in video_formats + audio_formats if fmt not in input_format]
            else:
                all_formats = [fmt for fmt in audio_formats if fmt not in input_format]
                
            # If we've filtered out all formats (rare edge case), add a safe default
            if not all_formats:
                if has_video:
                    all_formats = ["mkv"] if "mp4" in input_format else ["mp4"]
                else:
                    all_formats = ["m4a"] if "mp3" in input_format else ["mp3"]
            
            # Update dropdown values
            format_dropdown['values'] = all_formats
            
            # If the previously selected format is still valid, keep it
            if current_format in all_formats:
                self.output_format.set(current_format)
            else:
                # Otherwise set to a safe default
                self.output_format.set(all_formats[0])
        
        except Exception as e:
            print(f"Error detecting file type: {str(e)}")
            import traceback
            print(traceback.format_exc())

    def create_terminal_section(self, parent):
        terminal_frame = ttk.LabelFrame(parent, text="Terminal Output")
        terminal_frame.pack(fill='both', expand=True, pady=5) #Terminal frame
        
        # Add toggle button for terminal visibility
        toggle_frame = ttk.Frame(terminal_frame)
        toggle_frame.pack(fill='x')
        
        # Change the default value to False here
        self.show_terminal = tk.BooleanVar(value=False)
        toggle_btn = ttk.Checkbutton(
            toggle_frame, 
            text="Show Terminal Output", 
            variable=self.show_terminal,
            command=self.toggle_terminal_visibility
        )
        toggle_btn.pack(side='left')
        
        clear_btn = ttk.Button(toggle_frame, text="Clear", command=self.clear_terminal)
        clear_btn.pack(side='right')
        
        # Terminal text area with scrollbars
        self.terminal_text = scrolledtext.ScrolledText(terminal_frame, height=10, wrap=tk.WORD)
        self.terminal_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.terminal_text.config(state=tk.DISABLED)
        self.toggle_terminal_visibility()
    
    #saving location frame
    def create_save_progress_section(self, parent):
        save_frame = ttk.Frame(parent)
        save_frame.pack(fill='x', pady=5)
        
        ttk.Label(save_frame, text="Save output:").pack(side='left')
        
        self.save_location = tk.StringVar(value=self.download_folder)
        save_entry = ttk.Entry(save_frame, textvariable=self.save_location)
        save_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        browse_save_btn = ttk.Button(save_frame, text="Browse", command=self.browse_save_location)
        browse_save_btn.pack(side='left')
                
        # Progress bar
        self.progress_bar = ttk.Progressbar(parent, mode='determinate')
        self.progress_bar.pack(fill='x', pady=5)
        self.status_label = ttk.Label(parent, text="Ready")
        self.status_label.pack(anchor='center')
        
        # Cancel button
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill='x', pady=5)
        
        self.cancel_btn = ttk.Button(bottom_frame, text="Cancel", command=self.cancel_operation, state='disabled')
        self.cancel_btn.pack(side='left')
        
        # Current process
        self.current_process = None
    
    def setup_stdout_redirection(self):
        # Redirect stdout and stderr to our custom handler
        self.redirect = RedirectText(self.terminal_text, self.terminal_queue)
        sys.stdout = self.redirect
        sys.stderr = self.redirect

    def paste_clipboard(self):
        clipboard_text = self.parent.clipboard_get()
        if self.cmd_entry.get() == self.placeholder_text:
            self.cmd_entry.delete(0, "end")
            self.cmd_entry.config(foreground='black')
        self.cmd_entry.delete(0, "end")
        self.cmd_entry.insert(0, clipboard_text)
    # Process any pending output in the queue
    def update_terminal(self):
        try:
            while True:
                line = self.terminal_queue.get_nowait()
                self.terminal_text.config(state=tk.NORMAL)
                self.terminal_text.insert(tk.END, line)
                self.terminal_text.see(tk.END)
                self.terminal_text.config(state=tk.DISABLED)
                self.terminal_queue.task_done()
        except queue.Empty:
            pass
        # Schedule the next update
        self.parent.after(100, self.update_terminal)
    
    def toggle_terminal_visibility(self):
        if self.show_terminal.get():
            self.terminal_text.pack(fill='both', expand=True, padx=5, pady=5)
        else:
            self.terminal_text.pack_forget()
    
    def clear_terminal(self):
        self.terminal_text.config(state=tk.NORMAL)
        self.terminal_text.delete(1.0, tk.END)
        self.terminal_text.config(state=tk.DISABLED)
        
    def browse_save_location(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_location.set(folder)
            self.download_folder = folder
    
    def execute_command(self):
        command = self.cmd_entry.get()
        # Don't execute if it's just the placeholder
        if command == self.placeholder_text:
            return

        if self.download_in_progress:
            messagebox.showinfo("Info", "A download is already in progress")
            return
            
        command = self.cmd_entry.get().strip()
        if not command:
            messagebox.showerror("Error", "Please enter a command")
            return
        
        # Remove 'yt-dlp' prefix if present
        if command.startswith('yt-dlp '):
            command = command[7:].strip()
        
        # Prepare full command
        full_command = ["yt-dlp"]
        
        # Properly handle quoted arguments
        try:
            args = shlex.split(command)
            full_command.extend(args)
        except Exception:
            # Fall back to simple splitting if shlex fails, just for flexibility
            full_command.extend(command.split())
        
        # Add output template if not specified
        has_output = False
        for i, arg in enumerate(full_command):
            if arg in ['-o', '--output'] and i+1 < len(full_command):
                has_output = True
                break
        
        if not has_output:
            full_command.extend(["-o", os.path.join(self.save_location.get(), "%(title)s.%(ext)s")])
        
        # Reset and update UI
        self.progress_bar['value'] = 0
        self.status_label.config(text="Starting download...")
        self.cancel_btn.config(state='normal')
        
        # Reset cancellation flag and set download flag
        self.cancellation_requested = False
        self.download_in_progress = True
        
        print(f"Executing: {' '.join(full_command)}") # Print the command being executed
        
        # Start thread
        self.download_thread = threading.Thread(target=self.run_command, args=(full_command,))
        self.download_thread.daemon = True
        self.download_thread.start()

    def run_command(self, command):
        try:
            # Extract URL from command
            url = None
            for arg in command:
                if re.match(r'https?://', arg):
                    url = arg
                    break
            
            if not url:
                self.parent.after(0, lambda: self.status_label.config(text="No URL found in command"))
                self.parent.after(0, lambda: self.cancel_btn.config(state='disabled'))
                self.parent.after(0, lambda: messagebox.showerror("Error", "No URL found in the command. Please enter full command."))
                self.download_in_progress = False
                return
            
            # Custom YoutubeDL logger implementation that passes everything to terminal
            class PassthroughLogger:
                def __init__(self, parent_instance):
                    self.parent = parent_instance
                
                def debug(self, msg):
                    # Just check for cancellation but pass all messages through
                    if self.parent.cancellation_requested:
                        raise Exception("Download cancelled by user")
                    print(f"[debug] {msg}")
                
                def info(self, msg):
                    if self.parent.cancellation_requested:
                        raise Exception("Download cancelled by user")
                    print(f"[info] {msg}")
                
                def warning(self, msg):
                    print(f"[warning] {msg}")
                
                def error(self, msg):
                    print(f"[error] {msg}")
            
            # Custom progress hook that checks for cancellation
            def progress_hook(d):
                # Check cancellation flag immediately
                if self.cancellation_requested:
                    raise Exception("Download cancelled by user")
                
                # Regular progress handling
                if d['status'] == 'downloading':
                    if 'total_bytes' in d and d['total_bytes'] > 0:
                        percent = d['downloaded_bytes'] / d['total_bytes'] * 100
                        self.parent.after(0, lambda: self.progress_bar.config(value=percent))
                    elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                        percent = d['downloaded_bytes'] / d['total_bytes_estimate'] * 100
                        self.parent.after(0, lambda: self.progress_bar.config(value=percent))
                    
                    # Update status
                    if '_percent_str' in d and '_speed_str' in d and '_eta_str' in d:
                        status = f"Downloading: {d['_percent_str']} at {d['_speed_str']} ETA: {d['_eta_str']}"
                        self.parent.after(0, lambda: self.status_label.config(text=status))
                
                elif d['status'] == 'finished':
                    # Check cancellation again before processing
                    if self.cancellation_requested:
                        raise Exception("Download cancelled by user")
                        
                    self.parent.after(0, lambda: self.progress_bar.config(value=100))
                    self.parent.after(0, lambda: self.status_label.config(text="Download finished, processing..."))
            
            # Create yt-dlp options with passthrough logger and progress hook
            # Set verbosity to True to ensure all output is passed to terminal, for debbuging
            ydl_opts = {
                'progress_hooks': [progress_hook],
                'logger': PassthroughLogger(self),
                'quiet': False,
                'no_warnings': False,
                'verbose': False,
            }
            
            # Add custom options from command to ydl_opts
            for i, arg in enumerate(command[1:]):  # Skip 'yt-dlp'
                if arg.startswith('-') and not arg.startswith('http'):
                    if arg in ['-o', '--output'] and i+2 < len(command):
                        ydl_opts['outtmpl'] = command[i+2]
            
            try:
                # Add a quick check if already cancelled before starting
                if self.cancellation_requested:
                    raise Exception("Download cancelled by user")
                    
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Store ydl reference for potential cancellation
                    with self.process_lock:
                        self.current_process = {'ydl': ydl}
                    
                    # Check if already cancelled
                    if not self.cancellation_requested:
                        try:
                            ydl.download([url])
                            
                            # Only update UI if not cancelled
                            if not self.cancellation_requested:
                                self.parent.after(0, lambda: self.status_label.config(text="Download completed!"))
                        except Exception as e:
                            if "Download cancelled by user" in str(e):
                                self.parent.after(0, lambda: self.status_label.config(text="Download cancelled"))
                            else:
                                self.parent.after(0, lambda: self.status_label.config(text=f"Error: {str(e)}"))
                                print(f"Download error: {str(e)}")
                
            except Exception as e:
                # Handle exceptions outside the YoutubeDL with
                if "Download cancelled by user" in str(e):
                    self.parent.after(0, lambda: self.status_label.config(text="Download cancelled"))
                else:
                    self.parent.after(0, lambda: self.status_label.config(text=f"Error: {str(e)}"))
                    print(f"Download error: {str(e)}")
            
            finally:
                # Always clean up
                with self.process_lock:
                    self.current_process = None
                self.download_in_progress = False
                self.cancellation_requested = False
                self.parent.after(0, lambda: self.cancel_btn.config(state='disabled'))
                
        except Exception as e:
            self.parent.after(0, lambda: self.status_label.config(text=f"Error: {str(e)}"))
            self.parent.after(0, lambda: self.cancel_btn.config(state='disabled'))
            self.download_in_progress = False
            self.cancellation_requested = False
            print(f"Command execution error: {str(e)}")

    #Cancel the current operation using a combination of flag-based approach and thread termination.
    def cancel_operation(self):
        try:
            # Set cancellation flag first
            self.cancellation_requested = True
            self.status_label.config(text="Cancelling operation...")
            
            # Then try to abort specific processes
            with self.process_lock:
                if self.current_process:
                    if isinstance(self.current_process, dict) and self.current_process.get('ydl'):
                        # It's a download operation
                        ydl = self.current_process.get('ydl')
                        if ydl:
                            # Attempt to abort the download
                            try:
                                # Set params directly
                                ydl.params['abort'] = True
                            except Exception as e:
                                print(f"Error while aborting download: {str(e)}")
                        print("Download cancelled by user")
                    elif hasattr(self.current_process, 'pid'):
                        # It's a subprocess operation
                        try:
                            if os.name == 'nt':  # Windows
                                self.current_process.terminate()
                                time.sleep(0.5)
                                if self.current_process.poll() is None:
                                    self.current_process.kill()
                            else:  # Unix/Linux
                                os.kill(self.current_process.pid, signal.SIGTERM)
                                time.sleep(0.5)
                                if self.current_process.poll() is None:
                                    os.kill(self.current_process.pid, signal.SIGKILL)
                            print("Conversion cancelled by user")
                        except Exception as e:
                            print(f"Error cancelling process: {str(e)}")
            
            # Force terminate the download thread if it's running
            if self.download_in_progress and hasattr(self, 'download_thread') and self.download_thread.is_alive():
                # Instead of just waiting, we'll use a timeout approach
                self.download_thread.join(2.0)  # Wait up to 2 seconds for clean termination
                
                if self.download_thread.is_alive():
                    # Thread is still running - we need to clean up resources
                    print("Download thread did not terminate gracefully, forcing cleanup")
                    # We can't actually force-kill a Python thread, but we can clean up resources
                    self.download_in_progress = False
                    
            # Update UI
            self.status_label.config(text="Operation cancelled")
            self.progress_bar.stop()
            self.progress_bar.config(value=0, mode='determinate')
            self.cancel_btn.config(state='disabled')
            
        except Exception as e:
            # Catch any unexpected errors
            print(f"Unexpected error during cancellation: {str(e)}")
            self.status_label.config(text="Error during cancellation")

    #Handle application close event by terminating any running processes.
    def on_close(self):
        if self.download_in_progress:
            self.cancel_operation()
            # Give some time for cleanup
            self.parent.after(100, self._finish_close)
        else:
            self._finish_close()

    #Finalize the closing of the application & Perform any final cleanup if needed
    def _finish_close(self):
        self.parent.destroy()
        
    def start_conversion(self):
        if self.conversion_in_progress:
            messagebox.showinfo("Info", "A conversion is already in progress")
            return
            
        input_file = self.file_entry.get()
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("Error", "Please select a valid input file")
            return
        
        output_format = self.output_format.get()
        output_dir = self.save_location.get()
        quality_preset = self.quality_preset.get()
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_filename = os.path.basename(os.path.splitext(input_file)[0]) + f".{output_format}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Reset UI
        self.progress_bar['value'] = 0
        self.progress_bar.config(mode='determinate')
        self.progress_bar.start()
        self.status_label.config(text="Converting...")
        self.cancel_btn.config(state='normal')
        
        # Set flag
        self.conversion_in_progress = True
        
        # Print conversion info to terminal, for debbuging
        print(f"Converting: {input_file}")
        print(f"Output format: {output_format}")
        print(f"Quality preset: {quality_preset}")
        print(f"Output path: {output_path}")
        
        # Start conversion thread
        self.convert_thread = threading.Thread(
            target=self.convert_file, 
            args=(input_file, output_path, output_format, quality_preset)
        )
        self.convert_thread.daemon = True
        self.convert_thread.start()

    def convert_file(self, input_file, output_file, output_format, quality_preset):
        try:
            self.current_output_file = output_file #storing output path as a variable so that it is widely accessible
            
            # Determine input type (audio or video)
            probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', 
                        '-of', 'default=noprint_wrappers=1:nokey=1', input_file]
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            streams = result.stdout.strip().split('\n')
            
            has_video = 'video' in streams
            has_audio = 'audio' in streams
            
            # Basic command structure
            cmd = ['ffmpeg', '-i', input_file, '-y']
            
            # Determine if we're extracting audio from video
            is_audio_output = output_format in ['mp3', 'aac', 'm4a', 'opus', 'ogg', 'flac', 'wav']
            
            # Skip video processing for audio-to-audio conversion
            if is_audio_output and not has_video:
                cmd.append('-vn')  # No video
            
            # For video-to-audio extraction
            if is_audio_output and has_video:
                cmd.append('-vn')  # No video for audio output
            
            # Handle format-specific options based on quality preset
            if is_audio_output:
                # Audio settings based on quality presets
                if output_format == 'mp3':
                    if quality_preset == 'High':
                        cmd.extend(['-c:a', 'libmp3lame', '-ar', '48000', '-ac', '2', '-b:a', '320k'])
                    elif quality_preset == 'Medium':
                        cmd.extend(['-c:a', 'libmp3lame', '-ar', '44100', '-ac', '2', '-b:a', '192k'])
                    else:  # Low
                        cmd.extend(['-c:a', 'libmp3lame', '-ar', '44100', '-ac', '2', '-b:a', '128k'])

                        
                elif output_format == 'aac' or output_format == 'm4a':
                    if quality_preset == 'High':
                        cmd.extend(['-c:a', 'aac', '-ar', '48000', '-ac', '2', '-b:a', '256k'])
                    elif quality_preset == 'Medium':
                        cmd.extend(['-c:a', 'aac', '-ar', '44100', '-ac', '2', '-b:a', '192k'])
                    else:  # Low
                        cmd.extend(['-c:a', 'aac', '-ar', '44100', '-ac', '2', '-b:a', '128k'])
                        
                elif output_format == 'opus':
                    if quality_preset == 'High':
                        cmd.extend(['-c:a', 'libopus', '-ar', '48000', '-ac', '2', '-b:a', '192k'])
                    elif quality_preset == 'Medium':
                        cmd.extend(['-c:a', 'libopus', '-ar', '48000', '-ac', '2', '-b:a', '128k'])
                    else:  # Low
                        cmd.extend(['-c:a', 'libopus', '-ar', '48000', '-ac', '2', '-b:a', '96k'])
                        
                elif output_format == 'ogg':
                    if quality_preset == 'High':
                        cmd.extend(['-c:a', 'libvorbis', '-ar', '48000', '-ac', '2', '-b:a', '256k'])
                    elif quality_preset == 'Medium':
                        cmd.extend(['-c:a', 'libvorbis', '-ar', '44100', '-ac', '2', '-b:a', '192k'])
                    else:  # Low
                        cmd.extend(['-c:a', 'libvorbis', '-ar', '44100', '-ac', '2', '-b:a', '128k'])
                        
                elif output_format == 'flac':
                    if quality_preset == 'High':
                        cmd.extend(['-c:a', 'flac', '-ar', '96000', '-ac', '2', '-sample_fmt', 's32'])
                    elif quality_preset == 'Medium':
                        cmd.extend(['-c:a', 'flac', '-ar', '48000', '-ac', '2', '-sample_fmt', 's24'])
                    else:  # Low
                        cmd.extend(['-c:a', 'flac', '-ar', '44100', '-ac', '2', '-sample_fmt', 's16'])
                        
                elif output_format == 'wav':
                    if quality_preset == 'High':
                        cmd.extend(['-c:a', 'pcm_s24le', '-ar', '96000', '-ac', '2'])
                    elif quality_preset == 'Medium':
                        cmd.extend(['-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2'])
                    else:  # Low
                        cmd.extend(['-c:a', 'pcm_s16le', '-ar', '44100', '-ac', '2'])
            
            # Video output formats
            else:
                # Keep audio if available
                if has_audio:
                    if quality_preset == 'High':
                        cmd.extend(['-c:a', 'aac', '-b:a', '320k', '-ar', '48000'])
                    elif quality_preset == 'Medium':
                        cmd.extend(['-c:a', 'aac', '-b:a', '192k', '-ar', '44100'])
                    else:  # Low
                        cmd.extend(['-c:a', 'aac', '-b:a', '128k', '-ar', '44100'])
                
                # Video codec settings
                if output_format in ['mp4', 'mkv', 'mov']:
                    if quality_preset == 'High':
                        cmd.extend(['-c:v', 'libx264', '-crf', '18', '-preset', 'slow', '-profile:v', 'high'])
                    elif quality_preset == 'Medium':
                        cmd.extend(['-c:v', 'libx264', '-crf', '23', '-preset', 'medium', '-profile:v', 'main'])
                    else:  # Low
                        cmd.extend(['-c:v', 'libx264', '-crf', '28', '-preset', 'fast', '-profile:v', 'main'])
                        
                elif output_format == 'webm':
                    if quality_preset == 'High':
                        cmd.extend(['-c:v', 'libvpx-vp9', '-crf', '30', '-b:v', '0', '-deadline', 'good'])
                    elif quality_preset == 'Medium':
                        cmd.extend(['-c:v', 'libvpx-vp9', '-crf', '32', '-b:v', '0', '-deadline', 'good'])
                    else:  # Low
                        cmd.extend(['-c:v', 'libvpx-vp9', '-crf', '34', '-b:v', '0', '-deadline', 'realtime'])
                        
                elif output_format == 'avi':
                    if quality_preset == 'High':
                        cmd.extend(['-c:v', 'mpeg4', '-q:v', '3'])
                    elif quality_preset == 'Medium':
                        cmd.extend(['-c:v', 'mpeg4', '-q:v', '5'])
                    else:  # Low
                        cmd.extend(['-c:v', 'mpeg4', '-q:v', '7'])
                        
                elif output_format == 'gif':
                    # For GIFs, we'll use a palette for better quality
                    palette_path = os.path.join(os.path.dirname(output_file), "palette.png")
                    
                    # First pass to generate palette
                    palette_cmd = ['ffmpeg', '-i', input_file, '-vf', 
                                'fps=10,scale=320:-1:flags=lanczos,palettegen', 
                                '-y', palette_path]
                    subprocess.run(palette_cmd)
                    
                    # Update command to use palette
                    cmd = ['ffmpeg', '-i', input_file, '-i', palette_path, '-filter_complex',
                        'fps=10,scale=320:-1:flags=lanczos[x];[x][1:v]paletteuse',
                        '-y', output_file]
                    
                    # Skip the rest of the processing since we've set up a special command
                    print(f"Executing: {' '.join(cmd)}")
                    self.current_process = subprocess.Popen(
                        cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        bufsize=1
                    )
                    
                    # Continue with monitoring the process
                    return self.monitor_process()
            
#            # Add the output file
#            cmd.append(output_file)
            if output_format != 'gif':
                cmd.append(output_file)
            
            # Print command to terminal
            print(f"Executing: {' '.join(cmd)}")
            
            # Create and store the process with platform-specific settings for minimized window
            current_os = platform.system()
            
            if current_os == 'Windows':
                # For Windows, I use CREATE_NO_WINDOW flag
                import ctypes
                
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 6  # SW_MINIMIZE (6) for minimized window
                
                self.current_process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1,
                    startupinfo=startupinfo
                )
            
            elif current_os == 'Darwin':  # macOS
                # For macOS, use Terminal.app minimized
                terminal_cmd = ['osascript', '-e', 
                            'tell application "Terminal" to do script "' + 
                            ' '.join(cmd).replace('"', '\\"') + 
                            '" & exit']
                
                self.current_process = subprocess.Popen(
                    terminal_cmd,
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1
                )
            
            else:  # Linux and other Unix-like systems
                # For Linux, start in a minimized xterm or similar terminal
                if os.path.exists('/usr/bin/xterm'):
                    terminal_cmd = ['xterm', '-iconic', '-e', ' '.join(cmd)]
                    self.current_process = subprocess.Popen(
                        terminal_cmd,
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        bufsize=1
                    )
                else:
                    # Fallback if xterm is not available
                    self.current_process = subprocess.Popen(
                        cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        bufsize=1
                    )
            
            # Monitor the process output
            self.monitor_process()
            
        except Exception as e:
            self.parent.after(0, lambda: self.status_label.config(text=f"Error: {str(e)}"))
            print(f"Conversion error: {str(e)}")
            self.cleanup_conversion()

    #Monitor the FFmpeg process output and update progress
    def monitor_process(self):
        try:
            # Handle process output in real-time
            for line in self.current_process.stderr:
                print(line.strip())
                
                # Check for duration and progress info
                duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})', line)
                if duration_match:
                    hours, minutes, seconds = map(int, duration_match.groups())
                    self.total_duration = hours * 3600 + minutes * 60 + seconds
                    
                time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2})', line)
                if time_match and hasattr(self, 'total_duration') and self.total_duration > 0:
                    hours, minutes, seconds = map(int, time_match.groups())
                    current_time = hours * 3600 + minutes * 60 + seconds
                    progress = (current_time / self.total_duration) * 100
                    self.parent.after(0, lambda p=progress: self.update_conversion_progress(p))
            
            # Check if process was completed successfully
            returncode = self.current_process.wait()
            
            if returncode == 0:
                self.parent.after(0, lambda: self.status_label.config(text=f"Conversion completed successfully: {self.current_output_file}"))
                self.parent.after(0, lambda: self.progress_bar.config(value=100))
                print(f"Conversion completed successfully: {self.current_output_file}")
            else:
                self.parent.after(0, lambda: self.status_label.config(text="Conversion failed"))
                print("Conversion failed")
                
        except Exception as e:
            self.parent.after(0, lambda: self.status_label.config(text=f"Error: {str(e)}"))
            print(f"Monitoring error: {str(e)}")
        finally:
            self.cleanup_conversion()

    #Clean up after conversion is done
    def cleanup_conversion(self):
        self.current_process = None
        self.conversion_in_progress = False
        self.parent.after(0, lambda: self.progress_bar.stop())
        self.parent.after(0, lambda: self.progress_bar.config(mode='determinate', style='TProgressbar'))
        self.parent.after(0, lambda: self.cancel_btn.config(state='disabled'))

    #Cancel the ongoing conversion
    def cancel_conversion(self):
        if self.current_process and self.conversion_in_progress:
            print("Cancelling conversion...")            
            # Terminate the process
            if self.current_process:
                self.current_process.terminate()
                
            self.status_label.config(text="Conversion cancelled")
            self.cleanup_conversion()    
    def progress_hook(self, d):
        if not self.current_process or not self.current_process.get('active', False):
            return
            
        if d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', '0%')
                percent = percent.replace('%', '').strip()
                try:
                    percent_float = float(percent)
                except:
                    percent_float = 0
                
                speed = d.get('_speed_str', '?')
                eta = d.get('_eta_str', '?')
                filename = d.get('filename', '').split('/')[-1].split('\\')[-1]
                
                self.parent.after(0, lambda: self.progress_bar.config(value=percent_float))
                self.parent.after(0, lambda: self.status_label.config(
                    text=f"Downloading {filename}: {percent}% (Speed: {speed}, ETA: {eta})"
                ))
            except Exception as e:
                # Handle case where percent can't be converted
                self.parent.after(0, lambda: self.status_label.config(text="Downloading..."))
                print(f"Progress update error: {str(e)}")
        elif d['status'] == 'finished':
            self.parent.after(0, lambda: self.progress_bar.config(value=100))
            self.parent.after(0, lambda: self.status_label.config(text="Processing file..."))

    #Update the progress bar with the current conversion progress.
    def update_conversion_progress(self, progress):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.config(value=progress)
            # Optionally update status label with percentage
            self.status_label.config(text=f"Converting: {progress:.1f}%")
    
# Custom logger for yt-dlp to capture all output
class YTLogger:
    def debug(self, msg):
        if msg.strip():
            print(f"[debug] {msg}")
    
    def info(self, msg):
        if msg.strip():
            print(f"[info] {msg}")
    
    def warning(self, msg):
        if msg.strip():
            print(f"[warning] {msg}")
    
    def error(self, msg):
        if msg.strip():
            print(f"[error] {msg}")

if __name__ == "__main__":
    parent = tk.Tk()
    app = ExpertGui(parent)
    parent.mainloop()
