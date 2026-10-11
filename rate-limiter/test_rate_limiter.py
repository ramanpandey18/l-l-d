import threading
import time

import pytest
from rate_limiter import ClientConfig, TokenBucket, TokenBucketManager


# ---------- ClientConfig validation ----------

def test_config_zero_capacity_raises():
    with pytest.raises(ValueError):
        ClientConfig(capacity=0, refill_rate=1)


def test_config_negative_capacity_raises():
    with pytest.raises(ValueError):
        ClientConfig(capacity=-5, refill_rate=1)


def test_config_zero_refill_rate_raises():
    with pytest.raises(ValueError):
        ClientConfig(capacity=5, refill_rate=0)


def test_config_negative_refill_rate_raises():
    with pytest.raises(ValueError):
        ClientConfig(capacity=5, refill_rate=-1)


# ---------- TokenBucket.consume ----------

def test_bucket_starts_full_and_allows_burst_up_to_capacity():
    config = ClientConfig(capacity=3, refill_rate=1)
    bucket = TokenBucket(config, now=0.0)

    for _ in range(3):
        allowed, retry_after = bucket.consume(1.0, now=0.0)
        assert allowed is True
        assert retry_after == 0.0


def test_bucket_denies_when_empty():
    config = ClientConfig(capacity=1, refill_rate=1)
    bucket = TokenBucket(config, now=0.0)

    bucket.consume(1.0, now=0.0)  # drains the single token
    allowed, retry_after = bucket.consume(1.0, now=0.0)

    assert allowed is False
    assert retry_after == 1.0  # needs 1 full token, refill rate 1/sec


def test_bucket_refills_over_time():
    config = ClientConfig(capacity=5, refill_rate=1)
    bucket = TokenBucket(config, now=0.0)

    for _ in range(5):
        bucket.consume(1.0, now=0.0)  # drain fully

    allowed, _ = bucket.consume(1.0, now=2.5)  # 2.5 sec later -> 2.5 tokens refilled
    assert allowed is True


def test_bucket_never_exceeds_capacity_even_after_long_idle():
    config = ClientConfig(capacity=3, refill_rate=1)
    bucket = TokenBucket(config, now=0.0)

    bucket.consume(1.0, now=0.0)  # tokens: 2
    # simulate a huge time gap - should cap at capacity, not overflow
    allowed, _ = bucket.consume(3.0, now=1000.0)

    assert allowed is True
    assert bucket.tokens == 0.0  # capacity (3) minus the 3 just consumed


def test_consume_zero_or_negative_tokens_raises():
    config = ClientConfig(capacity=3, refill_rate=1)
    bucket = TokenBucket(config, now=0.0)

    with pytest.raises(ValueError):
        bucket.consume(0, now=0.0)

    with pytest.raises(ValueError):
        bucket.consume(-1, now=0.0)


# ---------- TokenBucketManager ----------

def test_unregistered_client_uses_default_config():
    default = ClientConfig(capacity=2, refill_rate=1)
    manager = TokenBucketManager(default_config=default)

    allowed1, _ = manager.allow_request("unknown-client")
    allowed2, _ = manager.allow_request("unknown-client")
    allowed3, _ = manager.allow_request("unknown-client")

    assert allowed1 is True
    assert allowed2 is True
    assert allowed3 is False  # capacity was 2, third request denied


def test_registered_client_uses_their_own_config():
    default = ClientConfig(capacity=1, refill_rate=1)
    manager = TokenBucketManager(default_config=default)
    manager.register_client("premium-client", ClientConfig(capacity=5, refill_rate=1))

    results = [manager.allow_request("premium-client")[0] for _ in range(5)]

    assert all(results)  # all 5 allowed, since their capacity is 5, not the default 1


def test_different_clients_have_independent_buckets():
    manager = TokenBucketManager(default_config=ClientConfig(capacity=1, refill_rate=1))

    alice_allowed, _ = manager.allow_request("alice")
    manager.allow_request("alice")  # drains alice's single token (denied, doesn't matter here)
    bob_allowed, _ = manager.allow_request("bob")  # bob has his own full bucket

    assert alice_allowed is True
    assert bob_allowed is True


def test_get_or_create_bucket_returns_same_instance_on_repeated_calls():
    manager = TokenBucketManager(default_config=ClientConfig(capacity=5, refill_rate=1))

    bucket1 = manager._get_or_create_bucket("alice", now=0.0)
    bucket2 = manager._get_or_create_bucket("alice", now=1.0)

    assert bucket1 is bucket2  # same bucket object, not recreated


# ---------- Concurrency ----------

def test_concurrent_requests_same_new_client_only_one_bucket_created():
    """Many threads hit a brand-new client_id at the same instant. Exactly
    ONE bucket should ever be created for that client, not one per thread."""
    manager = TokenBucketManager(default_config=ClientConfig(capacity=100, refill_rate=1))

    def attempt():
        manager.allow_request("brand-new-client")

    threads = [threading.Thread(target=attempt) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(manager.buckets) == 1


def test_concurrent_requests_never_exceed_capacity():
    """Many threads race to consume tokens from a small-capacity bucket.
    The number of ALLOWED requests must never exceed the bucket's capacity,
    even under concurrent access."""
    manager = TokenBucketManager(default_config=ClientConfig(capacity=10, refill_rate=0.0001))

    results = []
    results_lock = threading.Lock()

    def attempt():
        allowed, _ = manager.allow_request("shared-client")
        with results_lock:
            results.append(allowed)

    threads = [threading.Thread(target=attempt) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    allowed_count = sum(1 for r in results if r)
    assert allowed_count == 10  # exactly capacity, never more


def test_concurrent_requests_consistent_across_many_runs():
    for _ in range(15):
        manager = TokenBucketManager(default_config=ClientConfig(capacity=5, refill_rate=0.0001))
        results = []
        results_lock = threading.Lock()

        def attempt(target_manager=manager):
            allowed, _ = target_manager.allow_request("shared-client")
            with results_lock:
                results.append(allowed)

        threads = [threading.Thread(target=attempt) for _ in range(25)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        allowed_count = sum(1 for r in results if r)
        assert allowed_count == 5
