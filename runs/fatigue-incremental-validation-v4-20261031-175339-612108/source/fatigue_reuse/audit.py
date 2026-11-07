"""Offline audits never feed candidate choice or cache state."""
from dataclasses import asdict
import numpy as np
from research.fatigue_mechanism.model import Genome
from research.fatigue_mechanism.statistics import select_minima
from .neighbors import local_pool


def audit_chain(instance, initial, summary, rows, epochs, protocol):
    genome, version = initial, 0
    scales = np.asarray(summary["initial_objectives"])
    weights = np.asarray(protocol["targets"][summary["target"]])
    previous = summary["initial_value"]
    by_epoch = {e["epoch"]: e for e in epochs}
    epoch_counts, on_time_counts = {}, {}
    for row in rows:
        assert row["parent_version"] == version
        np.testing.assert_allclose(row["before_value"], previous, atol=1e-12)
        pool = local_pool(instance, genome, row["pool_seed"], protocol["candidate_count"])
        selected = pool[row["chosen_index"]]
        assert asdict(selected.genome) == row["chosen_genome"]
        support = list(range(len(pool))) if row["scores"] is None else select_minima(row["scores"]).tolist()
        assert row["score_support"] == support and row["chosen_index"] in support
        child_value = float(np.asarray(row["child_objectives"]) @ (weights / scales))
        np.testing.assert_allclose(child_value, row["child_value"], atol=1e-12)
        assert row["accepted"] == bool(row["on_time"] and previous - child_value > 1e-10)
        epoch_id = row["cache_epoch"]
        if epoch_id is not None:
            assert by_epoch[epoch_id]["version"] == version
            epoch_counts[epoch_id] = epoch_counts.get(epoch_id, 0) + 1
            on_time_counts[epoch_id] = on_time_counts.get(epoch_id, 0) + int(row["on_time"])
        if row["accepted"]:
            genome, version, previous = selected.genome, version + 1, child_value
    assert asdict(genome) == summary["final_genome"]
    assert summary["full_decodes"] == len(rows) + 1
    assert summary["accepted"] == version
    assert summary["cache_builds"] == len(epochs)
    for epoch in epochs:
        assert epoch["uses"] == epoch_counts[epoch["epoch"]]
        assert epoch["on_time_uses"] == on_time_counts[epoch["epoch"]]
        assert epoch["closed_reason"] in ("accepted", "forced_refresh", "terminal_right_censored")
    if summary["mode"] == "steps":
        assert len(rows) == protocol["decisions"]
    else:
        deadline = summary["deadline_ns"]
        assert all(r["on_time"] == (r["evaluation_completed_ns"] <= deadline) for r in rows)
        assert all(not r["accepted"] for r in rows if not r["on_time"])
    np.testing.assert_allclose(summary["gain"], summary["initial_value"] - previous, atol=1e-12)
    assert summary["bookkeeping_ns"] >= 0
    expected_partials = len(rows) * protocol["candidate_count"] if summary["selector"].startswith("cut_") else 0
    assert summary["partial_stage0_calls"] == expected_partials
    return {"candidate_regenerations": len(rows), "rows_verified": len(rows), "epochs_verified": len(epochs)}


def compare_ablation(cached, fresh):
    a, a_rows = cached
    b, b_rows = fresh
    assert a["final_genome"] == b["final_genome"]
    np.testing.assert_array_equal(a["final_objectives"], b["final_objectives"])
    for x, y in zip(a_rows, b_rows):
        assert x["chosen_genome"] == y["chosen_genome"] and x["accepted"] == y["accepted"]
        np.testing.assert_array_equal(x["scores"], y["scores"])
    return {"same_complete_trajectory": True, "cached_elapsed_ns": a["elapsed_ns"],
            "fresh_elapsed_ns": b["elapsed_ns"], "cached_builds": a["cache_builds"],
            "fresh_builds": b["cache_builds"], "cached_q": a["actual_q"],
            "gain": a["gain"], "cached_build_ns": a["phases_ns"].get("cache_build", 0),
            "fresh_build_ns": b["phases_ns"].get("cache_build", 0)}
