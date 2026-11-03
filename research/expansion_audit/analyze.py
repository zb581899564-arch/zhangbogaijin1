"""Audit frozen inputs, actual commands, costs and existing fronts; zero new FEs."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
from statistics import median

from research.dynamic_benchmark.io import csv_write
from .metrics import front_diagnostics, grid_hv

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)


def source_integrity(run):
    manifest = read(run / "source-manifest.json")
    changed, bad_snapshot = [], []
    for relative, expected in manifest.items():
        frozen, current = run / "source" / relative, ROOT / relative
        if hashlib.sha256(frozen.read_bytes()).hexdigest() != expected:
            bad_snapshot.append(relative)
        if not current.exists() or hashlib.sha256(current.read_bytes()).hexdigest() != expected:
            changed.append(relative)
    return {"sourceFiles": len(manifest), "invalidFrozenFiles": bad_snapshot,
            "currentDifferences": changed}


def load_runs(run, protocol):
    records = read(run / "analysis/initial/records.json")
    metric_index = {(r["instance"], r["seed"], r["variant"]): r for r in records}
    loaded = []
    for instance in protocol["instances"]:
        stem = instance["stem"]
        for seed in protocol["algorithm_seeds"]:
            for variant in protocol["variants"]:
                folder = run / "trials/initial" / stem / str(seed) / variant
                summary, command = read(folder / "summary.json"), read(folder / "command.json")
                assert summary["model"] == "dynamic-append-v1" and summary["incremental"]
                # A decode can finish after T and be rejected by the guard before
                # archive admission. These are paid interruptions, not free FEs.
                decoded = summary["decoder"]["dynamic.evaluations"]
                assert 0 <= decoded - summary["successful"] <= summary["timeInterruptedAttempts"]
                assert command[12:16] == [str(seed), str(instance["time_seconds"]), "1.0", "true"]
                inputs = run / "inputs" / stem
                assert [Path(p) for p in command[6:9]] == [inputs/(stem+".txt"), inputs/"RECONSTRUCTED-setup.txt", inputs/"fatigue-input.txt"]
                assert summary["seed"] == seed and summary["timeLimitSeconds"] == instance["time_seconds"]
                assert summary["failed"] == summary["timeInterruptedAttempts"]
                rows = [json.loads(line) for line in (folder / "anytime.jsonl").read_text().splitlines()]
                final = next(r for r in rows if r["checkpointKind"] == "TIME" and r["checkpoint"] == instance["time_seconds"])
                assert final["elapsedSeconds"] <= instance["time_seconds"]
                loaded.append({"instance": stem, "seed": seed, "variant": variant,
                               "scale": instance["normalization"]["scale"], "summary": summary,
                               "final": final["front"], "metric": metric_index[stem, seed, variant]})
    return loaded


def stage_row(run):
    s = run["summary"]
    search = s["search"]
    local = search.get("ordinaryVns", search)
    result = {k: run[k] for k in ["instance", "seed", "variant"]}
    stages = {"initialization": search.get("initialization.evaluations", 0),
              "global": search.get("global.evaluations", 0),
              "inter": local.get("inter.evaluations", 0), "intra": local.get("intra.evaluations", 0)}
    assert sum(stages.values()) == s["successful"]
    result.update(stages)
    result.update({"successfulFE": s["successful"], "searchSeconds": s["searchSeconds"],
                   "outerGenerations": search.get("generations.completed", search.get("generations", 0)),
                   "decodeSeconds": s["decoder"]["dynamic.decodeNanos"] / 1e9,
                   "cooperationSeconds": s.get("cooperation", {}).get("cooperationSeconds", 0),
                   "interAccepted": local.get("inter.accepted", 0), "intraAccepted": local.get("intra.accepted", 0),
                   "Q_updates": sum(search.get("qgs.g" + str(g) + ".updates", 0) for g in range(1, 5))})
    for action in range(3):
        result["Q_action" + str(action)] = sum(search.get(f"qgs.g{g}.action{action}", 0) for g in range(1, 5))
    return result


def summarize_stages(rows, variants):
    result = []
    for variant in variants:
        group = [row for row in rows if row["variant"] == variant]
        totals = {key: sum(row[key] for row in group) for key in group[0] if key not in ["instance", "seed", "variant"]}
        totals["variant"] = variant
        totals["medianOuterGenerations"] = median(row["outerGenerations"] for row in group)
        totals["FEPerSecond"] = totals["successfulFE"] / totals["searchSeconds"]
        totals["localFraction"] = (totals["inter"] + totals["intra"]) / totals["successfulFE"]
        totals["decodeTimeFraction"] = totals["decodeSeconds"] / totals["searchSeconds"]
        result.append(totals)
    return result


def audit_fronts(runs):
    import numpy as np
    lookup = {(r["instance"], r["seed"], r["variant"]): r for r in runs}
    differences, rows = [], []
    for run in runs:
        normalized = np.asarray(run["final"]) / np.asarray(run["scale"])
        for reference in [1.25, 1.5, 2.0]:
            expected = run["metric"]["hv"][str(reference)]
            differences.append(abs(grid_hv(normalized, reference) - expected))
        if run["variant"] not in ["BASELINE", "SYNC", "SHARE", "VALUE_SHARE"]:
            continue
        external = lookup[run["instance"], run["seed"], "NSGA2_4V"]
        detail = {k: run[k] for k in ["instance", "seed", "variant"]}
        detail.update(front_diagnostics(run["final"], external["final"], np.asarray(run["scale"])))
        rows.append(detail)
    assert max(differences) < 2e-12
    return rows, {"independentHVChecks": len(differences), "maximumAbsoluteHVDifference": max(differences)}


def main(run):
    protocol = read(run / "protocol.json")
    assert read(run / "final-status.json")["status"] == "SCREEN_COMPLETE"
    runs = load_runs(run, protocol)
    assert len(runs) == 270
    out = ROOT / "runs" / datetime.now().strftime("nsga-gap-audit-%Y%m%d-%H%M%S-%f")
    out.mkdir()
    stages = [stage_row(run) for run in runs]
    csv_write(out / "stage-runs.csv", stages)
    csv_write(out / "stage-summary.csv", summarize_stages(stages, protocol["variants"]))
    fronts, metrics = audit_fronts(runs)
    csv_write(out / "front-diagnostics.csv", fronts)
    save(out / "receipt.json", {"status": "passed", "sourceRun": str(run), "runsRead": len(runs),
         "newOptimizerRuns": 0, "newFE": 0, "integrity": source_integrity(run), **metrics})
    print(out, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    main(parser.parse_args().run.resolve())
