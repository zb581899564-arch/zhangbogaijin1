"""Predeclared tiny heterogeneous inputs, all with stage1 W<M."""
from dataclasses import asdict, replace
import numpy as np
from research.fatigue_mechanism.model import Instance
from research.fatigue_mechanism.instances import fatigue_profile
from .protocol import PROTOCOL


def make_instance(jobs, seed):
    rng = np.random.default_rng(seed+1000003*jobs)
    ranges = PROTOCOL["synthetic_ranges"]
    speeds = tuple(tuple(rng.uniform(*ranges["speed"], m) for m in (2, 3)) for _ in range(2))
    powers = tuple(tuple(rng.uniform(*ranges["power"], m) for m in (2, 3)) for _ in range(2))
    standby = tuple(tuple(np.ones(m) for m in (2, 3)) for _ in range(2))
    workers = tuple(tuple(rng.uniform(*ranges["efficiency"], 2) for _ in range(2)) for _ in range(2))
    wages = tuple(tuple(rng.uniform(*ranges["wage"], 2) for _ in range(2)) for _ in range(2))
    return Instance(rng.uniform(*ranges["processing"], (jobs, 2)), rng.uniform(*ranges["setup"], (jobs, 2)),
                    speeds, powers, standby, workers, wages, f"SYNTHETIC-v7-N{jobs}-seed{seed}",
                    "SYNTHETIC independent setup U[1,3]", "EXPLICIT synthetic standby=1")


def parameters(instance, seed):
    rate_seed = seed+1000003*instance.jobs+271828
    fast, fm = fatigue_profile(instance, PROTOCOL["profiles"]["strong_fast"], rate_seed)
    slow, sm = fatigue_profile(instance, PROTOCOL["profiles"]["strong_slow"], rate_seed)
    return {"beta0": replace(fast, beta=0.), "strong_fast": fast, "strong_slow": slow}, {"strong_fast": fm, "strong_slow": sm}


def instance_record(instance):
    def plain(value):
        if isinstance(value, np.ndarray): return value.tolist()
        if isinstance(value, (list, tuple)): return [plain(v) for v in value]
        return value
    return {k: plain(v) for k, v in asdict(instance).items()}
