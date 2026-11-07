"""Cost-only representative timings, no outcome-based protocol changes."""
from time import perf_counter_ns
import numpy as np
from research.fatigue_mechanism.decoder import decode
from .cases import instances, load, initial
from .operators import dimensions, draw
from .records import save


def run(project, output):
    rows, used, full = [], set(), 0
    for i, name in enumerate(instances(project)):
        instance, profiles = load(project, i, name)
        if instance.jobs in used:
            continue
        used.add(instance.jobs)
        _, parent = initial(instance, 60013)
        params = profiles["strong_fast_recovery"][0]
        for family in ("plain", "swap_rebind"):
            times, generations = [], []
            for repeat in range(8):
                started = perf_counter_ns()
                state, _ = draw(parent, family, dimensions(instance), 20261221+repeat)
                generated = perf_counter_ns()
                decode(instance, state.genome(), params, retain_trace=False)
                full += 1
                generations.append(generated-started)
                times.append(perf_counter_ns()-generated)
            rows.append({"instance": name, "jobs": instance.jobs, "family": family,
                         "median_generation_ns": int(np.median(generations)), "median_decode_ns": int(np.median(times))})
    save(output/"cost_calibration.json", {"no_gains_used": True, "rows": rows, "full_calls": full})
    return full
