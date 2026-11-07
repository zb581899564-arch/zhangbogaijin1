"""Append-only compressed streams with separately timed disk cost."""
import gzip
import json
from time import perf_counter_ns
from research.fatigue_coordination.records import save, encode


class Records:
    def __init__(self, output):
        self.io_ns = 0
        self.streams = {n: gzip.open(output/(n+".jsonl.gz"), "xt", encoding="utf-8", compresslevel=1)
                        for n in ("inputs", "search", "validation", "events")}

    def emit(self, name, row):
        started = perf_counter_ns()
        self.streams[name].write(json.dumps(row, ensure_ascii=False, default=encode, allow_nan=False)+"\n")
        self.io_ns += perf_counter_ns()-started

    def flush(self):
        for stream in self.streams.values():
            stream.flush()

    def close(self):
        for stream in self.streams.values():
            stream.close()


def read(output, name):
    with gzip.open(output/(name+".jsonl.gz"), "rt", encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)
