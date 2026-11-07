"""Truth-independent legal edits and explicitly non-gene sensitivity probes."""
from dataclasses import dataclass, replace
import numpy as np
from research.fatigue_mechanism.candidates import candidate_pool
from research.fatigue_mechanism.model import Genome


@dataclass(frozen=True)
class Trial:
    pool: str
    kind: str
    genome: Genome
    jobs: tuple
    relative_st: float = 0.


def local_pool(instance, parent, seed, count):
    rng, attrs = np.random.default_rng(seed), parent.by_job()
    proposals = []
    for job in parent.js:
        f, m, w = attrs[job]
        for kind, limit, current in (("one_machine", len(instance.speeds[f][0]), m),
                                      ("one_worker", len(instance.efficiencies[f][0]), w)):
            alternatives = [i for i in range(limit) if i != current]
            if alternatives:
                new = int(rng.choice(alternatives))
                changed = dict(attrs)
                changed[job] = (f, new, w) if kind == "one_machine" else (f, m, new)
                proposals.append(Trial("legal_local", kind, Genome.from_job_attributes(parent.js, changed), (job,)))
    for f in range(instance.factories):
        sequence = [j for j in parent.js if attrs[j][0] == f]
        for a, b in zip(sequence, sequence[1:]):
            js = list(parent.js)
            i, j = js.index(a), js.index(b)
            js[i], js[j] = js[j], js[i]
            proposals.append(Trial("legal_local", "adjacent_order", Genome.from_job_attributes(js, attrs), (a, b)))
    rng.shuffle(proposals)
    seen, result = {parent}, []
    for trial in proposals:
        if trial.genome not in seen:
            seen.add(trial.genome)
            result.append(trial)
        if len(result) == count:
            return tuple(result)
    raise ValueError("too few legal local edits; do not shrink a frozen pool")


def make_pool(instance, parent, seed, name, protocol):
    if name.startswith("probe_"):
        epsilon = float(name.removeprefix("probe_"))
        jobs = np.random.default_rng(seed).choice(instance.jobs, protocol["probe_jobs"], replace=False)
        return tuple(Trial(name, "ST_intervention", parent, (int(j),), sign * epsilon)
                     for j in jobs for sign in (-1, 1))
    if name == "legal_local":
        return local_pool(instance, parent, seed, protocol["legal_pool_count"])
    return tuple(Trial(name, c.kind, c.genome, c.jobs) for c in
                 candidate_pool(instance, parent, seed, protocol["legal_pool_count"]))


def trial_instance(instance, trial):
    if not trial.relative_st:
        return instance
    processing = instance.processing.copy()
    processing[trial.jobs[0], 0] *= 1 + trial.relative_st
    return replace(instance, processing=processing)


def delta_base(instance, trace, trial):
    if not trial.relative_st:
        return 0.
    op = trace.operations[trial.jobs[0]]
    return float(instance.processing[op.job, 0] * trial.relative_st
                 / instance.speeds[op.factory][0][op.machine_id]
                 / instance.efficiencies[op.factory][0][op.worker_id])
