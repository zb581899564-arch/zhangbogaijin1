"""Trace observed CENTER endpoints into the second global block on the unchanged two policies."""
from datetime import datetime
import difflib
from pathlib import Path
import shutil
import time

from reverse_ledger_analysis import archive_admissions
from run_center_entry_cross_replay import ANCHOR, ENTRY_FE, END_FE, file_sha, write_ledger
from run_dynamic_reverse_ledger_audit import BRIDGE, ROOT, MODES, ledger, trial_folder
from run_long_budget_bridge import controller_lock, execute, rows, run_one, write_once
from run_paired_qgs_guidance import replace


HOOK = "org.uma.jmetal.util.research.search.CenterPropagationTrace"
LABELS = ("SPECIAL", "UNIFORM")


def patch_entry(source):
    source = replace(source, "        ReverseClassOrigins.write(out);",
                     f'''        System.setProperty("research.center.from", "{ENTRY_FE}");
        System.setProperty("research.center.through", "{END_FE}");
        ReverseClassOrigins.write(out);''')
    return replace(source, "        evidence.finish(out);", f"        {HOOK}.finish(out);\n        evidence.finish(out);")


def patch_swarm(source):
    source = replace(source, "                ReverseAudit.run().selection(candidates, selected, globalSnapshots.size());",
                     """                ReverseAudit.run().selection(candidates, selected, globalSnapshots.size());
                CenterPropagationTrace.selection(candidates, selected, globalSnapshots.size());""")
    return replace(source, '            state.evaluate(child, "global", direction);',
                   '''            state.evaluate(child, "global", direction);
            CenterPropagationTrace.evaluated(particle, personal, leader, child, direction, composed);''')


def patch_support(source):
    return replace(source, '        count("assembliesProposed"); nanos += System.nanoTime() - start; return child;',
                   f'''        long[] paidSources = new long[chosen.length];
        for (int f = 0; f < chosen.length; f++) paidSources[f] = chosen[f].paidFE;
        {HOOK}.composition(paidSources);
        count("assembliesProposed"); nanos += System.nanoTime() - start; return child;''')


def overlay(root):
    src, classes = root / "source", root / "classes"
    src.mkdir()
    classes.mkdir()
    base = (ANCHOR / "classpath.txt").read_text(encoding="utf-8-sig").strip()
    paths = []
    for name, patch in (("LongBudgetRun", patch_entry), ("CanonicalHmopso", patch_swarm),
                        ("CooperationSupport", patch_support)):
        prior = ANCHOR / "source" / f"{name}.java"
        a = prior.read_text(encoding="utf-8")
        b = patch(a)
        out = src / prior.name
        out.write_text(b, encoding="utf-8")
        (src / f"{name}.diff").write_text("".join(difflib.unified_diff(
            a.splitlines(True), b.splitlines(True), fromfile=str(prior), tofile=out.name)), encoding="utf-8")
        paths.append(str(out))
    paths.append(shutil.copy2(ROOT / "src/algorithms/diagnostics/CenterPropagationTrace.java", src))
    shutil.copy2(Path(__file__), src)
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", base,
             "-d", str(classes), *paths], root / "compile.log")
    cp = f"{classes};{base}"
    (root / "classpath.txt").write_text(cp, encoding="utf-8")
    write_once(root / "class-hashes.json", {p.relative_to(classes).as_posix(): file_sha(p)
                                           for p in classes.rglob("*.class")})
    return cp


def analyze(folder, cutoff):
    endpoint, = rows(folder / "propagation-endpoints.jsonl")
    first = set(endpoint["centerEndpoints"])
    selected = set(endpoint["selectedCenterEndpoints"])
    assert selected <= first and first
    events = rows(folder / "propagation-gen2.jsonl")
    assert [r["paidFE"] for r in events] == list(range(cutoff - 4999, cutoff + 1))
    admitted = dict(archive_admissions(folder))
    assert all(r["admitted"] == (r["paidFE"] in admitted) for r in events)
    channels = {
        "parentFromSelectedCenter": lambda r: r["parentFE"] in selected,
        "personalGuideFromSelectedCenter": lambda r: r["personalInputFE"] in selected,
        "globalGuideFromSelectedCenter": lambda r: r["leaderInputFE"] in selected,
        "assemblyFromCenterPaid": lambda r: any(ENTRY_FE < f <= END_FE for f in (r["factorySourceFEs"] or [])),
        "assemblyFromSelectedCenter": lambda r: any(f in selected for f in (r["factorySourceFEs"] or [])),
    }
    report = {k: {"children": sum(fn(r) for r in events), "admitted": sum(fn(r) and r["admitted"] for r in events)}
              for k, fn in channels.items()}
    used = {r[field] for r in events for field in ("parentFE", "personalInputFE", "leaderInputFE") if r[field] in selected}
    return {"firstCenterEndpoints": len(first), "selected": len(selected), "uniqueSelectedUsedAsInput": len(used),
            "channels": report, "allChildren": len(events), "admittedChildren": sum(r["admitted"] for r in events)}


def main():
    root = ROOT / "runs" / datetime.now().strftime("center-propagation-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    print("CENTER_PROPAGATION_ROOT", root, flush=True)
    t, completed = time.monotonic(), []
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            frozen = [s for s in ledger(trial_folder(ANCHOR, "U_RECORD")) if s[0] <= 100]
            assert frozen[-1][0] == 100
            cutoff = 10100 + sum(s[4] for s in frozen)
            assert cutoff == 447916
            write_ledger(root / "prefix-ledger.csv", frozen)
            write_once(root / "protocol.json", {"anchor": str(ANCHOR), "cutoffFE": cutoff, "runs": list(LABELS),
                 "scope": "Observe existing policies through second global block. No counterfactual causal performance claim.",
                 "inputDefinition": "Matched paid CENTER endpoint used as receiver, guide supplied to JOB_ALIGNED, or pool fragment; overlapping channels."})
            cp = overlay(root)
            report = {}
            for label in LABELS:
                work = root / label
                shutil.copytree(BRIDGE / "inputs", work / "inputs")
                (work / "inputs/paired-audit.txt").write_text(f"replay\nQ\n{root / 'prefix-ledger.csv'}\n", encoding="utf-8")
                run_one(work, cp, "fatigue", MODES[label], (100, ENTRY_FE, END_FE, cutoff))
                folder = trial_folder(root, label)
                prior = trial_folder(ANCHOR, label)
                assert archive_admissions(folder) == [p for p in archive_admissions(prior) if p[0] <= cutoff]
                assert (folder / "selection-audit.jsonl").read_bytes() == (prior / "selection-audit.jsonl").read_bytes()
                assert (folder / "initial-population.jsonl").read_bytes() == (prior / "initial-population.jsonl").read_bytes()
                assert [r[:-1] for r in ledger(folder)] == [r[:-1] for r in frozen]
                report[label] = analyze(folder, cutoff)
                completed.append(label)
            write_once(root / "propagation.json", report)
    except BaseException as error:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "completed": completed, "error": str(error)})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "completed": completed, "searchFE": 2 * cutoff,
                                     "wallSeconds": time.monotonic() - t})
    print("CENTER_PROPAGATION_COMPLETE", root, flush=True)


if __name__ == "__main__":
    main()
