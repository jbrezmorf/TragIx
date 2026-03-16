"""
Consolidated quality-check script for songbook input files.

Runs regex-based checks, unclosed chord detection, chord naming
convention checks, and optionally chord diagram coverage analysis.

Usage:
    python scripts/check_songbook.py <file_or_dir> [--tail <tail.tex>] [-q]

Examples:
    python scripts/check_songbook.py nezboznej/songs/Přítel.txt
    python scripts/check_songbook.py nezboznej/songs/ --tail nezboznej/tail.tex
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------------------
# Individual checks.  Each takes [(line_num, line_text)] and returns issues.
# ---------------------------------------------------------------------------

def check_bad_apostrophes(lines):
    """Acute accent (´) or prime (′) used instead of apostrophe (').

    NOTE: requires human judgement -- the character may be a mistyped
    Czech diacritic (e.g. 't´' intended as 'ť') rather than a wrong
    apostrophe. Do not auto-fix.
    """
    issues = []
    for num, line in lines:
        for ch in ("\u00b4", "\u2032"):
            if ch in line:
                issues.append((num, f"Possible bad apostrophe '{ch}' -- or mistyped diacritic? (check manually)", line))
    return issues


def check_literal_ellipses(lines):
    """Literal ellipsis character instead of three dots."""
    issues = []
    for num, line in lines:
        if "\u2026" in line:
            issues.append((num, "Literal ellipsis '\u2026' (use '...' instead)", line))
    return issues


def check_asterisks(lines):
    issues = []
    for num, line in lines:
        if "*" in line and not line.strip().startswith("%"):
            issues.append((num, "Asterisk '*' in text", line))
    return issues


def check_dashes(lines):
    """Em-dashes, en-dashes, or double hyphens."""
    issues = []
    for num, line in lines:
        if "\u2014" in line or "\u2013" in line:
            issues.append((num, "Dash character in text", line))
        elif "--" in line and not line.strip().startswith("%"):
            issues.append((num, "Double hyphen '--'", line))
    return issues


def check_chords_at_line_end(lines):
    """Chord glued to text at line end (consecutive chords and post-period chords are OK)."""
    pat = re.compile(r"[^\s).]\([^)]+\)$")
    issues = []
    for num, line in lines:
        stripped = line.rstrip()
        if pat.search(stripped):
            issues.append((num, "Chord at end of line without preceding space", line))
    return issues


def check_bad_comma(lines):
    pat = re.compile(r",(?![ \}\(\t\r\n$]|$)")
    issues = []
    for num, line in lines:
        if line.strip().startswith("%"):
            continue
        if pat.search(line):
            issues.append((num, "Bad comma spacing", line))
    return issues


def check_header_special_chars(lines):
    pat = re.compile(
        r"^(?:N|A):.*[^a-zA-Z0-9 \u00e1\u00c1\u010d\u010c\u010f\u010e"
        r"\u00e9\u00c9\u011b\u011a\u00ed\u00cd\u0148\u0147\u00f3\u00d3"
        r"\u0159\u0158\u0161\u0160\u0165\u0164\u00fa\u00da\u016f\u016e"
        r"\u00fd\u00dd\u017e\u017d"
        r"\u013a\u0139\u013e\u013d\u0155\u0154\u00f4\u00d4"  # Slovak: ĺĹľĽŕŔôÔ
        r",.\-\\\{\}?!\r\n]"
    )
    issues = []
    for num, line in lines:
        if pat.match(line):
            issues.append((num, "Special chars in header (N:/A:)", line))
    return issues


def check_lowercase_chord_start(lines):
    pat = re.compile(r"\([a-z]")
    issues = []
    for num, line in lines:
        if any(line.strip().startswith(p) for p in ("Z:", "AC:", "ZC:", "%")):
            continue
        if pat.search(line):
            issues.append((num, "Lowercase chord start (e.g. (c) instead of (C))", line))
    return issues


def check_verse_label_dot(lines):
    pat = re.compile(r"^\d+\.")
    issues = []
    for num, line in lines:
        if pat.match(line.strip()):
            issues.append((num, "Verse label uses '.' instead of ':' (e.g. '1.' -> '1:')", line))
    return issues


def check_broken_repetitions(lines):
    pat = re.compile(r"(?:/:(?! )|(?<! ):/)")
    issues = []
    for num, line in lines:
        if pat.search(line):
            issues.append((num, "Broken repetition mark (missing space around /: or :/)", line))
    return issues


def check_multiply_sign(lines):
    pat = re.compile(r"\b\d+x\b")
    issues = []
    for num, line in lines:
        if pat.search(line):
            issues.append((num, "Use '\u00d7' instead of 'x' for repeat count", line))
    return issues


def check_broken_ellipses(lines):
    pat2 = re.compile(r"(?<!\.)\.\.(?!\.)")
    pat4 = re.compile(r"\.{4,}")
    issues = []
    for num, line in lines:
        if pat2.search(line):
            issues.append((num, "Two dots '..' (should be '...'?)", line))
        if pat4.search(line):
            issues.append((num, "Four or more dots (should be '...'?)", line))
    return issues


def check_unclosed_chords(lines):
    issues = []
    for num, line in lines:
        if line.count("(") > line.count(")"):
            issues.append((num, "Unclosed parenthesis (more '(' than ')')", line))
    return issues


def check_sus_chords(lines):
    """Chords using 'sus' notation (e.g. Esus4 should be E4)."""
    pat = re.compile(r"\([A-G][^)]*?sus[^)]*\)")
    issues = []
    for num, line in lines:
        for m in pat.finditer(line):
            issues.append((num, f"'sus' chord (use E4 not Esus4): {m.group()}", line))
    return issues


def check_mi_chords(lines):
    """Chords using 'mi' notation (e.g. Ami should be Am)."""
    pat = re.compile(r"\([A-G][\"b]?mi[^)]*\)")
    issues = []
    for num, line in lines:
        for m in pat.finditer(line):
            issues.append((num, f"'mi' chord (use Am not Ami): {m.group()}", line))
    return issues


def check_author_with_and(lines):
    """Author line using 'a' (Czech 'and') instead of comma to separate authors."""
    pat = re.compile(r"^A:.* a ", re.MULTILINE)
    issues = []
    for num, line in lines:
        if pat.match(line):
            issues.append((num, "Authors joined with 'a' instead of ','", line))
    return issues


def check_empty_author(lines):
    """Author line that is blank or whitespace-only."""
    pat = re.compile(r"^A:[ \t]*$")
    issues = []
    for num, line in lines:
        if pat.match(line):
            issues.append((num, "Empty author field", line))
    return issues


ALL_CHECKS = [
    ("Bad apostrophes", check_bad_apostrophes),
    ("Literal ellipses", check_literal_ellipses),
    ("Asterisks", check_asterisks),
    ("Dashes", check_dashes),
    ("Chords at line end", check_chords_at_line_end),
    ("Bad comma spacing", check_bad_comma),
    ("Special chars in headers", check_header_special_chars),
    ("Lowercase chord start", check_lowercase_chord_start),
    ("Verse label with dot", check_verse_label_dot),
    ("Broken repetitions", check_broken_repetitions),
    ("Multiply sign (x vs \u00d7)", check_multiply_sign),
    ("Broken ellipses", check_broken_ellipses),
    ("Unclosed chord parens", check_unclosed_chords),
    ("'sus' chords", check_sus_chords),
    ("'mi' chords", check_mi_chords),
    ("Author with 'a'", check_author_with_and),
    ("Empty author", check_empty_author),
]


# ---------------------------------------------------------------------------
# Chord diagram coverage analysis
# ---------------------------------------------------------------------------

def load_known_chords_from_tail(tail_path):
    known = set()
    with open(tail_path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\\chdig\{([^}]*)\}", line.strip())
            if m:
                chord = m.group(1).strip()
                if chord:
                    known.add(chord)
    return known


def extract_chords_from_line(line):
    chords = []
    for match in re.findall(r"\((.*?)\)", line):
        parts = match.strip().split()
        chords.extend(parts)
    return chords


def chord_coverage(all_lines, tail_path):
    known = load_known_chords_from_tail(tail_path)
    unknown_counter = Counter()
    used = set()

    for _num, line in all_lines:
        stripped = line.strip()
        if any(stripped.startswith(p) for p in ("Z:", "AC:", "ZC:", "%")):
            continue
        for chord in extract_chords_from_line(line):
            if chord in known:
                used.add(chord)
            else:
                unknown_counter[chord] += 1

    unused = sorted(known - used)
    return unknown_counter, unused


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

def run_checks_on_file(path, quiet=False):
    text = path.read_text(encoding="utf-8")
    numbered_lines = list(enumerate(text.splitlines(), 1))
    total = 0
    output = []

    for check_name, check_fn in ALL_CHECKS:
        issues = check_fn(numbered_lines)
        if issues:
            output.append(f"  {check_name}: {len(issues)} issue(s)")
            if not quiet:
                for line_num, msg, line_text in issues:
                    output.append(f"    L{line_num}: {msg}")
                    output.append(f"      | {line_text.rstrip()}")
            total += len(issues)

    return total, numbered_lines, output


def main():
    parser = argparse.ArgumentParser(
        description="Quality-check songbook input file(s).",
        epilog="Accepts a single file or a directory of .txt files.",
    )
    parser.add_argument("input", help="Path to a song file or directory of song files")
    parser.add_argument("--tail", help="Path to tail.tex for chord diagram coverage")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only show summary counts")
    args = parser.parse_args()

    files = collect_files(args.input)
    if not files:
        print(f"No .txt files found in {args.input}")
        return 1

    print(f"Checking {len(files)} file(s) in {args.input}")

    grand_total = 0
    all_lines = []

    for f in files:
        count, lines, output = run_checks_on_file(f, quiet=args.quiet)
        if count:
            if len(files) > 1:
                print(f"\n  {f.name}:")
            print("\n".join(output))
        grand_total += count
        all_lines.extend(lines)

    if args.tail:
        unknown, unused = chord_coverage(all_lines, args.tail)
        if unknown:
            print(f"\n{'='*60}")
            print(f"  Unknown chords (not in tail.tex): {len(unknown)} unique")
            print(f"{'='*60}")
            for chord, count in unknown.most_common():
                print(f"    {chord}: {count} occurrence(s)")
            grand_total += len(unknown)
        if unused:
            print(f"\n{'='*60}")
            print(f"  Unused chord diagrams (in tail.tex but not in songs): {len(unused)}")
            print(f"{'='*60}")
            if not args.quiet:
                for chord in unused:
                    print(f"    {chord}")

    print(f"\n--- Total: {grand_total} issue(s) across {len(files)} file(s) ---")
    return 1 if grand_total > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
