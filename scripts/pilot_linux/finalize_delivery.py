"""Seal completed evidence for transfer; performs no search or decoder call."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time
import zipfile


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def verify_and_record(root):
    required_pass = ["science-complete.json", "independent-audit.json",
                     "engineering/acceptance.json", "time-limit-acceptance.json",
                     "exact-hv-acceptance.json"]
    for name in required_pass:
        assert read(root / name)["passed"], name
    assert read(root / "independent-audit.json")["scienceFE"] == 9_000_000
    math = read(root / "math-checks-optimized-stage.json")
    assert math["status"] == "PASS" and len(math["checks"]) == 10
    report = root / "report"
    export = read(report / "figures/figure-qa.json")
    assert len(export["exports"]) == 10
    for figure in export["exports"]:
        for name in figure["files"]:
            assert (report / "figures" / name).stat().st_size > 0, name
        assert figure["svgEditableTextElements"] > 0
        assert abs(figure["physicalSizeMM"][0] - 183) < 1e-9
    visual = {
        "completedUTC": datetime.now(timezone.utc).isoformat(),
        "reviewer": "Primary assistant inspected all 10 actual figures in three Linux-rendered contact sheets",
        "passed": True, "figuresInspected": [row["stem"] for row in export["exports"]],
        "checks": ["Labels, legends, panel marks and axes readable without clipping",
                   "Same per-instance coordinates across all arms and seeds",
                   "Individual seeds and range bands labelled, not confidence intervals",
                   "All front points shown; 2D projection limitation labelled",
                   "Phase FE and time nested correctly; no duplicate sharing bar"],
        "sourcePreflight": "figure-source-preflight-context.json: PASS12 WARN2 FAIL0",
        "acceptedWarnings": ["TIFF not required for this pilot; SVG/PDF/600dpi PNG supplied",
                             "Static regex misreads 183*MM as inches; actual export metadata is183mm"],
        "history": "Original export figure-qa.json remains an earlier pending record; this closes its visual review",
        "scientificEAF": "Suppressed with three seeds; no five-seed scientific EAF display claimed"
    }
    write(report / "figures/visual-review.json", visual)
    decision = {
        "scienceFE": 9_000_000, "scienceFailedFE": 0,
        "evaluationImplementation": "ACCEPTED_FOR_THIS_PILOT",
        "currentFixedCombination": "CONDITIONAL_VALUE_DO_NOT_EXPAND",
        "retain": ["four objective roles", "existing sharing evidence", "joint local search", "exact decoder"],
        "reason": "FULL beats LOCAL_ONLY on20_8_5_1 but loses all three paired seeds on100_2_3_1; no universal stage deletion",
        "nextHypothesis": "Separate mature local receiver state from paid global/shared donor supply",
        "ordinaryRefuter": "Ordinary compatible donor-pool union; no extra role mechanism if it explains the gain",
        "oldFailures": "Do not restart PRE_FIRST by changing frequency; phase preference, visibility and archive-restart stops preserved",
        "newHypothesisExecuted": False, "mainlineChanged": False, "goalResumed": False,
        "pending": ["five-seed and held-out validation", "Linux matched classic controls", "trueTIME quality comparison"],
        "directAttributionIsCausal": False
    }
    write(report / "decision.json", decision)
    write(root / "delivery-acceptance.json", {
        "passed": True, "completedUTC": datetime.now(timezone.utc).isoformat(),
        "scienceFE": 9_000_000, "newSearchFEAtDelivery": 0, "newDecoderCallsAtDelivery": 0,
        "scienceFailures": 0, "engineeringInjectedFailures": 1,
        "requiredReceipts": required_pass, "mathematicalChecks": 10,
        "figures": 10, "figureFiles": 30, "visualReview": "report/figures/visual-review.json",
        "decision": "report/decision.json", "statisticsPending": False,
        "supersedesPendingFlagOnly": "science-complete.json was written before statistics; raw historical receipt preserved",
        "limits": decision["pending"], "originalMainlineModified": False,
        "backgroundExperimentCreated": False, "goalResumed": False
    })


def package(root, destination):
    started = time.perf_counter()
    paths = sorted(path for path in root.rglob("*") if path.is_file()
                   and "__pycache__" not in path.parts and path.name != "controller.lock")
    assert not any(path.is_symlink() for path in paths), "No dereferenced links in evidence delivery"
    manifest = [{"path": str(path.relative_to(root)), "bytes": path.stat().st_size,
                 "sha256": digest(path)} for path in paths]
    manifest_path = root / "evidence-manifest.json"
    write(manifest_path, {"files": manifest, "exclusions": ["__pycache__", "controller.lock"],
                          "manifestSelfExcluded": True, "runtimeBinariesOutsideRun": True})
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in [*paths, manifest_path]:
            archive.write(path, str(path.relative_to(root)))
    receipt = {"archive": str(destination), "bytes": destination.stat().st_size,
               "sha256": digest(destination), "includedFiles": len(paths) + 1,
               "packagingSeconds": time.perf_counter() - started,
               "source": str(root), "newSearchFE": 0, "newDecoderCalls": 0}
    write(destination.with_suffix(".receipt.json"), receipt)
    print(json.dumps(receipt), flush=True)


def main():
    if platform.system() != "Linux":
        raise RuntimeError("Delivery acceptance and evidence packaging run on Linux")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    assert not args.archive.exists()
    assert args.root.resolve() not in args.archive.resolve().parents
    verify_and_record(args.root)
    package(args.root, args.archive)


if __name__ == "__main__":
    main()
