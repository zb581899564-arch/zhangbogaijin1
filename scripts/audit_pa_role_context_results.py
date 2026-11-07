"""Independent scalar scoring checks and a scope correction for conditional dependence."""
from collections import Counter
import math
from pathlib import Path

import numpy as np

from run_long_budget_bridge import ROOT, read, write_once
from pa_role_context_data import group_folds, pair_data, physical_key
from pa_role_context_scores import score
from research.semantic_repair.evidence import digest


def scalar_score(data, train, query):
    n, f = len(train), data["factories"]
    nll = gain = order_loss = order_pairs = 0.
    for pair in range(data["codes"].shape[1]):
        counts = Counter(int(data["codes"][i, pair]) for i in train)
        cell = int(data["codes"][query, pair])
        a, b = divmod(cell, f)
        joint = (counts[cell] + .5) / (n + .5 * f * f)
        marginal_a = (sum(counts[a*f+j] for j in range(f)) + .5*f) / (n + .5*f*f)
        marginal_b = (sum(counts[i*f+b] for i in range(f)) + .5*f) / (n + .5*f*f)
        nll -= math.log(joint)
        gain += math.log(joint / marginal_a / marginal_b)
        if data["same"][query, pair]:
            same = [i for i in train if data["same"][i, pair]]
            before = sum(bool(data["before"][i, pair]) for i in same)
            p = (before + .5) / (len(same) + 1)
            order_loss -= math.log(p if data["before"][query, pair] else 1-p)
            order_pairs += 1
    pairs = data["codes"].shape[1]
    return np.asarray([nll / pairs, gain / pairs, order_loss, order_pairs])


def audit(root):
    snapshots = read(root / "working-snapshots.json")
    source = Path(read(root / "protocol.json")["source"])
    plan = read(source / "protocol.json")
    specs = {p["stem"]: p for p in plan["instances"]}
    sources, comparisons, checked = {}, [], 0
    for item in snapshots:
        stem, points = item["stem"], item["points"]
        data = pair_data(points, int(stem.split("_")[2]), specs[stem]["normalization"])
        for kind in ("PHYSICAL", "FACTORY"):
            folds, weights = group_folds(points, kind)
            assert abs(weights.sum() - len({physical_key(p) for p in points})) < 1e-10
            groups = {}
            for i, point in enumerate(points):
                key = physical_key(point) if kind == "PHYSICAL" else tuple(point["factories"])
                groups.setdefault(key, set()).add(int(folds[i]))
            assert all(len(v) == 1 for v in groups.values())
            for query in (0, 37, 99):
                train = np.flatnonzero(folds != folds[query])
                vectorized = score(data, train, np.asarray([query]))[0]
                expected = scalar_score(data, train, query)
                assert np.max(abs(vectorized - expected)) < 1e-10
                checked += 1
        for alias in item["aliases"]:
            folder = Path(alias)
            names = ("catalog.jsonl", "events.jsonl") if item["kind"] == "ENGINEERING" else ("initial-population.jsonl",)
            for name in names:
                path = folder / name
                sources[str(path)] = digest(path)
    analysis = read(root / "analysis.json")
    for item in analysis["datasets"]:
        if item["kind"] != "ENGINEERING" or item["generation"] != 2:
            continue
        for kind, values in item["crossValidation"].items():
            role, ordinary = values["overall"]["ROLE"], values["overall"]["OBJECTIVE_NEAREST_MATCHED"]
            factory = role["factoryPairNLL"] - ordinary["factoryPairNLL"]
            order = role["sameFactoryOrderNLL"] - ordinary["sameFactoryOrderNLL"]
            comparisons.append({"id": item["id"], "blocking": kind,
                                "roleMinusOrdinaryFactoryNLL": factory, "roleMinusOrdinaryOrderNLL": order,
                                "roleNotWorseOnBothPredictionLosses": factory <= 0 and order <= 0})
    write_once(root / "input-hashes-post-audit.json", sources)
    return {"status": "passed", "scalarQueryScoreComparisons": checked,
            "physicalDuplicatesAndFactoryPatternsNeverCrossFolds": True,
            "duplicateQueryWeightsSumToPhysicalGenotypeCount": True,
            "newSearchFE": 0, "newDecoderCalls": 0,
            "interpretationCorrection": "Requiring conditional JointGain exceed pooled Global is overly strong: conditioning may remove mixture-induced dependence while improving predictions. Original protocol/decision are retained; use the two prediction-loss comparisons below for the narrower factual conclusion, not a contribution veto",
            "roleVsOrdinaryPrediction": comparisons,
            "allEightRoleOrdinaryPairsNotWorseOnBothLosses": all(p["roleNotWorseOnBothPredictionLosses"] for p in comparisons),
            "goalAchieved": False}


if __name__ == "__main__":
    root = ROOT / "runs/pa-role-context-audit-20261106-005943-864946"
    result = audit(root)
    write_once(root / "independent-audit-and-interpretation.json", result)
    print("PA_ROLE_CONTEXT_INDEPENDENT_AUDIT_PASSED", result["scalarQueryScoreComparisons"],
          result["allEightRoleOrdinaryPairsNotWorseOnBothLosses"])
