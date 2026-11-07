"""Full counters and explicitly bounded composition samples, kept separate."""
from collections import Counter
from .storage import means_by

PRODUCERS = ("INITIALIZATION", "MAKESPAN", "CENTER", "ENERGY", "WORKER_COST")


def fraction(numerator, denominator):
    return numerator / denominator if denominator else None


def sample_row(row, identity, index, final_front, source):
    fragments = row["fragments"]
    producers = {fragment["producer"] for fragment in fragments}
    search_producers = producers - {"INITIALIZATION"}
    paid_sources = {fragment["paidFE"] for fragment in fragments}
    objective = tuple(row["objectives"])
    return identity | {"sampleIndex": index, "sampleWindow": "first16" if index < 16 else "last16",
        "generation": row["generation"], "family": row["family"], "paidFE": row["paidFE"],
        "distinctProducers": len(producers), "multipleProducers": len(producers) > 1,
        "multipleSearchProducers": len(search_producers) > 1, "distinctPaidEvaluations": len(paid_sources),
        "multiplePaidEvaluations": len(paid_sources) > 1,
        "producerSignature": "+".join(sorted(producers)),
        "stageSignature": "+".join(sorted({fragment["stage"] for fragment in fragments})),
        "externalAdmission": row["externalArchiveAdmission"],
        "objectivePresentAtCutoff": objective in final_front,
        "cmax": objective[0], "tec": objective[1], "twc": objective[2], "source": source}


def run_metrics(summary, header, samples, identity, source):
    co = summary["cooperation"]
    total = identity | {"source": source, "paidAssemblies": header["paidAssemblies"],
        "validPaidAssemblies": header["deadlineValidPaidAssemblies"],
        "selectedFragments": header["selectedFragments"],
        "admissions": header["deadlineValidArchiveAdmissions"],
        "admissionRate": fraction(header["deadlineValidArchiveAdmissions"], header["deadlineValidPaidAssemblies"]),
        "sameGenerationFraction": fraction(header["sameGenerationFragments"], header["selectedFragments"]),
        "lateFreshFraction": fraction(header["sameGenerationLateGroupFragments"], header["selectedFragments"]),
        "meanAgeFE": header["fragmentAgeFEMean"], "completeGenerations": summary["search"].get("generations.completed", 0),
        "poolAccepted": co.get("poolAccepted", 0), "poolRejected": co.get("poolRejected", 0),
        "poolTruncated": co.get("poolTruncated", 0), "assemblyRequests": co.get("assemblyRequests", 0),
        "infeasibleCap": co.get("infeasibleCap", 0), "cooperationSeconds": co["cooperationSeconds"],
        "successfulFE": summary["successful"], "attemptedFE": summary["attempted"],
        "sampleAssemblies": len(samples), "sampleCoverage": fraction(len(samples), header["deadlineValidPaidAssemblies"])}
    for producer in PRODUCERS:
        total["producerCount." + producer] = header["fromProducer"].get(producer, 0)
        total["producerFraction." + producer] = fraction(header["fromProducer"].get(producer, 0), header["selectedFragments"])
    for field in ("multipleProducers", "multipleSearchProducers", "multiplePaidEvaluations", "externalAdmission", "objectivePresentAtCutoff"):
        total["sampleFraction." + field] = fraction(sum(row[field] for row in samples), len(samples))
    return total


def review_compositions(project, sources):
    root = project / "runs" / "center-last-20261102-211306-648128"
    totals, generations, samples, fragments, sample_counts = [], [], [], [], []
    for path in sorted((root / "trials" / "order").glob("*/*/SHARE_*/composition-trace.jsonl")):
        folder = path.parent
        identity = {"campaign": root.name, "instance": path.parents[2].name,
                    "seed": int(path.parents[1].name), "variant": folder.name}
        summary_path = folder / "summary.json"
        summary = sources.json(summary_path)
        trace = sources.lines(path)
        header = trace[0]
        if header != dict(summary["cooperation"]["compositionTiming"], type="composition-summary"):
            raise ValueError("Trace-summary mismatch")
        if len(trace) > 33 or sum(header["fromProducer"].values()) != header["selectedFragments"]:
            raise ValueError("Invalid bounded/full counters")
        n_factories = int(identity["instance"].split("_")[2])
        if header["selectedFragments"] != header["deadlineValidPaidAssemblies"] * n_factories:
            raise ValueError("Wrong instance factories or fragment accounting")
        checkpoints = sources.lines(folder / "anytime.jsonl")
        final = [row for row in checkpoints if row["checkpointKind"] == "TIME" and row["checkpoint"] == summary["timeLimitSeconds"]]
        if len(final) != 1:
            raise ValueError("Missing exact cutoff front")
        final_front = {tuple(obj) for obj in final[0]["front"]}
        selected_samples = []
        for index, row in enumerate(trace[1:]):
            if not row["deadlineValid"] or row["paidFE"] != row["proposalFE"] + 1:
                raise ValueError("Unpaid/late sample")
            sample = sample_row(row, identity, index, final_front, str(path))
            selected_samples.append(sample); samples.append(sample)
            for fragment in row["fragments"]:
                fragments.append(identity | {"sampleIndex": index, "assemblyPaidFE": row["paidFE"],
                    "family": row["family"], **fragment, "source": str(path)})
        total = run_metrics(summary, header, selected_samples, identity, str(summary_path))
        for complete, label in ((True, "full"), (False, "partial")):
            group = [row for row in header["perGeneration"] if (row["generation"] <= total["completeGenerations"]) == complete]
            for field in ("eligibleCenterOpportunities", "proposedAssemblies", "paidAssemblies", "validPaidAssemblies"):
                total[label + "." + field] = sum(row[field] for row in group)
            total[label + ".generations"] = len(group)
            total[label + ".meanPaidPerGeneration"] = fraction(total[label + ".paidAssemblies"], len(group))
        for row in header["perGeneration"]:
            generations.append(identity | row | {"completeGeneration": row["generation"] <= total["completeGenerations"], "source": str(path)})
        if total["full.paidAssemblies"] + total["partial.paidAssemblies"] != total["paidAssemblies"]:
            raise ValueError("Full/partial accounting mismatch")
        for dimension in ("producerSignature", "stageSignature", "family", "sampleWindow"):
            for value, count in Counter(str(row[dimension]) for row in selected_samples).items():
                sample_counts.append(identity | {"dimension": dimension, "value": value, "sampleCount": count,
                    "sampleFraction": count / len(selected_samples), "source": str(path)})
        totals.append(total)
    if len(totals) != 60:
        raise ValueError("Expected sixty sharing runs")
    nonmetrics = {"campaign", "instance", "seed", "variant", "source"}
    fields = [key for key in totals[0] if key not in nonmetrics]
    instances = means_by(totals, ["instance", "variant"], fields)
    overall = means_by(instances, ["variant"], fields)
    for row in instances:
        row["sourceTable"] = "composition-runs.csv (same instance/variant; five seeds)"
    for row in overall:
        row["sourceTable"] = "composition-instances.csv (same variant; six instances equally)"
    return {"composition-runs": totals, "composition-instances": instances, "composition-summary": overall,
            "composition-generations": generations, "sample-assemblies": samples, "sample-fragments": fragments,
            "sample-strata": sample_counts}
