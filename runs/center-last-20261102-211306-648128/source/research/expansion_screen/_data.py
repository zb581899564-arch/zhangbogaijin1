"""Validate the frozen matrix before computing any performance verdict."""

import math
from collections.abc import Mapping

REFERENCES = ("1.25", "1.5", "2.0")


def layout(config, variants=None, seeds=None):
    instances = [item["stem"] for item in config["instances"]]
    variants = list(config["variants"] if variants is None else variants)
    seeds = list(config["algorithm_seeds"] if seeds is None else seeds)
    if not all(isinstance(name, str) and name for name in instances + variants):
        raise ValueError("Instance and variant labels must be nonempty strings")
    if not all(isinstance(seed, int) and not isinstance(seed, bool) for seed in seeds):
        raise ValueError("Seeds must be integers")
    if any(len(items) != len(set(items)) or not items for items in (instances, variants, seeds)):
        raise ValueError("Matrix axes must be nonempty and unique")
    return instances, variants, seeds


def nonnegative_number(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0)


def _metric_errors(record, allow_half_missing):
    errors = []
    hv = record.get("hv")
    if not isinstance(hv, Mapping) or any(not nonnegative_number(hv.get(ref)) for ref in REFERENCES):
        errors.append("hv requires finite nonnegative values at 1.25, 1.5 and 2.0")
    if not nonnegative_number(record.get("igdplus")):
        errors.append("igdplus must be finite and nonnegative")
    if not allow_half_missing and not nonnegative_number(record.get("hv_half")):
        errors.append("hv_half must be finite and nonnegative")
    fe_value = record.get("hv_fe15000")
    if fe_value is not None and not nonnegative_number(fe_value):
        errors.append("hv_fe15000 must be null or finite and nonnegative")
    return errors


def validate_records(records, config, variants=None, seeds=None, followup=False):
    """Return an index only after checking exact cells, metrics and duplicates."""
    try:
        instances, variants, seeds = layout(config, variants, seeds)
        records = list(records)
    except (KeyError, TypeError, ValueError) as error:
        return {}, {"status": "INVALID", "errors": [str(error)]}
    expected = {(instance, seed, variant)
                for instance in instances for seed in seeds for variant in variants}
    index, errors = {}, []
    configured_runs = config["followup"]["runs"] if followup else config.get("runs")
    if configured_runs != len(expected):
        errors.append({"reason": "Matrix axes disagree with configured run count",
                       "axis_product": len(expected), "configured_runs": configured_runs})
    for position, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append({"record": position, "reason": "Record is not a mapping"})
            continue
        key = (record.get("instance"), record.get("seed"), record.get("variant"))
        if not (isinstance(key[0], str) and isinstance(key[2], str)
                and isinstance(key[1], int) and not isinstance(key[1], bool)):
            errors.append({"record": position, "reason": "Malformed matrix key"})
            continue
        if key not in expected:
            errors.append({"record": position, "reason": "Unexpected matrix cell", "key": list(key)})
            continue
        if key in index:
            errors.append({"record": position, "reason": "Duplicate matrix cell", "key": list(key)})
            continue
        issues = _metric_errors(record, allow_half_missing=followup)
        if issues:
            errors.append({"record": position, "key": list(key), "reasons": issues})
        index[key] = record
    missing = sorted(expected - index.keys())
    status = "INVALID" if errors else "INSUFFICIENT_EVIDENCE" if missing else "COMPLETE"
    return index, {"status": status, "expected_runs": len(expected), "received_runs": len(records),
                   "unique_expected_cells": len(index), "errors": errors,
                   "missing_cells": [list(key) for key in missing]}
