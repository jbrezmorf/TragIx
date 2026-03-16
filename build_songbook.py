"""
Build a songbook PDF from individual song source files.

Usage (auto-detects Docker if luatex is not available locally):

    python build_songbook.py --variant nezboznej --edition 2025
    python build_songbook.py --variant nezboznej --edition 2025 --duplex
    python build_songbook.py --variant nezboznej --edition 2025 --clean
    python build_songbook.py --variant nezboznej --edition 2025 --songs-only
"""

import argparse
import locale
import platform
import re
import shutil
import subprocess
import sys
from functools import cmp_to_key
from pathlib import Path


# ---------------------------------------------------------------------------
# Locale
# ---------------------------------------------------------------------------

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
        print("Warning: Czech locale not available. Sorting may not be correct.")
        locale.setlocale(locale.LC_COLLATE, "")


def czech_compare(a, b):
    return locale.strcoll(a, b)


# ---------------------------------------------------------------------------
# Song collection
# ---------------------------------------------------------------------------

def _parse_header_field(content, field):
    """Extract a header field value from song content (e.g. 'N:', 'E:')."""
    for line in content.splitlines():
        if line.startswith(field):
            return line[len(field):].strip()
    return None


def _load_song_dir(directory):
    """Read all .txt files from a directory, return {title: content} dict."""
    pool = {}
    if not directory.exists():
        return pool
    for txt in sorted(directory.glob("*.txt")):
        content = txt.read_text(encoding="utf-8").strip()
        title = _parse_header_field(content, "N:")
        if title is None:
            continue
        pool[title] = content + "\n"
    return pool


def collect_songs(variant_dir, edition):
    """Collect songs whose E: header includes the requested edition year.

    Override files from overrides/ take precedence over songs/ when both
    exist for the same title.
    """
    songs_dir = variant_dir / "songs"
    if not songs_dir.exists():
        raise SystemExit(f"Songs directory not found: {songs_dir}")

    override_pool = _load_song_dir(variant_dir / "overrides")
    songs = []
    matched_overrides = set()

    for txt in sorted(songs_dir.glob("*.txt")):
        content = txt.read_text(encoding="utf-8").strip()
        title = _parse_header_field(content, "N:")
        if title is None:
            continue

        editions_raw = _parse_header_field(content, "E:")
        if not editions_raw:
            continue
        editions = {e.strip() for e in editions_raw.split(",")}
        if edition not in editions:
            continue

        if title in override_pool:
            songs.append((title, override_pool[title]))
            matched_overrides.add(title)
        else:
            songs.append((title, content + "\n"))

    unmatched = [t for t in override_pool if t not in matched_overrides]
    if unmatched:
        print(f"  Note: {len(unmatched)} override(s) not in edition (ignored): {unmatched}")

    print(f"  {len(songs)} songs collected ({len(matched_overrides)} using overrides)")
    return songs


# ---------------------------------------------------------------------------
# Build preparation
# ---------------------------------------------------------------------------

def prepare_build(songs, variant, build_dir):
    """Sort songs, write .sng files, songbook.tex, songlist.tex, and
    a convenience songlist_titles.txt into the build directory."""
    set_czech_locale()
    sorted_songs = sorted(songs, key=cmp_to_key(lambda a, b: czech_compare(a[0], b[0])))

    songs_dir = build_dir / "songs"
    songs_dir.mkdir(parents=True, exist_ok=True)

    src_path = build_dir / "songbook.src.txt"
    songlist_titles = build_dir / "songlist_titles.txt"
    separator = "=" * 18

    with (
        open(src_path, "w", encoding="utf-8") as src_file,
        open(songlist_titles, "w", encoding="utf-8") as titles_file,
    ):
        for idx, (title, content) in enumerate(sorted_songs, 1):
            safe_title = re.sub(r"[^\w\-]", "_", title, flags=re.UNICODE)
            safe_title = re.sub(r"_+", "_", safe_title).strip("_")
            filename = f"{idx:03d}_{safe_title}.sng"
            (songs_dir / filename).write_text(content, encoding="utf-8")
            src_file.write(content + "\n" + separator + "\n\n")
            titles_file.write(title + "\n")

    songbook_tex = build_dir / "songbook.tex"
    songbook_tex.write_text(
        "\\input ../head.tex\n"
        "\\input songlist.tex\n"
        "\\input ../tail.tex\n",
        encoding="utf-8",
    )

    songlist_tex = build_dir / "songlist.tex"
    with open(songlist_tex, "w", encoding="utf-8") as out:
        for sng in sorted((build_dir / "songs").glob("*.sng")):
            rel = sng.relative_to(build_dir).as_posix()
            out.write(f"\\inputsong{{{rel}}}\n")

    print(f"  Build files written to {build_dir}/")


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------

