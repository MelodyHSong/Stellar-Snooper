# ☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆
# ☆ Author: ☆ MelodyHSong ☆
# ☆ Language: Python
# ☆ File Name: app.py
# ☆ Description: Stellar Snooper - Cosmic Storage Telemetry & Disk Space Workstation
# ☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆

import sys
import os
import json
import time
import queue
import string
import shutil
import threading
import subprocess
from datetime import datetime
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from file_searcher import (
    search_files_engine,
    save_results_to_file as save_search_results,
    calculate_relevance,
    search_files as cli_search_files
)
from directory_mapper import (
    generate_directory_tree,
    save_tree_to_file as save_map_tree,
    map_directory as cli_map_directory
)

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Enable Windows High-DPI Awareness for crisp rendering
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# ==============================================================================
# ☆ COSMIC COLOR PALETTE & THEME
# ==============================================================================
BG_MAIN = "#0d1117"          # Deep space obsidian
BG_PANEL = "#161b22"         # Surface / card background
BG_SURFACE = "#21262d"       # Elevated widget background
BG_ACTIVE = "#30363d"        # Hover / selected item
BORDER_COLOR = "#30363d"     # Panel rim border
BORDER_ACTIVE = "#58a6ff"    # Focused active border

TEXT_PRIMARY = "#e2e8f0"     # Starlight white
TEXT_MUTED = "#8b949e"       # Dust gray
TEXT_DIM = "#586069"         # Nebula shadow

ACCENT_CYAN = "#58a6ff"      # Starlight cyan
ACCENT_GOLD = "#f2cc60"      # Celestial star gold
ACCENT_MINT = "#7ee787"      # Status ok / green
ACCENT_CORAL = "#f85149"     # Alert / danger red
ACCENT_PURPLE = "#bc8cff"    # Cosmic amethyst

FONT_HEADER = ("Segoe UI", 13, "bold")
FONT_SUBHEADER = ("Segoe UI", 10)
FONT_UI = ("Segoe UI", 9)
FONT_UI_BOLD = ("Segoe UI", 9, "bold")
FONT_CODE = ("Consolas", 10)
FONT_STATS = ("Consolas", 9)


def format_bytes(size_bytes):
    """Formats bytes into human-readable size string (TB, GB, MB, KB, B)."""
    if size_bytes >= 1024**4:
        return f"{size_bytes / (1024**4):.2f} TB"
    elif size_bytes >= 1024**3:
        return f"{size_bytes / (1024**3):.2f} GB"
    elif size_bytes >= 1024**2:
        return f"{size_bytes / (1024**2):.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes} B"


def get_available_drives():
    """Detects available drive letters on Windows with volume labels and free space."""
    drives = []
    if sys.platform != "win32":
        return [("/", "Root", 0, 0, 0)]

    for letter in string.ascii_uppercase:
        drive_root = f"{letter}:\\"
        if os.path.exists(drive_root):
            vol_name = ""
            try:
                import ctypes
                vol_buf = ctypes.create_unicode_buffer(261)
                ctypes.windll.kernel32.GetVolumeInformationW(
                    drive_root, vol_buf, ctypes.sizeof(vol_buf),
                    None, None, None, None, 0
                )
                vol_name = vol_buf.value
            except Exception:
                pass

            try:
                total, used, free = shutil.disk_usage(drive_root)
            except Exception:
                total, used, free = 0, 0, 0

            drives.append({
                "letter": f"{letter}:",
                "root": drive_root,
                "label": vol_name if vol_name else "Local Disk",
                "total": total,
                "used": used,
                "free": free
            })
    return drives


