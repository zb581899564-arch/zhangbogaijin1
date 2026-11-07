"""Exact shared physics with numeric stage0 outputs only, not per-op logs."""
from dataclasses import dataclass
import numpy as np
from research.fatigue_mechanism.decoder import _transition, _validate_genome


@dataclass(frozen=True)
class BoundaryState:
    C: np.ndarray
    v: np.ndarray
    direct: np.ndarray


def exact_stage0(instance, genome, arrays):
    _validate_genome(instance, genome)
    C, H = np.zeros(instance.jobs), np.zeros(instance.jobs)
    energy = labor = 0.
    attrs = genome.by_job()
    for f in range(instance.factories):
        last_m, last_w = {}, {}
        for j in genome.js:
            factory, m, w = attrs[j]
            if factory != f:
                continue
            parents = (-1, last_m.get(m, -1), last_w.get(w, -1))
            values, _ = _transition(instance, arrays, j, f, m, w, parents, C, H)
            C[j], H[j] = values[:2]
            energy += values[2]
            labor += values[3]
            last_m[m] = last_w[w] = j
    return BoundaryState(C, H, np.array([0., energy, labor]))
