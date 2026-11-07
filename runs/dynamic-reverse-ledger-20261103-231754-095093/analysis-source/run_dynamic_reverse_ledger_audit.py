"""Record UNIFORM's natural quotas, replay three policies, then audit the saved pools offline."""
import argparse
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import shutil
import time
from urllib.parse import urlparse
from urllib.request import url2pathname

from reverse_ledger_analysis import compare, phase_curve, pool_diagnosis
from reverse_ledger_build import ROLE_SOURCE, build
from run_dynamic_deep_roles import BRIDGE, FROZEN, MODES, REFERENCE, ROOT, SEED, STEM, ledger
from run_long_budget_bridge import (
    controller_lock, execute, nondominated, objectives, read, rows, run_one, verify_frozen, write_once,
)


POINTS = (100, 5100, 15000, 50000, 100000, 250000, 500000)
MODES = {**MODES, "U_RECORD": MODES["UNIFORM"], "NSGA": "NSGA2_4V"}
STAGES = ("initialization", "global", "inter", "intra")
REPLAY = ("UNIFORM", "SPECIAL", "NSGA")
RUNS = ("U_RECORD", *REPLAY)
OLD = ROLE_SOURCE.parent
LOCK = ROOT / "research/night_research"


def trial_folder(root, label):
    return root / label / "trials/fatigue" / MODES[label]


def frozen_ledger(root):
    return trial_folder(root, "U_RECORD") / "local-ledger.csv"


def preflight(root, cp):
    work = root / "engineering"
    work.mkdir()
    java = ["java", "-Xms32m", "-Xmx512m", "-cp", cp]
    checks = (
        "org.uma.jmetal.util.research.modelchecks.DynamicCoreChecks",
        "research.RuntimeChecks",
        "research.dynamic.DynamicRuntimeChecks",
        "org.uma.jmetal.util.research.runtime.AnytimeChecks",
    )
    for check in checks:
        execute([*java, check], work / f"{check.split('.')[-1]}.log")
    cls = "org.uma.jmetal.util.research.search.ReverseLedgerChecks"

    def fixture(name, limit, mode, source=None):
        out = work / name
        out.mkdir()
        execute([*java, cls, str(out), str(limit), mode, *([str(source)] if source else [])], out / "run.log")
        stream, = rows(out / "observation.jsonl")
        assert stream["paidFE"] == limit
        return ledger(out), stream["paidSHA256"], out / "local-ledger.csv"

    pilot, _, _ = fixture("fixture-discover", 64, "record")
    assert pilot[0][2] == -1 and pilot[0][4] >= 2 and pilot[1][2] == 0
    cases = {"global": 1, "cross-factory": 2, "intra-factory": pilot[0][4] + 2}
    for stage, limit in cases.items():
        a, stream, source = fixture(f"{stage}-record", limit, "record")
        b, replay, _ = fixture(f"{stage}-replay", limit, "replay", source)
        assert a == b and stream == replay
        assert (not a if stage == "global" else (a[-1][2] == -1 if stage == "cross-factory" else a[-1][2] == 0))
    write_once(work / "acceptance.json", {"checks": list(checks), "recordReplayBoundaries": cases,
                                         "fixtureFENotFormal": 64 + 2 * sum(cases.values())})


def run(root, label, cp):
    work = root / label
    shutil.copytree(BRIDGE / "inputs", work / "inputs")
    record = label == "U_RECORD"
    (work / "inputs/paired-audit.txt").write_text(
        "record\nQ\n-\n" if record else f"replay\nQ\n{frozen_ledger(root)}\n", encoding="utf-8")
    print("ARM", label, flush=True)
    try:
        return run_one(work, cp, "fatigue", MODES[label], POINTS)
    except BaseException as error:
        out = trial_folder(root, label)
        details = next(iter(rows(out / "search-end.jsonl")), {}) if (out / "search-end.jsonl").exists() else {}
        if not (out / "failures.jsonl").exists():
            write_once(out / "failures.jsonl", {"reason": str(error), "log": "run.log", **details})
        raise


