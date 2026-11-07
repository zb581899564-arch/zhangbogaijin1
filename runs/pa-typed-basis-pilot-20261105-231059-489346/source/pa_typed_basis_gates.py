"""Prospective tri-indicator resource decisions for the new typed basis, not old gates."""
def noninferior(row, hv_margin, igd_margin, c_margin, seed_hv, seed_igd, seed_c):
    med_c = row["medianC_A_B"] - row["medianC_B_A"]
    return bool(row["medianHVEffectPct"]["1.5"] >= hv_margin - 1e-10
        and row["medianIGDplusSymmetricWorseningPct"] <= igd_margin + 1e-10 and med_c >= c_margin - 1e-12
        and all(p["HVEffectPct"]["1.5"] >= seed_hv - 1e-10
                and p["IGDplusSymmetricWorseningPct"] <= seed_igd + 1e-10
                and p["coverage"]["C_A_B"] - p["coverage"]["C_B_A"] >= seed_c - 1e-12 for p in row["pairs"]))


def readiness(analysis):
    instances = []
    for spec in analysis["instances"]:
        by = {r["B"]: r for r in spec["comparisons"]}
        sham, atom = by["SHAM_BLOCK"], by["ATOM"]
        component = noninferior(sham, .5, 0, 0, -1, 5, -.02)
        component = component and all(sham["medianHVEffectPct"][str(r)] >= -1e-10 for r in (1.25, 2.))
        preserved = noninferior(atom, 0, 5, -.02, -1, 10, -.05)
        preserved = preserved and all(atom["medianHVEffectPct"][str(r)] >= -1e-10 for r in (1.25, 2.))
        classic = {}
        for name in ("NSGA2_PLAIN", "NSGA2_DEEP"):
            row = by[name]
            classic[name] = noninferior(row, -1, 5, -.02, -5, 15, -.1)
            classic[name] = classic[name] and all(row["medianHVEffectPct"][str(r)] >= -1 - 1e-10 for r in (1.25, 2.))
        old = {}
        for name in ("FULL_SHARED_DEEP", "LI_RECON_DEEP"):
            row = by[name]
            old[name] = noninferior(row, 1, 0, 0, 0, 10, -.05)
            old[name] = old[name] and all(row["medianHVEffectPct"][str(r)] >= -1e-10 for r in (1.25, 2.))
        passed = component and preserved and all(classic.values()) and all(old.values())
        instances.append({"stem": spec["stem"], "componentBeyondMoreVisits": component,
            "preservesOriginal": preserved, "classicNoninferiority": classic, "oldControlsImproved": old, "pass": passed})
    return {"instances": instances, "pass": all(r["pass"] for r in instances),
        "scope": "Allocation of further study budget for this fixed ordinary basis only; no novel-method/paper qualification"}