class DriveAnalyzerApp:
    def __init__(self, root, initial_target=None):
        self.root = root
        self.root.title("⭐ Stellar Snooper - [Cosmic Storage Workstation]")
        self.root.geometry("1140x720")
        self.root.minsize(860, 540)
        self.root.configure(bg=BG_MAIN)

        # Asset & Path Resolution
        self.app_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

        # State Variables
        self.config_path = os.path.join(self.base_dir, "config.json")
        self.config = self.load_config()
        self.background_queue = queue.Queue()
        self.is_scanning = False
        self.stop_requested = False
        self.scan_thread = None

        # File Searcher State
        self.is_searching = False
        self.stop_search_requested = False
        self.search_thread = None
        self.search_results = []
        self.search_summary = {}

        # Directory Mapper State
        self.is_mapping = False
        self.stop_map_requested = False
        self.map_thread = None
        self.map_result_text = ""
        self.map_stats = {}

        # Scan Results Cache
        self.current_target = None
        self.scanned_files = []
        self.scanned_folders = []
        self.extension_stats = defaultdict(lambda: {"count": 0, "size": 0})
        self.scan_summary = {}

        # Set Window Icon
        self.set_app_icon()

        # Build UI Components
        self.build_ui()

        # Keyboard Shortcut Bindings
        self.bind_shortcuts()

        # Window Close Protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # Periodic Queue Checker for Thread-safe UI updates
        self.root.after(100, self.process_queue)

        # Populate drive targets
        self.refresh_drives_list()

        # Handle initial target from CLI or context menu
        if initial_target:
            self.set_target_path(initial_target)
            self.log_message(f"Initialized target from launcher: {initial_target}", level="INFO")
        else:
            self.log_message("Stellar Snooper workstation ready for storage indexing.", level="INFO")

    # ==========================================================================
    # ☆ ASSET RESOLUTION & CONFIGURATION
    # ==========================================================================
    def set_app_icon(self):
        icon_candidates = [
            os.path.join(self.app_dir, "assets", "app_icon.ico"),
            os.path.join(self.base_dir, "assets", "app_icon.ico"),
        ]
        for icon_path in icon_candidates:
            if os.path.exists(icon_path):
                try:
                    self.root.iconbitmap(icon_path)
                    break
                except Exception:
                    pass

    def load_config(self):
        default_config = {
            "app_name": "Stellar Snooper",
            "version": "1.1.0",
            "preferences": {
                "default_drive": "C:",
                "top_files_limit": 20,
                "top_folders_limit": 10,
                "search_limit": 50,
                "search_default_extension": "ANY",
                "mapper_max_depth": 3,
                "mapper_ignore_hidden": True,
                "export_format": "json",
                "confirm_exit_on_scan": True
            }
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[!] Warning: Could not parse config.json: {e}")
        return default_config

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.log_message(f"Error saving configuration: {e}", level="ERROR")

    # ==========================================================================
    # ☆ GUI ARCHITECTURE
    # ==========================================================================
    def build_ui(self):
        self.setup_ttk_styles()

        # 1. Header Bar
        self.build_header()

        # 2. Main Container (Sidebar + Content Workspace)
        main_container = tk.Frame(self.root, bg=BG_MAIN)
        main_container.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        # Left Sidebar (Controls & Telemetry)
        self.build_sidebar(main_container)

        # Right Workspace (Notebook with Files, Folders, Analytics, Log)
        self.build_workspace(main_container)

        # 3. Bottom Status Bar
        self.build_statusbar()

    def setup_ttk_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Scrollbars
        style.configure(
            "Vertical.TScrollbar",
            background=BG_PANEL,
            troughcolor=BG_MAIN,
            bordercolor=BORDER_COLOR,
            arrowcolor=TEXT_MUTED
        )
        style.map("Vertical.TScrollbar", background=[("active", ACCENT_CYAN)])

        # Tabs (Notebook)
        style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=BG_PANEL,
            foreground=TEXT_MUTED,
            padding=[14, 6],
            font=FONT_UI_BOLD,
            borderwidth=0
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", BG_SURFACE)],
            foreground=[("selected", ACCENT_CYAN)]
        )

        # Combobox
        style.configure(
            "TCombobox",
            fieldbackground=BG_SURFACE,
            background=BG_PANEL,
            foreground=TEXT_PRIMARY,
            darkcolor=BORDER_COLOR,
            lightcolor=BORDER_COLOR,
            selectbackground=BG_ACTIVE,
            selectforeground=TEXT_PRIMARY
        )

        # Treeview (Data Tables)
        style.configure(
            "Treeview",
            background=BG_MAIN,
            foreground=TEXT_PRIMARY,
            fieldbackground=BG_MAIN,
            bordercolor=BORDER_COLOR,
            borderwidth=0,
            rowheight=26,
            font=FONT_CODE
        )
        style.configure(
            "Treeview.Heading",
            background=BG_PANEL,
            foreground=ACCENT_CYAN,
            relief="flat",
            font=FONT_UI_BOLD,
            padding=[6, 4]
        )
        style.map("Treeview", background=[("selected", BG_ACTIVE)], foreground=[("selected", ACCENT_GOLD)])
        style.map("Treeview.Heading", background=[("active", BG_SURFACE)], foreground=[("active", ACCENT_GOLD)])

    def build_header(self):
        header_frame = tk.Frame(self.root, bg=BG_PANEL, height=58, highlightthickness=1, highlightbackground=BORDER_COLOR)
        header_frame.pack(fill="x", padx=12, pady=(10, 8))
        header_frame.pack_propagate(False)

        # Left: Branding
        brand_frame = tk.Frame(header_frame, bg=BG_PANEL)
        brand_frame.pack(side="left", padx=14, pady=6)

        title_lbl = tk.Label(
            brand_frame,
            text="⭐ STELLAR SNOOPER",
            font=FONT_HEADER,
            fg=TEXT_PRIMARY,
            bg=BG_PANEL
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = tk.Label(
            brand_frame,
            text="High-Speed Storage Telemetry & Disk Space Workstation • Built for Windows",
            font=FONT_SUBHEADER,
            fg=TEXT_MUTED,
            bg=BG_PANEL
        )
        subtitle_lbl.pack(anchor="w")

        # Right: Status Pill & Primary Scan Button
        actions_frame = tk.Frame(header_frame, bg=BG_PANEL)
        actions_frame.pack(side="right", padx=14, pady=8)

        self.status_pill = tk.Label(
            actions_frame,
            text="● SYSTEM READY",
            font=FONT_UI_BOLD,
            fg=ACCENT_MINT,
            bg=BG_SURFACE,
            padx=10,
            pady=4,
            relief="flat"
        )
        self.status_pill.pack(side="right", padx=(8, 0))

        self.btn_scan = tk.Button(
            actions_frame,
            text="⚡ Start Scan",
            font=FONT_UI_BOLD,
            fg=BG_MAIN,
            bg=ACCENT_CYAN,
            activebackground="#79c0ff",
            activeforeground=BG_MAIN,
            relief="flat",
            padx=14,
            pady=4,
            cursor="hand2",
            command=self.toggle_scan
        )
        self.btn_scan.pack(side="right", padx=4)

    def build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=BG_PANEL, width=285, highlightthickness=1, highlightbackground=BORDER_COLOR)
        sidebar.pack(side="left", fill="y", padx=(0, 8))
        sidebar.pack_propagate(False)

        # 1. Target Selector Section
        lbl_target_sec = tk.Label(sidebar, text="SCAN TARGET", font=FONT_UI_BOLD, fg=ACCENT_GOLD, bg=BG_PANEL)
        lbl_target_sec.pack(anchor="w", padx=14, pady=(12, 4))

        drive_select_frame = tk.Frame(sidebar, bg=BG_PANEL)
        drive_select_frame.pack(fill="x", padx=12, pady=2)

        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(drive_select_frame, textvariable=self.drive_var, state="readonly", font=FONT_UI)
        self.drive_combo.pack(fill="x", pady=2)
        self.drive_combo.bind("<<ComboboxSelected>>", self.on_drive_selected)

        # Custom Folder button
        btn_browse = tk.Button(
            sidebar,
            text="📁  Browse Custom Folder...",
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            activebackground=BG_ACTIVE,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            anchor="w",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.on_browse_folder
        )
        btn_browse.pack(fill="x", padx=12, pady=4)

        # Target Display Card
        self.lbl_active_target = tk.Label(
            sidebar,
            text="Target: None",
            font=FONT_STATS,
            fg=ACCENT_CYAN,
            bg=BG_SURFACE,
            padx=8,
            pady=5,
            anchor="w",
            wraplength=250,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        self.lbl_active_target.pack(fill="x", padx=12, pady=(2, 8))

        # 2. Storage Usage Gauge
        lbl_gauge = tk.Label(sidebar, text="DRIVE CAPACITY", font=FONT_UI_BOLD, fg=ACCENT_GOLD, bg=BG_PANEL)
        lbl_gauge.pack(anchor="w", padx=14, pady=(8, 4))

        gauge_card = tk.Frame(sidebar, bg=BG_SURFACE, highlightthickness=1, highlightbackground=BORDER_COLOR)
        gauge_card.pack(fill="x", padx=12, pady=2)

        self.lbl_disk_text = tk.Label(
            gauge_card,
            text="Used: -- GB / -- GB",
            font=FONT_STATS,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            anchor="w"
        )
        self.lbl_disk_text.pack(anchor="w", padx=10, pady=(8, 2))

        # Canvas-drawn cosmic meter bar
        self.gauge_canvas = tk.Canvas(gauge_card, height=14, bg=BG_MAIN, highlightthickness=0)
        self.gauge_canvas.pack(fill="x", padx=10, pady=4)

        self.lbl_free_space = tk.Label(
            gauge_card,
            text="Free: -- GB (--% free)",
            font=FONT_STATS,
            fg=TEXT_MUTED,
            bg=BG_SURFACE,
            anchor="w"
        )
        self.lbl_free_space.pack(anchor="w", padx=10, pady=(0, 8))

        # 3. Live Telemetry Card
        lbl_telemetry = tk.Label(sidebar, text="LIVE SCAN TELEMETRY", font=FONT_UI_BOLD, fg=ACCENT_GOLD, bg=BG_PANEL)
        lbl_telemetry.pack(anchor="w", padx=14, pady=(10, 4))

        self.telemetry_card = tk.Frame(sidebar, bg=BG_SURFACE, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.telemetry_card.pack(fill="x", padx=12, pady=2)

        self.lbl_stat_files = tk.Label(
            self.telemetry_card,
            text="Files Indexed: 0",
            font=FONT_UI_BOLD,
            fg=ACCENT_CYAN,
            bg=BG_SURFACE,
            anchor="w"
        )
        self.lbl_stat_files.pack(anchor="w", padx=10, pady=(8, 2))

        self.lbl_stat_speed = tk.Label(
            self.telemetry_card,
            text="Scan Speed: 0 files/s",
            font=FONT_STATS,
            fg=ACCENT_MINT,
            bg=BG_SURFACE,
            anchor="w"
        )
        self.lbl_stat_speed.pack(anchor="w", padx=10, pady=1)

        self.lbl_stat_time = tk.Label(
            self.telemetry_card,
            text="Elapsed Time: 00:00.0",
            font=FONT_STATS,
            fg=TEXT_MUTED,
            bg=BG_SURFACE,
            anchor="w"
        )
        self.lbl_stat_time.pack(anchor="w", padx=10, pady=1)

        self.lbl_current_folder = tk.Label(
            self.telemetry_card,
            text="Idle",
            font=FONT_STATS,
            fg=TEXT_DIM,
            bg=BG_SURFACE,
            anchor="w",
            wraplength=240,
            justify="left"
        )
        self.lbl_current_folder.pack(anchor="w", padx=10, pady=(2, 8))

        # 4. Action Buttons
        lbl_actions = tk.Label(sidebar, text="CONTROLS & EXPORTS", font=FONT_UI_BOLD, fg=ACCENT_GOLD, bg=BG_PANEL)
        lbl_actions.pack(anchor="w", padx=14, pady=(10, 4))

        btn_export = tk.Button(
            sidebar,
            text="💾  Export Report (Ctrl+S)",
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            activebackground=BG_ACTIVE,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            anchor="w",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.on_export_report
        )
        btn_export.pack(fill="x", padx=12, pady=2)

        btn_clear = tk.Button(
            sidebar,
            text="🧹  Clear Scan Results",
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            activebackground=BG_ACTIVE,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            anchor="w",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.clear_results
        )
        btn_clear.pack(fill="x", padx=12, pady=2)

    def build_workspace(self, parent):
        workspace_frame = tk.Frame(parent, bg=BG_MAIN)
        workspace_frame.pack(side="right", fill="both", expand=True)

        self.notebook = ttk.Notebook(workspace_frame)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Top Largest Files
        tab_files = tk.Frame(self.notebook, bg=BG_PANEL)
        self.notebook.add(tab_files, text="  📄 Largest Files  ")
        self.build_files_tab(tab_files)

        # Tab 2: Top Largest Folders
        tab_folders = tk.Frame(self.notebook, bg=BG_PANEL)
        self.notebook.add(tab_folders, text="  📁 Largest Folders  ")
        self.build_folders_tab(tab_folders)

        # Tab 3: Analytics & Types
        tab_analytics = tk.Frame(self.notebook, bg=BG_PANEL)
        self.notebook.add(tab_analytics, text="  📊 Storage Analytics  ")
        self.build_analytics_tab(tab_analytics)

        # Tab 4: File Searcher
        tab_search = tk.Frame(self.notebook, bg=BG_PANEL)
        self.notebook.add(tab_search, text="  🔍 File Searcher  ")
        self.build_search_tab(tab_search)

        # Tab 5: Directory Mapper
        tab_mapper = tk.Frame(self.notebook, bg=BG_PANEL)
        self.notebook.add(tab_mapper, text="  🗺️ Directory Mapper  ")
        self.build_mapper_tab(tab_mapper)

        # Tab 6: Activity Log & Terminal Console
        tab_log = tk.Frame(self.notebook, bg=BG_PANEL)
        self.notebook.add(tab_log, text="  📜 Activity Log  ")
        self.build_log_tab(tab_log)

    def build_files_tab(self, parent):
        box = tk.Frame(parent, bg=BG_MAIN, highlightthickness=1, highlightbackground=BORDER_COLOR)
        box.pack(fill="both", expand=True, padx=8, pady=8)

        cols = ("rank", "name", "type", "size", "dir")
        self.tree_files = ttk.Treeview(box, columns=cols, show="headings", selectmode="browse")
        self.tree_files.heading("rank", text="#", anchor="center")
        self.tree_files.heading("name", text="File Name", anchor="w")
        self.tree_files.heading("type", text="Type", anchor="center")
        self.tree_files.heading("size", text="Size", anchor="e")
        self.tree_files.heading("dir", text="Directory Path", anchor="w")

        self.tree_files.column("rank", width=42, stretch=False, anchor="center")
        self.tree_files.column("name", width=220, anchor="w")
        self.tree_files.column("type", width=70, stretch=False, anchor="center")
        self.tree_files.column("size", width=110, stretch=False, anchor="e")
        self.tree_files.column("dir", width=420, anchor="w")

        scroll_y = ttk.Scrollbar(box, orient="vertical", command=self.tree_files.yview)
        scroll_x = ttk.Scrollbar(box, orient="horizontal", command=self.tree_files.xview)
        self.tree_files.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree_files.pack(fill="both", expand=True)

        # Double click & Context menu
        self.tree_files.bind("<Double-1>", self.on_file_double_click)
        self.menu_files = tk.Menu(self.root, tearoff=0, bg=BG_SURFACE, fg=TEXT_PRIMARY, activebackground=BG_ACTIVE)
        self.menu_files.add_command(label="Open in Windows Explorer", command=self.reveal_selected_file)
        self.menu_files.add_command(label="Open File", command=self.open_selected_file)
        self.menu_files.add_command(label="Copy File Path", command=self.copy_selected_file_path)
        self.tree_files.bind("<Button-3>", self.show_files_context_menu)

    def build_folders_tab(self, parent):
        box = tk.Frame(parent, bg=BG_MAIN, highlightthickness=1, highlightbackground=BORDER_COLOR)
        box.pack(fill="both", expand=True, padx=8, pady=8)

        cols = ("rank", "path", "size")
        self.tree_folders = ttk.Treeview(box, columns=cols, show="headings", selectmode="browse")
        self.tree_folders.heading("rank", text="#", anchor="center")
        self.tree_folders.heading("path", text="Folder Path", anchor="w")
        self.tree_folders.heading("size", text="Calculated Total Size", anchor="e")

        self.tree_folders.column("rank", width=42, stretch=False, anchor="center")
        self.tree_folders.column("path", width=550, anchor="w")
        self.tree_folders.column("size", width=160, stretch=False, anchor="e")

        scroll_y = ttk.Scrollbar(box, orient="vertical", command=self.tree_folders.yview)
        scroll_x = ttk.Scrollbar(box, orient="horizontal", command=self.tree_folders.xview)
        self.tree_folders.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree_folders.pack(fill="both", expand=True)

        self.tree_folders.bind("<Double-1>", self.on_folder_double_click)
        self.menu_folders = tk.Menu(self.root, tearoff=0, bg=BG_SURFACE, fg=TEXT_PRIMARY, activebackground=BG_ACTIVE)
        self.menu_folders.add_command(label="Open Folder in Windows Explorer", command=self.reveal_selected_folder)
        self.menu_folders.add_command(label="Copy Folder Path", command=self.copy_selected_folder_path)
        self.menu_folders.add_command(label="Set as Active Scan Target", command=self.set_selected_folder_as_target)
        self.tree_folders.bind("<Button-3>", self.show_folders_context_menu)

    def build_analytics_tab(self, parent):
        box = tk.Frame(parent, bg=BG_MAIN, highlightthickness=1, highlightbackground=BORDER_COLOR)
        box.pack(fill="both", expand=True, padx=8, pady=8)

        # Overview Metrics Top Frame
        metrics_frame = tk.Frame(box, bg=BG_PANEL, highlightthickness=1, highlightbackground=BORDER_COLOR)
        metrics_frame.pack(fill="x", padx=10, pady=10)

        self.lbl_analytics_summary = tk.Label(
            metrics_frame,
            text="Run a scan to generate storage telemetry and extension distributions.",
            font=FONT_UI_BOLD,
            fg=ACCENT_CYAN,
            bg=BG_PANEL,
            padx=14,
            pady=10,
            justify="left"
        )
        self.lbl_analytics_summary.pack(anchor="w")

        # Extension Breakdown Table
        lbl_ext_title = tk.Label(box, text="TOP FILE EXTENSIONS BY STORAGE CONSUMPTION", font=FONT_UI_BOLD, fg=ACCENT_GOLD, bg=BG_MAIN)
        lbl_ext_title.pack(anchor="w", padx=12, pady=(10, 4))

        ext_box = tk.Frame(box, bg=BG_MAIN)
        ext_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols = ("ext", "count", "size", "pct")
        self.tree_ext = ttk.Treeview(ext_box, columns=cols, show="headings", selectmode="browse")
        self.tree_ext.heading("ext", text="Extension", anchor="w")
        self.tree_ext.heading("count", text="File Count", anchor="e")
        self.tree_ext.heading("size", text="Total Space Consumed", anchor="e")
        self.tree_ext.heading("pct", text="Share of Target", anchor="e")

        self.tree_ext.column("ext", width=120, anchor="w")
        self.tree_ext.column("count", width=120, anchor="e")
        self.tree_ext.column("size", width=180, anchor="e")
        self.tree_ext.column("pct", width=120, anchor="e")

        scroll_ext = ttk.Scrollbar(ext_box, orient="vertical", command=self.tree_ext.yview)
        self.tree_ext.configure(yscrollcommand=scroll_ext.set)
        scroll_ext.pack(side="right", fill="y")
        self.tree_ext.pack(fill="both", expand=True)

    def build_search_tab(self, parent):
        box = tk.Frame(parent, bg=BG_MAIN)
        box.pack(fill="both", expand=True, padx=8, pady=8)

        # 1. Search Control Card (Top Bar)
        ctrl_card = tk.Frame(box, bg=BG_PANEL, highlightthickness=1, highlightbackground=BORDER_COLOR)
        ctrl_card.pack(fill="x", pady=(0, 6), padx=2)

        # Row 0: Target Location
        row0 = tk.Frame(ctrl_card, bg=BG_PANEL)
        row0.pack(fill="x", padx=10, pady=(8, 4))

        lbl_loc = tk.Label(row0, text="Search Path:", font=FONT_UI_BOLD, fg=ACCENT_GOLD, bg=BG_PANEL, width=12, anchor="w")
        lbl_loc.pack(side="left")

        self.search_path_var = tk.StringVar(value=self.current_target or "C:\\")
        entry_search_path = tk.Entry(
            row0,
            textvariable=self.search_path_var,
            font=FONT_CODE,
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            insertbackground=ACCENT_CYAN,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        entry_search_path.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_browse_search = tk.Button(
            row0,
            text="📁 Browse...",
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            activebackground=BG_ACTIVE,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            padx=10,
            pady=2,
            cursor="hand2",
            command=self.on_browse_search_path
        )
        btn_browse_search.pack(side="left", padx=2)

        btn_sync_search = tk.Button(
            row0,
            text="🔄 Active Target",
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            activebackground=BG_ACTIVE,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2",
            command=self.sync_search_with_active_target
        )
        btn_sync_search.pack(side="left", padx=2)

        # Row 1: Query, Extension, Limit, Search Button
        row1 = tk.Frame(ctrl_card, bg=BG_PANEL)
        row1.pack(fill="x", padx=10, pady=(4, 10))

        lbl_query = tk.Label(row1, text="Query / Name:", font=FONT_UI_BOLD, fg=TEXT_PRIMARY, bg=BG_PANEL, width=12, anchor="w")
        lbl_query.pack(side="left")

        self.search_query_var = tk.StringVar()
        entry_query = tk.Entry(
            row1,
            textvariable=self.search_query_var,
            font=FONT_UI,
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            insertbackground=ACCENT_CYAN,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        entry_query.pack(side="left", fill="x", expand=True, padx=(0, 4))
        entry_query.bind("<Return>", lambda e: self.toggle_search())

        btn_clear_query = tk.Button(
            row1,
            text="✕",
            font=FONT_UI_BOLD,
            fg=TEXT_MUTED,
            bg=BG_SURFACE,
            activebackground=BG_ACTIVE,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            padx=6,
            pady=2,
            cursor="hand2",
            command=lambda: self.search_query_var.set("")
        )
        btn_clear_query.pack(side="left", padx=(0, 10))

        lbl_ext = tk.Label(row1, text="Ext:", font=FONT_UI_BOLD, fg=TEXT_PRIMARY, bg=BG_PANEL)
        lbl_ext.pack(side="left", padx=(4, 4))

        self.search_ext_var = tk.StringVar(value=self.config.get("preferences", {}).get("search_default_extension", "ANY"))
        combo_ext = ttk.Combobox(
            row1,
            textvariable=self.search_ext_var,
            values=["ANY", "txt", "pdf", "docx", "py", "exe", "zip", "png", "jpg", "mp4", "iso"],
            width=7,
            font=FONT_UI
        )
        combo_ext.pack(side="left", padx=(0, 10))

        lbl_limit = tk.Label(row1, text="Limit:", font=FONT_UI_BOLD, fg=TEXT_PRIMARY, bg=BG_PANEL)
        lbl_limit.pack(side="left", padx=(4, 4))

        self.search_limit_var = tk.StringVar(value=str(self.config.get("preferences", {}).get("search_limit", 50)))
        combo_limit = ttk.Combobox(
            row1,
            textvariable=self.search_limit_var,
            values=["25", "50", "100", "250", "500", "ALL"],
            width=6,
            state="readonly",
            font=FONT_UI
        )
        combo_limit.pack(side="left", padx=(0, 12))

        self.btn_search = tk.Button(
            row1,
            text="🔍 Search Files",
            font=FONT_UI_BOLD,
            fg=BG_MAIN,
            bg=ACCENT_CYAN,
            activebackground="#79c0ff",
            activeforeground=BG_MAIN,
            relief="flat",
            padx=14,
            pady=3,
            cursor="hand2",
            command=self.toggle_search
        )
        self.btn_search.pack(side="left")

        # 2. Live Telemetry Strip
        telemetry_frame = tk.Frame(box, bg=BG_SURFACE, highlightthickness=1, highlightbackground=BORDER_COLOR)
        telemetry_frame.pack(fill="x", pady=(0, 6), padx=2)

        self.lbl_search_status = tk.Label(
            telemetry_frame,
            text="Ready to search • Enter a search query or filter by file extension.",
            font=FONT_UI,
            fg=ACCENT_CYAN,
            bg=BG_SURFACE,
            padx=10,
            pady=4
        )
        self.lbl_search_status.pack(side="left")

        self.lbl_search_metrics = tk.Label(
            telemetry_frame,
            text="Folders: 0 | Matches: 0 | Time: 00:00.0",
            font=FONT_STATS,
            fg=TEXT_MUTED,
            bg=BG_SURFACE,
            padx=10,
            pady=4
        )
        self.lbl_search_metrics.pack(side="right")

        # 3. Search Results Table
        table_box = tk.Frame(box, bg=BG_MAIN, highlightthickness=1, highlightbackground=BORDER_COLOR)
        table_box.pack(fill="both", expand=True, padx=2, pady=(0, 6))

        cols = ("rank", "relevance", "name", "ext", "size", "dir")
        self.tree_search = ttk.Treeview(table_box, columns=cols, show="headings", selectmode="browse")
        self.tree_search.heading("rank", text="#", anchor="center", command=lambda: self.sort_tree(self.tree_search, "rank", False, is_num=True))
        self.tree_search.heading("relevance", text="Relevance", anchor="center", command=lambda: self.sort_tree(self.tree_search, "relevance", True, is_pct=True))
        self.tree_search.heading("name", text="File Name", anchor="w", command=lambda: self.sort_tree(self.tree_search, "name", False))
        self.tree_search.heading("ext", text="Type", anchor="center", command=lambda: self.sort_tree(self.tree_search, "ext", False))
        self.tree_search.heading("size", text="Size", anchor="e", command=lambda: self.sort_tree(self.tree_search, "size", True, is_size=True))
        self.tree_search.heading("dir", text="Directory Path", anchor="w", command=lambda: self.sort_tree(self.tree_search, "dir", False))

        self.tree_search.column("rank", width=42, stretch=False, anchor="center")
        self.tree_search.column("relevance", width=85, stretch=False, anchor="center")
        self.tree_search.column("name", width=230, anchor="w")
        self.tree_search.column("ext", width=70, stretch=False, anchor="center")
        self.tree_search.column("size", width=110, stretch=False, anchor="e")
        self.tree_search.column("dir", width=420, anchor="w")

        scroll_y = ttk.Scrollbar(table_box, orient="vertical", command=self.tree_search.yview)
        scroll_x = ttk.Scrollbar(table_box, orient="horizontal", command=self.tree_search.xview)
        self.tree_search.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree_search.pack(fill="both", expand=True)

        # Double click & Context Menu
        self.tree_search.bind("<Double-1>", self.on_search_file_double_click)
        self.menu_search = tk.Menu(self.root, tearoff=0, bg=BG_SURFACE, fg=TEXT_PRIMARY, activebackground=BG_ACTIVE)
        self.menu_search.add_command(label="Open in Windows Explorer", command=self.reveal_selected_search_file)
        self.menu_search.add_command(label="Open File", command=self.open_selected_search_file)
        self.menu_search.add_command(label="Copy Full Path", command=self.copy_selected_search_file_path)
        self.menu_search.add_command(label="Copy Directory Path", command=self.copy_selected_search_dir_path)
        self.tree_search.bind("<Button-3>", self.show_search_context_menu)

        # 4. Bottom Action Bar
        action_bar = tk.Frame(box, bg=BG_MAIN)
        action_bar.pack(fill="x", padx=2, pady=2)

        btn_export = tk.Button(
            action_bar,
            text="💾  Export Search Results...",
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            activebackground=BG_ACTIVE,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.on_export_search_results
        )
        btn_export.pack(side="left", padx=(0, 6))

        btn_copy = tk.Button(
            action_bar,
            text="📋  Copy Path",
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            activebackground=BG_ACTIVE,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.copy_selected_search_file_path
        )
        btn_copy.pack(side="left", padx=2)

        btn_clear = tk.Button(
            action_bar,
            text="🧹  Clear Search",
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            activebackground=BG_ACTIVE,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.clear_search_results
        )
        btn_clear.pack(side="left", padx=2)

        self.lbl_search_summary_count = tk.Label(
            action_bar,
            text="0 matches listed",
            font=FONT_STATS,
            fg=TEXT_MUTED,
            bg=BG_MAIN
        )
        self.lbl_search_summary_count.pack(side="right", padx=6)

    def build_mapper_tab(self, parent):
        box = tk.Frame(parent, bg=BG_MAIN)
        box.pack(fill="both", expand=True, padx=8, pady=8)

        # 1. Controls Top Bar
        ctrl_card = tk.Frame(box, bg=BG_PANEL, highlightthickness=1, highlightbackground=BORDER_COLOR)
        ctrl_card.pack(fill="x", pady=(0, 6), padx=2)

        # Row 0: Target Path
        row0 = tk.Frame(ctrl_card, bg=BG_PANEL)
        row0.pack(fill="x", padx=10, pady=(8, 4))

        lbl_loc = tk.Label(row0, text="Map Target:", font=FONT_UI_BOLD, fg=ACCENT_GOLD, bg=BG_PANEL, width=12, anchor="w")
        lbl_loc.pack(side="left")

        self.mapper_path_var = tk.StringVar(value=self.current_target or "C:\\")
        entry_map_path = tk.Entry(
            row0,
            textvariable=self.mapper_path_var,
            font=FONT_CODE,
            bg=BG_SURFACE,
            fg=TEXT_PRIMARY,
            insertbackground=ACCENT_CYAN,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        entry_map_path.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_browse_map = tk.Button(
            row0,
            text="📁 Browse...",
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            activebackground=BG_ACTIVE,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            padx=10,
            pady=2,
            cursor="hand2",
            command=self.on_browse_mapper_path
        )
        btn_browse_map.pack(side="left", padx=2)

        btn_sync_map = tk.Button(
            row0,
            text="🔄 Active Target",
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            activebackground=BG_ACTIVE,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2",
            command=self.sync_mapper_with_active_target
        )
        btn_sync_map.pack(side="left", padx=2)

        # Row 1: Options & Generate Button
        row1 = tk.Frame(ctrl_card, bg=BG_PANEL)
        row1.pack(fill="x", padx=10, pady=(4, 10))

        lbl_depth = tk.Label(row1, text="Max Depth:", font=FONT_UI_BOLD, fg=TEXT_PRIMARY, bg=BG_PANEL, width=12, anchor="w")
        lbl_depth.pack(side="left")

        default_depth = self.config.get("preferences", {}).get("mapper_max_depth", 3)
        depth_str = f"{default_depth} Levels" if default_depth else "Full (Unlimited)"
        self.mapper_depth_var = tk.StringVar(value=depth_str)
        combo_depth = ttk.Combobox(
            row1,
            textvariable=self.mapper_depth_var,
            values=["Full (Unlimited)", "1 Level", "2 Levels", "3 Levels", "4 Levels", "5 Levels", "6 Levels"],
            width=16,
            state="readonly",
            font=FONT_UI
        )
        combo_depth.pack(side="left", padx=(0, 14))

        self.mapper_ignore_hidden_var = tk.IntVar(value=1 if self.config.get("preferences", {}).get("mapper_ignore_hidden", True) else 0)
        chk_hidden = tk.Checkbutton(
            row1,
            text="Exclude Hidden (.dotfiles)",
            variable=self.mapper_ignore_hidden_var,
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_PANEL,
            activebackground=BG_PANEL,
            activeforeground=ACCENT_CYAN,
            selectcolor=BG_SURFACE
        )
        chk_hidden.pack(side="left", padx=(0, 10))

        self.mapper_folders_only_var = tk.IntVar(value=0)
        chk_folders = tk.Checkbutton(
            row1,
            text="Directories Only",
            variable=self.mapper_folders_only_var,
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_PANEL,
            activebackground=BG_PANEL,
            activeforeground=ACCENT_CYAN,
            selectcolor=BG_SURFACE
        )
        chk_folders.pack(side="left", padx=(0, 14))

        self.btn_map = tk.Button(
            row1,
            text="🗺️ Generate Tree Map",
            font=FONT_UI_BOLD,
            fg=BG_MAIN,
            bg=ACCENT_CYAN,
            activebackground="#79c0ff",
            activeforeground=BG_MAIN,
            relief="flat",
            padx=14,
            pady=3,
            cursor="hand2",
            command=self.toggle_map
        )
        self.btn_map.pack(side="left")

        # 2. Status Strip
        status_frame = tk.Frame(box, bg=BG_SURFACE, highlightthickness=1, highlightbackground=BORDER_COLOR)
        status_frame.pack(fill="x", pady=(0, 6), padx=2)

        self.lbl_map_status = tk.Label(
            status_frame,
            text="Ready • Select a directory and click Generate Tree Map.",
            font=FONT_UI,
            fg=ACCENT_CYAN,
            bg=BG_SURFACE,
            padx=10,
            pady=4
        )
        self.lbl_map_status.pack(side="left")

        self.lbl_map_metrics = tk.Label(
            status_frame,
            text="Items Mapped: 0",
            font=FONT_STATS,
            fg=TEXT_MUTED,
            bg=BG_SURFACE,
            padx=10,
            pady=4
        )
        self.lbl_map_metrics.pack(side="right")

        # 3. Monospace ASCII Tree Text Display
        text_box = tk.Frame(box, bg=BG_MAIN, highlightthickness=1, highlightbackground=BORDER_COLOR)
        text_box.pack(fill="both", expand=True, padx=2, pady=(0, 6))

        self.map_text = tk.Text(
            text_box,
            font=FONT_CODE,
            bg=BG_MAIN,
            fg=TEXT_PRIMARY,
            relief="flat",
            wrap="none",
            padx=10,
            pady=10
        )
        scroll_y = ttk.Scrollbar(text_box, orient="vertical", command=self.map_text.yview)
        scroll_x = ttk.Scrollbar(text_box, orient="horizontal", command=self.map_text.xview)
        self.map_text.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.map_text.pack(side="left", fill="both", expand=True)

        self.map_text.tag_config("HEADER", foreground=ACCENT_CYAN, font=("Consolas", 10, "bold"))
        self.map_text.tag_config("FOLDER", foreground=ACCENT_GOLD, font=("Consolas", 10, "bold"))
        self.map_text.tag_config("FILE", foreground=TEXT_PRIMARY)
        self.map_text.tag_config("CONNECTOR", foreground=ACCENT_PURPLE)
        self.map_text.tag_config("DENIED", foreground=ACCENT_CORAL)

        # 4. Bottom Actions Bar
        action_bar = tk.Frame(box, bg=BG_MAIN)
        action_bar.pack(fill="x", padx=2, pady=2)

        btn_copy = tk.Button(
            action_bar,
            text="📋  Copy Tree to Clipboard",
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            activebackground=BG_ACTIVE,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.copy_map_to_clipboard
        )
        btn_copy.pack(side="left", padx=(0, 6))

        btn_export = tk.Button(
            action_bar,
            text="💾  Export Tree Map (.txt)...",
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            activebackground=BG_ACTIVE,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.on_export_map_tree
        )
        btn_export.pack(side="left", padx=2)

        btn_clear = tk.Button(
            action_bar,
            text="🧹  Clear Map",
            font=FONT_UI,
            fg=TEXT_PRIMARY,
            bg=BG_SURFACE,
            activebackground=BG_ACTIVE,
            activeforeground=TEXT_PRIMARY,
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.clear_map_tree
        )
        btn_clear.pack(side="left", padx=2)

        self.lbl_map_stats_summary = tk.Label(
            action_bar,
            text="Ready",
            font=FONT_STATS,
            fg=TEXT_MUTED,
            bg=BG_MAIN
        )
        self.lbl_map_stats_summary.pack(side="right", padx=6)

    def build_log_tab(self, parent):
        box = tk.Frame(parent, bg=BG_MAIN, highlightthickness=1, highlightbackground=BORDER_COLOR)
        box.pack(fill="both", expand=True, padx=8, pady=8)

        self.log_text = tk.Text(
            box,
            font=FONT_CODE,
            bg=BG_MAIN,
            fg=TEXT_MUTED,
            relief="flat",
            wrap="none",
            padx=10,
            pady=10
        )
        scroll_y = ttk.Scrollbar(box, orient="vertical", command=self.log_text.yview)
        scroll_x = ttk.Scrollbar(box, orient="horizontal", command=self.log_text.xview)
        self.log_text.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.log_text.pack(side="left", fill="both", expand=True)

        self.log_text.tag_config("INFO", foreground=ACCENT_CYAN)
        self.log_text.tag_config("SUCCESS", foreground=ACCENT_MINT)
        self.log_text.tag_config("WARNING", foreground=ACCENT_GOLD)
        self.log_text.tag_config("ERROR", foreground=ACCENT_CORAL)
        self.log_text.tag_config("TABLE", foreground=TEXT_PRIMARY)

    def build_statusbar(self):
        status_bar = tk.Frame(self.root, bg=BG_PANEL, height=26, highlightthickness=1, highlightbackground=BORDER_COLOR)
        status_bar.pack(fill="x", side="bottom")

        self.status_lbl = tk.Label(status_bar, text="Ready", font=FONT_STATS, fg=TEXT_MUTED, bg=BG_PANEL)
        self.status_lbl.pack(side="left", padx=14)

        version_lbl = tk.Label(
            status_bar,
            text=f"Version {self.config.get('version', '1.0.0')} • Cassiopeia Studios",
            font=FONT_STATS,
            fg=TEXT_DIM,
            bg=BG_PANEL
        )
        version_lbl.pack(side="right", padx=14)

        self.stats_lbl = tk.Label(status_bar, text="Files: 0 | Folders: 0", font=FONT_STATS, fg=TEXT_MUTED, bg=BG_PANEL)
        self.stats_lbl.pack(side="right", padx=14)

    # ==========================================================================
    # ☆ EVENT HANDLERS & TARGET SELECTION
    # ==========================================================================
    def bind_shortcuts(self):
        self.root.bind("<Control-r>", lambda e: self.toggle_scan())
        self.root.bind("<F5>", lambda e: self.toggle_scan())
        self.root.bind("<Escape>", lambda e: self.cancel_scan())
        self.root.bind("<Control-s>", lambda e: self.on_export_report())
        self.root.bind("<Control-o>", lambda e: self.on_browse_folder())
        self.root.bind("<Control-q>", lambda e: self.on_window_close())

    def refresh_drives_list(self):
        drives = get_available_drives()
        display_values = []
        default_index = 0

        for i, d in enumerate(drives):
            total_gb = d["total"] / (1024**3)
            free_gb = d["free"] / (1024**3)
            pct_free = (d["free"] / d["total"] * 100) if d["total"] > 0 else 0
            val = f"{d['letter']} [{d['label']}] ({total_gb:.0f} GB, {pct_free:.0f}% free)"
            display_values.append(val)
            if d['letter'].upper() == self.config.get("preferences", {}).get("default_drive", "C:").upper():
                default_index = i

        self.drive_combo["values"] = display_values
        if display_values:
            self.drive_combo.current(default_index)
            selected_letter = drives[default_index]["root"]
            self.set_target_path(selected_letter)

    def on_drive_selected(self, event=None):
        val = self.drive_var.get()
        if val:
            drive_letter = val.split()[0].rstrip(":") + ":\\"
            self.set_target_path(drive_letter)

    def on_browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Analyze", initialdir=self.current_target or "C:\\")
        if folder:
            self.set_target_path(os.path.normpath(folder) + os.sep)

    def set_target_path(self, path):
        normalized = os.path.normpath(path)
        if os.path.isdir(normalized) and not normalized.endswith(os.sep):
            normalized += os.sep
        self.current_target = normalized
        self.lbl_active_target.config(text=f"Target: {normalized}")
        self.update_drive_gauge(normalized)

        # Sync search and mapper paths if not manually set to another location
        if hasattr(self, "search_path_var"):
            curr_sp = self.search_path_var.get()
            if not curr_sp or curr_sp == "None" or not os.path.exists(curr_sp):
                self.search_path_var.set(normalized)
        if hasattr(self, "mapper_path_var"):
            curr_mp = self.mapper_path_var.get()
            if not curr_mp or curr_mp == "None" or not os.path.exists(curr_mp):
                self.mapper_path_var.set(normalized)

    def update_drive_gauge(self, path):
        try:
            total, used, free = shutil.disk_usage(path)
            pct = (used / total * 100) if total > 0 else 0
            self.lbl_disk_text.config(text=f"Used: {format_bytes(used)} / {format_bytes(total)} ({pct:.1f}%)")
            self.lbl_free_space.config(text=f"Free: {format_bytes(free)} ({100 - pct:.1f}% free)")

            self.gauge_canvas.delete("all")
            w = self.gauge_canvas.winfo_width()
            if w <= 1:
                w = 240
            h = 14
            fill_w = int((pct / 100) * w)

            # Choose bar color
            bar_color = ACCENT_MINT if pct < 70 else (ACCENT_GOLD if pct < 90 else ACCENT_CORAL)
            self.gauge_canvas.create_rectangle(0, 0, w, h, fill=BG_MAIN, outline=BORDER_COLOR)
            self.gauge_canvas.create_rectangle(0, 0, fill_w, h, fill=bar_color, outline="")
        except Exception:
            self.lbl_disk_text.config(text="Used: Unknown")
            self.lbl_free_space.config(text="Free: Unknown")

    def set_status_pill(self, text, color):
        self.status_pill.config(text=text, fg=color)

    def log_message(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] ", "DIM")
        self.log_text.insert("end", f"[{level:<7}] ", level)
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")

    # ==========================================================================
    # ☆ THREAD-SAFE SCANNING ENGINE
    # ==========================================================================
    def toggle_scan(self):
        if self.is_scanning:
            self.cancel_scan()
        else:
            self.start_scan()

    def cancel_scan(self):
        if self.is_scanning:
            self.stop_requested = True
            self.btn_scan.config(text="Stopping...", state="disabled")
            self.set_status_pill("● ABORTING...", ACCENT_CORAL)
            self.log_message("Abort requested by user. Terminating worker...", level="WARNING")

    def start_scan(self):
        if not self.current_target or not os.path.exists(self.current_target):
            messagebox.showerror("Invalid Target", f"Target directory not found:\n{self.current_target}")
            return

        self.is_scanning = True
        self.stop_requested = False
        self.btn_scan.config(text="⏹ Stop Scan", bg=ACCENT_CORAL, activebackground="#ff7b72", state="normal")
        self.set_status_pill("● SCANNING...", ACCENT_CYAN)
        self.status_lbl.config(text=f"Scanning {self.current_target}...")
        self.log_message(f"Starting storage analysis on: {self.current_target}", level="INFO")

        # Clear previous tables
        for row in self.tree_files.get_children():
            self.tree_files.delete(row)
        for row in self.tree_folders.get_children():
            self.tree_folders.delete(row)
        for row in self.tree_ext.get_children():
            self.tree_ext.delete(row)

        target = self.current_target
        file_limit = self.config.get("preferences", {}).get("top_files_limit", 20)
        folder_limit = self.config.get("preferences", {}).get("top_folders_limit", 10)

        def worker():
            file_list = []
            folder_sizes = defaultdict(int)
            ext_data = defaultdict(lambda: {"count": 0, "size": 0})
            start_time = time.time()
            total_scanned = 0
            last_progress_time = 0

            for root_dir, dirs, files in os.walk(target):
                if self.stop_requested:
                    break

                for name in files:
                    if self.stop_requested:
                        break

                    try:
                        filepath = os.path.join(root_dir, name)
                        file_size = os.path.getsize(filepath)

                        _, ext = os.path.splitext(name)
                        ext_lower = ext.lower() if ext else "[No Ext]"

                        file_list.append((name, ext_lower, root_dir, file_size))
                        ext_data[ext_lower]["count"] += 1
                        ext_data[ext_lower]["size"] += file_size

                        # Aggregate sizes upward
                        temp_path = root_dir
                        while True:
                            folder_sizes[temp_path] += file_size
                            parent = os.path.dirname(temp_path)
                            if parent == temp_path:
                                break
                            temp_path = parent

                        total_scanned += 1
                    except (OSError, PermissionError):
                        continue

                # Throttle UI progress messages to ~10Hz
                now = time.time()
                if now - last_progress_time >= 0.1:
                    last_progress_time = now
                    elapsed = max(now - start_time, 0.001)
                    speed = total_scanned / elapsed
                    self.background_queue.put(("PROGRESS", {
                        "scanned": total_scanned,
                        "speed": speed,
                        "elapsed": elapsed,
                        "current_dir": root_dir
                    }))

            duration = max(time.time() - start_time, 0.1)

            # Sort files descending
            file_list.sort(key=lambda x: x[3], reverse=True)
            sorted_folders = sorted(folder_sizes.items(), key=lambda x: x[1], reverse=True)

            self.background_queue.put(("COMPLETE", {
                "aborted": self.stop_requested,
                "target": target,
                "files": file_list[:file_limit],
                "all_files_count": len(file_list),
                "folders": sorted_folders[:folder_limit],
                "ext_data": dict(ext_data),
                "total_scanned": total_scanned,
                "duration": duration,
                "speed": total_scanned / duration
            }))

        self.scan_thread = threading.Thread(target=worker, daemon=True)
        self.scan_thread.start()

    def process_queue(self):
        try:
            while not self.background_queue.empty():
                msg_type, data = self.background_queue.get_nowait()
                if msg_type == "PROGRESS":
                    self.lbl_stat_files.config(text=f"Files Indexed: {data['scanned']:,}")
                    self.lbl_stat_speed.config(text=f"Scan Speed: {data['speed']:.0f} files/s")
                    mins, secs = divmod(int(data['elapsed']), 60)
                    frac = int((data['elapsed'] - int(data['elapsed'])) * 10)
                    self.lbl_stat_time.config(text=f"Elapsed Time: {mins:02d}:{secs:02d}.{frac}")
                    self.lbl_current_folder.config(text=f"...{data['current_dir'][-45:]}" if len(data['current_dir']) > 45 else data['current_dir'])
                elif msg_type == "COMPLETE":
                    self.on_scan_finished(data)
                elif msg_type == "SEARCH_PROGRESS":
                    self.on_search_progress(data)
                elif msg_type == "SEARCH_COMPLETE":
                    self.on_search_finished(data)
                elif msg_type == "MAP_PROGRESS":
                    self.on_map_progress(data)
                elif msg_type == "MAP_COMPLETE":
                    self.on_map_finished(data)
        except Exception:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def on_scan_finished(self, data):
        self.is_scanning = False
        self.btn_scan.config(text="⚡ Start Scan", bg=ACCENT_CYAN, activebackground="#79c0ff", state="normal")

        if data["aborted"]:
            self.set_status_pill("● SCAN ABORTED", ACCENT_CORAL)
            self.status_lbl.config(text=f"Scan aborted. Indexed {data['total_scanned']:,} files.")
            self.log_message(f"Scan aborted after indexing {data['total_scanned']:,} files in {data['duration']:.2f}s.", level="WARNING")
        else:
            self.set_status_pill("● SCAN COMPLETED", ACCENT_MINT)
            self.status_lbl.config(text=f"Scan complete: {data['total_scanned']:,} files processed.")
            self.log_message(f"Scan complete! Processed {data['total_scanned']:,} files in {data['duration']:.2f}s ({data['speed']:.0f} files/s).", level="SUCCESS")

        self.scanned_files = data["files"]
        self.scanned_folders = data["folders"]
        self.scan_summary = data

        # Populate Files Table
        for rank, (name, ftype, folder, size) in enumerate(data["files"], start=1):
            self.tree_files.insert("", "end", values=(
                rank,
                name,
                ftype,
                format_bytes(size),
                folder
            ))

        # Populate Folders Table
        for rank, (path, size) in enumerate(data["folders"], start=1):
            self.tree_folders.insert("", "end", values=(
                rank,
                path,
                format_bytes(size)
            ))

        # Populate Analytics Extension Table
        sorted_ext = sorted(data["ext_data"].items(), key=lambda x: x[1]["size"], reverse=True)
        total_size = sum(item[1]["size"] for item in sorted_ext)

        for ext_name, stats in sorted_ext[:30]:
            pct = (stats["size"] / total_size * 100) if total_size > 0 else 0
            self.tree_ext.insert("", "end", values=(
                ext_name,
                f"{stats['count']:,}",
                format_bytes(stats["size"]),
                f"{pct:.1f}%"
            ))

        # Update Analytics Metric Summary
        largest_file_name = data["files"][0][0] if data["files"] else "None"
        largest_file_size = format_bytes(data["files"][0][3]) if data["files"] else "0 B"
        self.lbl_analytics_summary.config(
            text=f"Target: {data['target']}  •  Total Scanned: {data['total_scanned']:,} files  •  Indexed Storage: {format_bytes(total_size)}\n"
                 f"Largest File: {largest_file_name} ({largest_file_size})  •  Average Speed: {data['speed']:.0f} files/s"
        )

        self.stats_lbl.config(text=f"Top Files: {len(data['files'])} | Top Folders: {len(data['folders'])}")

        # Print Box-Styled ASCII tables to Activity Log (preserving classic output!)
        self.render_ascii_summary_to_log(data)

    def render_ascii_summary_to_log(self, data):
        """Prints the signature box-styled ASCII summary tables into the log console."""
        self.log_text.insert("end", "\n" + "═" * 70 + "\n", "TABLE")
        self.log_text.insert("end", f"☆ SCAN REPORT FOR {data['target']}\n", "SUCCESS")
        self.log_text.insert("end", f"Processed {data['total_scanned']:,} files in {data['duration']:.2f}s ({data['speed']:.0f} files/s)\n", "INFO")
        self.log_text.insert("end", "─" * 70 + "\n", "TABLE")
        self.log_text.insert("end", f"{'#':<4} {'FILE NAME':<28} {'SIZE':<12} {'TYPE':<8} {'PATH'}\n", "INFO")
        for rank, (name, ftype, folder, size) in enumerate(data["files"][:10], start=1):
            self.log_text.insert("end", f"{rank:<4} {name[:27]:<28} {format_bytes(size):<12} {ftype:<8} {folder[:40]}\n", "TABLE")
        self.log_text.insert("end", "═" * 70 + "\n\n", "TABLE")
        self.log_text.see("end")

    # ==========================================================================
    # ☆ CONTEXT ACTIONS & EXPLORER SHORTCUTS
    # ==========================================================================
    def show_files_context_menu(self, event):
        item = self.tree_files.identify_row(event.y)
        if item:
            self.tree_files.selection_set(item)
            self.menu_files.post(event.x_root, event.y_root)

    def show_folders_context_menu(self, event):
        item = self.tree_folders.identify_row(event.y)
        if item:
            self.tree_folders.selection_set(item)
            self.menu_folders.post(event.x_root, event.y_root)

    def on_file_double_click(self, event):
        self.reveal_selected_file()

    def on_folder_double_click(self, event):
        self.reveal_selected_folder()

    def reveal_selected_file(self):
        sel = self.tree_files.selection()
        if sel:
            item = self.tree_files.item(sel[0])
            name = item["values"][1]
            folder = item["values"][4]
            full_path = os.path.join(folder, name)
            if os.path.exists(full_path):
                subprocess.run(["explorer", f"/select,{full_path}"])
            elif os.path.exists(folder):
                subprocess.run(["explorer", folder])

    def open_selected_file(self):
        sel = self.tree_files.selection()
        if sel:
            item = self.tree_files.item(sel[0])
            full_path = os.path.join(item["values"][4], item["values"][1])
            if os.path.exists(full_path):
                try:
                    os.startfile(full_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not open file:\n{e}")

    def copy_selected_file_path(self):
        sel = self.tree_files.selection()
        if sel:
            item = self.tree_files.item(sel[0])
            full_path = os.path.join(item["values"][4], item["values"][1])
            self.root.clipboard_clear()
            self.root.clipboard_append(full_path)
            self.status_lbl.config(text=f"Copied: {full_path}")

    def reveal_selected_folder(self):
        sel = self.tree_folders.selection()
        if sel:
            path = self.tree_folders.item(sel[0])["values"][1]
            if os.path.exists(path):
                subprocess.run(["explorer", path])

    def copy_selected_folder_path(self):
        sel = self.tree_folders.selection()
        if sel:
            path = self.tree_folders.item(sel[0])["values"][1]
            self.root.clipboard_clear()
            self.root.clipboard_append(path)
            self.status_lbl.config(text=f"Copied: {path}")

    def set_selected_folder_as_target(self):
        sel = self.tree_folders.selection()
        if sel:
            path = self.tree_folders.item(sel[0])["values"][1]
            self.set_target_path(path)
            self.notebook.select(0)
            self.log_message(f"Selected new scan target: {path}", level="INFO")

    # ==========================================================================
    # ☆ EXPORT & CLEAR ACTIONS
    # ==========================================================================
    def on_export_report(self):
        if not self.scanned_files and not self.scanned_folders:
            messagebox.showinfo("No Data", "No scan results to export. Run a scan first!")
            return

        date_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_target = "".join(c for c in (self.current_target or "drive") if c.isalnum())
        default_filename = f"drive_analysis_{safe_target}_{date_slug}.json"

        file_path = filedialog.asksaveasfilename(
            title="Export Storage Analysis Report",
            initialfile=default_filename,
            defaultextension=".json",
            filetypes=[("JSON Report", "*.json"), ("CSV File", "*.csv"), ("Text Report", "*.txt")]
        )
        if not file_path:
            return

        try:
            if file_path.endswith(".json"):
                report = {
                    "tool": "Stellar Snooper",
                    "timestamp": datetime.now().isoformat(),
                    "target": self.current_target,
                    "summary": {
                        "total_scanned_files": self.scan_summary.get("total_scanned", 0),
                        "duration_seconds": self.scan_summary.get("duration", 0),
                        "speed_files_per_sec": self.scan_summary.get("speed", 0)
                    },
                    "top_files": [
                        {"rank": i + 1, "name": f[0], "type": f[1], "directory": f[2], "size_bytes": f[3], "size_formatted": format_bytes(f[3])}
                        for i, f in enumerate(self.scanned_files)
                    ],
                    "top_folders": [
                        {"rank": i + 1, "path": f[0], "size_bytes": f[1], "size_formatted": format_bytes(f[1])}
                        for i, f in enumerate(self.scanned_folders)
                    ]
                }
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2)

            elif file_path.endswith(".csv"):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("Rank,Item Type,Name or Path,Extension,Size (Bytes),Formatted Size\n")
                    for i, item in enumerate(self.scanned_files, start=1):
                        f.write(f'{i},"File","{os.path.join(item[2], item[0])}","{item[1]}",{item[3]},"{format_bytes(item[3])}"\n')
                    for i, item in enumerate(self.scanned_folders, start=1):
                        f.write(f'{i},"Folder","{item[0]}","Folder",{item[1]},"{format_bytes(item[1])}"\n')

            else: # Text format
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"☆ STELLAR SNOOPER REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Target: {self.current_target}\n")
                    f.write(f"Total Scanned: {self.scan_summary.get('total_scanned', 0):,} files in {self.scan_summary.get('duration', 0):.2f}s\n\n")
                    f.write("--- TOP LARGEST FILES ---\n")
                    for i, f in enumerate(self.scanned_files, start=1):
                        f.write(f"{i:<3} {f[0]:<35} {format_bytes(f[3]):<12} {f[2]}\n")
                    f.write("\n--- TOP LARGEST FOLDERS ---\n")
                    for i, f in enumerate(self.scanned_folders, start=1):
                        f.write(f"{i:<3} {f[0]:<60} {format_bytes(f[1])}\n")

            self.status_lbl.config(text=f"Exported: {os.path.basename(file_path)}")
            self.log_message(f"Report exported successfully to: {file_path}", level="SUCCESS")
            messagebox.showinfo("Export Successful", f"Storage report saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export report:\n{e}")
            self.log_message(f"Export error: {e}", level="ERROR")

    def clear_results(self):
        for row in self.tree_files.get_children():
            self.tree_files.delete(row)
        for row in self.tree_folders.get_children():
            self.tree_folders.delete(row)
        for row in self.tree_ext.get_children():
            self.tree_ext.delete(row)
        self.scanned_files = []
        self.scanned_folders = []
        self.lbl_stat_files.config(text="Files Indexed: 0")
        self.lbl_stat_speed.config(text="Scan Speed: 0 files/s")
        self.lbl_stat_time.config(text="Elapsed Time: 00:00.0")
        self.lbl_current_folder.config(text="Idle")
        self.stats_lbl.config(text="Files: 0 | Folders: 0")
        self.status_lbl.config(text="Results cleared.")
        self.log_message("Cleared workspace results.", level="INFO")

    # ==========================================================================
    # ☆ FILE SEARCHER WORKER & ACTIONS
    # ==========================================================================
    def on_browse_search_path(self):
        folder = filedialog.askdirectory(title="Select Folder to Search", initialdir=self.search_path_var.get() or self.current_target or "C:\\")
        if folder:
            self.search_path_var.set(os.path.normpath(folder) + os.sep)

    def sync_search_with_active_target(self):
        if self.current_target:
            self.search_path_var.set(self.current_target)

    def toggle_search(self):
        if self.is_searching:
            self.cancel_search()
        else:
            self.start_search()

    def cancel_search(self):
        if self.is_searching:
            self.stop_search_requested = True
            self.btn_search.config(text="Stopping...", state="disabled")
            self.lbl_search_status.config(text="Aborting search...", fg=ACCENT_CORAL)

    def start_search(self):
        path = self.search_path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showerror("Invalid Path", f"Search directory path does not exist:\n{path}")
            return

        query = self.search_query_var.get().strip()
        ext = self.search_ext_var.get().strip()
        limit_str = self.search_limit_var.get().strip()
        limit = None if limit_str.upper() == "ALL" else int(limit_str)

        self.is_searching = True
        self.stop_search_requested = False
        self.btn_search.config(text="⏹ Stop Search", bg=ACCENT_CORAL, activebackground="#ff7b72", state="normal")
        self.lbl_search_status.config(text=f"Searching in {path}...", fg=ACCENT_CYAN)
        self.lbl_search_metrics.config(text="Folders: 0 | Matches: 0 | Time: 00:00.0")

        # Clear existing table
        for row in self.tree_search.get_children():
            self.tree_search.delete(row)

        def worker():
            res = search_files_engine(
                search_path=path,
                target_name=query,
                ext_filter=ext,
                limit=limit,
                progress_callback=lambda p: self.background_queue.put(("SEARCH_PROGRESS", p)),
                stop_check=lambda: self.stop_search_requested
            )
            res["aborted"] = self.stop_search_requested
            self.background_queue.put(("SEARCH_COMPLETE", res))

        self.search_thread = threading.Thread(target=worker, daemon=True)
        self.search_thread.start()

    def on_search_progress(self, data):
        mins, secs = divmod(int(data["elapsed"]), 60)
        frac = int((data["elapsed"] - int(data["elapsed"])) * 10)
        time_str = f"{mins:02d}:{secs:02d}.{frac}"
        self.lbl_search_metrics.config(
            text=f"Folders: {data['folders_scanned']:,} | Matches: {data['matches_found']:,} | Time: {time_str}"
        )

    def on_search_finished(self, data):
        self.is_searching = False
        self.btn_search.config(text="🔍 Search Files", bg=ACCENT_CYAN, activebackground="#79c0ff", state="normal")
        self.search_results = data["results"]
        self.search_summary = data

        duration = data["duration"]
        total_m = data["total_matches"]
        showing = len(data["results"])

        if data.get("aborted"):
            status_text = f"Search aborted. Found {total_m:,} matches ({showing} listed) in {duration:.2f}s."
            self.lbl_search_status.config(text=status_text, fg=ACCENT_CORAL)
            self.log_message(f"File search aborted: {showing} of {total_m:,} matches in {duration:.2f}s.", level="WARNING")
        else:
            status_text = f"Search complete! Found {total_m:,} matches ({showing} listed) in {duration:.2f}s."
            self.lbl_search_status.config(text=status_text, fg=ACCENT_MINT)
            self.log_message(f"File search completed: {total_m:,} matches found for '{data['target_name'] or '*'}' in {duration:.2f}s.", level="SUCCESS")

        self.lbl_search_summary_count.config(text=f"{showing} of {total_m:,} matches listed")

        for rank, r in enumerate(data["results"], start=1):
            score_str = f"{r['relevance']:.1%}" if data["target_name"] else "N/A"
            self.tree_search.insert("", "end", values=(
                rank,
                score_str,
                r["name"],
                r["ext"],
                format_bytes(r["size"]),
                r["dir"]
            ))

    def on_search_file_double_click(self, event):
        self.reveal_selected_search_file()

    def show_search_context_menu(self, event):
        item = self.tree_search.identify_row(event.y)
        if item:
            self.tree_search.selection_set(item)
            self.menu_search.post(event.x_root, event.y_root)

    def reveal_selected_search_file(self):
        sel = self.tree_search.selection()
        if sel:
            item = self.tree_search.item(sel[0])
            name = item["values"][2]
            folder = item["values"][5]
            full_path = os.path.join(folder, name)
            if os.path.exists(full_path):
                subprocess.run(["explorer", f"/select,{full_path}"])
            elif os.path.exists(folder):
                subprocess.run(["explorer", folder])

    def open_selected_search_file(self):
        sel = self.tree_search.selection()
        if sel:
            item = self.tree_search.item(sel[0])
            full_path = os.path.join(item["values"][5], item["values"][2])
            if os.path.exists(full_path):
                try:
                    os.startfile(full_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Could not open file:\n{e}")

    def copy_selected_search_file_path(self):
        sel = self.tree_search.selection()
        if sel:
            item = self.tree_search.item(sel[0])
            full_path = os.path.join(item["values"][5], item["values"][2])
            self.root.clipboard_clear()
            self.root.clipboard_append(full_path)
            self.status_lbl.config(text=f"Copied: {full_path}")

    def copy_selected_search_dir_path(self):
        sel = self.tree_search.selection()
        if sel:
            item = self.tree_search.item(sel[0])
            folder = item["values"][5]
            self.root.clipboard_clear()
            self.root.clipboard_append(folder)
            self.status_lbl.config(text=f"Copied directory: {folder}")

    def on_export_search_results(self):
        if not self.search_results:
            messagebox.showinfo("No Data", "No search results to export. Run a search first!")
            return

        date_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_slug = "".join(c for c in (self.search_query_var.get() or "search") if c.isalnum())
        default_name = f"search_results_{query_slug}_{date_slug}.txt"

        file_path = filedialog.asksaveasfilename(
            title="Export Search Results",
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt"), ("JSON File", "*.json"), ("CSV File", "*.csv")]
        )
        if not file_path:
            return

        fmt = "json" if file_path.endswith(".json") else ("csv" if file_path.endswith(".csv") else "txt")
        saved = save_search_results(
            results=self.search_results,
            target_name=self.search_query_var.get(),
            duration=self.search_summary.get("duration", 0),
            filename=file_path,
            export_format=fmt
        )
        if saved:
            self.status_lbl.config(text=f"Exported: {os.path.basename(file_path)}")
            self.log_message(f"Search results exported to: {file_path}", level="SUCCESS")
            messagebox.showinfo("Export Successful", f"Search results saved to:\n{file_path}")

    def clear_search_results(self):
        for row in self.tree_search.get_children():
            self.tree_search.delete(row)
        self.search_results = []
        self.lbl_search_status.config(text="Results cleared.", fg=TEXT_MUTED)
        self.lbl_search_metrics.config(text="Folders: 0 | Matches: 0 | Time: 00:00.0")
        self.lbl_search_summary_count.config(text="0 matches listed")

    # ==========================================================================
    # ☆ DIRECTORY MAPPER WORKER & ACTIONS
    # ==========================================================================
    def on_browse_mapper_path(self):
        folder = filedialog.askdirectory(title="Select Folder to Map", initialdir=self.mapper_path_var.get() or self.current_target or "C:\\")
        if folder:
            self.mapper_path_var.set(os.path.normpath(folder) + os.sep)

    def sync_mapper_with_active_target(self):
        if self.current_target:
            self.mapper_path_var.set(self.current_target)

    def toggle_map(self):
        if self.is_mapping:
            self.cancel_map()
        else:
            self.start_map()

    def cancel_map(self):
        if self.is_mapping:
            self.stop_map_requested = True
            self.btn_map.config(text="Stopping...", state="disabled")
            self.lbl_map_status.config(text="Aborting directory mapping...", fg=ACCENT_CORAL)

    def start_map(self):
        path = self.mapper_path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showerror("Invalid Path", f"Target directory path does not exist:\n{path}")
            return

        depth_val = self.mapper_depth_var.get().strip()
        if "Full" in depth_val or "Unlimited" in depth_val:
            max_depth = None
        else:
            try:
                max_depth = int(depth_val.split()[0])
            except Exception:
                max_depth = 3

        ignore_hidden = bool(self.mapper_ignore_hidden_var.get())
        folders_only = bool(self.mapper_folders_only_var.get())

        self.is_mapping = True
        self.stop_map_requested = False
        self.btn_map.config(text="⏹ Stop Mapping", bg=ACCENT_CORAL, activebackground="#ff7b72", state="normal")
        self.lbl_map_status.config(text=f"Mapping directory tree for {path}...", fg=ACCENT_CYAN)
        self.lbl_map_metrics.config(text="Items Mapped: 0")

        self.map_text.delete("1.0", "end")
        self.map_text.insert("end", f"Scanning directory structure for: {path}...\n", "HEADER")

        def worker():
            res = generate_directory_tree(
                start_path=path,
                max_depth=max_depth,
                ignore_hidden=ignore_hidden,
                folders_only=folders_only,
                stop_check=lambda: self.stop_map_requested,
                progress_callback=lambda d, f: self.background_queue.put(("MAP_PROGRESS", {"dirs": d, "files": f}))
            )
            res["aborted"] = self.stop_map_requested
            self.background_queue.put(("MAP_COMPLETE", res))

        self.map_thread = threading.Thread(target=worker, daemon=True)
        self.map_thread.start()

    def on_map_progress(self, data):
        total = data["dirs"] + data["files"]
        self.lbl_map_metrics.config(text=f"Dirs: {data['dirs']:,} | Files: {data['files']:,} (Total: {total:,})")

    def on_map_finished(self, data):
        self.is_mapping = False
        self.btn_map.config(text="🗺️ Generate Tree Map", bg=ACCENT_CYAN, activebackground="#79c0ff", state="normal")
        self.map_result_text = data["text"]
        self.map_stats = data["stats"]

        stats = data["stats"]
        self.map_text.delete("1.0", "end")

        for line in data["lines"]:
            if line.startswith("☆ Directory Map for:"):
                self.map_text.insert("end", line + "\n", "HEADER")
            elif "[Permission Denied]" in line or "[Error:" in line:
                self.map_text.insert("end", line + "\n", "DENIED")
            elif line.endswith("/"):
                self.map_text.insert("end", line + "\n", "FOLDER")
            else:
                self.map_text.insert("end", line + "\n", "FILE")

        if data.get("aborted"):
            status_str = f"Mapping aborted. Mapped {stats['dir_count']:,} dirs, {stats['file_count']:,} files in {stats['duration']:.2f}s."
            self.lbl_map_status.config(text=status_str, fg=ACCENT_CORAL)
            self.log_message(f"Directory tree mapping aborted for {data['start_path']}.", level="WARNING")
        else:
            status_str = f"Mapping complete! Mapped {stats['dir_count']:,} dirs and {stats['file_count']:,} files in {stats['duration']:.2f}s."
            self.lbl_map_status.config(text=status_str, fg=ACCENT_MINT)
            self.log_message(f"Directory tree mapped for {data['start_path']}: {stats['dir_count']:,} dirs, {stats['file_count']:,} files in {stats['duration']:.2f}s.", level="SUCCESS")

        self.lbl_map_metrics.config(text=f"Dirs: {stats['dir_count']:,} | Files: {stats['file_count']:,}")
        self.lbl_map_stats_summary.config(text=f"{stats['dir_count']:,} dirs, {stats['file_count']:,} files ({stats['duration']:.2f}s)")

    def copy_map_to_clipboard(self):
        if not self.map_result_text:
            messagebox.showinfo("No Data", "No directory tree to copy. Generate a map first!")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.map_result_text)
        self.status_lbl.config(text="Directory tree copied to clipboard.")
        messagebox.showinfo("Copied", "Directory tree map copied to clipboard!")

    def on_export_map_tree(self):
        if not self.map_result_text:
            messagebox.showinfo("No Data", "No directory tree to export. Generate a map first!")
            return

        date_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_path = self.mapper_path_var.get().strip()
        safe_name = "".join(c for c in os.path.basename(target_path.rstrip("\\/")) if c.isalnum()) or "dir"
        default_file = f"directory_map_{safe_name}_{date_slug}.txt"

        file_path = filedialog.asksaveasfilename(
            title="Export Directory Tree Map",
            initialfile=default_file,
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt")]
        )
        if not file_path:
            return

        saved = save_map_tree(self.map_result_text, target_path, filename=file_path)
        if saved:
            self.status_lbl.config(text=f"Exported: {os.path.basename(file_path)}")
            self.log_message(f"Directory tree map saved to: {file_path}", level="SUCCESS")
            messagebox.showinfo("Export Successful", f"Directory map saved to:\n{file_path}")

    def clear_map_tree(self):
        self.map_text.delete("1.0", "end")
        self.map_result_text = ""
        self.map_stats = {}
        self.lbl_map_status.config(text="Tree map cleared.", fg=TEXT_MUTED)
        self.lbl_map_metrics.config(text="Items Mapped: 0")
        self.lbl_map_stats_summary.config(text="Ready")

    def sort_tree(self, tree, col, reverse, is_num=False, is_pct=False, is_size=False):
        """Sorts ttk.Treeview content when clicking column headers."""
        items = [(tree.set(k, col), k) for k in tree.get_children("")]

        def sort_key(item):
            val = item[0]
            if is_pct:
                try:
                    return float(val.replace("%", "").strip())
                except ValueError:
                    return -1.0
            elif is_num:
                try:
                    return int(val)
                except ValueError:
                    return -1
            elif is_size:
                try:
                    parts = val.strip().split()
                    if len(parts) == 2:
                        num = float(parts[0])
                        unit = parts[1].upper()
                        mult = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}.get(unit, 1)
                        return num * mult
                except Exception:
                    pass
                return 0
            return val.lower()

        items.sort(key=sort_key, reverse=reverse)

        for index, (val, k) in enumerate(items):
            tree.move(k, "", index)

        tree.heading(col, command=lambda: self.sort_tree(tree, col, not reverse, is_num, is_pct, is_size))

    def on_window_close(self):
        if self.is_scanning or self.is_searching or self.is_mapping:
            if messagebox.askyesno("Operation in Progress", "A background task is currently running. Do you want to cancel and exit?"):
                self.stop_requested = True
                self.stop_search_requested = True
                self.stop_map_requested = True
                self.root.destroy()
        else:
            self.root.destroy()


# ==============================================================================
# ☆ MAIN ENTRY POINT (GUI & CLI MODES)
# ==============================================================================
def main():
    target_arg = None

    # Check CLI flags
    if len(sys.argv) > 1:
        flag = sys.argv[1]
        if flag == "--cli":
            target = sys.argv[2] if len(sys.argv) > 2 else None
            from custom_drive_analyzer import get_largest_items
            get_largest_items(target=target)
            return
        elif flag in ("--search", "-s"):
            target = sys.argv[2] if len(sys.argv) > 2 else None
            cli_search_files(target_dir=target)
            return
        elif flag in ("--map", "-m"):
            target = sys.argv[2] if len(sys.argv) > 2 else None
            cli_map_directory(start_path=target)
            return
        elif not flag.startswith("-"):
            target_arg = flag

    root = tk.Tk()
    app = DriveAnalyzerApp(root, initial_target=target_arg)
    root.mainloop()


if __name__ == "__main__":
    main()
