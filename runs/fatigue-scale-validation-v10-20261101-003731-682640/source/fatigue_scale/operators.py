"""Uniform legal strong-N1 sampling and cross-factory swap/rebinding."""
from itertools import combinations
import numpy as np
from .state import State, insert


def dimensions(instance):
    return tuple((len(instance.speeds[f][0]), len(instance.efficiencies[f][0])) for f in range(instance.factories))


def segments(state, job, dims):
    source = next(f for f, q in enumerate(state.queues) if job in q)
    result = []
    for target, (machines, workers) in enumerate(dims):
        if target != source and len(state.queues[source]) == 1:
            continue
        length = len(state.queues[target])-(target == source)
        total = (length+1)*machines*workers-(target == source)
        if total:
            result.append((target, total, machines, workers))
    return source, result


def indexed_move(state, job, dims, rank):
    source, values = segments(state, job, dims)
    for target, size, machines, workers in values:
        if rank >= size:
            rank -= size
            continue
        if target == source:
            old_m, old_w = state.resources[job]
            excluded = state.queues[source].index(job)*machines*workers+old_w*machines+old_m
            rank += rank >= excluded
        position, resource = divmod(rank, machines*workers)
        worker, machine = divmod(resource, machines)
        move = (job, target, int(position), int(machine), int(worker))
        return insert(state, *move), move
    raise IndexError(rank)


def one_move(state, job, dims, rng):
    _, values = segments(state, job, dims)
    size = sum(row[1] for row in values)
    # Some singleton factories have only one resource tuple; pay the noop.
    return indexed_move(state, job, dims, int(rng.integers(size))) if size else (state, None)


def cross_pair(state, rng):
    groups = [(a, b, len(state.queues[a])*len(state.queues[b])) for a, b in combinations(range(len(state.queues)), 2)]
    rank = int(rng.integers(sum(row[2] for row in groups)))
    for a, b, count in groups:
        if rank >= count:
            rank -= count
            continue
        i, j = divmod(rank, len(state.queues[b]))
        return a, b, state.queues[a][i], state.queues[b][j]
    raise AssertionError("nonempty factories required")


def draw(state, family, dims, seed):
    rng = np.random.default_rng(seed)
    if family == "plain":
        a, b = map(int, rng.choice(len(state.resources), 2, replace=False))
        middle, first = one_move(state, a, dims, rng)
        child, second = one_move(middle, b, dims, rng)
        return child, {"family": family, "jobs": [a, b], "moves": [first, second]}
    if family != "swap_rebind":
        raise ValueError(family)
    source, target, a, b = cross_pair(state, rng)
    resources = list(state.resources)
    resources[a] = tuple(int(rng.integers(size)) for size in dims[target])
    resources[b] = tuple(int(rng.integers(size)) for size in dims[source])
    queues = tuple(tuple(b if j == a else a if j == b else j for j in q) for q in state.queues)
    return State(queues, tuple(resources)), {"family": family, "jobs": [a, b], "resources": [resources[a], resources[b]]}
