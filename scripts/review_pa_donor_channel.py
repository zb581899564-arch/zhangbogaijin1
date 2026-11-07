"""Independent accounting and protected-source checks, including one explicit reused fixture."""
from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock
from pa_capability_support import SOURCE, initial_key, fees
from pa_specialist_bridge_build import INTERFACE
from research.semantic_repair.evidence import digest

PROBE = ROOT / "runs/pa-donor-channel-probe-20261105-215806-133644"
RECOVERY = ROOT / "runs/pa-donor-channel-probe-20261105-215450-025540"


def checked_runs():
    paths = sorted(PROBE.rglob("run-receipt.jsonl"))
    assert len(paths) == 45
    paths.append(RECOVERY / "20_8_5_1/ENGINEERING-LIVE/run-receipt.jsonl")
    new_hash = read(PROBE / "class-hashes.json")["org/uma/jmetal/util/research/modelglobal/PaPopulation.class"]
    assert read(PROBE / "class-hashes.json") == read(RECOVERY / "class-hashes.json")
    completed, checks = [], []
    for path in paths:
        folder = path.parent
        relative = folder.relative_to(PROBE) if folder.is_relative_to(PROBE) else folder.relative_to(RECOVERY)
        stem = relative.parts[0]
        receipt, = rows(path)
        assert receipt["successful"] == receipt["attempted"] == receipt["decoder"]["dynamic.evaluations"]
        assert receipt["failed"] == receipt["timeInterruptedAttempts"] == 0 and receipt["error"] is None
        identities, = rows(folder / "loaded-identity.jsonl")
        old, = rows(INTERFACE / stem / "PARITY/loaded-identity.jsonl")
        for name, prior in old.items():
            if isinstance(prior, dict) and "sha256" in prior:
                expected = new_hash if name.endswith(".PaPopulation") else prior["sha256"]
                assert identities[name]["sha256"] == expected, (folder, name)
        assert identities["javaVersion"] == "17.0.12"
        qa = read(folder / "checkpoint-validation.json")
        assert qa["status"] == "passed" and qa["allReachedPointsCovered"]
        completed.append((folder, receipt))
        checks.append({"run": str(folder), "successfulFE": receipt["successful"],
            "reused": folder.is_relative_to(RECOVERY), "delegateEvaluationsEqual": True,
            "recordedClassIdentitiesMatch": True, "offlineFullDecoderQA": qa["uniqueOfflineDecodes"]})
    total = fees(completed)
    assert total["successfulFE"] == total["attemptedFE"] == 1004043 and total["failedAttempts"] == 0
    assert sum(r["successfulFE"] for r in checks if r["reused"]) == 7900
    return {"runs": checks, **total, "newControllerFE": 996143, "reusedEngineeringFE": 7900}


def invariant_sections():
    original = (INTERFACE / "source/PaPopulation.java").read_text("utf-8-sig")
    isolated = (PROBE / "source/PaPopulation.java").read_text("utf-8-sig")
    for start, end in (("    private List<int[]> learn()", "    private static boolean accepts("),
                       ("    private static boolean accepts(", "    public List<PaIndividual> population()")):
        assert original.split(start)[1].split(end)[0] == isolated.split(start)[1].split(end)[0]
    paths = {"PaPopulation.java": "src/algorithms/model_global/population/PaPopulation.java",
             "PaPaidEvaluation.java": "src/algorithms/model_global/population/PaPaidEvaluation.java",
             "PaCapabilitySearch.java": "src/algorithms/diagnostics/pa_capability/PaCapabilitySearch.java"}
    for filename, path in paths.items(): assert digest(ROOT / path) == digest(INTERFACE / "source" / filename)
    plan = read(PROBE / "protocol.json")
    for spec in plan["instances"]:
        stem = spec["stem"]
        for seed in plan["seeds"]:
            starts = [initial_key(PROBE / stem / str(seed) / label) for label in plan["methods"]]
            assert all(len(s) == 100 and s == starts[0] for s in starts)
        for path in (PROBE / stem / "inputs").iterdir():
            if path.is_file(): assert digest(path) == digest(SOURCE / stem / "inputs" / path.name)
    engineering = read(PROBE / "engineering.json")
    assert engineering["passed"] and len(engineering["runs"]) == 10
    assert all(r["allPaidGenomesAndAcceptancesReconstructed"] for r in engineering["runs"])
    assert sum(r["successfulFE"] for r in engineering["runs"]) == 143643
    return {"originalAcceptsAndLearnBodiesUnchanged": True, "defaultPopulationEvaluatorAndEntryUnchanged": True,
        "common100InitialsAll9MethodsChecked": True, "copiedInputsMatchFrozenSource": True,
        "engineeringFullPaidGenomesAcceptanceAndNeutralAliasChecks": True}


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        assert read(PROBE / "status.json")["status"] == "COMPLETE"
        root = ROOT / "runs" / datetime.now().strftime("pa-donor-channel-review-%Y%m%d-%H%M%S-%f")
        root.mkdir(); print("PA_CHANNEL_REVIEW_ROOT", root, flush=True)
        write_once(root / "protocol.json", {"source": str(PROBE), "reused": str(RECOVERY),
            "scope": "All45new runs plus one explicitly reused7900FEengineering run; original search/metrics not changed",
            "newSearchFE": 0, "decoderCalls": 0})
        shutil.copy2(Path(__file__), root / Path(__file__).name)
        try:
            result = {**checked_runs(), **invariant_sections(), "newSearchFE": 0, "decoderCalls": 0, "goalAchieved": False}
            write_once(root / "analysis.json", result)
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error)})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", "newSearchFE": 0, "decoderCalls": 0})
        print("PA_CHANNEL_REVIEW_COMPLETE", result["successfulFE"], result["offlineFullDecoderQA"], flush=True)


if __name__ == "__main__":
    main()
