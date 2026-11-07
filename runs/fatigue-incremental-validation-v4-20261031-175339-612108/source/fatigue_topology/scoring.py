"""Reuse v1 cheap scores; probes change exactly one local base time."""
import numpy as np
from research.fatigue_mechanism.decoder import _transition
from research.fatigue_mechanism.prediction import Defects, prepare_defects, score_defects
from research.fatigue_mechanism.adjoint import adjoint
from research.fatigue_mechanism.statistics import select_minima
from .counterfactual import boundary_costates
from .trials import delta_base


def prepare(instance, params, parent, trials):
    if not trials[0].relative_st:
        return prepare_defects(instance, params, parent, trials)
    arrays, defects = params.arrays(instance), []
    for trial in trials:
        op = parent.operations[trial.jobs[0]]
        values, _ = _transition(instance, arrays, op.op_id, op.factory, op.machine_id, op.worker_id,
                                op.parents, parent.C, parent.v, op.base + delta_base(instance, parent, trial))
        defects.append(Defects((op.op_id,), np.array([[values[0] - op.C, values[1] - op.v]]),
                               np.array([[0., values[2] - op.energy, values[3] - op.labor]])))
    return tuple(defects)


def reverses(instance, params, parent, targets):
    result = {}
    for target, weights in targets.items():
        result[target] = {
            "fatigue_adjoint": adjoint(parent, instance, params, weights, parent.objectives),
            "time_only": adjoint(parent, instance, params, weights, parent.objectives, False),
            "cut": boundary_costates(instance, params, parent, weights),
        }
    return result


def predictions(instance, trace, trials, defects, reverse):
    values = {}
    for target, pullbacks in reverse.items():
        scores = {m: score_defects(defects, pullbacks[m]) for m in ("fatigue_adjoint", "time_only")}
        tangents = None
        if trials[0].relative_st:
            tangents = {m: [float(pullbacks[m].grad_base[t.jobs[0]] * delta_base(instance, trace, t)) for t in trials]
                        for m in scores}
        values[target] = {"scores": {m: s.tolist() for m, s in scores.items()},
                          "ties": {m: select_minima(s).tolist() for m, s in scores.items()}, "tangents": tangents}
    return values
