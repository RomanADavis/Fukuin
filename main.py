from ensurepip import version
import sqlite3

import sqlite3
from sqlite3 import Error
import xml.etree.ElementTree as ElementTree

# ordinal to bible book name
book_names = [line.strip() for line in open("books.txt").readlines()]

# Make KJV Database
connection = sqlite3.connect("db/bible.db")
cursor = connection.cursor()

## CREATE TABLES
cursor.execute("CREATE TABLE translation (translation)")
cursor.execute("CREATE TABLE testament (name, translation)")
cursor.execute("CREATE TABLE book (name, ordinal, testament, translation)")
cursor.execute("CREATE TABLE chapter (number, book)")
cursor.execute("CREATE TABLE verse (number, chapter, text, audio_path)")

# Parsing the XML Document
tree = ElementTree.parse("xml/kjv.xml")
root = tree.getroot()

for bible in root.iter():
    if bible.tag != "bible":
        continue
    
    translation = bible.attrib["translation"]
    query = "INSERT INTO translation (translation) VALUES (?)"
    cursor.execute(query, (translation,))
    
    bible_id = cursor.lastrowid
    for testament in bible.iter():
        if testament.tag != "testament":
            continue
        
        query = "INSERT INTO testament (name, translation) VALUES (?, ?)"
        data = (f'{testament.attrib["name"]} Testament', bible_id)
        cursor.execute(query, data)
        
        testament_id = cursor.lastrowid
        # print(testament_id)
        for book in testament.iter():
            if book.tag != "book":
                continue
            ordinal = book.attrib["number"]
            book_name = book_names[int(ordinal)]
            
            query = "INSERT INTO book (name, ordinal, testament, translation) VALUES (?, ?, ?, ?)"
            data = (book_name, int(ordinal), testament_id, bible_id)
            cursor.execute(query, data)
            
            book_id = cursor.lastrowid
            for chapter in book.iter():
                if chapter.tag != "chapter":
                    continue
                chapter_number = chapter.attrib["number"]
                
                query = "INSERT into chapter (number, book) VALUES (?, ?)"
                data = (int(chapter_number), book_id)
                cursor.execute(query, data)
                
                chapter_id = cursor.lastrowid
                for verse in chapter.iter():
                    if verse.tag != "verse":
                        continue
                    verse_number = verse.attrib["number"]
                    
                    # Figure out how to get audio path
                    book_path = f"{str(ordinal).zfill(2)} {book_name}"
                    chapter_path = f"{book_name} {chapter_number.zfill(3)}"
                    verse_path = f"{chapter_path} {verse_number.zfill(3)}.mp3"
                    audio_path = f"audio/{translation}/{book_path}/{chapter_path}/{verse_path}"

                    query = "INSERT into verse (number, chapter, text, audio_path) VALUES (?, ?, ?, ?)"
                    data = (int(verse_number), chapter_id, verse.text, audio_path)
                    cursor.execute(query, data)
                    print(cursor.lastrowid)
connection.commit()
cursor.close()
connection.close()