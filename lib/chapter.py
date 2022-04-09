from operator import index
from sqlite3 import Row
from xml.etree.ElementTree import ElementTree
from typing import Any, Dict, Tuple
from genanki import Model, Note, Deck, Package
from random import randrange
from pandas import DataFrame, ExcelWriter
from xlsxwriter import Workbook

import lib.verse
import lib.book
import lib.bible
from lib.parse_summaries import parse_summaries, record_summaries

class Chapter():
    table = "chapters"

    summaries = parse_summaries()
    
    fields = [
        {"name": "BookName"}, 
        {"name": "ChapterNumber"}, 
        {"name": "Summary"}
    ]

    templates = [
        {
            "name": "Designation -> Summary", 
            "qfmt": "{{BookName}} {{ChapterNumber}}\n\n{{type:Summary}}",
            "afmt": "{{BookName}} {{ChapterNumber}}\n\n<hr id=answer>\n\n{{type:Summary}}",
        }
    ]

    model_id = 1413464275 # arbitrary and randomly generated
    
    model = Model(model_id, "Chapter Model", fields=fields, templates=templates)
    
    def __init__(self, number: int, book: "lib.book.Book", bible: "lib.bible.Bible", id: int = None) -> None:
        self.number = number
        self.book = book
        self.bible = bible

        self.id = id
        
        self.number_of_verses = self.count_verses()
        self.verse_number = 0
        # print(self.summaries[book.name], book.name, number)
        self.summary = self.summaries[book.name][number]


    def note(self) -> Note:
        return Note(
            model=self.model,
            fields=[
                self.book.name,
                str(self.number),
                self.summary 
            ]
        )

    @classmethod
    def book(cls, path="ChapterSummaries.xlsx"):
        workbook = Workbook(path)

        header_format = workbook.add_format({
            "text_wrap": True,
            "bold": True,
            "valign": "vcenter",
            "align": "center",
            "bg_color": "magenta",
            "font_color": "black"
        })

        summary_format = workbook.add_format({
            "text_wrap": True, 
            "valign": "vcenter"
            })
        
        colors = [
            {"bg": "black", "fg": "white"},
            {"bg": "yellow", "fg": "black"},
            {"bg": "navy", "fg": "white"},
            {"bg": "brown", "fg": "white"},
            {"bg": "gray", "fg": "white"},
            {"bg": "green", "fg": "white"},
            {"bg": "white", "fg": "black"},
            {"bg": "orange", "fg": "white"},
            {"bg": "purple", "fg": "white"},
            {"bg": "red", "fg": "white"}
        ]

        for book_name, chapters in cls.summaries.items():
            records = record_summaries(cls.summaries, book_name)
            worksheet = workbook.add_worksheet(book_name)
            worksheet.write(0, 0, "CHAPTER", header_format)
            worksheet.write(0, 1, "SUMMARY", header_format)
            for index, record in enumerate(records):
                number_format = workbook.add_format({
                    "align": "center", 
                    "valign": "vcenter", 
                    "bg_color": colors[index % 10]["bg"], 
                    "font_color": colors[index % 10]["fg"], 
                    "bold": True
                    })
                worksheet.write(index + 1, 0, record["chapter"], number_format)
                worksheet.write(index + 1, 1, record["summary"], summary_format)
            worksheet.set_column(0, 0, 12)
            worksheet.set_column(1, 1, 100)
        workbook.close()
        

    @classmethod
    def decks(cls) -> Deck:
        decks = []
        summaries = parse_summaries()
        notes = []
        for index, (book, chapters) in enumerate(summaries.items()):
            ordinal = str(index + 1).zfill(2)
            deck_id = randrange(1 << 30, 1 << 31)
            deck = Deck(deck_id, f"Bible Summaries::{ordinal} {book}")
            for number, summary in chapters.items():
                deck.add_note(Note(
                    model=cls.model,
                    fields=[
                        book,
                        str(number), # Has to be converted to string
                        summary
                    ]
                ))
            decks.append(deck)
        return decks

    @classmethod
    def package(cls) -> Package:
        return Package(cls.decks())

    def count_verses(self) -> int:
        verse_table = lib.verse.Verse.table
        query = f"SELECT COUNT(*) FROM {verse_table} WHERE chapter = ?"
        row = self.execute(query, (self.number,))

        return row[0]

    def __iter__(self) -> "Chapter":
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
        #print(query, data)
        row = lib.bible.Bible.execute(query, data)

        return row

    @classmethod
    # Necessary because sometimes when we initialize a chapter it'll be FROM a
    # database and sometimes it'll be TO a database
    def create(cls, number : int, book : "lib.book.Book" = None, bible: "lib.bible.Bible" = None) -> "Chapter":
        query = f"INSERT INTO {cls.table} (number, book, bible) VALUES (?, ?, ?)"
        data = (number, book.id, bible.id)
        
        cls.execute(query, data)
        
        id = lib.bible.Bible.cursor.lastrowid

        return Chapter(number, book, bible, id)

    # TODO: While read is being lexible, maybe make it more flexible
    # Maybe return a join on book?
    def read(cls, attributes: Dict[str, Any]) -> "Chapter":
        sieve = " ".join([f"{key} = ?" for key in attributes.keys()])
        row = cls.exectute(f"SELECT * FROM {cls.table} WHERE {sieve}", hash.values)
        
        return cls.from_row(row)

    @classmethod
    # I could make this more flexible so that we could take some sort of
    # attribute list instead of an id; I currently think this is a bad idea:
    # please think about this a bit before changing this.
    def update(cls, id: int, attributes: Dict[str, Any]) -> "Chapter":
        update = " ".join([f"{key} = ?" for key in attributes.keys()])
        query = f"UPDATE {cls.table} SET {update} WHERE id = ?"

        row = cls.execute(query, [attributes.values] + [id])

        return cls.form_row(row)

    @classmethod
    def delete(cls, id: int) -> "Chapter":
       query = f"DELETE FORM {cls.table} WHERE id = ?"
       row = cls.execute(query, (id,))

       # Not sure how this works with delete if, say, the Book is deleted.
       return cls.from_row(row)

    @classmethod
    def from_tree_node(cls, chapter_tag: ElementTree, book: "lib.book.Book", bible: "lib.bible.Bible") -> "Chapter":
        number = int(chapter_tag.attrib["number"])
        chapter = Chapter.create(number, book, bible)

        for verse_tag in chapter_tag.iter():
            if verse_tag.tag != "verse":
                continue
            lib.verse.Verse.from_tree_node(verse_tag, chapter, book, bible)

        return chapter

    @staticmethod
    def from_row(row: Row, book: "lib.book.Book"=None) -> "Chapter":
        if not book:
            book = lib.book.Book.read({"id": row.book})
        
        chapter = lib.chapter.Chapter(row["number"], book)
        chapter.id = row["id"]

        return chapter