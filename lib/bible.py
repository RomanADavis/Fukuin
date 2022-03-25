from types import NoneType
from typing_extensions import Self
import xml.etree.ElementTree as ElementTree
import sqlite3
from sqlite3 import Row
from typing import Dict, List, Tuple
import os

import lib.book
import lib.testament

class Bible():
    database = "db/bible.db"
    connection = sqlite3.connect("db/bible.db")
    cursor = connection.cursor()
    table = "bibles"
    
    def __init__(self, translation: str) -> NoneType:
        self.translation = translation
        self.ordinal = 0
        self.id = None

    def __iter__(self) -> Self:
        self.ordinal = 0
        return self

    def next(self) -> lib.book.Book:
        self.ordinal += 1
        if self.ordinal > self.books_in_the_bible:
            raise StopIteration
        return lib.Book.read({"bible": self.id, "ordinal": self.ordinal})
        
    def prev(self) -> lib.book.Book:
        self.ordinal -= 1
        if self.ordinal < 1:
            raise StopIteration
        return lib.book.Book.read({"bible": self.id, "ordinal": self.ordinal})

    def books(self) -> List[lib.book.Book]:
        ids = self.cursor.execute(f"SELECT id FROM {self.table} WHERE bible == ?", self.id)
        return [lib.book.Book.read({"id": id}) for id in ids]

    # TODO: Work with slices
    # TODO: Work with book names
    # TODO: Work with slices of book names
    # TODO: Work with book abbreviations
    # TODO: Work with slices of abreviations
    # TODO: I haven't even added abbreviations to words or bibles yet; go do 
    # that.
    def __getitem__(self, index: int) -> lib.book.Book:
        # For simple index
        query = f"SELECT * FROM {self.table} WHERE bible = ?"
        row = lib.book.Book.execute(query, [self.id, index])
        return lib.book.Book.read(row)

    @classmethod
    def execute(cls, query: str, data: Tuple) -> Row:
        row = cls.cursor.execute(query, data).fetchone()

        cls.connection.commit()

        return row

    @classmethod
    # Necessary because sometimes we'll be saving a new Bible and sometimes
    # we'll be loading it from a database. And sometimes we may be
    # overwriting / editing an exist bible.
    def create(cls, translation: str) -> Self:
        query = f"INSERT INTO {cls.table} (translation) VALUES (?)"
        row = cls.execute(query, (translation,))
        
        bible = Bible(translation)
        bible.id = Bible.cursor.lastrowid
        
        return bible

    @classmethod
    def read(cls, attributes: Dict) -> Self:
        sieve = " ".join([f"{key} = ?" for key in attributes.keys()])
        query = f"SELECT * FROM {cls.table} where {sieve}"
        row = cls.execute(query, attributes.values())
        
        return Bible.from_row(row)
    
    # This is sort of copied mindlessly from the update method in book.
    # Might not need this much pagentry; may be justified by later changes. Idk.
    @classmethod
    def update(cls, id: int, attributes: Dict) -> Self:
        update = " ".join([f"{key} = ?" for key in attributes.keys()])
        query = f"UPDATE {cls.table} SET {update} WHERE id = ?"

        row = cls.execute(query, [attributes.values] + [id])

        return cls.form_row(row)

    @classmethod
    # Thought about making this more flexible with an attribute object;
    # currently think it's dumb.
    def delete(cls, id: int) -> Self:
        query = f"DELETE FROM {cls.table} WHERE id = ?"
        return cls.execute(query, (id,)).fetchone()

    @classmethod
    # Create a Bible object from an XML file
    def from_xml(cls, xml_path: str) -> Self:
        tree = ElementTree.parse(xml_path)
        root = tree.getroot()
        return cls.from_tree_node(root)

    @classmethod
    def from_tree_node(cls, node: ElementTree, database="db/bible.db") -> Self:
        bible = None
        
        cls.database = database
        cls.connection = sqlite3.connect(database)
        cls.cursor = Bible.connection.cursor()
        
        for bible_tag in node.iter():
            if bible_tag.tag != "bible":
                continue
            bible = cls.create(bible_tag.attrib["translation"])
            for testament_tag in bible_tag.iter():
                if testament_tag.tag != "testament":
                    continue
                lib.testament.Testament.from_tree_node(testament_tag, bible)


        if not bible:
            raise Exception(f"Bible#from_tree_node failed to parse node: {node}")
        
        return bible

    @classmethod
    def from_row(cls, row: Row) -> Self:
        bible = cls(row["translation"])
        bible.id = row["id"]
        return bible

    @classmethod
    def initialize_db(cls):
        cls.database = "db/bible.db"
        cls.connection.close()
        os.remove(cls.database)
        cls.connection = sqlite3.connect("db/bible.db")
        cls.cursor = cls.connection.cursor()

        cls.cursor.execute("CREATE TABLE bibles (translation)")
        cls.cursor.execute("CREATE TABLE testaments (name, bible)")
        cls.cursor.execute("CREATE TABLE books (name, ordinal, testament, bible)")
        cls.cursor.execute("CREATE TABLE chapters (number, book)")
        cls.cursor.execute("CREATE TABLE verses (number,  text, chapter, audio_path)")