"""
Automated fixer for songbook input files.

Applies safe, tested, non-interactive transformations.
Companion to check_songbook.py (which only reports issues).

Usage:
    python scripts/fix_songbook.py <file_or_dir> [--dry-run] [--fix FIXNAME ...]

Examples:
    python scripts/fix_songbook.py nezboznej/songs/Přítel.txt --dry-run
    python scripts/fix_songbook.py nezboznej/songs/
    python scripts/fix_songbook.py nezboznej/songs/ --fix apostrophes sus-chords

Without --fix, all fixes are applied. With --fix, only the named fixes run.
Use --dry-run to preview changes without modifying files.
"""

import argparse
import re
import sys
from pathlib import Path

SONG_SEPARATOR = "=" * 18


# ---------------------------------------------------------------------------
# Individual fixers.  Each takes the full file text and returns (new_text, count).
# ---------------------------------------------------------------------------

def fix_separators(text):
    """Normalize all song separator lines to exactly 18 '=' signs
    and ensure consistent blank-line spacing around them."""
    lines = text.splitlines()
    new_lines = []
    changes = 0
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.strip("= \t") == "" and line.count("=") >= 2:
            if line.strip() != SONG_SEPARATOR:
                changes += 1

            j = len(new_lines) - 1
            while j >= 0 and new_lines[j].strip() == "":
                j -= 1
            new_lines = new_lines[: j + 1]
            new_lines.append("")
            new_lines.append(SONG_SEPARATOR)

            i += 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            new_lines.append("")
            if i < len(lines):
                new_lines.append(lines[i])
                i += 1
            continue

        new_lines.append(line)
        i += 1

    return "\n".join(new_lines) + "\n", changes


def fix_quotations(text):
    """Replace quotation mark characters with \\uv{...}, per-line.
    Skips chords (inside parentheses). If a line has an odd number of
    quote chars outside parens, leaves them untouched and warns."""
    quote_chars = {'"', "\u201c", "\u201d", "\u201e"}
    lines = text.split("\n")
    result_lines = []
    total_pairs = 0

    for line_num, line in enumerate(lines, 1):
        parens = []
        stack = []
        for i, c in enumerate(line):
            if c == "(":
                stack.append(i)
            elif c == ")" and stack:
                parens.append((stack.pop(), i))

        def inside_parens(idx):
            return any(s <= idx <= e for s, e in parens)

        quote_positions = [
            i for i, c in enumerate(line) if c in quote_chars and not inside_parens(i)
        ]

        if len(quote_positions) % 2 != 0:
            print(f"  [quotations] WARNING: odd number of quotes on line {line_num}, skipping")
            result_lines.append(line)
            continue

        if not quote_positions:
            result_lines.append(line)
            continue

        built = []
        prev = 0
        for pair_idx in range(0, len(quote_positions), 2):
            open_pos = quote_positions[pair_idx]
            close_pos = quote_positions[pair_idx + 1]
            built.append(line[prev:open_pos])
            built.append("\\uv{")
            built.append(line[open_pos + 1 : close_pos])
            built.append("}")
            prev = close_pos + 1
            total_pairs += 1
        built.append(line[prev:])
        result_lines.append("".join(built))

    return "\n".join(result_lines), total_pairs


def fix_apostrophes(text):
    """Replace wrong apostrophe characters (acute accent, prime) with ASCII '."""
    count = 0
    for bad in ("\u00b4", "\u2032"):
        n = text.count(bad)
        if n:
            text = text.replace(bad, "'")
            count += n
    return text, count


def fix_ellipses(text):
    """Replace literal ellipsis character with three dots."""
    count = text.count("\u2026")
    return text.replace("\u2026", "..."), count


def fix_multiply_sign(text):
    """Replace \\b\\d+x\\b with the proper times sign (e.g. 3x -> 3\u00d7)."""
    pat = re.compile(r"\b(\d+)x\b")
    new_text, count = pat.subn(lambda m: m.group(1) + "\u00d7", text)
    return new_text, count


