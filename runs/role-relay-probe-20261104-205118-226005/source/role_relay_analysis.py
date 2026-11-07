"""No-search analysis of source/receiver responses and held-out ordinary restart controls."""
import numpy as np

from role_relay_plan import ROLES
from run_long_budget_bridge import read, rows, hypervolume, nondominated, write_once


def analyze(root):
    parents = {p["id"]: p for p in read(root / "parents.json")}
    cases = {c["id"]: c for c in read(root / "cases.json")}
    norm = read(root / "protocol.json")["normalization"]
    lower, scale = np.asarray(norm["lower"]), np.asarray(norm["scale"])
    normal = lambda x: (np.asarray(x) - lower) / scale
    base = normal(read(root / "background.json"))
    base_hv = hypervolume(base, (1.5,) * 3)
    records = rows(root / "trials.jsonl")
    assert len(records) == len(cases) == 512
    for r in records:
        c = cases[r["id"]]; p = parents[c["parent"]]
        assert r["successful"] == r["attempted"] == 257 and r["failed"] == 0
        assert r["decoder"]["dynamic.evaluations"] == 257
        assert r["search"].get("inter.evaluations", 0) + r["search"].get("intra.evaluations", 0) == 256
        assert any(point["objectives"] == p["objectives"] for point in r["front"]) or any(
            np.all(np.asarray(point["objectives"]) <= p["objectives"]) for point in r["front"])
        r.update({"cohort": p["cohort"], "source": p["source"], "split": p["split"], "parent": p["id"]})
        r["gain"] = max(0., hypervolume(np.vstack((base, normal([x["objectives"] for x in r["front"]]))), (1.5,) * 3) - base_hv)
    matrix = []
    for cohort in ("S", "U"):
        for split in ("TRAIN", "HOLDOUT"):
            for source in ROLES:
                for target in ROLES:
                    cell = [r for r in records if (r["cohort"], r["split"], r["source"], r["target"]) ==
                            (cohort, split, source, target)]
                    assert len(cell) == 8
                    matrix.append({"cohort": cohort, "split": split, "source": source, "target": target,
                                   "n": len(cell), "positive": sum(r["gain"] > 1e-12 for r in cell),
                                   "meanGain": float(np.mean([r["gain"] for r in cell])),
                                   "medianGain": float(np.median([r["gain"] for r in cell])),
                                   "meanSeconds": float(np.mean([r["searchSeconds"] for r in cell]))})
    decisions = []
    by = {(r["cohort"], r["split"], r["source"], r["target"]): r for r in matrix}
    for cohort in ("S", "U"):
        for target in ROLES:
            # This exploratory map is learned on TRAIN only. It is not an uncharged online selector.
            source = max((s for s in ROLES if s != target), key=lambda s: by[(cohort, "TRAIN", s, target)]["meanGain"])
            pool = [p for p in parents.values() if p["cohort"] == cohort and p["split"] == "HOLDOUT"]
            if target == "CENTER":
                key = lambda p: tuple(normal(p["objectives"]).tolist())
                # Ordinary multiobjective elite restart: rank by p+q PDDR on the same paid reference.
                def key(p):
                    x = np.asarray(p["objectives"])
                    a = np.asarray([q["objectives"] for q in pool])
                    dominated = np.sum(np.all(a <= x, axis=1) & np.any(a < x, axis=1))
                    dominates = np.sum(np.all(x <= a, axis=1) & np.any(x < a, axis=1))
                    return dominated + 1 / (dominates + 1), p["id"]
            else:
                obj = {"MAKESPAN": 0, "ENERGY": 1, "WORKER_COST": 2}[target]
                key = lambda p: (p["objectives"][obj], p["id"])
            elite = {p["id"] for p in sorted(pool, key=key)[:4]}
            rng = np.random.default_rng(9179001 + ROLES.index(target))
            random_set = set(rng.choice([p["id"] for p in pool], 4, replace=False))
            selected = {"RELAY": {p["id"] for p in pool if p["source"] == source},
                        "SELF": {p["id"] for p in pool if p["source"] == target},
                        "ELITE": elite, "RANDOM": random_set}
            report = {}
            for name, chosen in selected.items():
                for seed in (9173001, 9173027):
                    group = [r for r in records if r["parent"] in chosen and r["seed"] == seed and r["target"] == target]
                    assert len(group) == 4
                    front = [x["objectives"] for r in group for x in r["front"]]
                    report[f"{name}:{seed}"] = max(0., hypervolume(np.vstack((base, normal(front))), (1.5,) * 3) - base_hv)
            mean = {n: float(np.mean([report[f"{n}:{s}"] for s in (9173001, 9173027)])) for n in selected}
            passed = all(mean["RELAY"] > mean[n] + 1e-12 for n in ("SELF", "ELITE", "RANDOM"))
            decisions.append({"cohort": cohort, "target": target, "trainSelectedSource": source,
                              "heldoutBatchGain": mean, "replicateBatchGain": report, "beatsAllOrdinary": passed})
    # This gate only justifies a new closed-loop protocol, never full-cost efficacy.
    eligible = sum(d["beatsAllOrdinary"] for d in decisions if d["cohort"] == "S") >= 2
    output = {"backgroundHV": base_hv, "matrix": matrix, "heldout": decisions,
              "gate": "WORTH_CLOSED_LOOP" if eligible else "NO_ROLE_RELAY_SUPPORT",
              "limitation": "Role source is associated with starting quality; this does not identify an effect "
                            "beyond objective quality. Learning/probe cost is charged to development and has no "
                            "same-time search claim. Separate original-vs-relay full-budget testing is mandatory."}
    write_once(root / "analysis.json", output)
    return output
