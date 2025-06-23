def extract_songs(filepath):
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    song_lines = []

    for line in lines:
        line = line.strip()
        song_lines.append(line.split(".")[0])
    return set(song_lines)


def compare_songlists(file1, file2):
    songs_1 = extract_songs(file1)
    songs_2 = extract_songs(file2)

    removed = sorted(songs_1 - songs_2)
    added = sorted(songs_2 - songs_1)

    print("❌ Songs removed (in first file but not in second):")
    for song in removed:
        print(song)

    print("\n✅ Songs added (in second file but not in first):")
    for song in added:
        print(song)


# Example usage:
# compare_songlists("songlist_2007.txt", "songlist_2012.txt")
