"""
Same heavy concurrent workload, but now against the REAL LRUCache class
(with self.lock) to prove the structure stays consistent - run repeatedly
to rule out a single lucky pass.
"""
import threading
from lru_cache import LRUCache

all_correct = []

for run in range(10):
    cache = LRUCache(capacity=10)

    def worker(start):
        for i in range(start, start + 10):
            cache.put(i, f"val-{i}")

    threads = [threading.Thread(target=worker, args=(i * 10,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    order = []
    node = cache.head.next
    while node is not cache.tail:
        order.append(node.key)
        node = node.next

    dict_keys = set(cache.cache.keys())
    list_keys = set(order)

    correct = (
        len(dict_keys) <= cache.capacity
        and len(order) == len(dict_keys)
        and dict_keys == list_keys
    )
    all_correct.append(correct)

print(f"Runs with a fully consistent dict + linked list: {sum(all_correct)} / {len(all_correct)}")
print(f"All runs correct: {all(all_correct)}")
