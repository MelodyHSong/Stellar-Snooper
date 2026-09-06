# ☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆
# ☆ Author: ☆ MelodyHSong ☆
# ☆ Language: Python
# ☆ File Name: file_searcher.py
# ☆ Date: 2026-01-09 (Updated 2026-09-06 for v1.1.0)
# ☆ Version: 1.1.0
# ☆
# ☆ Description: Advanced file searcher with drive detection, progress 
# ☆ indicators, relevance ranking, timestamped exports, adjustable 
# ☆ limits, and a search duration timer.
# ☆ Integrated into the Stellar Snooper workstation suite.
# ☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆

import os
import difflib
import string
import sys
import time
import json
import csv
from datetime import datetime

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def get_available_drives():
    """Detects available drive letters on Windows or root on Unix-like systems."""
    drives = []
    if sys.platform == "win32":
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
    else:
        drives = ["/"]
    return drives


def format_bytes(size_bytes):
    """Utility to format bytes into readable KB, MB, GB, or TB."""
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


def calculate_relevance(target_name, filename):
    """Calculates sequence matching ratio between search query and filename."""
    if not target_name:
        return 1.0
    return difflib.SequenceMatcher(None, target_name.lower(), filename.lower()).ratio()


def search_files_engine(
    search_path,
    target_name="",
    ext_filter="any",
    limit=None,
    progress_callback=None,
    stop_check=None
):
    """
    Core search engine.
    Yields or returns matches with relevance scores, sizes, and file metadata.
    Supports real-time progress callbacks and graceful abort checks.
    """
    clean_ext = ext_filter.lower().strip().lstrip(".")
    target_query = target_name.strip().lower()

    matches = []
    dir_count = 0
    total_files_checked = 0
    start_time = time.time()
    last_callback_time = 0

    try:
        for root, dirs, files in os.walk(search_path):
            if stop_check and stop_check():
                break

            dir_count += 1
            for file in files:
                if stop_check and stop_check():
                    break

                total_files_checked += 1
                file_name_part, file_ext = os.path.splitext(file)
                f_ext_clean = file_ext.lower().replace(".", "")

                ext_match = (clean_ext == "any" or clean_ext == "" or clean_ext == f_ext_clean)
                if ext_match:
                    name_match = (not target_query or target_query in file.lower())
                    if name_match:
                        full_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(full_path)
                        except (OSError, PermissionError):
                            file_size = 0

                        relevance = calculate_relevance(target_name, file)
                        matches.append({
                            "name": file,
                            "ext": file_ext.lower() if file_ext else "[No Ext]",
                            "path": full_path,
                            "dir": root,
                            "size": file_size,
                            "relevance": relevance
                        })

            now = time.time()
            if progress_callback and (now - last_callback_time >= 0.1):
                last_callback_time = now
                elapsed = max(now - start_time, 0.001)
                progress_callback({
                    "folders_scanned": dir_count,
                    "files_checked": total_files_checked,
                    "matches_found": len(matches),
                    "elapsed": elapsed,
                    "current_dir": root
                })

    except (PermissionError, OSError):
        pass

    duration = max(time.time() - start_time, 0.001)

    # Relevance ranking (highest similarity first)
    if target_name:
        matches.sort(key=lambda x: (x["relevance"], x["size"]), reverse=True)
    else:
        # Default sort by size descending if no search query
        matches.sort(key=lambda x: x["size"], reverse=True)

    results = matches[:limit] if limit else matches

    return {
        "results": results,
        "total_matches": len(matches),
        "total_folders": dir_count,
        "total_files_checked": total_files_checked,
        "duration": duration,
        "search_path": search_path,
        "target_name": target_name,
        "ext_filter": ext_filter
    }


