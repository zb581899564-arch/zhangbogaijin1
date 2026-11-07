"""Resolve a post-run reference-version audit error; never rerun or overwrite original evidence."""
from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock
from frozen_classpath_identity import verify_capture
from pa_typed_basis_build import ENGINE, INTERFACE
from research.semantic_repair.evidence import digest

EXECUTION = ROOT / "runs/pa-typed-basis-engineering-20261105-223547-202723"


def native_results():
    results = []
    for path in sorted(EXECUTION.glob("*/*/audit/receipt.jsonl")):
        folder = path.parent
        receipt, = rows(path)
        assert receipt["status"] == "COMPLETE" and receipt["failedFE"] == 0
        assert receipt["successfulFE"] == receipt["attemptedFE"] == receipt["decoder"]["dynamic.evaluations"]
        parsed = read(folder / ("independent-fixtures.json" if (folder / "fixtures.jsonl").exists() else "independent-typed-replay.json"))
        assert parsed["successfulFE"] == receipt["successfulFE"]
        if "paidSHA256" in parsed: assert parsed["paidSHA256"] == receipt["paidSHA256"]
        results.append({"run": str(folder), "receipt": receipt, "independent": parsed})
    assert len(results) == 16 and sum(r["receipt"]["successfulFE"] for r in results) == 336214
    assert sum(r["receipt"]["fullDecoderQA"] for r in results) == 337814
    return results


def class_results():
    cp = (EXECUTION / "classpath.txt").read_text("utf-8-sig").strip()
    result, differences = [], []
    for path in sorted(EXECUTION.glob("*/*/audit/loaded-identity.jsonl")):
        loaded, = rows(path)
        checked = verify_capture(loaded, cp)
        assert loaded["javaVersion"] == "17.0.12"
        result.append({"run": str(path.parent), "checked": checked})
        stem = path.relative_to(EXECUTION).parts[0]
        older, = rows(ENGINE / stem / "main/audit/loaded-identity.jsonl")
        for name, actual in checked.items():
            if name.endswith((".PaPaidEvaluation", ".PaIndividual")):
                assert Path(actual["entry"]) == (INTERFACE / "classes").resolve()
                differences.append({"name": name, "actualInheritedSHA256": actual["sha256"],
                    "olderEngineeringSHA256": older[name]["sha256"], "actualDeclaredEntry": actual["entry"]})
    assert len(result) == 14
    return result, differences


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        root = ROOT / "runs" / datetime.now().strftime("pa-typed-basis-review-%Y%m%d-%H%M%S-%f")
        root.mkdir(); print("PA_TYPED_REVIEW_ROOT", root, flush=True)
        original = read(EXECUTION / "status.json")
        assert original["status"] == "INCOMPLETE_RETAINED" and original["recordedRuns"] == 16
        write_once(root / "protocol.json", {"source": str(EXECUTION), "originalFailure": original,
            "correction": "Original audit compared inherited interface classes to older engineering classes. Verify all recorded bytes AND sources against the ordered classpath frozen before execution; no hash whitelist or search change",
            "effectiveIdentity": "Original immutable execution plus this post-audit reference-version correction",
            "newSearchFE": 0, "decoderCalls": 0, "oldStatusRetained": True})
        for name in ("review_pa_typed_basis_engineering.py", "frozen_classpath_identity.py"):
            shutil.copy2(Path(__file__).with_name(name), root / name)
        try:
            for path, sha in read(EXECUTION / "source-hashes.json").items(): assert digest(EXECUTION / "source" / path) == sha
            for path, sha in read(EXECUTION / "controller-hashes.json").items(): assert digest(EXECUTION / "source" / path) == sha
            for filename, relative in (("PaPopulation.java", "src/algorithms/model_global/population/PaPopulation.java"),
                                       ("TypedScheduleGenome.java", "src/algorithms/model_global/encoding/TypedScheduleGenome.java")):
                assert digest(ROOT / relative) == digest(INTERFACE / "source" / filename)
            results = native_results(); classes, differences = class_results()
            value = {"runs": results, "classIdentities": classes, "inheritedVersionDifferencesFromOlderEngineering": differences,
                "actualSuccessfulFE": 336214, "failedEvaluations": 0, "fullDecoderQA": 337814,
                "engineeringPass": True, "newSearchFE": 0, "decoderCalls": 0, "originalFailureRetained": True,
                "defaultMainlineChanged": False, "performanceProved": False, "goalAchieved": False}
            write_once(root / "analysis.json", value)
            write_once(EXECUTION / "ACCEPTANCE.json", {"engineeringPass": True, "postAuditReview": str(root / "analysis.json"),
                "effectiveIdentity": "Original execution plus explicit post-audit reference correction; old status and frozen sources untouched",
                "newSearchFE": 0, "decoderCalls": 0, "goalAchieved": False})
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error)})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", "engineeringPass": True, "newSearchFE": 0, "decoderCalls": 0})
        print("PA_TYPED_REVIEW_COMPLETE engineeringFE336214 fullQA337814 newFE0", flush=True)


if __name__ == "__main__":
    main()
