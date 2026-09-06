# Changelog

All notable changes to **Stellar Snooper** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-09-06

### Added
- **Cosmic File Searcher (Desktop GUI Tab & CLI Engine)**:
  - Integrated high-speed file searcher module (`file_searcher.py`) with real-time crawl and relevance ranking.
  - Interactive search query bar with pattern matching, instant clear button, extension filter (`ANY`, `pdf`, `txt`, `docx`, `py`, `exe`, etc.), and configurable limits (`25`, `50`, `100`, `250`, `500`, `ALL`).
  - Sequence-matching similarity ranking via `difflib.SequenceMatcher` displaying relevance percentages.
  - Interactive results table (`ttk.Treeview`) with sortable column headers (Rank, Relevance, File Name, Type, Size, Directory Path).
  - Double-click and right-click context menu integration for instant Windows Explorer reveals (`explorer /select`), file execution, and clipboard copying.
  - Export capabilities to timestamped `.txt`, `.json`, and `.csv` files.
  - Thread-safe background execution with live telemetry (folders crawled, matches found, elapsed timer) and 1-click abort (`⏹ Stop Search`).
  - Command-line runner: `python app.py --search [TARGET]` or standalone `python file_searcher.py`.
- **Directory Mapper (Desktop GUI Tab & CLI Engine)**:
  - Integrated recursive directory tree visualizer (`directory_mapper.py`) featuring elegant ASCII branches (`├── `, `└── `, `│   `).
  - Configurable max depth limiter (`Full / Unlimited` or `1` to `6` levels deep) preventing terminal or GUI lockups on massive directories.
  - Filter toggles for excluding hidden files/directories (`.dotfiles`) and restricting views to directories only.
  - Monospace cosmic dark text viewer with color-coded syntax tags for root paths, directory branches, files, and permission warnings.
  - 1-click clipboard copier and `.txt` tree exporter.
  - Thread-safe background mapping with live progress counters and 1-click abort (`⏹ Stop Mapping`).
  - Command-line runner: `python app.py --map [TARGET]` or standalone `python directory_mapper.py [PATH] [-d DEPTH]`.
- **CLI Enhancements**:
  - `python app.py --search [TARGET]` (or `-s`): Run file searcher.
  - `python app.py --map [TARGET]` (or `-m`): Run directory tree mapper.
  - `python app.py --cli [TARGET]`: Run drive storage analyzer.
- **Enhanced Configuration & Preferences**:
  - Added default configuration keys in `config.json` for `search_limit`, `search_default_extension`, `mapper_max_depth`, and `mapper_ignore_hidden`.

---

## [1.0.0] - 2026-09-05

### Added
- **Cosmic Desktop Workstation GUI**: Built with Python and Tkinter, featuring deep space obsidian dark palette (`#0d1117`, `#161b22`), starlight cyan (`#58a6ff`), and celestial star gold (`#f2cc60`).
- **Cute Alien Snooper Mascot**: Custom synthesized multi-resolution `.ico` icon pipeline (`generate_icon.py`) featuring an alien snooper inspecting files with a golden magnifying glass.
- **Asynchronous Background Scanning Engine**: Queue-based thread runner for non-blocking UI during multi-terabyte scans, with ~10Hz live telemetry and 1-click abort (`⏹ Stop Scan` / `Escape`).
- **Interactive Telemetry Tables**:
  - Top Largest Files table (`ttk.Treeview`) with auto-scaled sizes (KB/MB/GB/TB).
  - Top Largest Folders table (`ttk.Treeview`) with recursive size aggregation.
  - Storage Analytics tab categorizing disk consumption by file extension.
  - Activity Log console with color-coded tags and box-styled ASCII summary tables.
- **Windows Explorer Shell Integration**:
  - Context menu verbs on Drives (`Drive\shell`) and Folders (`Directory\shell`): *⭐ Snoop Storage with Stellar Snooper*.
  - Desktop and Start Menu `.lnk` shortcut creation without administrator rights (`HKEY_CURRENT_USER`).
- **Report Exporter**: Multi-format storage report exports in JSON, CSV, and formatted Text (`Ctrl + S`).
- **Dual Execution Modes**: Interactive desktop GUI console alongside a headless, zero-dependency CLI mode (`python app.py --cli [TARGET]`).
- **1-Click Batch Scripts**: `run.bat`, `build.bat`, `install.bat`, and `uninstall.bat`.
