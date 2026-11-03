"""Ordinary physical moves, independent of objectives and fatigue."""
from dataclasses import dataclass
from itertools import combinations
import numpy as np
from research.fatigue_coordination.space import State, moves


@dataclass(frozen=True)
class Candidate:
    state: State

    @property
    def genome(self):
        return self.state.genome()


def resource(state, job):
    return (state.resources >> (2*job)) & 3


def bind(state, first, second, a, b):
    kept = state.resources & ~(3 << (2*first)) & ~(3 << (2*second))
    return State(state.queues, kept | (a << (2*first)) | (b << (2*second)))


def job_pairs(state, cross=False):
    jobs = sum(state.queues, ())
    factory = {j: f for f, queue in enumerate(state.queues) for j in queue}
    return tuple((a, b) for a, b in combinations(sorted(jobs), 2) if not cross or factory[a] != factory[b])


def exchange(state, first, second):
    queues = tuple(tuple(second if j == first else first if j == second else j for j in q) for q in state.queues)
    return State(queues, state.resources)


def draw(state, kind, rng):
    if kind == "plain":
        first, second = map(int, rng.choice(len(sum(state.queues, ())), 2, replace=False))
        choices = moves(state, first)
        middle = choices[int(rng.integers(len(choices)))]
        choices = moves(middle, second)
        return Candidate(choices[int(rng.integers(len(choices)))])
    pairs = job_pairs(state, cross=kind != "rebind")
    first, second = pairs[int(rng.integers(len(pairs)))]
    if kind == "rebind":
        old = 4*resource(state, first)+resource(state, second)
        code = int(rng.integers(15))
        code += code >= old
        return Candidate(bind(state, first, second, code//4, code % 4))
    child = exchange(state, first, second)
    if kind == "swap_rebind":
        child = bind(child, first, second, int(rng.integers(4)), int(rng.integers(4)))
    elif kind != "swap":
        raise ValueError(kind)
    return Candidate(child)


def pool(state, kind, seed, size):
    rng = np.random.default_rng(seed)
    return tuple(draw(state, kind, rng) for _ in range(size))


def labelled_children(state, kind):
    """Enumerate uniform labelled outcomes for ordinary resource/swap draws."""
    result = []
    for first, second in job_pairs(state, cross=kind != "rebind"):
        base = state if kind == "rebind" else exchange(state, first, second)
        if kind == "swap":
            result.append(base)
            continue
        for a in range(4):
            for b in range(4):
                child = bind(base, first, second, a, b)
                if kind != "rebind" or child != state:
                    result.append(child)
    return tuple(result)
