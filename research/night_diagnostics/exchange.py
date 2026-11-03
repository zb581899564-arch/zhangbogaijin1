"""Single whole-factory numeric substitutions; no candidate evaluation."""
from research.cooperation_roles.replay import assemble, encoding, score


def changes(candidate, parent):
    return [100 * (old - value) / old if old > 0 else None for value, old in zip(candidate, parent)]


def single_factory_potentials(request, identity, source):
    parent = request["parentObjectives"]
    factories = request["factories"]; rows = []
    for factory in factories:
        f = factory["factory"]
        for index, record in enumerate(factory["records"]):
            parts = [item["parent"] for item in factories]; parts[f] = record
            objectives = assemble(parts); improvements = changes(objectives, parent)
            changed = encoding(record) != encoding(factory["parent"])
            weak = all(value <= old + 1e-9 * max(1., old) for value, old in zip(objectives, parent))
            material = any(value is not None and value >= .1 for value in improvements)
            rows.append(identity | {"request": request["request"], "cycle": request["cycle"],
                "family": request["family"], "factory": f, "recordIndex": index,
                "producer": record["producer"], "sourcePaidFE": record["paidFE"], "sourceStage": record["stage"],
                "encodingChanged": changed, "potentialC": objectives[0], "potentialE": objectives[1], "potentialW": objectives[2],
                "parentC": parent[0], "parentE": parent[1], "parentW": parent[2],
                "gainMPercent": improvements[0], "gainEPercent": improvements[1], "gainWPercent": improvements[2],
                "deltaC": objectives[0] - parent[0], "deltaE": objectives[1] - parent[1], "deltaW": objectives[2] - parent[2],
                "capFeasible": objectives[0] <= request["cap"],
                "materialParetoImprovement": changed and weak and material,
                "weightedScore": score(objectives, request), "source": source})
    eligible = [row for row in rows if row["encodingChanged"]]
    cap_eligible = [row for row in eligible if row["capFeasible"]]
    summary = identity | {"request": request["request"], "family": request["family"], "cycle": request["cycle"],
        "potentialSubstitutions": len(eligible), "anyMaterialParetoImprovement": any(row["materialParetoImprovement"] for row in eligible),
        "anyCapFeasibleSingleSubstitution": bool(cap_eligible),
        "anyMaterialParetoAtCap": any(row["materialParetoImprovement"] for row in cap_eligible),
        "allFactoryAssemblyFeasible": request["feasible"], "source": source}
    for name in ("M", "E", "W"):
        values = [row["gain" + name + "Percent"] for row in eligible if row["gain" + name + "Percent"] is not None]
        summary["bestSingleGain" + name + "Percent"] = max(values) if values else None
        summary["anySingle" + name + "GainAtLeast01Percent"] = any(value >= .1 for value in values)
    combined = request["combinedObjectives"]
    full_gain = changes(combined, parent) if combined is not None else [None] * 3
    for name, value in zip(("M", "E", "W"), full_gain):
        summary["allFactoryGain" + name + "Percent"] = value
    summary["bestSingleCapWeightedScore"] = min(row["weightedScore"] for row in cap_eligible) if cap_eligible else None
    summary["allFactoryWeightedScore"] = score(combined, request) if combined is not None else None
    summary["singleUsesParentOutsideCurrentPoolSupport"] = True
    return rows, summary
