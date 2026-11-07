"""Zero-FE post-audit of native references, direct-view classes and historical default preservation."""
from pathlib import Path

from run_long_budget_bridge import ROOT, read, rows, write_once
from qgomea_reference_math import verify_native
from frozen_classpath_identity import verify_capture, resolve_class
from pa_specialist_bridge_build import INTERFACE
from research.semantic_repair.evidence import digest


def audit():
    native = ROOT / "runs/qgomea-native-audit-20261106-020936-977499"
    direct = ROOT / "runs/direct-schedule-math-audit-20261106-021640-361302"
    assert read(native / "status.json")["status"] == read(direct / "status.json")["status"] == "COMPLETE"
    assert verify_native(native / "cases.tsv", native / "native-results.tsv")["nativeCases"] == 19081
    for root in (native, direct):
        for name, value in read(root / "source-hashes.json").items():
            assert digest(root / "source" / name) == value
    for name, value in read(native / "native-input-hashes.json").items():
        assert digest(Path(name)) == value
    manifest = read(direct / "class-hashes.json")
    assert {p.relative_to(direct / "classes").as_posix(): digest(p) for p in (direct / "classes").rglob("*.class")} == manifest
    cp = (direct / "classpath.txt").read_text("utf-8-sig").strip()
    qa = structural = fallback = rejected = 0
    for stem in ("20_8_5_1", "100_2_3_1"):
        folder = direct / stem / "audit"
        capture, = rows(folder / "loaded-identity.jsonl")
        verify_capture(capture, cp)
        receipt, = rows(folder / "receipt.jsonl")
        assert receipt["status"] == "passed" and receipt["newDynamicSearchFE"] == 0
        qa += receipt["fullTimelineQA"]
        structural += receipt["unscoredJointFixtures"]
        fallback += receipt["emptyFactoryFallbacks"]
        rejected += receipt["malformedFixturesRejected"]
    assert (qa, structural, fallback, rejected) == (800, 4000, 58, 14)
    defaults = {}
    for name in ("PaPopulation.java", "PaPaidEvaluation.java", "PaCapabilitySearch.java"):
        paths = list((ROOT / "src").rglob(name))
        assert len(paths) == 1 and digest(paths[0]) == digest(INTERFACE / "source" / name)
        defaults[name] = digest(paths[0])
    old_cp = (INTERFACE / "classpath.txt").read_text("utf-8-sig").strip()
    for name in ("org.uma.jmetal.util.research.search.CanonicalHmopso", "org.uma.jmetal.util.research.classic.ClassicAlgorithm"):
        assert resolve_class(cp, name)["sha256"] == resolve_class(old_cp, name)["sha256"]
    return {"status": "passed", "nativeUniqueCases": 19081, "nativeIndependentOutputs": 95405,
            "javaNativeOutputComparisons": 76324, "knownSourceFullTimelineQA": qa,
            "unscoredJointFixtures": structural, "fallbacks": fallback, "malformedRejected": rejected,
            "defaultSourcesUnchanged": defaults, "newDynamicSearchFE": 0,
            "canonicalNativeClusteringMathMismatchRemains": True, "completeOptimizerAccepted": False,
            "goalAchieved": False}


if __name__ == "__main__":
    result = audit()
    root = ROOT / "runs/direct-schedule-math-audit-20261106-021640-361302"
    write_once(root / "post-audit.json", result)
    print("DIRECT_SCHEDULE_POST_AUDIT_PASSED", result["nativeUniqueCases"], result["knownSourceFullTimelineQA"])
