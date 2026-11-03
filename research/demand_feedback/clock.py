"""Original1800-second clock shared by dispatch and bounded offline analysis."""
import time
from research.semantic_repair.evidence import read


class Deadline:
    def __init__(self, root):
        clock = read(root / "clock.json")
        self.limit = clock["wallCapSeconds"]
        if self.limit != 1800:
            raise ValueError("Original30-minute demand campaign cap changed")
        self.offset = max(0., time.time() - clock["startedEpoch"])
        self.start = time.monotonic()

    def elapsed(self):
        return self.offset + time.monotonic() - self.start

    def remaining(self):
        return max(0., self.limit - self.elapsed())

    def require(self, margin=0):
        if self.remaining() <= margin:
            raise TimeoutError("Original30-minute clock exhausted; evidence retained")
