"""
Same race scenario, but now against the REAL Library class (with self.lock)
to prove the fix actually works, not just in theory.
"""
import threading
from library import Book, Member, Library

lib = Library()
lib.add_book(Book("1984", "George Orwell", "111"))
lib.add_copy("111")  # only ONE copy exists

alice = Member("Alice")
bob = Member("Bob")
lib.register_member(alice)
lib.register_member(bob)

results = {}

def try_borrow(name, member_id):
    try:
        lib.borrow_book("111", member_id)
        results[name] = "SUCCESS"
    except ValueError as e:
        results[name] = f"FAILED: {e}"

thread1 = threading.Thread(target=try_borrow, args=("Alice", alice.id))
thread2 = threading.Thread(target=try_borrow, args=("Bob", bob.id))

# Run the race many times to make sure the lock holds up consistently,
# not just by luck on a single run.
successes_per_run = []
for run in range(20):
    lib2 = Library()
    lib2.add_book(Book("1984", "George Orwell", "111"))
    lib2.add_copy("111")
    a = Member("Alice")
    b = Member("Bob")
    lib2.register_member(a)
    lib2.register_member(b)

    run_results = {}
    def attempt(name, member_id, target_lib):
        try:
            target_lib.borrow_book("111", member_id)
            run_results[name] = "SUCCESS"
        except ValueError:
            run_results[name] = "FAILED"

    t1 = threading.Thread(target=attempt, args=("Alice", a.id, lib2))
    t2 = threading.Thread(target=attempt, args=("Bob", b.id, lib2))
    t1.start(); t2.start()
    t1.join(); t2.join()

    success_count = sum(1 for v in run_results.values() if v == "SUCCESS")
    successes_per_run.append(success_count)

print("Successes per run (should ALWAYS be exactly 1):")
print(successes_per_run)
print(f"\nAll runs had exactly one winner: {all(s == 1 for s in successes_per_run)}")
