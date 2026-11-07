"""Reuse the v3 local chain; change only its score engine and record work."""
from collections import Counter
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.model import Genome
from research.fatigue_mechanism.validation import validate_schedule
from research.fatigue_reuse.chain import run as run_chain
from research.fatigue_reuse.audit import audit_chain
from . import scorer
from .protocol import PROTOCOL


def run_one(instance, params, initial, weights, identity, pool_seed, choice_seed, records, counts, position):
    method = identity["method"]
    selector = method.removesuffix("_full")
    engine = None if method.endswith("_full") or method == "random" else scorer
    records.emit("events", {**identity, "event": "starting", "method_position": position})
    result, rows, epochs = run_chain(instance, params, initial, weights, selector, identity["mode"], PROTOCOL,
                                     pool_seed, choice_seed, score_engine=engine)
    result.update({**identity, "selector": selector, "method_position": position,
                   "kernel": "full" if method.endswith("_full") else "incremental" if selector.startswith("cut_") else selector})
    check = audit_chain(instance, initial, result, rows, epochs, PROTOCOL)
    work = Counter()
    for epoch in epochs:
        if "incremental_work" in epoch:
            w = epoch["incremental_work"]
            assert w["candidate_evaluations"] == PROTOCOL["candidate_count"] * epoch["uses"]
            assert w["equivalent_full_ops"] == instance.jobs * w["candidate_evaluations"]
            assert w["equivalent_full_ops"] == w["recomputed_ops"] + w["reused_prefix_ops"] + w["unchanged_factory_ops"]
            work.update(w)
    result["incremental_work"] = dict(work)
    final = decode(instance, Genome(**result["final_genome"]), params)
    np.testing.assert_array_equal(final.objectives, result["final_objectives"])
    result["offline_final_validation"] = validate_schedule(instance, params, final)
    counts["offline_final_QA_full"] += 1
    counts["offline_candidate_regenerations"] += check["candidate_regenerations"]
    counts["search_full"] += result["full_decodes"]
    counts["search_partial_stage0"] += result["partial_stage0_calls"]
    counts["search_cache_builds"] += result["cache_builds"]
    counts["incremental_exact_ops"] += work["recomputed_ops"]
    if method.endswith("_full"):
        counts["reference_exact_ops"] += result["partial_stage0_calls"] * instance.jobs
    records.emit("chains", result)
    for row in rows:
        records.emit("steps", {**identity, **row})
    for epoch in epochs:
        records.emit("epochs", {**identity, **epoch})
    records.emit("events", {**identity, "event": "finished"})
    records.flush()
    return result, rows


def compare_implementations(incremental, reference):
    a, a_rows = incremental
    b, b_rows = reference
    assert a["final_genome"] == b["final_genome"]
    np.testing.assert_array_equal(a["final_objectives"], b["final_objectives"])
    assert len(a_rows) == len(b_rows)
    for x, y in zip(a_rows, b_rows):
        assert x["chosen_genome"] == y["chosen_genome"] and x["accepted"] == y["accepted"]
        np.testing.assert_array_equal(x["scores"], y["scores"])
    return {"selector": a["selector"], "same_scores_and_trajectory": True,
            "incremental_elapsed_ns": a["elapsed_ns"], "full_elapsed_ns": b["elapsed_ns"],
            "incremental_stage0_ns": a["stage0_ns"], "full_stage0_ns": b["stage0_ns"],
            "incremental_cache_ns": a["phases_ns"].get("cache_build", 0),
            "full_cache_ns": b["phases_ns"].get("cache_build", 0),
            "work": a["incremental_work"], "gain": a["gain"]}


def run_block(instance, params, initial, identity, pool_seed, choice_seed, block, records, counts):
    summaries = []
    for ti, (target, weights) in enumerate(PROTOCOL["targets"].items()):
        primary = target == "TEC" and identity["profile"] == "strong_fast_recovery"
        modes = ("steps", "time") if block % 2 == 0 else ("time", "steps")
        for mi, mode in enumerate(modes):
            repeats = range(PROTOCOL["primary_time_repeats"]) if primary and mode == "time" else range(1)
            for repeat in repeats:
                methods = list(PROTOCOL["methods"])
                if primary and repeat == 0:
                    methods += ["cut_fatigue_full", "cut_time_full"]
                rotation = (block + ti + mi + repeat) % len(methods)
                methods = methods[rotation:] + methods[:rotation]
                results = {}
                for position, method in enumerate(methods):
                    case = {**identity, "target": target, "mode": mode, "repeat": repeat, "method": method}
                    result, rows = run_one(instance, params, initial, weights, case, pool_seed, choice_seed,
                                            records, counts, position)
                    results[method] = result, rows
                    summaries.append(result)
                if primary and mode == "steps":
                    for selector in ("cut_fatigue", "cut_time"):
                        records.emit("ablation", {**identity, "target": target,
                                     **compare_implementations(results[selector], results[selector + "_full"])})
    return summaries
