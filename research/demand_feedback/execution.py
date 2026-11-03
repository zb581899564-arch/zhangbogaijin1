"""Reuse paid trial dispatch; explicitly add demand-validation wall cost once."""
import subprocess
import sys
import time
from research.semantic_repair.evidence import read, write_once
from research.cooperation_roles.execution import run_one as shared_run_one
from .protocol import ROOT, trial_folder
from .observations import attach_demand, apply_validation_receipt


def run_one(root, job, instance, spec, deadline):
    folder = trial_folder(root, job); extra = folder / "demand-validation.json"
    if folder.exists() and not extra.is_file():
        raise RuntimeError("Incomplete demand owner retained; no rerun: " + str(folder))
    run, dispatched = shared_run_one(root, job, instance, spec, deadline)
    started = time.monotonic(); attach_demand(run, folder)
    seconds = time.monotonic() - started
    if dispatched:
        write_once(extra, {"status": "passed", "additionalControllerValidationSeconds": seconds,
            "extraFE": 0, "scope": "Demand trace/header and fixed routing replay; additive to original execution.json validation"})
    apply_validation_receipt(run, read(extra))
    deadline.require(); return run, dispatched


def analyze_bounded(root, deadline):
    deadline.require(5); tag = str(time.time_ns()); receipt = root / ("analysis-result-" + tag + ".json")
    cmd = [sys.executable, "-B", "-m", "research.demand_feedback.worker", str(root), str(receipt)]
    write_once(root / ("analysis-command-" + tag + ".json"), cmd)
    try:
        with (root / ("analysis-process-" + tag + ".log")).open("x", encoding="utf-8") as stream:
            result = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=deadline.remaining())
    except subprocess.TimeoutExpired as error:
        raise TimeoutError("Original30min cap stopped offline analysis; partial artifacts preserved") from error
    if result.returncode or not receipt.exists():
        raise RuntimeError("Owned demand analysis failed; evidence retained")
    deadline.require(); return root / read(receipt)["analysis"]
