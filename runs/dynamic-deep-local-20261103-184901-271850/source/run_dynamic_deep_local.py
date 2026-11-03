"""Isolated dynamic-fatigue diagnostic: current SHARE and a matched deep-local pair."""
import argparse
import csv
from datetime import datetime
import difflib
from pathlib import Path
import shutil
import time

import numpy as np

from run_long_budget_bridge import (
    FE, FROZEN, ROOT, SEED, STEM, controller_lock, execute, hypervolume, igd_plus,
    nondominated, objectives, read, rows, run_one, verify_frozen, write_once,
)
from run_paired_qgs_guidance import ANCHOR, BRIDGE, adapt_entry, adapt_local, replace


MAIN, RECORD, SHARE, NSGA = "current-share", "allocation-record", "deep-share", "deep-nsga"
FORMAL = (MAIN, SHARE, NSGA)
MODES = {label: "NSGA2_4V" if label == NSGA else "SHARE_JOB_ALIGNED"
         for label in (*FORMAL, RECORD)}
STAGES = ("initialization", "global", "inter", "intra")
PHASE_LIMIT = FE[-1]


def entry(source):
    source = replace(adapt_entry(source),
                     'if (!useStatic || !mode.equals("BASELINE")) throw new IllegalArgumentException("Static audit only");',
                     'if (useStatic || mode.equals("BASELINE")) throw new IllegalArgumentException("Dynamic deep-local audit only");')
    return replace(source, '        org.uma.jmetal.util.research.search.QgsLocalLedger.finish(out);',
                   '''        if (!"plain".equals(options.get(0)))
            org.uma.jmetal.util.research.search.QgsLocalLedger.finish(out);''')


def classic(source):
    source = replace(source, "    private OrdinaryVns vns;",
                     "    private OrdinaryVns vns;\n    private DeepLocalVisits deep;")
    source = replace(source, "import org.uma.jmetal.util.research.search.OrdinaryVns;",
                     "import org.uma.jmetal.util.research.search.OrdinaryVns;\n"
                     "import org.uma.jmetal.util.research.search.DeepLocalVisits;")
    source = replace(source, '''        started = true;
        for (int i = 0; i < ClassicConfig.POPULATION; i++) {
            checkpoint.run(); population.add(evaluate(problem.createSolution(), "initialization"));
        }''', '''        started = true;
        if (!"NSGA2_4V".equals(config.mode)) throw new IllegalStateException("Deep NSGA-II control only");
        deep = new DeepLocalVisits(problem, instance);
        for (int i = 0; i < ClassicConfig.POPULATION; i++) {
            checkpoint.run();
            PermutationSolution<Integer> initial = problem.createSolution();
            deep.prepareInitial(initial, i);
            population.add(evaluate(initial, "initialization"));
        }''')
    source = replace(source, '''            population = next.population; scores = next.scores;
            count("generations");''', '''            population = next.population; scores = next.scores;
            count("generations");
            if (deep.due(globalOffspring)) {
                List<PermutationSolution<Integer>> local = deep.improve(population);
                next = selection.environmental(ClassicTools.union(population, local), ClassicConfig.POPULATION);
                population = next.population; scores = next.scores;
            }''')
    return replace(source, '        result.put("externalArchive", "RunContext-independent");',
                   '        result.put("externalArchive", "RunContext-independent");\n'
                   '        if (deep != null) result.putAll(deep.diagnostics());')


def add_checkpoint(source):
    anchor = "                    offspring.add(local.improve(particle, preference, reference));"
    return replace(source, anchor, "                    guarded.checkpoint();\n" + anchor)


def build(root):
    source, entry_classes, deep_classes = (root / d for d in ("source", "entry-classes", "deep-classes"))
    for folder in (source, entry_classes, deep_classes):
        folder.mkdir()
    cp = (BRIDGE / "classpath.txt").read_text(encoding="utf-8-sig").strip()
    items = (
        (BRIDGE / "source/LongBudgetRun.java", entry),
        (ANCHOR / "source/LocalSearch.java", adapt_local),
        (FROZEN / "source/src/java/search/CanonicalHmopso.java", add_checkpoint),
        (FROZEN / "source/src/algorithms/classic/ClassicAlgorithm.java", classic),
    )
    files = []
    for path, patch in items:
        before = path.read_text(encoding="utf-8")
        after = patch(before)
        out = source / path.name
        out.write_text(after, encoding="utf-8")
        (source / (path.stem + ".diff")).write_text("".join(difflib.unified_diff(
            before.splitlines(True), after.splitlines(True), fromfile=str(path), tofile=path.name)), encoding="utf-8")
        files.append(str(out))
    for name in ("QgsLocalLedger.java", "DeepLocalVisits.java"):
        files.append(shutil.copy2(ROOT / "src/algorithms/diagnostics" / name, source / name))
    for name in (Path(__file__).name, "run_paired_qgs_guidance.py", "run_long_budget_bridge.py"):
        shutil.copy2(ROOT / "scripts" / name, source / name)
    javac = ["javac", "-encoding", "UTF-8", "--release", "8", "-cp"]
    execute([*javac, cp, "-d", str(deep_classes), *files[1:]], root / "deep-compile.log")
    execute([*javac, f"{deep_classes};{cp}", "-d", str(entry_classes), files[0]], root / "entry-compile.log")
    paths = {MAIN: f"{entry_classes};{cp}", "deep": f"{entry_classes};{deep_classes};{cp}"}
    write_once(root / "classpaths.json", paths)
    return paths


