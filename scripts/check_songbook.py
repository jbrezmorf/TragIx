"""
Quality-check (and optionally auto-fix) songbook input files.

Runs format checks, chord convention checks, and optionally chord
diagram coverage analysis.  Deterministic issues can be auto-fixed
with --fix.

Usage:
    python scripts/check_songbook.py nezboznej/songs/
    python scripts/check_songbook.py nezboznej/songs/ --fix
    python scripts/check_songbook.py nezboznej/songs/ --fix --dry-run
    python scripts/check_songbook.py nezboznej/songs/ --edition 2025
    python scripts/check_songbook.py nezboznej/songs/ --tail nezboznej/tail.tex
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

SONG_SEPARATOR = "=" * 18


# ===================================================================
# Auto-fixers.  Each takes full file text, returns (new_text, count).
# ===================================================================

def fix_separators(text):
    """Normalize all song separator lines to exactly 18 '=' signs."""
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
    r"""Replace quotation mark characters with \uv{...}, per-line.
    Skips chords (inside parentheses).  Lines with an odd number of
    quote chars are left untouched (warning printed)."""
    quote_chars = {'"', "\u201c", "\u201d", "\u201e"}
    lines = text.split("\n")
    result_lines = []
    total_pairs = 0
    warnings = []

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

        positions = [
            i for i, c in enumerate(line) if c in quote_chars and not inside_parens(i)
        ]

        if len(positions) % 2 != 0:
            warnings.append(f"    [quotations] odd quotes on L{line_num}, skipped")
            result_lines.append(line)
            continue

        if not positions:
            result_lines.append(line)
            continue

        built = []
        prev = 0
        for pair_idx in range(0, len(positions), 2):
            op, cl = positions[pair_idx], positions[pair_idx + 1]
            built.append(line[prev:op])
            built.append("\\uv{")
            built.append(line[op + 1 : cl])
            built.append("}")
            prev = cl + 1
            total_pairs += 1
        built.append(line[prev:])
        result_lines.append("".join(built))

    return "\n".join(result_lines), total_pairs, warnings


def fix_ellipses(text):
    """Replace literal ellipsis character with three dots."""
    count = text.count("\u2026")
    return text.replace("\u2026", "..."), count


def fix_multiply_sign(text):
    """Replace Nx with N\u00d7 for repeat counts (e.g. 3x -> 3\u00d7)."""
    pat = re.compile(r"\b(\d+)x\b")
    new_text, count = pat.subn(lambda m: m.group(1) + "\u00d7", text)
    return new_text, count


def fix_verse_dots(text):
    """Replace verse labels using '.' with ':' (e.g. '1.' -> '1:')."""
    pat = re.compile(r"^(\d+)\.", re.MULTILINE)
    new_text, count = pat.subn(r"\1:", text)
    return new_text, count


def fix_sus_chords(text):
    """Replace sus notation: (Esus4) -> (E4), etc."""
    pat = re.compile(r"\(([A-G][\"b]?)sus(\d[^)]*)\)")
    new_text, count = pat.subn(r"(\1\2)", text)
    return new_text, count


def fix_mi_chords(text):
    """Replace mi notation: (Ami) -> (Am), (Emi7) -> (Em7), etc."""
    pat = re.compile(r"\(([A-G][\"b]?)mi([^)]*)\)")
    new_text, count = pat.subn(r"(\1m\2)", text)
    return new_text, count


def fix_missing_k_field(text):
    """Insert an empty K: line after E: if the header is missing one."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("E:"):
            if i + 1 < len(lines) and lines[i + 1].startswith("K:"):
                return text, 0
            lines.insert(i + 1, "K:")
            return "\n".join(lines) + "\n", 1
    return text, 0


ALL_FIXES = [
    ("separators", "Normalize song separators", fix_separators),
    ("quotations", "Replace quote chars with \\uv{...}", fix_quotations),
    ("ellipses", "Replace literal ellipsis with '...'", fix_ellipses),
    ("multiply", "Replace Nx with N\u00d7", fix_multiply_sign),
    ("verse-dots", "Replace '1.' with '1:'", fix_verse_dots),
    ("sus-chords", "Replace (Esus4) with (E4)", fix_sus_chords),
    ("mi-chords", "Replace (Ami) with (Am)", fix_mi_chords),
    ("k-field", "Add missing K: header field", fix_missing_k_field),
]


