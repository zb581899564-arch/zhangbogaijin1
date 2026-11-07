"""Targeted physical checks and branch-aware derivative diagnostics."""
from __future__ import annotations

from dataclasses import replace
import math
import numpy as np
from .adjoint import adjoint
from .decoder import decode, replay


def validate_schedule(instance, params, result, atol=1e-9):
    if len(result.operations) != instance.operations or len(result.execution_order) != instance.operations:
        raise AssertionError("complete trace required")
    seen, last_machine, last_worker = set(), {}, {}
    arrays = params.arrays(instance)
    energy = labor = 0.0
    for op_id in result.execution_order:
        op = result.operations[op_id]
        assert op.op_id == op_id == op.stage * instance.jobs + op.job
        assert all(p < 0 or p in seen for p in op.parents), "not topological"
        expected_job = op_id - instance.jobs if op.stage else -1
        assert op.parents[0] == expected_job
        assert op.parents[1] == last_machine.get(op.machine_uid, -1)
        assert op.parents[2] == last_worker.get(op.worker_uid, -1)
        if op.stage:
            assert result.operations[expected_job].factory == op.factory
        times = [result.C[p] if p >= 0 else 0.0 for p in op.parents]
        assert abs(op.start - max(times)) < atol
        before = result.v[op.parents[2]] if op.parents[2] >= 0 else arrays[3][op.worker_uid]
        u = before * math.exp(-arrays[1][op.worker_uid] * (op.start - times[2]))
        duration = op.base * (1 + arrays[2][op.worker_uid] * u)
        after = 1 - (1 - u) * math.exp(-arrays[0][op.worker_uid] * duration)
        expected_base = ((instance.processing[op.job, op.stage] / instance.speeds[op.factory][op.stage][op.machine_id]
                          + instance.setup[op.job, op.stage]) / instance.efficiencies[op.factory][op.stage][op.worker_id])
        assert abs(op.base - expected_base) < atol
        assert abs(op.u - u) < atol and abs(op.duration - duration) < atol
        assert abs(op.completion - op.start - duration) < atol and abs(op.v - after) < atol
        assert -atol <= op.u <= 1 + atol and -atol <= op.v <= 1 + atol
        gap = op.start - times[1] if op.parents[1] >= 0 else 0.
        expected_energy = instance.powers[op.factory][op.stage][op.machine_id] * duration + instance.standby[op.factory][op.stage][op.machine_id] * gap
        assert abs(op.energy - expected_energy) < atol
        assert abs(op.labor - instance.wages[op.factory][op.stage][op.worker_id] * duration) < atol
        last_machine[op.machine_uid] = last_worker[op.worker_uid] = op_id
        seen.add(op_id)
        energy += expected_energy
        labor += instance.wages[op.factory][op.stage][op.worker_id] * duration
    np.testing.assert_allclose(result.objectives, [max(result.C[list(result.final_ops)]), energy, labor], atol=atol, rtol=1e-12)
    return {"operations": len(seen), "negative_start_slope": sum(op.negative_start_slope for op in result.operations),
            "max_ties": len(result.makespan_ties)}


def branch_signature(result):
    """Aliases are the same branch; tied distinct parent IDs stay detectable."""
    return (tuple((i, result.operations[i].parents[result.operations[i].active_branch]) for i in result.execution_order),
            min(result.makespan_ties))


def topology_signature(result):
    return (result.execution_order, tuple((o.factory, o.machine_id, o.worker_id, o.parents) for o in result.operations))


def _perturbed_instance(instance, op, delta):
    processing = instance.processing.copy()
    processing[op.job, op.stage] += delta * instance.speeds[op.factory][op.stage][op.machine_id] * instance.efficiencies[op.factory][op.stage][op.worker_id]
    return replace(instance, processing=processing)


def finite_difference_check(instance, genome, params, weights=(1., 0., 0.), normscale=(1., 1., 1.), epsilon=1e-6):
    """Compare both fixed-topology replay and complete decoder with base FD.

    Branch/topology changes are excluded and COUNTED, not called derivative
    failures or silently dropped. The perturbation changes ST for just one op
    to give delta-base under the original binding.
    """
    original = decode(instance, genome, params)
    reverse = adjoint(original, instance, params, weights, normscale)
    base = np.array([o.base for o in original.operations])
    effective = np.asarray(weights) / np.asarray(normscale)
    expected_branch, expected_topology = branch_signature(original), topology_signature(original)
    report = {"replay_compared": 0, "full_compared": 0, "replay_branch_changes": 0, "full_branch_or_topology_changes": 0,
              "replay_max_scaled_error": 0., "full_max_scaled_error": 0.}
    for i, op in enumerate(original.operations):
        step = epsilon * max(1., base[i])
        if instance.processing[op.job, op.stage] <= step * instance.speeds[op.factory][op.stage][op.machine_id] * instance.efficiencies[op.factory][op.stage][op.worker_id]:
            raise ValueError("central difference would leave nonnegative processing domain")
        up, down = base.copy(), base.copy()
        up[i] += step
        down[i] -= step
        replay_pair = replay(instance, params, original, up), replay(instance, params, original, down)
        full_pair = (decode(_perturbed_instance(instance, op, step), genome, params),
                     decode(_perturbed_instance(instance, op, -step), genome, params))
        for name, pair in (("replay", replay_pair), ("full", full_pair)):
            stable = all(branch_signature(r) == expected_branch for r in pair)
            if name == "full":
                stable = stable and all(topology_signature(r) == expected_topology for r in pair)
            if not stable:
                report["replay_branch_changes" if name == "replay" else "full_branch_or_topology_changes"] += 1
                continue
            fd = float(effective @ (pair[0].objectives - pair[1].objectives) / (2 * step))
            error = abs(fd - reverse.grad_base[i]) / max(1., abs(fd), abs(reverse.grad_base[i]))
            report[f"{name}_compared"] += 1
            report[f"{name}_max_scaled_error"] = max(report[f"{name}_max_scaled_error"], error)
    return report
