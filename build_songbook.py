import argparse
import re
import shutil
import subprocess
import locale
from pathlib import Path
import platform
from functools import cmp_to_key


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


SONG_SEPARATOR = "=" * 18


def czech_compare(a, b):
    return locale.strcoll(a, b)


# ---------------------------------------------------------------------------
# Legacy: monolithic input file support (fallback when --edition not given)
# ---------------------------------------------------------------------------

def parse_songs_from_file(file_path):
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Warning: Skipping {file_path} (not valid UTF-8)")
        return []

    entries = [e.strip() for e in content.split(SONG_SEPARATOR) if e.strip()]
    songs = []
    for entry in entries:
        lines = entry.splitlines()
        title_line = next((line for line in lines if line.startswith("N:")), None)
        if not title_line:
            continue
        title = title_line[2:].strip()
        songs.append((title, entry.strip() + "\n"))
    return songs


def collect_all_songs(input_dir):
    songs = []
    for ext in ("*.sng", "*.src", "*.txt"):
        for file_path in Path(input_dir).glob(ext):
            songs += parse_songs_from_file(file_path)
    return songs


# ---------------------------------------------------------------------------
# New: manifest-based collection from individual song files
# ---------------------------------------------------------------------------

def _load_song_dir(directory):
    """Read all .txt files from a directory, return {title: content} dict."""
    pool = {}
    if not directory.exists():
        return pool
    for txt in sorted(directory.glob("*.txt")):
        content = txt.read_text(encoding="utf-8").strip()
        title_line = next(
            (l for l in content.splitlines() if l.startswith("N:")), None
        )
        if title_line is None:
            continue
        title = title_line[2:].strip()
        pool[title] = content + "\n"
    return pool


def collect_songs_from_edition(variant_dir, edition):
    """Collect songs for a specific edition using songlist + songs/ + overrides/."""
    songlist_path = variant_dir / "songlists" / f"{edition}.txt"
    if not songlist_path.exists():
        raise SystemExit(f"Songlist not found: {songlist_path}")

    titles = [l.strip() for l in songlist_path.read_text(encoding="utf-8").splitlines()
              if l.strip()]
    song_pool = _load_song_dir(variant_dir / "songs")
    override_pool = _load_song_dir(variant_dir / "overrides")

    songs = []
    matched_overrides = set()

    for title in titles:
        if title in override_pool:
            songs.append((title, override_pool[title]))
            matched_overrides.add(title)
        elif title in song_pool:
            songs.append((title, song_pool[title]))
        else:
            print(f"Warning: Song not found: '{title}'")

    unmatched = [t for t in override_pool if t not in matched_overrides]
    if unmatched:
        print(f"Note: {len(unmatched)} override(s) not referenced by songlist "
              f"(ignored): {unmatched}")

    print(f"Collected {len(songs)} songs from songlist "
          f"({len(matched_overrides)} using overrides)")
    return songs


def write_output_files(songs, build_dir):
    songs_dir = build_dir / "songs"
    songs_dir.mkdir(parents=True, exist_ok=True)

    sorted_songs = sorted(songs, key=cmp_to_key(lambda a, b: czech_compare(a[0], b[0])))

    src_path = build_dir / "songbook.src.txt"
    with open(src_path, "w", encoding="utf-8") as src_file:
        for idx, (title, content) in enumerate(sorted_songs, 1):
            safe_title = re.sub(r"[^\w\-]", "_", title, flags=re.UNICODE)
            safe_title = re.sub(r"_+", "_", safe_title).strip("_")
            filename = f"{idx:03d}_{safe_title}.sng"
            song_path = songs_dir / filename
            with open(song_path, "w", encoding="utf-8") as song_file:
                song_file.write(content)
            src_file.write(content + "\n" + SONG_SEPARATOR + "\n\n")


def create_tex_files(variant, build_dir):
    """Generate songbook.tex (trivial \\input wrapper) and songlist.tex (song entries)."""
    songbook_tex = build_dir / "songbook.tex"
    songlist_tex = build_dir / "songlist.tex"

    songbook_tex.write_text(
        "\\input ../head.tex\n"
        "\\input songlist.tex\n"
        "\\input ../tail.tex\n",
        encoding="utf-8",
    )

    with open(songlist_tex, "w", encoding="utf-8") as out:
        for song_file in sorted((build_dir / "songs").glob("*.sng")):
            rel_path = song_file.relative_to(build_dir).as_posix()
            out.write(f"\\inputsong{{{rel_path}}}\n")


