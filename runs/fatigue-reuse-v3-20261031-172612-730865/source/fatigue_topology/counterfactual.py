"""Feasible stage-boundary intervention and downstream-only pullbacks."""
from dataclasses import dataclass
import numpy as np
from research.fatigue_mechanism.decoder import _transition, _record, _validate_genome
from research.fatigue_mechanism.adjoint import local_derivatives
from research.fatigue_mechanism.model import DecodeResult


@dataclass(frozen=True)
class FirstStage:
    C: np.ndarray
    v: np.ndarray
    operations: tuple
    order: tuple
    energy: float
    labor: float


def stage0(instance, genome, params):
    _validate_genome(instance, genome)
    arrays, attrs = params.arrays(instance), genome.by_job()
    C, H = np.zeros(instance.operations), np.zeros(instance.operations)
    records, order, energy, labor = [None] * instance.jobs, [], 0., 0.
    for f in range(instance.factories):
        last_m, last_w = {}, {}
        for j in genome.js:
            factory, m, w = attrs[j]
            if factory != f:
                continue
            parents = (-1, last_m.get(m, -1), last_w.get(w, -1))
            values, times = _transition(instance, arrays, j, f, m, w, parents, C, H)
            C[j], H[j] = values[:2]
            energy += values[2]
            labor += values[3]
            records[j] = _record(instance, arrays, j, f, m, w, parents, values, times)
            order.append(j)
            last_m[m] = last_w[w] = j
    return FirstStage(C, H, tuple(records), tuple(order), energy, labor)


def fixed_later(instance, params, first, parent):
    """New stage0 plus old downstream routes; all max branches stay live."""
    arrays = params.arrays(instance)
    C, H = first.C.copy(), first.v.copy()
    records = list(first.operations) + [None] * (instance.operations - instance.jobs)
    order, energy, labor = list(first.order), first.energy, first.labor
    for op_id in parent.execution_order:
        old = parent.operations[op_id]
        if old.stage == 0:
            continue
        values, times = _transition(instance, arrays, op_id, old.factory, old.machine_id,
                                    old.worker_id, old.parents, C, H)
        C[op_id], H[op_id] = values[:2]
        energy += values[2]
        labor += values[3]
        records[op_id] = _record(instance, arrays, op_id, old.factory, old.machine_id,
                                 old.worker_id, old.parents, values, times)
        order.append(op_id)
    objectives = np.array([max(C[list(parent.final_ops)]), energy, labor])
    return DecodeResult(objectives, tuple(records), tuple(order), parent.final_ops,
                        parent.provenance, C, H)


def boundary_costates(instance, params, parent, weights, include_fatigue=True):
    """Do not propagate inside stage0 or include its direct cost a second time."""
    effective = np.asarray(weights) / parent.objectives
    arrays, costates = params.arrays(instance), np.zeros((instance.operations, 2))
    critical = min(parent.makespan_ties)
    costates[critical, 0] = effective[0]
    for op_id in reversed(parent.execution_order):
        op = parent.operations[op_id]
        if op.stage == 0:
            continue
        jac, de, dw = local_derivatives(instance, arrays, op, parent.C, include_fatigue)
        pullback = jac.T @ costates[op_id] + effective[1] * de + effective[2] * dw
        for role, predecessor in enumerate(op.parents):
            if predecessor >= 0:
                costates[predecessor, 0] += pullback[role]
        if op.parents[2] >= 0:
            costates[op.parents[2], 1] += pullback[3]
    return costates[:instance.jobs]


def cut_prediction(instance, parent, first, weights, cut):
    old_direct = np.array([0., sum(o.energy for o in parent.operations[:instance.jobs]),
                           sum(o.labor for o in parent.operations[:instance.jobs])])
    new_direct = np.array([0., first.energy, first.labor])
    state_delta = np.column_stack((first.C[:instance.jobs] - parent.C[:instance.jobs],
                                   first.v[:instance.jobs] - parent.v[:instance.jobs]))
    return float((new_direct - old_direct) @ (np.asarray(weights) / parent.objectives)
                 + np.sum(cut * state_delta))
