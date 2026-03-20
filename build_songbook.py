"""
Build a songbook PDF from individual song source files.

Usage (auto-detects Docker if luatex is not available locally):

    python build_songbook.py --variant nezboznej --edition 2025
    python build_songbook.py --variant nezboznej --edition 2025 --duplex
    python build_songbook.py --variant nezboznej --edition 2025 --clean
    python build_songbook.py --variant nezboznej --edition 2025 --songs-only
    python build_songbook.py --all                 # build everything from current_editions.txt
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

def prepare_build(songs, variant, build_dir, version_string=""):
    """Sort songs, write .sng files, songbook.tex, songlist.tex,
    version.tex, and a convenience songlist_titles.txt into the build dir."""
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

    version_tex = build_dir / "version.tex"
    version_tex.write_text(
        f"\\def\\SongbookVersion{{{version_string}}}\n",
        encoding="utf-8",
    )

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


def create_duplex(build_dir, variant, version_string=""):
    """Create an A5-imposed duplex PDF on A4 for print-shop delivery."""
    pdf = build_dir / f"{variant}_{version_string}.pdf"
    ps = pdf.with_suffix(".ps")
    tag = f"{variant}_{version_string}" if version_string else variant
    duplex_ps = build_dir / f"{tag}_duplex.ps"
    duplex_pdf = build_dir / f"{tag}_duplex.pdf"

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

def _find_docker():
    """Return the path to the docker CLI, searching PATH and well-known
    install locations (Docker Desktop on Windows often isn't on PATH in
    IDE terminals)."""
    found = shutil.which("docker")
    if found:
        return found
    if platform.system() == "Windows":
        import os
        candidate = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"),
                                 "Docker", "Docker", "resources", "bin", "docker.exe")
        if os.path.isfile(candidate):
            return candidate
    raise SystemExit(
        "docker not found on PATH (and not in the default install location).\n"
        "Install Docker Desktop or add it to PATH."
    )


def docker_run(args):
    """Re-invoke this script inside a Docker container with the correct
    volume mount(s) so build output lands on the host filesystem."""
    docker = _find_docker()
    image = "tragix-songbook"

    print(f"[docker] Building image '{image}'...")
    subprocess.run([docker, "build", "-t", image, "."], check=True)

    cwd = Path.cwd().as_posix()
    cmd = [docker, "run", "--rm"]

    if args.all:
        for variant, _, _ in load_editions():
            cmd += ["-v", f"{cwd}/{variant}/build:/songbook/{variant}/build"]
    else:
        cmd += ["-v", f"{cwd}/{args.variant}/build:/songbook/{args.variant}/build"]

    cmd += [image] + sys.argv[1:]

    print(f"[docker] Running build inside container...")
    result = subprocess.run(cmd)
    raise SystemExit(result.returncode)


# ---------------------------------------------------------------------------
# CLI and main
# ---------------------------------------------------------------------------

EDITIONS_FILE = "current_editions.txt"


def load_editions():
    """Read active editions from current_editions.txt.

    Returns [(variant, edition, version), ...].
    """
    path = Path(EDITIONS_FILE)
    if not path.exists():
        raise SystemExit(f"{EDITIONS_FILE} not found.")
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 3:
            raise SystemExit(
                f"Bad line in {EDITIONS_FILE}: {line!r} "
                "(expected: variant edition version)"
            )
        entries.append(tuple(parts))
    return entries


def _lookup_version(variant, edition):
    """Find the version for a given variant+edition in the editions file."""
    for v, e, ver in load_editions():
        if v == variant and e == edition:
            return ver
    raise SystemExit(
        f"No entry for {variant} {edition} in {EDITIONS_FILE}."
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build a songbook PDF from song source files.",
        epilog="If luatex is not found locally, the build runs inside Docker automatically.",
    )
    parser.add_argument(
        "--variant",
        help="Variant name (nezboznej or zboznej). Required unless --all is used.",
    )
    parser.add_argument(
        "--edition",
        help="Edition year (e.g. 2025). Required unless --all is used.",
    )
    parser.add_argument(
        "--all", action="store_true",
        help=f"Build all editions listed in {EDITIONS_FILE}.",
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
    args = parser.parse_args()

    if not args.all and (not args.variant or not args.edition):
        parser.error("--variant and --edition are required (or use --all).")

    return args


def build_one(variant, edition, version="0", duplex=False, clean=False, songs_only=False):
    """Build a single variant+edition combination."""
    variant_dir = Path(variant)
    build_dir = variant_dir / "build"
    version_string = f"{edition}.{version}"

    # -- Clean ---------------------------------------------------------------
    if build_dir.exists():
        print(f"Cleaning {build_dir}/...")
        shutil.rmtree(build_dir, ignore_errors=True)

    if clean:
        print("Done.")
        return

    # -- Collect songs -------------------------------------------------------
    print(f"Collecting songs for {variant} edition {edition}...")
    songs = collect_songs(variant_dir, edition)
    if not songs:
        raise SystemExit("No songs matched -- check E: headers in song files.")

    # -- Prepare build files -------------------------------------------------
    print("Preparing build files...")
    prepare_build(songs, variant, build_dir, version_string)

    if songs_only:
        print("Done (--songs-only).")
        return

    # -- Compile PDF ---------------------------------------------------------
    print("Compiling PDF...")
    compile_pdf(build_dir, passes=2)

    # -- Rename output PDF ---------------------------------------------------
    raw_pdf = build_dir / "songbook.pdf"
    final_name = f"{variant}_{version_string}.pdf"
    final_pdf = build_dir / final_name
    raw_pdf.rename(final_pdf)
    print(f"  Renamed to {final_pdf}")

    # -- Duplex (optional) ---------------------------------------------------
    if duplex:
        create_duplex(build_dir, variant, version_string)

    print("Done.")


def main():
    args = parse_args()

    if args.all:
        editions = load_editions()
        if not shutil.which("luatex") and not args.clean and not args.songs_only:
            docker_run(args)
            return
        for variant, edition, version in editions:
            print(f"\n{'='*60}")
            print(f"  Building {variant} {edition}.{version}")
            print(f"{'='*60}\n")
            build_one(variant, edition, version, args.duplex, args.clean, args.songs_only)
    else:
        version = _lookup_version(args.variant, args.edition)
        if not shutil.which("luatex") and not args.clean and not args.songs_only:
            docker_run(args)
            return
        build_one(args.variant, args.edition, version, args.duplex, args.clean, args.songs_only)


if __name__ == "__main__":
    main()
