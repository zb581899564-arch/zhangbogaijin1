"""Six matched fixed-FE searches, with real-time cuts, using a frozen linear PDDR kernel."""
from datetime import datetime
from hashlib import sha256
import math
from pathlib import Path
import shutil
import time

import numpy as np

from pddr_role_budget_plan import ANCHOR, CAP, design
from run_center_entry_cross_replay import write_ledger
from run_dynamic_deep_roles import BRIDGE, ledger
from run_dynamic_reverse_ledger_audit import ROOT, SEED, POINTS, trial_folder
from run_long_budget_bridge import controller_lock, hypervolume, objectives, read, rows, write_once
from run_pddr_isolation import TIME, run


PDDR = ROOT / "runs/pddr-equivalence-20261104-081553-961399"
ORDER = (("DEEP", "SPECIAL"), ("DEEP", "NSGA"), ("ROTATE", "NSGA"), ("ROTATE", "SPECIAL"),
         ("ROLE", "SPECIAL"), ("ROLE", "NSGA"))
STAGES = ("initialization", "global", "inter", "intra")
ALGORITHMS = ("SPECIAL", "NSGA")


def frozen_classpath():
    assert read(PDDR / "status.json")["status"] == "COMPLETE"
    assert read(PDDR / "equivalence-gate.json")["status"] == "PASS"
    for name, expected in read(PDDR / "class-hashes.json").items():
        assert sha256((PDDR / "classes" / name).read_bytes()).hexdigest() == expected
    return (PDDR / "classpath.txt").read_text(encoding="utf-8-sig").strip()


def verify(path, algorithm, plan, slots):
    receipt, = rows(path / "run-receipt.jsonl")
    actual = ledger(path)
    assert [s[:-1] for s in actual] == [s[:-1] for s in slots], (algorithm, plan, "physical ledger")
    assert receipt["attempted"] == receipt["successful"] == receipt["decoder"]["dynamic.evaluations"] == CAP
    assert receipt["failed"] == 0 and receipt["stopReason"] == "FE_LIMIT" and receipt["seed"] == SEED
    assert receipt["pddr"]["mode"] == "LINEAR" and receipt["pddr"]["auditedCenterComparisons"] == 0
    assert receipt["paidSHA256"] is None
    assert receipt["decoder"]["dynamic.recomputedOperations"] + receipt["decoder"]["dynamic.reusedOperations"] == 40 * CAP
    search = receipt["search"]
    stage = {s: search[s + ".evaluations"] for s in STAGES}
    assert stage == ({"initialization": 100, "global": 10000, "inter": 549, "intra": 489351}
                     if plan == "DEEP" else {"initialization": 100, "global": 20000, "inter": 800, "intra": 479100})
    for g in range(1, 5):
        assert search[f"inter.g{g}.evaluations"] == sum(s[4] for s in slots if s[1] == g and s[2] < 0)
        assert search[f"intra.g{g}.evaluations"] == sum(s[4] for s in slots if s[1] == g and s[2] >= 0)
    original = trial_folder(ANCHOR, algorithm)
    initial = path / "initial-population.jsonl"
    assert len(rows(initial)) == 100 and initial.read_bytes() == (original / initial.name).read_bytes()
    fe, timed = rows(path / "anytime.jsonl"), rows(path / "time.jsonl")
    assert [r["fe"] for r in fe] == list(POINTS) and all(r["reached"] for r in fe)
    assert len(timed) == len(TIME)
    assert all(r["reached"] and r["front"] and math.isclose(r["checkpoint"], t)
               and r["elapsedSeconds"] <= t + 1e-9 for r, t in zip(timed, TIME))
    solutions = rows(path / "solutions.jsonl")
    assert objectives(fe[-1]["front"]) == objectives(x["objectives"] for x in solutions)
    assert read(path / "summary.json")["offlineValidationDecodes"] == len(solutions)
    if plan == "DEEP":
        assert actual == ledger(original)
        assert (path / "solutions.jsonl").read_bytes() == (original / "solutions.jsonl").read_bytes()
        assert [objectives(r["front"]) for r in fe] == [objectives(r["front"]) for r in rows(original / "anytime.jsonl")]
    observed = {"stage": stage, "visits": actual[-1][0], "slots": len(actual),
                "continuations": sum(s[5] for s in actual),
                "outerCompleted": search.get("generations.completed", search.get("deepLocal.completedBlocks", 0)),
                "searchSeconds": receipt["searchSeconds"], "wallSeconds": read(path / "process.json")["wallSeconds"],
                "offlineValidationDecodes": len(solutions), "decoder": receipt["decoder"]}
    write_once(path / "verified.json", observed)
    return fe, timed, observed


