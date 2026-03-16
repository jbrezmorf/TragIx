# Zpěvníky oddílů Ichthys

TragIx = Tragoudi Ixtys = Zpívající Ryba

Scout troop songbook build system. Two variants:

- **Nezbožnej** (červený/red) -- secular campfire songs
- **Zbožnej** (zelený/green) -- gospel/church songs

## Repository structure

```
common/              Shared TeX
nezboznej/           Red songbook variant
  head.tex           Title page and preamble
  tail.tex           Chord diagrams and closing
  songs/             Individual song files (canonical, clean UTF-8)
  overrides/         Build-time layout overrides (spacing hacks etc.)
  songlists/         Edition manifests (one file per year)
  build/             Build output (generated, gitignored)
zboznej/             Green songbook variant (same structure)
fonts/               Custom Scout fonts (TheMix C5, SKAUT)
scripts/             Helper scripts
doc/                 Documentation and notes
zdroje/              Legacy song source archives
build_songbook.py    Main build script
Dockerfile           Reproducible build environment
```

## Building

### With Docker (recommended)

```bash
# Linux/Mac
./docker_build.sh zboznej rebuild 2026

# Windows PowerShell
.\docker_build.ps1 zboznej rebuild 2026
```

Arguments: `<variant> <target> [edition]`

The `edition` parameter selects which songlist to build from
(e.g. `2025`, `2026`). It reads `{variant}/songlists/{edition}.txt`,
collects matching songs from `songs/` (or `overrides/` when present),
and produces the PDF.

### Without Docker

Prerequisites:

```bash
sudo apt install -y python3 texlive texlive-luatex texlive-plain-generic \
  texlive-lang-czechslovak texlive-fonts-recommended poppler-utils psutils ghostscript
sudo locale-gen cs_CZ.UTF-8
```

Build:

```bash
python3 build_songbook.py --variant zboznej --edition 2026 --target rebuild
```

Build targets: `songs`, `build`, `rebuild`, `clean`, `all`, `duplex`,
`buildwithindex`, `test`, `retest`, `testwithindex`.

## Contributing songs

Songs are plain text files -- editable with any text editor, including
GitHub's built-in editor. No special tooling required.

### Editing a song

1. Navigate to `nezboznej/songs/` or `zboznej/songs/` on GitHub
2. Open the song file (e.g. `Přítel.txt`)
3. Click the pencil icon to edit
4. Make your changes and click **Propose changes**
5. This creates a Pull Request that the maintainer can review and merge

### Adding a new song

1. Click **Add file** in the appropriate `songs/` directory
2. Paste the song content in the [standard format](#song-file-format)
3. Propose the new file
4. Also edit the relevant songlist in `songlists/` to include the new title

### Removing a song from an edition

Edit the songlist file (e.g. `zboznej/songlists/2026.txt`) and remove the
title line. The song file itself stays in `songs/` for potential future use.

## Song file format

Full specification: `doc/song_format.txt` (English, technical).
Contributor-friendly version: `doc/jak_psat_pisnicky.txt` (Czech).

Quick reference:

- Header: `N:` name, `A:` author, `AC:` author code, `Z:` source, `ZC:` source code
- Verses: `1:`, `2:`, ... Refrains: `R:`, `R1:`, ... Bridge: `M:` Recitative: `C:`
- Chords inline before syllables: `(G)`, `(Am7)`, `(C"m)` (sharp = `"`, flat = `b`)
- Continuation lines: indented with spaces, or prefixed with `+`
- Repetition: `/: ... :/` or `3×/: ... :/`
- Comments: lines starting with `%`

## Helper scripts

```bash
# Quality check -- single file or whole directory
python scripts/check_songbook.py nezboznej/songs/Přítel.txt
python scripts/check_songbook.py nezboznej/songs/ --tail nezboznej/tail.tex

# Auto-fix safe issues (preview first with --dry-run)
python scripts/fix_songbook.py nezboznej/songs/ --dry-run
python scripts/fix_songbook.py nezboznej/songs/

# Sort a songlist by Czech locale
python scripts/sort_songlist.py zboznej/songlists/2026.txt
python scripts/sort_songlist.py --all          # sort all songlists
python scripts/sort_songlist.py --check --all  # verify sort order

# Compare two edition song lists
python scripts/compare_songlists.py zboznej/songlists/2012.txt zboznej/songlists/2026.txt
```

## Editions


| Variant         | 2007 | 2012 | 2025        | 2026        |
| --------------- | ---- | ---- | ----------- | ----------- |
| Nezbožnej (red) | yes  | yes  | **current** | --          |
| Zbožnej (green) | yes  | yes  | --          | in progress |


## Overrides

The `overrides/` directory holds build-time layout modifications for
already-printed editions (invisible spacing, placeholder songs, etc.).
During build, an override file takes precedence over the matching `songs/`
file. New editions start without overrides; they are created only during
final layout fine-tuning before print.

## Known issues (Nezbožnej)

These are intentionally left unfixed in the current printed edition:

- "Sbohem Galánečko", "Marnivá sestřenice", "Kozel", "Tři myši prašivý"  
have non-standard repetition marks or have them missing.
- "Mršina" has inconsistent line breaks across verses due to long lines  
that don't fit properly.

## Future ideas

- Capo as a header field (currently written as free text in the song).
- Time signature (takt) as a header field.
- Zbožnej: add mass-part labels to the header (which song goes with
which part of the liturgy).
- Triple-dot semantics: currently `...` means both "sing the obvious"
and "fade out" -- consider differentiating these.
- Most header fields (AC, Z, ZC) are underused -- reconsider whether
they should stay required.

