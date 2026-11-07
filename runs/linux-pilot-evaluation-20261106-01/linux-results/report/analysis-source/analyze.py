"""Linux Python 3.11 full-batch analysis; new reports only, never overwrite evidence."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import platform
import shutil
import sys
import traceback
import time

from report_io import actual_costs, load_runs, read_json, require_linux, write_csv, write_json


def _project_imports():
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "research" / "pilot_evaluation").is_dir():
            sys.path.insert(0, str(candidate))
            return candidate
    raise RuntimeError("Cannot locate research/pilot_evaluation alongside the analysis bundle")


def _new_attempt(root, requested):
    destination = requested.resolve() if requested is not None else root / "report"
    if destination.exists():
        raise FileExistsError(f"Report destination exists; use --output for a new attempt: {destination}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    attempt = destination.with_name(destination.name + "-attempt-" + stamp)
    attempt.mkdir(parents=True, exist_ok=False)
    return destination, attempt


def _save_sources(attempt, project):
    destination = attempt / "analysis-source"
    destination.mkdir()
    for name in ("analyze.py", "report_io.py", "analysis_tables.py", "comparisons.py", "provenance.py",
                 "stage_accounting.py", "report_text.py", "plotting.py", "front_plotting.py", "figure_exports.py", "exact_hv.py"):
        shutil.copy2(Path(__file__).resolve().parent / name, destination / name)
    package = destination / "research" / "pilot_evaluation"
    package.mkdir(parents=True)
    for source in (project / "research" / "pilot_evaluation").iterdir():
        if source.is_file() and source.suffix in (".py", ".md"):
            shutil.copy2(source, package / source.name)
    for relative in ("research/dynamic_benchmark/metrics.py", "research/dynamic_benchmark/tri_indicators.py",
                     "research/expansion_audit/metrics.py"):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(project / relative, target)


def _analyze_stages(runs, context, out):
    from provenance import inspect_provenance
    from stage_accounting import stage_costs
    tables = {key: [] for key in ("stage-costs", "source-costs", "admission-provenance", "working-populations",
                                  "working-stage-transitions", "selection-boundaries", "admission-provenance-summary")}
    ledgers, stops = [], []
    for run in runs:
        print("ANALYZE", run["instance"], run["seed"], run["arm"], flush=True)
        provenance = inspect_provenance(run, context[run["instance"]])
        costs, sources, ledger = stage_costs(run, context[run["instance"]], provenance["admissions"])
        tables["stage-costs"].extend(costs)
        tables["source-costs"].extend(sources)
        for name, key in (("admission-provenance", "admissionRows"), ("working-populations", "workingRows"),
                          ("working-stage-transitions", "transitionRows"), ("selection-boundaries", "selectionRows"),
                          ("admission-provenance-summary", "summaryRows")):
            tables[name].extend(provenance[key])
        ledgers.append(ledger)
        stops.append({"instance": run["instance"], "seed": run["seed"], "arm": run["arm"],
                      "stop": provenance["stop"], "limitations": provenance["limitations"]})
    for name, rows in tables.items():
        write_csv(out / (name + ".csv"), rows)
        write_json(out / (name + ".json"), rows)
    write_json(out / "stage-telescopes.json", ledgers)
    write_json(out / "provenance-boundaries.json", stops)
    return tables, ledgers


def _complete_analysis(root, out, plan, costs):
    statistics_start=time.perf_counter()
    import numpy
    import matplotlib
    from analysis_tables import contexts, convergence_rows, final_tables, reference_rows
    from comparisons import pairwise_comparisons
    from plotting import render_figures
    from report_text import fee_summary, write_report
    if not read_json(root / "science-complete.json").get("passed"):
        raise ValueError("Complete-batch scientific receipt is required before statistics")
    runs = load_runs(root, plan)
    context = contexts(runs, plan)
    full, flat, fronts = final_tables(runs, context, plan)
    convergence = convergence_rows(runs, context, plan)
    pairs = pairwise_comparisons(full, plan)
    write_json(out / "reference-fronts.json", reference_rows(context))
    write_json(out / "final-metrics.json", full)
    write_csv(out / "final-metrics.csv", flat)
    write_csv(out / "fronts.csv", fronts)
    write_json(out / "fronts.json", fronts)
    write_csv(out / "convergence.csv", convergence)
    write_json(out / "convergence.json", convergence)
    write_json(out / "pairwise.json", pairs)
    write_csv(out / "pairwise.csv", [row for item in pairs["comparisons"] for row in item["rawPairs"]])
    tables, ledgers = _analyze_stages(runs, context, out)
    statistics_seconds=time.perf_counter()-statistics_start
    plotting_start=time.perf_counter()
    figures = render_figures(full, convergence, tables["stage-costs"], plan, out / "figures")
    plotting_seconds=time.perf_counter()-plotting_start
    summary = {"status": "ANALYSIS_AND_EXPORTS_COMPLETE_VISUAL_AND_INDEPENDENT_AUDIT_SEPARATE",
               "scienceRuns": len(runs), "actualFeesByScope": fee_summary(costs),
               "offlineStatisticsSeconds": statistics_seconds, "offlinePlottingSeconds": plotting_seconds,
               "stageHVKernel": "moocore0.3.2 exact minimization HV; separately checked against frozen Python sweep",
               "scienceSuccessfulFE": sum(run["receipt"]["successful"] for run in runs),
               "finalMetricsRows": len(full), "convergenceRows": len(convergence),
               "admissionProvenanceRows": len(tables["admission-provenance"]), "stageRows": len(tables["stage-costs"]),
               "allStageTelescopesMatchedFinalHV": len(ledgers) == len(runs),
               "eafDisplay": "SUPPRESSED_AT_3_SEEDS", "eafDifferenceDisplay": "SUPPRESSED_AT_3_SEEDS",
               "sharedExclusiveSeconds": None, "sharedTimeStatus": "NOT_OBSERVED_DO_NOT_USE_COOPERATION_SUBSYSTEM_AS_EXCLUSIVE",
               "winner": None, "sameTimeQualityClaim": False, "causalPhasePercentages": False,
               "figures": [item["stem"] for item in figures],
               "pairedComparisons": [{key: item[key] for key in ("candidate", "control", "primary", "byInstance")} for item in pairs["comparisons"]],
               "runtime": {"platform": platform.system(), "python": sys.version, "numpy": numpy.__version__, "matplotlib": matplotlib.__version__}}
    write_json(out / "summary.json", summary)
    write_report(out / "REPORT.md", summary, full, pairs, plan)
    return summary


def main(args):
    start=time.perf_counter()
    require_linux()
    project = _project_imports()
    root = args.root.resolve()
    destination, attempt = _new_attempt(root, args.output)
    try:
        plan = read_json(root / "protocol.json")
        write_json(attempt / "protocol.json", plan)
        costs = actual_costs(root)
        write_json(attempt / "actual-costs.json", costs)
        write_csv(attempt / "actual-costs.csv", costs)
        _save_sources(attempt, project)
        summary = _complete_analysis(root, attempt, plan, costs)
        write_json(attempt/"analysis-runtime.json", {"totalSeconds":time.perf_counter()-start,
                    "statisticsSeconds":summary["offlineStatisticsSeconds"],"plottingSeconds":summary["offlinePlottingSeconds"]})
        if destination.exists():
            raise FileExistsError("Destination appeared during analysis; retain this attempt")
        attempt.rename(destination)
        print("REPORT_COMPLETE", destination, summary["scienceRuns"], flush=True)
    except BaseException as error:
        write_json(attempt / "analysis-failure.json", {"type": type(error).__name__, "message": str(error),
                                                       "traceback": traceback.format_exc(), "rawEvidenceUntouched": True})
        print("REPORT_ATTEMPT_RETAINED", attempt, file=sys.stderr, flush=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    main(parser.parse_args())
