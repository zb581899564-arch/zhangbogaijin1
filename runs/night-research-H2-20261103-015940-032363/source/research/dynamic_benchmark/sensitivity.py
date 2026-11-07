"""Post-hoc reference-point sensitivity; never replaces the frozen primary HV results."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
from .io import load, dump
from .metrics import hypervolume


def deadline_fronts(root, protocol):
    records = []
    for inst in protocol["instances"]:
        scale = np.asarray(inst["normalization"]["scale"])
        for budget in ["FE", "TIME"]:
            for seed in protocol["seeds"]:
                for variant in protocol["coreVariants"] + protocol["cooperationVariants"]:
                    file = root / "trials" / inst["stem"] / budget / str(seed) / variant / "anytime.jsonl"
                    last = json.loads(file.read_text(encoding="utf-8").splitlines()[-1])
                    records.append({"instance":inst["stem"], "budget":budget, "seed":seed,
                                    "variant":variant, "front":np.asarray(last["front"]) / scale})
    return records


def summarize(frame):
    rows = []
    for point in [1.25, 1.5]:
        for budget in ["FE", "TIME"]:
            table = frame[(frame.reference == point) & (frame.budget == budget)].groupby(["instance", "variant"]).HV.mean().unstack()
            pairs = [("VALUE","BASELINE"), ("VALUE","TAIL"), ("SHARE","BASELINE"),
                     ("SHARE","SYNC"), ("VALUE_SHARE","SHARE"), ("VALUE_SHARE","VALUE_SYNC")]
            for first, second in pairs:
                delta = table[first] - table[second]
                rows.append({"reference":point, "budget":budget, "comparison":first + " - " + second,
                             "meanDelta":float(delta.mean()), "meanRelativePercent":float((100*(table[first]/table[second]-1)).mean()),
                             "wins":int((delta > 0).sum()), "losses":int((delta < 0).sum())})
    return rows


def main(root):
    records = deadline_fronts(root, load(root / "protocol.json"))
    rows = []
    for point in [1.25, 1.5]:
        for record in records:
            prefix = {k:record[k] for k in ["instance","budget","seed","variant"]}
            rows.append({**prefix, "reference":point, "HV":hypervolume(record["front"], [point]*3),
                         "outsideReference":int(np.any(record["front"] >= point, axis=1).sum())})
    frame = pd.DataFrame(rows)
    frame.to_csv(root / "analysis/reference-sensitivity-runs.csv", index=False, encoding="utf-8-sig")
    result = {"classification":"POST_HOC_SENSITIVITY_ONLY", "primaryReferenceUnchanged":[1.1]*3,
              "reason":"1541 largest-instance frontier points outside frozen reference box; no new search or tuning",
              "comparisons":summarize(frame),
              "outsideCounts":{str(v):int(frame[frame.reference == v].outsideReference.sum()) for v in [1.25,1.5]}}
    dump(root / "analysis/reference-sensitivity.json", result)


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
