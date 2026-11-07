"""Reciprocal slot template and no-feedback reference-block audit."""
from datetime import datetime
from pathlib import Path
import shutil
import time

from run_center_entry_cross_replay import (
    ROOT, ANCHOR, SOURCES, ENTRY_FE, END_FE, analyze, check_capture, file_sha, phase_ledgers, replay,
)
from run_long_budget_bridge import controller_lock, execute, read, write_once


PRIOR = ROOT / "runs/center-entry-cross-20261103-233434-666587"
CELLS = ("SS", "SU", "US", "UU")


def preflight(root):
    assert read(PRIOR / "status.json")["status"] == "COMPLETE"
    assert read(ANCHOR / "analysis-status.json")["status"] == "COMPLETE"
    status = read(PRIOR / "status.json")
    assert status["formalStageFE"] == 4 * (END_FE - ENTRY_FE)
    prefix, slots = phase_ledgers(root)
    for file in ("capture-prefix-ledger.csv", "shared-center-ledger.csv"):
        assert file_sha(root / file) == file_sha(PRIOR / file), file
    captures = {label: check_capture(Path(p), label, prefix) for label, p in read(PRIOR / "reused-captures.json").items()}
    assert set(captures) == set(SOURCES)
    assert {k: {name: file_sha(v[0] / name) for name in ("entry.bin", "rng-slots.bin", "entry.jsonl")}
            for k, v in captures.items()} == read(PRIOR / "frozen-entries.json")
    s, u = (v[0].parents[2] / "inputs" for v in captures.values())
    for name in ("20_2_3_1.txt", "RECONSTRUCTED-setup.txt", "fatigue-input.txt"):
        assert file_sha(s / name) == file_sha(u / name), name
    write_once(root / "reused-captures.json", {k: str(v[0]) for k, v in captures.items()})
    return captures, slots


def overlay(root):
    src, classes = root / "source", root / "classes"
    src.mkdir()
    classes.mkdir()
    base = (PRIOR / "classpath.txt").read_text(encoding="utf-8-sig").strip()
    files = [str(shutil.copy2(ROOT / "src/algorithms/diagnostics" / f"{name}.java", src))
             for name in ("CenterReferenceProbe", "CenterRoleSwapProbe")]
    shutil.copy2(Path(__file__), src)
    shutil.copy2(Path(__file__).with_name("run_center_entry_cross_replay.py"), src)
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", base,
             "-d", str(classes), *files], root / "compile.log")
    cp = f"{classes};{base}"
    (root / "classpath.txt").write_text(cp, encoding="utf-8")
    write_once(root / "class-hashes.json", {p.relative_to(classes).as_posix(): file_sha(p)
                                           for p in classes.rglob("*.class")})
    return cp


def finish(root):
    reports = {"U": read(PRIOR / "factorial.json"), "S": read(root / "factorial.json")}
    terminal = {k: [r for r in rows if r["equivalentRunFE"] == END_FE] for k, rows in reports.items()}
    repeat = all(x > 1e-12 for rows in terminal.values() for r in rows
                 for x in r["effects"]["retained"]["referenceConditional"].values())
    summarize = {}
    for label, trace in read(root / "paired-acceptance.json").items():
        blocks = trace["blockProbe"]
        assert len(blocks) == 16
        assert all(b["fullFlips"] == trace["actualOnly"] + trace["alternateOnly"] for b in blocks)
        summarize[label] = {}
        for p in [b for b in blocks if b["partition"] == "physical"]:
            controls = [b for b in blocks if b["partition"] != "physical" and b["block"] == p["block"]]
            summarize[label][p["block"]] = {
                "size": p["size"], "physicalSingleRecovers": p["singleRecoversFullFlips"] / p["fullFlips"],
                "physicalRestoringCancels": p["restoringBlockCancelsFullFlips"] / p["fullFlips"],
                "mixedSingleRecovers": [b["singleRecoversFullFlips"] / p["fullFlips"] for b in controls],
                "mixedRestoringCancels": [b["restoringBlockCancelsFullFlips"] / p["fullFlips"] for b in controls],
            }
    write_once(root / "template-and-blocks.json", {"bothTemplatesBothEntrantsRetainedSign": repeat,
              "referenceGains": {k: {str(r["reference"]): r["effects"]["retained"]["referenceConditional"]
                                     for r in rows} for k, rows in terminal.items()}, "blocks": summarize})


def main():
    root = ROOT / "runs" / datetime.now().strftime("center-reference-followup-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    print("CENTER_REFERENCE_ROOT", root, flush=True)
    t, accepted = time.monotonic(), []
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            norm = read(PRIOR / "protocol.json")["normalization"]
            write_once(root / "protocol.json", {
                "anchor": str(PRIOR), "instance": "20_2_3_1", "seed": 8111009,
                "template": "SPECIAL saved Java RNG state at each slot", "order": list(CELLS),
                "phaseFE": END_FE - ENTRY_FE, "normalization": norm, "newCaptureFE": 0,
                "gate": "Reference direction for retained HV must repeat at stage end under both slot templates "
                        "with both entrant origins and references 1.25,1.5,2.0 to support a stable signed whole-reference claim.",
                "blocks": "same candidates; physical 15/55/15/15 blocks vs three fixed equal-size position permutations; "
                          "no feedback, no inference of independence across comparisons",
                "scope": "Reuse the same paid sources and quota. No candidate selector, publication claim, or mainline change.",
            })
            captures, slots = preflight(root)
            cp = overlay(root)
            results = {}
            for cell in CELLS:
                results[cell] = replay(root, cell, cp, captures, slots, rng_source="S", role_probe=True)
                accepted.append(cell)
            analyze(root, captures, results, norm)
            finish(root)
    except BaseException as error:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "accepted": accepted,
                                         "error": str(error), "wallSeconds": time.monotonic() - t})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "accepted": accepted,
                                     "formalStageFE": 4 * (END_FE - ENTRY_FE), "captureFE": 0,
                                     "wallSeconds": time.monotonic() - t})
    print("CENTER_REFERENCE_COMPLETE", root, flush=True)


if __name__ == "__main__":
    main()
