"""Exclusive artifact writes and append-only JSON streams."""
from dataclasses import is_dataclass, asdict
from pathlib import Path
import json
import numpy as np


def encode(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    if isinstance(value, Path): return str(value)
    if is_dataclass(value): return asdict(value)
    raise TypeError(type(value).__name__)


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, default=encode, allow_nan=False)


class Records:
    def __init__(self, output):
        self.streams = {name: (output/(name+".jsonl")).open("x", encoding="utf-8")
                        for name in ("census", "paired", "witnesses", "controls", "validation", "events")}

    def emit(self, name, value):
        self.streams[name].write(json.dumps(value, ensure_ascii=False, default=encode, allow_nan=False)+"\n")

    def flush(self):
        for stream in self.streams.values(): stream.flush()

    def close(self):
        for stream in self.streams.values(): stream.close()


def read(path):
    with path.open(encoding="utf-8") as stream:
        for line in stream: yield json.loads(line)
