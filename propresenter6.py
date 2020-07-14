import os, sys
import io
import PyRTF.Elements
import html
import pro6
import xml.etree.ElementTree as Xml

def get_songs():
    # Returns a list of filenames for songs that can be processed
    path = 'data/'
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

    file_list = []

    for file in files:
        if file[:5] == "SASB " and file[-4:] == ".txt":
            file_list.append(file)

    return file_list

def read_song_file(filename):
    # Parses a specific song file, and returns a dict with the details
    path = 'data/'
    file = open(os.path.join(path, filename), 'r')
    lines = file.readlines()

    data = {
        "filename": filename,
        "song_number": "",
        "first_line": "",
        "copyright": "",
        "terms": "",
        "ccli_number": "",
        "ccli_title": "",
        "author": "",
        "info": "",
        "groups": []
    }

    in_group = False
    current_group_name = ""
    current_group_text = ""
    current_group_colour = "1 1 1 0"

    for line in lines:
        line = line.strip()

        if line[:12] == "SONG NUMBER:":
            data['song_number'] = line[13:]
        elif line[:11] == "FIRST LINE:":
            data['first_line'] = line[12:]
        elif line[:10] == "COPYRIGHT:":
            data['copyright'] = line[11:]
        elif line[:6] == "TERMS:":
            data['terms'] = line[7:]
        elif line[:12] == "CCLI NUMBER:":
            data['ccli_number'] = line[13:]
        elif line[:11] == "CCLI TITLE:":
            data['ccli_title'] = line[12:]
        elif line[:7] == "AUTHOR:":
            data['author'] = line[8:]
        elif line[:5] == "INFO:":
            data['info'] = line[6:]

        elif line[:1] == "[" and line[-1:] == "]":
            if current_group_text != '':
                data['groups'].append({
                    'label': current_group_name,
                    'text': current_group_text.strip(),
                    'colour': current_group_colour,
                })
            in_group = True
            current_group_name = line[1:-1]
            current_group_text = ""

            if current_group_name == "VERSE 1":
                current_group_colour = "0 0 1 1"
            elif current_group_name == "VERSE 2":
                current_group_colour = "0 1 0 1"
            elif current_group_name == "VERSE 3":
                current_group_colour = "0.9 0.5 0 1"
            elif current_group_name == "VERSE 4":
                current_group_colour = "0 0.5 0.9 1"
            elif current_group_name == "VERSE 5":
                current_group_colour = "0.9 0 0.5 1"
            elif current_group_name == "VERSE 6":
                current_group_colour = "0.5 0.9 1 1"
            elif current_group_name == "CHORUS 1":
                current_group_colour = "1 0 0 1"
            elif current_group_name == "BRIDGE 1":
                current_group_colour = "0 0 0 1"

        elif in_group:
            current_group_text += line + "\r\n"
    
    if in_group and current_group_text != '':
        data['groups'].append({
            'label': current_group_name,
            'text': current_group_text.strip(),
            'colour': current_group_colour,
        })

    return data

