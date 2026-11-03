"""Serial experiment with actual time/FE budgets and immutable raw records."""
from collections import Counter
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from time import perf_counter_ns
import json
import platform
import shutil
import sys
import traceback
import numpy as np
from research.fatigue_mechanism.instances import load_instance, parent_genome, fatigue_profile
from research.fatigue_mechanism.decoder import decode
from research.fatigue_mechanism.model import Genome
from research.fatigue_mechanism.validation import validate_schedule
from .protocol import PROTOCOL
from .calibration import calibrate
from .chain import run as run_chain
from .audit import audit_chain, compare_ablation


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


class Records:
    def __init__(self, path):
        names = ("inputs", "calibration", "chains", "steps", "epochs", "events", "ablation")
        self.streams = {name: (path / (name + ".jsonl")).open("x", encoding="utf-8") for name in names}
        self.io_ns = 0

    def emit(self, name, value):
        start = perf_counter_ns()
        self.streams[name].write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")
        self.io_ns += perf_counter_ns() - start

    def flush(self):
        for stream in self.streams.values():
            stream.flush()

    def close(self):
        for stream in self.streams.values():
            stream.close()


def initialize(project):
    path = project / "runs" / ("fatigue-reuse-v3-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    path.mkdir(parents=True, exist_ok=False)
    save(path / "protocol.json", PROTOCOL)
    save(path / "environment.json", {"python": sys.version, "executable": sys.executable, "numpy": np.__version__,
         "platform": platform.platform(), "processor": platform.processor(), "threads": 1,
         "started_local": datetime.now().isoformat()})
    for package in ("fatigue_mechanism", "fatigue_topology", "fatigue_reuse"):
        for source in (project / "research" / package).rglob("*.py"):
            target = path / "source" / package / source.relative_to(project / "research" / package)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    return path


def run_block(instance, params, initial, identity, pool_seed, choice_seed, block_index, records, counts):
    summaries = []
    for ti, (target, weights) in enumerate(PROTOCOL["targets"].items()):
        modes = ("steps", "time") if block_index % 2 == 0 else ("time", "steps")
        for mi, mode in enumerate(modes):
            methods = list(PROTOCOL["methods"])
            is_ablation = target == "TEC" and mode == "steps" and identity["profile"] == "strong_fast_recovery"
            if is_ablation:
                methods.append("cut_fatigue_fresh")
            rotation = (block_index + ti + mi) % len(methods)
            methods = methods[rotation:] + methods[:rotation]
            ablation = {}
            for position, method in enumerate(methods):
                case_id = {**identity, "target": target, "mode": mode, "method": method}
                records.emit("events", {**case_id, "event": "starting", "method_position": position})
                selector = "cut_fatigue" if method == "cut_fatigue_fresh" else method
                result, rows, epochs = run_chain(instance, params, initial, weights, selector, mode, PROTOCOL,
                                                  pool_seed, choice_seed, method == "cut_fatigue_fresh")
                result.update({**case_id, "selector": selector, "method_position": position})
                check = audit_chain(instance, initial, result, rows, epochs, PROTOCOL)
                counts["offline_candidate_regenerations"] += check["candidate_regenerations"]
                final = decode(instance, Genome(**result["final_genome"]), params)
                counts["offline_final_QA_full"] += 1
                np.testing.assert_allclose(final.objectives, result["final_objectives"], atol=1e-8, rtol=1e-12)
                result["offline_final_validation"] = validate_schedule(instance, params, final)
                counts["search_full"] += result["full_decodes"]
                counts["search_partial_stage0"] += result["partial_stage0_calls"]
                counts["search_cache_builds"] += result["cache_builds"]
                records.emit("chains", result)
                for row in rows:
                    records.emit("steps", {**case_id, **row})
                for epoch in epochs:
                    records.emit("epochs", {**case_id, **epoch})
                records.emit("events", {**case_id, "event": "finished"})
                summaries.append(result)
                if is_ablation and selector == "cut_fatigue":
                    ablation[method] = result, rows
                records.flush()
            if is_ablation:
                records.emit("ablation", {**identity, "target": target,
                             **compare_ablation(ablation["cut_fatigue"], ablation["cut_fatigue_fresh"])})
    return summaries


def run(project):
    output, started, counts = initialize(project), perf_counter_ns(), Counter()
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
        save(output / "completion.json", {"status": "complete", "cases": case_index, "chains": len(results),
             "calls": dict(counts), "algorithm_elapsed_ns_sum": sum(r["elapsed_ns"] for r in results),
             "experiment_wall_ns": perf_counter_ns() - started, "json_io_ns": records.io_ns})
    except BaseException:
        save(output / "failure.json", {"status": "failed", "active_case": active, "completed_cases": case_index,
             "completed_chains": len(results), "calls_so_far": dict(counts), "traceback": traceback.format_exc()})
        raise
    finally:
        records.close()
    print(f"COMPLETE {output}", flush=True)
    return output
