"""Append-only repair for v7's instance-seed/RNG-seed field collision."""
import json
from pathlib import Path
import shutil
from .records import read, save, encode


def repair(output):
    protocol = json.loads((output/"protocol.json").read_text(encoding="utf-8"))
    events = list(read(output/"events.jsonl"))
    rows = list(read(output/"controls.jsonl"))
    changes = []
    target = output/"controls.corrected.jsonl"
    with target.open("x", encoding="utf-8") as stream:
        for number, row in enumerate(rows, 1):
            mi = protocol["models"].index(row["model"])
            instance_seed = row["seed"]-20261127-1009*row["parent"]-mi*10000019
            assert instance_seed in protocol["seeds"]
            match = [e for e in events if e["jobs"] == row["jobs"] and e["seed"] == instance_seed
                     and row["parent"] in e["selected"]]
            assert len(match) == 1
            corrected = {**row, "seed": instance_seed, "rng_seed": row["seed"]}
            stream.write(json.dumps(corrected, ensure_ascii=False, default=encode, allow_nan=False)+"\n")
            changes.append({"line": number, "instance_seed": instance_seed, "rng_seed": row["seed"]})
    save(output/"seed_field_erratum.json", {"cause": "run_trial.seed RNG metadata overwrote instance identity.seed in controls JSON merge",
        "original_retained": "controls.jsonl", "corrected": target.name, "changes": changes,
        "validated": "RNG formula inversion and independent panel event membership for every row",
        "impact": "metadata only; numeric inputs/parents/evaluations/scalars/probabilities/counts and grouped summaries unchanged",
        "new_decoder_calls": 0})
    directory = output/"posthoc_source"
    directory.mkdir(exist_ok=True)
    for name in ("provenance.py", "controls.py", "checks/test_coordination.py"):
        destination = directory/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(__file__).parent/name, destination)
    print(f"SEED_ERRATUM {len(changes)} rows, original preserved", flush=True)


if __name__ == "__main__":
    import sys
    repair(Path(sys.argv[1]))
