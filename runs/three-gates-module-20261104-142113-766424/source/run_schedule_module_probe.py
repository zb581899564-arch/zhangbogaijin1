"""All four-vector module exchanges for every NSGA-only terminal target. Paid diagnosis, not a new method."""
from datetime import datetime
from pathlib import Path
import shutil

import numpy as np

from audit_schedule_opportunity import ROOT, SOURCE, PRIOR, by_job, summarize_pair
from run_dynamic_deep_roles import BRIDGE
from run_long_budget_bridge import execute, hypervolume, nondominated, read, rows, write_once
from reverse_ledger_analysis import single_gains


def main():
    root = ROOT / "runs" / datetime.now().strftime("three-gates-module-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    print("MODULE_ROOT", root, flush=True)
    s, n = [rows(SOURCE / f"{a}-LINEAR/solutions.jsonl") for a in ("SPECIAL", "NSGA")]
    scale = np.asarray(read(PRIOR / "protocol.json")["normalization"]["scale"])
    sf, nf = [np.asarray([r["objectives"] for r in a]) / scale for a in (s, n)]
    covered = np.any(np.all(sf[:, None] <= nf[None, :], axis=2), axis=0)
    target = np.flatnonzero(~covered)
    write_once(root / "protocol.json", {"source": str(SOURCE), "targetCount": len(target),
              "method": "All 16 JS/FA/MA/WA module combinations, per-job aligned, for every NSGA endpoint not "
                        "weakly covered by SPECIAL; SPECIAL parent is nearest normalized objective neighbor.",
              "scope": "Uses oracle final NSGA donors for attribution, never feedback or an algorithm proposal.",
              "maxPaidFE": 16 * len(target), "allFullDecodes": True})
    lines, pairs = [], []
    for j in target:
        i = int(np.argmin(np.linalg.norm(sf - nf[j], axis=1)))
        pairs.append(summarize_pair(s[i], n[j], i, int(j)))
        genes = [by_job(r) for r in (s[i], n[j])]
        for mask in range(16):
            order = n[j]["JS"] if mask & 1 else s[i]["JS"]
            by = np.column_stack([genes[bool(mask & (1 << (q + 1)))][:, q] for q in range(3)])
            vectors = [order] + [by[order, q].tolist() for q in range(3)]
            lines.append("\t".join(map(str, [f"{j}:{mask}", *[x for v in vectors for x in v]])))
    (root / "cases.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_once(root / "pairs.json", pairs)
    cp = (ROOT / "runs/pddr-equivalence-20261104-081553-961399/classpath.txt").read_text(encoding="utf-8-sig").strip()
    src = root / "source"
    src.mkdir()
    classes = root / "classes"
    classes.mkdir()
    java = shutil.copy2(ROOT / "src/algorithms/diagnostics/ScheduleModuleProbe.java", src)
    shutil.copy2(Path(__file__), src)
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", cp, "-d", str(classes), str(java)], root / "compile.log")
    cmd = ["java", "-Xmx2g", "-cp", f"{classes};{cp}", "research.dynamic.ScheduleModuleProbe",
           str(BRIDGE / "inputs/20_2_3_1.txt"), str(BRIDGE / "inputs/RECONSTRUCTED-setup.txt"),
           str(BRIDGE / "inputs/fatigue-input.txt"), str(root / "cases.tsv"), str(root)]
    write_once(root / "command.json", cmd)
    execute(cmd, root / "run.log")
    receipt = read(root / "receipt.json")
    output = rows(root / "results.jsonl")
    assert receipt["attempted"] == receipt["successful"] == len(lines) == len(output)
    assert receipt["failed"] == 0
    keyed = {r["case"]: r for r in output}
    for pair in pairs:
        j = pair["nsgaIndex"]
        assert keyed[f"{j}:0"]["objectives"] == pair["specialObjectives"]
        assert keyed[f"{j}:15"]["objectives"] == pair["nsgaObjectives"]
        assert keyed[f"{j}:0"]["repairEdits"] == keyed[f"{j}:15"]["repairEdits"] == 0
    points = np.asarray([r["objectives"] for r in output]) / scale
    gains = single_gains(sf, points)
    reports = []
    for mask in range(16):
        indices = [i for i, r in enumerate(output) if int(r["case"].split(":")[1]) == mask]
        records = [output[i] for i in indices]
        repairs = [r["repairEdits"] for r in records]
        cmax_delta = [r["objectives"][0] / p["specialObjectives"][0] - 1 for r, p in zip(records, pairs)]
        reports.append({"mask": mask, "donorModules": [k for q, k in enumerate(("JS","FA","MA","WA")) if mask & (1 << q)],
                       "positiveHV": int(np.sum(gains[indices] > 1e-12)), "meanSingleGain": float(gains[indices].mean()),
                       "meanCmaxChange": float(np.mean(cmax_delta)), "medianCmaxChange": float(np.median(cmax_delta)),
                       "repairedCases": sum(x > 0 for x in repairs), "meanRepairEdits": float(np.mean(repairs))})
    write_once(root / "module-summary.json", reports)
    write_once(root / "status.json", {"status": "COMPLETE", "paidProbeFE": len(lines),
                                      "originalReplayChecks": 2 * len(target), "algorithmSearchStarted": False})
    for r in reports:
        print(r, flush=True)


if __name__ == "__main__":
    main()