# ===================================================================
# Checks.  Each takes [(line_num, line_text)], returns issue tuples.
# ===================================================================

def check_bad_apostrophes(lines):
    """Acute accent or prime used instead of apostrophe.
    NOTE: may be a mistyped Czech diacritic -- requires manual review."""
    issues = []
    for num, line in lines:
        for ch in ("\u00b4", "\u2032"):
            if ch in line:
                issues.append((num, f"Possible bad apostrophe '{ch}' (or mistyped diacritic?)", line))
    return issues


def check_literal_ellipses(lines):
    issues = []
    for num, line in lines:
        if "\u2026" in line:
            issues.append((num, "Literal ellipsis '\u2026' (use '...')", line))
    return issues


def check_asterisks(lines):
    issues = []
    for num, line in lines:
        if "*" in line and not line.strip().startswith("%"):
            issues.append((num, "Asterisk '*' in text", line))
    return issues


def check_dashes(lines):
    issues = []
    for num, line in lines:
        if "\u2014" in line or "\u2013" in line:
            issues.append((num, "Dash character in text", line))
        elif "--" in line and not line.strip().startswith("%"):
            issues.append((num, "Double hyphen '--'", line))
    return issues


def check_chords_at_line_end(lines):
    pat = re.compile(r"[^\s).]\([^)]+\)$")
    issues = []
    for num, line in lines:
        if pat.search(line.rstrip()):
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
        r"\u013a\u0139\u013e\u013d\u0155\u0154\u00f4\u00d4"
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
        if any(line.strip().startswith(p) for p in ("Z:", "AC:", "ZC:", "K:", "%")):
            continue
        if pat.search(line):
            issues.append((num, "Lowercase chord start", line))
    return issues


def check_broken_repetitions(lines):
    pat = re.compile(r"(?:/:(?! )|(?<! ):/)")
    issues = []
    for num, line in lines:
        if pat.search(line):
            issues.append((num, "Broken repetition mark (missing space around /: or :/)", line))
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
            issues.append((num, "Unclosed parenthesis", line))
    return issues


def check_author_with_and(lines):
    pat = re.compile(r"^A:.* a ", re.MULTILINE)
    issues = []
    for num, line in lines:
        if pat.match(line):
            issues.append((num, "Authors joined with 'a' instead of ','", line))
    return issues


def check_empty_author(lines):
    pat = re.compile(r"^A:[ \t]*$")
    issues = []
    for num, line in lines:
        if pat.match(line):
            issues.append((num, "Empty author field", line))
    return issues


def check_missing_k_field(lines):
    """K: header line must be present (after E:)."""
    has_e = any(line.startswith("E:") for _, line in lines)
    has_k = any(line.startswith("K:") for _, line in lines)
    if has_e and not has_k:
        return [(1, "Missing K: header field (run --fix to add)", "")]
    return []


ALL_CHECKS = [
    ("Bad apostrophes", check_bad_apostrophes),
    ("Literal ellipses", check_literal_ellipses),
    ("Asterisks", check_asterisks),
    ("Dashes", check_dashes),
    ("Chords at line end", check_chords_at_line_end),
    ("Bad comma spacing", check_bad_comma),
    ("Special chars in headers", check_header_special_chars),
    ("Lowercase chord start", check_lowercase_chord_start),
    ("Broken repetitions", check_broken_repetitions),
    ("Broken ellipses", check_broken_ellipses),
    ("Unclosed chord parens", check_unclosed_chords),
    ("Author with 'a'", check_author_with_and),
    ("Empty author", check_empty_author),
    ("Missing K: field", check_missing_k_field),
]


# ===================================================================
# Chord diagram coverage
# ===================================================================

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
        if any(stripped.startswith(p) for p in ("Z:", "AC:", "ZC:", "K:", "%")):
            continue
        for chord in extract_chords_from_line(line):
            if chord in known:
                used.add(chord)
            else:
                unknown_counter[chord] += 1
    return unknown_counter, sorted(known - used)


# ===================================================================
# File collection
# ===================================================================

def collect_files(path, edition=None):
    p = Path(path)
    files = sorted(p.glob("*.txt")) if p.is_dir() else [p]
    if edition and len(files) > 1:
        files = [f for f in files if _file_has_edition(f, edition)]
    return files


def _file_has_edition(path, edition):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("E:"):
            return edition in {e.strip() for e in line[2:].split(",")}
    return False


