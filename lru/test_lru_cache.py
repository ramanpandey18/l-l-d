import threading

import pytest
from lru_cache import LRUCache


# ---------- construction ----------

def test_zero_capacity_raises():
    with pytest.raises(ValueError):
        LRUCache(0)


def test_negative_capacity_raises():
    with pytest.raises(ValueError):
        LRUCache(-1)


# ---------- get / put basics ----------

def test_put_then_get():
    cache = LRUCache(2)
    cache.put(1, "a")

    assert cache.get(1) == "a"


def test_get_missing_key_raises():
    cache = LRUCache(2)

    with pytest.raises(KeyError):
        cache.get(99)


def test_put_updates_existing_key_value():
    cache = LRUCache(2)
    cache.put(1, "a")
    cache.put(1, "b")

    assert cache.get(1) == "b"


def test_updating_existing_key_does_not_change_size():
    cache = LRUCache(2)
    cache.put(1, "a")
    cache.put(2, "b")
    cache.put(1, "z")  # update, not a new key

    assert len(cache.cache) == 2


# ---------- eviction ----------

def test_eviction_when_over_capacity():
    cache = LRUCache(2)
    cache.put(1, "a")
    cache.put(2, "b")
    cache.put(3, "c")  # should evict key 1 (least recently used)

    with pytest.raises(KeyError):
        cache.get(1)

    assert cache.get(2) == "b"
    assert cache.get(3) == "c"


def test_get_marks_key_as_recently_used_protecting_it_from_eviction():
    cache = LRUCache(2)
    cache.put(1, "a")
    cache.put(2, "b")
    cache.get(1)          # 1 is now most recently used
    cache.put(3, "c")     # should evict 2, not 1

    assert cache.get(1) == "a"
    with pytest.raises(KeyError):
        cache.get(2)
    assert cache.get(3) == "c"


def test_put_on_existing_key_marks_it_recently_used():
    cache = LRUCache(2)
    cache.put(1, "a")
    cache.put(2, "b")
    cache.put(1, "z")     # updating 1 should mark it most recently used
    cache.put(3, "c")     # should evict 2, not 1

    assert cache.get(1) == "z"
    with pytest.raises(KeyError):
        cache.get(2)


def test_capacity_one_immediate_eviction():
    cache = LRUCache(1)
    cache.put(1, "a")
    cache.put(2, "b")     # should immediately evict 1

    with pytest.raises(KeyError):
        cache.get(1)
    assert cache.get(2) == "b"


def test_repeated_access_pattern_full_trace():
    """Mirrors the classic LeetCode LRU example end to end."""
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1        # cache: {2, 1}, 2 is now LRU

    cache.put(3, 3)                 # evicts 2
    with pytest.raises(KeyError):
        cache.get(2)

    cache.put(4, 4)                 # evicts 1
    with pytest.raises(KeyError):
        cache.get(1)

    assert cache.get(3) == 3
    assert cache.get(4) == 4


# ---------- delete ----------

def test_delete_existing_key():
    cache = LRUCache(2)
    cache.put(1, "a")

    cache.delete(1)

    with pytest.raises(KeyError):
        cache.get(1)


def test_delete_missing_key_raises():
    cache = LRUCache(2)

    with pytest.raises(KeyError):
        cache.delete(99)


def test_delete_frees_capacity_for_new_entries():
    cache = LRUCache(1)
    cache.put(1, "a")
    cache.delete(1)

    cache.put(2, "b")  # should succeed without needing to evict anything

    assert cache.get(2) == "b"


# ---------- linked list integrity (internal structure check) ----------

def test_internal_list_matches_lru_order():
    cache = LRUCache(3)
    cache.put(1, "a")
    cache.put(2, "b")
    cache.put(3, "c")
    cache.get(1)  # 1 becomes most recently used

    order = []
    node = cache.head.next
    while node is not cache.tail:
        order.append(node.key)
        node = node.next

    assert order == [2, 3, 1]  # LRU -> MRU


# ---------- Concurrency ----------

def test_concurrent_put_at_capacity_no_corruption():
    """Many threads putting distinct keys into a small-capacity cache at
    once should never corrupt the linked list or leave more entries than
    capacity allows."""
    cache = LRUCache(5)

    def worker(start):
        for i in range(start, start + 20):
            cache.put(i, f"val-{i}")

    threads = [threading.Thread(target=worker, args=(i * 20,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # cache must never exceed capacity, and the dict + linked list must
    # agree on exactly how many entries exist
    assert len(cache.cache) <= cache.capacity

    order = []
    node = cache.head.next
    while node is not cache.tail:
        order.append(node.key)
        node = node.next

    assert len(order) == len(cache.cache)
    assert set(order) == set(cache.cache.keys())


def test_concurrent_get_and_put_no_corruption():
    """Interleaved get/put from multiple threads should never corrupt the
    structure - checked by verifying dict and linked list stay consistent."""
    cache = LRUCache(10)
    for i in range(10):
        cache.put(i, f"val-{i}")

    def reader():
        for _ in range(100):
            for i in range(10):
                try:
                    cache.get(i)
                except KeyError:
                    pass

    def writer(start):
        for i in range(start, start + 50):
            cache.put(i, f"val-{i}")

    threads = [
        threading.Thread(target=reader),
        threading.Thread(target=reader),
        threading.Thread(target=writer, args=(100,)),
        threading.Thread(target=writer, args=(200,)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    order = []
    node = cache.head.next
    while node is not cache.tail:
        order.append(node.key)
        node = node.next

    assert len(order) == len(cache.cache) <= cache.capacity
    assert set(order) == set(cache.cache.keys())
