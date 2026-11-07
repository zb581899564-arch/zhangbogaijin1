"""Numerical legality, canonical invariance and sampled trace equality gate."""
from collections import Counter
from dataclasses import asdict
from time import perf_counter_ns
import traceback
import numpy as np
from research.fatigue_mechanism.decoder import decode, _validate_genome
from research.fatigue_mechanism.validation import validate_schedule
from .artifacts import create
from .cases import instances, load, initial
from .operators import dimensions, draw
from .state import replay
from .records import Records, save


def validate(project):
    output, counts, started = create(project, "validation"), Counter(), perf_counter_ns()
    records, active = Records(output), None
    print(f"VALIDATION_DIRECTORY {output}", flush=True)
    try:
        for index, name in enumerate(instances(project)):
            active = name
            instance, profiles = load(project, index, name)
            genome, parent = initial(instance, 60013)
            for model, (params, _) in profiles.items():
                original = decode(instance, genome, params)
                canonical = decode(instance, parent.genome(), params, retain_trace=False)
                np.testing.assert_array_equal(original.objectives, canonical.objectives)
                np.testing.assert_array_equal(original.C, canonical.C)
                np.testing.assert_array_equal(original.v, canonical.v)
                validate_schedule(instance, params, original)
                counts["canonical_pairs"] += 1
                counts["full_calls"] += 2
                for family in ("plain", "swap_rebind"):
                    state = parent
                    for step in range(8):
                        child, edit = draw(state, family, dimensions(instance), 20261220+1009*index+step)
                        assert replay(state, edit) == child
                        _validate_genome(instance, child.genome())
                        value = decode(instance, child.genome(), params, retain_trace=False)
                        counts["full_calls"] += 1
                        if step == 7:
                            traced = decode(instance, child.genome(), params)
                            np.testing.assert_array_equal(traced.objectives, value.objectives)
                            np.testing.assert_array_equal(traced.C, value.C)
                            np.testing.assert_array_equal(traced.v, value.v)
                            validate_schedule(instance, params, traced)
                            counts["trace_pairs"] += 1
                            counts["full_calls"] += 1
                        counts["legal_moves"] += 1
                        state = child
                records.emit("validation", {"instance": name, "model": model, "canonical_bitwise": True,
                    "legal_children": 16, "trace_pairs": 2, "initial_state": asdict(parent)})
            print(f"VALIDATED {index+1}/36 {name}", flush=True)
        assert counts["canonical_pairs"] == 108 and counts["trace_pairs"] == 216 and counts["legal_moves"] == 1728
        save(output/"validation.json", {"status": "pass", "counts": dict(counts), "wall_ns": perf_counter_ns()-started})
    except BaseException:
        save(output/"failure.json", {"active": active, "counts": dict(counts), "traceback": traceback.format_exc()})
        raise
    finally:
        records.close()
    print(f"VALIDATION_PASS {output}", flush=True)
    return output
