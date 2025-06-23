import sys
import re


def extract_chords(line):
    return re.findall(r"\(([^)]+)\)", line)


def load_known_chords(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def find_unknown_chords(song_path, known_chords):
    with open(song_path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if line.startswith(("Z:", "AC:", "ZC:")):
                continue
            for chord in extract_chords(line):
                if chord not in known_chords:
                    print(f"Unknown chord '{chord}' on line {lineno}: {line.strip()}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <song_file> <known_chords_file>")
        sys.exit(1)

    song_file = sys.argv[1]
    known_chords_file = sys.argv[2]

    known_chords = load_known_chords(known_chords_file)
    find_unknown_chords(song_file, known_chords)


if __name__ == "__main__":
    main()
