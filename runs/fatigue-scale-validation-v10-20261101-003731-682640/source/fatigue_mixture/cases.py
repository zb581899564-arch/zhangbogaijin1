"""Reused development tables and genuinely new prespecified confirmation inputs."""
import json
import shutil
from time import perf_counter_ns
import numpy as np
from research.fatigue_coordination.instances import make_instance, parameters, instance_record
from research.fatigue_coordination.census import evaluate
from research.fatigue_coordination.analysis import analyze
from research.fatigue_coordination.records import encode
from .protocol import PROTOCOL
from .records import save


def configurations():
    for split in ("development", "confirmation"):
        for seed in PROTOCOL[split+"_seeds"]:
            yield {"split": split, "jobs": 4, "instance_seed": seed}


def load(project, output, graph, identity, records, counts):
    seed = identity["instance_seed"]
    directory = output/f"N4-seed{seed}"
    directory.mkdir()
    instance = make_instance(4, seed)
    params, metadata = parameters(instance, seed)
    if identity["split"] == "development":
        prior = project/"runs"/PROTOCOL["prior_run"]/directory.name
        for name in ("instance.json", "fatigue.json", "physical_tables.npz"):
            shutil.copyfile(prior/name, directory/name)
        assert json.loads((directory/"instance.json").read_text(encoding="utf-8")) == instance_record(instance)
        assert json.loads((directory/"fatigue.json").read_text(encoding="utf-8")) == json.loads(json.dumps(metadata, default=encode))
        with np.load(directory/"physical_tables.npz") as data:
            tables, reference = data["objectives"], data["reference"]
        counts["reused_census_rows"] += tables.shape[0]*tables.shape[1]
    else:
        save(directory/"instance.json", instance_record(instance))
        save(directory/"fatigue.json", metadata)
        tables, _, _, reference = evaluate(instance, params, graph.space, directory, records, counts,
                                           {"jobs": 4, "seed": seed, "split": "confirmation"})
    started = perf_counter_ns()
    analyses = [analyze(graph, tables[mi, :, 1]/reference[1], 1e-10) for mi in range(3)]
    for mi, model in enumerate(PROTOCOL["models"]):
        np.savez_compressed(directory/(model+"_TEC_landscape.npz"),
                            **{k: v for k, v in analyses[mi].items() if k != "summary"})
        records.emit("events", {**identity, "event": "TEC_landscape", "model": model, **analyses[mi]["summary"]})
    counts["landscape_ns"] += perf_counter_ns()-started
    return instance, params, tables, reference, analyses


def parents(graph, analyses, identity):
    rng = np.random.default_rng(PROTOCOL["panel_seed"]+identity["instance_seed"]+1000003*identity["jobs"])
    eligible = np.flatnonzero(np.logical_or.reduce([a["strict"] for a in analyses]))
    source = eligible if len(eligible) else np.arange(graph.space.size)
    return (("barrier" if len(eligible) else "barrier_fallback", int(rng.choice(source))),
            ("uniform", int(rng.integers(graph.space.size))))
