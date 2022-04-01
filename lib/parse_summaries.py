from typing import Dict

def parse_summaries() -> Dict[str, Dict]:
    lines = open("./text/summaries.txt").readlines()
    lines = [l.rstrip() for l in lines]

    books = open("./text/books.txt").readlines()[1:]
    books = [b.rstrip() for b in books]

    chapters = {b: {} for b in books}
    book = False
    for line in lines:
        chapter_line = book_line = False
        for b in books:
            if line.startswith(b):
                if line.split()[-1].isdigit():
                    if book:
                        chapters[book][chapter_number] = chapters[book][chapter_number].rstrip()
                    book = b
                    chapter_number = int(line.split()[-1])
                    chapter_line = True
                elif b == line:
                    book_line = True
                break
        #print(line)
        if chapter_line:
            chapters[book][chapter_number] = ""
        elif book_line:
            continue
        else:
            chapters[book][chapter_number] += line + " "
    chapters[book][chapter_number] = chapters[book][chapter_number].rstrip()
    return chapters
