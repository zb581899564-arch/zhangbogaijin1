"""Joint-view validation after native integer reference checks, without evaluating new search candidates."""
from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from pa_specialist_bridge_build import INTERFACE
from frozen_classpath_identity import verify_capture
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest

NATIVE = ROOT / "runs/qgomea-native-audit-20261106-020936-977499"
PAID = ROOT / "runs/pa-role-acceptance-probe-20261106-011839-887122"


def write_sources(path, stem):
    points = [point for seed in (14590003, 14590037)
              for point in rows(PAID / stem / str(seed) / "FOUR_JOINT/initial-population.jsonl")]
    assert len(points) == 200
    with path.open("x", encoding="utf-8") as output:
        for i, point in enumerate(points):
            data = [str(i), ",".join(repr(v) for v in point["objectives"])]
            data += [",".join(map(str, point[key])) for key in ("JS", "FA", "MA", "WA")]
            output.write("\t".join(data) + "\n")


def build(root):
    source, classes = root / "source", root / "classes"
    source.mkdir(); classes.mkdir()
    for folder in ("src/algorithms/model_global/direct", "src/algorithms/diagnostics/qgomea_reference"):
        for path in (ROOT / folder).glob("*.java"):
            shutil.copy2(path, source / path.name)
    base = (INTERFACE / "classpath.txt").read_text("utf-8-sig").strip()
    execute(["java", "-version"], root / "jdk-version.log")
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", base, "-d", str(classes),
             *map(str, source.glob("*.java"))], root / "compile.log")
    cp = str(classes) + ";" + base
    (root / "classpath.txt").write_text(cp, encoding="utf-8")
    write_once(root / "class-hashes.json", class_hashes(classes))
    write_once(root / "source-hashes.json", {p.name: digest(p) for p in source.glob("*.java")})
    return cp


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        root = ROOT / "runs" / datetime.now().strftime("direct-schedule-math-audit-%Y%m%d-%H%M%S-%f")
        root.mkdir()
        write_once(root / "protocol.json", {"version": "DIRECT_JOINT_VIEW_MATHEMATICS-v1", "registered": "2026-11-06",
                   "nativeReference": str(NATIVE), "paidSources": str(PAID), "sourceViews": 400,
                   "nativeCases": 19081, "fullTimelineQA": 800, "unscoredJointFixtures": 4000,
                   "scope": "Integer primitives and immutable direct representation only, not a complete qGOMEA or searchalgorithm",
                   "resourceExtension": "Everymaskoperation copies completeFMW byjob, outside-mask tuplesstaywithparent. This is an explicit proposedjoint extension, not originalpermutation-onlycode",
                   "billingBoundary": "No newchildobjectives arecomputed or selected. Only400previouslypaidinitialvectors get before/afterfulltimelineQA. Everyfuturegeneratedsearchattemptincludingduplicates/fallbackmustbepaid",
                   "nativeMismatch": "CanonicalUPGMAmismatch,globalRNG,FIandstoppingboundaries remain unresolved beforealgorithm/performanceacceptance",
                   "newDynamicSearchFE": 0, "goalAchieved": False})
        print("DIRECT_SCHEDULE_MATH_ROOT", root, flush=True)
        try:
            cp = build(root)
            command = ["java", "-Xms32m", "-Xmx2g", "-cp", cp, "research.dynamic.DirectPermutationAudit",
                       str(NATIVE / "cases.tsv"), str(NATIVE / "native-results.tsv"), str(root / "native-permutation-receipt.jsonl")]
            write_once(root / "native-permutation-command.json", command)
            execute(command, root / "native-permutation.log")
            results = []
            for stem in ("20_8_5_1", "100_2_3_1"):
                folder = root / stem; folder.mkdir()
                shutil.copytree(PAID / stem / "inputs", folder / "inputs")
                write_sources(folder / "known-sources.tsv", stem)
                inp = folder / "inputs"
                command = ["java", "-Xms32m", "-Xmx2g", "-Dresearch.snapshot.mode=ANCHOR", "-cp", cp,
                           "research.dynamic.DirectScheduleAudit", str(inp / (stem + ".txt")), str(inp / "RECONSTRUCTED-setup.txt"),
                           str(inp / "fatigue-input.txt"), str(folder / "known-sources.tsv"), str(folder / "audit")]
                write_once(folder / "command.json", command)
                execute(command, folder / "run.log")
                receipt, = rows(folder / "audit/receipt.jsonl")
                assert receipt["status"] == "passed" and receipt["knownPaidSources"] == 200 and receipt["fullTimelineQA"] == 400
                assert receipt["unscoredJointFixtures"] == 2000 and receipt["malformedFixturesRejected"] == 7
                capture, = rows(folder / "audit/loaded-identity.jsonl"); verify_capture(capture, cp)
                results.append({"stem": stem, **receipt})
            native, = rows(root / "native-permutation-receipt.jsonl")
            assert native["cases"] == 19081 and native["nativeOutputComparisons"] == 76324
            write_once(root / "analysis.json", {"nativePermutation": native, "instances": results,
                       "newDynamicSearchFE": 0, "fullTimelineQA": 800, "completeOptimizerImplemented": False, "goalAchieved": False})
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error), "newDynamicSearchFE": 0})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", "newDynamicSearchFE": 0,
                   "fullTimelineQA": 800, "unscoredJointFixtures": 4000, "goalAchieved": False})
        print("DIRECT_SCHEDULE_MATH_COMPLETE", root, results, flush=True)


if __name__ == "__main__":
    main()
