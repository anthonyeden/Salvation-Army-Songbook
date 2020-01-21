# The Salvation Army Songbook

If you happen to find The Salvation Army Songbook as a SQLite file, this repository will help you do some useful stuff with it.

## Features

1. Parse all songs into a sensibly structured TXT file
2. Lookup CCLI Titles & Numbers from the SongSelect website
3. Generate ProPresenter 6 documents

## Instructions

1. Install Python 3
2. Install Pro6-Utils
 a. Install the `pro6` folder from this repo: https://github.com/anthonyeden/Pro6-Utils
 b. `pip3 install hachoir`
 c. `pip3 install PyRTF3`
3. Find The Salvation Army Songbook as a SQLite file (`sahb.sqlite`) and copy it into the same directory as this project
4. Run `python3 parse.py` to generate lyric text files in the `data/` folder
5. Run `python3 propresenter6.py` to generate ProPresenter 6 documents

Once you've run the ProPresenter6 script, you'll need to import all the documents into ProPresenter, and apply a template. Until you do this, the text will have a warning triangle indicating an error in the document.