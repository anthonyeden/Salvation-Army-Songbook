# This script creates a CSV file based on the song data in the .txt files

import sys, os
import csv
import propresenter6

if __name__ == "__main__":
    songs = propresenter6.get_songs()

    with open('data/songs.csv', 'w', encoding='utf-8') as csvfile:
        csvfile.write('\ufeff')
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['song_number', 'first_line', 'copyright', 'terms', 'ccli_number', 'ccli_title', 'author', 'info', 'lyrics'])

        for filename in songs:
            data = propresenter6.read_song_file(filename)
            
            lyrics = ''
            for group in data['groups']:
                if lyrics != '':
                    lyrics += "\r\n\r\n\r\n"
                lyrics += '[' + group['label'] + ']' + "\r\n" + group['text']

            csvwriter.writerow([data['song_number'], data['first_line'], data['copyright'], data['terms'], data['ccli_number'], data['ccli_title'], data['author'], data['info'], lyrics])

