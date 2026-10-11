import threading
from datetime import date, timedelta

import pytest
from library import Book, BookCopy, Member, Library


# ---------- add_book ----------

def test_add_book_success():
    lib = Library()
    book = Book("1984", "George Orwell", "111")

    lib.add_book(book)

    assert len(lib.catalog) == 1
    assert lib.catalog[0] is book


def test_add_book_empty_title_raises():
    lib = Library()
    book = Book("", "George Orwell", "111")

    with pytest.raises(ValueError):
        lib.add_book(book)


def test_add_book_empty_author_raises():
    lib = Library()
    book = Book("1984", "", "111")

    with pytest.raises(ValueError):
        lib.add_book(book)


def test_add_book_empty_isbn_raises():
    lib = Library()
    book = Book("1984", "George Orwell", "")

    with pytest.raises(ValueError):
        lib.add_book(book)


# ---------- add_copy ----------

def test_add_copy_success():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))

    lib.add_copy("111")

    assert len(lib.copies) == 1
    assert lib.copies[0].isbn == "111"
    assert lib.copies[0].status == "available"
    assert lib.copies[0].copy_id is not None


def test_add_copy_multiple_copies_same_isbn():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))

    lib.add_copy("111")
    lib.add_copy("111")
    lib.add_copy("111")

    assert len(lib.copies) == 3
    # each copy should have its own unique copy_id
    copy_ids = {copy.copy_id for copy in lib.copies}
    assert len(copy_ids) == 3


def test_add_copy_unknown_isbn_raises():
    lib = Library()
    # no book added to catalog at all

    with pytest.raises(ValueError):
        lib.add_copy("does-not-exist")


def test_add_copy_empty_isbn_raises():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))

    with pytest.raises(ValueError):
        lib.add_copy("")


# ---------- register_member ----------

def test_register_member_success():
    lib = Library()
    member = Member("Alice")

    lib.register_member(member)

    assert member.id is not None
    assert len(lib.members) == 1
    assert lib.members[0].name == "Alice"
    assert lib.members[0].fines_owed == 0.0


def test_register_member_empty_name_raises():
    lib = Library()
    member = Member("")

    with pytest.raises(ValueError):
        lib.register_member(member)


# ---------- borrow_book ----------

def test_borrow_book_success():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")
    member = Member("Alice")
    lib.register_member(member)

    lib.borrow_book("111", member.id)

    copy = lib.copies[0]
    assert copy.status == "borrowed"
    assert copy.borrowed_by == member.id
    assert copy in member.borrowed_books


def test_borrow_book_sets_due_date():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")
    member = Member("Alice")
    lib.register_member(member)

    lib.borrow_book("111", member.id)

    copy = lib.copies[0]
    assert copy.due_date == date.today() + timedelta(days=Library.LOAN_PERIOD_DAYS)


def test_borrow_book_picks_any_available_copy():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")
    lib.add_copy("111")
    member = Member("Alice")
    lib.register_member(member)

    lib.borrow_book("111", member.id)

    borrowed_count = sum(1 for c in lib.copies if c.status == "borrowed")
    available_count = sum(1 for c in lib.copies if c.status == "available")
    assert borrowed_count == 1
    assert available_count == 1


def test_borrow_second_copy_when_first_already_borrowed():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")
    lib.add_copy("111")
    alice = Member("Alice")
    bob = Member("Bob")
    lib.register_member(alice)
    lib.register_member(bob)

    lib.borrow_book("111", alice.id)   # takes the first available copy
    lib.borrow_book("111", bob.id)     # should get the second copy, not fail

    assert all(c.status == "borrowed" for c in lib.copies)


def test_borrow_nonexistent_isbn_raises():
    lib = Library()
    member = Member("Alice")
    lib.register_member(member)

    with pytest.raises(ValueError):
        lib.borrow_book("does-not-exist", member.id)


def test_borrow_when_no_copies_added_raises():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))  # title exists, but no copies
    member = Member("Alice")
    lib.register_member(member)

    with pytest.raises(ValueError):
        lib.borrow_book("111", member.id)


def test_borrow_when_all_copies_borrowed_raises():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")
    alice = Member("Alice")
    bob = Member("Bob")
    lib.register_member(alice)
    lib.register_member(bob)
    lib.borrow_book("111", alice.id)  # takes the only copy

    with pytest.raises(ValueError):
        lib.borrow_book("111", bob.id)


def test_borrow_book_invalid_member_raises():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")

    with pytest.raises(ValueError):
        lib.borrow_book("111", "no-such-member-id")


def test_borrow_book_at_limit_raises():
    lib = Library()
    member = Member("Alice")
    lib.register_member(member)

    for i in range(Library.MAX_BOOKS_PER_MEMBER):
        isbn = f"isbn-{i}"
        lib.add_book(Book(f"Book {i}", "Some Author", isbn))
        lib.add_copy(isbn)
        lib.borrow_book(isbn, member.id)

    lib.add_book(Book("Extra Book", "Some Author", "isbn-extra"))
    lib.add_copy("isbn-extra")

    with pytest.raises(ValueError):
        lib.borrow_book("isbn-extra", member.id)


# ---------- return_book ----------

