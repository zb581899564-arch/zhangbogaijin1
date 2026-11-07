"""Joint indicator analysis for an early mechanism contrast, not method qualification."""
import numpy as np

from run_long_budget_bridge import rows, hypervolume, igd_plus, nondominated
from research.dynamic_benchmark.tri_indicators import bidirectional_coverage, directional_description


def analyze(root, plan, *, phase=None, kind="FE"):
    instances = []
    for spec in plan["instances"]:
        stem, norm = spec["stem"], spec["normalization"]
        limit = spec["time_seconds"] if kind == "TIME" else spec["feLimit"]
        fronts, receipts, observations = {}, {}, []
        for seed in plan["seeds"]:
            for label in plan["methods"]:
                out = root / stem / str(seed) / ((phase + "-" if phase else "") + label)
                point, = [r for r in rows(out / "anytime.jsonl") if r["checkpointKind"] == kind
                          and r["checkpoint"] == limit and r["reached"]]
                fronts[seed, label] = np.asarray(point["front"], dtype=float)
                receipts[seed, label], = rows(out / "run-receipt.jsonl")
        normalized = {key: (f - norm["lower"]) / norm["scale"] for key, f in fronts.items()}
        reference = nondominated(np.vstack(list(normalized.values())))
        values = {}
        for (seed, label), front in normalized.items():
            receipt = receipts[seed, label]
            value = {"seed": seed, "method": label, "frontSize": len(front),
                "HV": {str(r): hypervolume(front, (r,) * 3) for r in (1.25, 1.5, 2.)},
                "IGDplus": igd_plus(front, reference), "objectiveMin": fronts[seed, label].min(axis=0).tolist(),
                "specialistOnlyCandidates": receipt["search"].get("specialistOnlyAcceptanceCandidates"),
                "blockedCandidates": receipt["search"].get("blockedSpecialistOnly"),
                "successfulFE": receipt["successful"], "searchSeconds": receipt["searchSeconds"]}
            values[seed, label] = value
            observations.append(value)
        comparisons = []
        for a, b in plan["comparisons"]:
            pairs = []
            for seed in plan["seeds"]:
                av, bv = values[seed, a], values[seed, b]
                assert all(x > 1e-12 for x in bv["HV"].values())
                hv = {str(r): 100 * (av["HV"][str(r)] / bv["HV"][str(r)] - 1) for r in (1.25, 1.5, 2.)}
                den = av["IGDplus"] + bv["IGDplus"]
                igd = 200 * (av["IGDplus"] - bv["IGDplus"]) / den if den else 0.
                c = bidirectional_coverage(fronts[seed, a], fronts[seed, b])
                pairs.append({"seed": seed, "HVEffectPct": hv, "IGDplusSymmetricWorseningPct": igd,
                    "coverage": c, "directions": directional_description(hv["1.5"], igd, c["C_A_B"], c["C_B_A"])})
            med_hv = {str(r): float(np.median([p["HVEffectPct"][str(r)] for p in pairs])) for r in (1.25, 1.5, 2.)}
            med_igd = float(np.median([p["IGDplusSymmetricWorseningPct"] for p in pairs]))
            med_ab = float(np.median([p["coverage"]["C_A_B"] for p in pairs]))
            med_ba = float(np.median([p["coverage"]["C_B_A"] for p in pairs]))
            comparisons.append({"A": a, "B": b, "pairs": pairs, "medianHVEffectPct": med_hv,
                "medianIGDplusSymmetricWorseningPct": med_igd, "medianC_A_B": med_ab, "medianC_B_A": med_ba,
                "medianDirections": directional_description(med_hv["1.5"], med_igd, med_ab, med_ba)})
        instances.append({"stem": stem, "feLimit": limit, "empiricalReferenceSize": len(reference),
            "observations": observations, "comparisons": comparisons})
    return {"instances": instances, "sameTimeProved": False, "finalAlgorithmQualified": False,
        "scope": "Two full PA generations on two development instances and two fresh seeds; causal acceptance contrast only",
        "oldLearningOrQualificationDecisionReopened": False, "goalAchieved": False}
