"""Execute the frozen336214FE ordinary typed-basis engineering contract, no performance gate."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from pa_typed_basis_build import build, SOURCE, ENGINE
from pa_typed_basis_replay import audit, audit_fixtures
from research.semantic_repair.evidence import digest
from frozen_classpath_identity import verify_capture

CONTRACT = ROOT / "research/gomea_reference_audit/PA_TYPED_BASIS_ENGINEERING_V1.json"


def totals(root):
    receipts = [r for p in root.glob("*/*/audit/receipt.jsonl") for r in rows(p)]
    result = {key: sum(r.get(key, 0) for r in receipts)
              for key in ("successfulFE", "attemptedFE", "failedFE", "fullDecoderQA")}
    result["recordedRuns"] = len(receipts)
    return result


def run_one(root, cp, stem, label, basis, limit, fixture=False):
    folder = root / stem / label
    out = folder / "audit"
    out.mkdir(parents=True)
    inputs = root / stem / "inputs"
    files = [inputs / (stem + ".txt"), inputs / "RECONSTRUCTED-setup.txt", inputs / "fatigue-input.txt",
             SOURCE / stem / "11730007/sources.tsv"]
    write_once(folder / "input-hashes.json", {str(p): digest(p) for p in files})
    entry = "research.dynamic.PaTypedFixtureRun" if fixture else "research.dynamic.PaPopulationRun"
    command = ["java", "-Xms32m", "-Xmx2g", "-Dresearch.snapshot.mode=ANCHOR", "-Dresearch.pa.traceIdentity=true",
               "-Dresearch.pa.typedBasis=" + basis, "-Dresearch.pa.typedTrace=" + str(out / "typed-steps.jsonl"),
               "-cp", cp, entry, *map(str, files), str(out), "13630003", str(limit)]
    write_once(folder / "command.json", command)
    print("PA_TYPED_ENGINEERING_RUN", stem, label, limit, flush=True)
    execute(command, folder / "run.log", timeout=600)
    if fixture:
        result = audit_fixtures(out, ENGINE / stem / "main/audit/catalog.jsonl")
    else:
        result = audit(out, basis)
    assert result["successfulFE"] == limit
    return {"stem": stem, "label": label, "basis": basis, **result}


def check_identity(root):
    old = ROOT / "runs/pa-capability-interfaces-20261105-175043-036508/source"
    for source, saved in (("src/algorithms/model_global/population/PaPopulation.java", "PaPopulation.java"),
                          ("src/algorithms/model_global/encoding/TypedScheduleGenome.java", "TypedScheduleGenome.java")):
        assert digest(ROOT / source) == digest(old / saved)
    for path in root.glob("*/*/audit/loaded-identity.jsonl"):
        actual, = rows(path)
        verify_capture(actual, (root / "classpath.txt").read_text("utf-8-sig").strip())
        assert actual["javaVersion"] == "17.0.12"
    return {"defaultPopulationAndGenomeUnchanged": True, "recordedUnmodifiedCoreClassesMatch": True}


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        root = ROOT / "runs" / datetime.now().strftime("pa-typed-basis-engineering-%Y%m%d-%H%M%S-%f")
        root.mkdir(); plan = read(CONTRACT)
        write_once(root / "protocol.json", {"frozenContract": plan, "contractSHA256": digest(CONTRACT),
            "purpose": "Engineering only, not performance or contribution gate",
            "fixtureSelection": "Structure-only deterministic indices; first case per kind uses a singleton donor view to force empty-pool paid fallback, remaining cases prefer structural changes/new marginal combinations; no objectives used",
            "QA": "Every actual paid candidate and physical-neutral reencoding gets full timeline comparison, outside search FE but inside engineering wall time",
            "defaultMainlineChanged": False, "goalAchieved": False})
        print("PA_TYPED_BASIS_ENGINEERING_ROOT", root, flush=True)
        results = []
        try:
            for stem in ("20_8_5_1", "100_2_3_1"):
                shutil.copytree(SOURCE / stem / "inputs", root / stem / "inputs")
            cp = build(root)
            for name in ("run_pa_typed_basis_engineering.py", "pa_typed_basis_build.py", "pa_typed_basis_replay.py",
                         "pa_population_replay.py", "pa_population_state_checks.py", "pa_population_model_checks.py", "pa_model_audit_analysis.py"):
                shutil.copy2(Path(__file__).with_name(name), root / "source" / name)
            write_once(root / "controller-hashes.json", {p.name: digest(p) for p in (root / "source").glob("*.py")})
            for stem in ("20_8_5_1", "100_2_3_1"):
                results.append(run_one(root, cp, stem, "fixtures", "TYPED", 164, fixture=True))
            for stem in ("20_8_5_1", "100_2_3_1"):
                for basis in ("ATOM", "TYPED", "SHAM_BLOCK"):
                    limit = plan["completeRuns"][stem][basis + "_FE"]
                    result = run_one(root, cp, stem, basis, basis, limit)
                    assert result["generations"] == 2 and result["programs"] == 200
                    if basis == "ATOM":
                        old = read(ENGINE / stem / "main/audit/independent-replay.json")
                        assert result["paidSHA256"] == old["paidSHA256"]
                    if basis in ("ATOM", "SHAM_BLOCK"):
                        assert result["typedCounts"].get("pointsWithInitialUnseenTuple", 0) == 0
                    results.append(result)
            for basis in plan["cutoffs"]["bases"]:
                full, = [r for r in results if r["stem"] == "20_8_5_1" and r["label"] == basis]
                for limit in plan["cutoffs"]["FE"]:
                    result = run_one(root, cp, "20_8_5_1", basis + "-cut" + str(limit), basis, limit)
                    assert result["paidSHA256"] == full["prefixPaidSHA256"][str(limit)]
                    results.append(result)
            actual = totals(root)
            assert actual["successfulFE"] == actual["attemptedFE"] == plan["maximumEngineeringSearchFE"] == 336214
            assert actual["failedFE"] == 0 and actual["recordedRuns"] == 16
            write_once(root / "analysis.json", {"runs": results, **actual, **check_identity(root),
                "engineeringPass": True, "sameBudgetPerformanceProved": False, "defaultMainlineChanged": False, "goalAchieved": False})
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error), **totals(root)})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", **totals(root), "engineeringPass": True, "goalAchieved": False})
        print("PA_TYPED_BASIS_ENGINEERING_COMPLETE", totals(root), flush=True)


if __name__ == "__main__":
    main()
