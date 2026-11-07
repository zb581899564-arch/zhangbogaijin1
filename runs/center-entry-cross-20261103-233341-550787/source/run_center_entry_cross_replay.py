"""Isolated 2x2 CENTER replay on accepted reverse-ledger entrance states."""
from datetime import datetime
import difflib
from hashlib import sha256
import json
from pathlib import Path
import shutil
import struct
import subprocess
import time

import numpy as np

from reverse_ledger_analysis import archive_admissions
from run_dynamic_reverse_ledger_audit import MODES, ROOT, SEED, STEM, trial_folder
from run_dynamic_deep_roles import BRIDGE, ledger
from run_long_budget_bridge import controller_lock, execute, hypervolume, nondominated, objectives, read, rows, run_one, write_once
from run_paired_qgs_guidance import replace


ANCHOR = ROOT / "runs/dynamic-reverse-ledger-20261103-231754-095093"
BASE_CHECKS = (100, 5100, 15000, 50000, 70132, 100000, 250000, 309927)
ENTRY_FE, END_FE = 70132, 309927
SOURCES = {"S": "SPECIAL", "U": "UNIFORM"}
CELLS = ("UU", "US", "SU", "SS")  # validate the original UNIFORM pair before running crosses
HOOK = "org.uma.jmetal.util.research.search.CenterEntryTrace"


def capture_entry(source):
    source = replace(source, "        ReverseClassOrigins.write(out);",
                     '        System.setProperty("research.center.capture", out.toString());\n        ReverseClassOrigins.write(out);')
    source = replace(source, "                evidence.paid((PermutationSolution<?>) s, paid, changed, archive);",
                     f"                evidence.paid((PermutationSolution<?>) s, paid, changed, archive);\n"
                     f"                {HOOK}.paid((PermutationSolution<?>) s, paid);")
    return replace(source, "    private static EDHHFSPW load(", "    static EDHHFSPW load(")


def capture_swarm(source):
    source = replace(source, '''                    if (direction == Direction.CENTER)
                        ReverseAudit.run().phase("center-entry", updated.get(Direction.CENTER), reference);''',
                     '''                    if (direction == Direction.CENTER) {
                        ReverseAudit.run().phase("center-entry", updated.get(Direction.CENTER), reference);
                        CenterEntryTrace.capture(updated.get(Direction.CENTER), reference);
                    }''')
    source = replace(source, "                        offspring.add(local.improve(particle, preference, reference));",
                     '''                        Particle improved = local.improve(particle, preference, reference);
                        offspring.add(improved);
                        if (direction == Direction.CENTER) CenterEntryTrace.retained(improved);''')
    return replace(source, "                    if (direction == Direction.MAKESPAN)\n",
                   "                    if (direction == Direction.CENTER) CenterEntryTrace.finish();\n"
                   "                    if (direction == Direction.MAKESPAN)\n")


def capture_local(source):
    source = replace(source, "        QgsLocalLedger.Slot slot = ledger.inter(state.ledgerGroup(direction));",
                     "        CenterEntryTrace.slot(state.ledgerGroup(direction), -1);\n"
                     "        QgsLocalLedger.Slot slot = ledger.inter(state.ledgerGroup(direction));")
    source = replace(source, "                state.checkLocalSlot();",
                     "                state.checkLocalSlot();\n                CenterEntryTrace.slot(state.ledgerGroup(direction), round);")
    assert source.count("ReverseAudit.run().better(") == 3
    return source.replace("ReverseAudit.run().better(", "CenterEntryTrace.better(")


