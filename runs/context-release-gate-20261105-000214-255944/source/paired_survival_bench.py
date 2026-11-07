"""Shared mechanics for isolated whole-budget survival experiments, with no policy selection."""
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once
from run_dynamic_deep_roles import ledger
from run_center_entry_cross_replay import write_ledger

FROZEN = ROOT / "runs/night-research-H1-20261103-010138-848045"
ANCHOR = ROOT / "runs/pddr-role-budget-20261104-095957/DEEP"
CHECKS = (100, 5100, 15000, 50000, 100000, 250000, 500000)


def prepare(root, instances, seeds, arms):
    specs = [x for x in read(FROZEN / "protocol.json")["instances"] if x["stem"] in instances]
    order = []
    for i, stem in enumerate(instances):
        shutil.copytree(FROZEN / "inputs" / stem, root / stem / "inputs")
        for j, seed in enumerate(seeds):
            folder = root / stem / str(seed); folder.mkdir()
            f = int(stem.split("_")[2]); rng = np.random.default_rng(seed ^ 0x5A17)
            slots = [(v,g,r,int(rng.integers(f)) if r >= 0 else -1,n,0) for v,g,r,old_f,n,_ in ledger(ANCHOR / "SPECIAL-LINEAR")]
            write_ledger(folder / "ledger.csv", slots)
            offset = (i + j) % len(arms)
            order.extend({"stem": stem, "seed": seed, "arm": a} for a in (*arms[offset:], *arms[:offset]))
    return specs, order


def run_cell(root, cp, spec, jvm_overrides=None):
    stem, seed, arm = (spec[k] for k in ("stem", "seed", "arm"))
    folder = root / stem / str(seed); out = folder / arm; out.mkdir(); inp = root / stem / "inputs"
    li = spec.get("liLegacy", arm == "LI_MATCHED_DEEP")
    mode = spec.get("mode", "NSGA2_4V" if arm == "NSGA" else "BASELINE" if li else "SHARE_JOB_ALIGNED")
    policy = "FORCE" if arm in ("NSGA", "LI_MATCHED_DEEP") else arm
    cmd = ["java", "-Xms32m", "-Xmx2g", f"-Dresearch.batch.mode={policy}", f"-Dresearch.li.v2={str(li).lower()}",
           f"-Dresearch.common.initials={str(spec.get('commonInitials', li)).lower()}", "-cp", cp, "research.dynamic.PddrIsolationRun",
           str(inp / f"{stem}.txt"), str(inp / "RECONSTRUCTED-setup.txt"), str(inp / "fatigue-input.txt"),
           str(out), mode, "LINEAR", str(folder / "ledger.csv"), "500000", str(seed), *map(str, CHECKS)]
    for key, value in (jvm_overrides or {}).items():
        prefix = "-D" + key + "="
        cmd = [x for x in cmd if not x.startswith(prefix)]
        cmd.insert(cmd.index("-cp"), prefix + str(value))
    write_once(out / "command.json", cmd); print("PAIRED_CELL", stem, seed, arm, flush=True)
    start = time.monotonic()
    with (out / "run.log").open("x", encoding="utf-8") as log:
        code = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=600).returncode
    write_once(out / "process.json", {"returnCode": code, "wallSeconds": time.monotonic() - start})
    if code: raise RuntimeError((out / "run.log").read_text(encoding="utf-8")[-2500:])
    verify_cell(out, folder)
    return out


def verify_cell(out, folder):
    r, = rows(out / "run-receipt.jsonl")
    assert r["attempted"] == r["successful"] == r["decoder"]["dynamic.evaluations"] == 500000 and r["failed"] == 0
    assert {s:r["search"][s + ".evaluations"] for s in ("initialization","global","inter","intra")} == {
        "initialization":100,"global":10000,"inter":549,"intra":489351}
    expected = [tuple(map(int, x.split(","))) for x in (folder / "ledger.csv").read_text(encoding="utf-8-sig").splitlines()[1:]]
    assert [x[:-1] for x in ledger(out)] == [x[:-1] for x in expected]
    initials = [p / "initial-population.jsonl" for p in folder.iterdir() if p.is_dir() and (p / "initial-population.jsonl").exists()]
    assert all(p.read_bytes() == initials[0].read_bytes() for p in initials)
    assert read(out / "summary.json")["offlineValidationDecodes"] == len(rows(out / "solutions.jsonl"))
    end = rows(out / "anytime.jsonl")[-1]
    assert {tuple(x) for x in end["front"]} == {tuple(x["objectives"]) for x in rows(out / "solutions.jsonl")}
    write_once(out / "verified.json", {"successfulFE":500000,"failedFE":0,"sameInitials":True,"samePhysicalLedger":True,"finalArchiveMatches":True})


def class_hashes(classes):
    return {p.relative_to(classes).as_posix():sha256(p.read_bytes()).hexdigest() for p in classes.rglob("*.class")}
