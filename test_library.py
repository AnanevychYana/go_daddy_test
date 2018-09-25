import os
import random
from string import ascii_letters
from typing import List
import unittest
from xml.etree import ElementTree as et

from library import Library, DuplicatedBookTitleError, BookNotFoundError, WrongXmlPathError


def random_book() -> dict:
    return {
        'title': random_word(),
        'year': random.randint(0, 2018),
        'category': random_word(),
        'authors': [random_word() for _ in range(random.randint(1, 10))],
        'price': random.uniform(0, 1000),
        'language': random_word(),
        'cover': random_word()
    }


def random_word(length: int = None, chars: str = ascii_letters) -> str:
    length = length or random.randint(1, 64)
    return "".join([random.choice(chars) for _ in range(length)])


def create_books_xml_file(books: List[dict], filename: str):
    root = et.Element('books')
    tree = et.ElementTree(root)
    for book in books:
        root.append(book_to_xml_elem(book))
    with open(filename, 'wb') as f:
        tree.write(f, encoding='utf-8')


def book_to_xml_elem(book: dict) -> et.Element:
    item = et.Element('book')
    simple_fields = ('title', 'year', 'category', 'price', 'language', 'cover')
    for field in simple_fields:
        element = et.Element(field)
        element.text = str(book[field])
        item.append(element)
    for author in book['authors']:
        element = et.Element('author')
        element.text = author
        item.append(element)
    return item


class LibraryTest(unittest.TestCase):
    def setUp(self):
        self.library = Library()

    def tearDown(self):
        self.library.clean()

    def assert_books_equal(self, book1, book2):
        self.assertEqual(book1['title'], book2['title'])
        self.assertEqual(book1['category'], book2['category'])
        self.assertEqual(book1['year'], book2['year'])
        self.assertEqual(book1['language'], book2['language'])
        self.assertEqual(book1['cover'], book2['cover'])
        self.assertListEqual(book1['authors'], book2['authors'])

    def test_add_book(self):
        book = random_book()
        self.library.add_book(book['category'], book['title'], book['authors'], book['year'], book['price'],
                              book['language'], book['cover'])
        book_from_db = self.library.get_all_books()[0]
        self.assert_books_equal(book, book_from_db)

    def test_add_book_existing_title(self):
        book = random_book()
        self.library.add_book(book['category'], book['title'], book['authors'], book['year'], book['price'],
                              book['language'], book['cover'])
        self.assertRaises(DuplicatedBookTitleError, self.library.add_book, book['category'], book['title'],
                          book['authors'], book['year'], book['price'], book['language'], book['cover'])

    def test_get_books(self):
        books_from_db = self.library.get_all_books()
        self.assertEqual(len(books_from_db), 0)
        books = [random_book() for _ in range(10)]
        for book in books:
            self.library.add_book(book['category'], book['title'], book['authors'], book['year'], book['price'],
                                  book['language'], book['cover'])
        books_from_db = self.library.get_all_books()
        for book, book_from_db in zip(books, books_from_db):
            self.assert_books_equal(book, book_from_db)

    def test_remove_book(self):
        books = [random_book() for _ in range(10)]
        for book in books:
            self.library.add_book(book['category'], book['title'], book['authors'], book['year'], book['price'],
                                  book['language'], book['cover'])
        index = random.randint(0, 9)
        self.library.remove_book(books[index]['title'])
        books_from_db = self.library.get_all_books()
        self.assertNotIn(books[index], books_from_db)

    def test_remove_book_with_not_existing_title(self):
        title = random_word()
        self.assertRaises(BookNotFoundError, self.library.remove_book, title)

    def test_check_book_exist(self):
        title = random_word()
        self.assertFalse(self.library.check_book_exist(title))
        book = random_book()
        self.library.add_book(book['category'], book['title'], book['authors'], book['year'], book['price'],
                              book['language'], book['cover'])
        self.assertTrue(self.library.check_book_exist(book['title']))

    def test_books_from_xml(self):
        books = [random_book() for _ in range(10)]
        # Creating test XML file
        filename = f"{random_word()}.xml"
        create_books_xml_file(books, filename)
        self.library.books_from_xml(filename)
        books_from_db = self.library.get_all_books()
        for book, book_from_db in zip(books, books_from_db):
            self.assert_books_equal(book, book_from_db)
        os.remove(filename)
        self.assertRaises(WrongXmlPathError, self.library.books_from_xml, random_word())

    def test_clean(self):
        books = [random_book() for _ in range(10)]
        for book in books:
            self.library.add_book(book['category'], book['title'], book['authors'], book['year'], book['price'],
                                  book['language'], book['cover'])
        books_from_db = self.library.get_all_books()
        self.assertEqual(len(books_from_db), 10)
        self.library.clean()
        books_from_db = self.library.get_all_books()
        self.assertEqual(len(books_from_db), 0)
