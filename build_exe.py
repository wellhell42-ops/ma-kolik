#!/usr/bin/env python3
"""
Windows .exe oluşturma scripti.

Kullanım:
    pip install pyinstaller
    python build_exe.py

Bu script PyInstaller kullanarak tek dosya Windows uygulaması oluşturur.
"""

import subprocess
import sys
from pathlib import Path


def build():
    base_dir = Path(__file__).parent

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "MackolikStats",
        "--add-data", f"mackolik{';' if sys.platform == 'win32' else ':'}mackolik",
        "--hidden-import", "mackolik",
        "--hidden-import", "mackolik.scrapers",
        "--hidden-import", "mackolik.scrapers.standings",
        "--hidden-import", "mackolik.scrapers.player_stats",
        "--hidden-import", "mackolik.scrapers.matches",
        "--hidden-import", "mackolik.scrapers.live_scores",
        "--hidden-import", "mackolik.scrapers.team_stats",
        "--hidden-import", "mackolik.exporters",
        "--hidden-import", "mackolik.exporters.exporter",
        "--hidden-import", "mackolik.models",
        "--hidden-import", "mackolik.demo",
        "--hidden-import", "mackolik.config",
        "--hidden-import", "mackolik.scraper",
        "--hidden-import", "lxml",
        "--hidden-import", "lxml.etree",
        "--hidden-import", "openpyxl",
        str(base_dir / "gui.py"),
    ]

    # Add icon if it exists
    icon_path = base_dir / "mackolik.ico"
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])

    print("Building MackolikStats.exe...")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=str(base_dir))

    if result.returncode == 0:
        exe_path = base_dir / "dist" / ("MackolikStats.exe" if sys.platform == "win32" else "MackolikStats")
        print(f"\nBaşarılı! Uygulama oluşturuldu: {exe_path}")
        print("\nKullanım:")
        print(f"  {exe_path}")
    else:
        print("\nHata! Build başarısız oldu.")
        sys.exit(1)


if __name__ == "__main__":
    build()
