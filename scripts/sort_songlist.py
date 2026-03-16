#!/usr/bin/env python3
"""Sort songlist files using Czech locale collation.

Usage:
    python scripts/sort_songlist.py zboznej/songlists/2026.txt
    python scripts/sort_songlist.py --all           # sort every songlists/*.txt
    python scripts/sort_songlist.py --check FILE    # verify already sorted (exit 1 if not)
"""

import argparse
import locale
import platform
import sys
from pathlib import Path


def set_czech_locale():
    system = platform.system()
    try:
        if system == "Windows":
            locale.setlocale(locale.LC_COLLATE, "cs-CZ")
        elif system in ("Linux", "Darwin"):
            locale.setlocale(locale.LC_COLLATE, "cs_CZ.UTF-8")
        else:
            raise RuntimeError(f"Unsupported platform: {system}")
    except locale.Error:
        print("Warning: Czech locale not available, falling back to system default.",
              file=sys.stderr)
        locale.setlocale(locale.LC_COLLATE, "")


def sort_lines(lines):
    return sorted(lines, key=locale.strxfrm)


def process_file(path, check_only=False):
    text = path.read_text(encoding="utf-8")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    sorted_lines = sort_lines(lines)

    if lines == sorted_lines:
        print(f"  {path}: OK ({len(lines)} titles)")
        return True

    if check_only:
        print(f"  {path}: NOT SORTED")
        for i, (a, b) in enumerate(zip(lines, sorted_lines)):
            if a != b:
                print(f"    First mismatch at line {i+1}: '{a}' should be '{b}'")
                break
        return False

    path.write_text("\n".join(sorted_lines) + "\n", encoding="utf-8")
    print(f"  {path}: SORTED ({len(sorted_lines)} titles)")
    return True


def find_all_songlists():
    root = Path(".")
    results = []
    for variant_dir in sorted(root.iterdir()):
        sl_dir = variant_dir / "songlists"
        if sl_dir.is_dir():
            results.extend(sorted(sl_dir.glob("*.txt")))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", help="Songlist file(s) to sort")
    parser.add_argument("--all", action="store_true",
                        help="Find and sort all */songlists/*.txt files")
    parser.add_argument("--check", action="store_true",
                        help="Check order without modifying (exit 1 if unsorted)")
    args = parser.parse_args()

    if not args.files and not args.all:
        parser.print_help()
        return

    set_czech_locale()

    files = [Path(f) for f in args.files] if args.files else find_all_songlists()
    if not files:
        print("No songlist files found.")
        return

    all_ok = all(process_file(f, check_only=args.check) for f in files)
    if args.check and not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
