#!/usr/bin/python3
import sys
import subprocess
import os

def convert_encoding(text, source_encoding):
    """ Convert text from source encoding to ASCII using an external conversion tool. """
    process = subprocess.Popen(['./cstocs', source_encoding, 'ascii', '--'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate(text.encode(source_encoding))
    return output.decode('ascii').strip()


def write_song(song_filename, current_song):
    with open(song_filename, 'w', encoding='utf8') as song_file:
                        song_file.write(''.join(current_song))

def main(filename):
    encoding = "utf8"
    song_number = 0
    current_song = []
    song_filename = ""

    with open(filename, 'r', encoding=encoding) as file:
        for line in file:
            if line.startswith('='):
                continue
            if line.startswith('encoding:'):
                encoding = line.strip().split(': ')[1]
                continue
            if line.startswith('N:'):
                if song_filename:
                    # Write previous song to its file
                    write_song(song_filename, current_song)    
                    current_song = []
                # Setup new song file
                title = line.strip().split(': ')[1].replace(' ', '_')
                title_ascii = title #convert_encoding(title, encoding)
                song_number += 1
                song_filename = f'songs/{song_number:03d}{title_ascii}.sng'
                if not os.path.exists('songs'):
                    os.makedirs('songs')
            #elif line.strip() == "=":
                ## Finish current song and reset for next
                #if song_filename:
                    #with open(song_filename, 'w', encoding='ascii') as song_file:
                        #song_file.write(''.join(current_song))
                    #current_song = []
                    #song_filename = ""
            
            current_song.append(line)

        # Final song write-out if exists
        if song_filename:
            write_song(song_filename, current_song)

if __name__ == "__main__":
    main(sys.argv[1])
