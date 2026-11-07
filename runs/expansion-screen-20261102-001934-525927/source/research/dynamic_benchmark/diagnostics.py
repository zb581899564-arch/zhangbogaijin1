"""Expose paid direction/cohort counts from existing summaries; no new evaluations."""
from pathlib import Path
import sys
from .io import load, csv_write


def export(root):
    rows = []
    ids = {"MAKESPAN":1, "CENTER":2, "ENERGY":3, "WORKER_COST":4}
    for file in sorted((root / "trials").glob("*/*/*/*/summary.json")):
        summary = load(file)
        joint = summary.get("joint")
        if joint is None:
            continue
        instance, budget, seed, variant = file.parts[-5:-1]
        heads = joint["perDirection"]
        if sum(head["completedTrajectories"] for head in heads.values()) != joint["completedTrajectories"]:
            raise ValueError("Trajectory head accounting mismatch: " + str(file))
        for direction, head in heads.items():
            group = str(ids[direction])
            rows.append({"instance":instance, "budget":budget, "seed":seed, "variant":variant,
                         "direction":direction, "globalFE":summary["search"].get("global.g"+group+".evaluations", 0),
                         "qgsUpdates":summary["search"].get("qgs.g"+group+".updates", 0), **head})
    csv_write(root / "analysis/direction-diagnostics.csv", rows)
    print("DIRECTION_ACCOUNTING_PASS", len(rows), "rows; existing successful trajectories only")


if __name__ == "__main__":
    export(Path(sys.argv[1]).resolve())
