"""Frozen serial36-instance experiment, validated full physics only."""
from collections import Counter
from dataclasses import asdict
from time import perf_counter_ns
import traceback
import numpy as np
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.validation import validate_schedule
from .protocol import PROTOCOL
from .artifacts import create, gate
from .cases import instances, load, initial, cells
from .chain import run as run_chain
from .state import State
from .records import Records, save
from . import calibration


def verify(instance, params, result, counts):
    started = perf_counter_ns()
    final = decode(instance, State.from_record(result["final_state"]).genome(), params)
    np.testing.assert_array_equal(final.objectives, result["final_objectives"])
    validate_schedule(instance, params, final)
    counts["final_QA_full"] += 1
    counts["final_QA_ns"] += perf_counter_ns()-started


def block(instance, profiles, state, identity, records, counts):
    seed = 20261222+identity["seed_index"]*1000003+identity["parent_seed"]
    for cell_no, (model, target, mode, seconds, primary) in enumerate(cells()):
        ordering = np.random.default_rng(seed+cell_no*1009).permutation(PROTOCOL["methods"])
        for method in ordering:
            result = run_chain(instance, profiles[model][0], state, str(method), seed,
                PROTOCOL["targets"][target], mode, seconds, PROTOCOL["fixed_children"])
            counts["search_full"] += result["full_decodes"]
            counts["search_online_ns"] += result["elapsed_ns"]
            counts["search_runs"] += 1
            verify(instance, profiles[model][0], result, counts)
            records.emit("search", {**identity, "model": model, "target": target, "primary": primary,
                "jobs": instance.jobs, "factories": instance.factories, "stages": instance.stages, **result})


def run(project, validation):
    evidence = gate(project, validation)
    started, counts = perf_counter_ns(), Counter()
    output = create(project, "performance")
    counts["source_snapshot_ns"] = perf_counter_ns()-started
    save(output/"validation_gate.json", {"source": str(validation), **evidence, "source_and_data_equal": True})
    records, active = Records(output), None
    print(f"RUN_DIRECTORY {output}", flush=True)
    try:
        counts["calibration_full"] = calibration.run(project, output)
        for i, name in enumerate(instances(project)):
            instance, profiles = load(project, i, name)
            save(output/"data"/(name+".setup.json"), instance.setup.tolist())
            for seed in PROTOCOL["parent_seeds"]:
                active = {"instance": name, "parent_seed": seed, "seed_index": i}
                _, state = initial(instance, seed)
                records.emit("inputs", {**active, "initial_state": asdict(state),
                    "profiles": {k: meta for k, (_, meta) in profiles.items()},
                    "setup_source": instance.setup_source, "standby_source": instance.standby_source})
                block(instance, profiles, state, active, records, counts)
                counts["parents"] += 1
                records.flush()
                save(output/(f"checkpoint-{counts['parents']:03d}.json"), {"active": active, "counts": dict(counts), "wall_ns": perf_counter_ns()-started})
                print(f"PARENT {counts['parents']}/108 runs={counts['search_runs']} {name} seed={seed}", flush=True)
        assert counts["search_runs"] == PROTOCOL["expected_chains"] and counts["parents"] == 108
        counts["total_new_full_calls"] = counts["calibration_full"]+counts["search_full"]+counts["final_QA_full"]
        save(output/"completion.json", {"status": "complete", "counts": dict(counts),
            "wall_ns": perf_counter_ns()-started, "disk_json_ns": records.io_ns})
    except BaseException:
        save(output/"failure.json", {"active": active, "counts": dict(counts), "traceback": traceback.format_exc()})
        raise
    finally:
        records.close()
    print(f"COMPLETE {output}", flush=True)
    return output
