"""Engineering calibration precedes freezing; trial outputs never choose protocol constants."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
import math

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from baseline_build import execute
from dynamic_build import build_dynamic
from dynamic_inputs import materialize

INSTANCES = ["20_2_3_1", "20_8_5_1", "100_2_3_1", "100_8_3_1", "200_5_3_1", "200_8_5_1"]
CORE = ["BASELINE", "RANDOM", "GREEDY", "TAIL", "VALUE"]
EXTRA = ["SYNC", "VALUE_SYNC", "SHARE", "VALUE_SHARE"]
SEEDS = [7021103, 7021129, 7021151, 7021183, 7021211]
FE = 30000


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def command(cp, input_dir, out, stem, mode, fe, seed, seconds):
    return ["java", "-Xms32m", "-Xmx2g", "-cp", cp, "research.dynamic.DynamicRun",
            str(ROOT/"data/chapter4"/(stem+".txt")), str(input_dir/"RECONSTRUCTED-setup.txt"),
            str(input_dir/"fatigue-input.txt"), str(out), mode, str(fe), str(seed),
            str(seconds) if seconds is not None else "Infinity", "1.0", "true", "false", "0", "true"]


def prepare():
    out = ROOT/"runs"/datetime.now().strftime("dynamic-step45-%Y%m%d-%H%M%S-%f")
    out.mkdir()
    cp = build_dynamic(out, True)
    (out/"classpath.txt").write_text(cp, encoding="utf-8")
    records = []
    # Quality outcomes in calibration are not read or printed, only cost and mechanism coverage.
    for stem in INSTANCES:
        inputs = out/"inputs"/stem; inputs.mkdir(parents=True)
        instance, params, metadata = materialize(ROOT/"data/chapter4"/(stem+".txt"), inputs, 314159, "strong_fast", 271828)
        dump(inputs/"source.json", metadata)
        calibration = out/"calibration"/stem; calibration.mkdir(parents=True)
        execute(command(cp, inputs, calibration, stem, "VALUE", FE, 991033, None), calibration/"run.log", timeout=300)
        summary = json.loads((calibration/"summary.json").read_text(encoding="utf-8"))
        heads = summary["joint"]["perDirection"]
        if not all(v["updates"] >= 2 for v in heads.values()):
            raise RuntimeError("Calibration did not cover learning startup: "+stem)
        # 1.5x measured VALUE FE cost; baseline quality and trial outcomes never consulted.
        seconds = max(3, math.ceil(summary["searchSeconds"]*1.5))
        records.append({"stem":stem, "feLimit":FE, "timeLimitSeconds":seconds,
                        "calibrationSeconds":summary["searchSeconds"], "calibrationGenerations":summary["search"].get("generations.completed",0),
                        "calibrationHeadUpdates":{k:v["updates"] for k,v in heads.items()}})
        print("CALIBRATED",stem,summary["searchSeconds"],seconds,flush=True)
    # Freeze numerical normalization from unrelated random encodings, not optimizer outcomes.
    from research.fatigue_mechanism.instances import parent_genome
    from research.fatigue_mechanism.decoder import decode
    import numpy as np
    for row in records:
        stem=row["stem"]; inputs=out/"inputs"/stem
        instance, params, _ = materialize(ROOT/"data/chapter4"/(stem+".txt"), inputs, 314159, "strong_fast", 271828)
        values = [decode(instance,parent_genome(instance,880000+i),params,False).objectives for i in range(128)]
        scale = np.max(np.asarray(values),axis=0).tolist()
        row["normalization"]={"lower":[0,0,0],"scale":scale,"reference":[1.1,1.1,1.1],"source":"max of128 random parents, seeds880000..880127"}
        dump(inputs/"normalization-parents.json", [list(map(float,v)) for v in values])
        print("NORMALIZED",stem,flush=True)
    files=sorted([* (ROOT/"src/java").rglob("*.java"), *(ROOT/"src/algorithms/joint").glob("*.java"), *(ROOT/"src/algorithms/cooperation").glob("*.java"), *Path(__file__).parent.glob("*.py")])
    manifest={}
    for file in files:
        rel=file.relative_to(ROOT); payload=file.read_bytes(); dest=out/"source"/rel; dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(payload)
        manifest[str(rel)] = hashlib.sha256(payload).hexdigest()
    dump(out/"source-manifest.json",manifest)
    protocol={"version":"step45-development-v1","frozenAt":datetime.now().isoformat(),"instances":records,"seeds":SEEDS,
              "coreVariants":CORE,"cooperationVariants":EXTRA,"checkpoints":[.25,.5,1.],"mode":"sequential independent JVM",
              "search":"default100/15/Q50/local30; incremental shared; all online costs included",
              "referenceSet":"nondominated union of all9 variants final deadline-valid archives in both budgets and5 seeds per instance; empirical, not truePF",
              "statistics":"seed means within instance; six paired instance effects; exact one-sided signflip;5000 paired bootstrap;Holm within step across both budgets",
              "timeTarget":"95% of largest final HV across9 variants per instance; first scheduled checkpoint; no interpolation; unachieved censored",
              "scope":"development6 instances; one synthetic strong_fast profile; no test-set/generalization claim",
              "environment":{"platform":platform.platform(),"python":sys.version,"heap":"32m..2g","externalTasks":"uncontrolled desktop background; run order balanced/randomized; no competing benchmark JVM"}}
    dump(out/"protocol.json",protocol)
    dump(out/"status.json",{"status":"FROZEN_READY","completed":0,"expected":540})
    print("FROZEN",out,flush=True)
    return out


def run(root):
    protocol=json.loads((root/"protocol.json").read_text(encoding="utf-8"))
    cp=(root/"classpath.txt").read_text(encoding="utf-8")
    variants=protocol["coreVariants"]+protocol["cooperationVariants"]
    jobs=[]; rng=random.Random(921173)
    for budget in ["FE","TIME"]:
        for row in protocol["instances"]:
            for seed in protocol["seeds"]:
                order=variants.copy();rng.shuffle(order)
                for variant in order: jobs.append((row,budget,seed,variant))
    expected=len(jobs); dump(root/"run-order.json",[{"instance":a["stem"],"budget":b,"seed":c,"variant":d} for a,b,c,d in jobs])
    completed=0
    for row,budget,seed,mode in jobs:
        folder=root/"trials"/row["stem"]/budget/str(seed)/mode
        if (folder/"summary.json").exists():
            summary=json.loads((folder/"summary.json").read_text(encoding="utf-8"))
            if summary["status"]!="passed": raise RuntimeError("Existing failed run preserved: "+str(folder))
        else:
            folder.mkdir(parents=True,exist_ok=True)
            seconds=row["timeLimitSeconds"] if budget=="TIME" else None
            cmd=command(cp,root/"inputs"/row["stem"],folder,row["stem"],mode,9223372036854775807 if seconds else row["feLimit"],seed,seconds)
            dump(folder/"command.json",cmd)
            try: execute(cmd,folder/"run.log",timeout=max(300, (seconds or row["calibrationSeconds"])*5+60))
            except Exception as ex:
                dump(root/"status.json",{"status":"FAILED_PRESERVED","completed":completed,"expected":expected,"run":str(folder),"error":str(ex)})
                raise
        completed+=1
        dump(root/"status.json",{"status":"RUNNING" if completed<expected else "RUNS_COMPLETE","completed":completed,"expected":expected,"lastRun":str(folder)})
        if completed%9==0: print("RUNS",completed,"/",expected,row["stem"],budget,flush=True)
    return root


if __name__=="__main__":
    root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else prepare()
    run(root)
