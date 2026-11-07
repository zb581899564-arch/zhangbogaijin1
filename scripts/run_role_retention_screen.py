"""New-data screen of role-conditioned global retention; no neighborhood or probability tuning."""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np

from run_dynamic_deep_roles import ledger
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, hypervolume, igd_plus, nondominated, controller_lock
from run_global_retention_gate import build as build_gate
from run_paired_qgs_guidance import replace
from run_center_entry_cross_replay import write_ledger

FROZEN = ROOT / "runs/night-research-H1-20261103-010138-848045"
ANCHOR = ROOT / "runs/pddr-role-budget-20261104-095957/DEEP"
INSTANCES = ("20_8_5_1", "100_2_3_1")
SEEDS = (9210007, 9210031, 9210061)
ARMS = ("FORCE", "ROLE_GREEDY", "CENTER_GREEDY", "NSGA", "LI_MATCHED_DEEP")
FE = (100, 5100, 15000, 50000, 100000, 250000, 500000)


def build(root):
    # Freeze the same proposal/current machinery used in the preceding discovery batch.
    cp = build_gate(root)
    src, classes = root / "source", root / "classes"
    shutil.copy2(ROOT / "src/algorithms/diagnostics/CommonInitials.java", src)
    shutil.copy2(Path(__file__), src)
    state = (ROOT / "runs/pddr-equivalence-20261104-081553-961399/source/SearchState.java").read_text(encoding="utf-8")
    state = replace(state, "        if (support != null) support.prepareInitialization(solution, initialized);",
                    "        if (support != null) support.prepareInitialization(solution, initialized);\n"
                    "        else CommonInitials.prepare(solution, initialized, instance);")
    (src / "SearchState.java").write_text(state, encoding="utf-8")
    entry = (src / "PddrIsolationRun.java").read_text(encoding="utf-8")
    entry = replace(entry, "        cfg.mergeGlobalLocal = cfg.paperResourceOperators = !DynamicSearch.isClassic(mode);",
                    "        cfg.mergeGlobalLocal = cfg.paperResourceOperators = !DynamicSearch.isClassic(mode)\n"
                    "                && !Boolean.getBoolean(\"research.li.v2\");")
    (src / "PddrIsolationRun.java").write_text(entry, encoding="utf-8")
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", cp, "-d", str(classes),
             str(src / "CommonInitials.java"), str(src / "SearchState.java"), str(src / "PddrIsolationRun.java")], root / "common-initial-compile.log")
    write_once(root / "effective-class-hashes.json", {p.relative_to(classes).as_posix(): sha256(p.read_bytes()).hexdigest()
                                                    for p in classes.rglob("*.class")})
    return cp


def prepare(root):
    old_protocol = read(FROZEN / "protocol.json")
    specs = [s for s in old_protocol["instances"] if s["stem"] in INSTANCES]
    ordered = []
    for i, stem in enumerate(INSTANCES):
        for j, seed in enumerate(SEEDS):
            rotated = ARMS[(i + j) % len(ARMS):] + ARMS[:(i + j) % len(ARMS)]
            ordered.extend({"stem": stem, "seed": seed, "arm": a} for a in rotated)
            folder = root / stem / str(seed); folder.mkdir(parents=True)
            f = int(stem.split("_")[2]); rng = np.random.default_rng(seed ^ 0x5A17)
            slots = [(v, g, r, int(rng.integers(f)) if r >= 0 else -1, n, 0)
                     for v, g, r, old_f, n, _ in ledger(ANCHOR / "SPECIAL-LINEAR")]
            write_ledger(folder / "ledger.csv", slots)
        shutil.copytree(FROZEN / "inputs" / stem, root / stem / "inputs")
    write_once(root / "protocol.json", {"candidate": "ROLE_GREEDY", "instances": specs, "seeds": SEEDS,
        "arms": ARMS, "order": ordered, "actualFEPerCell": 500000, "totalActualFE": len(ordered) * 500000,
        "selectionOrigin": "ROLE_GREEDY was a positive ordinary control (+0.928% vs FORCE, -0.347% vs NSGA) "
                           "in a failed DOM_GUARD study, not a preregistered winner. This is a fresh hypothesis screen.",
        "controls": "CENTER_GREEDY changes only global acceptance preference to CENTER; the four Q reward "
                    "roles, local preferences, subgroup sizes, sharing and proposal kernels remain. LI_MATCHED_DEEP "
                    "is canonical v2 search (legacy S/O, paper baseline PSO) with the shared deep-local quota, "
                    "and must be labelled an augmented comparison, not the original published algorithm result.",
        "commonInitials": "All five arms receive identical paid initial vectors. LI and NSGA release the "
                          "temporary initializer's family flags immediately, retaining their original search scope.",
        "ledger": "Original L_U per-visit/round FE; factory draws fixed independently for each new instance/seed, "
                  "covering its true F. No adaptive quota changes; all five arms share each ledger.",
        "gate": {"eachInstanceMedianHVgainVsFORCEpct": 1, "positiveSeedsPerInstance": 2,
                 "eachInstanceMedianGapVsNSGAMinPct": -1, "medianVsCENTERGREEDYMustBePositive": True,
                 "sameTimeAndIGDplusMustNotMateriallyRegress": True},
        "timePrimary": {s["stem"]: s["time_seconds"] for s in specs},
        "reference": [1.25, 1.5, 2], "noIncompleteCellReplacement": True,
        "scope": "Small new-seed development screen; no independent confirmation or journal-level novelty claim."})
    return ordered


