# TragIx — Scout Troop Songbook Build System

TragIx (Tragoudi Ixtys = "Singing Fish") builds printable A5 songbook
PDFs from plain-text song files using LuaTeX (pdfcsplain format).

Two songbook variants:
- **Nezbožnej** (red) — secular campfire songs
- **Zbožnej** (green) — gospel / church songs

## Repository layout

```
common/lyric.tex         Core TeX macros (song parsing, chord rendering, page layout)
nezboznej/               Red variant
  head.tex               Title page + per-variant flags
  tail.tex               Chord diagrams + closing
  songs/                 One .txt file per song (canonical source)
  overrides/             Build-time layout hacks for already-printed editions
zboznej/                 Green variant (same structure; tail.tex also has category legend)
fonts/                   Custom Scout fonts (TheMix C5, SKAUT)
scripts/check_songbook.py  Quality checker + auto-fixer
build_songbook.py        Main build script
current_editions.txt     Active build targets (variant edition version)
Dockerfile / .dockerignore  Reproducible build environment
```

## Build flow

`build_songbook.py` is the single entry point.  It auto-detects whether
`luatex` is available locally; if not, it builds and runs inside Docker.

```
current_editions.txt   →   build_songbook.py --all
                                ↓
                           collect_songs()     filters by E: header
                           prepare_build()     writes .sng, songbook.tex, version.tex
                             ↓ K: field codes are expanded to display strings here
                           compile_pdf()       luatex × 2 passes (for index)
                             ↓
                           {variant}_{edition}.{version}.pdf
```

### current_editions.txt format

Three columns: `variant edition version`.  The version appears on the
title page (via generated `version.tex` → `\SongbookVersion`) and in
the output PDF filename.  Bump version when rebuilding.

## Song file format

Seven header fields in strict order (parsed by TeX `\getheader`):

```
N: Song Title
A: Author
AC: Author code
Z: Source songbook
ZC: Source reference number
E: 2007, 2012, 2025
K: MV MZ AR ZJ
```

- **N:** and **E:** are used by the Python build script.
- **A:** and **ZC:** are rendered in the PDF (ZC only when `\showsourcereftrue`).
- **K:** holds space-separated category abbreviation codes.  During build,
  mass-part codes (M-prefix) are expanded to full Czech names; others stay
  as abbreviations.  Rendered as an italic subtitle when `\showcategorytrue`.
  See `MASS_PART_NAMES` and `VIBE_DISPLAY` dicts in `build_songbook.py`.
- **AC:** and **Z:** are parsed but not currently rendered.

All seven fields must be present in every song file, even if empty.
The TeX parser is a rigid pattern match and will fail with
"File ended while scanning use of \getheader" if a field is missing.

## Per-variant flags (set in head.tex)

| Flag                  | Nezbožnej | Zbožnej | Effect                                   |
|-----------------------|-----------|---------|------------------------------------------|
| `\preservelayouttrue` | yes       | no      | Freeze page layout for reprints          |
| `\showsourcereftrue`  | no        | yes     | Show ZC: in parens after song title      |
| `\showcategorytrue`   | no        | yes     | Show K: as italic subtitle under title   |

## TeX architecture (common/lyric.tex)

- `\getheader` — fixed 7-field pattern matcher; calls `\MakeSongHeader`
- `\MakeSongHeader` — renders title, optional source ref, author, optional category
- `\inputsong` — wraps each song in a vbox, activates chord catcodes
- `\songanchor` / `\toclink` / `\tocendlink` — invisible PDF hyperlinks
  (index entries link to songs; uses `\pdfdest` / `\pdfstartlink`)
- `\setlyricoutput` — custom multi-column output routine (`\poisepages`)

### Known TeX pitfalls

- `\pdfdest` must be placed in **horizontal mode** (after `\noindent`);
  placing it in vertical mode causes the output routine to loop.
- Tracing macros (`\tracingmacros`, etc.) are defined at the end of
  lyric.tex and set to 0.  Setting them to non-zero generates multi-GB
  log files and slows builds ~10x.

## Quality checker (scripts/check_songbook.py)

```bash
python scripts/check_songbook.py zboznej/songs/ --fix          # apply fixes
python scripts/check_songbook.py zboznej/songs/ --fix --dry-run # preview
python scripts/check_songbook.py zboznej/songs/ --edition 2026  # filter
```

Auto-fixes: separators, quotation marks, ellipses, multiply signs,
verse label dots, sus/mi chord notation, missing K: field.

## CI (.github/workflows/build.yaml)

Two jobs: `lint` (runs checker with `--fix --dry-run`) then `build`
(Docker-based PDF compilation).  Both read `current_editions.txt`.

## Docker

`.dockerignore` excludes `*/build/`, `.git`, `__pycache__`, `*.pdf`,
`*.ps`, `*.log`, `zdroje/` to keep the build context small.
On Windows, `_find_docker()` in build_songbook.py searches common
Docker Desktop install paths if `docker` isn't on PATH.

## Conventions

- Song files are UTF-8 plain text with Czech diacritics.
- Chords use the Czech system: H (not B), `"` for sharp, `b` for flat.
