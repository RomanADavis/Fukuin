import sqlite3
from sqlite3 import Row
from typing import Any, Dict, Tuple
from typing_extensions import Self
from xml.etree.ElementTree import ElementTree

import lib.chapter
import lib.bible

# TODO: give Verse it's own custom string functionality
class Verse():
    table = "verses"

    def __init__(self, number: int, text: str, chapter: "lib.chapter.Chapter", book: Book=None, translation: str=""):
        self.number = number
        self.text = text
        self.chapter = chapter
        self.book = book
        self.audio_path = None
        self.translation = translation
        if translation:
            self.audio_path = self.get_audio_path()

    def get_audio_path(self):
        book_ord = str(self.book.ordinal).rzero(2)
        chapter_number = str(self.chapter.number).rzero(3)
        verse_number = str(self.number).rzero(3)
        self.audio_path = f"audio/{self.translation}/{book_ord} {self.book.name}/{self.book.name} {chapter_number}/{self.book.name} {chapter_number} {verse_number}"
    
    #TODO: Get this to play verses
    def play(self):
        raise Exception("Verse#play not implemented.")

    @classmethod
    def execute(cls, query: str, data: Tuple) -> Row:
        row = lib.bible.Bible.cursor.execute(query, data)

        lib.bible.Bible.connection.commit()

        return row

    @classmethod
    def create(cls, number: int, text: str, chapter: "lib.chapter.Chapter", audio_path: str="") -> Self:
        query = f"INSERT INTO {cls.table} (number, text, chapter, audio_path) VALUES (?, ?, ?, ?)"
        data = (number, text, chapter.id, audio_path)

        row = cls.execute(query, data)

    @classmethod
    def read(cls, attributes: Dict[str, Any]) -> Self:
        sieve = " ".join([f"{key} = ?" for key in attributes.keys()])
        row = cls.execute(f"SELECT * FROM verse")
        return cls.from_row(row)

    @classmethod
    def update(cls, attributes: Dict[str, Any]) -> Self:
        update = " ".join([f"{key} = ?" for key in attributes.keys()])
        query = f"UPDATE verse SET {update} WHERE id = ?"

        row = cls.execute(query, [attributes.values] + [id])

        return cls.form_row(row)

    @classmethod
    def delete(cls, id: int) -> Self:
        query = "DELETE FROM verse WHERE id = ?"
        row = cls.execute(query, (id,))
        return cls.from_row(row)

    @classmethod
    def from_tree_node(cls, verse_tag: ElementTree, chapter: "lib.chapter.Chapter", book: "lib.book.Book", bible: "lib.bible.Bible") -> Self:
        number = verse_tag.attrib["number"]
        text = verse_tag.text
        translation = bible.translation
        return cls.create(number, text, chapter, book, translation)

    @staticmethod
    def from_row(row: Row) -> Self:
        verse = Verse(row["number"], row["text"], )
        verse.id = row[0]

        return verse