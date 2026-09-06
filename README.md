# ☆ Stellar Snooper ☆

> "Cosmic storage telemetry—mapping stellar byte constellations across local disks."

Welcome to **Stellar Snooper**! ⭐🛸🔍 This project is a modern Windows desktop workstation utility built with Python and Tkinter—converted from a command-line script into the full **Desktop Tool Template** architecture with cosmic dark aesthetics, non-blocking asynchronous scanning, interactive tables, relevance-ranked file searching, visual directory tree mapping, and Windows Explorer right-click integration.

<img width="1227" height="821" alt="image" src="https://github.com/user-attachments/assets/bb0ece3d-adc8-473c-aaff-6c3a79fdebce" />


---

## ✨ Architecture & Key Features (v1.1.0)

- 🎨 **Cosmic Workstation Aesthetics**:
  - Deep space obsidian theme (`#0d1117`, `#161b22`, `#21262d`, `#30363d`) with starlight cyan (`#58a6ff`), celestial gold (`#f2cc60`), status mint (`#7ee787`), and cosmic amethyst (`#bc8cff`) accents.
  - Native Windows High-DPI awareness (`ctypes.windll.shcore`) ensuring ultra-crisp fonts and icons on 1080p, 1440p, and 4K displays.
- ⚡ **Non-Blocking Background Engines**:
  - Queue-based asynchronous worker running in daemon threads—scans multi-terabyte drives, crawls deep file hierarchies, and maps directory trees without freezing the Tkinter GUI.
  - Live progress telemetry: files indexed counter, real-time scan rate (`files/sec`), elapsed timer (`mm:ss.s`), and active directory monitor.
  - 1-click operation cancellation (`⏹ Stop Scan` / `⏹ Stop Search` / `⏹ Stop Mapping` / `Escape`) for immediate, graceful interruption.
- 🔍 **Cosmic File Searcher (v1.1.0 New)**:
  - **Relevance-Ranked Crawl**: Powered by `difflib.SequenceMatcher` to rank results with exact similarity percentages.
  - **Extension & Limit Filters**: Filter by `ANY` or specific formats (`pdf`, `txt`, `docx`, `py`, `exe`, `png`, `mp4`, etc.) and limit results (`25`, `50`, `100`, `250`, `500`, `ALL`).
  - **Interactive Treeview**: Sortable columns for Rank, Relevance, File Name, Type, Size, and Directory.
  - **Explorer Shell Reveals**: Double-click or right-click to highlight matches directly in Windows Explorer (`explorer /select,"path"`), open files, or copy paths.
  - **Timestamped Multi-Format Exporter**: Save search results directly to `.txt`, `.json`, or `.csv` files.
- 🗺️ **Directory Mapper & ASCII Tree Visualizer (v1.1.0 New)**:
  - **Visual ASCII Trees**: Generates clean, publication-ready directory trees (`├── `, `└── `, `│   `).
  - **Configurable Depth Controls**: Limit traversal to `Full (Unlimited)` or `1` through `6` levels deep to avoid massive terminal or buffer overruns.
  - **Filter Toggles**: Options to exclude hidden files/directories (`.dotfiles`) and filter for directories only.
  - **Rich Monospace Viewer**: Styled cosmic dark text viewer with color-coded syntax tags for directories, files, connectors, and permission warnings.
  - **1-Click Clipboard & File Export**: Copy tree directly to clipboard or export to formatted `.txt`.
- 📊 **Interactive Storage Workstation**:
  - **Top Largest Files Table** (`ttk.Treeview`): Auto-scaled sizes (KB/MB/GB/TB) with sortable columns.
  - **Top Largest Folders Table** (`ttk.Treeview`): Recursive folder aggregation identifying top directory disk hogs.
  - **Storage Analytics Tab**: Categorized breakdown of storage consumption by file extension.
  - **Activity Log & Terminal**: Real-time event logging and classic box-styled ASCII summary report tables.
- 🛸 **Dual Windows Shell Integration**:
  - **Drive & Folder Context Menus**: Register right-click verbs on drives (`Drive\shell`) and folders (`Directory\shell` & `Directory\Background\shell`): *⭐ Snoop Storage with Stellar Snooper*.
  - **Desktop & Start Menu Shortcuts**: Seamless 1-click `.lnk` creation via native Windows APIs.
  - **Zero-Admin Installation**: Integrates cleanly into `HKEY_CURRENT_USER`—no UAC prompts or Administrator privileges required.
- 💾 **Report Exporter**:
  - Export complete storage analysis reports and search queries to **JSON**, **CSV**, or formatted **Text** formats (`Ctrl+S`).
