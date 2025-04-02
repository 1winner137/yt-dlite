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
import sys
from io import StringIO

class RedirectText:
    def __init__(self, text_widget, queue):
        self.queue = queue
        self.text_widget = text_widget
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def write(self, string):
        self.original_stdout.write(string)
        self.queue.put(string)
        
    def flush(self):
        self.original_stdout.flush()

class YTDLPSimpleGui:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title("YT-DLP GUI")
        self.parent.geometry("750x540")
        
        # Queue for terminal output
        self.terminal_queue = queue.Queue()
        
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
        # Label
        ttk.Label(parent, text="yt-dlp", font=('', 12, 'bold')).pack(anchor='w')
        
        # Command entry frame
        cmd_frame = ttk.Frame(parent)
        cmd_frame.pack(fill='x', pady=5)
        
        self.cmd_entry = ttk.Entry(cmd_frame)
        self.cmd_entry.pack(side='left', fill='x', expand=True)
        
        # ADD PASTE BUTTON HERE
        paste_btn = ttk.Button(cmd_frame, text="Paste command", command=self.paste_clipboard)
        paste_btn.pack(side='left', padx=5)
        
        execute_btn = ttk.Button(cmd_frame, text="Execute", command=self.execute_command)
        execute_btn.pack(side='left', padx=5)
            
    def create_converter_section(self, parent):
        # Label
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
        format_dropdown = ttk.Combobox(conv_frame, textvariable=self.output_format, 
                                    values=all_formats, state="readonly", width=10)
        format_dropdown.pack(side='left', padx=5)
        
        # Quality presets - inline
        ttk.Label(conv_frame, text="Quality:").pack(side='left', padx=(10, 5))
        
        self.quality_preset = tk.StringVar(value="Medium")
        quality_options = ttk.Combobox(conv_frame, textvariable=self.quality_preset,
                                    values=["High", "Medium", "Low"], state="readonly", width=10)
        quality_options.pack(side='left', padx=5)
        
        # Convert button - inline
        convert_btn = ttk.Button(conv_frame, text="Convert", command=self.start_conversion)
        convert_btn.pack(side='left', padx=(15, 5))
                

    def browse_file(self):
        """Browse for input file"""
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

    def update_format_options(self, event=None):
        """Update format options based on the input file type"""
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
            
            # Update format dropdown based on file type
            format_dropdown = self.output_format.master  # Get the combobox widget
            
            if has_video:
                # For video files, show all format options
                audio_formats = ["mp3", "m4a", "aac", "opus", "ogg", "flac", "wav"]
                video_formats = ["mp4", "mkv", "mov", "webm", "avi", "gif"]
                all_formats = video_formats + audio_formats
                format_dropdown['values'] = all_formats
            else:
                # For audio files, show only audio formats
                audio_formats = ["mp3", "m4a", "aac", "opus", "ogg", "flac", "wav"]
                format_dropdown['values'] = audio_formats
                
                # If current format is video, switch to default audio
                current_format = self.output_format.get()
                if current_format not in audio_formats:
                    self.output_format.set("mp3")
        
        except Exception as e:
            print(f"Error detecting file type: {str(e)}")
        
    def create_terminal_section(self, parent):
        # Terminal frame
        terminal_frame = ttk.LabelFrame(parent, text="Terminal Output")
        terminal_frame.pack(fill='both', expand=True, pady=5)
        
        # Add toggle button for terminal visibility
        toggle_frame = ttk.Frame(terminal_frame)
        toggle_frame.pack(fill='x')
        
        self.show_terminal = tk.BooleanVar(value=True)
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
    
    def create_save_progress_section(self, parent):
        # Save location frame
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

        # Status label (centered)
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
        self.cmd_entry.delete(0, tk.END)
        self.cmd_entry.insert(0, clipboard_text)

    def update_terminal(self):
        # Process any pending output in the queue
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
            # Fall back to simple splitting if shlex fails
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
        
        # Set flag
        self.download_in_progress = True
        
        # Print the command being executed
        print(f"Executing: {' '.join(full_command)}")
        
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
                self.download_in_progress = False
                return
            
            # Create yt-dlp options with progress hook
            ydl_opts = {
                'progress_hooks': [self.progress_hook],
                'logger': YTLogger(),
                'quiet': False,
                'no_warnings': False,
            }
            
            # Add custom options from command to ydl_opts
            for i, arg in enumerate(command[1:]):  # Skip 'yt-dlp'
                if arg.startswith('-') and not arg.startswith('http'):
                    if arg in ['-o', '--output'] and i+2 < len(command):
                        ydl_opts['outtmpl'] = command[i+2]
            
            # Set download process
            self.current_process = {'active': True, 'ydl': None}
            
            def download_with_ydl():
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        self.current_process['ydl'] = ydl
                        if self.current_process['active']:  # Check if cancelled
                            ydl.download([url])
                    
                    if self.current_process['active']:
                        self.parent.after(0, lambda: self.status_label.config(text="Download completed!"))
                except Exception as e:
                    if self.current_process['active']:
                        self.parent.after(0, lambda: self.status_label.config(text=f"Error: {str(e)}"))
                        print(f"Download error: {str(e)}")
                finally:
                    self.current_process = None
                    self.download_in_progress = False
                    self.parent.after(0, lambda: self.cancel_btn.config(state='disabled'))
            
            # Start the actual download process
            download_thread = threading.Thread(target=download_with_ydl)
            download_thread.daemon = True
            download_thread.start()
                
        except Exception as e:
            self.parent.after(0, lambda: self.status_label.config(text=f"Error: {str(e)}"))
            self.parent.after(0, lambda: self.cancel_btn.config(state='disabled'))
            self.download_in_progress = False
            print(f"Command execution error: {str(e)}")
        
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
        quality_preset = self.quality_preset.get()  # Get selected quality preset
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_filename = os.path.basename(os.path.splitext(input_file)[0]) + f".{output_format}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Reset UI
        self.progress_bar['value'] = 0
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start()
        self.status_label.config(text="Converting...")
        self.cancel_btn.config(state='normal')
        
        # Set flag
        self.conversion_in_progress = True
        
        # Print conversion info to terminal
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
            # Store the output file path as an instance variable so it's accessible in monitor_process
            self.current_output_file = output_file
            
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
            
            # Add the output file
            cmd.append(output_file)
            
            # Print command to terminal
            print(f"Executing: {' '.join(cmd)}")
            
            # Create and store the process
            self.current_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1  # Line buffered
            )
            
            # Monitor the process output
            self.monitor_process()
            
        except Exception as e:
            self.parent.after(0, lambda: self.status_label.config(text=f"Error: {str(e)}"))
            print(f"Conversion error: {str(e)}")
            self.cleanup_conversion()

    def monitor_process(self):
        """Monitor the FFmpeg process output and update progress"""
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
                self.parent.after(0, lambda: self.status_label.config(text=f"Conversion completed successfully"))
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

    def cleanup_conversion(self):
        """Clean up after conversion is done"""
        self.current_process = None
        self.conversion_in_progress = False
        self.parent.after(0, lambda: self.progress_bar.stop())
        self.parent.after(0, lambda: self.progress_bar.config(mode='determinate'))
        self.parent.after(0, lambda: self.cancel_btn.config(state='disabled'))

    def cancel_conversion(self):
        """Cancel the ongoing conversion"""
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
    
    def cancel_operation(self):
        # Cancel download operation
        if self.current_process:
            if isinstance(self.current_process, dict) and self.current_process.get('ydl'):
                # It's a download operation
                self.current_process['active'] = False
                ydl = self.current_process.get('ydl')
                if ydl:
                    # Attempt to abort the download
                    try:
                        ydl._finish_multiline_status()
                        ydl.to_screen("Download aborted by user")
                    except:
                        pass
                print("Download cancelled by user")
            elif hasattr(self.current_process, 'pid'):
                # It's a subprocess operation
                try:
                    if os.name == 'nt':  # Windows
                        self.current_process.terminate()
                    else:  # Unix/Linux
                        os.kill(self.current_process.pid, signal.SIGTERM)
                    print("Conversion cancelled by user")
                except Exception as e:
                    print(f"Error cancelling process: {str(e)}")
            
            self.status_label.config(text="Operation cancelled")
            self.current_process = None
        
        # Reset flags
        self.download_in_progress = False
        self.conversion_in_progress = False
        
        # Reset UI
        self.cancel_btn.config(state='disabled')
        self.progress_bar.stop()
        self.progress_bar.config(value=0, mode='determinate')

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
    app = YTDLPSimpleGui(parent)
    parent.mainloop()
