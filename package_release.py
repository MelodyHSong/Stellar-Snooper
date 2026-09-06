# ☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆
# ☆ Author: ☆ MelodyHSong ☆
# ☆ Language: Python
# ☆ File Name: package_release.py
# ☆ Description: Automated build, packaging, and checksum generation for Stellar Snooper releases.
# ☆ [Desktop Tool Template: Release Packaging Automation]
# ☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆

import os
import sys
import shutil
import zipfile
import hashlib
import subprocess

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
RELEASE_DIR = os.path.join(BASE_DIR, "release")

# ==============================================================================
# ☆ RELEASE CONFIGURATION
# ==============================================================================
APP_NAME = "Stellar-Snooper"
VERSION = "1.1.0"
DIST_EXE_NAME = "stellar_snooper.exe"
SPEC_FILE_NAME = "stellar_snooper.spec"

# Attempt dynamic detection from setup_integration.py if available
try:
    import setup_integration as si
    if hasattr(si, "DIST_EXE_NAME"):
        DIST_EXE_NAME = si.DIST_EXE_NAME
    if hasattr(si, "SPEC_FILE"):
        SPEC_FILE_NAME = si.SPEC_FILE
    if hasattr(si, "APP_TITLE"):
        APP_NAME = si.APP_TITLE.replace(" ", "-")
except Exception:
    pass

# Load version from config.json if available
try:
    import json
    cfg_path = os.path.join(BASE_DIR, "config.json")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            VERSION = cfg.get("version", VERSION)
except Exception:
    pass


def calculate_sha256(filepath):
    """Calculate SHA-256 hash of a file."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def step(msg):
    print(f"\n[+] {msg}")


def build_icon():
    """Generate multi-resolution icons if generate_icon.py exists."""
    icon_script = os.path.join(BASE_DIR, "generate_icon.py")
    if os.path.exists(icon_script):
        step("Generating multi-resolution cosmic icon asset...")
        res = subprocess.run([sys.executable, icon_script], cwd=BASE_DIR)
        if res.returncode != 0:
            print("[!] Warning: Icon generation exited with non-zero code. Proceeding with existing icon if available.")


def build_executable():
    """Compile standalone executable using PyInstaller."""
    step("Compiling standalone executable with PyInstaller...")
    spec_path = os.path.join(BASE_DIR, SPEC_FILE_NAME)
    if not os.path.exists(spec_path):
        specs = [f for f in os.listdir(BASE_DIR) if f.endswith(".spec")]
        if specs:
            spec_path = os.path.join(BASE_DIR, specs[0])
        else:
            raise FileNotFoundError(f"PyInstaller spec file not found: {SPEC_FILE_NAME}")

    res = subprocess.run([sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", spec_path], cwd=BASE_DIR)
    if res.returncode != 0:
        raise RuntimeError(f"PyInstaller build failed with exit code {res.returncode}.")

    exe_path = os.path.join(DIST_DIR, DIST_EXE_NAME)
    if not os.path.exists(exe_path) or os.path.getsize(exe_path) == 0:
        raise FileNotFoundError(f"Executable missing or empty: {exe_path}")
    print(f"    Executable verified: {exe_path} ({os.path.getsize(exe_path):,} bytes)")
    return exe_path


def create_zip_package():
    """Package standalone portable release archive."""
    step("Packaging standalone portable release archive...")
    zip_v_name = f"{APP_NAME}-v{VERSION}-Windows-x64.zip"
    zip_alias_name = f"{APP_NAME}-Windows-x64.zip"

    zip_v_dist = os.path.join(DIST_DIR, zip_v_name)
    zip_alias_dist = os.path.join(DIST_DIR, zip_alias_name)
    zip_release = os.path.join(RELEASE_DIR, zip_v_name)

    os.makedirs(DIST_DIR, exist_ok=True)
    os.makedirs(RELEASE_DIR, exist_ok=True)

    # Core release files to include
    files_to_pack = [
        ("dist/" + DIST_EXE_NAME, DIST_EXE_NAME),
        ("config.json", "config.json"),
        ("README.md", "README.md"),
        ("CHANGELOG.md", "CHANGELOG.md"),
        ("LICENSE", "LICENSE"),
        ("run.bat", "run.bat"),
        ("install.bat", "install.bat"),
        ("uninstall.bat", "uninstall.bat"),
        ("assets/app_icon.ico", "assets/app_icon.ico"),
    ]

    with zipfile.ZipFile(zip_v_dist, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, arc in files_to_pack:
            full_src = os.path.join(BASE_DIR, src)
            if os.path.exists(full_src):
                zf.write(full_src, arc)
                print(f"    Packed: {src} -> {arc}")

    # Copy to alias and release directory
    shutil.copy2(zip_v_dist, zip_alias_dist)
    shutil.copy2(zip_v_dist, zip_release)

    print(f"    Archive created: {zip_v_dist} ({os.path.getsize(zip_v_dist):,} bytes)")
    print(f"    Archive alias:   {zip_alias_dist} ({os.path.getsize(zip_alias_dist):,} bytes)")
    return [zip_v_dist, zip_alias_dist, zip_release]


def generate_checksums(files):
    """Generate SHA-256 checksums file in dist/ and release/."""
    step("Generating SHA-256 checksums...")
    checksums_dist = os.path.join(DIST_DIR, "SHA256SUMS.txt")
    checksums_release = os.path.join(RELEASE_DIR, "SHA256SUMS.txt")

    lines = []
    seen = set()
    for filepath in files:
        filename = os.path.basename(filepath)
        if filename in seen:
            continue
        seen.add(filename)
        sha = calculate_sha256(filepath)
        size = os.path.getsize(filepath)
        lines.append(f"{sha}  {filename}")
        print(f"    {filename:<42}  {size:>10,} bytes  SHA256: {sha}")

    content = "\n".join(lines) + "\n"
    with open(checksums_dist, "w", encoding="utf-8") as f:
        f.write(content)
    with open(checksums_release, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"    Checksums saved to: {checksums_dist} and {checksums_release}")
    return checksums_dist


def main():
    print("=" * 70)
    print(f"   ⭐ {APP_NAME.upper()} v{VERSION} — RELEASE PACKAGING SEQUENCE 🛸   ")
    print("=" * 70)

    os.makedirs(DIST_DIR, exist_ok=True)
    build_icon()
    exe_path = build_executable()
    zip_paths = create_zip_package()

    # Track distinct files
    all_artifacts = [exe_path, zip_paths[0], zip_paths[1]]
    checksums_path = generate_checksums(all_artifacts)

    print("\n" + "=" * 70)
    print("   ✨ ALL RELEASE FILES COMPILED AND VERIFIED SUCCESSFULLY! ✨   ")
    print("=" * 70)
    for f in all_artifacts + [checksums_path]:
        print(f"   * dist/{os.path.basename(f)}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
