"""Offline H1: distinguish elite loss before G/L from loss inside selection."""
import math
from collections import defaultdict
from statistics import mean

import numpy as np

from research.dynamic_benchmark.metrics import hypervolume

VECTORS = ("JS", "FA", "MA", "WA")


def points(values):
    """Validate three minimization objectives, allowing an empty candidate pool."""
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return np.empty((0, 3), dtype=float)
    if array.ndim != 2 or array.shape[1] != 3 or not np.isfinite(array).all():
        raise ValueError("Expected finite objective triples")
    return array


def objective(record):
    values = record.get("objectives", record.get("objs"))
    return points([values])[0]


def encoding(record):
    source = record.get("encoding", record)
    values = []
    for key in VECTORS:
        vector = source.get(key)
        if not isinstance(vector, list) or not vector:
            raise ValueError("Missing exact four-vector encoding: " + key)
        if any(isinstance(value, bool) or not isinstance(value, int) for value in vector):
            raise ValueError("Noninteger encoding: " + key)
        values.append(tuple(vector))
    if len({len(value) for value in values}) != 1:
        raise ValueError("Chapter4 encoding vectors have different lengths")
    return tuple(values)


def normalize(values, normalization):
    lower = np.asarray(normalization["lower"], dtype=float)
    scale = np.asarray(normalization["scale"], dtype=float)
    if lower.shape != (3,) or scale.shape != (3,) or not np.isfinite(lower).all():
        raise ValueError("Invalid frozen normalization")
    if not np.isfinite(scale).all() or np.any(scale <= 0):
        raise ValueError("Normalization scale must be finite and positive")
    return (points(values) - lower) / scale


def nondominated_mask(values):
    """Preserve duplicate-objective records for genotype survival denominators."""
    values = points(values)
    if not len(values):
        return np.zeros(0, dtype=bool)
    weak = np.all(values[:, None, :] <= values[None, :, :], axis=2)
    strict = np.any(values[:, None, :] < values[None, :, :], axis=2)
    return ~np.any(weak & strict, axis=0)


def covered_by(targets, candidates, *, strict=False):
    targets, candidates = points(targets), points(candidates)
    if not len(candidates):
        return np.zeros(len(targets), dtype=bool)
    relation = np.all(candidates[:, None, :] <= targets[None, :, :], axis=2)
    if strict:
        relation &= np.any(candidates[:, None, :] < targets[None, :, :], axis=2)
    return np.any(relation, axis=0)


def _fraction(mask):
    return float(np.mean(mask)) if len(mask) else None


def _positive_gap(high, low):
    if high < low - 1e-10:
        raise ValueError("HV union monotonicity failed")
    return max(0., high - low)


def generation_metrics(record, normalization, reference=(1.5, 1.5, 1.5)):
    populations = {key: record[key] for key in ("parents", "global", "local", "selected")}
    if not populations["parents"] or not populations["selected"]:
        raise ValueError("A captured generation requires parents and selected records")
    raw, genes = {}, {}
    for key, population in populations.items():
        raw[key] = points([objective(item) for item in population])
        genes[key] = {encoding(item) for item in population}
    p, g, l, s = (normalize(raw[key], normalization) for key in populations)
    gl, pgl = np.concatenate((g, l)), np.concatenate((p, g, l))
    pnd = nondominated_mask(p)
    elite = p[pnd]
    elite_genes = [encoding(item) for item, keep in zip(populations["parents"], pnd) if keep]
    glnd = gl[nondominated_mask(gl)]
    hv = {key: hypervolume(value, reference)
          for key, value in (("P", p), ("G", g), ("L", l), ("S", s), ("GL", gl), ("PGL", pgl))}
    parent_genes = [encoding(item) for item in populations["parents"]]
    result = {"generation": record["generation"], "elapsedSeconds": record["elapsedSeconds"],
              "successfulFE": record["successfulFE"], "deadlineValid": record["deadlineValid"],
              "parentRecords": len(p), "parentNDRecords": len(elite), "globalRecords": len(g),
              "localRecords": len(l), "selectedRecords": len(s), "GLNDRecords": len(glnd),
              **{"hv" + key: value for key, value in hv.items()},
              "parentNDUncoveredByGLFraction": _fraction(~covered_by(elite, gl)),
              "parentNDStrictlyDominatedByGLFraction": _fraction(covered_by(elite, gl, strict=True)),
              "parentNDCoveredByGLFraction": _fraction(covered_by(elite, gl)),
              "GLNDCoveredBySelectedFraction": _fraction(covered_by(glnd, s)),
              "offlineOracleParentGainHV": _positive_gap(hv["PGL"], hv["GL"]),
              "offlineOracleParentGainPercentOfGL":
                  100 * (hv["PGL"] - hv["GL"]) / hv["GL"] if hv["GL"] > 1e-12 else None,
              "GLHVMinusSelectedHV": hv["GL"] - hv["S"]}
    for suffix, pool in (("GL", genes["global"] | genes["local"]), ("Selected", genes["selected"])):
        result["parentGenotypeSurvival" + suffix + "Fraction"] = _fraction([gene in pool for gene in parent_genes])
        result["parentNDGenotypeSurvival" + suffix + "Fraction"] = _fraction([gene in pool for gene in elite_genes])
    if "parentSelected" in record:
        selected = record["parentSelected"]
        candidates = normalize([objective(item) for item in selected], normalization)
        candidate_genes = {encoding(item) for item in selected}
        result.update({"hvParentSelected": hypervolume(candidates, reference),
                       "parentNDGenotypeSurvivalParentSelectedFraction":
                           _fraction([gene in candidate_genes for gene in elite_genes]),
                       "parentNDCoveredByParentSelectedFraction": _fraction(covered_by(elite, candidates))})
    return result