def test_return_book_success_no_fine_when_on_time():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")
    member = Member("Alice")
    lib.register_member(member)
    lib.borrow_book("111", member.id)

    fine = lib.return_book("111", member.id)

    copy = lib.copies[0]
    assert fine == 0.0
    assert member.fines_owed == 0.0
    assert copy.status == "available"
    assert copy.borrowed_by is None
    assert copy.due_date is None
    assert copy not in member.borrowed_books


def test_return_book_late_charges_fine():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")
    member = Member("Alice")
    lib.register_member(member)
    lib.borrow_book("111", member.id)

    # simulate the copy being 5 days overdue
    lib.copies[0].due_date = date.today() - timedelta(days=5)

    fine = lib.return_book("111", member.id)

    assert fine == 5 * Library.FINE_PER_DAY
    assert member.fines_owed == 5 * Library.FINE_PER_DAY


def test_return_book_fines_accumulate_across_multiple_late_returns():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")
    lib.add_copy("111")
    member = Member("Alice")
    lib.register_member(member)

    lib.borrow_book("111", member.id)
    lib.copies[0].due_date = date.today() - timedelta(days=2)
    lib.return_book("111", member.id)

    lib.borrow_book("111", member.id)
    lib.copies[0].due_date = date.today() - timedelta(days=3)
    lib.return_book("111", member.id)

    assert member.fines_owed == 5 * Library.FINE_PER_DAY


def test_return_book_by_wrong_member_raises():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")
    alice = Member("Alice")
    bob = Member("Bob")
    lib.register_member(alice)
    lib.register_member(bob)
    lib.borrow_book("111", alice.id)

    with pytest.raises(ValueError):
        lib.return_book("111", bob.id)


def test_return_book_never_borrowed_raises():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")
    member = Member("Alice")
    lib.register_member(member)

    with pytest.raises(ValueError):
        lib.return_book("111", member.id)


def test_return_book_invalid_member_raises():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")
    member = Member("Alice")
    lib.register_member(member)
    lib.borrow_book("111", member.id)

    with pytest.raises(ValueError):
        lib.return_book("111", "no-such-member-id")


# ---------- search_book ----------

def test_search_book_by_title_returns_book_and_count():
    lib = Library()
    book = Book("1984", "George Orwell", "111")
    lib.add_book(book)
    lib.add_copy("111")
    lib.add_copy("111")

    results = lib.search_book("1984")

    assert len(results) == 1
    found_book, available_count = results[0]
    assert found_book is book
    assert available_count == 2


def test_search_book_by_author_case_insensitive():
    lib = Library()
    book = Book("Golang", "Google", "111")
    lib.add_book(book)
    lib.add_copy("111")

    results = lib.search_book("google")

    assert len(results) == 1
    found_book, available_count = results[0]
    assert found_book is book
    assert available_count == 1


def test_search_book_count_excludes_borrowed_copies():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")
    lib.add_copy("111")
    member = Member("Alice")
    lib.register_member(member)
    lib.borrow_book("111", member.id)  # one of the two copies is now borrowed

    results = lib.search_book("1984")

    _, available_count = results[0]
    assert available_count == 1


def test_search_book_title_with_no_copies_returns_zero_count():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    # no copies added at all

    results = lib.search_book("1984")

    _, available_count = results[0]
    assert available_count == 0


def test_search_book_no_match_returns_empty_list():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")

    results = lib.search_book("nonexistent")

    assert results == []


def test_search_book_empty_query_raises():
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))

    with pytest.raises(ValueError):
        lib.search_book("")


# ---------- concurrency ----------

def test_concurrent_borrow_only_one_winner_for_single_copy():
    """Two threads race to borrow the SAME single copy. Exactly one must win."""
    lib = Library()
    lib.add_book(Book("1984", "George Orwell", "111"))
    lib.add_copy("111")  # only one copy exists

    alice = Member("Alice")
    bob = Member("Bob")
    lib.register_member(alice)
    lib.register_member(bob)

    results = {}

    def attempt(name, member_id):
        try:
            lib.borrow_book("111", member_id)
            results[name] = "SUCCESS"
        except ValueError:
            results[name] = "FAILED"

    t1 = threading.Thread(target=attempt, args=("Alice", alice.id))
    t2 = threading.Thread(target=attempt, args=("Bob", bob.id))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    success_count = sum(1 for outcome in results.values() if outcome == "SUCCESS")
    assert success_count == 1


def test_concurrent_borrow_consistent_across_many_runs():
    """Repeat the race multiple times to rule out a single lucky pass."""
    for _ in range(20):
        lib = Library()
        lib.add_book(Book("1984", "George Orwell", "111"))
        lib.add_copy("111")
        alice = Member("Alice")
        bob = Member("Bob")
        lib.register_member(alice)
        lib.register_member(bob)

        results = {}

        def attempt(name, member_id, target_lib=lib):
            try:
                target_lib.borrow_book("111", member_id)
                results[name] = "SUCCESS"
            except ValueError:
                results[name] = "FAILED"

        t1 = threading.Thread(target=attempt, args=("Alice", alice.id))
        t2 = threading.Thread(target=attempt, args=("Bob", bob.id))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        success_count = sum(1 for outcome in results.values() if outcome == "SUCCESS")
        assert success_count == 1
