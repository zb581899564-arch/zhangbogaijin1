"""Demand counters by run then instance; bounded event replays kept separate."""
from research.cooperation_roles.tables import aggregate, observation_tables

COUNTERS = ("tightRequestsRecorded", "queries", "eligibleQueries", "actionableQueries", "routedOverrides", "resolvedOrNoGapQueries")


def demand_tables(runs):
    tables = observation_tables(runs)
    totals, samples, factories = [], [], []
    for run in runs:
        identity = {key: run[key] for key in ("instance", "seed", "variant")}
        data = run["summary"]["cooperation"].get("demandFeedback")
        row = identity | {"mode": data["mode"] if data else "NONE", "managerEnabled": data is not None,
            "source": run["folder"] + ("/demand-trace.jsonl" if data else "/summary.json")}
        row.update({field: data[field] if data else None for field in COUNTERS})
        for field, numerator, denominator in (("eligibleFraction", "eligibleQueries", "queries"),
                ("actionableFraction", "actionableQueries", "eligibleQueries"),
                ("overridePerActionableFraction", "routedOverrides", "actionableQueries"),
                ("resolvedOrNoGapFraction", "resolvedOrNoGapQueries", "eligibleQueries")):
            row[field] = data[numerator] / data[denominator] if data and data[denominator] else None
        row["capturedQueries"] = len(run["demandReplay"]) if data else None
        row["sampleEligibleCoverage"] = len(run["demandReplay"]) / data["eligibleQueries"] if data and data["eligibleQueries"] else None
        totals.append(row)
        for event in run["demandReplay"]:
            samples.append(identity | event | {"source": row["source"]})
            for factory, minimum in enumerate(event["factoryMinC"]):
                factories.append(identity | {"eligibleQuery": event["eligibleQuery"], "family": event["family"],
                    "factory": factory, "factoryMinC": minimum, "cap": event["cap"],
                    "relativeGap": (minimum - event["cap"]) / event["cap"],
                    "targeted": factory == event["targetFactory"], "selected": factory == event["selectedFactory"],
                    "source": row["source"]})
    fields = [*COUNTERS, "eligibleFraction", "actionableFraction", "overridePerActionableFraction",
              "resolvedOrNoGapFraction", "capturedQueries", "sampleEligibleCoverage"]
    per_instance = aggregate(totals, ("instance", "variant"), fields)
    summary = aggregate(per_instance, ("variant",), fields)
    for row in per_instance:
        row["sourceTable"] = "demand-run-metrics.csv; same instance/variant; five seeds"
    for row in summary:
        row["sourceTable"] = "demand-instance-metrics.csv; same variant; six instances equally"
    tables.update({"demand-run-metrics": totals, "demand-query-replay": samples,
        "demand-factory-gaps": factories, "demand-instance-metrics": per_instance, "demand-summary": summary})
    return tables
