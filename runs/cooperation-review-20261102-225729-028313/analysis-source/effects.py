"""Recompute same-campaign paired effects from saved per-run HVs."""
from statistics import mean, median


CAMPAIGNS = (
    ("semantic-repair-20261102-130342-703425", (
        ("SHARE_FIX", "SYNC_FIX", "sharing_module"),
        ("SHARE_FIX", "SO", "net_configuration"))),
    ("job-aligned-closure-20261102-174433-417375", (
        ("SHARE", "SO", "net_configuration"),
        ("SHARE_JOB", "SO_JOB", "net_configuration"))),
    ("sync-job-audit-20261102-184848-424022", (
        ("SHARE_JOB", "SYNC_JOB", "sharing_module"),
        ("SHARE_JOB", "SO_JOB", "net_configuration"))),
    ("center-last-20261102-211306-648128", (
        ("SHARE_ORIGINAL", "SYNC_ORIGINAL", "sharing_module"),
        ("SHARE_LAST", "SYNC_LAST", "sharing_module"))),
)


def historical_effects(project, sources):
    seeds, instances, overall, propagation = [], [], [], []
    for name, pairs in CAMPAIGNS:
        root = project / "runs" / name
        status = sources.json(root / "final-status.json")
        analysis = root / status["analysis"]
        records_path = analysis / "records.json"
        records = sources.json(records_path)
        index = {(row["instance"], row["seed"], row["variant"]): row for row in records}
        if len(index) != len(records):
            raise ValueError("Duplicate historical metric cell")
        for candidate, control, kind in pairs:
            for instance in sorted({row["instance"] for row in records}):
                subset = sorted({row["seed"] for row in records if row["instance"] == instance})
                if len(subset) != 5:
                    raise ValueError("Five complete seeds required")
                identity = {"campaign": name, "candidate": candidate, "control": control,
                            "kind": kind, "instance": instance, "source": str(records_path)}
                paired = []
                for seed in subset:
                    a, b = index[instance, seed, candidate], index[instance, seed, control]
                    row = identity | {"seed": seed, "candidateT": a["hv"]["1.5"],
                        "controlT": b["hv"]["1.5"], "candidateFE15000": a["hv_fe15000"],
                        "controlFE15000": b["hv_fe15000"]}
                    seeds.append(row); paired.append(row)
                result = identity | {"seeds": len(subset)}
                for suffix in ("T", "FE15000"):
                    av = [row["candidate" + suffix] for row in paired]
                    bv = [row["control" + suffix] for row in paired]
                    if any(value is None for value in av + bv):
                        raise ValueError("Censored historical fixed-FE comparison")
                    denominator = mean(bv)
                    if denominator <= 1e-12:
                        raise ValueError("Unresolved effect denominator")
                    effect = 100 * (mean(av) - denominator) / denominator
                    positives = sum(a > b for a, b in zip(av, bv))
                    negatives = sum(a < b for a, b in zip(av, bv))
                    result.update({"effect" + suffix + "Percent": effect,
                        "positiveSeeds" + suffix: positives, "negativeSeeds" + suffix: negatives,
                        "practicalWin" + suffix: effect >= 1 and positives >= 3,
                        "practicalLoss" + suffix: effect <= -1 and negatives >= 3})
                instances.append(result)
            group = [row for row in instances if row["campaign"] == name
                     and row["candidate"] == candidate and row["control"] == control]
            overall.append({"campaign": name, "candidate": candidate, "control": control, "kind": kind,
                "instances": len(group), "meanTPercent": mean(row["effectTPercent"] for row in group),
                "medianTPercent": median(row["effectTPercent"] for row in group),
                "meanFE15000Percent": mean(row["effectFE15000Percent"] for row in group),
                "practicalWinsT": sum(row["practicalWinT"] for row in group),
                "practicalLossesT": sum(row["practicalLossT"] for row in group), "source": str(records_path)})
        # Flags belong to generated origin IDs and follow unchanged encodings.
        # Multiple generated origins may share an encoding; this is not a global
        # count of distinct genotypes, descendants, or final-HV attribution.
        import csv, io
        metric_path = analysis / "run-metrics.csv"
        for row in csv.DictReader(io.StringIO(sources.text(metric_path))):
            if not row["variant"].startswith("SHARE"):
                continue
            identity = {"campaign": name, "instance": row["instance"], "seed": int(row["seed"]),
                        "variant": row["variant"], "source": str(metric_path)}
            fields = ["successful", "attempted", "deadlineValidFE", "searchSeconds", "cooperationSeconds",
                      "semanticAudit.originsCap"]
            fields += [field for field in row if field.startswith("semanticAudit.sharedOrigins")]
            propagation.append(identity | {field: float(row[field]) if row[field] else None for field in fields})
    return seeds, instances, overall, propagation
