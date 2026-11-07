"""Rotate methods on frozen teacher cases, then audit without feedback."""
from collections import Counter
from time import perf_counter_ns
import shutil
import traceback
from research.fatigue_mechanism.instances import load_instance, parent_genome, fatigue_profile
from .protocol import PROTOCOL, all_instances, selected_instances
from .artifacts import create, gate
from .records import Records, save
from .chain import run as run_chain
from .audit import check
from .mechanism import evaluate


def rotate(values, index):
    i = index % len(values)
    return list(values[i:])+list(values[:i])


def run_methods(instance, params, initial, identity, seeds, block, records, counts):
    output = []
    weights = PROTOCOL["targets"][identity["target"]]
    for position, method in enumerate(rotate(PROTOCOL["methods"], block)):
        case = {**identity, "method": method}
        records.emit("events", {**case, "event": "starting", "method_position": position})
        result, rows, epochs = run_chain(instance, params, initial, weights, case, seeds)
        result["method_position"] = position
        audit = check(instance, params, initial, weights, result, rows, epochs)
        counts.update({"runs": 1, "search_full": result["full_decodes"], "teacher_full": result["teacher_full_decodes"],
                       "selected_full": len(rows), "partial_stage0": result["partial_calls"], "offline_final_full": 1,
                       "offline_pool_regenerations": audit["regenerated_pools"], "algorithm_ns": result["elapsed_ns"]})
        records.emit("chains", result)
        for row in rows:
            records.emit("steps", {**case, **row})
        for epoch in epochs:
            records.emit("epochs", {**case, **epoch})
        records.emit("events", {**case, "event": "finished"})
        records.flush()
        output.append((result, rows, epochs))
    return output


def run_context(instance, params, initial, identity, seeds, block, records, counts):
    for target in rotate(list(PROTOCOL["targets"]), block):
        case = {**identity, "target": target, "mode": "snapshot"}
        result = run_methods(instance, params, initial, case, seeds, block, records, counts)
        truth = evaluate(instance, params, initial, PROTOCOL["targets"][target], result)
        records.emit("mechanism", {**case, **truth})
        counts["snapshot_cases"] += 1
        counts["offline_candidate_full"] += truth["offline_candidate_full_calls"]
    for mi, mode in enumerate(rotate(["steps", "time"], block)):
        run_methods(instance, params, initial, {**identity, "target": "TEC", "mode": mode},
                    seeds, block+mi, records, counts)


def run(project, validation):
    evidence = gate(project, validation)
    output, counts, started = create(project, "performance"), Counter(), perf_counter_ns()
    save(output/"validation_gate.json", {"source": str(validation), "evidence": evidence,
                                        "all_validated_sources_and_data_identical": True})
    records, active, block = Records(output), None, 0
    order = all_instances(project)
    print(f"RUN_DIRECTORY {output}", flush=True)
    try:
        for filename in selected_instances(project):
            index = order.index(filename)
            instance = load_instance(project/"data/chapter4"/filename, PROTOCOL["setup_seed_base"]+index)
            params, metadata = fatigue_profile(instance, PROTOCOL["profile"], PROTOCOL["profile_seed_base"]+index)
            shutil.copyfile(instance.source, output/filename)
            save(output/(filename+".setup.json"), instance.setup.tolist())
            for seed in PROTOCOL["parent_seeds"]:
                initial = parent_genome(instance, seed)
                for ri, regime in enumerate(PROTOCOL["regimes"]):
                    for size in PROTOCOL["block_sizes"]:
                        active = {"instance": filename, "parent_seed": seed, "regime": regime, "block_size": size}
                        seeds = {"bank": PROTOCOL["bank_seed_base"]+1009*index+seed+ri*10000019,
                                 "pool": PROTOCOL["pool_seed_base"]+1009*index+seed,
                                 "choice": PROTOCOL["choice_seed_base"]+1009*index+seed}
                        records.emit("inputs", {**active, "seeds": seeds, "fatigue": metadata,
                            "setup_source": instance.setup_source, "standby_source": instance.standby_source})
                        run_context(instance, params, initial, active, seeds, block, records, counts)
                        block += 1
                print(f"PARENT {block//4}/65 contexts={block} runs={counts['runs']} {filename} seed={seed}", flush=True)
        assert counts["runs"] == PROTOCOL["expected_total_runs"]
        assert counts["snapshot_cases"] == PROTOCOL["expected_snapshot_cases"]
        records.flush()
        save(output/"completion.json", {"status": "complete", "contexts": block, "calls": dict(counts),
             "algorithm_elapsed_ns_sum": counts["algorithm_ns"], "experiment_wall_ns": perf_counter_ns()-started,
             "json_io_ns": records.io_ns})
    except BaseException:
        save(output/"failure.json", {"active": active, "contexts": block, "calls": dict(counts), "traceback": traceback.format_exc()})
        raise
    finally:
        records.close()
    print(f"COMPLETE {output}", flush=True)
    return output