- 🔄 **Multi-Mode Execution**:
  - **Desktop GUI Mode**: Full interactive workstation console (`run.bat` or `python app.py`).
  - **Standalone Binary Mode**: Compiled single-file `.exe` via PyInstaller (`build.bat`).
  - **Headless CLI Suite**:
    - Storage analyzer: `python app.py --cli [TARGET]` or `python custom_drive_analyzer.py [TARGET]`
    - File searcher: `python app.py --search [TARGET]` or `python file_searcher.py [TARGET]`
    - Directory mapper: `python app.py --map [TARGET]` or `python directory_mapper.py [TARGET]`

---

## 📁 Project Directory Structure

```text
StellarSnooper/
├── assets/
│   └── app_icon.ico                 # Multi-resolution icon asset (256, 48, 32, 16)
├── app.py                           # Core Tkinter workstation application & CLI bridge
├── config.json                      # Persistent settings (default drive, limits, themes)
├── custom_drive_analyzer.py         # Standalone CLI storage analyzer with zero-dependency fallback
├── file_searcher.py                 # Standalone FileSearcher engine & CLI menu
├── directory_mapper.py              # Standalone DirectoryMapper engine & CLI tree printer
├── generate_icon.py                 # Pillow script synthesizing cute alien snooper icon
├── setup_integration.py             # Windows context menu & shortcut installer
├── stellar_snooper.spec             # PyInstaller specification for windowed standalone .exe
├── run.bat                          # Smart launcher (.exe -> pythonw -> python)
├── build.bat                        # 1-click PyInstaller build automation
├── install.bat                      # 1-click context menu & shortcut installer
├── uninstall.bat                    # 1-click clean uninstaller
├── requirements.txt                 # Dependencies (pillow, pyinstaller, optional tqdm)
├── CHANGELOG.md                     # Semantic version history and release logs
├── pyproject.toml                   # Project metadata and packaging config
├── .gitignore                       # Git ignore rules for builds, pycache, dist
├── LICENSE                          # MIT License (Cassiopeia Studios)
└── README.md                        # Documentation and quick-start guide
```

---

## 🚀 Getting Started

### 1. Launch the Desktop GUI
Double-click `run.bat` or run:
```bash
python app.py
```
To open and analyze a specific drive or folder directly:
```bash
python app.py D:\
```

### 2. Run in CLI Terminal Mode

#### Storage Space Analyzer:
```bash
python app.py --cli C:
# or
python custom_drive_analyzer.py D:\Projects
```

#### File Searcher:
```bash
python app.py --search C:\Users\Melody\Projects
# or standalone interactive menu:
python file_searcher.py
```

#### Directory Tree Mapper:
```bash
python app.py --map .
# or with custom depth and options:
python directory_mapper.py C:\Users\Melody\Projects -d 3
```

### 3. Install Windows Explorer Integration
Register right-click shortcuts for all drives and folders:
- Double-click `install.bat`, or run:
```bash
python setup_integration.py --install
```

### 4. Build Standalone Executable (`.exe`)
Compile into a single standalone windowed executable:
- Double-click `build.bat`, or run:
```bash
python setup_integration.py --build
```
The compiled binary will be placed in `dist\stellar_snooper.exe`.

---

## 🖱️ Windows Integration & CLI Commands

### 1-Click Batch Files
| Script | Description |
| :--- | :--- |
| `run.bat` | Launches standalone `.exe` if compiled; otherwise launches `app.py` silently via `pythonw.exe`. |
| `build.bat` | Checks Python in PATH, installs dependencies, and compiles with PyInstaller. |
| `install.bat` | Registers Explorer right-click menus for drives and folders, and places Desktop/Start Menu shortcuts. |
| `uninstall.bat` | Cleanly removes all registry keys and shortcuts from the system. |

### Terminal CLI Options
```bash
# Auto-detect and install shell integration (prefers .exe if compiled, else pythonw)
python setup_integration.py --install

# Install specifically in Python development mode
python setup_integration.py --install --mode python

# Inspect current Windows registry & shortcut status
python setup_integration.py --status

# Compile standalone executable with PyInstaller
python setup_integration.py --build

# Cleanly wipe all integrations and shortcuts
python setup_integration.py --uninstall
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `F5` or `Ctrl + R` | Start / Toggle Storage Scan |
| `Escape` | Cancel Active Scan / Search / Map |
| `Ctrl + O` | Browse Custom Target Folder |
| `Ctrl + S` | Export Storage Analysis Report (JSON / CSV / TXT) |
| `Ctrl + Q` | Exit Application |

---

## 📜 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

*Made with ♡ by Melody H. Song*
