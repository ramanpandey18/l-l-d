from typing import Optional, Dict
import threading
import math
import uuid

class User:
    def __init__(self, name):
        self.id: Optional[str] = None
        self.name = name

class Url:
    def __init__(self, user_id: str, long_url: str):
        self.user_id = user_id
        self.long_url = long_url
        self.short_code: Optional[str] = None

class ShortUrl:
    ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.urls: Dict[str, Url] = {}  # short_code -> Url
        self.user_url_lookup: Dict[tuple, str] = {}  # (user_id, long_url) -> short_code
        self.counter: int = 0
        self.lock = threading.Lock()

    def add_user(self, user: User) -> str | None:
        if not isinstance(user, User):
            raise TypeError("Expected a User instance")

        if not isinstance(user.name, str) or not user.name.strip():
            raise ValueError("Invalid or empty user name")
        with self.lock:
            if user.id is None:
                user.id = str(uuid.uuid4())
            # assert user.id is not None  # Narrows user.id from `str | None` to `str`
            # self.users[user.id] = user
            self.users[user.id] = user
        return user.id

    def _encode_base62(self, number: int) -> str:
        if number == 0:
            return self.ALPHABET[0]
        chars = []
        while number > 0:
            remainder = number % 62
            chars.append(self.ALPHABET[remainder])
            number //= 62
        return "".join(reversed(chars))

    def shorten(self, user_id, url) -> str | None:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user id is empty or invalid.")

        if not isinstance(url, str) or not url.strip():
            raise ValueError("url is empty or invalid.")

        with self.lock:
            if user_id not in self.users:
                raise ValueError(f"User with ID {user_id} does not exist.")
            key = (user_id, url)

            if key in self.user_url_lookup:
                return self.user_url_lookup[key]

            self.counter += 1
            short_code = self._encode_base62(self.counter)

            url_obj = Url(user_id, url)
            url_obj.short_code = short_code

            self.urls[short_code] = url_obj
            self.user_url_lookup[key] = short_code
            return short_code

    def resolve(self, short_url) -> str | None:
        if not isinstance(short_url, str) or not short_url.strip():
            raise ValueError("url is empty or invalid.")
        with self.lock:
            url_obj = self.urls.get(short_url)
            if url_obj is None:
                raise ValueError(f"Unable to resolve url {short_url}")
            return url_obj.long_url

    def resolve_v2(self, user_id, short_url) -> str | None:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user id is empty or invalid.")

        if not isinstance(short_url, str) or not short_url.strip():
            raise ValueError("url is empty or invalid.")

        with self.lock:
            url_obj = self.urls.get(short_url)
            if url_obj is None:
                raise ValueError(f"Unable to resolve url {short_url} for user {user_id}")
            return url_obj.long_url