def save_results_to_file(results, target_name, duration, filename=None, export_format="txt"):
    """Saves search results to a timestamped file (.txt, .json, or .csv)."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not filename:
        safe_tag = "".join(c for c in (target_name or "all_files") if c.isalnum())
        filename = f"search_results_{safe_tag}_{timestamp}.{export_format}"

    try:
        if export_format == "json" or filename.endswith(".json"):
            data = {
                "tool": "Stellar Snooper File Searcher",
                "timestamp": datetime.now().isoformat(),
                "search_query": target_name if target_name else "All Files",
                "duration_seconds": round(duration, 3),
                "total_results": len(results),
                "results": [
                    {
                        "rank": i + 1,
                        "name": r["name"] if isinstance(r, dict) else r[0],
                        "relevance": f"{r['relevance']:.1%}" if isinstance(r, dict) else "N/A",
                        "size_bytes": r["size"] if isinstance(r, dict) else 0,
                        "size_formatted": format_bytes(r["size"]) if isinstance(r, dict) else "N/A",
                        "full_path": r["path"] if isinstance(r, dict) else r[1]
                    }
                    for i, r in enumerate(results)
                ]
            }
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        elif export_format == "csv" or filename.endswith(".csv"):
            with open(filename, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Rank", "Relevance", "File Name", "Extension", "Size (Bytes)", "Formatted Size", "Full Path"])
                for i, r in enumerate(results, start=1):
                    if isinstance(r, dict):
                        writer.writerow([
                            i,
                            f"{r['relevance']:.1%}" if target_name else "N/A",
                            r["name"],
                            r.get("ext", ""),
                            r["size"],
                            format_bytes(r["size"]),
                            r["path"]
                        ])
                    else:
                        writer.writerow([i, "N/A", r[0], "", "", "", r[1]])

        else: # Plain Text format
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Search Results for: {target_name if target_name else 'All Files'}\n")
                f.write(f"Date of Search: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Search Duration: {duration:.2f} seconds\n")
                f.write("=" * 88 + "\n")
                f.write(f"{'Relevance':<10} | {'File Name':<32} | {'Size':<10} | {'Full Path'}\n")
                f.write("-" * 88 + "\n")
                for r in results:
                    if isinstance(r, dict):
                        score = f"{r['relevance']:.1%}" if target_name else "N/A"
                        name = (r["name"][:29] + "...") if len(r["name"]) > 32 else r["name"]
                        size_str = format_bytes(r["size"])
                        f.write(f"{score:<10} | {name:<32} | {size_str:<10} | {r['path']}\n")
                    else:
                        name, path = r
                        score = f"{calculate_relevance(target_name, name):.1%}" if target_name else "N/A"
                        f.write(f"{score:<10} | {name[:32]:<32} | {'--':<10} | {path}\n")

        print(f"\n☆ Results successfully saved to: {filename} ☆")
        return filename
    except Exception as e:
        print(f"\nError saving file: {e}")
        return None


def get_limit_choice():
    """Prompts the user to select how many files to list."""
    print("\nHow many results would you like to see?")
    print("1. 25")
    print("2. 50")
    print("3. 100")
    print("4. ALL")

    limit_map = {"1": 25, "2": 50, "3": 100, "4": None}
    while True:
        choice = input("Select an option (1-4): ").strip()
        if choice in limit_map:
            return limit_map[choice]
        print("Invalid choice. Please select 1, 2, 3, or 4.")


def search_files(target_dir=None, query=None, ext="any", limit=None):
    """Interactive CLI menu and search runner."""
    if target_dir is not None:
        # Non-interactive / parameterized invocation
        if not os.path.exists(target_dir):
            print(f"Error: The path '{target_dir}' does not exist.")
            return

        print(f"\nSearching in: {target_dir}...")
        start_time = time.time()
        res = search_files_engine(
            search_path=target_dir,
            target_name=query or "",
            ext_filter=ext or "any",
            limit=limit,
            progress_callback=lambda p: sys.stdout.write(
                f"\rScanning... Folders: {p['folders_scanned']} | Found: {p['matches_found']}"
            )
        )
        sys.stdout.write("\r" + " " * 60 + "\r")
        sys.stdout.flush()

        results = res["results"]
        duration = res["duration"]

        if not results:
            print(f"No matching files found. (Scan took {duration:.2f} seconds)")
            return

        print(f"\nSearch Complete! Time taken: {duration:.2f} seconds")
        print(f"Results (Showing {len(results)} of {res['total_matches']} found):")
        print(f"{'Relevance':<10} | {'File Name':<32} | {'Size':<10} | {'Full Path'}")
        print("-" * 96)
        for r in results:
            score_str = f"{r['relevance']:>9.1%}" if query else "   N/A    "
            display_name = (r["name"][:29] + "...") if len(r["name"]) > 32 else r["name"]
            size_str = format_bytes(r["size"])
            print(f"{score_str} | {display_name:<32} | {size_str:<10} | {r['path']}")
        return

    # Interactive Loop
    while True:
        print("\n" + "=" * 42)
        print(" ☆ STELLAR SNOOPER - FILE SEARCHER MENU ☆")
        print("=" * 42)

        drives = get_available_drives()
        for i, drive in enumerate(drives, 1):
            print(f"{i}. Scan Drive {drive}")

        print(f"{len(drives) + 1}. Enter a manual path")
        print(f"{len(drives) + 2}. Exit")

        choice = input("\nSelect an option: ").strip()

        if choice == str(len(drives) + 2):
            print("Exiting searcher. Goodbye! ☆")
            break

        if choice == str(len(drives) + 1):
            search_path = input("Enter the full directory path: ").strip()
        elif choice.isdigit() and 1 <= int(choice) <= len(drives):
            search_path = drives[int(choice) - 1]
        else:
            print("Invalid selection. Please try again.")
            continue

        if not os.path.exists(search_path):
            print(f"Error: The path '{search_path}' does not exist.")
            continue

        target_name = input("Enter filename (Leave blank to list all files): ").strip()
        ext_input = input("Enter file extension (e.g., 'pdf', 'txt') or 'ANY' for all: ").strip().lower()

        if ext_input == "any" and not target_name:
            print("\n[!] Error: You cannot search for 'ANY' extension without a filename.")
            print("Restarting the search menu...\n")
            continue

        limit = get_limit_choice()

        print(f"\nSearching in: {search_path}...")

        try:
            res = search_files_engine(
                search_path=search_path,
                target_name=target_name,
                ext_filter=ext_input,
                limit=limit,
                progress_callback=lambda p: (
                    sys.stdout.write(f"\rScanning... Folders: {p['folders_scanned']} | Found: {p['matches_found']}"),
                    sys.stdout.flush()
                )
            )
            sys.stdout.write("\r" + " " * 70 + "\r")
            sys.stdout.flush()
        except KeyboardInterrupt:
            print(f"\nSearch cancelled by user.")
            continue

        results = res["results"]
        duration = res["duration"]

        if not results:
            print(f"No matching files found. (Scan took {duration:.2f} seconds)")
        else:
            print(f"\nSearch Complete! Time taken: {duration:.2f} seconds")
            print(f"Results (Showing {len(results)} of {res['total_matches']} found):")
            print(f"{'Relevance':<10} | {'File Name':<32} | {'Size':<10} | {'Full Path'}")
            print("-" * 96)

            for r in results:
                score_str = f"{r['relevance']:>9.1%}" if target_name else "   N/A    "
                display_name = (r["name"][:29] + "...") if len(r["name"]) > 32 else r["name"]
                size_str = format_bytes(r["size"])
                print(f"{score_str} | {display_name:<32} | {size_str:<10} | {r['path']}")

            export_choice = input("\nWould you like to export these results to a file? (y/n): ").strip().lower()
            if export_choice == "y":
                fmt_choice = input("Select format: [1] Text (.txt), [2] JSON (.json), [3] CSV (.csv): ").strip()
                fmt = "json" if fmt_choice == "2" else ("csv" if fmt_choice == "3" else "txt")
                save_results_to_file(results, target_name, duration, export_format=fmt)

        input("\nPress Enter to return to the menu...")


if __name__ == "__main__":
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        search_files(target_dir=sys.argv[1])
    else:
        search_files()