def build(root):
    source, classes = root / "source", root / "classes"
    source.mkdir()
    classes.mkdir()
    base = (ANCHOR / "classpath.txt").read_text(encoding="utf-8-sig").strip()
    changes = (
        (ANCHOR / "source/LongBudgetRun.java", capture_entry),
        (ANCHOR / "source/CanonicalHmopso.java", capture_swarm),
        (ANCHOR / "source/LocalSearch.java", capture_local),
        (ANCHOR / "source/Particle.java", lambda s: replace(
            s, "final class Particle {", "final class Particle implements java.io.Serializable {\n"
            "    private static final long serialVersionUID = 1L;")),
        (ROOT / "runs/night-research-H1-20261103-010138-848045/source/src/java/runtime/SeededRandom.java",
         lambda s: replace(s, "    public static long seed()", """    public static void restoreForCenterReplay(Random state) {
        current();
        random = java.util.Objects.requireNonNull(state);
    }
    public static long seed()""")),
    )
    files = []
    for prior, patch in changes:
        before = prior.read_text(encoding="utf-8")
        after = patch(before)
        target = source / prior.name
        target.write_text(after, encoding="utf-8")
        (source / f"{target.stem}.diff").write_text("".join(difflib.unified_diff(
            before.splitlines(True), after.splitlines(True), fromfile=str(prior), tofile=target.name)), encoding="utf-8")
        files.append(str(target))
    for name in ("CenterEntryTrace", "CenterReferenceProbe", "FrozenCenterSupport", "CenterCrossSearch", "CenterCrossRun"):
        files.append(shutil.copy2(ROOT / f"src/algorithms/diagnostics/{name}.java", source / f"{name}.java"))
    shutil.copy2(Path(__file__), source / Path(__file__).name)
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", base,
             "-d", str(classes), *files], root / "compile.log")
    cp = f"{classes};{base}"
    (root / "classpath.txt").write_text(cp, encoding="utf-8")
    return cp


def write_ledger(path, slots):
    with path.open("x", encoding="utf-8") as f:
        f.write("visit,group,round,factory,paid,restarts\n")
        for row in slots:
            f.write(",".join(map(str, row)) + "\n")


def phase_ledgers(root):
    original = ledger(trial_folder(ANCHOR, "U_RECORD"))
    prefix = [s for s in original if s[0] <= 70]
    prior = [s for s in prefix if s[0] <= 15]
    center = [(s[0] - 15, *s[1:-1], 0) for s in prefix if s[0] > 15]
    assert sum(s[4] for s in prior) + 5100 == ENTRY_FE
    assert all(s[1] == 2 for s in center) and center[-1][0] == 55
    assert sum(s[4] for s in center) == END_FE - ENTRY_FE
    write_ledger(root / "capture-prefix-ledger.csv", prefix)
    write_ledger(root / "shared-center-ledger.csv", center)
    return prefix, center


def genome_hash(points):
    h = sha256()
    for s in points:
        for name in ("JS", "FA", "MA", "WA"):
            v = s["genome"][name]
            h.update(struct.pack(">" + "i" * (len(v) + 1), len(v), *v))
        h.update(struct.pack(">ddd", *s["objectives"]))
    return h.hexdigest()


def capture(root, label, cp, prefix):
    mode = MODES[SOURCES[label]]
    work = root / f"capture-{label}"
    shutil.copytree(BRIDGE / "inputs", work / "inputs")
    (work / "inputs/paired-audit.txt").write_text(f"replay\nQ\n{root / 'capture-prefix-ledger.csv'}\n", encoding="utf-8")
    print("CAPTURE", label, flush=True)
    result = run_one(work, cp, "fatigue", mode, BASE_CHECKS)
    folder = work / "trials/fatigue" / mode
    prior = trial_folder(ANCHOR, SOURCES[label])
    assert (folder / "initial-population.jsonl").read_bytes() == (prior / "initial-population.jsonl").read_bytes()
    assert [s[:-1] for s in ledger(folder)] == [s[:-1] for s in prefix]
    assert (folder / "center-entry.jsonl").read_bytes() == (prior / "center-entry.jsonl").read_bytes()
    admission_prefix = [r for r in archive_admissions(prior) if r[0] <= END_FE]
    assert archive_admissions(folder) == admission_prefix
    entry, = rows(folder / "entry.jsonl")
    phase = rows(folder / "center-entry.jsonl")[-1]
    assert entry["paidFE"] == ENTRY_FE and len(entry["center"]) == 55 and len(entry["reference"]) == 100
    assert genome_hash(entry["center"]) == phase["centerSHA256"]
    assert genome_hash(entry["reference"]) == phase["referenceSHA256"]
    assert all(0 < x["paid"] <= ENTRY_FE for key in ("center", "reference") for x in entry[key])
    assert objectives(entry["background"]) == objectives(nondominated([p for t, p in admission_prefix if t <= ENTRY_FE]))
    assert result["receipt"]["decoder"]["dynamic.evaluations"] == END_FE
    return folder, entry


