"""Reconstruct every pool/choice/acceptance; no oracle fed to search."""
from collections import Counter
from dataclasses import asdict
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.validation import validate_schedule
from research.fatigue_mechanism.model import Genome
from research.fatigue_mechanism.statistics import select_minima
from .teachers import restore_bank, bank_genomes
from .candidates import make_pool
from .protocol import PROTOCOL


def check(instance, params, initial, weights, result, rows, epochs, protocol=PROTOCOL):
    bank = restore_bank(result["teacher_bank"])
    regenerated = bank_genomes(instance, initial, result["seeds"]["bank"], result["regime"])
    assert tuple(t.genome for t in bank) == regenerated
    effective = np.asarray(weights)/result["initial_objectives"]
    for teacher in bank:
        assert teacher.value == float(np.asarray(teacher.objectives) @ effective)
    teachers = tuple(sorted(bank, key=lambda t: (t.value, t.bank_index))[:2])
    assert result["teacher_indices"] == [t.bank_index for t in teachers]
    genome, version, previous = initial, 0, float(np.asarray(result["initial_objectives"]) @ effective)
    uses, on_time, epoch_by_id, partials = Counter(), Counter(), {e["epoch"]: e for e in epochs}, 0
    for step, row in enumerate(rows):
        assert row["step"] == step and row["parent_version"] == version
        pool, metadata = make_pool(instance, genome, teachers, row["pool_seed"], result["block_size"], result["regime"])
        assert metadata == row["pool_metadata"]
        selected = pool[row["chosen_index"]]
        assert asdict(selected.genome) == row["chosen_genome"]
        support = list(range(len(pool))) if row["scores"] is None else select_minima(row["scores"]).tolist()
        assert row["score_support"] == support and row["chosen_index"] in support
        if result["method"] == "direct":
            own = {t.bank_index: t.value for t in teachers}
            np.testing.assert_array_equal(row["scores"], [min((own[i] for i, _ in c.origins), default=0.) for c in pool])
        after = float(np.asarray(row["child_objectives"]) @ effective)
        assert after == row["child_value"] and previous == row["before_value"]
        assert row["accepted"] == bool(row["on_time"] and previous-after > 1e-10)
        assert row["on_time"] == (result["deadline_ns"] is None or row["evaluation_completed_ns"] <= result["deadline_ns"])
        if row["cache_epoch"] is not None:
            eid = row["cache_epoch"]
            assert epoch_by_id[eid]["version"] == version
            uses[eid] += 1
            on_time[eid] += int(row["on_time"])
        if row["accepted"]:
            genome, previous, version = selected.genome, after, version+1
        partials += len(pool) if result["method"] in ("time", "fatigue") else 0
    for e in epochs:
        assert e["uses"] == uses[e["epoch"]] and e["on_time_uses"] == on_time[e["epoch"]]
        assert e["closed_reason"] in ("accepted", "terminal_right_censored")
        if "incremental_work" in e:
            w = e["incremental_work"]
            assert w["equivalent_full_ops"] == w["candidate_evaluations"]*instance.jobs
            assert w["equivalent_full_ops"] == w["recomputed_ops"]+w["reused_prefix_ops"]+w["unchanged_factory_ops"]
    assert asdict(genome) == result["final_genome"] and version == result["accepted"]
    assert result["full_decodes"] == 9+len(rows) and result["teacher_full_decodes"] == 8
    assert result["partial_calls"] == partials and result["bookkeeping_ns"] >= 0
    if result["mode"] != "time":
        assert len(rows) == (1 if result["mode"] == "snapshot" else protocol["decisions"])
    else:
        assert result["deadline_ns"] == int(protocol["time_budget_seconds"]*1e9)
        assert result["elapsed_ns"] >= result["deadline_ns"]
    final = decode(instance, Genome(**result["final_genome"]), params)
    np.testing.assert_array_equal(final.objectives, result["final_objectives"])
    np.testing.assert_allclose(result["gain"], float(np.asarray(result["initial_objectives"]) @ effective)-previous, atol=1e-14)
    return {"final_schedule": validate_schedule(instance, params, final), "regenerated_pools": len(rows)}