def folder(root, label):
    return root / label / "trials/fatigue" / MODES[label]


def run(root, label, cp):
    work = root / label
    shutil.copytree(BRIDGE / "inputs", work / "inputs")
    mode = {MAIN: "plain", RECORD: "record"}.get(label, "replay")
    ledger = str(folder(root, RECORD) / "local-ledger.csv") if mode == "replay" else "-"
    (work / "inputs/paired-audit.txt").write_text(f"{mode}\nQ\n{ledger}\n", encoding="utf-8")
    print("ARM", label, flush=True)
    return run_one(work, cp, "fatigue", MODES[label], FE)


def reuse_finished_arm(root, previous, label):
    """Keep complete arms from an output-only failure in the last comparator."""
    old = folder(previous, label)
    receipt, = rows(old / "run-receipt.jsonl")
    curve = rows(old / "anytime.jsonl")
    replayed = rows(old / "solutions.jsonl")
    summary = read(old / "summary.json")
    assert receipt["mode"] == MODES[label] and receipt["seed"] == SEED and receipt["stopReason"] == "FE_LIMIT"
    assert receipt["attempted"] == receipt["successful"] == PHASE_LIMIT and receipt["failed"] == 0
    assert [row["fe"] for row in curve] == list(FE) and all(row["reached"] for row in curve)
    assert len(replayed) == summary["archiveSize"] == summary["offlineValidationDecodes"]
    assert objectives(curve[-1]["front"]) == objectives(row["objectives"] for row in replayed)
    shutil.copytree(previous / label, root / label)
    return {"receipt": receipt, "curve": curve, "replays": len(replayed)}


def ledger(folder):
    with (folder / "local-ledger.csv").open(encoding="utf-8", newline="") as file:
        return [tuple(int(row[k]) for k in ("visit", "group", "round", "factory", "paid", "restarts"))
                for row in csv.DictReader(file)]


