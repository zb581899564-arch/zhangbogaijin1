"""Reverse-mode derivatives through the actual traced execution topology."""
from __future__ import annotations

import math
import numpy as np
from .model import AdjointResult


def local_derivatives(instance, arrays, op, completion, include_fatigue=True):
    """Columns: C_job, C_machine, C_worker, v_worker, base."""
    a, mu, beta, _ = (x[op.worker_uid] for x in arrays)
    ds = np.zeros(5)
    ds[op.active_branch] = 1.0
    du = np.zeros(5)
    if include_fatigue:
        # exp(-mu*(S-Cw)) is also defined when h0=0, so do not divide by h.
        worker_finish = completion[op.parents[2]] if op.parents[2] >= 0 else 0.0
        recovery = math.exp(-mu * (op.start - worker_finish))
        du = -mu * op.u * ds
        du[2] += mu * op.u
        du[3] += recovery
    dp = op.base * beta * du
    dp[4] += 1.0 + beta * op.u
    dC = ds + dp
    ep = math.exp(-a * op.duration)
    dH = ep * du + a * (1.0 - op.u) * ep * dp if include_fatigue else np.zeros(5)
    dgap = np.zeros(5)
    if op.parents[1] >= 0:
        dgap = ds.copy()
        dgap[1] -= 1.0
    power = instance.powers[op.factory][op.stage][op.machine_id]
    idle = instance.standby[op.factory][op.stage][op.machine_id]
    wage = instance.wages[op.factory][op.stage][op.worker_id]
    return np.vstack((dC, dH)), power * dp + idle * dgap, wage * dp


def adjoint(result, instance, params, weights=(1., 0., 0.), normscale=(1., 1., 1.), include_fatigue=True):
    """Gradient of dot(weights / normscale, [Cmax, TEC, TWC]).

    include_fatigue=False holds u/duration's state dependence fixed on the SAME
    fatigue forward trace; it is a time-channel control, not another model.
    """
    if not result.operations or not result.execution_order:
        raise ValueError("adjoint requires a retained forward trace")
    weights, normscale = np.asarray(weights, float), np.asarray(normscale, float)
    if weights.shape != (3,) or normscale.shape != (3,) or not np.all(np.isfinite(weights)) or not np.all(np.isfinite(normscale)) or np.any(normscale <= 0):
        raise ValueError("three finite weights and positive normalization scales required")
    effective = weights / normscale
    arrays = params.arrays(instance)
    costates, gradient = np.zeros((instance.operations, 2)), np.zeros(instance.operations)
    critical = max(result.final_ops, key=lambda op: (result.C[op], -op))
    costates[critical, 0] = effective[0]
    for op_id in reversed(result.execution_order):
        op = result.operations[op_id]
        jac, de, dw = local_derivatives(instance, arrays, op, result.C, include_fatigue)
        pullback = jac.T @ costates[op_id] + effective[1] * de + effective[2] * dw
        gradient[op_id] = pullback[4]
        # Alias roles MUST accumulate; a predecessor can be all three parents.
        for role, parent in enumerate(op.parents):
            if parent >= 0:
                costates[parent, 0] += pullback[role]
        if op.parents[2] >= 0:
            costates[op.parents[2], 1] += pullback[3]
    return AdjointResult(costates, gradient, float(effective @ result.objectives), effective)


def adjoint_objectives(result, instance, params, normscale=(1., 1., 1.), include_fatigue=True):
    return tuple(adjoint(result, instance, params, w, normscale, include_fatigue) for w in np.eye(3))
