"""Compare two songlist files and show added/removed songs."""
import sys


def extract_songs(filepath):
    with open(filepath, encoding="utf-8") as f:
        songs = set()
        for line in f:
            line = line.strip()
            if line and not line.endswith(":"):
                songs.add(line)
        return songs


def compare_songlists(file1, file2):
    songs_1 = extract_songs(file1)
    songs_2 = extract_songs(file2)

    removed = sorted(songs_1 - songs_2)
    added = sorted(songs_2 - songs_1)
    common = sorted(songs_1 & songs_2)

    if removed:
        print(f"Songs only in {file1} ({len(removed)}):")
        for song in removed:
            print(f"  - {song}")

    if added:
        print(f"\nSongs only in {file2} ({len(added)}):")
        for song in added:
            print(f"  + {song}")

    print(f"\nCommon: {len(common)}, Only in first: {len(removed)}, Only in second: {len(added)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <songlist1> <songlist2>")
        sys.exit(1)
    compare_songlists(sys.argv[1], sys.argv[2])