def create_pro6_doc(data):
    # Create a new document
    doc = pro6.document.presentation.PresentationDocument("Song", 1080, 1920, CCLISongTitle = data['ccli_title'], CCLISongNumber = data['ccli_number'], CCLIAuthor = data['author'])

    # Create a null group at the beginning - arrangements won't work properly without this
    group = pro6.document.group.SlideGroup('', '1 1 1 0')
    doc.append(group)

    # Create a blank slide at the beginning
    group = pro6.document.group.SlideGroup('Blank', '1 1 1 0')
    slide = pro6.document.slide.DisplaySlide()
    textbox = pro6.document.elements.TextElement()
    textbox.position = pro6.util.xmlhelp.Rect3D(1700.0, 800.0, 0.0, 110.0, 140.0)
    slide.elements.append(textbox)
    group.slides.append(slide)
    doc.append(group)

    # Loop over each group, and create the group
    for data_group in data['groups']:
        group = pro6.document.group.SlideGroup(data_group['label'], data_group['colour'])

        # Split lines
        lines_orig = data_group['text'].split("\n")
        lines = []

        insert_blank_after_next = False

        # Limit lines to 30 characters - split in the middle of a line if it's too long
        for i, line in enumerate(lines_orig):
            line = line.strip()

            if len(line) > 28:
                # Split!
                middle_i = int(len(line) / 2) + 1
                middle_space = line[middle_i:].find(" ")

                if middle_space <= 0:
                    middle_i = int(len(line) / 2) - 10
                    middle_space = line[middle_i:].find(" ")

                if middle_space > 0:
                    middle_space += middle_i
                    line_1 = line[:middle_space]
                    line_2 = line[middle_space + 1:]

                    if line_1[-1:] == "," or line_1[-1:] == ";" or line_1[-1:] == ".":
                        line_1 = line_1[:-1]

                    if len(lines) % 2 != 0:
                        lines.append("")
                    else:
                        insert_blank_after_next = True

                    lines.append(line_1)
                    lines.append(line_2)

                else:
                    lines.append(line)
                    if insert_blank_after_next:
                        lines.append("")
                    insert_blank_after_next = False

            else:
                lines.append(line)
                if insert_blank_after_next:
                    lines.append("")
                insert_blank_after_next = False

        DEFAULT_RTF = '''{\\rtf1\\ansi\\ansicpg1252\\cocoartf1561\\cocoasubrtf610
{\\fonttbl\\f0\\fnil\\fcharset0 Helvetica;}
{\\colortbl;\\red255\\green255\\blue255;}
{\\*\\expandedcolortbl;;}
\\pard\\slleading240\\pardirnatural\\qc\\partightenfactor0

\\f0\\b\\fs180 \\cf1 \\kerning1\\expnd24\\expndtw120
\\shad\\shadx60\\shady-60\\shadr99\\shado255 \\shadc0 <<<TEXTPLACEHOLDER>>>}'''

        # Create each slide
        for data_slide in [lines[i:i+2] for i in range(0, len(lines), 2)]:

            # Create a slide and a textbox
            slide = pro6.document.slide.DisplaySlide()
            textbox = pro6.document.elements.TextElement()
            textbox.position = pro6.util.xmlhelp.Rect3D(1700.0, 800.0, 0.0, 110.0, 140.0)

            # Plain text version
            textbox.text = "\r\n".join(data_slide).strip().encode('utf-8')

            # Create a RTF document to contain the text
            these_lines = []
            for line in data_slide:
                if line.strip() != '':
                    these_lines.append(line.strip())

            print(these_lines)
            text_fixed = u"\n".join(these_lines)
            text_fixed = text_fixed.replace("\r", "")
            text_fixed = html.unescape(text_fixed)
            text_fixed = ''.join([r'\u%s?' % str(ord(e)) for e in text_fixed])

            textbox.rtf = DEFAULT_RTF.replace("<<<TEXTPLACEHOLDER>>>", text_fixed).encode('utf-8')

            # Add the textbox to the slide
            slide.elements.append(textbox)

            # Add this new slide to the group    
            group.slides.append(slide)

        doc.append(group)

    # Create a blank slide at the end
    group = pro6.document.group.SlideGroup('Blank', '1 1 1 0')
    slide = pro6.document.slide.DisplaySlide()
    textbox = pro6.document.elements.TextElement()
    textbox.position = pro6.util.xmlhelp.Rect3D(1700.0, 800.0, 0.0, 110.0, 140.0)
    slide.elements.append(textbox)
    group.slides.append(slide)
    doc.append(group)

    # Setup default arrangement
    doc = pro6_arrangement_create_default(doc)

    # Save the Pro6 file to disk
    filename_out = os.path.join("data/", data['filename'][:-4] + ".pro6")
    doc.write(filename_out)
    return filename_out

def pro6_arrangement_create_default(doc):
    # Builds a default arrangement for this song, using simple logic that works for typical hymns

    arrangement = []

    chorus_uuid = None
    verses_before_chorus = 0
    verses_count = 0

    # Build our arrangement as a list of group GUIDs
    # Straight through until 1st chorus, then a chorus after each subsequent verse
    for group_key, group in enumerate(doc.groups):

        if 'uuid' not in group._attrib:
            group._attrib['uuid'] = pro6.util.general.create_uuid().upper()

        this_uuid = group._attrib['uuid']

        # If a group doesn't have a name, don't put it into the arrangement
        if group.name is None or group.name == "":
            del doc.groups[group_key]
            continue

        # Insert the current verse
        arrangement.append(this_uuid)

        # Find the UUID of the Chorus
        if group.name == "CHORUS 1":
            chorus_uuid = this_uuid

        # Determine how many verses between each chorus
        if chorus_uuid is None and group.name[:5] == "VERSE":
            verses_before_chorus += 1

        elif group.name[:5] == "VERSE":
            verses_count += 1

        if verses_before_chorus == verses_count and chorus_uuid is not None:
            # Insert the chorus
            arrangement.append(chorus_uuid)
            verses_count = 0

    # Create the arrangement in the correct XML structure
    uuid = pro6.util.general.create_uuid().upper()
    arrangement_xml_groupids = []

    for x in arrangement:
        elem = Xml.Element("NSString", {})
        elem.text = str(x)
        arrangement_xml_groupids.append(elem)

    arrangement_array = pro6.util.xmlhelp.create_array('groupIDs', arrangement_xml_groupids)
    arrangements_container = Xml.Element("RVSongArrangement", {'color': '0 0 0 0', 'name': 'Default', 'uuid': uuid})    
    arrangements_container.append(arrangement_array)
    doc.arrangements.append(arrangements_container)

    # The document needs a UUID, or else it rewrite all the other Group UUIDs
    doc._attrib['uuid'] = pro6.util.general.create_uuid().upper()

    # Set the default arrangement as 'selected'
    doc._attrib['selectedArrangementID'] = uuid

    return doc

if __name__ == "__main__":
    songs = get_songs()
    for filename in songs:
        print(filename)
        data = read_song_file(filename)

        create_pro6_doc(data)