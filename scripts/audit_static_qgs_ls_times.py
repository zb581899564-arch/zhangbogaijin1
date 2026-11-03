"""Isolated chapter-4 Algorithm 5 interpretation; no production-class changes."""
from datetime import datetime
import difflib
from pathlib import Path
import shutil
import time

from run_long_budget_bridge import (
    FE, FROZEN, ROOT, SEED, STEM, analyze, controller_lock, execute, objectives, read, rows,
    run_one, verify_frozen, write_once,
)

BRIDGE = ROOT / "runs/long-budget-bridge-20261103-082221-744929"
REFERENCE = ROOT / "runs/historical-nsga-comparison-20261103-155556-328249"
SOURCE = FROZEN / "source/src/java/search/LocalSearch.java"


def build_probe(root, cp):
    before = SOURCE.read_text(encoding="utf-8")
    single = """            int factory = SeededRandom.current().nextInt(instance.factories());
            factory = state.localFactory(current, direction, factory);
            current = vns(current, factory, direction, reference);"""
    outer_rounds = """            state.count("audit.paperLS.particlesStarted");
            for (int round = 0; round < config.localProposalCap; round++) {
                int factory = SeededRandom.current().nextInt(instance.factories());
                factory = state.localFactory(current, direction, factory);
                state.count("audit.paperLS.roundsStarted");
                current = vns(current, factory, direction, reference);
                state.count("audit.paperLS.roundsCompleted");
            }
            state.count("audit.paperLS.particlesCompleted");"""
    cap = "int[] remaining = {config.localProposalCap};"
    assert before.count(single) == before.count(cap) == 1
    after = before.replace(single, outer_rounds).replace(
        cap, "int[] remaining = {chapter == 4 ? Integer.MAX_VALUE : config.localProposalCap};")
    source, classes = root / "source", root / "classes"
    source.mkdir()
    classes.mkdir()
    shutil.copy2(SOURCE, source / "frozen-LocalSearch.java")
    (source / "LocalSearch.java").write_text(after, encoding="utf-8")
    (source / "variant.diff").write_text("".join(difflib.unified_diff(
        before.splitlines(True), after.splitlines(True), fromfile="frozen", tofile="static-outer-round-probe")),
        encoding="utf-8")
    shutil.copy2(Path(__file__), source / Path(__file__).name)
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", cp, "-d", str(classes),
             str(source / "LocalSearch.java")], root / "compile.log")
    return str(classes) + ";" + cp


def archive_reference(mode, origin):
    folder = origin / "trials/static" / mode
    receipt, = rows(folder / "run-receipt.jsonl")
    saved = {point["fe"]: point for point in rows(folder / "anytime.jsonl")}
    assert receipt["successful"] == FE[-1] and receipt["seed"] == SEED
    return {"receipt": receipt, "curve": [saved[fe] for fe in FE],
            "replays": read(folder / "summary.json")["offlineValidationDecodes"]}


def verify_runs(control, probe):
    old = archive_reference("BASELINE", BRIDGE)
    assert all(objectives(a["front"]) == objectives(b["front"]) for a, b in zip(control["curve"], old["curve"]))
    assert objectives(control["curve"][0]["front"]) == objectives(probe["curve"][0]["front"])
    result = {}
    for label, run in (("frozenQGS", control), ("outerLS30", probe)):
        c = run["receipt"]["search"]
        counts = {stage: c[stage + ".evaluations"] for stage in ("initialization", "global", "inter", "intra")}
        assert sum(counts.values()) == FE[-1]
        result[label] = {**counts, "generationsCompleted": c.get("generations.completed", 0),
                         "paperLSDiagnostics": {k: v for k, v in c.items() if k.startswith("audit.paperLS.")}}
    c = result["outerLS30"]["paperLSDiagnostics"]
    assert c["audit.paperLS.roundsCompleted"] >= 30 * c["audit.paperLS.particlesCompleted"]
    assert c["audit.paperLS.roundsStarted"] - c["audit.paperLS.roundsCompleted"] in (0, 1)
    return result


def main():
    root = ROOT / "runs" / datetime.now().strftime("static-qgs-paper-ls-audit-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    print("PAPER_LS_ROOT", root, flush=True)
    start = time.monotonic()
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            verify_frozen(FROZEN)
            write_once(root / "protocol.json", {
                "instance": STEM, "seed": SEED, "actualFE": FE[-1], "checkpoints": list(FE),
                "control": str(BRIDGE), "normalization": read(BRIDGE / "protocol.json")["normalization"],
                "reference": str(REFERENCE), "decoder": "canonical-v1; frozen reconstructed SUT; standby=1",
                "order": ["frozenQGS", "outerLS30"],
                "intervention": "Ch4 per-particle outer loop of up to 30 VNS sweeps; redraw factory each sweep; retain existing shake/descent/reset/acceptance; no local proposal cap. Actual shared 500000 FE still binds.",
                "scope": "One operational reading of paper Algorithm 5; not complete paper semantics, no production changes, no parameter selection",
            })
            cp = (BRIDGE / "classpath.txt").read_text(encoding="utf-8-sig").strip()
            probe_cp = build_probe(root, cp)
            work = [root / "frozenQGS", root / "outerLS30"]
            for folder in work:
                shutil.copytree(BRIDGE / "inputs", folder / "inputs")
            control = run_one(work[0], cp, "static", "BASELINE", FE)
            probe = run_one(work[1], probe_cp, "static", "BASELINE", FE)
            ledger = verify_runs(control, probe)
            archive = {"BASELINE": control, "QGS_OUTER_LS_30": probe,
                       "NSGA2_4V": archive_reference("NSGA2_4V", REFERENCE),
                       "NSGA2_HISTORICAL_ADAPTED": archive_reference("NSGA2_HISTORICAL_ADAPTED", REFERENCE)}
            analyze(root, {"static": archive}, read(BRIDGE / "protocol.json")["normalization"])
            write_once(root / "stage-ledger.json", ledger)
    except BaseException as error:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": str(error),
                                         "wallSeconds": time.monotonic() - start})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "newSearchFE": 1000000,
                                     "controlCheckpointsExact": True, "wallSeconds": time.monotonic() - start})
    print("PAPER_LS_COMPLETE", root, flush=True)


if __name__ == "__main__":
    main()
