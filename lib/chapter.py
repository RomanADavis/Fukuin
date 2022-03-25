from sqlite3 import Row
from xml.etree.ElementTree import ElementTree
from typing import Any, Dict, Iterable, Tuple
from typing_extensions import Self

import lib.verse
import lib.book
import lib.bible

class Chapter():
    table = "chapters"

    def __init__(self, number: int, book: "lib.book.Book", id: int = None):
        self.number = number
        self.book = book
        self.id = id
        
        self.number_of_verses = self.count_verses()
        self.verse_number = 0
    
    def count_verses(self) -> int:
        verse_table = lib.verse.Verse.table
        query = f"SELECT COUNT(*) FROM {verse_table} WHERE chapter = ?"
        row = self.execute(query, (self.number,))

        return row[0]

    def __iter__(self) -> Self:
        self.verse_number = 0
        # Recount, in case someone changes the number of verses.
        self.number_of_verses = self.count_verses()
        return self

    # return next verse and increment number
    def next(self) -> "lib.verse.Verse":
        self.number += 1
        if self.number > self.number_of_verses:
            raise StopIteration
        return lib.verse.Verse.load({"chapter": self.id, "number": self.number})

    def prev(self) -> "lib.verse.Verse":
        self.number -= 1
        if self.number < 1:
            raise StopIteration
        return lib.verse.Verse.load({"chapter": self.id, "number": self.number})

     # TODO: Add slice functionality
    def __getitem__(self, index: int) -> "lib.verse.Verse":
        # For simple index
        query = f"SELECT * FROM {self.table} WHERE chapter = ? and ordinal = ?"
        row = lib.verse.Verse.execute(query, [self.id, index])
        return lib.verse.Verse.load(row)

    @classmethod
    def execute(cls, query: str, data: Tuple) -> Row:
        print(query, data)
        row = lib.bible.Bible.execute(query, data)

        return row

    @classmethod
    # Necessary because sometimes when we initialize a chapter it'll be FROM a
    # database and sometimes it'll be TO a database
    def create(cls, number : int, book : "lib.book.Book" = None) -> Self:
        query = f"INSERT INTO {cls.table} (number, book) VALUES (?,?)"
        data = (number, book.id)
        
        cls.execute(query, data)
        
        id = lib.bible.Bible.cursor.lastrowid

        return Chapter(number, book, id)

    # TODO: While read is being lexible, maybe make it more flexible
    # Maybe return a join on book?
    def read(cls, attributes: Dict[str, Any]) -> Self:
        sieve = " ".join([f"{key} = ?" for key in attributes.keys()])
        row = cls.exectute(f"SELECT * FROM {cls.table} WHERE {sieve}", hash.values)
        
        return cls.from_row(row)

    @classmethod
    # I could make this more flexible so that we could take some sort of
    # attribute list instead of an id; I currently think this is a bad idea:
    # please think about this a bit before changing this.
    def update(cls, id: int, attributes: Dict[str, Any]) -> Self:
        update = " ".join([f"{key} = ?" for key in attributes.keys()])
        query = f"UPDATE {cls.table} SET {update} WHERE id = ?"

        row = cls.execute(query, [attributes.values] + [id])

        return cls.form_row(row)

    @classmethod
    def delete(cls, id: int) -> Self:
       query = f"DELETE FORM {cls.table} WHERE id = ?"
       row = cls.execute(query, (id,))

       # Not sure how this works with delete if, say, the Book is deleted.
       return cls.from_row(row)

    @classmethod
    def from_tree_node(cls, chapter_tag: ElementTree, book: "lib.book.Book") -> Self:
        number = chapter_tag.attrib["number"]
        chapter = Chapter.create(number, book)

        for verse_tag in chapter_tag.iter():
            if verse_tag.tag != "verse":
                continue
            lib.verse.Verse.from_tree_node(verse_tag, chapter)

        return chapter

    @staticmethod
    def from_row(row: Row, book: "lib.book.Book"=None) -> Self:
        if not book:
            book = lib.book.Book.read({"id": row.book})
        
        chapter = lib.chapter.Chapter(row["number"], book)
        chapter.id = row["id"]

        return chapter