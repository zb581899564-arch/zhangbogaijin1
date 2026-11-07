"""Complete final-front and registered-checkpoint tables on the common reference."""
import math

import numpy as np

from research.dynamic_benchmark.metrics import nondominated
from research.pilot_evaluation import (ObjectiveScale, evaluate_front, hypervolume,
                                      igd, igd_plus, shared_final_reference)
from report_io import identity, require_linux


def contexts(runs, plan):
    require_linux()
    result = {}
    for spec in plan["instances"]:
        selected = [run for run in runs if run["instance"] == spec["stem"]]
        final_fronts = {f"{run['arm']}/{run['seed']}": run["front"] for run in selected}
        if len(final_fronts) != len(plan["arms"]) * len(plan["seeds"]):
            raise ValueError("Reference must contain all registered arm/seed final fronts")
        normalization = spec["normalization"]
        lower = np.asarray(normalization["lower"], dtype=float)
        scale = ObjectiveScale(tuple(lower), tuple(lower + np.asarray(normalization["scale"])))
        reference = shared_final_reference(final_fronts)
        result[spec["stem"]] = {"scale": scale, "reference": reference,
                                "normalized_reference": scale.normalize(reference.objectives),
                                "hv_reference": normalization["reference"]}
    return result


def reference_rows(context):
    return {instance: {"sources": item["reference"].source_ids,
                       "raw_objectives": item["reference"].objectives,
                       "normalized_objectives": item["normalized_reference"].tolist(),
                       "lower": item["scale"].lower, "upper": item["scale"].upper,
                       "hv_reference": item["hv_reference"], "offline_only": True}
            for instance, item in context.items()}


def front_metrics(front, context):
    """Use the non-dominated objective set, including for working populations."""
    require_linux()
    normalized = nondominated(context["scale"].normalize(front))
    if not len(normalized):
        return {"HV": 0.0, "IGDplus": None, "IGD": None, "ndPointCount": 0, "metricStatus": "EMPTY_FRONT"}
    return {"HV": hypervolume(normalized, context["hv_reference"]),
            "IGDplus": igd_plus(normalized, context["normalized_reference"]),
            "IGD": igd(normalized, context["normalized_reference"]),
            "ndPointCount": len(normalized), "metricStatus": "AVAILABLE"}


def final_tables(runs, context, plan):
    require_linux()
    full, flat, fronts = [], [], []
    for run in runs:
        item = context[run["instance"]]
        metrics = evaluate_front(run["front"], item["reference"], item["scale"], item["hv_reference"])
        normalized = item["scale"].normalize(run["front"])
        receipt = run["receipt"]
        sensitivity = {str(reference): hypervolume(normalized, [reference] * 3) for reference in plan["hvReferences"]}
        trace_seconds = sum(receipt["trace"]["observationNanosByPhase"].values()) / 1e9
        net = receipt["searchSeconds"] - trace_seconds - receipt["observationCheckpointSeconds"]
        row = {**identity(run), **{key: metrics[key] for key in ("HV", "IGDplus", "IGD")},
               "frontPoints": len(normalized), "attempted": receipt["attempted"], "successful": receipt["successful"],
               "failed": receipt["failed"], "searchSecondsInclusive": receipt["searchSeconds"],
               "traceObservationSeconds": trace_seconds,
               "checkpointObservationSeconds": receipt["observationCheckpointSeconds"],
               "netObservationSubtractionReferenceSeconds": net if net >= 0 else None,
               "netTimeStatus": "ARITHMETIC_REFERENCE_NOT_MEASURED_RUNTIME" if net >= 0 else "NEGATIVE_SUBTRACTION_UNKNOWN",
               "paidSHA256": receipt["paidSHA256"],
               "cooperationSubsystemSecondsIncludesCommonLifecycle": receipt["search"].get("cooperation", {}).get("cooperationSeconds"),
               "outsidePrimaryHVBox": int(np.any(normalized >= item["hv_reference"], axis=1).sum()),
               **{f"HV_ref_{key}": value for key, value in sensitivity.items()}}
        if not all(math.isfinite(row[key]) for key in ("HV", "IGDplus", "IGD")):
            raise ValueError("Nonfinite final metric")
        flat.append({**row, **{f"minNormalized_{name}": value["normalized_minimum"] for name, value in metrics["extremes"].items()}})
        full.append({**row, "extremes": metrics["extremes"], "hvSensitivity": sensitivity,
                     "rawFront": run["front"], "normalizedFront": normalized.tolist()})
        for ordinal, (raw, norm) in enumerate(zip(run["front"], normalized)):
            fronts.append({**identity(run), "pointIndex": ordinal,
                           **{name: float(raw[i]) for i, name in enumerate(("Cmax", "TEC", "TWC"))},
                           **{f"normalized_{name}": float(norm[i]) for i, name in enumerate(("Cmax", "TEC", "TWC"))}})
    return full, flat, fronts


def convergence_rows(runs, context, plan):
    require_linux()
    result = []
    for run in runs:
        for checkpoint, row in sorted(run["checkpoints"].items()):
            common = {**identity(run), "checkpoint": checkpoint, "registeredCheckpoint": checkpoint in plan["checkpoints"],
                      "reached": row["reached"], "fe": row.get("fe"), "elapsedSeconds": row.get("elapsedSeconds")}
            if row["reached"]:
                result.append({**common, **front_metrics(row["front"], context[run["instance"]])})
            else:
                result.append({**common, "HV": None, "IGDplus": None, "IGD": None,
                               "ndPointCount": None, "metricStatus": "NOT_REACHED"})
    return result
