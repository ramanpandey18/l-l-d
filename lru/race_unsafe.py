"""
Multiple threads call put() on the SAME LRUCache at once, without a lock.
The linked list pointer-rewiring in _insert_at_front/_remove is a multi-step
"read some pointers, then write them" sequence - if two threads interleave
partway through, the list's prev/next pointers can end up inconsistent
with each other, corrupting the structure (nodes lost, cycles formed, or
the dict and list disagreeing about what's actually in the cache).

A tiny artificial delay is inserted mid-operation to reliably force the
interleaving that would otherwise only happen rarely by chance.
"""
import threading
import time


class UnsafeNode:
    def __init__(self, key, val):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None


class UnsafeLRUCache:
    """Same logic as LRUCache, but WITHOUT a lock, and with an artificial
    delay inserted in the middle of the pointer-rewiring."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = {}
        self.head = UnsafeNode(0, 0)
        self.tail = UnsafeNode(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _insert_at_front(self, node):
        mru_node = self.tail.prev
        mru_node.next = node
        time.sleep(0.001)  # <-- artificial gap mid pointer-rewiring
        node.prev = mru_node
        node.next = self.tail
        self.tail.prev = node

    def _remove(self, node):
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

    def put_unsafe(self, key, val):
        if key in self.cache:
            node = self.cache[key]
            node.val = val
            self._remove(node)
            self._insert_at_front(node)
        else:
            new_node = UnsafeNode(key, val)
            self.cache[key] = new_node
            self._insert_at_front(new_node)
            if len(self.cache) > self.capacity:
                lru_node = self.head.next
                self._remove(lru_node)
                del self.cache[lru_node.key]

    def order(self):
        result = []
        node = self.head.next
        seen = set()
        # guard against infinite loop if a cycle was corrupted into the list
        while node is not self.tail and node.key not in seen:
            seen.add(node.key)
            result.append(node.key)
            node = node.next
        return result


cache = UnsafeLRUCache(capacity=10)

def worker(start):
    for i in range(start, start + 10):
        cache.put_unsafe(i, f"val-{i}")

threads = [threading.Thread(target=worker, args=(i * 10,)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()

list_order = cache.order()
dict_keys = set(cache.cache.keys())
list_keys = set(list_order)

print(f"Dict has {len(dict_keys)} entries, capacity is {cache.capacity}")
print(f"Linked list has {len(list_order)} reachable entries")
print(f"Dict keys:  {sorted(dict_keys)}")
print(f"List keys:  {sorted(list_keys)}")
print(f"Do they match? {dict_keys == list_keys}")

if dict_keys != list_keys or len(dict_keys) > cache.capacity:
    print("\nBUG CONFIRMED: the dict and linked list disagree, or capacity was violated -")
    print("the linked list has been corrupted by unsynchronized concurrent access.")
