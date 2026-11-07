"""Offline analysis of the frozen step4/5 experiment. No search feedback."""
from pathlib import Path
import sys
from .io import load, dump
from .metrics import check_metrics
from .data import collect_runs, metric_tables, instance_means
from .inference import comparisons, target_attainment, accounting
from .report import write_report


def analyze(root):
    check_metrics()
    p = load(root / "protocol.json")
    status = load(root / "status.json")
    variants = p["coreVariants"] + p["cooperationVariants"]
    expected = len(p["instances"]) * len(p["seeds"]) * len(variants) * 2
    if status["completed"] != expected:
        raise RuntimeError("Incomplete runs; no final analysis")
    output = root / "analysis"
    output.mkdir(exist_ok=False)
    allruns, references = collect_runs(root, p, output, variants)
    rows, curves = metric_tables(allruns, references, p, output)
    means = instance_means(rows, p, variants, output)
    paired = comparisons(p, means, output)
    target_attainment(rows, curves, output)
    audit = accounting(allruns, rows, p, references, output)
    write_report(rows, paired, audit, output)
    dump(root / "status.json", {"status":"ANALYSIS_COMPLETE", "completed":expected,
                               "expected":expected, "analysis":"analysis/report.md"})
    print(audit)
    print(output)


if __name__ == "__main__":
    analyze(Path(sys.argv[1]).resolve())
