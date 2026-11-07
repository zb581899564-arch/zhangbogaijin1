"""Explicitly reconstructed data and fixed experimental parents."""
from __future__ import annotations

from pathlib import Path
import re
import numpy as np
from .model import Instance, FatigueParams, Genome


def load_instance(path: Path, setup_seed: int) -> Instance:
    factories, stages, jobs = map(int, path.read_text(encoding="utf-8").splitlines()[0].split())
    rows = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()[1:]
            if re.fullmatch(r"[-+0-9.eE,\s]+", line.strip())]
    cursor = 0

    def take(count):
        nonlocal cursor
        result = np.array([float(x) for x in rows[cursor].split(",")])
        cursor += 1
        if len(result) != count:
            raise ValueError(f"wrong data row {cursor}: {path}")
        return result

    machines = [take(stages).astype(int) for _ in range(factories)]
    speeds = [[take(int(machines[f][k])) for k in range(stages)] for f in range(factories)]
    powers = [[take(int(machines[f][k])) for k in range(stages)] for f in range(factories)]
    processing = np.array([take(stages) for _ in range(jobs)])
    totals = take(factories).astype(int)
    levels = [take(int(t)) for t in totals]
    costs = [take(int(t)) for t in totals]
    if cursor != len(rows):
        raise ValueError(f"unconsumed numeric data: {path}")
    efficiencies, wages, standby = [], [], []
    for f in range(factories):
        counts = [int(m - 1 if m > 2 else m) for m in machines[f]]
        if sum(counts) != totals[f] or not any(w < m for w, m in zip(counts, machines[f])):
            raise ValueError(f"stage worker partition / ESWA Eq8 violation: {path}")
        bounds = np.cumsum([0, *counts])
        efficiencies.append([levels[f][bounds[k]:bounds[k + 1]] for k in range(stages)])
        wages.append([costs[f][bounds[k]:bounds[k + 1]] for k in range(stages)])
        standby.append([np.ones(int(m)) for m in machines[f]])
    setup = np.random.default_rng(setup_seed).integers(1, 10, (jobs, stages))
    return Instance(processing, setup, speeds, powers, standby, efficiencies, wages,
                    source=str(path.resolve()),
                    setup_source=f"RECONSTRUCTED NOT AUTHOR DATA; numpy PCG64 discrete U[1,9]; seed={setup_seed}",
                    standby_source="EXPLICIT RECONSTRUCTION: standby power=1, absent from supplied benchmark")


def parent_genome(instance: Instance, seed: int) -> Genome:
    rng = np.random.default_rng(seed)
    js = tuple(map(int, rng.permutation(instance.jobs)))
    factories = np.concatenate([np.arange(instance.factories),
                               rng.integers(instance.factories, size=instance.jobs - instance.factories)])
    rng.shuffle(factories)
    attrs = {job: (int(factories[job]),
                   int(rng.integers(len(instance.speeds[factories[job]][0]))),
                   int(rng.integers(len(instance.efficiencies[factories[job]][0]))))
             for job in range(instance.jobs)}
    return Genome.from_job_attributes(js, attrs)


def fatigue_profile(instance: Instance, profile: dict, seed: int) -> tuple[FatigueParams, dict]:
    speed = np.median(np.concatenate([x for f in instance.speeds for x in f]))
    efficiency = np.median(np.concatenate([x for f in instance.efficiencies for x in f]))
    time_scale = float(np.median((instance.processing / speed + instance.setup) / efficiency))
    rng = np.random.default_rng(seed)
    heterogeneity = rng.uniform(0.85, 1.15, (3, instance.worker_count))
    params = FatigueParams(profile["alpha_per_base"] / time_scale * heterogeneity[0],
                           profile["mu_per_base"] / time_scale * heterogeneity[1],
                           profile["beta"] * heterogeneity[2], 0.0)
    return params, {"time_scale":time_scale,"heterogeneity_seed":seed,
                    "alpha":np.asarray(params.alpha).tolist(),"mu":np.asarray(params.mu).tolist(),
                    "beta":np.asarray(params.beta).tolist(),"h0":0.0,
                    "source":"synthetic sensitivity scenarios, not physiological measurements"}
