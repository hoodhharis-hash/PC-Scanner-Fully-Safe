import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import subprocess
import time

# ================= CONFIG =================
DANGEROUS_EXTENSIONS = (".exe", ".bat", ".cmd", ".vbs", ".ps1", ".scr")

USER_DIRS = [
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Documents")
]

# ================= ADMIN CHECK =================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# ================= OPEN FILE LOCATION (FIXED) =================
def open_location(path):
    if os.path.exists(path):
        subprocess.Popen(
            ["explorer", "/select,", os.path.normpath(path)]
        )

# ================= RISK LEVEL =================
def calculate_risk(file_path):
    try:
        size = os.path.getsize(file_path)
        ext = file_path.lower()

        if ext.endswith((".vbs", ".ps1", ".scr")):
            return "HIGH"
        if size > 10 * 1024 * 1024:
            return "HIGH"
        if size > 3 * 1024 * 1024:
            return "MEDIUM"
        return "LOW"
    except:
        return "LOW"

# ================= SCAN =================
def scan_files(paths, progress_cb, done_cb):
    results = []
    all_files = []

    for path in paths:
        for root, dirs, files in os.walk(path):
            for f in files:
                all_files.append(os.path.join(root, f))

    total = len(all_files) or 1

    for i, file_path in enumerate(all_files):
        try:
            progress_cb((i / total) * 100)
            time.sleep(0.001)

            if file_path.lower().endswith(DANGEROUS_EXTENSIONS):
                risk = calculate_risk(file_path)
                results.append((file_path, risk))

        except (PermissionError, FileNotFoundError):
            continue

    progress_cb(100)
    done_cb(results)

# ================= UI =================
class HackerScanner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("System Security Scanner")
        self.geometry("1000x600")
        self.configure(bg="#0a0f0a")

        self.setup_style()
        self.create_ui()

    # ================= STYLE =================
    def setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background="#0a0f0a",
            foreground="lime",
            rowheight=26,
            fieldbackground="#0a0f0a",
            borderwidth=0
        )

        style.configure(
            "Treeview.Heading",
            background="#050805",
            foreground="lime",
            font=("Consolas", 11, "bold")
        )

        style.map("Treeview", background=[("selected", "#0f3d0f")])

        style.configure(
            "TProgressbar",
            background="lime",
            troughcolor="#050805"
        )

    # ================= UI LAYOUT =================
    def create_ui(self):
        header = tk.Frame(self, bg="#050805", height=60)
        header.pack(fill="x")

        tk.Label(
            header,
            text="SYSTEM SECURITY SCANNER",
            fg="lime",
            bg="#050805",
            font=("Consolas", 20, "bold")
        ).pack(pady=12)

        controls = tk.Frame(self, bg="#0a0f0a")
        controls.pack(pady=10)

        self.mode = tk.StringVar(value="user")

        for text, val in [("USER MODE", "user"), ("ADMIN MODE", "admin")]:
            tk.Radiobutton(
                controls,
                text=text,
                variable=self.mode,
                value=val,
                fg="lime",
                bg="#0a0f0a",
                selectcolor="#0a0f0a",
                font=("Consolas", 11)
            ).pack(side="left", padx=20)

        self.scan_btn = tk.Button(
            controls,
            text="START SCAN",
            bg="#050805",
            fg="lime",
            font=("Consolas", 12, "bold"),
            width=14,
            command=self.start_scan
        )
        self.scan_btn.pack(side="left", padx=30)

        self.status = tk.Label(
            self,
            text="Idle",
            fg="lime",
            bg="#0a0f0a",
            font=("Consolas", 10)
        )
        self.status.pack()

        self.progress = ttk.Progressbar(self, length=800)
        self.progress.pack(pady=10)

        # ===== TABLE =====
        self.tree = ttk.Treeview(
            self,
            columns=("Risk", "Path"),
            show="headings"
        )

        self.tree.heading("Risk", text="Risk Level")
        self.tree.heading("Path", text="File Location")

        self.tree.column("Risk", width=120, anchor="center")
        self.tree.column("Path", width=820)

        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.tree.bind("<Double-1>", self.open_selected)

    # ================= SCAN =================
    def start_scan(self):
        self.tree.delete(*self.tree.get_children())
        self.progress['value'] = 0
        self.status.config(text="Scanning...")

        if self.mode.get() == "admin" and not is_admin():
            messagebox.showerror("Admin Required", "Run as Administrator.")
            self.status.config(text="Idle")
            return

        paths = USER_DIRS if self.mode.get() == "user" else ["C:/"]

        threading.Thread(
            target=scan_files,
            args=(paths, self.update_progress, self.scan_done),
            daemon=True
        ).start()

    # ================= THREAD SAFE =================
    def update_progress(self, value):
        self.after(0, lambda: self.progress.configure(value=value))

    def scan_done(self, results):
        self.after(0, lambda: self.show_results(results))

    # ================= RESULTS =================
    def show_results(self, results):
        self.status.config(text="Scan Complete")

        if not results:
            self.tree.insert("", "end", values=("SAFE", "No suspicious files found"))
            return

        for file_path, risk in results:
            self.tree.insert(
                "",
                "end",
                values=(risk, file_path)
            )

    # ================= OPEN FILE LOCATION (FIXED) =================
    def open_selected(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        file_path = self.tree.item(selected[0], "values")[1]
        open_location(file_path)

# ================= RUN =================
if __name__ == "__main__":
    app = HackerScanner()
    app.mainloop()
