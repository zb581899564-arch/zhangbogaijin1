"""New-seed performance only after the independent numerical gate passes."""
from collections import Counter
from dataclasses import asdict
from time import perf_counter_ns
import json
import shutil
import traceback
from research.fatigue_mechanism.instances import load_instance, parent_genome, fatigue_profile
from research.fatigue_reuse.experiment import Records, save
from .artifacts import create, validation_gate
from .calibration import calibrate
from .runner import run_block
from .protocol import PROTOCOL


def run(project, validation):
    evidence = validation_gate(project, validation)
    output, counts, started = create(project, "performance"), Counter(), perf_counter_ns()
    save(output / "validation_gate.json", {"source": str(validation), "evidence": evidence,
         "verified_kernel_sources_and_instances_unchanged": True})
    print(f"RUN_DIRECTORY {output}", flush=True)
    records, results, case_index, active = Records(output), [], 0, None
    try:
        eligible = json.loads((project / "docs/chapter4_instance_eligibility.json").read_text(encoding="utf-8"))["eligible"]
        for i, filename in enumerate(PROTOCOL["instances"]):
            assert filename in eligible
            instance = load_instance(project / "data/chapter4" / filename, PROTOCOL["setup_seed_base"] + i)
            shutil.copyfile(instance.source, output / filename)
            save(output / (filename + ".setup.json"), instance.setup.tolist())
            for seed in PROTOCOL["parent_seeds"]:
                initial = parent_genome(instance, seed)
                pool_seed = PROTOCOL["pool_seed_base"] + 1009*i + seed
                choice_seed = PROTOCOL["choice_seed_base"] + 1009*i + seed
                for profile in PROTOCOL["profiles"]:
                    active = {"instance": filename, "parent_seed": seed, "profile": profile["name"]}
                    params, metadata = fatigue_profile(instance, profile, PROTOCOL["profile_seed_base"] + i)
                    records.emit("inputs", {**active, "genome": asdict(initial), "fatigue": metadata,
                         "pool_seed": pool_seed, "choice_seed": choice_seed, "source": instance.source,
                         "setup_source": instance.setup_source, "standby_source": instance.standby_source})
                    calibration = calibrate(instance, params, initial, pool_seed, PROTOCOL["candidate_count"])
                    records.emit("calibration", {**active, **calibration})
                    for name, count in calibration["calls"].items():
                        counts["calibration_" + name] += count
                    results.extend(run_block(instance, params, initial, active, pool_seed, choice_seed,
                                              case_index, records, counts))
                    case_index += 1
                    print(f"CASE {case_index}/90 chains={len(results)} {filename} seed={seed} {profile['name']}", flush=True)
        assert len(results) == PROTOCOL["expected_chains"]
        save(output / "completion.json", {"status": "complete", "cases": case_index, "chains": len(results),
             "calls": dict(counts), "algorithm_elapsed_ns_sum": sum(r["elapsed_ns"] for r in results),
             "experiment_wall_ns": perf_counter_ns() - started, "json_io_ns": records.io_ns})
    except BaseException:
        save(output / "failure.json", {"active_case": active, "completed_cases": case_index,
             "completed_chains": len(results), "calls": dict(counts), "traceback": traceback.format_exc()})
        raise
    finally:
        records.close()
    print(f"COMPLETE {output}", flush=True)
    return output