def file_sha(path):
    return sha256(path.read_bytes()).hexdigest()


def replay(root, label, cp, captures, slots):
    print("REPLAY", label, flush=True)
    out = root / label
    out.mkdir()
    inputs = captures["U"][0].parents[2] / "inputs"
    files = [captures[x][0] / "entry.bin" for x in (*label, "S" if label[1] == "U" else "U")]
    rng = captures["U"][0] / "rng-slots.bin"
    cmd = ["java", "-Xms32m", "-Xmx2g", "-cp", cp, "research.dynamic.CenterCrossRun",
           str(inputs / f"{STEM}.txt"), str(inputs / "RECONSTRUCTED-setup.txt"),
           str(inputs / "fatigue-input.txt"), str(out), str(root / "shared-center-ledger.csv"),
           *map(str, files), str(rng), str(END_FE - ENTRY_FE), str(SEED)]
    write_once(out / "command.json", cmd)
    started = time.monotonic()
    code = None
    try:
        with (out / "run.log").open("x", encoding="utf-8") as log:
            code = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=600).returncode
    finally:
        write_once(out / "process.json", {"returnCode": code, "wallSeconds": time.monotonic() - started})
    if code != 0:
        raise RuntimeError((out / "run.log").read_text(encoding="utf-8", errors="replace")[-3500:])
    receipt, = rows(out / "run-receipt.jsonl")
    trace, = rows(out / "center-trace.jsonl")
    endpoints, admitted = rows(out / "endpoints.jsonl"), rows(out / "admissions.jsonl")
    actual = ledger(out)
    assert [r[:-1] for r in actual] == [r[:-1] for r in slots]
    limit = END_FE - ENTRY_FE
    dec = receipt["decoder"]
    assert receipt["attempted"] == receipt["successful"] == dec["dynamic.evaluations"] == trace["paidFE"] == limit
    assert receipt["failed"] == 0 and receipt["stopReason"] == "FE_LIMIT" and receipt["seed"] == SEED
    assert dec["dynamic.recomputedOperations"] + dec["dynamic.reusedOperations"] == limit * 40
    assert receipt["search"]["inter.evaluations"] == sum(s[4] for s in slots if s[2] < 0)
    assert receipt["search"]["intra.evaluations"] == sum(s[4] for s in slots if s[2] >= 0)
    assert len(endpoints) == 55 and endpoints[-1]["paid"] == limit and trace["slots"] == len(slots)
    assert objectives(nondominated([a["objectives"] for a in admitted])) == objectives(
        s["objectives"] for s in rows(out / "solutions.jsonl"))
    if label == "UU":
        original, = rows(captures["U"][0] / "center-trace.jsonl")
        assert trace["paidSHA256"] == original["paidSHA256"]
        assert (out / "endpoints.jsonl").read_bytes() == (captures["U"][0] / "endpoints.jsonl").read_bytes()
        common_original = archive_admissions(captures["U"][0])
        own_background = captures["U"][1]["background"]
        assert objectives(nondominated(own_background + [a["objectives"] for a in admitted])) == objectives(
            nondominated([p for _, p in common_original]))
    write_once(out / "validation.json", {"ledgerSlots": len(actual), "quotaContinuations": sum(r[-1] for r in actual),
                                         "endpoints": len(endpoints), "paid": limit,
                                         "inputs": {"entrants": file_sha(files[0]), "reference": file_sha(files[1]),
                                                    "rngBank": file_sha(rng)}, "UUExactControl": label == "UU"})
    return endpoints, admitted, trace["referenceProbe"]


