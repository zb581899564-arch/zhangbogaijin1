"""Read materialized physical inputs and derive a conservative makespan bound."""
import re
import numpy as np


def load_materialized(folder, stem, sources):
    path = folder / (stem + ".txt"); text = sources.text(path)
    factories, stages, jobs = map(int, text.splitlines()[0].split())
    rows = [line.strip() for line in text.splitlines()[1:] if re.fullmatch(r"[-+0-9.eE,\s]+", line.strip())]
    cursor = 0
    def take(count):
        nonlocal cursor
        values = np.asarray([float(value) for value in rows[cursor].split(",")]); cursor += 1
        if len(values) != count or not np.isfinite(values).all():
            raise ValueError("Malformed physical numeric row: " + str(path))
        return values
    machines = [take(stages) for _ in range(factories)]
    if any(np.any(values < 1) or np.any(values != values.astype(int)) for values in machines):
        raise ValueError("Invalid machine counts")
    speeds = [[take(int(machines[f][k])) for k in range(stages)] for f in range(factories)]
    powers = [[take(int(machines[f][k])) for k in range(stages)] for f in range(factories)]
    processing = np.asarray([take(stages) for _ in range(jobs)])
    totals = take(factories)
    if np.any(totals != totals.astype(int)) or np.any(totals < stages):
        raise ValueError("Invalid total worker counts")
    levels = [take(int(total)) for total in totals]; costs = [take(int(total)) for total in totals]
    if cursor != len(rows) or np.any(processing <= 0):
        raise ValueError("Unconsumed data or nonpositive ST")
    if any(np.any(v <= 0) for factory in speeds for v in factory) or any(np.any(v <= 0) for v in levels):
        raise ValueError("Nonpositive speed/worker efficiency")
    if any(np.any(v < 0) for factory in powers for v in factory) or any(np.any(v < 0) for v in costs):
        raise ValueError("Negative physical power/wage")
    setup_path = folder / "RECONSTRUCTED-setup.txt"
    setup = np.asarray([[float(value) for value in line.split(",")] for line in sources.text(setup_path).splitlines() if line.strip() and not line.startswith("#")])
    if setup.shape != (jobs, stages) or not np.isfinite(setup).all() or np.any(setup < 0):
        raise ValueError("Malformed materialized SUT")
    fatigue_path = folder / "fatigue-input.txt"; workers = [[set() for _ in range(stages)] for _ in range(factories)]
    seen = set()
    for line in sources.text(fatigue_path).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        values = [float(value) for value in line.split(",")]
        if len(values) != 7 or not all(np.isfinite(values)):
            raise ValueError("Malformed fatigue input")
        f, k, w = map(int, values[:3])
        if values[:3] != [f, k, w] or not (0 <= f < factories and 0 <= k < stages and w >= 0):
            raise ValueError("Invalid fatigue resource id")
        if (f, k, w) in seen or any(value < 0 for value in values[3:6]) or not 0 <= values[6] <= 1:
            raise ValueError("Fatigue parameters do not ensure beta*u>=0")
        seen.add((f, k, w)); workers[f][k].add(w)
    counts = [[len(values) for values in factory] for factory in workers]
    min_base = np.zeros((factories, jobs, stages)); concurrency = np.zeros((factories, stages))
    for f in range(factories):
        if sum(counts[f]) != totals[f]:
            raise ValueError("Materialized workers do not partition benchmark worker rows")
        at = 0
        for k in range(stages):
            count = counts[f][k]
            if workers[f][k] != set(range(count)) or count != (int(machines[f][k]) - 1 if machines[f][k] > 2 else int(machines[f][k])):
                raise ValueError("Worker-stage partition differs from current model contract")
            efficiency = max(levels[f][at:at + count]); at += count
            min_base[f, :, k] = (processing[:, k] / max(speeds[f][k]) + setup[:, k]) / efficiency
            concurrency[f, k] = min(machines[f][k], count)
    return {"jobs": jobs, "factories": factories, "stages": stages, "minBase": min_base,
        "concurrency": concurrency, "source": str(path), "setupSource": str(setup_path), "fatigueSource": str(fatigue_path)}


def safe_bound(model, fa):
    if len(fa) != model["jobs"] or set(fa) != set(range(model["factories"])):
        raise ValueError("Incomplete or empty fixed-FA context")
    job_path = max(sum(model["minBase"][f, job, :]) for job, f in enumerate(fa))
    load = max(sum(model["minBase"][f, job, k] for job, assigned in enumerate(fa) if assigned == f) /
               model["concurrency"][f, k] for f in range(model["factories"]) for k in range(model["stages"]))
    return {"jobPathLB": float(job_path), "stageLoadLB": float(load), "safeCmaxLB": float(max(job_path, load))}
