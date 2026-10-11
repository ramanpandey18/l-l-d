"""
Two separate bugs, demonstrated side by side:

BUG A: without global_lock, many threads hitting a BRAND NEW client_id at
once can each conclude "no bucket exists yet" and each create their OWN
bucket - silently overwriting each other in the dict, and worse, each
bucket thinks it's starting fresh with full capacity, defeating the whole
point of a per-client limit.

BUG B: without the per-bucket lock, concurrent consume() calls on the SAME
bucket can interleave their "read tokens, then write tokens" steps,
letting more requests through than the bucket's capacity allows - the
core promise a rate limiter exists to keep.

Artificial delays are inserted to reliably force each interleaving.
"""
import threading
import time


class UnsafeBucket:
    def __init__(self, capacity, refill_rate, now):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_updated = now

    def consume_unsafe(self, now):
        elapsed = now - self.last_updated
        tokens_now = min(self.capacity, self.tokens + elapsed * self.refill_rate)

        time.sleep(0.001)  # <-- artificial gap between "read" and "write"

        if tokens_now >= 1:
            self.tokens = tokens_now - 1
            self.last_updated = now
            return True
        self.tokens = tokens_now
        self.last_updated = now
        return False


class UnsafeManager:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets = {}

    def get_or_create_bucket_unsafe(self, client_id, now):
        if client_id in self.buckets:
            return self.buckets[client_id]
        time.sleep(0.001)  # <-- artificial gap between "check" and "create"
        bucket = UnsafeBucket(self.capacity, self.refill_rate, now)
        self.buckets[client_id] = bucket
        return bucket


# ---------- BUG A: duplicate bucket creation for a new client ----------
print("=== Bug A: no global lock, racing to create a bucket for a NEW client ===")
mgr = UnsafeManager(capacity=5, refill_rate=1)
created_buckets = []
created_lock = threading.Lock()

def create_attempt():
    bucket = mgr.get_or_create_bucket_unsafe("brand-new-client", now=0.0)
    with created_lock:
        created_buckets.append(id(bucket))  # track identity of the object we got back

threads = [threading.Thread(target=create_attempt) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

unique_buckets = set(created_buckets)
print(f"Threads: 10, unique bucket objects created: {len(unique_buckets)}")
if len(unique_buckets) > 1:
    print("BUG CONFIRMED: more than one bucket was created for the same client!\n")

# ---------- BUG B: over-consumption on the SAME bucket ----------
print("=== Bug B: no per-bucket lock, racing to consume from the SAME bucket ===")
shared_bucket = UnsafeBucket(capacity=10, refill_rate=0.0001, now=0.0)
results = []
results_lock = threading.Lock()

def consume_attempt():
    allowed = shared_bucket.consume_unsafe(now=0.0)
    with results_lock:
        results.append(allowed)

threads = [threading.Thread(target=consume_attempt) for _ in range(50)]
for t in threads:
    t.start()
for t in threads:
    t.join()

allowed_count = sum(results)
print(f"Bucket capacity: 10, requests attempted: 50, requests ALLOWED: {allowed_count}")
if allowed_count > 10:
    print("BUG CONFIRMED: more requests were allowed than the bucket's capacity!")
