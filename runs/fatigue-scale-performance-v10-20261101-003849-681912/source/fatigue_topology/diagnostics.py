"""Topology labels are offline observations, never an online selection gate."""
import numpy as np


def binding(op):
    return op.factory, op.machine_id, op.worker_id, op.parents


def regime(parent, child, jobs):
    first_graph = later_graph = first_branch = later_branch = 0
    for old, new in zip(parent.operations, child.operations):
        graph_change = binding(old) != binding(new)
        branch_change = old.parents[old.active_branch] != new.parents[new.active_branch]
        if old.op_id < jobs:
            first_graph += graph_change
            first_branch += branch_change
        else:
            later_graph += graph_change
            later_branch += branch_change
    sink = min(parent.makespan_ties) != min(child.makespan_ties)

    def order(result):
        groups = {}
        for i in result.execution_order:
            op = result.operations[i]
            if op.stage:
                groups.setdefault((op.factory, op.stage), []).append(op.job)
        return groups

    def label(graph, branches):
        if graph:
            return "topology_changed"
        return "graph_same_branch_changed" if branches or sink else "graph_same_branch_same"

    return {"first_graph_changed_ops": first_graph, "later_graph_changed_ops": later_graph,
            "first_active_parent_changed_ops": first_branch, "later_active_parent_changed_ops": later_branch,
            "sink_changed": sink, "later_execution_order_changed": order(parent) != order(child),
            "full_regime": label(first_graph + later_graph, first_branch + later_branch),
            "later_regime": label(later_graph, later_branch)}


def error_terms(cheap, cut, fixed, actual):
    terms = np.array([cut - cheap, fixed - cut, actual - fixed], dtype=float)
    np.testing.assert_allclose(terms.sum(), actual - cheap, atol=1e-12, rtol=1e-10)
    return dict(zip(("stage0_approximation", "downstream_nonlinearity_or_max", "later_dispatch_change"), terms.tolist()))
