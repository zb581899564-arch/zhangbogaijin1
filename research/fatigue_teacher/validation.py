"""Old-seed numerical/legality gate for new teacher-derived block edits."""
from collections import Counter
from time import perf_counter_ns
import shutil
import traceback
import numpy as np
from research.fatigue_mechanism.decoder import decode, _validate_genome
from research.fatigue_mechanism.instances import load_instance, parent_genome, fatigue_profile
from research.fatigue_mechanism.validation import validate_schedule
from research.fatigue_reuse.stage0 import exact_stage0
from research.fatigue_reuse import scorer as full_scorer
from research.fatigue_incremental.prefix import build_prefix, incremental_stage0
from .teachers import build_bank
from .candidates import make_pool, physical_signature
from . import scoring
from .records import Records, save
from .artifacts import create
from .protocol import PROTOCOL, all_instances


def verify_pool(instance, params, receiver, seed, regime, size):
    parent = decode(instance, receiver, params)
    validate_schedule(instance, params, parent)
    before = parent.C.copy()
    weights, scales = [0., 1., 0.], parent.objectives
    teachers, _ = build_bank(instance, params, receiver, np.asarray(weights)/scales, 711000+seed, regime)
    pool, metadata = make_pool(instance, receiver, teachers, 911000+seed, size, regime)
    assert len({physical_signature(instance, c.genome) for c in pool}) == len(pool)
    prefix = build_prefix(instance, receiver, parent)
    for candidate in pool:
        _validate_genome(instance, candidate.genome)
        child = decode(instance, candidate.genome, params)
        validate_schedule(instance, params, child)
        full = exact_stage0(instance, candidate.genome, params.arrays(instance))
        np.testing.assert_array_equal(full.C, child.C[:instance.jobs])
        np.testing.assert_array_equal(full.v, child.v[:instance.jobs])
        attrs = candidate.genome.by_job()
        order = [j for f in range(instance.factories) for j in candidate.genome.js if attrs[j][0] == f]
        np.testing.assert_array_equal(full.direct, [0., sum(child.operations[j].energy for j in order),
                                                    sum(child.operations[j].labor for j in order)])
        if regime == "fixed_FA":
            incremental, work = incremental_stage0(instance, candidate.genome, params.arrays(instance), prefix)
            for name in ("C", "v", "direct"):
                np.testing.assert_array_equal(getattr(incremental, name), getattr(full, name))
            assert sum(work[k] for k in ("recomputed_ops", "reused_prefix_ops", "unchanged_factory_ops")) == instance.jobs
    for method in ("cheap", "time", "fatigue"):
        cache = scoring.build(instance, params, receiver, parent, method, regime, weights, scales, 0)
        predicted, _, _ = scoring.scores(instance, params, receiver, parent, pool, teachers, cache, method, regime, 0)
        assert np.isfinite(predicted).all()
        if regime == "fixed_FA" and method != "cheap":
            reference = full_scorer.build(instance, params, receiver, parent, "cut_"+method, weights, scales, 0)
            expected, _, _ = full_scorer.scores(instance, params, receiver, parent, pool, reference, 0)
            np.testing.assert_array_equal(predicted, expected)
    np.testing.assert_array_equal(parent.C, before)
    return {"candidates": len(pool), "metadata": metadata, "full_schedules": 1+len(pool)}


def run(project):
    output, counts, started = create(project, "validation"), Counter(), perf_counter_ns()
    records, active = Records(output), None
    print(f"VALIDATION_DIRECTORY {output}", flush=True)
    try:
        for i, filename in enumerate(all_instances(project)):
            instance = load_instance(project/"data/chapter4"/filename, PROTOCOL["setup_seed_base"]+i)
            params, _ = fatigue_profile(instance, PROTOCOL["profile"], PROTOCOL["profile_seed_base"]+i)
            shutil.copyfile(instance.source, output/filename)
            for seed in PROTOCOL["validation_seeds"]:
                receiver = parent_genome(instance, seed)
                for regime in PROTOCOL["regimes"]:
                    for size in PROTOCOL["block_sizes"]:
                        active = {"instance": filename, "seed": seed, "regime": regime, "block_size": size}
                        result = verify_pool(instance, params, receiver, seed+1009*i, regime, size)
                        records.emit("validation", {**active, **result})
                        counts.update({"cases": 1, "candidates": result["candidates"], "full_schedules": result["full_schedules"]})
            records.flush()
            print(f"VALIDATED {i+1}/36 cases={counts['cases']}", flush=True)
        assert counts["cases"] == PROTOCOL["validation_cases"]
        save(output/"completion.json", {"status": "passed", **dict(counts),
             "C_v_direct_and_fixed_FA_scores_bitwise_equal": True, "wall_ns": perf_counter_ns()-started})
    except BaseException:
        save(output/"failure.json", {"active": active, "counts": dict(counts), "traceback": traceback.format_exc()})
        raise
    finally:
        records.close()
    return output
