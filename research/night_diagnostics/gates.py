"""Old-evidence resource-gate suggestions, before any new night performance."""


def suggestions(tables):
    seeds = []
    for row in tables["archive-coverage"]:
        if row["variant"] != "SHARE_SPECIAL":
            continue
        identity = {key: row[key] for key in ("campaign", "instance", "seed")}
        requests = [item for item in tables["single-request-summary"] if all(item[key] == value for key, value in identity.items())]
        h1 = {"allFourFamiliesRecovered": row["recoveredFamilyCount"] == 4,
            "cutoffEncodingsComplete": row["cutoffUnknownEncodings"] == 0,
            "atLeast4NonFamilyFA": row["nonFamilyUniqueFA"] >= 4,
            "nonFamilyExclusiveHVAtLeast1Percent": row["nonFamilyExclusiveHVFraction"] is not None and row["nonFamilyExclusiveHVFraction"] >= .01}
        h2_requests = [item["request"] for item in requests if item["anyMaterialParetoImprovement"]]
        seeds.append(identity | {"H1conditions": h1, "H1passes": all(h1.values()),
            "H2potentialRequestIDs": h2_requests, "H2passesNumericPotential": bool(h2_requests),
            "H2actualGeneIntegrityLossIdentified": False, "source": row["source"]})
    instances = []
    for campaign, instance in sorted({(row["campaign"], row["instance"]) for row in seeds}):
        group = [row for row in seeds if row["campaign"] == campaign and row["instance"] == instance]
        instances.append({"campaign": campaign, "instance": instance, "H1passingSeeds": sum(row["H1passes"] for row in group),
            "H2passingPotentialSeeds": sum(row["H2passesNumericPotential"] for row in group), "requiredSeeds": 3})
    return {"status": "SUGGESTIONS_FOR_MAIN_AGENT_TO_FREEZE", "seedEvidence": seeds, "instanceEvidence": instances,
        "H1suggestion": "At least3 instances x at least3/5 seeds: four contexts recovered, no unknown cutoff encoding,>=4 nonfamily FA,>=1% nonfamily exclusive HV",
        "H2suggestion": "At least3 instances x at least3/5 seeds: at least1 changed whole-factory substitution with all3 goals no worse and one>=0.1% better",
        "H2limitation": "Numeric potential supports a paid controlled preservation test; actual gene-transfer loss remains unmeasured",
        "newPerformanceUsed": False, "automaticExperimentAuthorization": False}
