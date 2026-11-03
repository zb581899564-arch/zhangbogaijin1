"""Flatten bounded observations while retaining their sampling/source limits."""
from statistics import mean
from research.center_last.observations import composition_metrics
from research.sync_job_audit.feedback import feedback_records


def aggregate(rows, keys, fields):
    groups = {}
    for row in rows:
        groups.setdefault(tuple(row[key] for key in keys), []).append(row)
    return [dict(zip(keys, key)) | {"units": len(group)} |
        {field: mean(row[field] for row in group if row[field] is not None)
            if any(row[field] is not None for row in group) else None for field in fields}
        for key, group in groups.items()]


def observation_tables(runs):
    tables = {name: [] for name in ("pool-run-metrics", "pool-request-replay", "producer-withdrawal",
        "pool-chosen-records", "composition-run-metrics", "composition-generation-metrics",
        "composition-paid-samples", "feedback-run-metrics", "feedback-steps", "coverage")}
    for run in runs:
        identity = {key: run[key] for key in ("instance", "seed", "variant")}
        summary = run["summary"]; search = summary["search"]
        tables["coverage"].append(identity | {"completeGenerations": search.get("generations.completed", 0),
            "startedGenerations": summary["semanticAudit"]["feedbackTiming"]["generationsStarted"],
            "FE15000Reached": run["fe"] is not None, "source": run["folder"] + "/summary.json"} |
            {key: value for key, value in search.items() if key.startswith(("qgs.g", "local.g"))})
        feedback, steps = feedback_records(run)
        feedback["source"] = run["folder"] + "/feedback-trace.jsonl"
        for row in steps:
            row["source"] = feedback["source"]
        tables["feedback-run-metrics"].append(feedback); tables["feedback-steps"].extend(steps)
        total, generations, samples = composition_metrics(run)
        if total is not None:
            total["source"] = run["folder"] + "/composition-trace.jsonl"
            for row in generations + samples:
                row["source"] = total["source"]
            tables["composition-run-metrics"].append(total)
            tables["composition-generation-metrics"].extend(generations)
            tables["composition-paid-samples"].extend(samples)
        if run["poolTrace"] is None:
            continue
        replays = run["poolReplay"]; count = len(replays); full = summary["cooperation"]["poolEvidence"]
        metrics = identity | full | {"capturedRequests": count,
            "sampleCoverage": count / full["requests"] if full["requests"] else None,
            "genuineComplementaritySamples": sum(row["genuineComplementarity"] for row in replays),
            "feasibilityCompletionSamples": sum(row["feasibilityCompletionWithoutWholeBaseline"] for row in replays),
            "multipleSearchProducerSamples": sum(row["distinctChosenSearchProducers"] >= 2 for row in replays),
            "source": run["folder"] + "/cooperation-evidence.jsonl"}
        tables["pool-run-metrics"].append(metrics)
        for replay in replays:
            tables["pool-request-replay"].append(identity | replay | {"source": metrics["source"]})
        tables["producer-withdrawal"].extend(identity | row | {"source": metrics["source"]} for row in run["poolWithdrawals"])
        for request in run["poolTrace"][1:]:
            for factory in request["factories"]:
                chosen = factory["chosen"]
                if chosen is not None:
                    tables["pool-chosen-records"].append(identity | {"request": request["request"],
                        "family": request["family"], "factory": factory["factory"],
                        "paidFE": chosen["paidFE"], "generation": chosen["generation"],
                        "stage": chosen["stage"], "producer": chosen["producer"],
                        "localC": chosen["objectives"][0], "localE": chosen["objectives"][1], "localW": chosen["objectives"][2],
                        "wholeC": chosen["wholeObjectives"][0], "wholeE": chosen["wholeObjectives"][1], "wholeW": chosen["wholeObjectives"][2],
                        "source": metrics["source"]})
    fields = ["requests", "tightRequests", "tightRequestsMissingFactory", "feasibleRequests",
        "weightedImprovementAtLeast001", "capturedRequests", "sampleCoverage", "genuineComplementaritySamples",
        "feasibilityCompletionSamples", "multipleSearchProducerSamples"]
    per_instance = aggregate(tables["pool-run-metrics"], ("instance", "variant"), fields)
    tables["pool-instance-metrics"] = per_instance
    tables["pool-summary"] = aggregate(per_instance, ("variant",), fields)
    for row in tables["pool-instance-metrics"]:
        row["sourceTable"] = "pool-run-metrics.csv; matching instance/variant; seeds averaged"
    for row in tables["pool-summary"]:
        row["sourceTable"] = "pool-instance-metrics.csv; matching variant; instances equally"
    return tables
