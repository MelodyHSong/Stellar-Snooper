# ☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆
# ☆ Author: ☆ MelodyHSong ☆
# ☆ Language: Python
# ☆ File Name: directory_mapper.py
# ☆ Date: 2026-01-24 (Updated 2026-09-06 for v1.1.0)
# ☆ Version: 1.1.0
# ☆
# ☆ Description: Recursively maps a directory structure into a visual ASCII tree.
# ☆ "Mapping the chaos of your folders, one branch at a time."
# ☆ Integrated into the Stellar Snooper workstation suite.
# ☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆

import os
import sys
import time
from datetime import datetime

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def generate_directory_tree(
    start_path,
    max_depth=None,
    ignore_hidden=True,
    folders_only=False,
    stop_check=None,
    progress_callback=None
):
    """
    Recursively generates an ASCII tree structure for a directory.
    Yields or returns a dict with formatted lines and statistics.
    """
    start_time = time.time()
    stats = {
        "dir_count": 0,
        "file_count": 0,
        "permission_denied_count": 0,
        "duration": 0.0
    }
    lines = []

    norm_start = os.path.abspath(start_path)
    lines.append(f"☆ Directory Map for: {norm_start}")
    lines.append("")

    def _walk(current_path, indent="", current_depth=1):
        if stop_check and stop_check():
            return

        if max_depth is not None and current_depth > max_depth:
            return

        try:
            raw_items = os.listdir(current_path)
        except PermissionError:
            stats["permission_denied_count"] += 1
            lines.append(f"{indent}└── [Permission Denied]")
            return
        except OSError as e:
            lines.append(f"{indent}└── [Error: {e}]")
            return

        # Filter items
        filtered = []
        for item in raw_items:
            if ignore_hidden and item.startswith("."):
                continue
            item_path = os.path.join(current_path, item)
            is_dir = os.path.isdir(item_path)
            if folders_only and not is_dir:
                continue
            filtered.append((item, item_path, is_dir))

        # Sort: directories first, then files alphabetically
        filtered.sort(key=lambda x: (not x[2], x[0].lower()))

        for index, (item, path, is_dir) in enumerate(filtered):
            if stop_check and stop_check():
                break

            is_last = (index == len(filtered) - 1)
            connector = "└── " if is_last else "├── "

            if is_dir:
                stats["dir_count"] += 1
                lines.append(f"{indent}{connector}{item}/")
            else:
                stats["file_count"] += 1
                lines.append(f"{indent}{connector}{item}")

            if progress_callback and (stats["dir_count"] + stats["file_count"]) % 50 == 0:
                progress_callback(stats["dir_count"], stats["file_count"])

            if is_dir:
                extension = "    " if is_last else "│   "
                _walk(path, indent + extension, current_depth + 1)

    _walk(norm_start, "", 1)
    stats["duration"] = max(time.time() - start_time, 0.001)

    return {
        "lines": lines,
        "text": "\n".join(lines),
        "stats": stats,
        "start_path": norm_start
    }


def save_tree_to_file(tree_text, start_path, filename=None):
    """Exports generated ASCII tree map to a text file with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not filename:
        safe_tag = "".join(c for c in os.path.basename(start_path.rstrip("\\/")) if c.isalnum()) or "root"
        filename = f"directory_map_{safe_tag}_{timestamp}.txt"

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Stellar Snooper Directory Map\n")
            f.write(f"# Target: {start_path}\n")
            f.write(f"# Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            f.write(tree_text)
            f.write("\n")
        print(f"\n☆ Tree map successfully saved to: {filename} ☆")
        return filename
    except Exception as e:
        print(f"\nError saving directory map: {e}")
        return None


def map_directory(start_path=None, max_depth=None, ignore_hidden=True, folders_only=False):
    """
    CLI directory tree mapper.
    Maps start_path and prints to terminal.
    """
    if not start_path:
        start_path = os.getcwd()

    if not os.path.exists(start_path):
        print(f"Error: Directory path '{start_path}' does not exist.")
        return

    result = generate_directory_tree(
        start_path=start_path,
        max_depth=max_depth,
        ignore_hidden=ignore_hidden,
        folders_only=folders_only
    )

    print(result["text"])
    stats = result["stats"]
    print("\n" + "─" * 60)
    print(f"☆ Mapped {stats['dir_count']:,} directories and {stats['file_count']:,} files in {stats['duration']:.2f}s.")
    if stats["permission_denied_count"] > 0:
        print(f"☆ Access denied to {stats['permission_denied_count']} folders.")
    print("─" * 60)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stellar Snooper - ASCII Directory Tree Mapper")
    parser.add_argument("path", nargs="?", default=None, help="Root directory path to map (defaults to current directory)")
    parser.add_argument("-d", "--depth", type=int, default=None, help="Maximum recursion depth limit")
    parser.add_argument("--all", action="store_true", help="Include hidden files and folders (.dotfiles)")
    parser.add_argument("--folders-only", action="store_true", help="Only map directory structure, hiding files")
    parser.add_argument("-o", "--output", help="Save output directly to a text file")

    args = parser.parse_args()
    target_path = args.path if args.path else os.getcwd()

    res = generate_directory_tree(
        start_path=target_path,
        max_depth=args.depth,
        ignore_hidden=not args.all,
        folders_only=args.folders_only
    )
    print(res["text"])
    stats = res["stats"]
    print("\n" + "─" * 60)
    print(f"☆ Mapped {stats['dir_count']:,} directories and {stats['file_count']:,} files in {stats['duration']:.2f}s.")
    print("─" * 60)

    if args.output:
        save_tree_to_file(res["text"], target_path, filename=args.output)
