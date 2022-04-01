from sqlite3 import Row
from typing import Any, Dict
from xml.etree.ElementTree import ElementTree

import lib.bible
import lib.chapter
import lib.testament

class Book():
    # ordinal to bible book name
    book_names = [line.strip() for line in open("./text/books.txt").readlines()]
    books_in_the_bible = 66

    def __init__(self, name: str, ordinal: int, testament: "lib.testament.Testament", bible: "lib.bible.Bible", id: int = None) -> None:
        self.name = name
        # A number representing it's order in the bible: Genesis is 1, etc.
        self.ordinal = ordinal 
        self.testament = testament # Should be an id
        self.bible = bible # Should be an id
        self.number = 0 # Chapter number for iteration
        self.id = id
        self.chapters_in_book = self.count_chapters()

    def count_chapters(self) -> int:
        count = self.execute("SELECT COUNT() FROM chapters WHERE book = ?", (self.id,))

        return count[0]

    def __iter__(self) -> "Book":
        self.number = 0
        self.chapters_in_book = self.count_chapters()
        return self

    # return next chapter and increment number
    def next(self) -> "lib.chapter.Chapter":
        self.number += 1
        if self.number > self.chapters_in_book:
            raise StopIteration
        return lib.chapter.Chapter.read({"book": self.id, "number": self.ordinal})

    # return previous chapter and decrement number
    def prev(self) -> "lib.chapter.Chapter":
        self.number -= 1
        if self.number < 1:
            raise StopIteration
        return lib.chapter.Chapter.read({"book": self.id, "number": self.ordinal})   

    # TODO: Add slice functionality
    def __getitem__(self, index: int) -> "lib.chapter.Chapter":
        # For simple index
        query = "SELECT * FROM chapter WHERE book = ? and chapter = ?"
        row = lib.chapter.Chapter.execute(query, [self.id, index])
        return lib.chapter.Chapter.from_row(row, self)

    @staticmethod
    # TODO: Find out what types can go into sqlite, put them in a type union,
    # call it "SQLType" or something like that, and use it to replace "Any"
    # here.
    def execute(query: str, data: Dict[str, Any]) -> Row:
        try:
            row = lib.bible.Bible.cursor.execute(query, data).fetchone()
        except:
            raise Exception(f"Book#execute failed query: {query} with values: {data}")

        lib.bible.Bible.connection.commit()

        return row

    @classmethod
    # Necessary because sometimes when we initialize a book it'll be FROM a
    # database and sometimes it'll be TO a database
    def create(cls, name: str, ordinal: int, testament: "lib.testament.Testament", bible: "lib.bible.Bible") -> "Book":
        query = "INSERT INTO books (name, ordinal, testament, bible) VALUES (?,?,?,?)"
        data = (name, ordinal, testament.id, bible.id)
        
        cls.execute(query, data)
        
        book = Book(name, ordinal, testament, bible)
        book.id = lib.bible.Bible.cursor.lastrowid
        return book

    @classmethod
    def read(cls, attributes: Dict[str, Any]) -> "Book": # Would need a dictionary to work this way.
        sieve = " ".join([f"{key} = ?" for key in attributes.keys()])
        row = cls.exectute(f"SELECT * FROM books WHERE {sieve}", hash.values)
        
        return cls.from_row(row)

    @classmethod
    # I could make this more flexible so that we could take some sort of
    # attribute list instead of an id; I currently think this is a bad idea:
    # please think about this a bit before changing this.
    def update(cls, id: int, attributes: Dict[str, Any]) -> "Book":
        update = " ".join([f"{key} = ?" for key in attributes.keys()])
        query = f"UPDATE book SET {update} WHERE id = ?"

        row = cls.execute(query, [attributes.values] + [id])

        return cls.form_row(row)
    
    @classmethod
    # Thought about making this more flexible with an attribute object;
    # currently think it's dumb.
    def delete(cls, id: int) -> "Book":
        query = "DELETE FROM book WHERE id = ?"
        row = cls.execute(query, (id,))
        
        return cls.from_row(row)
    
    @classmethod
    def from_tree_node(cls, book_tag: ElementTree, testament: "lib.testament.Testament", bible: "lib.bible.Bible") -> "Book":
        ordinal = book_tag.attrib["number"]
        name = cls.book_names[int(ordinal)]
        book = cls.create(name, ordinal, testament, bible)
        
        for chapter_tag in book_tag.iter():
            if chapter_tag.tag != "chapter":
                continue
            lib.chapter.Chapter.from_tree_node(chapter_tag, book, bible)

        return book

    @staticmethod
    # Come up with a seperate path for doing this in Bible and Testament
    def from_row(row: Row, testament: "lib.testament.Testament"=None, bible: "lib.bible.Bible"=None) -> "Book":
        if not testament:
            testament = lib.testament.Testament.read({"id": row["testament"]})
        if not bible:
            testament = lib.bible.Bible.read({"id": row["bible"]})
        book = Book(row["name"], row["ordinal"], testament, bible, row["id"])
        
        return book