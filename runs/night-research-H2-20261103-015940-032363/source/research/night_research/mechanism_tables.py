"""Full transfer counts and preservation rates, separate from quality conclusions."""
from research.expansion_screen._metrics import mean
from .factory_transfer import COUNTERS


def transfer_counters(run):
    return run["summary"].get("cooperation", {}).get("factoryTransfer", {})


def _rate(numerator, denominator):
    return numerator / denominator if denominator else None


def _method_summary(label, owners):
    totals = {key: sum(owner[key] for owner in owners) for key in COUNTERS}
    instances = []
    for instance in sorted({owner["instance"] for owner in owners}):
        rows = [owner for owner in owners if owner["instance"] == instance]
        paid = sum(owner["paidTransfers"] for owner in rows)
        intact = sum(owner["source0EncodingPreserved"] for owner in rows)
        timeline = sum(owner["source0TimelineMatched"] for owner in rows)
        instances.append({"instance": instance, "paidTransfers": paid,
            "localEncodingPreservedRate": _rate(intact, paid), "sourceTimelineMatchedRate": _rate(timeline, paid)})
    intact = [row["localEncodingPreservedRate"] for row in instances]
    timeline = [row["sourceTimelineMatchedRate"] for row in instances]
    return {"variant": label, "mode": owners[0]["mode"], "owners": len(owners), **totals,
        "pooledLocalEncodingPreservedRate": _rate(totals["source0EncodingPreserved"], totals["paidTransfers"]),
        "pooledSourceTimelineMatchedRate": _rate(totals["source0TimelineMatched"], totals["paidTransfers"]),
        "instanceMeanLocalEncodingPreservedRate": mean(intact) if all(value is not None for value in intact) else None,
        "instanceMeanSourceTimelineMatchedRate": mean(timeline) if all(value is not None for value in timeline) else None,
        "instances": instances}


def transfer_tables(runs):
    owners, opportunities = [], []
    for run in runs:
        counters = transfer_counters(run)
        if not counters:
            continue
        identity = {key: run[key] for key in ("instance", "seed", "variant")}
        owners.append({**identity, "mode": counters["mode"], **{key: counters[key] for key in COUNTERS},
            "localEncodingPreservedRate": _rate(counters["source0EncodingPreserved"], counters["paidTransfers"]),
            "sourceTimelineMatchedRate": _rate(counters["source0TimelineMatched"], counters["paidTransfers"])})
        opportunities.extend({**identity, **cell, "scheduledAttempts": cell["opportunities"] // 4}
            for cell in counters["perFamilyDirection"])
    methods = [_method_summary(label, [row for row in owners if row["variant"] == label])
        for label in sorted({row["variant"] for row in owners})]
    return {"methodSummary": methods, "ownerRows": owners, "opportunityRows": opportunities,
        "scope": "Full-search counts include late events; deadline-valid counts are separate. Preservation rates are descriptive witnesses, not quality or significance. Local encodings replayed independently; atomic timelines and other factories witnessed by accepted Java checks."}
