"""A common, bounded legal pool; generation never consults objective values."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import numpy as np
from .model import Genome


@dataclass(frozen=True)
class Candidate:
    kind: str
    jobs: tuple[int, int]
    genome: Genome


def _edit(parent, a, b, kind):
    attrs = parent.by_job()
    order = list(parent.js)
    if kind in ("worker_swap", "resource_swap", "joint_swap"):
        fa, ma, wa = attrs[a]
        fb, mb, wb = attrs[b]
        if kind == "worker_swap":
            attrs[a], attrs[b] = (fa, ma, wb), (fb, mb, wa)
        else:
            attrs[a], attrs[b] = (fa, mb, wb), (fb, ma, wa)
    if kind in ("order_swap", "joint_swap"):
        i, j = order.index(a), order.index(b)
        order[i], order[j] = order[j], order[i]
    elif kind == "order_insert":
        order.remove(b)
        order.insert(order.index(a), b)
    return Genome.from_job_attributes(order, attrs)


def candidate_pool(instance, parent, seed, count=16):
    rng = np.random.default_rng(seed)
    attrs = parent.by_job()
    pairs = [pair for pair in combinations(sorted(attrs), 2) if attrs[pair[0]][0] == attrs[pair[1]][0]]
    rng.shuffle(pairs)
    kinds = ("worker_swap", "resource_swap", "order_swap", "order_insert", "joint_swap")
    proposed = []
    seen = {parent}
    for a, b in pairs[:max(12, count)]:
        for kind in kinds:
            child = _edit(parent, a, b, kind)
            if child in seen:
                continue
            for job, (f, m, w) in child.by_job().items():
                if f != attrs[job][0] or not (0 <= m < len(instance.speeds[f][0])
                                            and 0 <= w < len(instance.efficiencies[f][0])):
                    raise AssertionError("candidate is not a legal same-factory first-stage edit")
            if kind in ("order_swap", "order_insert") and child.by_job() != attrs:
                raise AssertionError("a sequence-only edit changed job-owned resources")
            seen.add(child)
            proposed.append(Candidate(kind, (a, b), child))
    rng.shuffle(proposed)
    if len(proposed) < count:
        raise ValueError("too few distinct legal candidates; do not silently alter the frozen pool size")
    return tuple(proposed[:count])
