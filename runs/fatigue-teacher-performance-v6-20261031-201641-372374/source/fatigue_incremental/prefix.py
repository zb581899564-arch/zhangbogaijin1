"""Reuse only an identical factory prefix; recompute its entire new suffix."""
from dataclasses import dataclass
import numpy as np
from research.fatigue_mechanism.decoder import _transition, _validate_genome
from research.fatigue_reuse.stage0 import BoundaryState


def readonly(values):
    result = np.array(values, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class FactoryPrefix:
    tokens: tuple
    machine_checkpoints: tuple
    worker_checkpoints: tuple


@dataclass(frozen=True)
class PrefixCache:
    factories: tuple
    factory_by_job: tuple
    C: np.ndarray
    v: np.ndarray
    energy: np.ndarray
    labor: np.ndarray
    direct: np.ndarray


def tokens_by_factory(instance, genome, expected_factory=None):
    _validate_genome(instance, genome)
    result = [[] for _ in range(instance.factories)]
    for j, f, m, w in zip(genome.js, genome.fa, genome.ma, genome.wa):
        if expected_factory is not None and f != expected_factory[j]:
            raise ValueError("prefix reuse requires fixed per-job factory assignment")
        result[f].append((j, m, w))
    return tuple(tuple(tokens) for tokens in result)


def ordered_direct(tokens, energy, labor):
    # Same addition order as full exact_stage0, including floating-point rounding.
    e = w = 0.
    for factory in tokens:
        for j, _, _ in factory:
            e += energy[j]
            w += labor[j]
    return np.array([0., e, w])


def build_prefix(instance, genome, parent):
    sequences = tokens_by_factory(instance, genome)
    factories, by_job = [], [None] * instance.jobs
    energy, labor = np.zeros(instance.jobs), np.zeros(instance.jobs)
    for f, tokens in enumerate(sequences):
        last_m = [-1] * len(instance.speeds[f][0])
        last_w = [-1] * len(instance.efficiencies[f][0])
        machine_checkpoints, worker_checkpoints = [tuple(last_m)], [tuple(last_w)]
        for j, m, w in tokens:
            old = parent.operations[j]
            assert (old.factory, old.stage, old.machine_id, old.worker_id) == (f, 0, m, w)
            assert old.parents == (-1, last_m[m], last_w[w])
            energy[j], labor[j], by_job[j] = old.energy, old.labor, f
            last_m[m] = last_w[w] = j
            machine_checkpoints.append(tuple(last_m))
            worker_checkpoints.append(tuple(last_w))
        factories.append(FactoryPrefix(tokens, tuple(machine_checkpoints), tuple(worker_checkpoints)))
    return PrefixCache(tuple(factories), tuple(by_job), readonly(parent.C[:instance.jobs]),
                       readonly(parent.v[:instance.jobs]), readonly(energy), readonly(labor),
                       readonly(ordered_direct(sequences, energy, labor)))


def incremental_stage0(instance, genome, arrays, cache):
    sequences = tokens_by_factory(instance, genome, cache.factory_by_job)
    changed = [(f, tokens) for f, tokens in enumerate(sequences) if tokens != cache.factories[f].tokens]
    work = {"recomputed_ops": 0, "reused_prefix_ops": 0,
            "unchanged_factory_ops": sum(len(t) for f, t in enumerate(sequences)
                                         if t == cache.factories[f].tokens),
            "affected_factory_visits": len(changed)}
    if not changed:
        return BoundaryState(cache.C, cache.v, cache.direct), work
    C, H = cache.C.copy(), cache.v.copy()
    energy, labor = cache.energy.copy(), cache.labor.copy()
    for f, tokens in changed:
        old = cache.factories[f]
        first = next(i for i, (new, prior) in enumerate(zip(tokens, old.tokens)) if new != prior)
        last_m = list(old.machine_checkpoints[first])
        last_w = list(old.worker_checkpoints[first])
        work["reused_prefix_ops"] += first
        for j, m, w in tokens[first:]:
            parents = (-1, last_m[m], last_w[w])
            values, _ = _transition(instance, arrays, j, f, m, w, parents, C, H)
            C[j], H[j], energy[j], labor[j] = values[:4]
            last_m[m] = last_w[w] = j
            work["recomputed_ops"] += 1
    return BoundaryState(C, H, ordered_direct(sequences, energy, labor)), work
