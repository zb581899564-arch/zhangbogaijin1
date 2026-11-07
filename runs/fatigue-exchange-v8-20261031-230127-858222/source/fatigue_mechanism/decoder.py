"""Append-only ECT/FIFO decoder and local frozen-predecessor transitions."""
from __future__ import annotations

import math
import numpy as np
from .model import DecodeResult, LocalTransition, OperationTrace


def _validate_genome(instance, genome):
    n = instance.jobs
    if any(len(x) != n for x in (genome.js, genome.fa, genome.ma, genome.wa)) or sorted(genome.js) != list(range(n)):
        raise ValueError("four position-aligned length-N vectors and a job permutation required")
    if set(genome.fa) != set(range(instance.factories)):
        raise ValueError("each factory must receive at least one job")
    for f, m, w in zip(genome.fa, genome.ma, genome.wa):
        if not 0 <= m < len(instance.speeds[f][0]) or not 0 <= w < len(instance.efficiencies[f][0]):
            raise ValueError("invalid first-stage resource assignment")


def _transition(instance, arrays, op_id, factory, machine, worker, parents, C, H, base_override=None):
    job, stage = op_id % instance.jobs, op_id // instance.jobs
    uid = instance.worker_uid(factory, stage, worker)
    a, mu, beta, h0 = (x[uid] for x in arrays)
    times = tuple(C[p] if p >= 0 else 0.0 for p in parents)
    start = max(times)
    before = H[parents[2]] if parents[2] >= 0 else h0
    u = before * math.exp(-mu * (start - times[2]))
    base = ((instance.processing[job, stage] / instance.speeds[factory][stage][machine]
             + instance.setup[job, stage]) / instance.efficiencies[factory][stage][worker])
    if base_override is not None:
        base = float(base_override)
    duration = base * (1.0 + beta * u)
    v = 1.0 - (1.0 - u) * math.exp(-a * duration)
    gap = start - times[1] if parents[1] >= 0 else 0.0
    energy = instance.powers[factory][stage][machine] * duration + instance.standby[factory][stage][machine] * gap
    labor = instance.wages[factory][stage][worker] * duration
    return (start + duration, v, energy, labor, base, duration, u, start), times


def _record(instance, arrays, op_id, factory, machine, worker, parents, values, times):
    stage, job = divmod(op_id, instance.jobs)
    active = times.index(max(times))  # Explicit one-sided tie rule: job, machine, worker.
    ties = tuple(i for i, t in enumerate(times) if t == max(times))
    uid = instance.worker_uid(factory, stage, worker)
    negative = 1.0 - arrays[1][uid] * arrays[2][uid] * values[4] * values[6] < 0
    return OperationTrace(*values, op_id, job, factory, stage, machine, worker,
                          instance.machine_uid(factory, stage, machine), uid,
                          tuple(parents), active, ties, bool(negative))


def decode(instance, genome, fatigue_params, retain_trace=True):
    """A full decode is one forward evaluation; no insertion, right shift or rest."""
    _validate_genome(instance, genome)
    arrays = fatigue_params.arrays(instance)
    C, H = np.zeros(instance.operations), np.zeros(instance.operations)
    traces = [None] * instance.operations if retain_trace else None
    order = [] if retain_trace else None
    energy = labor = 0.0
    attrs = genome.by_job()
    for f in range(instance.factories):
        sequence = [j for j in genome.js if attrs[j][0] == f]
        for k in range(instance.stages):
            if k:
                sequence = sorted(sequence, key=lambda j: C[(k - 1) * instance.jobs + j])
            last_m = [-1] * len(instance.speeds[f][k])
            last_w = [-1] * len(instance.efficiencies[f][k])
            for j in sequence:
                if k == 0:
                    _, machine, worker = attrs[j]
                else:
                    machine = min(range(len(last_m)), key=lambda m: (C[last_m[m]] if last_m[m] >= 0 else 0.0, m))
                    worker = min(range(len(last_w)), key=lambda w: (C[last_w[w]] if last_w[w] >= 0 else 0.0, w))
                op_id = k * instance.jobs + j
                parents = ((k - 1) * instance.jobs + j if k else -1, last_m[machine], last_w[worker])
                values, times = _transition(instance, arrays, op_id, f, machine, worker, parents, C, H)
                C[op_id], H[op_id] = values[:2]
                energy += values[2]
                labor += values[3]
                last_m[machine] = last_w[worker] = op_id
                if retain_trace:
                    traces[op_id] = _record(instance, arrays, op_id, f, machine, worker, parents, values, times)
                    order.append(op_id)
    final_ops = tuple((instance.stages - 1) * instance.jobs + j for j in range(instance.jobs))
    objectives = np.array([max(C[list(final_ops)]), energy, labor])
    return DecodeResult(objectives, tuple(traces) if retain_trace else (), tuple(order) if retain_trace else (),
                        final_ops, (instance.source, instance.setup_source, instance.standby_source), C, H)


def local_transition(instance, params, op_id, machine_id, worker_id, parents, cached_trace, *, factory_id=None):
    """Rebind stage-0 resources against OLD predecessor outputs, without decoding.

    Factory defaults to the cached binding; first-stage FA moves must supply
    factory_id explicitly. Downstream models keep cached bindings.
    """
    request = (op_id, machine_id, worker_id, parents, factory_id)
    return local_transitions(instance, params, (request,), cached_trace)[0]


def local_transitions(instance, params, requests, cached_trace):
    """Batch local defects against old states, validating fatigue arrays once.

    Each request is (op_id, machine_id, worker_id, parents, factory_id).
    A None factory_id preserves the cached factory. Requests are independent:
    one result never changes a later request's predecessor states.
    """
    arrays = params.arrays(instance)
    results = []
    for op_id, machine_id, worker_id, parents, factory_id in requests:
        old = cached_trace.operations[op_id]
        if old.stage != 0:
            raise ValueError("local resource/parent rebinding is restricted to first stage")
        factory = old.factory if factory_id is None else factory_id
        values, _ = _transition(instance, arrays, op_id, factory, machine_id,
                                worker_id, parents, cached_trace.C, cached_trace.v)
        results.append(LocalTransition(*values))
    return tuple(results)


def replay(instance, params, cached_trace, base=None, retain_trace=True):
    """Frozen bindings/order replay for finite differences, with max branches live."""
    arrays = params.arrays(instance)
    C, H = np.zeros(instance.operations), np.zeros(instance.operations)
    traces = [None] * instance.operations if retain_trace else None
    energy = labor = 0.0
    for op_id in cached_trace.execution_order:
        old = cached_trace.operations[op_id]
        override = None if base is None else base[op_id]
        values, times = _transition(instance, arrays, op_id, old.factory, old.machine_id,
                                    old.worker_id, old.parents, C, H, override)
        C[op_id], H[op_id] = values[:2]
        energy += values[2]
        labor += values[3]
        if retain_trace:
            traces[op_id] = _record(instance, arrays, op_id, old.factory, old.machine_id,
                                     old.worker_id, old.parents, values, times)
    objectives = np.array([max(C[list(cached_trace.final_ops)]), energy, labor])
    return DecodeResult(objectives, tuple(traces) if retain_trace else (), cached_trace.execution_order,
                        cached_trace.final_ops, cached_trace.provenance, C, H)
