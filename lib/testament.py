from typing import List, Dict, Any
from typing_extensions import Self
from xml.etree.ElementTree import ElementTree
from sqlite3 import Row

import lib.bible
import lib.book

class Testament():
    # Just the name of the table here, but one could consider the
    # possibility of having this be a "table_name" variable and then
    # loading the entire table to Testament#table variable.
    table = "testaments"

    def __init__(self, name: str, bible: "lib.bible.Bible", id: int = None):
        self.name = name
        self.bible = bible
        self.ordinal = 0
        self.id = id

    # Thought about making seperate $books attribute and #get_books() function,
    # but it seems like it would be a source of subtle bugs, making people
    # expect one to be the other.
    def books(self) -> List["lib.bible.Bible"]:
        book_table = lib.book.Book.table
        ids = lib.bible.Bible.cursor.execute(f"SELECT id FROM {book_table} where testament = ? ORDER BY ordinal", self.id)
        return [lib.book.Book.load({"id": id}) for id in ids]

    # TODO: Work with slices
    # TODO: Work with book names
    # TODO: Work with slices of book names
    # TODO: Work with book abbreviations
    # TODO: Work with slices of abreviations
    # TODO: I haven't even added abbreviations to words or bibles yet; go do 
    # that.
    def __getitem__(self, index: int) -> "lib.book.Book":
        # For simple index; we can't just count on ordinals when we're dealing
        # with one testament.
        return self.books()[index]

    @classmethod
    def execute(cls, query: str, data: Dict[str, Any]) -> Row:
        row = lib.bible.Bible.cursor.execute(query, data).fetchone()

        lib.bible.Bible.connection.commit()

        return row

    @classmethod
    # Necessary because sometimes we'll be saving a new Bible and sometimes
    # we'll be loading it from a database. And sometimes we may be
    # overwriting / editing an exist bible.
    def create(cls, name: str, bible: "lib.bible.Bible") -> Self:
        query = f"INSERT INTO {cls.table} (name, bible) VALUES (?, ?)"
        Testament.execute(query, (name, bible.id))
        
        testament = Testament(name, bible)
        testament.id = lib.bible.Bible.cursor.lastrowid
        
        return testament

    @classmethod
    # TODO: Maybe make this some sort of LEFT JOIN?
    # Y'know SELECT t.*, b.* FROM testaments LEFT JOIN bibles b ON t.bible = b.id WHRE t.id = ?
    def read(cls, attributes: Dict[str, Any], bible: "lib.bible.Bible" = None) -> Self:
        sieve = " ".join([f"{key} = ?" for key in attributes.keys()])
        query = f"SELECT * FROM {cls.table} where {sieve}"
        row = cls.execute(query, attributes.values())
        
        return Testament.from_row(row, bible)
    
    # This is sort of copied mindlessly from the update method in book.
    # Might not need this much pagentry; may be justified by later changes. Idk.
    @classmethod
    def update(cls, id: int, attributes: Dict[str, Any], bible: "lib.bible.Bible" = None) -> Self:
        update = " ".join([f"{key} = ?" for key in attributes.keys()])
        query = f"UPDATE {cls.table} SET {update} WHERE id = ?"

        row = Testament.execute(query, [attributes.values] + [id])

        return Testament.form_row(row, bible)

    @classmethod
    # Thought about making this more flexible with an attribute object;
    # currently think it's dumb.
    def delete(cls, id: int) -> Self:
        query = f"DELETE FROM {cls.table} WHERE id = ?"
        row = cls.execute(query, (id,))

    @classmethod
    def from_tree_node(cls, node: ElementTree, bible: "lib.bible.Bible") -> Self:
        name = node.attrib["name"]
        testament = Testament.create(name, bible)
        
        for book_tag in node.iter():
            if book_tag.tag != "book":
                continue
            lib.book.Book.from_tree_node(book_tag, testament, bible)
        
        return testament
    
    @staticmethod
    def from_row(row: Row, bible: "lib.bible.Bible" = None) -> Self:
        if not bible:
            bible = lib.bible.Bible.read({"id": row["bible"]})
        testament = Testament(row["name"], bible)
        testament.id = row["id"]
        
        return testament