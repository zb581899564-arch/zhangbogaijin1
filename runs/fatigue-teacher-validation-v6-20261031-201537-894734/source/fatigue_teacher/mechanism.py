"""Shared-pool truth is evaluated only after every selector has committed."""
from dataclasses import asdict
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.validation import validate_schedule
from research.fatigue_mechanism.statistics import selection_metrics
from .teachers import restore_bank
from .candidates import make_pool, physical_signature
from .protocol import PROTOCOL


def evaluate(instance, params, initial, weights, runs):
    first, first_rows, _ = runs[0]
    bank = restore_bank(first["teacher_bank"])
    by_index = {t.bank_index: t for t in bank}
    teachers = tuple(by_index[i] for i in first["teacher_indices"])
    seed = first_rows[0]["pool_seed"]
    pool, metadata = make_pool(instance, initial, teachers, seed, first["block_size"], first["regime"])
    effective = np.asarray(weights)/first["initial_objectives"]
    actual, objectives = [], []
    initial_value = float(np.asarray(first["initial_objectives"]) @ effective)
    for candidate in pool:
        child = decode(instance, candidate.genome, params)
        validate_schedule(instance, params, child)
        objectives.append(child.objectives.tolist())
        actual.append(float(child.objectives @ effective)-initial_value)
    metrics = []
    for result, rows, _ in runs:
        assert result["teacher_bank"] == first["teacher_bank"]
        np.testing.assert_array_equal(result["initial_objectives"], first["initial_objectives"])
        other_pool, other_meta = make_pool(instance, initial, teachers, rows[0]["pool_seed"], result["block_size"], result["regime"])
        assert tuple(c.genome for c in other_pool) == tuple(c.genome for c in pool) and other_meta == metadata
        selected = rows[0]["chosen_index"]
        np.testing.assert_array_equal(rows[0]["child_objectives"], objectives[selected])
        values = selection_metrics(rows[0]["scores"], actual)
        support = rows[0]["score_support"]
        values["accepted_gain"] = float(np.mean([max(0., -actual[i]) if -actual[i] > 1e-10 else 0. for i in support]))
        values["mean_abs_prediction_error"] = None if result["method"] in ("direct", "random") else float(np.mean(np.abs(np.asarray(rows[0]["scores"])-actual)))
        if result["method"] == "direct":
            values["sign_accuracy"] = None  # own teacher score is not a predicted receiver delta
        metrics.append({"method": result["method"], "realized_gain": result["gain"],
                        "elapsed_ns": result["elapsed_ns"], **values})
    return {"pool_seed": seed, "pool_metadata": metadata, "candidates": [asdict(c) for c in pool],
            "true_objectives": objectives, "actual_delta": actual, "selection": metrics,
            "source_teacher_values": first["teacher_values"], "shared_pool_verified": True,
            "offline_candidate_full_calls": len(pool)}
