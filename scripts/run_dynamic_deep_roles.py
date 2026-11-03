"""Matched dynamic 500k-FE specialization ablation, with archive origin evidence."""
from bisect import bisect_left
from collections import Counter
import csv
from datetime import datetime
import difflib
from itertools import groupby
from pathlib import Path
import shutil
import time

import numpy as np

from run_dynamic_deep_local import BRIDGE, FE, FROZEN, ROOT, SEED, STEM, STAGES, ledger
from run_long_budget_bridge import (
    c_coverage, controller_lock, execute, hypervolume, igd_plus, nondominated,
    objectives, read, rows, run_one, verify_frozen, write_once,
)
from run_paired_qgs_guidance import replace


ANCHOR = ROOT / "runs/dynamic-deep-local-20261103-184901-271850"
MODES = {"SPECIAL": "SHARE_JOB_ALIGNED", "UNIFORM": "SHARE_JOB_ALIGNED_UNIFORM"}
REFERENCE = ANCHOR / "deep-share/trials/fatigue/SHARE_JOB_ALIGNED"
PRIOR_NSGA = ANCHOR / "deep-nsga/trials/fatigue/NSGA2_4V"
ROLES = ("MAKESPAN", "CENTER", "ENERGY", "WORKER_COST")
GROUP_SIZES = (15, 55, 15, 15)


def adapt_entry(source):
    source = replace(source, '''        if (!mode.equals("BASELINE") && !mode.equals("NSGA2_4V")
                && !(mode.equals("SHARE_JOB_ALIGNED") && !useStatic))''',
                     '''        if (useStatic || (!mode.equals("SHARE_JOB_ALIGNED")
                && !mode.equals("SHARE_JOB_ALIGNED_UNIFORM")))''')
    source = replace(source, '        if (useStatic || mode.equals("BASELINE")) throw new IllegalArgumentException("Dynamic deep-local audit only");\n', "")
    source = replace(source, "        List<String> initial = new java.util.ArrayList<>();",
                     '''        List<String> initial = new java.util.ArrayList<>();
        List<String> admissions = new java.util.ArrayList<>();
        admissions.add("fe,cmax,tec,twc");''')
    source = replace(source, "                if (paid <= 100) {",
                     '''                if (changed)
                    admissions.add(paid + "," + s.getObjective(0) + "," + s.getObjective(1) + "," + s.getObjective(2));
                if (paid <= 100) {''')
    return replace(source, "        List<PermutationSolution<Integer>> results = context.result();",
                   '''        receipt.put("cooperation", search.cooperation.diagnostics());
        Files.write(out.resolve("archive-admissions.csv"), admissions, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        List<PermutationSolution<Integer>> results = context.result();''')


def adapt_local(source):
    # A ledger slot belongs to a physical subgroup, even when its preference is CENTER.
    source = replace(source, "ledger.inter(direction.id())", "ledger.inter(state.ledgerGroup(direction))")
    return replace(source, "ledger.round(direction.id(), round, factory)",
                   "ledger.round(state.ledgerGroup(direction), round, factory)")


def adapt_state(source):
    anchor = "    void observationGroup(Direction group) { observationGroup = group; }"
    return replace(source, anchor, anchor + '''
    int ledgerGroup(Direction preference) {
        return (observationGroup == null ? preference : observationGroup).id();
    }''')


def build(root):
    source, classes = root / "source", root / "classes"
    source.mkdir()
    classes.mkdir()
    base = read(ANCHOR / "classpaths.json")["deep"]
    items = ((ANCHOR / "source/LongBudgetRun.java", adapt_entry),
             (ANCHOR / "source/LocalSearch.java", adapt_local),
             (FROZEN / "source/src/java/search/SearchState.java", adapt_state))
    files = []
    for path, patch in items:
        original = path.read_text(encoding="utf-8")
        result = patch(original)
        out = source / path.name
        out.write_text(result, encoding="utf-8")
        (source / (path.stem + ".diff")).write_text("".join(difflib.unified_diff(
            original.splitlines(True), result.splitlines(True), fromfile=str(path), tofile=path.name)), encoding="utf-8")
        files.append(str(out))
    shutil.copy2(Path(__file__), source / Path(__file__).name)
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", base,
             "-d", str(classes), *files], root / "compile.log")
    cp = f"{classes};{base}"
    (root / "classpath.txt").write_text(cp, encoding="utf-8")
    return cp


