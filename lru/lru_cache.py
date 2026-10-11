from typing import Dict
import threading
class Node:
    def __init__(self, key: int, val: int):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None

class LRUCache:
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be greater than 0.")
        self.capacity = capacity
        self.cache: Dict[int, Node] = {}
        self.head = Node(0, 0)  # dummy - most recently used end
        self.tail = Node(0, 0)  # dummy - least recently used end
        self.head.next = self.tail
        self.tail.prev = self.head
        self.lock = threading.Lock()

    # HEAD <-> A <-> B <-> C <-> TAIL
    #     MRU -> C
    #     MRU boundary -> TAIL
    #     LRU boundary -> HEAD
    # We want D to become the new MRU.
    # HEAD <-> A <-> B <-> C <-> D <-> TAIL

    def _insert_at_front(self, node:Node) -> None:
        mru_node = self.tail.prev
        mru_node.next = node
        node.prev = mru_node
        node.next = self.tail
        self.tail.prev = node

    def _remove(self, node: Node) -> None:
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

    def get(self, key: int) -> int:
        with self.lock:
            if key in self.cache:
                self._remove(self.cache[key])
                self._insert_at_front(self.cache[key])
                return self.cache[key].val
            raise KeyError(f"key {key} does not exist in cache.")


    def put(self, key: int, val: int) -> None:
        with self.lock:
            if key in self.cache:
                node = self.cache[key]
                node.val = val
                self._remove(node)
                self._insert_at_front(node)
            else:
                new_node = Node(key, val)
                self.cache[key] = new_node
                self._insert_at_front(self.cache[key])
                if len(self.cache) > self.capacity:
                    lru_node = self.head.next
                    self._remove(lru_node)
                    del self.cache[lru_node.key]

            # If the key already exists, get rid of its old node positioning
            # if key in self.cache:
            #     self._remove(self.cache[key])
            #
            # # Add the fresh node into our structures
            # new_node = Node(key, val)
            # self.cache[key] = new_node
            # self._insert_at_front(self.cache[key])
            # # If we went over capacity, evict the least recently used node (right after head)
            # if len(self.cache) > self.capacity:
            #     lru_node = self.head.next
            #     self._remove(lru_node)
            #     del self.cache[lru_node.key]

    def delete(self, key: int) -> None:
        with self.lock:
            if key in self.cache:
                node = self.cache[key]
                self._remove(node)
                del self.cache[key]
                return
            raise KeyError(f"key {key} does not exist.")