def class_identity(root, folder):
    actual = read(folder / "class-origins.json")
    expected = {p.relative_to(root / "classes").as_posix()[:-6].replace("/", ".")
                for p in (root / "classes").rglob("*.class") if "$" not in p.name}
    checked = {}
    for record in actual["classes"]:
        path = Path(url2pathname(urlparse(record["codeSource"]).path))
        name = record["name"]
        if name in expected:
            assert path.resolve() == (root / "classes").resolve(), name
        if path.is_dir():
            content = (path / (name.replace(".", "/") + ".class")).read_bytes()
            assert sha256(content).hexdigest() == record["sha256"], name
        checked[name] = (record["codeSource"], record["sha256"])
    assert expected - {"org.uma.jmetal.util.research.search.ReverseLedgerChecks", "research.dynamic.ReverseClassOrigins"} <= set(checked)
    return checked


def stage_ledger(result, slots):
    r = result["receipt"]
    counters, dec = r["search"], r["decoder"]
    stage = {name: counters.get(name + ".evaluations", 0) for name in STAGES}
    assert r["attempted"] == r["successful"] == sum(stage.values()) == dec["dynamic.evaluations"] == POINTS[-1]
    assert dec["dynamic.recomputedOperations"] + dec["dynamic.reusedOperations"] == 40 * POINTS[-1]
    assert stage["initialization"] == 100 and slots and all(s[4] > 0 for s in slots)
    assert stage["inter"] == sum(s[4] for s in slots if s[2] < 0)
    assert stage["intra"] == sum(s[4] for s in slots if s[2] >= 0)
    visits = slots[-1][0]
    extra = stage["global"] - 5000 * ((visits + 99) // 100)
    assert extra == 0 or (visits % 100 == 0 and 0 < extra <= 5000)
    return stage, "global" if extra else ("inter" if slots[-1][2] < 0 else "intra")


def swarm_observations(folder):
    phase = rows(folder / "center-entry.jsonl")
    assert [r["event"] for r in phase] == ["global-end", "makespan-local-end", "center-entry"]
    assert all(len({r[k] for r in phase}) == 1 for k in ("centerSHA256", "referenceSHA256"))
    assert phase[0]["paidFE"] == 5100 < phase[1]["paidFE"] == phase[2]["paidFE"]
    selection = rows(folder / "selection-audit.jsonl")
    assert len(selection) == 200 and sum(r["kept"] for r in selection) == 100
    assert [r["index"] for r in selection] == list(range(200))
    fronts = objectives(nondominated([r["objectives"] for r in selection]))
    global_points = objectives(r["objectives"] for r in selection[:100])
    new = [r for r in selection[100:] if tuple(r["objectives"]) in fronts - global_points]
    return {"phases": phase, "selectedLocal": sum(r["kept"] for r in selection[100:]),
            "localNewNondominated": len(new), "localNewNondominatedKept": sum(r["kept"] for r in new),
            "localNewNondominatedTiedNotKept": sum(r["pddr"] == 1 and not r["kept"] for r in new)}


def verify_arm(root, label, result, reference, persist=True):
    folder = trial_folder(root, label)
    assert (folder / "initial-population.jsonl").read_bytes() == (REFERENCE / "initial-population.jsonl").read_bytes()
    classes = class_identity(root, folder)
    obs, = rows(folder / "observation.jsonl")
    slots = ledger(folder)
    stage, terminal = stage_ledger(result, slots)
    if reference:
        assert classes == reference["classes"]
        assert stage == reference["stage"] and terminal == reference["terminal"]
        assert [r[:-1] for r in slots] == [r[:-1] for r in reference["slots"]]
    if label == "UNIFORM":
        assert obs["paidSHA256"] == reference["obs"]["paidSHA256"]
        assert slots == reference["slots"] and not any(r[-1] for r in slots)
        assert all(objectives(a["front"]) == objectives(b["front"]) and a["fe"] == b["fe"]
                   for a, b in zip(result["curve"], reference["curve"]))
        for name in ("archive-admissions.csv", "center-entry.jsonl", "selection-audit.jsonl", "pool-snapshots.jsonl"):
            assert (folder / name).read_bytes() == (trial_folder(root, "U_RECORD") / name).read_bytes(), name
    swarm = {}
    if label != "NSGA":
        coop = result["receipt"]["cooperation"]
        assert coop["targetSpecialization"] == (label == "SPECIAL") and coop["sharing"]
        assert sum(result["receipt"]["search"].get(f"qgs.g{i}.updates", 0) for i in range(1, 5)) > 0
        assert obs["centerPbestCount"] > 0 and not obs["centerPbestMissingBirth"]
        swarm = swarm_observations(folder)
    report = {"stage": stage, "terminal": terminal, "visits": slots[-1][0], "slots": len(slots),
              "quotaContinuations": sum(r[-1] for r in slots), "obs": obs,
              "decoder": result["receipt"]["decoder"], "swarm": swarm,
              "searchSeconds": result["receipt"]["searchSeconds"], "offlineReplays": result["replays"],
              "wallSeconds": read(folder / "process.json")["wallSeconds"]}
    path = root / f"validation-{label}.json"
    if persist:
        write_once(path, report)
    else:
        assert read(path) == report, label
    return {"classes": classes, "stage": stage, "terminal": terminal, "slots": slots, "obs": obs,
            "curve": result["curve"], "report": report}


def run_analysis(root, trials, norm):
    curve = compare({k: trials[k] for k in REPLAY}, norm)
    pool = pool_diagnosis({label: trial_folder(root, label) for label in ("SPECIAL", "UNIFORM")}, norm)
    previous = read(OLD / "comparison.json")[-1]["arms"]
    old_gains = {ref: previous["SPECIAL"]["HV"][ref] / previous["UNIFORM"]["HV"][ref] - 1
                 for ref in ("1.25", "1.5", "2.0")}
    old = old_gains["1.5"]
    gain = curve[-1]["specialVsUniform"]
    ledger_gate = gain["1.5"] >= 0.01 and all(x > 0 for x in (*old_gains.values(), *gain.values()))
    blocked = any(
        v["obs"]["pddrTiedAdmittedUniqueFE"] > 0 or v["swarm"]["localNewNondominatedTiedNotKept"] > 0
        for k in ("SPECIAL", "UNIFORM") for v in [read(root / f"validation-{k}.json")])
    result = {"oldSpecialLedgerRelativeHV": old, "oldSpecialLedgerSensitivity": old_gains,
              "uniformLedgerRelativeHV": gain, "ledgerGate": ledger_gate,
              "omissionGate": pool["omissionGate"], "supplyGate": pool["supplyGate"],
              "eligibleToPlanOneSelector": ledger_gate and pool["omissionGate"] and pool["supplyGate"],
              "observedTieOrSurvivorBlock": blocked,
              "eligibleToConsiderCenterReplay": ledger_gate and not (pool["omissionGate"] and pool["supplyGate"]) and blocked,
              "scope": "one instance, seed and matched quota per block; no automatic experiment or mainline change"}
    write_once(root / "comparison.json", curve)
    write_once(root / "pool-diagnosis.json", pool)
    write_once(root / "decision.json", result)
    write_phase_curve(root)


def write_phase_curve(root):
    validation = read(root / "validation-U_RECORD.json")
    folders = {label: trial_folder(root, label) for label in REPLAY}
    result = phase_curve(ledger(trial_folder(root, "U_RECORD")), validation["stage"], folders,
                         read(root / "protocol.json")["normalization"])
    write_once(root / "phase-curve.json", result)


def resume_analysis(root):
    status = read(root / "status.json")
    assert status["status"] == "INCOMPLETE_RETAINED" and status["stage"] == "offline-analysis"
    assert status["accepted"] == list(RUNS)
    evidence = root / "analysis-source"
    evidence.mkdir()
    for name in (Path(__file__).name, "reverse_ledger_analysis.py"):
        shutil.copy2(Path(__file__).with_name(name), evidence / name)
    started = time.monotonic()
    trials, reference = {}, None
    for label in RUNS:
        folder = trial_folder(root, label)
        receipt, = rows(folder / "run-receipt.jsonl")
        curve = rows(folder / "anytime.jsonl")
        summary = read(folder / "summary.json")
        replayed = rows(folder / "solutions.jsonl")
        assert receipt["failed"] == 0 and receipt["stopReason"] == "FE_LIMIT"
        assert [r["fe"] for r in curve] == list(POINTS) and all(r["reached"] for r in curve)
        assert objectives(curve[-1]["front"]) == objectives(r["objectives"] for r in replayed)
        assert len(replayed) == summary["offlineValidationDecodes"]
        trial = {"receipt": receipt, "curve": curve, "replays": len(replayed)}
        checked = verify_arm(root, label, trial, reference, persist=False)
        if label == "U_RECORD":
            reference = checked
        trials[label] = trial
    run_analysis(root, trials, read(root / "protocol.json")["normalization"])
    write_once(root / "analysis-status.json", {"status": "COMPLETE", "accepted": list(RUNS),
                                               "formalSearchFE": 2000000, "newSearchFE": 0,
                                               "offlineWallSeconds": time.monotonic() - started,
                                               "initialStatusRetained": "status.json"})
    print("OFFLINE_ANALYSIS_COMPLETE", root, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume-analysis", type=Path, help="Recover offline analysis for four already accepted arms")
    offline = parser.parse_args().resume_analysis
    if offline is not None:
        root = offline.resolve(strict=True)
        assert root.parent == ROOT / "runs" and root.name.startswith("dynamic-reverse-ledger-")
        resume_analysis(root)
        return
    root = ROOT / "runs" / datetime.now().strftime("dynamic-reverse-ledger-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    print("REVERSE_LEDGER_ROOT", root, flush=True)
    start, stage, finished = time.monotonic(), "prepare", []
    try:
        with controller_lock(LOCK, "dispatch.lock"):
            verify_frozen(FROZEN)
            norm = read(OLD / "protocol.json")["normalization"]
            write_once(root / "protocol.json", {
                "instance": STEM, "seed": SEED, "maxFormalSearchFE": 2000000, "checkpoints": list(POINTS),
                "normalization": norm, "hvReferences": [1.25, 1.5, 2.0], "priorSpecialLedger": str(OLD),
                "matrix": {label: MODES[label] for label in RUNS}, "executionOrder": list(RUNS),
                "QGS": "original Q-table; only registered objective-role switch in SHARE comparisons",
                "gate": {"uniformLedgerRelativeHVMin": .01, "omissionArchiveGain": .001,
                         "omissionActualFractionOfBestMaxExclusive": .5, "omissionSampleFraction": .2,
                         "omissionFamilies": 2, "supplyMinPairs": 8, "supplyMinFamilies": 2,
                         "supplyMaterialWinArchiveFraction": .001, "supplyMinMaterialWinRate": .2},
                "snapshotSampling": "first/last entered CENTER global stages; first/last request per family; "
                                    "missing counts against predesignated omission slots; exact same FE cross pairs",
                "time": "single JVM at a time; observation recorded separately, no same-time inference",
                "policy": "Stop on engineering failure; never replace an arm or start extension automatically",
            })
            stage = "build"
            cp = build(root)
            stage = "engineering"
            preflight(root, cp)
            trials, accepted = {}, {}
            for label in RUNS:
                stage = label
                trials[label] = run(root, label, cp)
                accepted[label] = verify_arm(root, label, trials[label], accepted.get("U_RECORD"))
                finished.append(label)
            stage = "offline-analysis"
            run_analysis(root, trials, norm)
    except BaseException as error:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "stage": stage, "accepted": finished,
                                         "error": str(error), "wallSeconds": time.monotonic() - start})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "accepted": finished, "formalSearchFE": 2000000,
                                     "wallSeconds": time.monotonic() - start})
    print("REVERSE_LEDGER_COMPLETE", root, flush=True)


if __name__ == "__main__":
    main()
