"""
Demonstration: two threads race to shorten the SAME (user, url) pair at the
exact same time. Without a lock, both can pass the "does this pair already
exist?" check before either one writes the result, so BOTH end up creating
a brand new short code - defeating the "same user, same url -> same code"
guarantee, and wasting two counter values instead of one.

A tiny artificial delay is inserted between the check and the write to
reliably widen the race window (in real systems, this gap is filled by
things like a database round-trip).
"""
import threading
import time
from typing import Dict, Optional


class UnsafeUrl:
    def __init__(self, user_id: str, long_url: str):
        self.user_id = user_id
        self.long_url = long_url
        self.short_code: Optional[str] = None


class UnsafeShortUrl:
    """Same shorten() logic as ShortUrl, but WITHOUT a lock, and with an
    artificial delay inserted between the check and the write."""

    ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    def __init__(self):
        self.urls: Dict[str, UnsafeUrl] = {}
        self.user_url_lookup: Dict[tuple, str] = {}
        self.counter = 0

    def _encode_base62(self, number: int) -> str:
        if number == 0:
            return self.ALPHABET[0]
        chars = []
        while number > 0:
            remainder = number % 62
            chars.append(self.ALPHABET[remainder])
            number //= 62
        return "".join(reversed(chars))

    def shorten_unsafe(self, user_id: str, url: str) -> str:
        key = (user_id, url)

        if key in self.user_url_lookup:
            return self.user_url_lookup[key]

        time.sleep(0.01)  # <-- artificial gap between "check" and "act"

        self.counter += 1
        short_code = self._encode_base62(self.counter)

        url_obj = UnsafeUrl(user_id, url)
        url_obj.short_code = short_code

        self.urls[short_code] = url_obj
        self.user_url_lookup[key] = short_code
        return short_code


su = UnsafeShortUrl()
results = {}

def try_shorten(name):
    code = su.shorten_unsafe("user-1", "https://example.com")
    results[name] = code

t1 = threading.Thread(target=try_shorten, args=("Thread A",))
t2 = threading.Thread(target=try_shorten, args=("Thread B",))
t1.start()
t2.start()
t1.join()
t2.join()

print("--- Results ---")
for name, code in results.items():
    print(f"{name}: got code '{code}'")

print(f"\nCounter ended at: {su.counter} (should have been 1 if truly deduplicated)")
print(f"Total Url entries created: {len(su.urls)} (should have been 1)")
if len(su.urls) > 1:
    print("BUG CONFIRMED: two different short codes were created for the same (user, url) pair!")