def compile_pdf(build_dir, passes=2):
    """Run luatex the specified number of times (2 = with index)."""
    cmd = ["luatex", "-fmt", "pdfcsplain", "--interaction=nonstopmode", "songbook.tex"]
    for i in range(1, passes + 1):
        label = f"pass {i}/{passes}" if passes > 1 else "single pass"
        print(f"  Compiling ({label})...")
        result = subprocess.run(cmd, cwd=build_dir, capture_output=True, text=True)
        if result.returncode != 0:
            errors = [l for l in result.stdout.splitlines() if l.startswith("!")]
            if errors:
                print(f"  TeX errors:")
                for e in errors:
                    print(f"    {e}")
            raise SystemExit(f"luatex failed on {label} (exit {result.returncode})")

    pdf = build_dir / "songbook.pdf"
    size_kb = pdf.stat().st_size // 1024
    print(f"  Output: {pdf} ({size_kb} KB)")


def create_duplex(build_dir, variant):
    """Create an A5-imposed duplex PDF on A4 for print-shop delivery."""
    pdf = build_dir / "songbook.pdf"
    ps = pdf.with_suffix(".ps")
    duplex_ps = build_dir / f"{variant}_duplex.ps"
    duplex_pdf = build_dir / f"{variant}_duplex.pdf"

    print("  Creating duplex PDF...")
    subprocess.run(["pdftops", str(pdf), str(ps)], check=True)

    pstops_expr = (
        "2:-1L(21cm,0cm)+0L(21cm,14.85cm),"
        "1L(21cm,0cm)+-0L(21cm,14.85cm)"
    )
    subprocess.run(["pstops", "-pa4", pstops_expr, str(ps), str(duplex_ps)], check=True)
    subprocess.run(["ps2pdf", "-sPAPERSIZE=a4", str(duplex_ps), str(duplex_pdf)], check=True)

    size_kb = duplex_pdf.stat().st_size // 1024
    print(f"  Output: {duplex_pdf} ({size_kb} KB)")


# ---------------------------------------------------------------------------
# Docker self-bootstrapping
# ---------------------------------------------------------------------------

def docker_run(args):
    """Re-invoke this script inside a Docker container with the correct
    volume mount so build output lands on the host filesystem."""
    image = "tragix-songbook"

    print(f"[docker] Building image '{image}'...")
    subprocess.run(["docker", "build", "-t", image, "."], check=True)

    build_mount = f"{Path.cwd().as_posix()}/{args.variant}/build:/songbook/{args.variant}/build"

    cmd = [
        "docker", "run", "--rm",
        "-v", build_mount,
        image,
    ]
    cmd += sys.argv[1:]

    print(f"[docker] Running build inside container...")
    result = subprocess.run(cmd)
    raise SystemExit(result.returncode)


# ---------------------------------------------------------------------------
# CLI and main
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Build a songbook PDF from song source files.",
        epilog="If luatex is not found locally, the build runs inside Docker automatically.",
    )
    parser.add_argument(
        "--variant", required=True,
        help="Variant name (nezboznej or zboznej)",
    )
    parser.add_argument(
        "--edition", required=True,
        help="Edition year (e.g. 2025). Selects songs whose E: header includes this year.",
    )
    parser.add_argument(
        "--duplex", action="store_true",
        help="Also produce an A5-on-A4 duplex PDF for print-shop delivery.",
    )
    parser.add_argument(
        "--clean", action="store_true",
        help="Only clean the build directory, then exit.",
    )
    parser.add_argument(
        "--songs-only", action="store_true",
        help="Collect and write song files but do not compile the PDF.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    variant_dir = Path(args.variant)
    build_dir = variant_dir / "build"

    if not shutil.which("luatex") and not args.clean and not args.songs_only:
        docker_run(args)
        return

    # -- Clean ---------------------------------------------------------------
    if build_dir.exists():
        print(f"Cleaning {build_dir}/...")
        shutil.rmtree(build_dir, ignore_errors=True)

    if args.clean:
        print("Done.")
        return

    # -- Collect songs -------------------------------------------------------
    print(f"Collecting songs for {args.variant} edition {args.edition}...")
    songs = collect_songs(variant_dir, args.edition)
    if not songs:
        raise SystemExit("No songs matched -- check E: headers in song files.")

    # -- Prepare build files -------------------------------------------------
    print("Preparing build files...")
    prepare_build(songs, args.variant, build_dir)

    if args.songs_only:
        print("Done (--songs-only).")
        return

    # -- Compile PDF ---------------------------------------------------------
    print("Compiling PDF...")
    compile_pdf(build_dir, passes=2)

    # -- Duplex (optional) ---------------------------------------------------
    if args.duplex:
        create_duplex(build_dir, args.variant)

    print("Done.")


if __name__ == "__main__":
    main()