def validate(root, trials):
    initial = [(folder(root, label) / "initial-population.jsonl").read_bytes() for label in trials]
    assert len(initial[0].splitlines()) == 100 and all(genomes == initial[0] for genomes in initial)
    old = rows(BRIDGE / "trials/fatigue/SHARE_JOB_ALIGNED/anytime.jsonl")
    assert same_fronts(old, trials[MAIN]["curve"]), "Frozen current SHARE trace changed"
    assert same_fronts(trials[RECORD]["curve"], trials[SHARE]["curve"]), "Recorded SHARE replay drift"
    slots = ledger(folder(root, RECORD))
    summary = {}
    for label, trial in trials.items():
        receipt = trial["receipt"]
        search, dec = receipt["search"], receipt["decoder"]
        stage = {key: search[key + ".evaluations"] for key in STAGES}
        assert sum(stage.values()) == dec["dynamic.evaluations"] == PHASE_LIMIT
        assert dec["dynamic.recomputedOperations"] + dec["dynamic.reusedOperations"] == PHASE_LIMIT * 40
        counts = {"FE": stage, "decoder": dec, "offlineArchiveReplays": trial["replays"],
                  "searchSeconds": receipt["searchSeconds"],
                  "wallSeconds": read(folder(root, label) / "process.json")["wallSeconds"],
                  "globalGenerationsCompleted": search.get("generations"),
                  "completedOuterOrLocalBlocks": search.get(
                      "generations.completed", search.get("deepLocal.completedBlocks", 0))}
        if label != MAIN:
            current = ledger(folder(root, label))
            assert [r[:-1] for r in current] == [r[:-1] for r in slots], label
            assert sum(r[4] for r in current if r[2] < 0) == stage["inter"]
            assert sum(r[4] for r in current if r[2] >= 0) == stage["intra"]
            assert stage["global"] == 5000 * ((slots[-1][0] + 99) // 100) or (
                slots[-1][0] % 100 == 0 and 0 < stage["global"] - 5000 * (slots[-1][0] // 100) <= 5000)
            counts.update(visits=slots[-1][0], slots=len(slots), quotaContinuations=sum(r[-1] for r in current))
        summary[label] = counts
    assert summary[RECORD]["FE"] == summary[SHARE]["FE"] == summary[NSGA]["FE"]
    return summary


def same_fronts(left, right):
    return (len(left) == len(right) and
            all(a["fe"] == b["fe"] and objectives(a["front"]) == objectives(b["front"]) for a, b in zip(left, right)))


def comparison(trials, norm):
    lower, scale = np.asarray(norm["lower"]), np.asarray(norm["scale"])
    fronts = {label: [(np.asarray(p["front"]) - lower) / scale for p in trials[label]["curve"]] for label in FORMAL}
    reference = nondominated(np.concatenate([fronts[label][-1] for label in FORMAL]))
    result = []
    for i, fe in enumerate(FE):
        arm = {}
        for label in FORMAL:
            raw = np.asarray(trials[label]["curve"][i]["front"])
            f = fronts[label][i]
            arm[label] = {"HV": {str(r): float(hypervolume(f, (r,) * 3)) for r in (1.25, 1.5, 2.0)},
                          "IGDplus": float(igd_plus(f, reference)),
                          "archiveSize": len(f), "objectiveMinima": raw.min(axis=0).tolist()}
        def gains(a, b):
            return {r: 100 * (a["HV"][r] / b["HV"][r] - 1) if b["HV"][r] else None for r in a["HV"]}
        result.append({"FE": fe, "arms": arm,
                       "deepShare_vs_current_pct": gains(arm[SHARE], arm[MAIN]),
                       "deepShare_vs_deepNsga_pct": gains(arm[SHARE], arm[NSGA])})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reuse-prefix", type=Path, help="Preserved run with the final NSGA arm's terminal-guard error")
    previous = parser.parse_args().reuse_prefix
    if previous is not None:
        previous = previous.resolve(strict=True)
        if (previous.parent != ROOT / "runs" or
                "Too many local visits" not in read(previous / "status.json")["error"]):
            raise ValueError("Reuse is restricted to the retained terminal-guard failure")
    root = ROOT / "runs" / datetime.now().strftime("dynamic-deep-local-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    print("DEEP_LOCAL_ROOT", root, flush=True)
    start = time.monotonic()
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            verify_frozen(FROZEN)
            norm = read(BRIDGE / "protocol.json")["normalization"]
            protocol = {
                "instance": STEM, "seed": SEED, "FEPerTrial": PHASE_LIMIT, "checkpoints": list(FE),
                "formal": list(FORMAL), "allocationRun": RECORD,
                "inputs": str(BRIDGE / "inputs"), "localKernelSource": str(ANCHOR / "source/LocalSearch.java"),
                "decoder": "frozen dynamic-append-v1 with exact incremental decoder; no evaluation cache bypass",
                "matching": "Identical first 100 evaluated four vectors. Every 5000 global FE, 100 local visits with matched preference, "
                            "factory, per-round paid quotas; repeat a naturally exhausted pass until its quota is used.",
                "nsga": "Original 4V variation and NSGA-II selection; local preference slots only, no persistent families or sharing. "
                        "At each block retain NSGA-II selection from the union of pre-local survivors and local results.",
                "scope": "Single instance and seed, schedule frozen from deep SHARE allocation replay. Comparison of algorithm packages, "
                         "not a separate causal contrast for four swarms. Record wall time, not a wall-time-controlled race.",
                "normalization": norm, "HVReference": [1.5] * 3, "HVSensitivity": [1.25, 2.0],
                "IGDplusReference": "Nondominated union of the three formal terminal archives",
            }
            if previous is not None:
                assert protocol == read(previous / "protocol.json")
            write_once(root / "protocol.json", protocol)
            cp = build(root)
            if previous is not None:
                for name in ("LongBudgetRun.java", "LocalSearch.java", "CanonicalHmopso.java", "QgsLocalLedger.java"):
                    assert (root / "source" / name).read_bytes() == (previous / "source" / name).read_bytes()
                write_once(root / "reused-arms.json", {label: str(folder(previous, label)) for label in (MAIN, RECORD, SHARE)})
            trials = {}
            for label in (MAIN, RECORD, SHARE, NSGA):
                trials[label] = (reuse_finished_arm(root, previous, label) if previous is not None and label != NSGA
                                 else run(root, label, cp[MAIN if label == MAIN else "deep"]))
            write_once(root / "validation.json", validate(root, trials))
            write_once(root / "comparison.json", comparison(trials, norm))
    except BaseException as error:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": str(error),
                                         "wallSeconds": time.monotonic() - start})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "formalFE": PHASE_LIMIT * 3,
                                     "allocationFE": PHASE_LIMIT, "wallSeconds": time.monotonic() - start})
    print("DEEP_LOCAL_COMPLETE", root, flush=True)


if __name__ == "__main__":
    main()
