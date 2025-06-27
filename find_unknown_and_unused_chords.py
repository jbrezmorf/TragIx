import sys
import re
from collections import Counter


def load_known_chords_from_tail(file_path):
    known = set()
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("\\chdig"):
                match = re.match(r"\\chdig\{([^}]*)\}", line)
                if match:
                    chord = match.group(1).strip()
                    if chord:
                        known.add(chord)
    return known


def extract_chords_from_line(line):
    chords = []
    for match in re.findall(r"\((.*?)\)", line):
        parts = match.strip().split()
        chords.extend(parts)
    return chords


def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <song_input_file> <tail_tex_file>")
        sys.exit(1)

    song_file = sys.argv[1]
    tail_tex_file = sys.argv[2]

    known_chords = load_known_chords_from_tail(tail_tex_file)
    unknown_chords_counter = Counter()
    used_chords = set()

    with open(song_file, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            stripped = line.strip()
            if any(stripped.startswith(prefix) for prefix in ["Z:", "AC:", "ZC:"]):
                continue

            chords_in_line = extract_chords_from_line(line)
            for chord in chords_in_line:
                if chord in known_chords:
                    used_chords.add(chord)
                else:
                    unknown_chords_counter[chord] += 1
                    print(f"Line {line_num}: Unknown chord '{chord}' in: {stripped}")

    if unknown_chords_counter:
        print("\nSummary of unknown chords found:")
        for chord, count in unknown_chords_counter.most_common():
            print(f"- {chord}: {count} time(s)")
    else:
        print("No unknown chords found.\n")

    unused_known_chords = sorted(known_chords - used_chords)
    if unused_known_chords:
        print("\nKnown chords NOT used anywhere in the song input file:")
        for chord in unused_known_chords:
            print(f"- {chord}")
    else:
        print("All known chords are used at least once in the song input file.")


if __name__ == "__main__":
    main()
