import sqlite3
#from sqlite3 import Error
import xml.etree.ElementTree as ElementTree
from lib.bible import Bible
from lib.book import Book
from lib.chapter import Chapter
from lib.verse import Verse
from lib.testament import Testament


## CREATE TABLES
# TODO: Add xml path to the Bible table
# TODO: Write a script to rename xml files after their translation name (the 
# attribute in the book tag.)
# TODO: Download all the xml bibles from https://www.beblia.com/pages/bibleXML.aspx?Language=Ewe&DLang=Ewe&Book=40&Chapter=1
# TODO: Download all audio bibles from the same
# TODO: Parse the English ones into versese, using Aeneas or Gentle or whatever
# TODO: Figure out a way to add vocab to gentle alignment tools for better verses
# TODO: Parses xml bibles into our database
# TODO: Actually get back to making these bibles into Anki decks
# TODO: Turn our bible memorization system into a usable web app
# TODO: Make mnemonics / memory palaces that don't suck.
# TODO: Make an API / library for the bible that doesn't suck.

# Parsing the XML Document
Bible.initialize_db()
bible = Bible.from_xml("xml/kjv.xml")