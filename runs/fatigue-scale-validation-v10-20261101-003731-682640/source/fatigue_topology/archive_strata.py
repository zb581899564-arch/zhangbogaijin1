"""Exploratory v1-only stratification, with no new decoder calls."""
from collections import defaultdict
from pathlib import Path
import json
import sys
import numpy as np
from .experiment import save


def run(archive, destination):
    def read(name):
        return [json.loads(line) for line in (archive / (name + ".jsonl")).read_text(encoding="utf-8").splitlines()]

    inputs = {(r["instance"], r["parent_seed"], r["profile"]): r for r in read("predictions")}
    indexed = defaultdict(list)
    weights = {"Cmax": [1, 0, 0], "TEC": [0, 1, 0], "TWC": [0, 0, 1], "balanced": [1/3]*3}
    for candidate in read("candidates"):
        k = candidate["instance"], candidate["parent_seed"], candidate["profile"]
        prediction = inputs[k]
        group = "later_graph_same" if candidate["later_topology_changed_ops"] == 0 else "later_topology_changed"
        for target, w in weights.items():
            actual = float(np.asarray(candidate["delta"]) @ (np.asarray(w) / prediction["parent_objectives"]))
            for method, scores in prediction["targets"][target]["scores"].items():
                indexed[target, group, method].append((scores[candidate["index"]], actual))
    rows = []
    for (target, group, method), items in indexed.items():
        predicted, actual = np.array(items).T
        denominator = np.abs(actual).sum()
        rows.append({"target": target, "group": group, "method": method, "candidates": len(items),
                     "mae": float(np.abs(predicted - actual).mean()),
                     "wape": float(np.abs(predicted - actual).sum() / denominator) if denominator > 1e-14 else None})
    output = {"scope": "exploratory archived v1 observations; not held-out/causal evidence",
              "source": str(archive.resolve()), "new_decodes": 0, "groups": rows}
    save(destination / "v1_exploratory_strata.json", output)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run(Path(sys.argv[1]), Path(sys.argv[2]))
