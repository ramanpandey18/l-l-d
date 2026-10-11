"""
Same two scenarios, but now against the REAL TokenBucketManager/TokenBucket
(with global_lock and per-bucket lock) - run repeatedly to rule out luck.
"""
import threading
from rate_limiter import ClientConfig, TokenBucketManager

bug_a_results = []
bug_b_results = []

for run in range(15):
    # --- Bug A check: one bucket per new client, even under a race ---
    manager = TokenBucketManager(default_config=ClientConfig(capacity=5, refill_rate=1))
    created_bucket_ids = []
    lock = threading.Lock()

    def create_attempt(target_manager=manager):
        bucket = target_manager._get_or_create_bucket("brand-new-client", now=0.0)
        with lock:
            created_bucket_ids.append(id(bucket))

    threads = [threading.Thread(target=create_attempt) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    bug_a_results.append(len(set(created_bucket_ids)) == 1)

    # --- Bug B check: never exceed capacity under a race ---
    manager2 = TokenBucketManager(default_config=ClientConfig(capacity=10, refill_rate=0.0001))
    results = []
    results_lock = threading.Lock()

    def consume_attempt(target_manager=manager2):
        allowed, _ = target_manager.allow_request("shared-client")
        with results_lock:
            results.append(allowed)

    threads = [threading.Thread(target=consume_attempt) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    bug_b_results.append(sum(results) == 10)

print(f"Bug A (one bucket per client) correct: {sum(bug_a_results)} / {len(bug_a_results)}")
print(f"Bug B (never exceed capacity) correct: {sum(bug_b_results)} / {len(bug_b_results)}")
print(f"All runs fully correct: {all(bug_a_results) and all(bug_b_results)}")
