"""Isolate initial preference metadata, exact engineering replay and joint-indicator analysis."""
import shutil

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, hypervolume, igd_plus, nondominated
from pa_specialist_bridge_build import INTERFACE, replace_once
from pa_paid_donor_data import at
from pa_population_replay import analyze as replay
from research.dynamic_benchmark.tri_indicators import bidirectional_coverage
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes

ENGINE = ROOT / "runs/pa-population-engineering-20261105-164116-698339"
SOURCE = ROOT / "runs/linkage-mixing-probe-20261105-142116-487815"


def build(root):
    source, classes = root / "source", root / "classes"
    source.mkdir(); classes.mkdir()
    population = (INTERFACE / "source/PaPopulation.java").read_text("utf-8-sig")
    population = replace_once(population, "        population.add(point); observer.initial(",
                              "        point = PaPreferenceMode.initial(point);\n        population.add(point); observer.initial(")
    (source / "PaPopulation.java").write_text(population, encoding="utf-8")
    search = (INTERFACE / "source/PaCapabilitySearch.java").read_text("utf-8-sig")
    search = replace_once(search, '        if(population!=null)result.put("completeGenerations",population.completedGenerations); return result;',
                           '        if(population!=null) { result.put("completeGenerations",population.completedGenerations); result.putAll(PaPreferenceMode.diagnostics()); } return result;')
    (source / "PaCapabilitySearch.java").write_text(search, encoding="utf-8")
    for path in (ROOT / "src/algorithms/diagnostics/pa_role_acceptance").glob("*.java"):
        shutil.copy2(path, source / path.name)
    base = (INTERFACE / "classpath.txt").read_text("utf-8-sig").strip()
    execute(["java", "-version"], root / "jdk-version.log")
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", base, "-d", str(classes),
             *map(str, source.glob("*.java"))], root / "compile.log")
    cp = str(classes) + ";" + base
    (root / "classpath.txt").write_text(cp, encoding="utf-8")
    write_once(root / "source-hashes.json", {p.name: digest(p) for p in source.glob("*.java")})
    write_once(root / "class-hashes.json", class_hashes(classes))
    return cp


def native_case(root, cp, stem, mode):
    folder = root / stem / ("ENGINE-" + mode)
    out = folder / "audit"
    out.mkdir(parents=True)
    limit = 7900 if stem == "20_8_5_1" else 39900
    inp = root / stem / "inputs"
    files = [inp / (stem + ".txt"), inp / "RECONSTRUCTED-setup.txt", inp / "fatigue-input.txt",
             SOURCE / stem / "11730007/sources.tsv"]
    command = ["java", "-Xms32m", "-Xmx2g", "-Dresearch.snapshot.mode=ANCHOR", "-Dresearch.pa.traceIdentity=true",
               "-Dresearch.pa.preferenceMode=" + mode, "-cp", cp, "research.dynamic.PaPopulationRun",
               *map(str, files), str(out), "13630003", str(limit)]
    write_once(folder / "command.json", command)
    execute(command, folder / "run.log", timeout=600)
    result = replay(out)
    receipt, = rows(out / "receipt.jsonl")
    assert receipt["completedGenerations"] == 2 and receipt["failedFE"] == 0
    expected = {"CENTER": 100} if mode == "CENTER" else {"MAKESPAN": 15, "CENTER": 55, "ENERGY": 15, "WORKER_COST": 15}
    from collections import Counter
    assert dict(Counter(p["role"] for p in receipt["lastPopulation"])) == expected
    if mode == "FOUR":
        old, = rows(ROOT / "runs/pa-paid-donor-probe-20261106-001143-747475" / stem / "ENGINEERING-NONE/audit/receipt.jsonl")
        assert receipt["paidSHA256"] == old["paidSHA256"]
    return {"stem": stem, "mode": mode, "receipt": receipt, "independent": result}


def analyze(root, plan):
    results = []
    for spec in plan["instances"]:
        stem, norm = spec["stem"], spec["normalization"]
        raw = {(seed, name): np.asarray(at(root / stem / str(seed) / name, 50000)[0]["front"], float)
               for seed in plan["seeds"] for name in plan["methods"]}
        normalized = {key: (front - norm["lower"]) / norm["scale"] for key, front in raw.items()}
        reference = nondominated(np.vstack(list(normalized.values())))
        values = {key: {"seed": key[0], "method": key[1], "frontSize": len(front),
                        "HV": {str(r): hypervolume(front, (r,)*3) for r in (1.25, 1.5, 2.)},
                        "IGDplus": igd_plus(front, reference)} for key, front in normalized.items()}
        comparisons = []
        pairs = (("FOUR_JOINT", "CENTER_JOINT"), ("FOUR_RELABEL", "CENTER_RELABEL"),
                 ("FOUR_JOINT", "NSGA_DEEP"), ("FOUR_JOINT", "FOUR_RELABEL"))
        for a, b in pairs:
            observations = []
            for seed in plan["seeds"]:
                av, bv = values[seed, a], values[seed, b]
                hv = {r: 100 * (av["HV"][r] / bv["HV"][r] - 1) for r in av["HV"]}
                den = av["IGDplus"] + bv["IGDplus"]
                igd = 200 * (av["IGDplus"] - bv["IGDplus"]) / den if den else 0.
                observations.append({"seed": seed, "HVEffectPct": hv, "IGDplusSymmetricWorseningPct": igd,
                                     "coverage": bidirectional_coverage(raw[seed, a], raw[seed, b])})
            comparisons.append({"A": a, "B": b, "pairs": observations,
                                "medianHVEffectPct": {str(r): float(np.median([p["HVEffectPct"][str(r)] for p in observations])) for r in (1.25, 1.5, 2.)},
                                "medianIGDplusSymmetricWorseningPct": float(np.median([p["IGDplusSymmetricWorseningPct"] for p in observations])),
                                "medianC_A_B": float(np.median([p["coverage"]["C_A_B"] for p in observations])),
                                "medianC_B_A": float(np.median([p["coverage"]["C_B_A"] for p in observations]))})
        results.append({"stem": stem, "observations": list(values.values()), "comparisons": comparisons})
    return {"instances": results, "sameTimeProved": False, "goalAchieved": False}
