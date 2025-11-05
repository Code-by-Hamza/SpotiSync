import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sv_ttk
import webbrowser
import csv
import os
import subprocess
import shlex
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sys
import time
import threading
import queue
import shutil
import json
from datetime import datetime
# ----------------------------------------------

# Version info
APP_VERSION = "1.0.0"
APP_NAME = "SpotiSync"

#Tooltip Helper Class
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event):
        if self.tooltip_window:
            return
        try:
            bx = by = 0
            bbox = self.widget.bbox("insert")
            if bbox is not None:
                bx, by, _, _ = bbox
            x = self.widget.winfo_rootx() + (bx if bx else 0) + 20
            y = self.widget.winfo_rooty() + (by if by else 0) + 20
        except Exception:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + 20

        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="#333333",
            foreground="#FFFFFF",
            relief="solid",
            bd=1,
            padx=8,
            pady=6,
            justify="left",
            wraplength=360,
            font=("Segoe UI", 9),
        )
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# Main Application Class
class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        root.geometry("650x600") 
        root.minsize(550, 500)
        
        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, 'SpotiSync.ico')
            else:
                icon_path = os.path.join(os.path.dirname(__file__), 'SpotiSync.ico')
            
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass        

        self.settings_file = self.get_settings_path()
        self.settings = self.load_settings()
        
        # Download control
        self.cancel_download = False
        self.is_downloading = False
        
        # Stats tracking
        self.stats = {"success": 0, "failed": 0, "skipped": 0, "total": 0}

        sv_ttk.set_theme("dark")
        
        if self.settings.get("first_run", True):
            self.root.after(500, self.show_welcome_dialog)

        # Create the main frames
        input_frame = ttk.LabelFrame(root, text="Inputs")
        input_frame.pack(fill="x", padx=10, pady=5)
        input_frame.columnconfigure(2, weight=1)

        options_frame = ttk.LabelFrame(root, text="Options")
        options_frame.pack(fill="x", padx=10, pady=5)
        options_frame.columnconfigure(3, weight=1)
        options_frame.columnconfigure(5, weight=1)

        status_frame = ttk.LabelFrame(root, text="Status")
        status_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(1, weight=1)
        
        # Menu bar
        self.create_menu_bar()


        self.csv_label = ttk.Label(input_frame, text="CSV File:")
        self.csv_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.csv_help = ttk.Label(input_frame, text="(?)", cursor="question_arrow")
        self.csv_help.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="w")
        ToolTip(self.csv_help, "The .csv file you exported from Exportify.com\nNote: A CSV file can be any csv file as long as it has 'Track Name' column!")
        
        self.csv_path = tk.StringVar()
        self.csv_entry = ttk.Entry(input_frame, textvariable=self.csv_path)
        self.csv_entry.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.csv_button = ttk.Button(
            input_frame, 
            text="Browse...", 
            command=self.browse_csv_file
        )
        self.csv_button.grid(row=0, column=3, padx=5, pady=5)

        self.get_csv_button = ttk.Button(
            input_frame, 
            text="Get CSV...", 
            command=self.open_exportify
        )
        self.get_csv_button.grid(row=0, column=4, padx=(0, 5), pady=5)

        self.create_csv_button = ttk.Button(
            input_frame,
            text="Create CSV...",
            command=self.open_create_csv_window
        )
        self.create_csv_button.grid(row=0, column=5, padx=5, pady=5)

        self.out_label = ttk.Label(input_frame, text="Output:")
        self.out_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.out_help = ttk.Label(input_frame, text="(?)", cursor="question_arrow")
        self.out_help.grid(row=1, column=1, padx=(0, 5), pady=5, sticky="w")
        default_download_dir = self.settings.get("output_dir") or self.get_default_download_dir()
        ToolTip(self.out_help, f"The folder where your songs will be saved.\n(Default: '{default_download_dir}')")
        
        self.out_path = tk.StringVar(value=default_download_dir)
        self.out_entry = ttk.Entry(input_frame, textvariable=self.out_path)
        self.out_entry.grid(row=1, column=2, columnspan=2, padx=5, pady=5, sticky="ew")

        self.out_button = ttk.Button(
            input_frame, 
            text="Browse...", 
            command=self.browse_output_folder
        )
        self.out_button.grid(row=1, column=4, padx=5, pady=5)
        
        self.open_folder_button = ttk.Button(
            input_frame,
            text="Open Folder",
            command=self.open_output_folder
        )
        self.open_folder_button.grid(row=1, column=5, padx=(0, 5), pady=5)

        self.format_label = ttk.Label(options_frame, text="Format:")
        self.format_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.format_help = ttk.Label(options_frame, text="(?)", cursor="question_arrow")
        self.format_help.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="w")
        ToolTip(self.format_help, "The audio format you want for the final file.\n(e.g., mp3, m4a, wav)")
        
        self.format_var = tk.StringVar(value=self.settings.get("format", "mp3"))
        self.format_menu = ttk.Combobox(
            options_frame, 
            textvariable=self.format_var, 
            values=["mp3", "m4a", "wav", "opus", "aac"],
            width=8
        )

        self.format_menu.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        self.threads_label = ttk.Label(options_frame, text="Threads:")
        self.threads_label.grid(row=0, column=3, padx=5, pady=5, sticky="e")
        self.threads_help = ttk.Label(options_frame, text="(?)", cursor="question_arrow")
        self.threads_help.grid(row=0, column=4, padx=(0, 5), pady=5, sticky="w")
        ToolTip(self.threads_help, "Number of songs to download at the same time.\n(Default: 2)")
        
        self.threads_var = tk.StringVar(value=str(self.settings.get("threads", 2)))
        self.threads_entry = ttk.Entry(options_frame, textvariable=self.threads_var, width=5)
        self.threads_entry.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        self.archive_label = ttk.Label(options_frame, text="Archive File:")
        self.archive_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.archive_help = ttk.Label(options_frame, text="(?)", cursor="question_arrow")
        self.archive_help.grid(row=1, column=1, padx=(0, 5), pady=5, sticky="w")
        ToolTip(self.archive_help, "A text file to track downloaded songs.\nThis prevents downloading the same song twice.")
        
        self.archive_var = tk.StringVar(value="downloaded_archive.txt")
        self.archive_entry = ttk.Entry(options_frame, textvariable=self.archive_var)
        self.archive_entry.grid(row=1, column=2, columnspan=3, padx=5, pady=5, sticky="ew")

        self.dry_run_var = tk.BooleanVar()
        self.dry_run_check = ttk.Checkbutton(
            options_frame, 
            text="Dry Run...", 
            variable=self.dry_run_var
        )
        self.dry_run_check.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        self.dry_run_help = ttk.Label(options_frame, text="(?)", cursor="question_arrow")
        self.dry_run_help.grid(row=2, column=2, padx=(0, 5), pady=5, sticky="w")
        ToolTip(self.dry_run_help, "Show what commands would be run without\nactually downloading or modifying files.")

        # Help button (i have to fix later)
        self.help_button = ttk.Button(
            options_frame,
            text="Help",
            command=self.open_help_window
        )
        self.help_button.grid(row=2, column=5, padx=5, pady=5, sticky="e")
        self.exists_label = ttk.Label(options_frame, text="If file exists:")
        self.exists_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.exists_help = ttk.Label(options_frame, text="(?)", cursor="question_arrow")
        self.exists_help.grid(row=3, column=1, padx=(0, 5), pady=5, sticky="w")
        ToolTip(self.exists_help, "What to do if the target file already exists.\nDefault: Skip (do nothing).\nOverwrite: download again and replace the file.")

        self.exists_var = tk.StringVar(value="Skip")
        self.exists_menu = ttk.Combobox(
            options_frame,
            textvariable=self.exists_var,
            values=["Skip", "Overwrite"],
            width=10,
            state="readonly",
        )
        self.exists_menu.grid(row=3, column=2, padx=5, pady=5, sticky="w")

        self.stats_frame = ttk.Frame(status_frame)
        self.stats_frame.grid(row=0, column=0, padx=5, pady=(5, 0), sticky="ew")
        
        self.stats_label = ttk.Label(self.stats_frame, text="Ready to download")
        self.stats_label.pack(side="left")
        
        self.progress_bar = ttk.Progressbar(status_frame, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.status_log = tk.Text(status_frame, height=10, state="disabled")
        self.status_log.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_log.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.status_log['yscrollcommand'] = scrollbar.set
        
        # text tags for colored output
        self.status_log.tag_config("success", foreground="#4CAF50")
        self.status_log.tag_config("error", foreground="#F44336")
        self.status_log.tag_config("warning", foreground="#FF9800")
        self.status_log.tag_config("info", foreground="#2196F3")
        self.status_log.tag_config("progress", foreground="#9E9E9E")

        button_frame = ttk.Frame(status_frame)
        button_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        self.start_button = ttk.Button(
            button_frame, 
            text="Start Download", 
            command=self.start_download_thread)
        self.start_button.grid(row=0, column=0, padx=(0, 2), sticky="ew")
        
        self.cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_download_process,
            state="disabled"
        )
        self.cancel_button.grid(row=0, column=1, padx=(2, 0), sticky="ew")
        
        self.queue = queue.Queue()
        
        self.root.after(100, self.check_dependencies)
    # functions for buttons 
    def get_settings_path(self):
        """Get the path for settings file (AppData or portable mode)."""
        try:
            appdata = os.getenv('APPDATA')
            if appdata:
                app_dir = Path(appdata) / APP_NAME
                app_dir.mkdir(parents=True, exist_ok=True)
                return app_dir / "settings.json"
        except Exception:
            pass

        try:
            if getattr(sys, 'frozen', False):
                exe_dir = Path(sys.executable).parent
            else:
                exe_dir = Path(__file__).parent
            return exe_dir / "settings.json"
        except Exception:
            return Path("settings.json")
    
    def load_settings(self):
        """Load settings from JSON file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        # Default settings
        return {
            "first_run": True,
            "format": "mp3",
            "threads": 2,
            "output_dir": "",
            "recent_files": [],
            "archive_file": "downloaded_archive.txt",
            "exists_action": "Skip"
        }
    
    def save_settings(self):
        """Save current settings to JSON file."""
        try:
            self.settings["format"] = self.format_var.get()
            self.settings["threads"] = int(self.threads_var.get())
            self.settings["output_dir"] = self.out_path.get()
            self.settings["archive_file"] = self.archive_var.get()
            self.settings["exists_action"] = self.exists_var.get()
            
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def create_menu_bar(self):
        """Create application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open CSV...", command=self.browse_csv_file)
        file_menu.add_command(label="Open Output Folder", command=self.open_output_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Get CSV from Exportify", command=self.open_exportify)
        tools_menu.add_command(label="Create Custom CSV", command=self.open_create_csv_window)
        tools_menu.add_command(label="Check Dependencies", command=self.check_dependencies)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Help & Guide", command=self.open_help_window)
        help_menu.add_command(label="About", command=self.show_about_dialog)
    
    def show_welcome_dialog(self):
        """Show welcome dialog on first run."""
        msg = (
            f"Welcome to {APP_NAME}!\n\n"
            "Quick Start:\n"
            "1. Click 'Get CSV...' to export your Spotify playlist\n"
            "2. Select the CSV file you downloaded\n"
            "3. Choose your output folder\n"
            "4. Click 'Start Download'\n\n"
            "The app will automatically configure itself for you.\n"
            "Click 'Help' in the menu for detailed instructions."
        )
        
        result = messagebox.showinfo(
            "Welcome to SpotiSync",
            msg,
            parent=self.root
        )
        
        self.settings["first_run"] = False
        self.save_settings()
    
    def show_about_dialog(self):
        """Show about dialog with version info."""
        msg = (
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "A simple tool to download music from Spotify playlists\n"
            "using YouTube as the source.\n\n"
            "Uses yt-dlp for downloading.\n\n"
            f"Settings: {self.settings_file}\n"
            f"Date: {datetime.now().strftime('%Y-%m-%d')}"
        )
        messagebox.showinfo("About", msg, parent=self.root)
    
    def check_dependencies(self):
        """Check if required binaries (yt-dlp, ffmpeg) are available."""
        yt_dlp_cmd = self.get_yt_dlp_path()
        ffmpeg_path = self.get_ffmpeg_path()
        
        missing = []
        
        # Check yt-dlp
        try:
            result = subprocess.run(
                yt_dlp_cmd + ["--version"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                self.log_status(f"[INFO] yt-dlp found: {version}", "info")
            else:
                self.log_status("[WARNING] yt-dlp may not be properly installed", "warning")
                missing.append("yt-dlp")
        except FileNotFoundError:
            self.log_status("[ERROR] yt-dlp not found", "error")
            missing.append("yt-dlp")
        except Exception as e:
            self.log_status(f"[WARNING] Could not verify yt-dlp: {e}", "warning")
        
        # Check ffmpeg
        if ffmpeg_path:
            try:
                result = subprocess.run(
                    [ffmpeg_path, "-version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                
                if result.returncode == 0:
                    first_line = result.stdout.split('\n')[0]
                    self.log_status(f"[INFO] ffmpeg found: {first_line}", "info")
                else:
                    self.log_status("[WARNING] ffmpeg found but may not work correctly", "warning")
            except Exception as e:
                self.log_status(f"[WARNING] Could not verify ffmpeg: {e}", "warning")
        else:
            self.log_status("[INFO] ffmpeg not found (optional - may affect audio quality)", "info")
        
        if "yt-dlp" in missing:
            msg = (
                "yt-dlp not found!\n\n"
                "This is required for SpotiSync to work.\n"
                "Please ensure yt-dlp.exe is bundled with this application\n"
                "or install it separately.\n\n"
                "Download from: https://github.com/yt-dlp/yt-dlp/releases"
            )
            messagebox.showwarning("Dependency Missing", msg, parent=self.root)
    
    def open_output_folder(self):
        """Open the output folder in file explorer."""
        out_dir = self.out_path.get().strip()
        if not out_dir:
            messagebox.showwarning("No Folder", "Please select an output folder first.", parent=self.root)
            return
        
        try:
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            
            if os.name == 'nt':  # Windows
                os.startfile(out_dir)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', out_dir])
            else:  # Linux
                subprocess.run(['xdg-open', out_dir])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{e}", parent=self.root)
    
    def cancel_download_process(self):
        """Cancel the ongoing download."""
        if self.is_downloading:
            self.cancel_download = True
            self.log_status("[INFO] Cancelling download...", "warning")
            self.cancel_button.config(state="disabled")
    
    def update_stats_display(self):
        """Update the statistics display."""
        if self.stats["total"] > 0:
            completed = self.stats["success"] + self.stats["failed"] + self.stats["skipped"]
            text = (
                f"Progress: {completed}/{self.stats['total']} | "
                f"✓ {self.stats['success']} | "
                f"✗ {self.stats['failed']} | "
                f"⊘ {self.stats['skipped']}"
            )
            self.stats_label.config(text=text)
        else:
            self.stats_label.config(text="Ready to download")

    def browse_csv_file(self):
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
        )
        if filename:
            try:
                newfile = self.create_trackname_only_csv(filename)
                if newfile:
                    self.csv_path.set(newfile)
                    self.log_status(f"[INFO] Extracted 'Track Name' to: {newfile}")
                else:
                    self.csv_path.set(filename)
                    self.log_status("[WARN] 'Track Name' column not found; using original CSV.")
            except Exception as e:
                self.csv_path.set(filename)
                self.log_status(f"[ERROR] Failed to process CSV: {e}")

    def browse_output_folder(self):
        directory = filedialog.askdirectory(
            title="Select Output Folder"
        )
        if directory:
            self.out_path.set(directory)
    
    def open_exportify(self):
        """Opens the Exportify website in a new browser tab."""
        webbrowser.open_new_tab("https://exportify.net/")

    def create_trackname_only_csv(self, src_path: str) -> str | None:
        """Create a CSV containing only the 'Track Name' column from src_path.

        Returns the path to the new CSV (string) or None if the column wasn't found.
        """
        try:
            src = Path(src_path)
            with open(src, newline='', encoding='utf-8') as fh:
                reader = csv.reader(fh)
                headers = next(reader)
                track_idx = None
                for i, h in enumerate(headers):
                    if h and 'track' in h.lower() and 'name' in h.lower():
                        track_idx = i
                        break
                if track_idx is None:
                    return None

                dest = src.with_name(src.stem + "_trackname.csv")
                with open(dest, 'w', newline='', encoding='utf-8') as out:
                    writer = csv.writer(out)
                    writer.writerow(['Track Name'])
                    for row in reader:
                        val = row[track_idx] if track_idx < len(row) else ''
                        writer.writerow([val])

                return str(dest)
        except Exception as e:
            return None
    
    def get_yt_dlp_path(self):
        """Return an executable command list to run yt-dlp reliably on Windows and POSIX.

        Preference order:
        1) Bundled binary when frozen
        2) Local binary next to this script (yt-dlp.exe / yt-dlp)
        3) Binary discovered on PATH
        4) Python module fallback: [sys.executable, -m, yt_dlp]
        """
        binary_name = "yt-dlp.exe" if os.name == 'nt' else "yt-dlp"

        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundled = os.path.join(sys._MEIPASS, binary_name)
            if os.path.exists(bundled):
                return [bundled]

        try:
            script_dir = Path(__file__).resolve().parent
            local_bin = script_dir / binary_name
            if local_bin.exists():
                return [str(local_bin)]
        except Exception:
            pass

        found = shutil.which(binary_name)
        if found:
            return [found]

        return [sys.executable, "-m", "yt_dlp"]
    
    def get_ffmpeg_path(self):
        """Return the path to ffmpeg executable.

        Preference order:
        1) Bundled binary when frozen
        2) Local binary next to this script (ffmpeg.exe / ffmpeg)
        3) Binary discovered on PATH
        4) None (yt-dlp will use its own or show error)
        """
        binary_name = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"

        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundled = os.path.join(sys._MEIPASS, binary_name)
            if os.path.exists(bundled):
                return bundled

        try:
            script_dir = Path(__file__).resolve().parent
            local_bin = script_dir / binary_name
            if local_bin.exists():
                return str(local_bin)
        except Exception:
            pass

        found = shutil.which(binary_name)
        if found:
            return found
        return None

    def get_default_download_dir(self):
        """Return a sensible default Downloads directory for the current user.

        Tries common locations like ~/Downloads (case-insensitive). Falls back to
        'downloads' under the current user's home if the directory doesn't exist yet.
        """
        try:
            home = Path.home()
            candidates = [home / "Downloads", home / "downloads"]
            for c in candidates:
                if c.exists():
                    return str(c)

            return str(candidates[0])
        except Exception:
            return "downloads"

    def find_title_artist(self, headers):
        h = [x.lower() for x in headers]
        title_idx = None
        artist_idx = None
        for i, name in enumerate(h):
            if any(k in name for k in ('track', 'title', 'song')) and title_idx is None:
                title_idx = i
            if 'artist' in name and artist_idx is None:
                artist_idx = i
        return title_idx, artist_idx

    def build_query(self, title, artist):
        parts = []
        if title:
            parts.append(title.strip())
        if artist:
            parts.append(artist.strip())
        q = " - ".join(parts)
        q = " ".join(q.split())
        if len(q) == 0:
            return None
        return q + " audio"

    def download_track(self, query, csv_title, out_dir, audio_format, archive_file, dry_run=False, extra_opts=None, timeout=300, exists_action="Skip"):

        yt_dlp_cmd = self.get_yt_dlp_path()
        ffmpeg_path = self.get_ffmpeg_path()

        search_spec = f"ytsearch1:{query}"
        safe_title = self.sanitize_filename(csv_title)
        out_template = os.path.join(out_dir, f"{safe_title}.%(ext)s")

        cmd = yt_dlp_cmd + [
            search_spec,
            "--no-playlist",
            "-x", "--audio-format", audio_format,
            "-o", out_template,
            "--restrict-filenames",
            "--ignore-errors",
            "--newline",
            "--no-warnings",
        ]
        
        if ffmpeg_path:
            cmd += ["--ffmpeg-location", ffmpeg_path]
        
        if exists_action == "Overwrite":
            cmd += ["--force-overwrites"]
        if archive_file:
            cmd += ["--download-archive", archive_file]
        if extra_opts:
            cmd += extra_opts

        if dry_run:
            return {"query": query, "cmd": " ".join(shlex.quote(x) for x in cmd), "status": "dry-run"}

        target_path = os.path.join(out_dir, f"{safe_title}.{audio_format}")
        if exists_action == "Skip" and os.path.exists(target_path):
            return {"query": query, "status": "skipped"}

        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                startupinfo=startupinfo,
            )

            start_time = time.time()
            last_progress = None
            import re
            prog_re = re.compile(r"^\[download\]\s+(?P<percent>\d+(?:\.\d+)?)%\s+of\s+(?P<size>\S+)\s+at\s+(?P<speed>\S+)\s+ETA\s+(?P<eta>\S+)")

            if proc.stdout is not None:
                for line in proc.stdout:
                    line = (line or "").rstrip()
                    if not line:
                        continue
                    if line.startswith("[download] Destination:") or line.startswith("[ExtractAudio]"):
                        try:
                            self.queue.put({"status": "info", "query": query, "message": line})
                        except Exception:
                            pass
                    m = prog_re.match(line)
                    if m:
                        progress = {
                            "status": "progress",
                            "query": query,
                            "percent": m.group("percent"),
                            "size": m.group("size"),
                            "speed": m.group("speed"),
                            "eta": m.group("eta"),
                        }
                        last_progress = progress
                        try:
                            self.queue.put(progress)
                        except Exception:
                            pass

                    if timeout and (time.time() - start_time) > timeout:
                        proc.kill()
                        return {"query": query, "status": "timeout", "error": f"Timed out after {timeout}s"}

            proc.wait()
            success = proc.returncode == 0
            return {"query": query, "returncode": proc.returncode, "status": "ok" if success else "failed"}
        except FileNotFoundError as e:
            return {"query": query, "status": "failed", "error": f"yt-dlp not found: {e}"}
        except Exception as e:
            return {"query": query, "status": "failed", "error": str(e)}

    def parse_csv_and_build_queries(self, csv_path):
        queries = []
        try:
            with open(csv_path, newline='', encoding='utf-8') as fh:
                reader = csv.reader(fh)
                headers = next(reader)
                title_idx, artist_idx = self.find_title_artist(headers)

                if title_idx is None:
                    return None, "Couldn't auto-detect title column from CSV headers."

                for idx, row in enumerate(reader, start=1):
                    title = row[title_idx] if title_idx < len(row) else ""
                    artist = row[artist_idx] if (artist_idx is not None and artist_idx < len(row)) else ""
                    q = self.build_query(title, artist)
                    if q:
                        queries.append({"title": title, "artist": artist, "query": q})
            return queries, None
        except FileNotFoundError:
            return None, f"File not found: {csv_path}"
        except Exception as e:
            return None, f"Error parsing CSV: {e}"

    def open_help_window(self):
        """Open a small help window with a detailed usage guide."""
        if hasattr(self, "help_window") and self.help_window and tk.Toplevel.winfo_exists(self.help_window):
            self.help_window.lift()
            self.help_window.focus_force()
            return

        self.help_window = tk.Toplevel(self.root)
        self.help_window.title("How to use SpotiSync")
        self.help_window.geometry("560x420")
        self.help_window.minsize(420, 320)
        self.help_window.transient(self.root)

        # container
        container = ttk.Frame(self.help_window)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        title_lbl = ttk.Label(container, text="SpotiSync – Help & Guide", font=("Segoe UI", 12, "bold"))
        title_lbl.pack(anchor="w", pady=(0, 6))
        ttk.Separator(container, orient="horizontal").pack(fill="x", pady=(0, 8))

        text_frame = ttk.Frame(container)
        text_frame.pack(fill="both", expand=True)

        help_text = tk.Text(text_frame, wrap="word", height=15, state="normal")
        vscroll = ttk.Scrollbar(text_frame, orient="vertical", command=help_text.yview)
        help_text.configure(yscrollcommand=vscroll.set)
        help_text.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        guide = (
            "Welcome to SpotiSync!\n\n"
            "Quick Start\n"
            "- 'Get CSV...': Open Exportify to export playlists.\n"
            "- 'Browse...': Select an existing CSV file.\n"
            "- 'Create CSV...': Type titles (one per line) and save a CSV with a 'Track Name' column.\n"
            "- When you select a CSV, SpotiSync may auto-create a Track-Name-only CSV.\n"
            "- Output: Save location (defaults to your Downloads folder).\n"
            "- Format: mp3, m4a, wav, etc.\n"
            "- Threads: More threads = faster, heavier.\n"
            "- Archive File: Avoids duplicate downloads.\n"
            "- If file exists: 'Skip' (default) or 'Overwrite'.\n"
            "- Dry Run: Show commands without downloading or modifying files.\n"
            "- Start Download to begin.\n\n"
            "During Download\n"
            "- Live progress per track: percent, size, speed, ETA.\n"
            "- Completed: [OK]  Failed: [FAIL]  Timeout: [TIMEOUT]  Skipped: [SKIP].\n\n"
            "Notes & Tips\n"
            "- Searches YouTube for 'Track - Artist audio' when possible.\n"
            "- Filenames are sanitized.\n"
            "- If yt-dlp isn't found, Python module fallback is used.\n"
            "- Use the archive file to prevent re-downloading.\n"
            "- 'Open Exportify' opens the Exportify website.\n\n"
            "Troubleshooting\n"
            "- Check the Status log for yt-dlp errors.\n"
            "- Ensure the CSV has a 'Track Name' header.\n"
            "- Lower Threads if your network or system is slow.\n"
        )

        help_text.insert("1.0", guide)
        help_text.config(state="disabled")

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(8, 0))

        exportify_btn = ttk.Button(actions, text="Open Exportify", command=self.open_exportify)
        exportify_btn.pack(side="left")

        close_btn = ttk.Button(actions, text="Close", command=self.help_window.destroy)
        close_btn.pack(side="right")

        def on_close():
            try:
                self.help_window.destroy()
            finally:
                self.help_window = None

        self.help_window.protocol("WM_DELETE_WINDOW", on_close)

    def open_create_csv_window(self):
        """Open a small window to create a CSV with 'Track Name' column."""
        if hasattr(self, "create_csv_window") and self.create_csv_window and tk.Toplevel.winfo_exists(self.create_csv_window):
            self.create_csv_window.lift()
            self.create_csv_window.focus_force()
            return

        self.create_csv_window = tk.Toplevel(self.root)
        self.create_csv_window.title("Create Track CSV")
        self.create_csv_window.geometry("520x360")
        self.create_csv_window.minsize(420, 280)
        self.create_csv_window.transient(self.root)

        container = ttk.Frame(self.create_csv_window)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        lbl = ttk.Label(container, text="Enter one track title per line. The CSV will contain a 'Track Name' column.")
        lbl.pack(anchor="w", pady=(0, 8))

        text_frame = ttk.Frame(container)
        text_frame.pack(fill="both", expand=True)

        self.create_csv_text = tk.Text(text_frame, wrap="word", height=12)
        vscroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.create_csv_text.yview)
        self.create_csv_text.configure(yscrollcommand=vscroll.set)
        self.create_csv_text.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        actions = ttk.Frame(container)
        actions.pack(fill="x", pady=(10, 0))

        save_btn = ttk.Button(actions, text="Save CSV", command=self.save_created_csv)
        save_btn.pack(side="left")

        cancel_btn = ttk.Button(actions, text="Cancel", command=self.create_csv_window.destroy)
        cancel_btn.pack(side="right")

        def on_close_create():
            try:
                self.create_csv_window.destroy()
            finally:
                self.create_csv_window = None
                self.create_csv_text = None

        self.create_csv_window.protocol("WM_DELETE_WINDOW", on_close_create)

    def save_created_csv(self):
        """Save the entered titles to a CSV and select it."""
        try:
            raw = self.create_csv_text.get("1.0", tk.END)
            titles = [line.strip() for line in raw.splitlines() if line.strip()]
            if not titles:
                self.log_status("[WARN] No titles entered; nothing to save.")
                return

            default_dir = self.out_path.get().strip() or os.getcwd()
            Path(default_dir).mkdir(parents=True, exist_ok=True)
            initial_path = os.path.join(default_dir, "tracks.csv")

            save_path = filedialog.asksaveasfilename(
                title="Save CSV",
                defaultextension=".csv",
                filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
                initialfile=os.path.basename(initial_path),
                initialdir=os.path.dirname(initial_path),
            )
            if not save_path:
                return

            with open(save_path, 'w', newline='', encoding='utf-8') as fh:
                writer = csv.writer(fh)
                writer.writerow(['Track Name'])
                for t in titles:
                    writer.writerow([t])

            self.csv_path.set(save_path)
            self.log_status(f"[INFO] Created CSV with {len(titles)} tracks: {save_path}")

        except Exception as e:
            self.log_status(f"[ERROR] Failed to create CSV: {e}")
        finally:
            try:
                if hasattr(self, "create_csv_window") and self.create_csv_window:
                    self.create_csv_window.destroy()
            except Exception:
                pass

    def log_status(self, message, tag=None):
        """Safely inserts a message into the status_log text widget with optional color."""
        self.status_log.config(state="normal")
        
        if tag:
            self.status_log.insert(tk.END, message + "\n", tag)
        else:
            if message.startswith("[OK]") or message.startswith("[SUCCESS]"):
                self.status_log.insert(tk.END, message + "\n", "success")
            elif message.startswith("[FAIL]") or message.startswith("[ERROR]"):
                self.status_log.insert(tk.END, message + "\n", "error")
            elif message.startswith("[WARN]") or message.startswith("[WARNING]"):
                self.status_log.insert(tk.END, message + "\n", "warning")
            elif message.startswith("[INFO]"):
                self.status_log.insert(tk.END, message + "\n", "info")
            elif message.startswith("[PROG]"):
                self.status_log.insert(tk.END, message + "\n", "progress")
            else:
                self.status_log.insert(tk.END, message + "\n")
        
        self.status_log.config(state="disabled")
        self.status_log.see(tk.END)  

    def process_queue(self):
        """Checks the queue for messages from the download thread."""
        try:
            while True:
                msg = self.queue.get_nowait()

                if msg == "DONE":
                    self.start_button.config(state="normal")
                    self.cancel_button.config(state="disabled")
                    self.is_downloading = False
                    self.save_settings()  
                    
                    if not self.cancel_download:
                        self.log_status("\n✓ Download Complete!", "success")
                        self.update_stats_display()
                        
                        if messagebox.askyesno(
                            "Complete",
                            f"Download finished!\n\n"
                            f"Success: {self.stats['success']}\n"
                            f"Failed: {self.stats['failed']}\n"
                            f"Skipped: {self.stats['skipped']}\n\n"
                            f"Open output folder?",
                            parent=self.root
                        ):
                            self.open_output_folder()
                    else:
                        self.log_status("\n✗ Download Cancelled", "warning")
                    
                    return 
                
                elif isinstance(msg, dict) and 'total_tracks' in msg:
                    self.progress_bar['maximum'] = msg['total_tracks']
                    self.progress_bar['value'] = 0
                    self.stats = {"success": 0, "failed": 0, "skipped": 0, "total": msg['total_tracks']}
                    self.update_stats_display()
                
                elif isinstance(msg, dict) and 'status' in msg:
                    status = msg.get("status")
                    query = msg.get("query")
                    if status == "progress":
                        pct = msg.get("percent")
                        size = msg.get("size")
                        speed = msg.get("speed")
                        eta = msg.get("eta")
                        completed = self.stats["success"] + self.stats["failed"] + self.stats["skipped"]
                        self.root.title(f"{APP_NAME} - Downloading ({completed}/{self.stats['total']}) - {pct}%")
                        self.log_status(f"[PROG] {pct}% of {size} at {speed} ETA {eta}  :: {query}")

                    elif status == "info":
                        self.log_status(f"[INFO] {msg.get('message','').strip()}")

                    elif status == "dry-run":
                        self.log_status(f"[DRY] {msg['cmd']}")

                    elif status == "ok":
                        self.stats["success"] += 1
                        self.log_status(f"[OK] {query}", "success")
                        self.progress_bar.step(1)
                        self.update_stats_display()

                    elif status == "failed":
                        self.stats["failed"] += 1
                        code = msg.get('returncode')
                        err = msg.get('error') or (msg.get('stderr') or '').strip()

                        if code is not None:
                            self.log_status(f"[FAIL] {query} (Code: {code})", "error")
                        else:
                            self.log_status(f"[FAIL] {query}", "error")
                        if err:
                            self.log_status(f"       Error: {err}", "error")
                        self.progress_bar.step(1)
                        self.update_stats_display()
                    elif status == "skipped":
                        self.stats["skipped"] += 1
                        self.log_status(f"[SKIP] {query}", "warning")
                        self.progress_bar.step(1)
                        self.update_stats_display()
                    elif status == "timeout":
                        self.stats["failed"] += 1
                        self.log_status(f"[TIMEOUT] {query}", "error")
                        err = msg.get('error')
                        if err:
                            self.log_status(f"          {err}", "error")
                        self.progress_bar.step(1)
                        self.update_stats_display()
                    else:
                        self.log_status(f"[{status.upper()}] {query}")

                else:
                    self.log_status(str(msg))

        except queue.Empty:
            if self.is_downloading or not self.queue.empty():
                self.root.after(100, self.process_queue)

    def start_download_thread(self):
        """Starts the download process in a separate thread."""
        self.start_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.cancel_download = False
        self.is_downloading = True

        self.status_log.config(state="normal")
        self.status_log.delete("1.0", tk.END)
        self.status_log.config(state="disabled")

        csv_path = self.csv_path.get()
        out_dir = self.out_path.get()
        audio_format = self.format_var.get()
        archive_file = self.archive_var.get()
        dry_run = self.dry_run_var.get()
        exists_action = self.exists_var.get()
        
        try:
            threads = int(self.threads_var.get())
            if threads < 1:
                threads = 1
        except ValueError:
            threads = 1

        if not csv_path:
            messagebox.showerror("Error", "Please select a CSV file.", parent=self.root)
            self.start_button.config(state="normal")
            self.cancel_button.config(state="disabled")
            self.is_downloading = False
            return
        
        if not out_dir:
            messagebox.showerror("Error", "Please select an output folder.", parent=self.root)
            self.start_button.config(state="normal")
            self.cancel_button.config(state="disabled")
            self.is_downloading = False
            return

        args = (csv_path, out_dir, audio_format, threads, archive_file, dry_run, exists_action)
        threading.Thread(target=self.download_worker, args=args, daemon=True).start()

        self.root.after(100, self.process_queue)

    def download_worker(self, csv_path, out_dir, audio_format, threads, archive_file, dry_run, exists_action):
        """This is the main function that runs in the new thread."""
        try:
            self.queue.put(f"Parsing CSV: {csv_path} ...")
            Path(out_dir).mkdir(parents=True, exist_ok=True)

            queries, error = self.parse_csv_and_build_queries(csv_path)
            if error:
                self.queue.put(f"[ERROR] {error}")
                self.queue.put("DONE")
                return

            self.queue.put(f"Found {len(queries)} tracks. Using {threads} threads.")
            self.queue.put({"total_tracks": len(queries)})
            extra_opts = None 

            start_time = time.time()
            with ThreadPoolExecutor(max_workers=threads) as ex:
                futures = {
                ex.submit(self.download_track, q['query'], q['title'], out_dir, audio_format, archive_file, dry_run, extra_opts, 300, exists_action): q 
                for q in queries}

                for fut in as_completed(futures):
                    # Check for cancellation
                    if self.cancel_download:
                        self.queue.put("[INFO] Cancelling remaining downloads...")
                        ex.shutdown(wait=False, cancel_futures=True)
                        break
                    
                    try:
                        res = fut.result()
                        self.queue.put(res)
                    except Exception as e:
                        self.queue.put(f"[THREAD ERROR] {e}")

            elapsed = time.time() - start_time
            if not self.cancel_download:
                self.queue.put(f"Total time: {elapsed:.1f}s. Archive: {archive_file}")

        except Exception as e:
            self.queue.put(f"[FATAL ERROR] {e}")
        finally:
            self.queue.put("DONE")
            self.root.title(f"{APP_NAME} v{APP_VERSION}")
    
    def sanitize_filename(self, s):
        """Strips invalid characters from a string for a filename."""
        s = str(s).strip()
        # Replace characters that are invalid in Windows filenames
        s = s.replace(':', '-').replace('"', "'").replace('?', '').replace('/', '_')
        s = s.replace('\\', '_').replace('*', '_').replace('<', '_').replace('>', '_').replace('|', '_')
        return " ".join(s.split()) # Consolidate whitespace
    
    def parse_csv_and_build_queries(self, csv_path):
        queries = []
        try:
            with open(csv_path, newline='', encoding='utf-8') as fh:
                reader = csv.reader(fh)
                headers = next(reader)
                title_idx, artist_idx = self.find_title_artist(headers)
                
                if title_idx is None:
                    return None, "Couldn't auto-detect title column from CSV headers."

                for idx, row in enumerate(reader, start=1):
                    title = row[title_idx] if title_idx < len(row) else ""
                    artist = ""
                    q = self.build_query(title, artist)
                    if q:
                        queries.append({"title": title, "artist": "", "query": q})
            return queries, None 
        except FileNotFoundError:
            return None, f"File not found: {csv_path}"
        except Exception as e:
            return None, f"Error parsing CSV: {e}"

# Run the Application
if __name__ == "__main__":
    main_window = tk.Tk()
    app = DownloaderApp(main_window)
    main_window.mainloop()