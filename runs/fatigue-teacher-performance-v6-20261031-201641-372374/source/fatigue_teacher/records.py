"""Append-only streams and explicit serialization/flush accounting."""
from time import perf_counter_ns
import json
from research.fatigue_reuse.experiment import save


class Records:
    def __init__(self, output):
        names = ("inputs", "chains", "steps", "epochs", "mechanism", "events", "validation")
        self.streams = {n: (output/(n+".jsonl")).open("x", encoding="utf-8") for n in names}
        self.io_ns = 0

    def emit(self, name, value):
        start = perf_counter_ns()
        self.streams[name].write(json.dumps(value, ensure_ascii=False, allow_nan=False)+"\n")
        self.io_ns += perf_counter_ns()-start

    def flush(self):
        start = perf_counter_ns()
        for stream in self.streams.values():
            stream.flush()
        self.io_ns += perf_counter_ns()-start

    def close(self):
        for stream in self.streams.values():
            stream.close()


def read(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)
