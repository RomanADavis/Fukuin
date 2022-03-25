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

    def __init__(self, number: int, text: str, chapter: "lib.chapter.Chapter", audio_path: str =""):
        self.number = number
        self.text = text
        self.chapter = chapter
        self.audio_path = audio_path

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
    def from_tree_node(cls, verse_tag: ElementTree, chapter: "lib.chapter.Chapter") -> Self:
        number = verse_tag.attrib["number"]
        text = verse_tag.text
        return cls.create(number, text, chapter)

    @staticmethod
    def from_row(row: Row) -> Self:
        verse = Verse(row["number"], row["text"], )
        verse.id = row[0]

        return verse