"""Typed inputs and trace records for the isolated dynamic-fatigue prototype."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
import numpy as np


def _readonly(values):
    result = np.array(values, dtype=float, copy=True)
    result.setflags(write=False)
    return result


def _resources(values):
    return tuple(tuple(_readonly(stage) for stage in factory) for factory in values)


@dataclass(frozen=True)
class Instance:
    processing: np.ndarray
    setup: np.ndarray
    speeds: Sequence
    powers: Sequence
    standby: Sequence
    efficiencies: Sequence
    wages: Sequence
    source: str
    setup_source: str
    standby_source: str

    def __post_init__(self):
        for name in ("processing", "setup"):
            object.__setattr__(self, name, _readonly(getattr(self, name)))
        for name in ("speeds", "powers", "standby", "efficiencies", "wages"):
            object.__setattr__(self, name, _resources(getattr(self, name)))
        if self.processing.ndim != 2 or self.setup.shape != self.processing.shape:
            raise ValueError("processing/setup must have matching [job, stage] shape")
        if not self.source or not self.setup_source or not self.standby_source:
            raise ValueError("explicit data, setup and standby provenance is required")
        if self.jobs < 1 or self.stages < 1 or self.factories < 1:
            raise ValueError("nonempty instance required")
        for name in ("processing", "setup"):
            x = getattr(self, name)
            if not np.all(np.isfinite(x)) or np.any(x < 0):
                raise ValueError(f"invalid {name}")
        for name in ("speeds", "powers", "standby", "efficiencies", "wages"):
            data = getattr(self, name)
            if len(data) != self.factories or any(len(f) != self.stages for f in data):
                raise ValueError(f"invalid {name} resource dimensions")
            for f in range(self.factories):
                for k in range(self.stages):
                    x = data[f][k]
                    expected = self.speeds[f][k] if name in ("speeds", "powers", "standby") else self.efficiencies[f][k]
                    if len(x) != len(expected) or len(x) == 0 or not np.all(np.isfinite(x)):
                        raise ValueError(f"invalid {name} resources")
                    invalid_values = np.any(x <= 0) if name in ("speeds", "efficiencies") else np.any(x < 0)
                    if invalid_values:
                        raise ValueError(f"invalid {name} values")

    @property
    def jobs(self): return self.processing.shape[0]

    @property
    def stages(self): return self.processing.shape[1]

    @property
    def factories(self): return len(self.speeds)

    @property
    def operations(self): return self.jobs * self.stages

    @property
    def worker_count(self): return sum(len(k) for f in self.efficiencies for k in f)

    @property
    def machine_count(self): return sum(len(k) for f in self.speeds for k in f)

    @property
    def n_jobs(self): return self.jobs
    @property
    def n_stages(self): return self.stages
    @property
    def n_factories(self): return self.factories

    def _uid(self, field, f, k, local):
        return sum(len(s) for factory in field[:f] for s in factory) + sum(len(s) for s in field[f][:k]) + local

    def worker_uid(self, f, k, w): return self._uid(self.efficiencies, f, k, w)

    def machine_uid(self, f, k, m): return self._uid(self.speeds, f, k, m)


@dataclass(frozen=True)
class FatigueParams:
    alpha: object
    mu: object
    beta: object
    h0: object = 0.0

    def arrays(self, instance):
        values = []
        for name in ("alpha", "mu", "beta", "h0"):
            x = np.asarray(getattr(self, name), dtype=float)
            if x.ndim == 0:
                x = np.full(instance.worker_count, float(x))
            if x.shape != (instance.worker_count,) or not np.all(np.isfinite(x)) or np.any(x < 0):
                raise ValueError(f"{name} must be nonnegative scalar or global-worker vector")
            if name == "h0" and np.any(x > 1):
                raise ValueError("h0 must be within [0,1]")
            values.append(x)
        return tuple(values)


@dataclass(frozen=True)
class Genome:
    js: tuple
    fa: tuple
    ma: tuple
    wa: tuple

    def __post_init__(self):
        for name in ("js", "fa", "ma", "wa"):
            raw = tuple(getattr(self, name))
            if any(int(v) != v for v in raw):
                raise ValueError("genome entries must be integers")
            object.__setattr__(self, name, tuple(map(int, raw)))

    def by_job(self):
        """Return job -> (factory, first-stage machine, first-stage worker)."""
        return dict(zip(self.js, zip(self.fa, self.ma, self.wa)))

    @classmethod
    def from_job_attributes(cls, js, attributes):
        rows = [attributes[j] for j in js]
        return cls(tuple(js), tuple(r[0] for r in rows), tuple(r[1] for r in rows), tuple(r[2] for r in rows))


@dataclass(frozen=True)
class LocalTransition:
    completion: float
    v: float
    energy: float
    labor: float
    base: float
    duration: float
    u: float
    start: float

    @property
    def C(self): return self.completion
    @property
    def b(self): return self.base
    @property
    def d(self): return self.duration
    @property
    def S(self): return self.start


@dataclass(frozen=True)
class OperationTrace(LocalTransition):
    op_id: int
    job: int
    factory: int
    stage: int
    machine_id: int
    worker_id: int
    machine_uid: int
    worker_uid: int
    parents: tuple
    active_branch: int
    tie_roles: tuple
    negative_start_slope: bool


@dataclass(frozen=True)
class DecodeResult:
    objectives: np.ndarray
    operations: tuple
    execution_order: tuple
    final_ops: tuple
    provenance: tuple
    # Cached outputs remain available even in the minimal forward path.
    completion: np.ndarray
    fatigue: np.ndarray

    @property
    def C(self): return self.completion
    @property
    def v(self): return self.fatigue

    @property
    def makespan_ties(self):
        return tuple(i for i in self.final_ops if self.C[i] == self.objectives[0])


@dataclass(frozen=True)
class AdjointResult:
    costates: np.ndarray
    grad_base: np.ndarray
    value: float
    weights: np.ndarray

    @property
    def lambdas(self): return self.costates
