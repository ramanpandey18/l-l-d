"""
Same race scenario, but now against the REAL ShortUrl class (with self.lock)
to prove the fix actually works - run many times to rule out a single lucky pass.
"""
import threading
from url_shortener import User, ShortUrl

successes = []

for run in range(20):
    su = ShortUrl()
    user_id = su.add_user(User("Alice"))

    results = {}

    def attempt(name, target_su=su, target_user_id=user_id):
        code = target_su.shorten(target_user_id, "https://example.com")
        results[name] = code

    t1 = threading.Thread(target=attempt, args=("A",))
    t2 = threading.Thread(target=attempt, args=("B",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    same_code = results["A"] == results["B"]
    only_one_entry = len(su.urls) == 1
    correct = same_code and only_one_entry
    successes.append(correct)

print(f"Runs where both threads got the SAME code and only 1 entry was created: "
      f"{sum(successes)} / {len(successes)}")
print(f"All runs correct: {all(successes)}")
