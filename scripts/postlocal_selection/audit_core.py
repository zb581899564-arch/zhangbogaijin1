"""Independent numeric evidence primitives; never evaluates a schedule."""
from collections import Counter
import hashlib
import json
import math
import struct

import numpy as np


ROLES = ("MAKESPAN", "CENTER", "ENERGY", "WORKER_COST")
ROLE_COUNTS = Counter(dict(zip(ROLES, (15, 55, 15, 15))))
FAMILY_COUNTS = Counter({-1: 80, 0: 5, 1: 5, 2: 5, 3: 5})
OBJECTIVE_ROLE = {"MAKESPAN": 0, "ENERGY": 1, "WORKER_COST": 2}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read_json(path):
    with path.open(encoding="utf-8-sig") as stream:
        return json.load(stream)


def json_lines(path):
    with path.open(encoding="utf-8-sig") as stream:
        for number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except Exception as error:
                    raise ValueError(f"Invalid JSON at {path}:{number}") from error


def raw_bytes(raw, fee=0):
    result = struct.pack(">q", fee)
    for name in ("JS", "FA", "MA", "WA"):
        values = raw[name]
        result += struct.pack(">i", len(values))
        result += struct.pack(">" + "i" * len(values), *values)
    return result + struct.pack(">ddd", *raw["objectives"])


def raw_hash(raw):
    return hashlib.sha256(raw_bytes(raw)).hexdigest()


def state_raw(point, catalog):
    resources, keys = point["resources"], point["keys"]
    order = sorted(range(len(resources)), key=lambda job: (keys[job], -job))
    result = {"JS": order, "objectives": point["objectives"]}
    for axis, name in enumerate(("FA", "MA", "WA")):
        result[name] = [catalog[resources[job]][axis] for job in order]
    return result


def physical(raw, factories):
    return tuple(tuple((j, m, w) for j, f, m, w in
                       zip(raw["JS"], raw["FA"], raw["MA"], raw["WA"]) if f == factory)
                 for factory in range(factories))


def factory_by_job(raw):
    result = [None] * len(raw["JS"])
    require(sorted(raw["JS"]) == list(range(len(result))), "JS is not a permutation")
    for job, factory in zip(raw["JS"], raw["FA"]):
        result[job] = factory
    return result


def check_raw(raw, jobs, factories):
    require(all(len(raw[name]) == jobs for name in ("JS", "FA", "MA", "WA")),
            "Wrong raw genome length")
    require(set(factory_by_job(raw)) == set(range(factories)), "Missing or unknown factory")
    require(len(raw["objectives"]) == 3 and all(map(math.isfinite, raw["objectives"])),
            "Invalid objective vector")


def check_population(rows):
    require(len(rows) == 100, "Population must have exactly 100 members")
    require(Counter(p["role"] for p in rows) == ROLE_COUNTS, "Role quotas changed")
    require(Counter(p["family"] for p in rows) == FAMILY_COUNTS, "Family quotas changed")
    fixed = {}
    for row in rows:
        if row["family"] >= 0:
            factory = factory_by_job(row["raw"])
            require(fixed.setdefault(row["family"], factory) == factory,
                    "Fixed-family allocation changed")


def same_front(actual, expected, label):
    left = np.asarray(actual, dtype=float).reshape((-1, 3))
    right = np.asarray(expected, dtype=float).reshape((-1, 3))
    require(np.isfinite(left).all() and np.isfinite(right).all(), label + " is nonfinite")
    require(sorted(map(tuple, left)) == sorted(map(tuple, right)), label + " differs")


class ParetoLedger:
    """Exact pre-insertion flags, preserving the original insertion order."""
    def __init__(self, initial=()):
        self.points = np.empty((0, 3))
        for row in initial:
            self.offer(row)
        same_front(self.points, initial, "Initial archive (must be unique nondominated)")

    def offer(self, raw):
        child = np.asarray(raw, dtype=float)
        require(child.shape == (3,) and np.isfinite(child).all(), "Invalid paid objectives")
        before = len(self.points)
        weak = np.all(self.points <= child, axis=1)
        equal = np.all(self.points == child, axis=1)
        dominated, identical = bool(np.any(weak & ~equal)), bool(np.any(equal))
        fresh = not dominated and not identical
        if fresh:
            remove = np.all(child <= self.points, axis=1) & np.any(child != self.points, axis=1)
            self.points = np.vstack((self.points[~remove], child))
        return dict(dominated=dominated, equal=identical, fresh=fresh,
                    before=before, after=len(self.points))


def check_flags(actual, expected, label):
    for key, value in expected.items():
        require(actual[key] == value and type(actual[key]) is type(value),
                f"{label}.{key}: {actual[key]!r} != {value!r}")


def points_tsv(path):
    result = []
    with path.open(encoding="utf-8-sig") as stream:
        for number, line in enumerate(stream, 1):
            fields = line.rstrip("\r\n").split("\t")
            require(len(fields) == 10, f"Invalid input columns at {path}:{number}")
            origin, index, fee, role, family = fields[:5]
            raw = {"objectives": [float(v) for v in fields[5].split(",")]}
            for name, value in zip(("JS", "FA", "MA", "WA"), fields[6:]):
                raw[name] = [int(v) for v in value.split(",")]
            result.append(dict(origin=origin, sourceIndex=int(index), sourcePaidByFE=int(fee),
                               role=role, family=int(family), raw=raw))
    return result
