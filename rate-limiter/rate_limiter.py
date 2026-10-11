from threading import Lock
import time

class ClientConfig:
    def __init__(self, capacity: float, refill_rate: float):
        if capacity <= 0:
            raise ValueError("capacity must be greater than 0.")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be greater than 0.")
        self.capacity = capacity
        self.refill_rate = refill_rate

class TokenBucket:
    def __init__(self, config: ClientConfig, now: float):
        self.config = config
        self.tokens = config.capacity
        self.last_updated = now
        self.lock = Lock()

    def consume(self, tokens_requested: float, now: float) -> tuple[bool, float]:
        if tokens_requested <= 0:
            raise ValueError("tokens_requested must be greater than 0.")
        with self.lock:
            elapsed = now - self.last_updated
            if elapsed > 0:
                self.tokens = min(
                    self.config.capacity,
                    self.tokens + elapsed * self.config.refill_rate
                )
                self.last_updated = now

            if self.tokens >= tokens_requested:
                self.tokens -= tokens_requested
                return True, 0.0

            deficit = tokens_requested - self.tokens
            retry_after = deficit / self.config.refill_rate
            return False, retry_after

class TokenBucketManager:
    def __init__(self, default_config: ClientConfig):
        self.default_config = default_config
        self.buckets: dict[str, TokenBucket] = {}
        self.client_configs: dict[str, ClientConfig] = {}
        self.global_lock = Lock()

    def register_client(self, client_id: str, config: ClientConfig) -> None:
        with self.global_lock:
            self.client_configs[client_id] = config

    def allow_request(self, client_id: str, tokens_requested: float = 1.0) -> tuple[bool, float]:
        now = time.monotonic()
        bucket = self._get_or_create_bucket(client_id, now)
        return bucket.consume(tokens_requested, now)

    def _get_or_create_bucket(self, client_id: str, now: float) -> TokenBucket:
        # fast path
        if client_id in self.buckets:
            return self.buckets[client_id]

        # slow path
        with self.global_lock:
            if client_id in self.buckets:
                return self.buckets[client_id]

            config = self.client_configs.get(client_id, self.default_config)
            bucket = TokenBucket(config, now)
            self.buckets[client_id] = bucket
            return bucket
