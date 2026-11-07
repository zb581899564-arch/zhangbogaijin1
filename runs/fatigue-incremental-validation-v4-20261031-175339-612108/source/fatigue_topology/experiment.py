"""Frozen, held-out mechanism experiment; all results go to a fresh directory."""
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import json
import platform
import shutil
import sys
import time
import traceback
import numpy as np
from research.fatigue_mechanism.instances import load_instance, parent_genome, fatigue_profile
from research.fatigue_mechanism.validation import validate_schedule
from .protocol import PROTOCOL
from .trials import make_pool
from .scoring import reverses
from .timing import Accounting, case_timing
from .case import run_pool


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def initialize(project):
    output = project / "runs" / ("fatigue-topology-v2-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    output.mkdir(parents=True, exist_ok=False)
    save(output / "protocol.json", PROTOCOL)
    save(output / "environment.json", {"python": sys.version, "executable": sys.executable, "numpy": np.__version__,
          "platform": platform.platform(), "processor": platform.processor(), "threads": 1,
          "started_local": datetime.now().isoformat()})
    for package in ("fatigue_topology", "fatigue_mechanism"):
        for source in (project / "research" / package).rglob("*.py"):
            target = output / "source" / package / source.relative_to(project / "research" / package)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    return output


def run(project):
    output, counter, started = initialize(project), Accounting(), time.perf_counter()
    print(f"RUN_DIRECTORY {output}", flush=True)
    streams = {name: (output / (name + ".jsonl")).open("x", encoding="utf-8")
               for name in ("inputs", "predictions", "observations", "selections", "timing")}
    observations, selections, completed = [], [], 0

    def emit(name, value):
        streams[name].write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")
        streams[name].flush()

    try:
        eligible = json.loads((project / "docs/chapter4_instance_eligibility.json").read_text(encoding="utf-8"))["eligible"]
        for i, filename in enumerate(PROTOCOL["instances"]):
            assert filename in eligible
            instance = load_instance(project / "data/chapter4" / filename, PROTOCOL["setup_seed_base"] + i)
            shutil.copyfile(instance.source, output / filename)
            save(output / (filename + ".setup.json"), instance.setup.tolist())
            for seed in PROTOCOL["parent_seeds"]:
                genome = parent_genome(instance, seed)
                pool_seed = PROTOCOL["pool_seed_base"] + 1009*i + seed
                factories = {name: (lambda name=name: make_pool(instance, genome, pool_seed, name, PROTOCOL))
                             for name in PROTOCOL["pools"]}
                pools = {name: factory() for name, factory in factories.items()}
                for profile in PROTOCOL["profiles"]:
                    identity = {"instance": filename, "parent_seed": seed, "profile": profile["name"]}
                    params, metadata = fatigue_profile(instance, profile, PROTOCOL["profile_seed_base"] + i)
                    trace = counter.adaptive("parent_prediction", instance, genome, params)
                    check = validate_schedule(instance, params, trace)
                    emit("inputs", {**identity, "genome": asdict(genome), "pool_seed": pool_seed,
                         "fatigue": metadata, "parent_objectives": trace.objectives.tolist(), "validation": check,
                         "source": instance.source, "setup_source": instance.setup_source, "standby_source": instance.standby_source})
                    reverse = reverses(instance, params, trace, PROTOCOL["targets"])
                    common = case_timing(counter, instance, params, genome, trace, PROTOCOL["targets"], PROTOCOL["timing_repeats"])
                    emit("timing", {**identity, "scope": "case", "values": common})
                    for name, pool in pools.items():
                        obs, selected = run_pool(counter, instance, params, trace, pool, factories[name], reverse,
                                                 {**identity, "pool": name}, PROTOCOL, common, emit)
                        observations.extend(obs)
                        selections.extend(selected)
                    completed += 1
                    print(f"CASE {completed}/90 {filename} seed={seed} {profile['name']}", flush=True)
        save(output / "completion.json", {"status": "complete", "cases": completed, "observations": len(observations),
             "selections": len(selections), "calls": dict(counter.calls), "wall_seconds": time.perf_counter() - started})
    except BaseException:
        save(output / "failure.json", {"status": "failed", "completed_cases": completed,
             "calls": dict(counter.calls), "traceback": traceback.format_exc()})
        raise
    finally:
        for stream in streams.values():
            stream.close()
    return output
