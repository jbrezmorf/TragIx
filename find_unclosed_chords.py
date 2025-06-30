import sys

def find_unclosed_chords(filename: str):
    print(f"Checking for unclosed parenthesis in {filename}...")
    with open(filename, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if line.count("(") > line.count(")"):
                print(f"Unclosed parenthesis on line {line_num}: {line.strip()}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python find_unclosed_chords.py <filename>")
        sys.exit(1)
    filename = sys.argv[1]
    find_unclosed_chords(filename)


# import os
# import find_unclosed_chords as fuc
# for sng in os.listdir("./nezboznej/build/songs"):
#   fuc.find_unclosed_chords(os.path.join("./nezboznej/build/songs", sng)
