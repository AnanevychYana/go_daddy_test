import argparse
import os
from typing import List, Any
from xml.etree import ElementTree

from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()
engine = create_engine('sqlite:///books.db')
Session = sessionmaker(bind=engine)


class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    language = Column(String)
    cover = Column(String)


class BookNotFoundError(Exception):
    pass


class DuplicatedBookTitleError(Exception):
    pass


class WrongXmlPathError(Exception):
    pass


class Library:
    """
    Responsible for working with DB.
    """
    def __init__(self):
        Base.metadata.create_all(engine)
        self.session = Session()

    def books_from_xml(self, path_to_xml: str):
        """
        Adds books from provided XML file into the DB.
        :param path_to_xml: path to XML file with books.
        """
        records = []
        try:
            xml_file = open(path_to_xml)
        except FileNotFoundError:
            raise WrongXmlPathError(f"File {path_to_xml} doesn't exist")

        root = ElementTree.XML(xml_file.read())
        xml_file.close()

        for child in root:
            record = {}
            authors = []
            if child.attrib:
                record.update(child.attrib)
            for subchild in child:
                if subchild.tag == 'author':
                    authors.append(subchild.text)
                else:
                    record[subchild.tag] = subchild.text
                if subchild.attrib:
                    record.update(subchild.attrib)
            record['authors'] = authors
            records.append(record)

        for record in records:
            self.add_book(record['category'], record['title'], record['authors'], int(record['year']),
                          float(record['price']), record.get('language', None), record.get('cover', None))

    def remove_book(self, name: str):
        """
        Removes first occurrence of the book with specified name from the DB.
        :param name: name of the book to remove.
        """
        book_to_remove = self.session.query(Book).filter_by(title=name).first()
        if book_to_remove:
            self.session.delete(book_to_remove)
            self.session.commit()
        else:
            raise BookNotFoundError(f"Book with title {name} was not found in the system")

    def add_book(self, category: str, title: str, authors: List[str], year: int, price: float, language: str = None,
                 cover: str = None) -> int:
        """
        Adds book to the DB.
        :param category: category of the new book.
        :param title: title of the new book.
        :param authors: list of authors' names of the new book.
        :param year: year of publication of the new book.
        :param price: price of the new book.
        :param language: language of the new book.
        :param cover: cover of the new book.
        :return: id of the newly created book.
        """
        if self.check_book_exist(title):
            raise DuplicatedBookTitleError(f"Book with title {title} already exist in the system")
        new_book = Book(category=category, title=title, author=self._form_author(authors), year=year, price=price,
                        language=language, cover=cover)
        self.session.add(new_book)
        self.session.commit()
        return new_book.id

    def get_all_books(self) -> List[dict]:
        """
        Gets all books in the DB.
        :return: list of all available books.
        """
        books = self.session.query(Book).all()
        books_list = []
        for book in books:
            books_list.append({
                'title': book.title,
                'year': book.year,
                'category': book.category,
                'authors': self._form_authors(book.author),
                'price': book.price,
                'language': book.language,
                'cover': book.cover
            })
        return books_list

    def check_book_exist(self, title: str) -> bool:
        """
        Checks if book with specified title already exist in the system.
        :param title: title of the book to check.
        :return: True if book with provided title already exist, False otherwise.
        """
        book = self.session.query(Book).filter_by(title=title).first()
        return True if book else False

    def clean(self):
        """
        Cleans the DB.
        """
        for book in self.session.query(Book).all():
            self.session.delete(book)
        self.session.commit()

    @staticmethod
    def _form_author(authors: List[str]) -> str:
        """
        Forms string for DB representing authors of the book.
        :param authors: list of names of the authors.
        :return: formed authors string.
        """
        return ','.join(authors)

    @staticmethod
    def _form_authors(author: str) -> List[str]:
        """
        Forms list of string from DB string representing authors of the book.
        :param author: string representing authors of the book.
        :return: formed list of authors.
        """
        return author.split(',')


class Application:
    def __init__(self):
        self.library = Library()

    def execute_command(self):
        """
        Executes command according to command-line arguments.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("-A", "--add", help="add new book to library", action="store_true")
        parser.add_argument("-R", "--remove", help="remove existing book from library")
        parser.add_argument("-P", "--print", help="print all existing books from library", action="store_true")
        parser.add_argument("-X", "--xml", help="add books from provided xml file to library")
        args = parser.parse_args()
        if args.add:
            self.read_book()
        elif args.remove:
            try:
                self.library.remove_book(args.remove)
            except BookNotFoundError:
                print(f"Book with title {args.remove} was not found in the system.")
        elif args.print:
            books = self.library.get_all_books()
            if books:
                self.pretty_print_books(books)
            else:
                print('No books to print in the system.')
        elif args.xml:
            if os.path.isfile(args.xml):
                self.library.books_from_xml(args.xml)
            else:
                print(f"{args.xml} is not a file, provide valid path to file.")

    @staticmethod
    def pretty_print_books(books: List[dict]):
        """
        :param books: list with dicts representing the books.
        """
        for book in books:
            print(f"{book['title']} ({book['year']})")
            print(f"\tCategory: {book['category']}")
            print(f"\tAuthor(s): {', '.join(book['authors'])}")
            print(f"\tPrice: {book['price']}")
            if book['language']:
                print(f"\tLanguage: {book['language']}")
            if book['cover']:
                print(f"\tCover: {book['cover']}")
            print('\n')

    @staticmethod
    def get_input_value(value_name: str = '', required: bool = False, return_type: type = str) -> Any:
        """
        Reads input from stdin.
        :param value_name: name of the input value.
        :param required: specifies if the value could be None.
        :param return_type: return type of the value.
        :return: value from the stdin.
        """
        inp = None
        while inp is None:
            inp = input(f"Please, enter the {value_name}:")
            while not inp and required:
                inp = input(f"The {value_name} is required, please enter again:")
            try:
                inp = return_type(inp)
            except ValueError:
                print(f"Bad input for {value_name}, must be of type {return_type}!")
                inp = None
        inp = inp or None
        return inp

    def read_book(self):
        """
        Reads values from console for the book.
        """
        title = self.get_input_value('title', required=True)
        while self.library.check_book_exist(title):
            print(f"Book with title {title} already exist, please enter different title.")
            title = self.get_input_value('title', required=True)
        category = self.get_input_value('category', required=True)
        authors = []
        author = self.get_input_value(f"author {len(authors) + 1}", required=True)
        authors.append(author)
        while author:
            author = self.get_input_value(f"author {len(authors) + 1}")
            if author:
                authors.append(author)
        year = self.get_input_value('year', required=True, return_type=int)
        price = self.get_input_value('price', required=True, return_type=float)
        language = self.get_input_value('language')
        cover = self.get_input_value('cover')
        self.library.add_book(category, title, authors, year, price, language, cover)


if __name__ == '__main__':
    Application().execute_command()