def phase_schedule(slots):
    phases = [{"phase": "init", "start": 0, "end": 100}]

    def add(name, paid):
        start = phases[-1]["end"]
        phases.append({"phase": name, "start": start, "end": start + paid})

    for block, round_slots in groupby(slots, key=lambda r: (r[0] - 1) // 100 + 1):
        for role, size in zip(ROLES, GROUP_SIZES):
            add(f"g{block}.{role}", 50 * size)
        for group, part in groupby(round_slots, key=lambda r: r[1]):
            add(f"l{block}.{ROLES[group - 1]}", sum(r[4] for r in part))
    assert phases[-1]["end"] == FE[-1]
    return phases


def trial_folder(root, label):
    return root / label / "trials/fatigue" / MODES[label]


def trial(root, label, cp, points):
    work = root / label
    shutil.copytree(BRIDGE / "inputs", work / "inputs")
    (work / "inputs/paired-audit.txt").write_text(
        f"replay\nQ\n{REFERENCE / 'local-ledger.csv'}\n", encoding="utf-8")
    return run_one(work, cp, "fatigue", MODES[label], points)


def admission_points(folder):
    with (folder / "archive-admissions.csv").open(encoding="utf-8", newline="") as file:
        rows_ = list(csv.DictReader(file))
    return {tuple(float(row[key]) for key in ("cmax", "tec", "twc")): int(row["fe"]) for row in rows_}


def validate(root, trials, slots):
    previous_curve = rows(REFERENCE / "anytime.jsonl")
    previous_init = (REFERENCE / "initial-population.jsonl").read_bytes()
    assert len(previous_init.splitlines()) == 100
    expected = read(ANCHOR / "validation.json")["deep-share"]["FE"]
    report, origins = {}, {}
    for label, result in trials.items():
        folder = trial_folder(root, label)
        receipt = result["receipt"]
        search, decoder, coop = (receipt[key] for key in ("search", "decoder", "cooperation"))
        stage = {s: search[s + ".evaluations"] for s in STAGES}
        assert stage == expected and sum(stage.values()) == decoder["dynamic.evaluations"] == FE[-1]
        assert decoder["dynamic.recomputedOperations"] + decoder["dynamic.reusedOperations"] == 40 * FE[-1]
        assert (folder / "initial-population.jsonl").read_bytes() == previous_init
        actual = ledger(folder)
        assert [r[:-1] for r in actual] == [r[:-1] for r in slots]
        assert coop["sharing"] and coop["targetSpecialization"] == (label == "SPECIAL")
        assert coop["rolePreferenceMap"] == {role: role if label == "SPECIAL" else "CENTER" for role in ROLES}
        assert coop["globalOrder"] == ",".join(ROLES)
        assert all(search[f"qgs.g{i}.updates"] == 100 for i in range(1, 5))
        assert coop["assembliesValidated"] + search["alignedKernelProposals"] == stage["global"]
        origins[label] = admission_points(folder)
        for row in result["curve"]:
            replay = nondominated([p for p, paid in origins[label].items() if paid <= row["fe"]])
            assert objectives(replay) == objectives(row["front"]), (label, row["fe"])
        report[label] = {"FE": stage, "decoder": decoder, "cooperation": coop, "configuration": receipt["configuration"],
                         "quotaContinuations": sum(r[-1] for r in actual), "archiveAdmissions": len(origins[label]),
                         "offlineArchiveReplays": result["replays"],
                         "searchSeconds": receipt["searchSeconds"],
                         "wallSeconds": read(folder / "process.json")["wallSeconds"]}
    by_fe = {row["fe"]: objectives(row["front"]) for row in trials["SPECIAL"]["curve"]}
    assert all(by_fe[row["fe"]] == objectives(row["front"]) for row in previous_curve)
    return report, origins


def compare(trials, origins, phases, norm):
    lower, scale = np.asarray(norm["lower"]), np.asarray(norm["scale"])
    normed = lambda front: (np.asarray(front) - lower) / scale
    hv = lambda front, r=1.5: float(hypervolume(front, (r,) * 3))
    curves = {label: {row["fe"]: row["front"] for row in r["curve"]} for label, r in trials.items()}
    nsga = {row["fe"]: row["front"] for row in rows(PRIOR_NSGA / "anytime.jsonl")}
    reference = nondominated(np.concatenate([normed(c[FE[-1]]) for c in curves.values()]))
    ends = [phase["end"] for phase in phases]
    result = []
    for fe, raw_special in curves["SPECIAL"].items():
        raw = {"SPECIAL": raw_special, "UNIFORM": curves["UNIFORM"][fe]}
        arms = {}
        for label, points in raw.items():
            front = normed(points)
            cohorts = Counter(phases[bisect_left(ends, origins[label][p])]["phase"] for p in objectives(points))
            arms[label] = {"HV": {str(r): hv(front, r) for r in (1.25, 1.5, 2.0)},
                           "IGDplus": float(igd_plus(front, reference)), "objectiveMinima": np.min(points, axis=0).tolist(),
                           "archiveSize": len(front), "originCounts": dict(sorted(cohorts.items()))}
        s, u = (arms[label]["HV"]["1.5"] for label in MODES)
        row = {"FE": fe, "phase": phases[bisect_left(ends, fe)]["phase"], "arms": arms,
               "specialMinusUniformHV": s - u, "special_vs_uniform_pct": 100 * (s / u - 1),
               "cSpecialUniform": c_coverage(raw["SPECIAL"], raw["UNIFORM"]),
               "cUniformSpecial": c_coverage(raw["UNIFORM"], raw["SPECIAL"])}
        if fe in nsga:
            h = hv(normed(nsga[fe]))
            row.update(priorNsgaHV=h, special_vs_prior_nsga_pct=100 * (s / h - 1),
                       uniform_vs_prior_nsga_pct=100 * (u / h - 1))
        result.append(row)
    indexed = {row["FE"]: row["specialMinusUniformHV"] for row in result}
    phase_gain = [dict(p, gapDelta=indexed[p["end"]] - indexed.get(p["start"], 0.0)) for p in phases]
    return result, phase_gain


def main():
    root = ROOT / "runs" / datetime.now().strftime("dynamic-deep-roles-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    print("DEEP_ROLES_ROOT", root, flush=True)
    start = time.monotonic()
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            verify_frozen(FROZEN)
            slots = ledger(REFERENCE)
            phases = phase_schedule(slots)
            points = sorted({*FE, *(phase["end"] for phase in phases), 240000, 245000, 255000, 260000})
            norm = read(ANCHOR / "protocol.json")["normalization"]
            write_once(root / "protocol.json", {
                "instance": STEM, "seed": SEED, "FEPerTrial": FE[-1], "modes": MODES,
                "allocation": str(REFERENCE / "local-ledger.csv"), "checkpoints": points, "phases": phases,
                "normalization": norm, "HVReference": [1.5] * 3, "HVSensitivity": [1.25, 2.0],
                "IGDplusReference": "Nondominated union of the two formal terminal archives",
                "comparison": "Only the registered objective-role switch changes. Both retain four physical subgroups, "
                              "independent QGS tables, fixed families, sharing and per-slot local FE and factories.",
                "scope": "Joint effect of objective roles across grouping, guidance, reward and local selection. "
                         "One seed on frozen SPECIAL quotas, not an isolated component effect within a particular stage.",
                "contextComparator": str(PRIOR_NSGA), "contextComparatorNewFE": 0,
            })
            cp = build(root)
            trials = {label: trial(root, label, cp, points) for label in MODES}
            report, origins = validate(root, trials, slots)
            comparisons, phase_gain = compare(trials, origins, phases, norm)
            write_once(root / "validation.json", report)
            write_once(root / "comparison.json", comparisons)
            write_once(root / "phase-gaps.json", phase_gain)
    except BaseException as error:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": str(error),
                                         "wallSeconds": time.monotonic() - start})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "formalFE": 2 * FE[-1],
                                     "wallSeconds": time.monotonic() - start})
    print("DEEP_ROLES_COMPLETE", root, flush=True)


if __name__ == "__main__":
    main()
