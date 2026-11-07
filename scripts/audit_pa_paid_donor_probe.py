"""Zero-FE independent accounting and frozen-artifact checks for the paid-donor study."""
import argparse
from pathlib import Path

from run_long_budget_bridge import ROOT, read, rows, write_once
from frozen_classpath_identity import verify_capture, resolve_class
from pa_capability_support import initial_key
from pa_paid_donor_analysis import analyze, readiness
from pa_paid_donor_data import at, initial_records, role
from pa_specialist_bridge_build import INTERFACE
from research.semantic_repair.evidence import digest


def checked_run(folder, native=False):
    command = read((folder.parent if native else folder) / "command.json")
    cp = command[command.index("-cp") + 1]
    identity, = rows(folder / "loaded-identity.jsonl")
    classes = verify_capture(identity, cp)
    assert identity["javaVersion"] == "17.0.12"
    receipt, = rows(folder / ("receipt.jsonl" if native else "run-receipt.jsonl"))
    if native:
        assert receipt["successfulFE"] == receipt["attemptedFE"] == receipt["expectedFE"]
        assert receipt["failedFE"] == 0
        replay = read(folder / "independent-borrowed-replay.json")
        assert replay["allPaidGenomesBorrowedViewsAndAcceptanceReconstructed"]
        assert replay["paidSHA256"] == receipt["paidSHA256"]
        paid, qa = receipt["successfulFE"], receipt["fullDecoderQA"] + receipt["borrow"]["borrow.fullQA"]
    else:
        assert receipt["attempted"] == receipt["successful"] == receipt["feLimit"]
        assert receipt["failed"] == receipt["timeInterruptedAttempts"] == 0
        assert receipt["error"] is None and receipt["stopReason"] == "FE_LIMIT"
        assert receipt["decoder"]["dynamic.evaluations"] == receipt["successful"]
        assert sum(receipt["search"].get(k + ".evaluations", 0)
                   for k in ("initialization", "global", "inter", "intra")) == receipt["successful"]
        validation = read(folder / "checkpoint-validation.json")
        assert validation["status"] == "passed" and validation["allReachedPointsCovered"]
        paid, qa = receipt["successful"], validation["uniqueOfflineDecodes"]
    return {"folder": str(folder.relative_to(ROOT)), "paidFE": paid,
            "extraFullQA": qa, "recordedClassesChecked": len(classes)}


def checked_pool(path):
    provenance = read(path.with_suffix(".provenance.json"))
    assert digest(path) == provenance["teacherFileSHA256"]
    folder = Path(provenance["source"])
    points = initial_records(folder) if provenance["kind"] == "INITIAL_RANDOM" else at(folder, 50000)[1]
    data = [line.split("\t") for line in path.read_text("utf-8-sig").splitlines()]
    assert len(data) == len(provenance["selectedIndices"]) == 100
    for i, (fields, index, born) in enumerate(zip(data, provenance["selectedIndices"], provenance["selectedBornFE"])):
        point = points[index]
        assert fields[:3] == [str(i), role(i), str(born)] and born == point["bornFE"] <= 50000
        assert list(map(float, fields[3].split(","))) == point["objectives"]
        for field, name in zip(fields[4:], ("JS", "FA", "MA", "WA")):
            assert list(map(int, field.split(","))) == point[name]
    return {"pool": str(path.relative_to(ROOT)), "rows": 100,
            "maximumSourceBornFE": max(provenance["selectedBornFE"]), "kind": provenance["kind"]}


def unchanged_defaults(root):
    names = {"PaPopulation.java", "PaPaidEvaluation.java", "PaCapabilitySearch.java"}
    result = {}
    for name in names:
        paths = list((ROOT / "src").rglob(name))
        assert len(paths) == 1 and digest(paths[0]) == digest(INTERFACE / "source" / name)
        result[name] = digest(paths[0])
    for file in ("source-hashes.json", "controller-hashes.json"):
        for name, value in read(root / file).items():
            assert digest(root / "source" / name) == value
    manifest = read(root / "class-hashes.json")
    actual = {p.relative_to(root / "classes").as_posix(): digest(p)
              for p in (root / "classes").rglob("*.class")}
    assert actual == manifest
    # The classical and canonical search implementations are inherited unchanged.
    old = (INTERFACE / "classpath.txt").read_text("utf-8-sig").strip()
    new = (root / "classpath.txt").read_text("utf-8-sig").strip()
    for name in ("org.uma.jmetal.util.research.classic.ClassicAlgorithm",
                 "org.uma.jmetal.util.research.search.CanonicalHmopso"):
        assert resolve_class(old, name)["sha256"] == resolve_class(new, name)["sha256"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    common = [checked_run(path.parent) for path in sorted(root.rglob("run-receipt.jsonl"))]
    native = [checked_run(path.parent, True) for path in sorted(root.glob("*/ENGINEERING-*/audit/receipt.jsonl"))]
    assert len(common) == 52 and len(native) == 4
    pools = []
    for path in sorted(root.rglob("*.tsv")):
        if path.with_suffix(".provenance.json").exists():
            pools.append(checked_pool(path))
    assert len(pools) == 18
    plan = read(root / "protocol.json")
    for spec in plan["instances"]:
        for seed in plan["seeds"]:
            folder = root / spec["stem"] / str(seed)
            reference = initial_key(folder / "SOURCE_S")
            for name in ("SOURCE_U", "SOURCE_N", "PURE", "INIT_GRAFT", "GRAFT_S", "GRAFT_U", "GRAFT_N"):
                assert initial_key(folder / name) == reference
    fresh = analyze(root, plan)
    stored = read(root / "analysis.json")
    for key, value in fresh.items():
        assert stored[key] == value, key
    assert readiness(fresh) == stored["readiness"]
    paid = sum(row["paidFE"] for row in common + native)
    qa = sum(row["extraFullQA"] for row in common + native)
    assert paid == stored["totalActualFE"] == 3137200
    assert qa == stored["totalFullQA"] == 123751
    defaults = unchanged_defaults(root)
    result = {"status": "passed", "newSearchFE": 0, "newDecoderCalls": 0,
              "commonRuns": common, "nativeRuns": native, "sourcePools": pools,
              "totalActualFE": paid, "totalFullQA": qa,
              "threeIndicatorAndFrozenDecisionRecalculationExact": True,
              "productionDefaultsUnchanged": defaults,
              "goalAchieved": False}
    write_once(root / "post-audit.json", result)
    print("PA_PAID_DONOR_POST_AUDIT_PASSED", paid, qa)


if __name__ == "__main__":
    main()