def analysis(all_runs, norm):
    lower, scale = np.asarray(norm["lower"]), np.asarray(norm["scale"])
    hv = lambda row, ref=1.5: float(hypervolume((np.asarray(row["front"]) - lower) / scale, (ref,) * 3))
    result = {}
    for field, cuts, pos in (("fixedFE", POINTS, 0), ("fixedTime", TIME, 1)):
        result[field] = []
        for i, cut in enumerate(cuts):
            a = {f"{p}-{k}": {"fe": pair[pos][i]["fe"], "hv": hv(pair[pos][i])}
                 for (p, k), pair in all_runs.items()}
            result[field].append({"cut": cut, "arms": a,
                "gapPct": {p: 100 * (a[f"{p}-SPECIAL"]["hv"] / a[f"{p}-NSGA"]["hv"] - 1)
                           for p in ("DEEP", "ROTATE", "ROLE")}})
    result["terminalSensitivityGapPct"] = {str(ref): {
        p: 100 * (hv(all_runs[(p, "SPECIAL")][0][-1], ref) / hv(all_runs[(p, "NSGA")][0][-1], ref) - 1)
        for p in ("DEEP", "ROTATE", "ROLE")} for ref in (1.25, 1.5, 2)}
    result["receipts"] = {f"{p}-{k}": r[2] for (p, k), r in all_runs.items()}
    return result


def main():
    root = ROOT / "runs" / time.strftime("pddr-role-budget-%Y%m%d-%H%M%S")
    root.mkdir()
    print("PDDR_ROLE_ROOT", root, flush=True)
    started, complete = time.monotonic(), []
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            cp = frozen_classpath()
            plans, calibration = design()
            norm = read(ANCHOR / "protocol.json")["normalization"]
            write_once(root / "calibration.json", calibration)
            for name, slots in plans.items():
                work = root / name
                work.mkdir()
                shutil.copytree(BRIDGE / "inputs", work / "inputs")
                write_ledger(work / "ledger.csv", slots)
            write_once(root / "protocol.json", {"instance": "20_2_3_1", "seed": SEED, "actualFEPerRun": CAP,
                "order": list(ORDER), "pddrFrozen": str(PDDR), "timeCutsSeconds": list(TIME), "normalization": norm,
                "calibration": "Prior first-cycle SPECIAL L_U paid archive; first quarter after which all later rates "
                               "are at most 25% of the best previous quarter, else no knee. L_S sensitivity only.",
                "DEEP": "Frozen original L_U ledger; 10,000 global FE", "ROTATE": "Four 5,000 global-FE cycles; equal "
                        "intra FE per entrant", "ROLE": "Same cycles/slot factories; role intra weight proportional "
                        "to historical FE to knee; largest remainder; equal per entrant within role",
                "commonNewPlan": "Per cycle 119,975 local FE, two inter FE per visit; frozen original first-cycle "
                                 "factory draws partitioned 8/8/7/7 per visit position; fixed role order",
                "ledgerSHA256": {n: sha256((root / n / "ledger.csv").read_bytes()).hexdigest() for n in plans},
                "scope": "One instance/seed, all six arms same actual FE. Compare capped time snapshots; no broad claims."})
            (root / "classpath.txt").write_text(cp, encoding="utf-8")
            for name in ("run_pddr_role_budget.py", "pddr_role_budget_plan.py"):
                shutil.copy2(Path(__file__).with_name(name), root)
            all_runs = {}
            for plan, algorithm in ORDER:
                print("PLAN", plan, flush=True)
                path = run(root / plan, cp, algorithm, "LINEAR")
                all_runs[(plan, algorithm)] = verify(path, algorithm, plan, plans[plan])
                complete.append(f"{plan}-{algorithm}")
            write_once(root / "comparison.json", analysis(all_runs, norm))
    except BaseException as error:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "completed": complete, "error": str(error)})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "completed": complete, "searchFE": len(ORDER) * CAP,
                                     "calibrationFE": 0, "wallSeconds": time.monotonic() - started})
    print("PDDR_ROLE_COMPLETE", root, flush=True)


if __name__ == "__main__":
    main()
