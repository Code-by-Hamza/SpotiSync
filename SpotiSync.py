import tkinter as tk
from tkinter import ttk, filedialog
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
# ----------------------------------------------

# --- Tooltip Helper Class ---
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
        
        # Get widget position
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True) 
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(
            self.tooltip_window, 
            text=self.text, 
            background="#333333", 
            foreground="#FFFFFF", 
            relief="solid", 
            borderwidth=1, 
            padding=5
        )
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# --- Main Application Class ---
class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root = root
        self.root.title("SpotiSync")
        root.geometry("600x550") 
        root.minsize(500, 450)

        sv_ttk.set_theme("dark")

        # --- 1. Create the main frames ---
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

        # --- 2. Populate the "Inputs" frame ---
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

        self.out_label = ttk.Label(input_frame, text="Output:")
        self.out_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.out_help = ttk.Label(input_frame, text="(?)", cursor="question_arrow")
        self.out_help.grid(row=1, column=1, padx=(0, 5), pady=5, sticky="w")
        ToolTip(self.out_help, "The folder where your songs will be saved.\n(Default: 'downloads')")
        
        self.out_path = tk.StringVar(value="downloads")
        self.out_entry = ttk.Entry(input_frame, textvariable=self.out_path)
        self.out_entry.grid(row=1, column=2, columnspan=2, padx=5, pady=5, sticky="ew")

        self.out_button = ttk.Button(
            input_frame, 
            text="Browse...", 
            command=self.browse_output_folder
        )
        self.out_button.grid(row=1, column=4, padx=5, pady=5)

        # --- 3. Populate the "Options" frame ---
        self.format_label = ttk.Label(options_frame, text="Format:")
        self.format_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.format_help = ttk.Label(options_frame, text="(?)", cursor="question_arrow")
        self.format_help.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="w")
        ToolTip(self.format_help, "The audio format you want for the final file.\n(e.g., mp3, m4a, wav)")
        
        self.format_var = tk.StringVar(value="mp3")
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
        
        self.threads_var = tk.StringVar(value="2")
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
        ToolTip(self.dry_run_help, "Show what commands would be run without\nactually downloading any files.")

        # Help button
        self.help_button = ttk.Button(
            options_frame,
            text="Help",
            command=self.open_help_window
        )
        self.help_button.grid(row=2, column=5, padx=5, pady=5, sticky="e")

        # --- 4. Populate the "Status" frame ---
        self.progress_bar = ttk.Progressbar(status_frame, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.status_log = tk.Text(status_frame, height=10, state="disabled")
        self.status_log.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_log.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.status_log['yscrollcommand'] = scrollbar.set

        self.start_button = ttk.Button(
            status_frame, 
            text="Start Download", 
            command=self.start_download_thread)
        self.start_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.queue = queue.Queue()

    # --- 5. Button Functions ---
    def browse_csv_file(self):
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
        )
        if filename:
            # Attempt to auto-extract only the 'Track Name' column to a new CSV.
            try:
                newfile = self.create_trackname_only_csv(filename)
                if newfile:
                    self.csv_path.set(newfile)
                    self.log_status(f"[INFO] Extracted 'Track Name' to: {newfile}")
                else:
                    # If extraction failed (no column), fall back to original file
                    self.csv_path.set(filename)
                    self.log_status("[WARN] 'Track Name' column not found; using original CSV.")
            except Exception as e:
                # On unexpected errors, fall back and report
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
                # Find index of 'Track Name' (case-insensitive, allow surrounding text)
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
            # Let caller handle logging; return None to indicate failure
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

        # 1) PyInstaller bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundled = os.path.join(sys._MEIPASS, binary_name)
            if os.path.exists(bundled):
                return [bundled]

        # 2) Local directory
        try:
            script_dir = Path(__file__).resolve().parent
            local_bin = script_dir / binary_name
            if local_bin.exists():
                return [str(local_bin)]
        except Exception:
            pass

        # 3) PATH
        found = shutil.which(binary_name)
        if found:
            return [found]

        # 4) Python module fallback
        return [sys.executable, "-m", "yt_dlp"]

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

    def download_track(self, query, csv_title, out_dir, audio_format, archive_file, dry_run=False, extra_opts=None, timeout=300):
        # Resolve yt-dlp command (may be a list)
        yt_dlp_cmd = self.get_yt_dlp_path()

        search_spec = f"ytsearch1:{query}"
        safe_title = self.sanitize_filename(csv_title)
        # Create an output template using the sanitized title
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
        if archive_file:
            cmd += ["--download-archive", archive_file]
        if extra_opts:
            cmd += extra_opts

        if dry_run:
            return {"query": query, "cmd": " ".join(shlex.quote(x) for x in cmd), "status": "dry-run"}

        try:
            # Hide console window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # Stream stdout to parse progress
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
            # Regex for lines like: "[download]  12.3% of 4.95MiB at 1.23MiB/s ETA 00:03"
            import re
            prog_re = re.compile(r"^\[download\]\s+(?P<percent>\d+(?:\.\d+)?)%\s+of\s+(?P<size>\S+)\s+at\s+(?P<speed>\S+)\s+ETA\s+(?P<eta>\S+)")

            if proc.stdout is not None:
                for line in proc.stdout:
                    line = (line or "").rstrip()
                    if not line:
                        continue
                    # Push informative lines for context
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

                    # Timeout guard
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
        # If already open, focus it
        if hasattr(self, "help_window") and self.help_window and tk.Toplevel.winfo_exists(self.help_window):
            self.help_window.lift()
            self.help_window.focus_force()
            return

        self.help_window = tk.Toplevel(self.root)
        self.help_window.title("How to use SpotiSync")
        self.help_window.geometry("560x420")
        self.help_window.minsize(420, 320)
        self.help_window.transient(self.root)

        # Container frame
        container = ttk.Frame(self.help_window)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_lbl = ttk.Label(container, text="SpotiSync – Help & Guide", font=("Segoe UI", 12, "bold"))
        title_lbl.pack(anchor="w", pady=(0, 8))

        # Scrollable text
        text_frame = ttk.Frame(container)
        text_frame.pack(fill="both", expand=True)

        help_text = tk.Text(text_frame, wrap="word", height=15, state="normal")
        vscroll = ttk.Scrollbar(text_frame, orient="vertical", command=help_text.yview)
        help_text.configure(yscrollcommand=vscroll.set)
        help_text.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        guide = (
            "Welcome to SpotiSync!\n\n"
            "Quick Start:\n"
            "1) CSV File: Click 'Get CSV...' to open Exportify, or 'Browse...' to select a CSV.\n"
            "   - A CSV with a 'Track Name' column works best.\n"
            "   - When you select a CSV, SpotiSync tries to auto-make a file with only 'Track Name'.\n"
            "2) Output: Choose where downloaded songs will be saved (default: downloads).\n"
            "3) Format: Pick your desired audio format (e.g., mp3, m4a, wav).\n"
            "4) Threads: Number of simultaneous downloads. Higher = faster, but heavier.\n"
            "5) Archive File: Keeps track of downloaded tracks to avoid duplicates.\n"
            "6) Dry Run: If enabled, shows the commands without downloading.\n"
            "7) Start Download: Begins processing. Progress and results show in the Status log.\n\n"
            "Notes & Tips:\n"
            "- The app searches YouTube for 'Track - Artist audio' when possible.\n"
            "- Filenames are sanitized to be safe for your system.\n"
            "- If yt-dlp isn't found, the app will try running it via Python module fallback.\n"
            "- Use the archive file to prevent re-downloading tracks you've already saved.\n"
            "- You can open Exportify directly from the 'Get CSV...' button.\n\n"
            "Troubleshooting:\n"
            "- If downloads fail, check the Status log for error messages from yt-dlp.\n"
            "- Ensure your CSV has a recognizable 'Track Name' column header.\n"
            "- Try lowering Threads on slow networks or systems.\n"
        )

        help_text.insert("1.0", guide)
        help_text.config(state="disabled")

        # Action row
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

    def log_status(self, message):
        """Safely inserts a message into the status_log text widget."""
        self.status_log.config(state="normal")
        self.status_log.insert(tk.END, message + "\n")
        self.status_log.config(state="disabled")
        self.status_log.see(tk.END) # Auto-scroll to the bottom

    def process_queue(self):
        """Checks the queue for messages from the download thread."""
        try:
            while True:
                # Get a message from the queue
                msg = self.queue.get_nowait()

                if msg == "DONE":
                    # Re-enable the start button
                    self.start_button.config(state="normal")
                    self.log_status("\n--- Download Finished! ---")
                    return # Stop checking the queue
                
                elif isinstance(msg, dict) and 'total_tracks' in msg:
                    # Set up the progress bar
                    self.progress_bar['maximum'] = msg['total_tracks']
                    self.progress_bar['value'] = 0
                
                elif isinstance(msg, dict) and 'status' in msg:
                    # Message from download_track
                    status = msg.get("status")
                    query = msg.get("query")
                    if status == "progress":
                        pct = msg.get("percent")
                        size = msg.get("size")
                        speed = msg.get("speed")
                        eta = msg.get("eta")
                        self.log_status(f"[PROG] {pct}% of {size} at {speed} ETA {eta}  :: {query}")
                        # Do not advance the overall progress bar on incremental progress
                    elif status == "info":
                        self.log_status(f"[INFO] {msg.get('message','').strip()}")
                    elif status == "dry-run":
                        self.log_status(f"[DRY] {msg['cmd']}")
                    elif status == "ok":
                        self.log_status(f"[OK] {query}")
                        self.progress_bar.step(1)
                    elif status == "failed":
                        code = msg.get('returncode')
                        err = msg.get('error') or (msg.get('stderr') or '').strip()
                        if code is not None:
                            self.log_status(f"[FAIL] {query} (Code: {code})")
                        else:
                            self.log_status(f"[FAIL] {query}")
                        if err:
                            self.log_status(f"       Error: {err}")
                        self.progress_bar.step(1)
                    elif status == "timeout":
                        self.log_status(f"[TIMEOUT] {query}")
                        err = msg.get('error')
                        if err:
                            self.log_status(f"          {err}")
                        self.progress_bar.step(1)
                    else:
                        self.log_status(f"[{status.upper()}] {query}")

                else:
                    # It's a plain string message
                    self.log_status(str(msg))

        except queue.Empty:
            # If the queue is empty, schedule this function to run again
            self.root.after(100, self.process_queue)

    def start_download_thread(self):
        """Starts the download process in a separate thread."""
        # 1. Disable button
        self.start_button.config(state="disabled")

        # 2. Clear the log
        self.status_log.config(state="normal")
        self.status_log.delete("1.0", tk.END)
        self.status_log.config(state="disabled")

        # 3. Get all values from the GUI
        csv_path = self.csv_path.get()
        out_dir = self.out_path.get()
        audio_format = self.format_var.get()
        archive_file = self.archive_var.get()
        dry_run = self.dry_run_var.get()
        
        try:
            threads = int(self.threads_var.get())
            if threads < 1:
                threads = 1
        except ValueError:
            threads = 1
        
        # 4. Basic validation
        if not csv_path:
            self.log_status("[ERROR] Please select a CSV file.")
            self.start_button.config(state="normal")
            return

        # 5. Start the worker thread
        # We pass all the GUI values to the worker function
        args = (csv_path, out_dir, audio_format, threads, archive_file, dry_run)
        threading.Thread(target=self.download_worker, args=args, daemon=True).start()

        # 6. Start the queue-checking loop
        self.root.after(100, self.process_queue)

    def download_worker(self, csv_path, out_dir, audio_format, threads, archive_file, dry_run):
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
                ex.submit(self.download_track, q['query'], q['title'], out_dir, audio_format, archive_file, dry_run, extra_opts): q 
                for q in queries}

                for fut in as_completed(futures):
                    try:
                        res = fut.result()
                        # Put the result dictionary directly into the queue
                        self.queue.put(res)
                    except Exception as e:
                        self.queue.put(f"[THREAD ERROR] {e}")

            elapsed = time.time() - start_time
            self.queue.put(f"Total time: {elapsed:.1f}s. Archive: {archive_file}")

        except Exception as e:
            self.queue.put(f"[FATAL ERROR] {e}")
        finally:
            self.queue.put("DONE")
    
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
            return queries, None # Return (queries, error)
        except FileNotFoundError:
            return None, f"File not found: {csv_path}"
        except Exception as e:
            return None, f"Error parsing CSV: {e}"

# --- Run the Application ---
if __name__ == "__main__":
    main_window = tk.Tk()
    app = DownloaderApp(main_window)
    main_window.mainloop()