def fix_verse_dots(text):
    """Replace verse labels using . with : (e.g. '1.' -> '1:' at line start)."""
    pat = re.compile(r"^(\d+)\.", re.MULTILINE)
    new_text, count = pat.subn(r"\1:", text)
    return new_text, count


def fix_sus_chords(text):
    """Replace sus notation: (Esus4) -> (E4), (Asus2) -> (A2), etc."""
    pat = re.compile(r"\(([A-G][\"b]?)sus(\d[^)]*)\)")
    new_text, count = pat.subn(r"(\1\2)", text)
    return new_text, count


def fix_mi_chords(text):
    """Replace mi notation: (Ami) -> (Am), (Emi7) -> (Em7), etc."""
    pat = re.compile(r"\(([A-G][\"b]?)mi([^)]*)\)")
    new_text, count = pat.subn(r"(\1m\2)", text)
    return new_text, count


# ---------------------------------------------------------------------------
# Registry of all available fixes, in recommended application order.
# ---------------------------------------------------------------------------

ALL_FIXES = [
    ("separators", "Normalize song separators to 18 '='", fix_separators),
    ("quotations", "Replace quote chars with \\uv{...}", fix_quotations),
    ("apostrophes", "Fix wrong apostrophe characters", fix_apostrophes),
    ("ellipses", "Replace literal ellipsis with '...'", fix_ellipses),
    ("multiply", "Replace Nx with N\u00d7 for repeats", fix_multiply_sign),
    ("verse-dots", "Replace verse label '1.' with '1:'", fix_verse_dots),
    ("sus-chords", "Replace (Esus4) with (E4)", fix_sus_chords),
    ("mi-chords", "Replace (Ami) with (Am)", fix_mi_chords),
]


# ---------------------------------------------------------------------------
# File collection
# ---------------------------------------------------------------------------

def collect_files(path):
    p = Path(path)
    if p.is_dir():
        return sorted(p.glob("*.txt"))
    return [p]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_file(path, selected, dry_run):
    text = path.read_text(encoding="utf-8")
    original = text
    file_changes = 0

    for name, description, fn in ALL_FIXES:
        if name not in selected:
            continue
        text, count = fn(text)
        if count:
            print(f"  {name}: {count} change(s) -- {description}")
            file_changes += count

    if file_changes == 0:
        return 0

    if dry_run:
        return file_changes

    if text != original:
        path.write_text(text, encoding="utf-8")

    return file_changes


def main():
    parser = argparse.ArgumentParser(
        description="Apply automated fixes to songbook input file(s).",
        epilog="Available fixes: " + ", ".join(name for name, _, _ in ALL_FIXES),
    )
    parser.add_argument("input", help="Path to a song file or directory of song files")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would change without modifying files",
    )
    parser.add_argument(
        "--fix", nargs="+", metavar="NAME",
        help="Only apply these specific fixes (default: all)",
    )
    args = parser.parse_args()

    fix_names = {name for name, _, _ in ALL_FIXES}
    if args.fix:
        unknown = set(args.fix) - fix_names
        if unknown:
            parser.error(f"Unknown fix(es): {', '.join(unknown)}")
        selected = set(args.fix)
    else:
        selected = fix_names

    files = collect_files(args.input)
    if not files:
        print(f"No .txt files found in {args.input}")
        return 1

    grand_total = 0
    for f in files:
        if len(files) > 1:
            print(f"\n--- {f.name} ---")
        count = process_file(f, selected, args.dry_run)
        grand_total += count

    if grand_total == 0:
        print("No changes needed.")
    elif args.dry_run:
        print(f"\n[dry-run] Would apply {grand_total} change(s) across {len(files)} file(s)")
    else:
        print(f"\nApplied {grand_total} change(s) across {len(files)} file(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
