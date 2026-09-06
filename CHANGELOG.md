# Changelog

All notable changes to **Stellar Snooper** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-05

### Added
- **Cosmic Desktop Workstation GUI**: Built with Python and Tkinter, featuring deep space obsidian dark palette (#0d1117, #161b22), starlight cyan (#58a6ff), and celestial star gold (#f2cc60).
- **Cute Alien Snooper Mascot**: Custom synthesized multi-resolution .ico icon pipeline (generate_icon.py) featuring an alien snooper inspecting files with a golden magnifying glass.
- **Asynchronous Background Scanning Engine**: Queue-based thread runner for non-blocking UI during multi-terabyte scans, with ~10Hz live telemetry and 1-click abort (⏹ Stop Scan / Escape).
- **Interactive Telemetry Tables**:
  - Top Largest Files table (	tk.Treeview) with auto-scaled sizes (KB/MB/GB/TB).
  - Top Largest Folders table (	tk.Treeview) with recursive size aggregation.
  - Storage Analytics tab categorizing disk consumption by file extension.
  - Activity Log console with color-coded tags and box-styled ASCII summary tables.
- **Windows Explorer Shell Integration**:
  - Context menu verbs on Drives (Drive\shell) and Folders (Directory\shell): *⭐ Snoop Storage with Stellar Snooper*.
  - Desktop and Start Menu .lnk shortcut creation without administrator rights (HKEY_CURRENT_USER).
- **Report Exporter**: Multi-format storage report exports in JSON, CSV, and formatted Text (Ctrl + S).
- **Dual Execution Modes**: Interactive desktop GUI console alongside a headless, zero-dependency CLI mode (python app.py --cli [TARGET]).
- **1-Click Batch Scripts**: un.bat, uild.bat, install.bat, and uninstall.bat.
