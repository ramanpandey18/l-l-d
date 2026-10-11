"""
Demonstration: two threads racing to borrow the SAME single copy of a book.
We add a tiny artificial delay between "check" and "act" to widen the race
window - in real systems this gap is filled by things like a database call,
which is exactly when races like this actually bite.
"""
import threading
import time
from datetime import date, timedelta
from typing import List, Optional
import uuid


class BookCopy:
    def __init__(self, isbn: str):
        self.copy_id: Optional[str] = None
        self.isbn = isbn
        self.status = "available"
        self.borrowed_by: Optional[str] = None


class UnsafeLibrary:
    """Same borrow logic as our Library, but WITHOUT a lock, and with an
    artificial delay inserted between the check and the update to make the
    race condition reliably visible."""

    def __init__(self):
        self.copies: List[BookCopy] = []

    def borrow_book_unsafe(self, isbn: str, member_id: str):
        found_copy = None
        for copy in self.copies:
            if copy.isbn == isbn and copy.status == "available":
                found_copy = copy
                break
        if found_copy is None:
            raise ValueError(f"{member_id}: no available copy")

        time.sleep(0.01)  # <-- artificial gap between "check" and "act"

        found_copy.status = "borrowed"
        found_copy.borrowed_by = member_id
        print(f"{member_id} successfully borrowed copy {found_copy.copy_id}")


# Set up ONE single copy of a book - only one person should be able to get it
lib = UnsafeLibrary()
only_copy = BookCopy("111")
only_copy.copy_id = "copy-1"
lib.copies.append(only_copy)

results = {}

def try_borrow(member_name):
    try:
        lib.borrow_book_unsafe("111", member_name)
        results[member_name] = "SUCCESS"
    except ValueError as e:
        results[member_name] = f"FAILED: {e}"

thread1 = threading.Thread(target=try_borrow, args=("Alice",))
thread2 = threading.Thread(target=try_borrow, args=("Bob",))

thread1.start()
thread2.start()
thread1.join()
thread2.join()

print("\n--- Results ---")
for name, outcome in results.items():
    print(f"{name}: {outcome}")

success_count = sum(1 for v in results.values() if v == "SUCCESS")
print(f"\nCopy's final borrowed_by: {only_copy.borrowed_by}")
print(f"Number of threads that think they succeeded: {success_count}")
if success_count > 1:
    print("BUG CONFIRMED: more than one thread believes it borrowed the same single copy!")
