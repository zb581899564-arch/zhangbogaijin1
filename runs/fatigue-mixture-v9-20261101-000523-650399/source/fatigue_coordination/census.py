"""One common physical decoder evaluated exhaustively; trace QA is separate."""
from time import perf_counter_ns
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.validation import validate_schedule
from .protocol import PROTOCOL


def evaluate(instance, params, space, output, records, counts, identity):
    objectives = np.empty((3, space.size, 3))
    C = np.empty((3, space.size, instance.operations))
    H = np.empty_like(C)
    reference = decode(instance, space.state(0).genome(), params["beta0"], retain_trace=False).objectives
    counts["reference_full"] += 1
    sampled = np.random.default_rng(20261125+identity["seed"]).choice(space.size, 8, replace=False)
    for mi, name in enumerate(PROTOCOL["models"]):
        started = perf_counter_ns()
        for i in range(space.size):
            result = decode(instance, space.state(i).genome(), params[name], retain_trace=False)
            objectives[mi, i], C[mi, i], H[mi, i] = result.objectives, result.C, result.v
        counts["census_full"] += space.size
        counts["census_ns"] += perf_counter_ns()-started
        assert np.isfinite(objectives[mi]).all() and np.isfinite(C[mi]).all() and np.isfinite(H[mi]).all()
        assert np.min(H[mi]) >= 0 and np.max(H[mi]) <= 1
        started = perf_counter_ns()
        for i in sampled:
            full = decode(instance, space.state(i).genome(), params[name])
            np.testing.assert_array_equal(full.objectives, objectives[mi, i])
            np.testing.assert_array_equal(full.C, C[mi, i])
            np.testing.assert_array_equal(full.v, H[mi, i])
            validate_schedule(instance, params[name], full)
            counts["sample_QA_full"] += 1
        counts["sample_QA_ns"] += perf_counter_ns()-started
        records.emit("validation", {**identity, "model": name, "sampled_states": sampled,
            "full_vs_minimal_objectives_C_v_bitwise_equal": True, "all_states_finite": True})
        print(f"DECODED N={instance.jobs} seed={identity['seed']} {name} states={space.size}", flush=True)
    np.savez_compressed(output/"physical_tables.npz", objectives=objectives, C=C, fatigue=H, reference=reference)
    return objectives, C, H, reference
