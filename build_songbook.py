import argparse
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
        locale.setlocale(locale.LC_COLLATE, "")  # System default fallback


SONG_SEPARATOR = "=" * 18


def czech_compare(a, b):
    return locale.strcoll(a, b)


def parse_songs_from_file(file_path):
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

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
    for file_path in list((input_dir).glob("*.txt")) + list(
        Path(input_dir).glob("*.src")
    ):
        songs += parse_songs_from_file(file_path)
    return songs


def write_output_files(songs, build_dir):
    songs_dir = build_dir / "songs"
    songs_dir.mkdir(parents=True, exist_ok=True)

    sorted_songs = sorted(songs, key=cmp_to_key(lambda a, b: czech_compare(a[0], b[0])))

    src_path = build_dir / "songbook.src.txt"
    with open(src_path, "w", encoding="utf-8") as src_file:
        for idx, (title, content) in enumerate(sorted_songs, 1):
            filename = f"{idx:03d}_{title.replace(' ', '_')}.sng"
            song_path = songs_dir / filename
            with open(song_path, "w", encoding="utf-8") as song_file:
                song_file.write(content)
            src_file.write(content + "\n" + SONG_SEPARATOR + "\n\n")


def create_combined_tex_file(variant, build_dir):
    variant_dir = Path(variant)
    head = variant_dir / "head.tex"
    tail = variant_dir / "tail.tex"
    src = build_dir / "songbook.src.txt"
    output_tex = build_dir / "songbook.tex"

    with open(output_tex, "w", encoding="utf-8") as out:
        with open(head, encoding="utf-8") as f:
            out.write(f.read())
            out.write("\n")

        for song_file in sorted((build_dir / "songs").glob("*.sng")):
            out.write(f"\\inputsong{{{Path("." + str(song_file).split(build_dir.name)[-1]).as_posix()}}}\n")

        with open(tail, encoding="utf-8") as f:
            out.write(f.read())
            out.write("\n")


def compile_pdf(build_dir):
    # luatex -fmt pdfcsplain songbook.tex --interaction=nonstopmode
    subprocess.run(["luatex", "-fmt", "pdfcsplain", "songbook.tex", "--interaction=nonstopmode"], cwd=build_dir, check=True)

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

    if  "test" in args.target:
        input_dir = input_dir.with_name(input_dir.name + "_test")
        build_dir = build_dir.with_name(build_dir.name + "_test")

    if args.target in ["clean", "rebuild", "all", "retest"]:
        clean(build_dir)

    set_czech_locale()
    if args.target in ["rebuild", "songs", "all", "retest"]:
        songs = collect_all_songs(input_dir)
        write_output_files(songs, build_dir)
        create_combined_tex_file(args.variant, build_dir)


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
