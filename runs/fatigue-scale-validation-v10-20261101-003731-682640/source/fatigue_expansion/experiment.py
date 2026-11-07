"""Serial expanded equal-time trials using the unchanged v4 score engines."""
from collections import Counter
from dataclasses import asdict
from time import perf_counter_ns
import shutil
import traceback
from research.fatigue_mechanism.instances import load_instance, parent_genome, fatigue_profile
from research.fatigue_reuse.experiment import Records, save
from research.fatigue_incremental.runner import run_one, compare_implementations
from .artifacts import create, gate
from .protocol import PROTOCOL, instances, cells, chain_protocol


def rotate(values, offset):
    offset %= len(values)
    return values[offset:] + values[:offset]


def fixed_control(instance, params, initial, identity, pool_seed, choice_seed, block, records, counts):
    results = {}
    for position, method in enumerate(rotate(["cut_time", "cut_time_full"], block)):
        case = {**identity, "target": "TEC", "mode": "steps", "repeat": 0,
                "budget_seconds": 0., "primary": False, "method": method}
        results[method] = run_one(instance, params, initial, PROTOCOL["targets"]["TEC"], case,
                                 pool_seed, choice_seed, records, counts, position, chain_protocol(0.))
    evidence = compare_implementations(results["cut_time"], results["cut_time_full"])
    records.emit("ablation", {**identity, "target": "TEC", **evidence})
    return [r[0] for r in results.values()]


def time_block(instance, profiles, initial, identity, pool_seed, choice_seed, block, records, counts):
    totals = []
    for cell_index, (profile, target, budget, primary) in enumerate(rotate(cells(), block)):
        for position, method in enumerate(rotate(PROTOCOL["methods"], block+cell_index)):
            case = {**identity, "profile": profile, "target": target, "budget_seconds": budget,
                    "mode": "time", "repeat": 0, "primary": primary, "method": method}
            result, _ = run_one(instance, profiles[profile][0], initial, PROTOCOL["targets"][target], case,
                                pool_seed, choice_seed, records, counts, position, chain_protocol(budget))
            totals.append(result["elapsed_ns"])
    return len(totals), sum(totals)


def run(project, validation):
    evidence = gate(project, validation)
    output, counts, started = create(project, "performance"), Counter(), perf_counter_ns()
    save(output / "validation_gate.json", {"source": str(validation), "evidence": evidence,
                                           "all_validated_sources_and_instances_identical": True})
    print(f"RUN_DIRECTORY {output}", flush=True)
    records, chains, elapsed_sum, block, active = Records(output), 0, 0, 0, None
    try:
        for i, name in enumerate(instances(project)):
            instance = load_instance(project / "data/chapter4" / name, PROTOCOL["setup_seed_base"] + i)
            shutil.copyfile(instance.source, output / name)
            save(output / (name + ".setup.json"), instance.setup.tolist())
            profiles = {p["name"]: fatigue_profile(instance, p, PROTOCOL["profile_seed_base"] + i)
                        for p in PROTOCOL["profiles"]}
            for seed in PROTOCOL["parent_seeds"]:
                active = {"instance": name, "parent_seed": seed}
                initial = parent_genome(instance, seed)
                pool_seed = PROTOCOL["pool_seed_base"] + 1009*i + seed
                choice_seed = PROTOCOL["choice_seed_base"] + 1009*i + seed
                records.emit("inputs", {**active, "genome": asdict(initial),
                     "profiles": {p: meta for p, (_, meta) in profiles.items()}, "pool_seed": pool_seed,
                     "choice_seed": choice_seed, "source": instance.source, "setup_source": instance.setup_source,
                     "standby_source": instance.standby_source, "seed_index": i, "prior6": i < 6})
                fixed = fixed_control(instance, profiles["strong_fast_recovery"][0], initial,
                     {**active, "profile": "strong_fast_recovery"}, pool_seed, choice_seed, block, records, counts)
                chains += len(fixed)
                elapsed_sum += sum(r["elapsed_ns"] for r in fixed)
                number, elapsed = time_block(instance, profiles, initial, active, pool_seed, choice_seed,
                                             block, records, counts)
                chains += number
                elapsed_sum += elapsed
                block += 1
                print(f"PARENT {block}/108 chains={chains} {name} seed={seed}", flush=True)
        assert chains == PROTOCOL["expected_chains"]
        save(output / "completion.json", {"status": "complete", "parents": block, "instances": 36,
             "chains": chains, "calls": dict(counts), "algorithm_elapsed_ns_sum": elapsed_sum,
             "experiment_wall_ns": perf_counter_ns()-started, "json_serialization_write_ns": records.io_ns})
    except BaseException:
        save(output / "failure.json", {"active": active, "completed_parents": block, "chains": chains,
                                       "calls": dict(counts), "traceback": traceback.format_exc()})
        raise
    finally:
        records.close()
    print(f"COMPLETE {output}", flush=True)
    return output
