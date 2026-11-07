"""Numerical validation on old seeds before any new-seed performance run."""
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
from .artifacts import create
from .prefix import build_prefix, incremental_stage0
from .protocol import PROTOCOL


def run(project):
    output, counts, started = create(project, "validation"), Counter(), perf_counter()
    print(f"VALIDATION_DIRECTORY {output}", flush=True)
    stream = (output / "parents.jsonl").open("x", encoding="utf-8")
    active = None
    try:
        for i, filename in enumerate(PROTOCOL["instances"]):
            instance = load_instance(project / "data/chapter4" / filename, PROTOCOL["setup_seed_base"] + i)
            shutil.copyfile(instance.source, output / filename)
            for seed in PROTOCOL["validation"]["seeds"]:
                for profile in PROTOCOL["profiles"]:
                    params, _ = fatigue_profile(instance, profile, PROTOCOL["profile_seed_base"] + i)
                    arrays, genome = params.arrays(instance), parent_genome(instance, seed)
                    for walk in range(PROTOCOL["validation"]["parents_per_case"]):
                        active = {"instance": filename, "seed": seed, "profile": profile["name"], "walk": walk}
                        parent = decode(instance, genome, params)
                        counts["full_parent"] += 1
                        validate_schedule(instance, params, parent)
                        cache = build_prefix(instance, genome, parent)
                        pool_seed = 20261108 + 1009*i + seed + 1000003*walk
                        pool = local_pool(instance, genome, pool_seed, 16)
                        work_total = Counter()
                        for index, candidate in enumerate(pool):
                            active["candidate"] = index
                            incremental, work = incremental_stage0(instance, candidate.genome, arrays, cache)
                            full = exact_stage0(instance, candidate.genome, arrays)
                            for field in ("C", "v", "direct"):
                                np.testing.assert_array_equal(getattr(incremental, field), getattr(full, field))
                            assert work["recomputed_ops"] + work["reused_prefix_ops"] + work["unchanged_factory_ops"] == instance.jobs
                            work_total.update(work)
                            counts["comparisons"] += 1
                        stream.write(json.dumps({**active, "genome": asdict(genome), "pool_seed": pool_seed,
                                     "verified_candidates": 16, "work": dict(work_total)}, ensure_ascii=False) + "\n")
                        genome = pool[(walk * 5 + 3) % len(pool)].genome
                    stream.flush()
            print(f"VALIDATED {filename} comparisons={counts['comparisons']}", flush=True)
        assert counts["comparisons"] == 8640
        save(output / "completion.json", {"status": "passed", "comparisons": counts["comparisons"],
             "parent_schedules_validated": counts["full_parent"], "C_v_direct_bitwise_equal": True,
             "wall_seconds": perf_counter() - started, "scope": "correctness only, old seeds; not performance evidence"})
    except BaseException:
        save(output / "failure.json", {"active": active, "counts": dict(counts), "traceback": traceback.format_exc()})
        raise
    finally:
        stream.close()
    return output