# ===================================================================
# Per-file processing
# ===================================================================

def process_file(path, do_fix, dry_run, quiet):
    """Process one song file: run fixers, then checks.

    Returns (fix_count, check_count, numbered_lines_after_fix).
    Only prints output for files that have something to report.
    """
    text = path.read_text(encoding="utf-8")
    original = text

    fix_output = []
    fix_count = 0
    fix_warnings = []

    for name, description, fn in ALL_FIXES:
        result = fn(text)
        if len(result) == 3:
            text, count, warnings = result
            fix_warnings.extend(warnings)
        else:
            text, count = result
        if count:
            fix_output.append(f"    {name}: {count} -- {description}")
            fix_count += count

    if do_fix and not dry_run and text != original:
        path.write_text(text, encoding="utf-8")

    numbered_lines = list(enumerate(text.splitlines(), 1))
    check_output = []
    check_count = 0

    for check_name, check_fn in ALL_CHECKS:
        issues = check_fn(numbered_lines)
        if issues:
            check_output.append(f"    {check_name}: {len(issues)} issue(s)")
            if not quiet:
                for line_num, msg, line_text in issues:
                    check_output.append(f"      L{line_num}: {msg}")
                    check_output.append(f"        | {line_text.rstrip()}")
            check_count += len(issues)

    if fix_count or check_count:
        print(f"\n  {path.name}:")

    if fix_count:
        if do_fix and not dry_run:
            label = "fixed"
        elif do_fix:
            label = "would fix"
        else:
            label = "auto-fixable"
        print(f"  [{label}]")
        print("\n".join(fix_output))
        for w in fix_warnings:
            print(w)

    if check_count:
        print("\n".join(check_output))

    return fix_count, check_count, numbered_lines


# ===================================================================
# Main
# ===================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Quality-check songbook input file(s).",
        epilog=(
            "Without --fix, reports all issues (auto-fixable and manual). "
            "With --fix, applies safe auto-fixes and reports remaining issues."
        ),
    )
    parser.add_argument("input", help="Path to a song file or directory of song files")
    parser.add_argument("--edition", help="Only process songs whose E: header includes this year")
    parser.add_argument("--fix", action="store_true", help="Apply safe auto-fixes")
    parser.add_argument("--dry-run", action="store_true", help="With --fix: preview changes without writing")
    parser.add_argument("--tail", help="Path to tail.tex for chord diagram coverage")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only show summary counts")
    args = parser.parse_args()

    if args.dry_run and not args.fix:
        parser.error("--dry-run requires --fix")

    files = collect_files(args.input, edition=args.edition)
    if not files:
        print(f"No .txt files found in {args.input}")
        return 1

    label = f"{args.input} (edition {args.edition})" if args.edition else args.input
    mode = ""
    if args.fix:
        mode = " [fix --dry-run]" if args.dry_run else " [fix]"
    print(f"Checking {len(files)} file(s) in {label}{mode}")

    total_fixes = 0
    total_issues = 0
    all_lines = []

    for f in files:
        fc, cc, lines = process_file(f, args.fix, args.dry_run, args.quiet)
        total_fixes += fc
        total_issues += cc
        all_lines.extend(lines)

    if args.tail:
        unknown, unused = chord_coverage(all_lines, args.tail)
        if unknown:
            print(f"\n{'='*60}")
            print(f"  Unknown chords (not in tail.tex): {len(unknown)} unique")
            print(f"{'='*60}")
            for chord, count in unknown.most_common():
                print(f"    {chord}: {count} occurrence(s)")
            total_issues += len(unknown)
        if unused:
            print(f"\n{'='*60}")
            print(f"  Unused chord diagrams (in tail.tex but not in songs): {len(unused)}")
            print(f"{'='*60}")
            if not args.quiet:
                for chord in unused:
                    print(f"    {chord}")

    parts = []
    if total_fixes:
        if args.fix and not args.dry_run:
            parts.append(f"{total_fixes} auto-fixed")
        elif args.fix:
            parts.append(f"{total_fixes} would fix")
        else:
            parts.append(f"{total_fixes} auto-fixable")
    if total_issues:
        parts.append(f"{total_issues} issue(s)")
    summary = ", ".join(parts) if parts else "all clean"
    print(f"\n--- {summary} across {len(files)} file(s) ---")

    return 1 if total_issues > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
