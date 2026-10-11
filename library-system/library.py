from typing import List, Optional
from datetime import date, timedelta
import uuid
import threading

class Book:
    def __init__(self, title: str, author: str, isbn: str):
        self.title = title
        self.author = author
        self.isbn = isbn

class BookCopy:
    def __init__(self, isbn: str):
        self.copy_id: Optional[str] = None
        self.isbn = isbn
        self.status = "available"
        self.borrowed_by: Optional[str] = None
        self.due_date: Optional[date] = None

class Member:
    def __init__(self, name: str):
        self.id: Optional[str] = None
        self.name = name
        self.borrowed_books = []
        self.fines_owed: float = 0.0

class Library:
    MAX_BOOKS_PER_MEMBER = 3
    LOAN_PERIOD_DAYS = 14
    FINE_PER_DAY = 1

    def __init__(self):
        self.catalog: List[Book] = []
        self.copies: List[BookCopy] = []
        self.members: List[Member] = []
        self.lock = threading.Lock()

    def add_book(self, book: Book):
        if book.title == "":
            raise ValueError("title cannot be empty.")
        if book.author == "":
            raise ValueError("author cannot be empty.")
        if book.isbn == "":
            raise ValueError("unique id cannot be empty.")

        self.catalog.append(book)

    def add_copy(self, isbn):
        if isbn == "":
            raise ValueError("book id cannot be empty for book copy.")
        book_found = None
        for book in self.catalog:
            if isbn == book.isbn:
                book_found = book
                break
        if book_found is None:
            raise ValueError("book copy not found.")

        book_copy = BookCopy(isbn)
        book_copy.copy_id = str(uuid.uuid4())
        self.copies.append(book_copy)

    def register_member(self, member: Member):
        if member.name == "":
            raise ValueError("member name cannot be empty.")

        member.id = str(uuid.uuid4())
        self.members.append(member)

    def borrow_book(self, isbn: str, member_id: str):
        if isbn.strip() == "":
            raise ValueError("isbn not available.")
        if member_id.strip() == "":
            raise ValueError("member_id not available.")
        with self.lock:
            found_copy = None
            for current_copy in self.copies:
                if current_copy.isbn == isbn and current_copy.status == "available":
                    found_copy = current_copy
                    break
            if found_copy is None:
                raise ValueError("Book is not available or does not exist.")

            found_member = None
            for current_member in self.members:
                if current_member.id == member_id:
                    found_member = current_member
                    break
            if found_member is None:
                raise ValueError("user not found.")

            if len(found_member.borrowed_books) >= self.MAX_BOOKS_PER_MEMBER:
                raise ValueError("Member has reached the maximum borrow limit.")

            found_copy.status = "borrowed"
            found_copy.borrowed_by = found_member.id
            found_copy.due_date = date.today() + timedelta(days = self.LOAN_PERIOD_DAYS)
            found_member.borrowed_books.append(found_copy)

    def return_book(self, isbn: str, member_id: str) -> float:
        if isbn.strip() == "":
            raise ValueError("isbn not available.")
        if member_id.strip() == "":
            raise ValueError("member_id not available.")
        with self.lock:
            found_copy = None
            for current_copy in self.copies:
                if current_copy.isbn == isbn and current_copy.status == "borrowed":
                    found_copy = current_copy
                    break
            if found_copy is None:
                raise ValueError("Book is not available or does not exist.")

            if found_copy.borrowed_by != member_id:
                raise ValueError("This member did not borrow this book.")

            if found_copy.due_date is None:
                raise ValueError("This copy has no due date recorded.")

            found_member = None
            for current_member in self.members:
                if current_member.id == member_id:
                    found_member = current_member
                    break
            if found_member is None:
                raise ValueError("user not found.")

            due = 0.0
            total_days = (date.today() - found_copy.due_date).days
            if total_days > 0:
                due += self.FINE_PER_DAY * total_days

            found_copy.status = "available"
            found_copy.borrowed_by = None
            found_copy.due_date = None

            found_member.borrowed_books.remove(found_copy)
            found_member.fines_owed += due

        return due

    def search_book(self, query: str):
        if query.strip() == "":
            raise ValueError("query cannot be empty.")

        results = []
        for book in self.catalog:
            if query.casefold() in book.title.casefold() or query.casefold() in book.author.casefold():
                available_count = 0
                for copy in self.copies:
                    if book.isbn == copy.isbn and copy.status == "available":
                        available_count += 1

                results.append((book, available_count))

        return results
