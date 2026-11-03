"""Broader-size correctness gate, independent of new performance seeds."""
from collections import Counter
from dataclasses import asdict
from time import perf_counter
import json
import shutil
import traceback
import numpy as np
from research.fatigue_mechanism.instances import load_instance, parent_genome, fatigue_profile
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.validation import validate_schedule
from research.fatigue_reuse.neighbors import local_pool
from research.fatigue_reuse.stage0 import exact_stage0
from research.fatigue_reuse.experiment import save
from research.fatigue_incremental.prefix import build_prefix, incremental_stage0
from .artifacts import create
from .protocol import PROTOCOL, instances


def run(project):
    output, counts, started = create(project, "validation"), Counter(), perf_counter()
    print(f"VALIDATION_DIRECTORY {output}", flush=True)
    active = None
    try:
        with (output / "parents.jsonl").open("x", encoding="utf-8") as stream:
            for i, name in enumerate(instances(project)):
                instance = load_instance(project / "data/chapter4" / name, PROTOCOL["setup_seed_base"] + i)
                shutil.copyfile(instance.source, output / name)
                for seed in PROTOCOL["validation"]["seeds"]:
                    for profile in PROTOCOL["profiles"]:
                        params, _ = fatigue_profile(instance, profile, PROTOCOL["profile_seed_base"] + i)
                        arrays, genome = params.arrays(instance), parent_genome(instance, seed)
                        for walk in range(PROTOCOL["validation"]["parents_per_case"]):
                            active = {"instance": name, "seed": seed, "profile": profile["name"], "walk": walk}
                            parent = decode(instance, genome, params)
                            validate_schedule(instance, params, parent)
                            counts["parent_schedules"] += 1
                            cache = build_prefix(instance, genome, parent)
                            pool_seed = 20261113 + 1009*i + seed + 1000003*walk
                            pool = local_pool(instance, genome, pool_seed, PROTOCOL["candidate_count"])
                            work_total = Counter()
                            for ci, candidate in enumerate(pool):
                                active["candidate"] = ci
                                value, work = incremental_stage0(instance, candidate.genome, arrays, cache)
                                full = exact_stage0(instance, candidate.genome, arrays)
                                for field in ("C", "v", "direct"):
                                    np.testing.assert_array_equal(getattr(value, field), getattr(full, field))
                                assert work["recomputed_ops"] + work["reused_prefix_ops"] + work["unchanged_factory_ops"] == instance.jobs
                                work_total.update(work)
                                counts["comparisons"] += 1
                            stream.write(json.dumps({**active, "genome": asdict(genome), "pool_seed": pool_seed,
                                         "verified_candidates": len(pool), "work": dict(work_total)}) + "\n")
                            genome = pool[(walk*5+3) % len(pool)].genome
                stream.flush()
                print(f"VALIDATED {i+1}/36 comparisons={counts['comparisons']} {name}", flush=True)
        assert counts["comparisons"] == PROTOCOL["validation"]["expected_comparisons"]
        assert counts["parent_schedules"] == PROTOCOL["validation"]["expected_parent_schedules"]
        save(output / "completion.json", {"status": "passed", **dict(counts), "C_v_direct_bitwise_equal": True,
                                          "wall_seconds": perf_counter()-started})
    except BaseException:
        save(output / "failure.json", {"active": active, "counts": dict(counts), "traceback": traceback.format_exc()})
        raise
    return output
