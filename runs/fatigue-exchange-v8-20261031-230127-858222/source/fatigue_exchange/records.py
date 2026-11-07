"""Exclusive metadata plus compressed append-only scientific observations."""
import gzip
import json
from research.fatigue_coordination.records import encode, save


class Records:
    def __init__(self, output):
        self.streams = {n: gzip.open(output/(n+".jsonl.gz"), "xt", encoding="utf-8", compresslevel=1)
                        for n in ("coverage", "search", "snapshots", "validation", "events")}

    def emit(self, name, row):
        self.streams[name].write(json.dumps(row, ensure_ascii=False, default=encode, allow_nan=False)+"\n")

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
