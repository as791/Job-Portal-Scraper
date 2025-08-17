import time
from threading import Lock

class TokenBucket:
    def __init__(self, rate_per_sec: float, capacity: int | None = None):
        self.rate = max(rate_per_sec, 0.001)
        self.capacity = capacity or 1
        self.tokens = self.capacity
        self.timestamp = time.monotonic()
        self.lock = Lock()

    def consume(self, tokens: int = 1):
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.timestamp
            self.timestamp = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            if self.tokens < tokens:
                needed = tokens - self.tokens
                sleep_time = needed / self.rate
                time.sleep(sleep_time)
                self.tokens = 0
                self.timestamp = time.monotonic()
            else:
                self.tokens -= tokens
