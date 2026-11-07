"""Run the predeclared small mechanism diagnosis into a new immutable directory."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import json
import platform
import shutil
import sys
import traceback
import numpy as np
from .candidates import candidate_pool
from .case import run_case
from .instances import load_instance, parent_genome, fatigue_profile
from .protocol import PROTOCOL
from .reporting import summarize, markdown_report
from .timing import DecodeCounter


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def initialize_run(project):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    output = project / "runs" / f"fatigue-mechanism-v1-{stamp}"
    output.mkdir(parents=True, exist_ok=False)
    save_json(output / "protocol.json", PROTOCOL)
    save_json(output / "environment.json", {"python": sys.version, "executable": sys.executable,
              "numpy": np.__version__, "platform": platform.platform(), "processor": platform.processor(),
              "threads": 1, "started_local": datetime.now().isoformat()})
    source = Path(__file__).parent
    for path in source.rglob("*.py"):
        target = output / "source" / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    return output


def run(project):
    output = initialize_run(project)
    print(f"RUN_DIRECTORY {output}", flush=True)
    counter, selections, cases = DecodeCounter(), [], []
    streams = {name: (output / (name + ".jsonl")).open("x", encoding="utf-8")
               for name in ("inputs", "predictions", "candidates", "selections", "timing")}

    def emit(name, value):
        streams[name].write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")
        streams[name].flush()

    try:
        eligible = json.loads((project / "docs/chapter4_instance_eligibility.json").read_text(encoding="utf-8"))["eligible"]
        for index, filename in enumerate(PROTOCOL["instances"]):
            if filename not in eligible:
                raise ValueError(f"not an eligible source instance: {filename}")
            setup_seed = PROTOCOL["setup_seed_base"] + index
            source_path = project / "data/chapter4" / filename
            instance = load_instance(source_path, setup_seed)
            shutil.copyfile(source_path, output / filename)
            save_json(output / (filename + ".setup.json"), {"seed": setup_seed, "values": instance.setup.tolist()})
            for seed in PROTOCOL["parent_seeds"]:
                parent = parent_genome(instance, seed)
                pool_seed = seed + PROTOCOL["candidate_seed_offset"] + 1009 * index
                pool_factory = lambda: candidate_pool(instance, parent, pool_seed, PROTOCOL["candidate_count"])
                pool = pool_factory()
                for profile in PROTOCOL["profiles"]:
                    profile_seed = PROTOCOL["profile_seed_base"] + index
                    params, metadata = fatigue_profile(instance, profile, profile_seed)
                    identity = {"instance": filename, "parent_seed": seed, "profile": profile["name"]}
                    emit("inputs", {**identity, "genome": asdict(parent), "pool_seed": pool_seed, "setup_seed": setup_seed,
                         "fatigue": metadata, "data_source": instance.source, "setup_source": instance.setup_source,
                         "standby_source": instance.standby_source})
                    rows, case = run_case(counter, instance, params, parent, pool, pool_factory, identity, PROTOCOL, emit)
                    selections.extend(rows)
                    cases.append(case)
                    print(f"CASE {len(cases)}/90 {filename} seed={seed} {profile['name']}", flush=True)
        summary = summarize(selections, cases, counter.calls, PROTOCOL)
        save_json(output / "summary.json", summary)
        (output / "report.md").write_text(markdown_report(summary), encoding="utf-8")
        print(f"COMPLETE cases={len(cases)} full_decodes={sum(counter.calls.values())}", flush=True)
    except BaseException:
        save_json(output / "failure.json", {"status": "failed", "traceback": traceback.format_exc(),
                  "completed_cases": len(cases), "full_decode_accounting": dict(counter.calls)})
        raise
    finally:
        for stream in streams.values():
            stream.close()
    return output
