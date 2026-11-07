"""First-stage local defects on cached states; no candidate decode or truth access."""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from .decoder import local_transitions


@dataclass(frozen=True)
class Defects:
    ids: tuple
    state_change: np.ndarray
    direct_change: np.ndarray


def prepare_defects(instance, params, parent_trace, candidates, max_affected=16):
    requests, per_candidate = [], []
    for candidate in candidates:
        last_m, last_w, ids = {}, {}, []
        attrs = candidate.genome.by_job()
        for job in candidate.genome.js:
            f, m, w = attrs[job]
            parents = (-1, last_m.get((f, m), -1), last_w.get((f, w), -1))
            old = parent_trace.operations[job]  # stage-0 op_id equals job identity
            if (f, m, w, parents) != (old.factory, old.machine_id, old.worker_id, old.parents):
                ids.append(job)
                requests.append((job, m, w, parents, f))
            last_m[f, m] = last_w[f, w] = job
        if len(ids) > max_affected:
            raise ValueError("candidate exceeds the frozen direct-defect bound")
        per_candidate.append(tuple(ids))
    transitions = local_transitions(instance, params, requests, parent_trace)
    cursor, output = 0, []
    for ids in per_candidate:
        state, direct = [], []
        for op_id in ids:
            new, old = transitions[cursor], parent_trace.operations[op_id]
            state.append((new.completion - old.completion, new.v - old.v))
            direct.append((0.0, new.energy - old.energy, new.labor - old.labor))
            cursor += 1
        output.append(Defects(ids, np.asarray(state).reshape(-1, 2), np.asarray(direct).reshape(-1, 3)))
    return tuple(output)


def score_defects(defects, adjoints):
    """Adjoints.weights already includes normalization; own direct cost counted once."""
    scores = []
    for defect in defects:
        direct = float(np.sum(defect.direct_change @ adjoints.weights))
        downstream = float(np.sum(adjoints.costates[list(defect.ids)] * defect.state_change))
        scores.append(direct + downstream)
    return np.asarray(scores)
