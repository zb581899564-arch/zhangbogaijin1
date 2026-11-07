"""Exclusive metadata and compressed observations, no old evidence rewrites."""
import gzip
import json
from research.fatigue_coordination.records import encode, save
from research.fatigue_exchange.records import read


class Records:
    def __init__(self, output):
        self.streams = {n: gzip.open(output/(n+".jsonl.gz"), "xt", encoding="utf-8", compresslevel=1)
                        for n in ("coverage", "search", "validation", "events")}

    def emit(self, name, row):
        self.streams[name].write(json.dumps(row, ensure_ascii=False, default=encode, allow_nan=False)+"\n")

    def flush(self):
        for stream in self.streams.values():
            stream.flush()

    def close(self):
        for stream in self.streams.values():
            stream.close()
