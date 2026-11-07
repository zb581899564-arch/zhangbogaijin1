"""Post-run independent cost, class, paired-initialization and indicator checks."""
from pathlib import Path

from run_long_budget_bridge import ROOT, read, rows, write_once
from pa_role_acceptance_support import analyze
from run_pa_role_acceptance_probe import counts, decision, METHODS
from pa_capability_support import initial_key
from frozen_classpath_identity import verify_capture
from research.semantic_repair.evidence import digest


def audit(root):
    plan = read(root / "protocol.json")
    cp = (root / "classpath.txt").read_text("utf-8-sig").strip()
    native_paths = list(root.glob("*/ENGINE-*/audit/receipt.jsonl"))
    common_paths = list(root.rglob("run-receipt.jsonl"))
    assert len(native_paths) == 4 and len(common_paths) == 20
    for path in native_paths + common_paths:
        folder = path.parent
        capture, = rows(folder / "loaded-identity.jsonl")
        verify_capture(capture, cp)
        assert capture["javaVersion"] == "17.0.12"
        receipt, = rows(path)
        if path.name == "run-receipt.jsonl":
            assert receipt["successful"] == receipt["attempted"] == 50000
            assert receipt["failed"] == receipt["timeInterruptedAttempts"] == 0 and receipt["error"] is None
            assert receipt["decoder"]["dynamic.evaluations"] == 50000
            validation = read(folder / "checkpoint-validation.json")
            assert validation["status"] == "passed" and validation["allReachedPointsCovered"]
        else:
            assert receipt["successfulFE"] == receipt["attemptedFE"] == receipt["paidFullTimelineQA"]
            replay = read(folder / "independent-replay.json")
            assert receipt["failedFE"] == 0 and receipt["paidSHA256"] == replay["paidSHA256"]
    for spec in plan["instances"]:
        for seed in plan["seeds"]:
            folder = root / spec["stem"] / str(seed)
            assert {p.name for p in folder.iterdir()} == set(METHODS)
            expected = initial_key(folder / "FOUR_JOINT")
            assert all(initial_key(folder / method) == expected for method in METHODS)
    assert {p.relative_to(root / "classes").as_posix(): digest(p) for p in (root / "classes").rglob("*.class")} == read(root / "class-hashes.json")
    for manifest in ("source-hashes.json", "controller-hashes.json"):
        for name, value in read(root / manifest).items():
            assert digest(root / "source" / name) == value
    original = read(root / "analysis.json")
    fresh = analyze(root, plan)
    assert all(original[key] == value for key, value in fresh.items())
    assert original["decision"] == decision(fresh)
    fees = counts(root)
    assert all(original[key] == value for key, value in fees.items())
    assert fees["actualSuccessfulFE"] == fees["actualAttemptedFE"] == 1095600 and fees["failedFE"] == 0
    assert fees["extraFullDecoderQA"] == 103267
    inputs = {str(p): digest(p) for p in root.glob("*/inputs/*") if p.is_file()}
    write_once(root / "input-hashes-post-audit.json", inputs)
    return {"status": "passed", "runtimeCaptures": 24, "nativeFullTimelineAndReplayRuns": 4,
            "commonScientificRuns": 20, "allRegisteredCasesPresentAndInitialsIdentical": True,
            "compiledClassesAndFrozenSourceMatch": True, "allThreeIndicatorsAndDecisionRecalculatedExactly": True,
            "newSearchFE": 0, "newDecoderCalls": 0, **fees, "goalAchieved": False}


if __name__ == "__main__":
    root = ROOT / "runs/pa-role-acceptance-probe-20261106-011839-887122"
    result = audit(root)
    write_once(root / "post-audit.json", result)
    print("PA_ROLE_ACCEPTANCE_POST_AUDIT_PASSED", result["actualSuccessfulFE"], result["extraFullDecoderQA"])
