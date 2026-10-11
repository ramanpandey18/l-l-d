import threading

import pytest
from url_shortener import User, Url, ShortUrl


# ---------- add_user ----------

def test_add_user_success():
    su = ShortUrl()
    user = User("Alice")

    user_id = su.add_user(user)

    assert user_id is not None
    assert user.id == user_id
    assert su.users[user_id] is user


def test_add_user_wrong_type_raises():
    su = ShortUrl()

    with pytest.raises(TypeError):
        su.add_user("not a user")  # type: ignore


def test_add_user_empty_name_raises():
    su = ShortUrl()
    user = User("")

    with pytest.raises(ValueError):
        su.add_user(user)


def test_add_user_whitespace_name_raises():
    su = ShortUrl()
    user = User("   ")

    with pytest.raises(ValueError):
        su.add_user(user)


# ---------- _encode_base62 ----------

def test_encode_base62_zero():
    su = ShortUrl()
    assert su._encode_base62(0) == "a"


def test_encode_base62_single_digit():
    su = ShortUrl()
    assert su._encode_base62(1) == "b"
    assert su._encode_base62(61) == "9"


def test_encode_base62_rolls_over_to_two_chars():
    su = ShortUrl()
    assert su._encode_base62(62) == "ba"
    assert su._encode_base62(63) == "bb"


def test_encode_base62_rolls_over_to_three_chars():
    su = ShortUrl()
    assert su._encode_base62(62 * 62) == "baa"


def test_encode_base62_produces_unique_codes_for_a_range():
    su = ShortUrl()
    codes = [su._encode_base62(i) for i in range(1000)]
    assert len(codes) == len(set(codes))  # all unique, no collisions


# ---------- shorten ----------

def test_shorten_success_returns_code():
    su = ShortUrl()
    user_id = su.add_user(User("Alice"))

    code = su.shorten(user_id, "https://example.com")

    assert code is not None
    assert su.urls[code].long_url == "https://example.com"
    assert su.urls[code].user_id == user_id


def test_shorten_same_user_same_url_returns_same_code():
    su = ShortUrl()
    user_id = su.add_user(User("Alice"))

    code1 = su.shorten(user_id, "https://example.com")
    code2 = su.shorten(user_id, "https://example.com")

    assert code1 == code2
    assert len(su.urls) == 1  # no duplicate entry was created


def test_shorten_different_users_same_url_get_different_codes():
    su = ShortUrl()
    alice_id = su.add_user(User("Alice"))
    bob_id = su.add_user(User("Bob"))

    alice_code = su.shorten(alice_id, "https://example.com")
    bob_code = su.shorten(bob_id, "https://example.com")

    assert alice_code != bob_code
    assert su.urls[alice_code].user_id == alice_id
    assert su.urls[bob_code].user_id == bob_id


def test_shorten_same_user_different_urls_get_different_codes():
    su = ShortUrl()
    user_id = su.add_user(User("Alice"))

    code1 = su.shorten(user_id, "https://example.com")
    code2 = su.shorten(user_id, "https://another.com")

    assert code1 != code2


def test_shorten_unknown_user_raises():
    su = ShortUrl()

    with pytest.raises(ValueError):
        su.shorten("no-such-user-id", "https://example.com")


def test_shorten_empty_user_id_raises():
    su = ShortUrl()

    with pytest.raises(ValueError):
        su.shorten("", "https://example.com")


def test_shorten_empty_url_raises():
    su = ShortUrl()
    user_id = su.add_user(User("Alice"))

    with pytest.raises(ValueError):
        su.shorten(user_id, "")


def test_shorten_counter_not_wasted_on_repeat_lookup():
    su = ShortUrl()
    user_id = su.add_user(User("Alice"))

    su.shorten(user_id, "https://example.com")
    counter_after_first = su.counter

    su.shorten(user_id, "https://example.com")  # repeat, should not touch counter
    counter_after_repeat = su.counter

    assert counter_after_first == counter_after_repeat


# ---------- resolve ----------

def test_resolve_success():
    su = ShortUrl()
    user_id = su.add_user(User("Alice"))
    code = su.shorten(user_id, "https://example.com")

    resolved = su.resolve(code)

    assert resolved == "https://example.com"


def test_resolve_unknown_code_raises():
    su = ShortUrl()

    with pytest.raises(ValueError):
        su.resolve("does-not-exist")


def test_resolve_empty_code_raises():
    su = ShortUrl()

    with pytest.raises(ValueError):
        su.resolve("")


# ---------- Concurrency ----------

def test_concurrent_shorten_same_user_same_url_only_one_code_created():
    """Two threads race to shorten the SAME (user, url) pair at once.
    Both should end up with the exact same code, and only one Url entry
    should ever be created - not two."""
    su = ShortUrl()
    user_id = su.add_user(User("Alice"))

    results = {}

    def attempt(name):
        code = su.shorten(user_id, "https://example.com")
        results[name] = code

    t1 = threading.Thread(target=attempt, args=("A",))
    t2 = threading.Thread(target=attempt, args=("B",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results["A"] == results["B"]
    assert len(su.urls) == 1


def test_concurrent_shorten_different_urls_no_counter_collisions():
    """Two threads shorten DIFFERENT urls for the same user at once.
    The counter increments must not collide/skip due to the race -
    both should get distinct, valid codes."""
    su = ShortUrl()
    user_id = su.add_user(User("Alice"))

    results = {}

    def attempt(name, url):
        code = su.shorten(user_id, url)
        results[name] = code

    t1 = threading.Thread(target=attempt, args=("A", "https://a.com"))
    t2 = threading.Thread(target=attempt, args=("B", "https://b.com"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results["A"] != results["B"]
    assert len(su.urls) == 2
    assert su.counter == 2