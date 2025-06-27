import sys
import re
from collections import Counter


def extract_chords(line):
    chords = []
    for match in re.findall(r"\(([^)]+)\)", line):
        parts = match.strip().split()
        chords.extend(parts)
    return chords


def load_known_chords(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def find_unknown_chords(song_path, known_chords):
    unknown_chords_counter = Counter()
    with open(song_path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if line.startswith(("Z:", "AC:", "ZC:")):
                continue
            for chord in extract_chords(line):
                if chord not in known_chords:
                    print(f"Unknown chord '{chord}' on line {lineno}: {line.strip()}")
                    unknown_chords_counter[chord] += 1

    if unknown_chords_counter:
        print("\nSummary of unique unknown chords:")
        for chord, count in unknown_chords_counter.most_common():
            print(f"- {chord}: {count} time(s)")
    else:
        print("\nNo unknown chords found.")


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
