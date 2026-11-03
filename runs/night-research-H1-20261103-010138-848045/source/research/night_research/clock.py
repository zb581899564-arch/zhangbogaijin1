"""Original campaign clock and absolute 07:00 stop, including bounded workers."""
import time
from research.semantic_repair.evidence import read


class Deadline:
    def __init__(self, root):
        clock = read(root / "clock.json")
        if clock["wallCapSeconds"] != 3600:
            raise ValueError("The original one-hour campaign cap changed")
        self.started_epoch = clock["startedEpoch"]
        self.stop_epoch = min(self.started_epoch + clock["wallCapSeconds"], clock["absoluteStopEpoch"])
        self.loaded_epoch, self.monotonic = time.time(), time.monotonic()

    def now(self):
        # Wall-clock forward adjustments may shorten, never extend the hard stop.
        return max(time.time(), self.loaded_epoch + time.monotonic() - self.monotonic)

    def elapsed(self):
        return max(0., self.now() - self.started_epoch)

    def remaining(self):
        return max(0., self.stop_epoch - self.now())

    def require(self, margin=0):
        if self.remaining() <= margin:
            raise TimeoutError("Original campaign/absolute night deadline exhausted; all evidence retained")