def effects(cells):
    entry = {"R_S": cells["SS"] - cells["US"], "R_U": cells["SU"] - cells["UU"]}
    ref = {"X_S": cells["SS"] - cells["SU"], "X_U": cells["US"] - cells["UU"]}
    return {"entryConditional": entry, "referenceConditional": ref,
            "entryAverage": sum(entry.values()) / 2, "referenceAverage": sum(ref.values()) / 2,
            "interaction": entry["R_S"] - entry["R_U"], "diagonal": cells["SS"] - cells["UU"]}


def analyze(root, captures, result, norm):
    lower, scale = np.asarray(norm["lower"]), np.asarray(norm["scale"])
    background = nondominated(captures["S"][1]["background"] + captures["U"][1]["background"])
    report = []
    for ref in (1.25, 1.5, 2.0):
        hv = lambda front: float(hypervolume((np.asarray(front) - lower) / scale, (ref,) * 3))
        base = hv(background)
        entry = {k: hv(np.vstack((background, [s["objectives"] for s in v[1]["center"]]))) - base
                 for k, v in captures.items()}
        for local_fe in (250000 - ENTRY_FE, END_FE - ENTRY_FE):
            measures = {"discoveries": {}, "retained": {}}
            for label, (endpoints, admitted, _) in result.items():
                for name, source, field in (("discoveries", admitted, "FE"), ("retained", endpoints, "paid")):
                    points = [s["objectives"] for s in source if s[field] <= local_fe]
                    measures[name][label] = hv(np.vstack((background, points))) - base
            report.append({"reference": ref, "phaseFE": local_fe, "equivalentRunFE": local_fe + ENTRY_FE,
                           "backgroundHV": base, "entryOnlyDelta": entry, "gains": measures,
                           "effects": {name: effects(data) for name, data in measures.items()}})
    probe = {k: {**v[2], "flipRate": (v[2]["actualOnly"] + v[2]["alternateOnly"]) / v[2]["comparisons"]}
             for k, v in result.items()}
    write_once(root / "factorial.json", report)
    write_once(root / "paired-acceptance.json", probe)


def main():
    root = ROOT / "runs" / datetime.now().strftime("center-entry-cross-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    print("CENTER_CROSS_ROOT", root, flush=True)
    started, completed = time.monotonic(), []
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            assert read(ANCHOR / "analysis-status.json")["status"] == "COMPLETE"
            norm = read(ANCHOR / "protocol.json")["normalization"]
            write_once(root / "protocol.json", {"instance": STEM, "seed": SEED, "anchor": str(ANCHOR),
                "entryFE": ENTRY_FE, "endFE": END_FE, "phaseFE": END_FE - ENTRY_FE, "cells": list(CELLS),
                "rng": "Restore the same UNIFORM actual Java Random state at each corresponding physical slot; "
                       "candidate paths and within-slot draw counts can diverge",
                "primary": "End-of-stage HV gain from retained local endpoints against the common entry background",
                "secondary": "HV of all paid discoveries and paired decision changes for the same candidate/incumbent",
                "normalization": norm, "hvReferences": [1.25, 1.5, 2.0],
                "scope": "single phase and seed; frozen family constraints; no QGS or post-local selection in crossed stage"})
            prefix, slots = phase_ledgers(root)
            cp = build(root)
            captures = {}
            for k in SOURCES:
                captures[k] = capture(root, k, cp, prefix)
                completed.append(f"capture-{k}")
            write_once(root / "frozen-entries.json", {k: {
                name: file_sha(v[0] / name) for name in ("entry.bin", "rng-slots.bin", "entry.jsonl")}
                for k, v in captures.items()})
            trials = {}
            for label in CELLS:
                trials[label] = replay(root, label, cp, captures, slots)
                completed.append(label)
            analyze(root, captures, trials, norm)
    except BaseException as e:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "completed": completed,
                                         "error": str(e), "wallSeconds": time.monotonic() - started})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "completed": completed,
                                     "formalStageFE": len(CELLS) * (END_FE - ENTRY_FE),
                                     "captureFE": 2 * END_FE, "wallSeconds": time.monotonic() - started})
    print("CENTER_CROSS_COMPLETE", root, flush=True)


if __name__ == "__main__":
    main()