def compile_pdf(build_dir):
    subprocess.run(
        ["luatex", "-fmt", "pdfcsplain", "--interaction=nonstopmode", "songbook.tex"],
        cwd=build_dir, check=True,
    )

def create_duplex_pdf(pdf_path: Path, output_path: Path):
    # zpev-duplex.pdf : zpevnik.pdf
    # 	 pdftops zpevnik.pdf zpevnik.ps
    # 	 #pstops -pa4 '2:-1L(29.7cm,0cm)+0L(29.7cm,14.85cm),1L(29.7cm,0cm)+-0L(29.7cm,14.85cm)' zpevnik.ps zpev-duplex.ps
    # 	 pstops -pa4 '2:-1L(21cm,0cm)+0L(21cm,14.85cm),1L(21cm,0cm)+-0L(21cm,14.85cm)' zpevnik.ps zpev-duplex.ps
    # 	 ps2pdf zpev-duplex.ps zpevnik-duplex.pdf
    # 	 #pdfjam zpevnik.pdf --nup 2x1 --landscape --paper a4paper --outfile zpev-duplex.pdf
    
    ps_path = pdf_path.with_suffix('.ps')
    duplex_ps = output_path.with_suffix('.ps')
    duplex_pdf = output_path.with_suffix('.pdf')

    # Step 1: Convert PDF to PS
    subprocess.run(['pdftops', str(pdf_path), str(ps_path)], check=True)

    # Step 2: Rearrange pages into A5-imposed duplex layout on A4
    # Note: 21cm wide page, 14.85cm tall half-page
    pstops_expr = (
        "2:-1L(21cm,0cm)+0L(21cm,14.85cm),"
        "1L(21cm,0cm)+-0L(21cm,14.85cm)"
    )
    subprocess.run(['pstops', '-pa4', pstops_expr, str(ps_path), str(duplex_ps)], check=True)

    # Step 3: Convert rearranged PS back to final PDF
    subprocess.run(['ps2pdf', "-sPAPERSIZE=a4", str(duplex_ps), str(duplex_pdf)], check=True)


def clean(build_dir):
    shutil.rmtree(build_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(
        description="Build songbook PDF from source files."
    )
    parser.add_argument(
        "--variant", required=True, help="Variant name (e.g. zboznej, nezboznej)"
    )
    parser.add_argument(
        "--edition",
        help="Edition year (e.g. 2025, 2026). "
             "Reads {variant}/songlists/{edition}.txt as manifest and "
             "collects songs from {variant}/songs/ and {variant}/overrides/. "
             "Omit to fall back to legacy monolithic input files.",
    )
    parser.add_argument(
        "--target",
        choices=["build", "clean", "rebuild", "songs", "duplex", "buildwithindex", "all", "test", "retest", "testwithindex"],
        default="build",
        help="Build target",
    )

    args = parser.parse_args()
    variant_dir = Path(args.variant)
    input_dir = variant_dir / "input"
    build_dir = variant_dir / "build"
    args.target = args.target.lower()

    if "test" in args.target:
        input_dir = input_dir.with_name(input_dir.name + "_test")
        build_dir = build_dir.with_name(build_dir.name + "_test")

    if args.target in ["clean", "rebuild", "all", "retest"]:
        clean(build_dir)

    set_czech_locale()
    if args.target in ["rebuild", "songs", "all", "retest"]:
        if args.edition:
            songs = collect_songs_from_edition(variant_dir, args.edition)
        else:
            songs = collect_all_songs(input_dir)
        write_output_files(songs, build_dir)
        create_tex_files(args.variant, build_dir)


    if args.target in ["buildwithindex", "build", "rebuild", "all", "test", "testwithindex", "retest"]:
        compile_pdf(build_dir)

    if args.target in ["buildwithindex", "testwithindex", "all"]:
        compile_pdf(build_dir)

    if args.target in ["duplex", "all"]:
        create_duplex_pdf(
            build_dir / "songbook.pdf",
            build_dir / f"{args.variant}_duplex.pdf"
        )

if __name__ == "__main__":
    main()