def run(root, cp, spec):
    stem, seed, arm = (spec[k] for k in ("stem", "seed", "arm"))
    folder = root / stem / str(seed); out = folder / arm; out.mkdir(); inp = root / stem / "inputs"
    li = arm == "LI_MATCHED_DEEP"
    mode = "NSGA2_4V" if arm == "NSGA" else "BASELINE" if li else "SHARE_JOB_ALIGNED"
    retention = arm if arm in ("ROLE_GREEDY", "CENTER_GREEDY") else "FORCE"
    cmd = ["java", "-Xms32m", "-Xmx2g", f"-Dresearch.retention.mode={retention}",
           f"-Dresearch.li.v2={str(li).lower()}", f"-Dresearch.common.initials={str(li).lower()}", "-cp", cp,
           "research.dynamic.PddrIsolationRun", str(inp / f"{stem}.txt"), str(inp / "RECONSTRUCTED-setup.txt"),
           str(inp / "fatigue-input.txt"), str(out), mode, "LINEAR", str(folder / "ledger.csv"),
           "500000", str(seed), *map(str, FE)]
    write_once(out / "command.json", cmd); print("SCREEN_CELL", stem, seed, arm, flush=True)
    start = time.monotonic()
    with (out / "run.log").open("x", encoding="utf-8") as log:
        code = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=600).returncode
    write_once(out / "process.json", {"returnCode": code, "wallSeconds": time.monotonic() - start})
    if code: raise RuntimeError((out / "run.log").read_text(encoding="utf-8")[-2500:])
    r, = rows(out / "run-receipt.jsonl")
    assert r["attempted"] == r["successful"] == r["decoder"]["dynamic.evaluations"] == 500000 and r["failed"] == 0
    assert {s: r["search"][s + ".evaluations"] for s in ("initialization", "global", "inter", "intra")} == {
        "initialization": 100, "global": 10000, "inter": 549, "intra": 489351}
    expected = (folder / "ledger.csv").read_text(encoding="utf-8-sig").splitlines()[1:]
    assert [x[:-1] for x in ledger(out)] == [tuple(map(int, x.split(",")))[:-1] for x in expected]
    first = [p / "initial-population.jsonl" for p in folder.iterdir() if p.is_dir() and (p / "initial-population.jsonl").exists()][0]
    assert (out / "initial-population.jsonl").read_bytes() == first.read_bytes()
    assert read(out / "summary.json")["offlineValidationDecodes"] == len(rows(out / "solutions.jsonl"))
    write_once(out / "verified.json", {"FE": 500000, "zeroFailures": True, "matchedInitial": True, "matchedPhysicalSlots": True})


def analyze(root):
    protocol = read(root / "protocol.json"); per_instance = []; cell_results = []
    for spec in protocol["instances"]:
        stem, norm, cut = spec["stem"], spec["normalization"], spec["time_seconds"]
        normal = lambda x: (np.asarray(x) - norm["lower"]) / norm["scale"]
        fs = {(seed, a): rows(root / stem / str(seed) / a / "anytime.jsonl")[-1]["front"] for seed in SEEDS for a in ARMS}
        empirical = nondominated(np.vstack([normal(x) for x in fs.values()]))
        metrics = {}
        for seed in SEEDS:
            for a in ARMS:
                folder = root / stem / str(seed) / a
                timed = next((r for r in rows(folder / "time.jsonl") if abs(r["checkpoint"] - cut) < 1e-9), None)
                metrics[(seed, a)] = {"HV": {str(ref): float(hypervolume(normal(fs[(seed, a)]), (ref,) * 3)) for ref in (1.25, 1.5, 2)},
                                      "timeHV": float(hypervolume(normal(timed["front"]), (1.5,) * 3)) if timed else None,
                                      "timeFE": timed["fe"] if timed else None,
                                      "timeCutAvailable": timed is not None,
                                      "IGDplus": float(igd_plus(normal(fs[(seed, a)]), empirical))}
                cell_results.append({"stem": stem, "seed": seed, "arm": a, **metrics[(seed, a)]})
        effects = {a: [100 * (metrics[(s, "ROLE_GREEDY")]["HV"]["1.5"] / metrics[(s, a)]["HV"]["1.5"] - 1) for s in SEEDS]
                   for a in ARMS if a != "ROLE_GREEDY"}
        decision = np.median(effects["FORCE"]) >= 1 and sum(x > 0 for x in effects["FORCE"]) >= 2 \
            and np.median(effects["NSGA"]) >= -1 and np.median(effects["CENTER_GREEDY"]) > 0
        per_instance.append({"stem": stem, "candidateEffectsPct": effects,
                             "medianEffectsPct": {a: float(np.median(x)) for a, x in effects.items()}, "primaryPass": bool(decision)})
    out = {"instances": per_instance, "cells": cell_results,
           "timeLimitation": "The requested 5-second cut was absent from the inherited recorder; no interpolation or "
                             "nearby-cut substitution is used. FE evidence remains complete; full time gate cannot pass.",
           "primaryGate": "REVIEW_AUXILIARIES" if all(x["primaryPass"] for x in per_instance) else "STOP_ROLE_GREEDY_SCREEN"}
    write_once(root / "comparison.json", out); return out


def main():
    root = ROOT / "runs" / datetime.now().strftime("role-retention-screen-%Y%m%d-%H%M%S-%f")
    root.mkdir(); print("SCREEN_ROOT", root, flush=True)
    start, completed = time.monotonic(), []
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            plan = prepare(root); cp = build(root)
            for spec in plan: run(root, cp, spec); completed.append(spec)
            result = analyze(root)
    except BaseException as exc:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "completed": completed, "error": str(exc)})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "completed": len(completed), "paidFE": len(completed) * 500000,
                                      "wallSeconds": time.monotonic() - start, "primaryGate": result["primaryGate"]})
    print("SCREEN_COMPLETE", result["instances"], flush=True)


if __name__ == "__main__":
    main()
