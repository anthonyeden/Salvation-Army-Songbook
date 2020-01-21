import sys, os
import re
import ssl
import urllib.request
import urllib.parse
import db

def get_songs():
    songs = db.execute(''' SELECT text.id, songNumber, first, textdata.text, about, idLanguage, copy3
    FROM text, textdata
    WHERE text.id = textdata.idText
    ORDER BY text.songNumber ASC ''')

    songs_all = []

    for i, song in enumerate(songs):
        song['first_cleaned'] = song_title_clean(song['first'])
        song['copyright'] = get_copyright(song['copy3'])
        song['sources'] = get_sources(song['id'])
        song['text_parsed'] = song_text_parse(song['text'])

        song['copyright']['ccli_number'] = ""
        song['copyright']['ccli_title'] = ""

        if song['copyright']['ccli'] is True:
            ccli_details = search_ccli_number(song)
            if ccli_details is not False:
                song['copyright']['ccli_number'] = ccli_details['ccli_number']
                song['copyright']['ccli_title'] = ccli_details['title']

        songs_all.append(song)

        print("PROGRESS: %s of %s" % (i + 1, len(songs)))

    return songs_all

def get_sources(song_id):
    copyright = db.execute(''' SELECT sourceName, born, died, biog
    FROM text_textSource, textSource
    WHERE text_textSource.idText = ?
    AND text_textSource.idSource = textSource.id''',
    (song_id,))

    return copyright

def get_copyright(code):
    copyright = db.execute(''' SELECT copyright, address, email, encrypt AS terms FROM copyright
    WHERE code = ? ''',
    (code,))

    terms = db.execute(''' SELECT ccliTerms FROM terms
    WHERE id = ? ''',
    (copyright[0]['terms'],))

    copyright[0]['terms'] = terms[0]['ccliTerms']

    if 'CCLI' in copyright[0]['terms']:
        copyright[0]['ccli'] = True
    else:
        copyright[0]['ccli'] = False

    return copyright[0]

def search_ccli_number(song):
    # Do a web search for this song in the CCLI database

    headers = {}
    headers['User-Agent'] = "Salvation-Army-Songbook-Search"

    params = {}
    params['SongContent'] = ""
    params['PrimaryLanguage'] = ""
    params['Keys'] = ""
    params['Themes'] = ""
    params['List'] = ""
    params['Sort'] = ""
    params['SearchText'] = " ".join(song['text_parsed'][0]['lines'][:2])

    # Ignore the SSL Certificate
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request('https://songselect.ccli.com/search/results?%s' % urllib.parse.urlencode(params), headers = headers)
    html = urllib.request.urlopen(req, context = ctx).read()

    pos_1 = html.find(b'<p class="song-result-title">')
    if pos_1 > 1:
        html_sub = html[pos_1:]
        pos_2 = html_sub.find(b'</p>')
        if pos_2 > 1:
            # Parse out the CCLI Number & Title
            html_sub = html_sub[:pos_2]

            id = html_sub[html_sub.find(b'/Songs/')+7:]
            id = id[:id.find(b'/')]

            title = html_sub[html_sub.find(b'">', html_sub.find(b'/Songs/'))+2:]
            title = title[:title.find(b'<')]

            return {
                'title': title.decode("utf-8") ,
                'ccli_number': id.decode("utf-8") ,
            }
    
    return False


def cleanhtml(raw_html):
    # We just need a really dumb way to strip out HTML tags
    # I know this can be tricked, but for our purposes it doesn't matter
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    cleantext = cleantext.replace("&#160;", " ")
    cleantext = cleantext.replace("  ", " ")
    cleantext = cleantext.strip()
    return cleantext

def song_title_clean(title):
    allowed = 'abcdefghijklmnopqrstuvwxyz123456789 '  
    return ''.join(c for c in title if c.lower() in allowed)

def song_text_parse(text):
    # Supplied text is quasi-HTML
    # Every line is a new paragraph tag
    # Blocks are separated by an empty line: <p></p>
    # Chorus lines are like this: <p><span fontStyle="italic">This is my chorus text</span></p>
    # If a line starts with a number, this is the verse number. The first verse never has a number
    # The last block is always copyright/authorship text

    text_stripped = cleanhtml(text)
    text_lines = text_stripped.split("\n")
    text_lines_original = text.split("\n")

    start_new_block = True

    lyric_blocks = []

    for i, line in enumerate(text_lines):

        line = line.strip()

        if start_new_block is True:

            # If we need to create a new block, and the previous block is still empty, delete it
            if len(lyric_blocks) > 0 and len(lyric_blocks[len(lyric_blocks) - 1]['lines']) == 0:
                del lyric_blocks[len(lyric_blocks) - 1]

            if line[:1].isnumeric():
                # Start verse with a specific number
                verse = line[:1]
                line = line[2:]
                type = 'verse'
            else:
                verse = 1
                type = 'verse'

            if '<span fontStyle="italic">' in text_lines_original[i]:
                type = 'chorus'

            lyric_blocks.append({
                "type": type,
                "number": verse,
                "lines": []
            })

            start_new_block = False

        if line == '':
            start_new_block = True
            continue

        # Remove punctuation from the end of every line
        if line[-1:] == ";" or line[-1:] == ":" or line[-1:] == "," or line[-1:] == ".":
            line = line[:-1]

        # De-encode characters
        # &#8217; = '
        line = line.replace("&#8217;", "'")

        # Add this line to the latest block
        lyric_blocks[len(lyric_blocks) - 1]['lines'].append(line)

    # Remove the last block - authorship info
    del lyric_blocks[len(lyric_blocks) - 1]

    return lyric_blocks

def song_create_file(song):

    filename = 'SASB ' + str(song['songNumber']) + ' - ' + str(song['first_cleaned']) + '.txt'
    file = open(os.path.join('data/', filename), 'w')

    authors = []
    for source in song['sources']:
        authors.append(source['sourceName'])

    file.write("SONG NUMBER: " + str(song['songNumber']) + "\r\n")
    file.write("FIRST LINE: " + str(song['first']) + "\r\n")
    file.write("COPYRIGHT: " + str(song['copyright']['copyright']) + "\r\n")
    file.write("TERMS: " + str(song['copyright']['terms']) + "\r\n")
    file.write("CCLI NUMBER: " + str(song['copyright']['ccli_number']) + "\r\n")
    file.write("CCLI TITLE: " + str(song['copyright']['ccli_title']) + "\r\n")
    file.write("AUTHOR: " + ", ".join(authors) + "\r\n")
    file.write("INFO: " + str(song['about'].replace("\r", "").replace("\n", "\\n").replace("\t", " ")) + "\r\n")
    file.write("\r\n\r\n")

    for block in song['text_parsed']:
        file.write("[" + str(block['type']).upper() + " " + str(block['number']) + "]\r\n")
        file.write("\r\n".join(block['lines']))
        file.write("\r\n\r\n")

if __name__ == "__main__":
    for song in get_songs():
        song_create_file(song)