def validate_generations(records, seconds):
    generations = [record for record in records if record.get("type") == "generation"
                   and record.get("complete", True) is not False]
    numbers, last_time, last_fe = set(), -1., -1
    for record in generations:
        number, elapsed, fe = record["generation"], record["elapsedSeconds"], record["successfulFE"]
        if not isinstance(number, int) or number in numbers or number < 0:
            raise ValueError("Duplicated or invalid captured generation")
        if not math.isfinite(elapsed) or elapsed < last_time or fe < last_fe:
            raise ValueError("Captured generation chronology or FE regressed")
        if not isinstance(record["deadlineValid"], bool):
            raise ValueError("Missing explicit deadline validity")
        if record["deadlineValid"] and elapsed > seconds + 1e-9:
            raise ValueError("Future generation was marked deadline-valid")
        for key in ("extraFE", "additionalFE", "observerExtraFE"):
            if record.get(key, 0) != 0:
                raise ValueError("Mechanism capture added evaluation calls")
        numbers.add(number)
        last_time, last_fe = elapsed, fe
    return [record for record in generations if record["deadlineValid"]]


def batch_metrics(record, normalization, reference=(1.5, 1.5, 1.5)):
    """Global paid-batch progress uses one frozen P per captured generation."""
    parents = normalize([objective(item) for item in record["parents"]], normalization)
    base = hypervolume(parents, reference)
    rows, seen = [], set()
    for batch in record.get("batches", []):
        identity = batch["direction"], batch["step"]
        if identity in seen:
            raise ValueError("Duplicate direction/step within one generation")
        candidates = normalize(batch["objectives"], normalization)
        rows.append({"generation": record["generation"], "direction": batch["direction"],
                     "step": batch["step"], "elapsedSeconds": batch["elapsedSeconds"],
                     "successfulFE": batch["successfulFE"], "batchSize": len(candidates),
                     "batchHV": hypervolume(candidates, reference), "parentReferenceHV": base,
                     "batchDeltaHVAgainstFixedParents": _positive_gap(
                         hypervolume(np.concatenate((parents, candidates)), reference), base)})
        seen.add(identity)
    return rows


def retention_gate(rows, instances, variants=("SO", "SHARE")):
    """Predeclared branch: six instance means, with seeds averaged within run."""
    instances = [item["stem"] if isinstance(item, dict) else item for item in instances]
    result = {"thresholdMeanPercent": 1., "thresholdPositiveInstances": 4,
              "aggregation": "captured generations within run, seeds within instance, six instances equally",
              "scope": "Oracle diagnostic determines a bounded branch; does not estimate closed-loop gain",
              "variants": {}}
    for variant in variants:
        run_groups = defaultdict(list)
        for row in rows:
            if row["variant"] == variant:
                run_groups[row["instance"], row["seed"]].append(row["offlineOracleParentGainPercentOfGL"])
        per_instance = []
        for instance in instances:
            runs = [values for (name, _), values in run_groups.items() if name == instance]
            available = bool(runs) and all(value is not None for values in runs for value in values)
            run_means = [mean(values) for values in runs] if available else []
            per_instance.append({"instance": instance, "runs": len(runs),
                                 "meanOracleParentGainPercentOfGL": mean(run_means) if run_means else None})
        resolved = len(instances) == 6 and all(row["meanOracleParentGainPercentOfGL"] is not None for row in per_instance)
        values = [row["meanOracleParentGainPercentOfGL"] for row in per_instance] if resolved else []
        average, positives = mean(values) if values else None, sum(value > 0 for value in values)
        result["variants"][variant] = {"status": "RESOLVED" if resolved else "UNRESOLVED",
                                       "instances": per_instance,
                                       "meanOracleParentGainPercentOfGL": average,
                                       "positiveInstances": positives,
                                       "triggered": resolved and average >= 1. and positives >= 4}
    resolved = all(row["status"] == "RESOLVED" for row in result["variants"].values())
    result["status"] = "RESOLVED" if resolved else "UNRESOLVED"
    result["triggered"] = any(row["triggered"] for row in result["variants"].values()) if resolved else None
    return result


def summarize(rows, keys):
    """Descriptive means for captured records; never pretend generations independent."""
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    result = []
    for identity, group in sorted(groups.items(), key=lambda item: str(item[0])):
        metrics = {key for row in group for key, value in row.items()
                   if isinstance(value, (int, float)) and not isinstance(value, bool) and key not in keys}
        record = dict(zip(keys, identity)) | {"capturedRecords": len(group)}
        for key in sorted(metrics):
            values = [row[key] for row in group if row.get(key) is not None]
            record[key + "Mean"] = mean(values) if values else None
            record[key + "Max"] = max(values) if values else None
        result.append(record)
    return result
