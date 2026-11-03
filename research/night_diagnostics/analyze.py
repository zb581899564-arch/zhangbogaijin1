"""Read-only two-campaign H1/H2 diagnostic with zero new FE."""
from datetime import datetime
from pathlib import Path
import shutil
import json
from research.cooperation_review.storage import Sources, csv_write, json_write
from research.cooperation_roles.replay import request_replay
from research.cooperation_roles.tables import aggregate
from .physical import load_materialized, safe_bound
from .contexts import family_contexts, archive_coverage
from .exchange import single_factory_potentials
from .report import write_report
from .gates import suggestions

ROOT = Path(__file__).resolve().parents[2]
CAMPAIGNS = ("cooperation-roles-20261102-231315-641007", "demand-feedback-20261102-234716-144779")


def inventory(root):
    return {str(path.relative_to(root)): (stat.st_size, stat.st_mtime_ns)
        for path in root.rglob("*") if path.is_file() for stat in [path.stat()]}


def request_bounds(request, family, model, identity, source):
    bound = safe_bound(model, family)
    minima = [min(record["objectives"][0] for record in factory["records"]) if factory["records"] else None
              for factory in request["factories"]]
    impossible = request["cap"] < bound["safeCmaxLB"] - 1e-9 * max(1., bound["safeCmaxLB"])
    missing = any(value is None or value > request["cap"] for value in minima)
    if request["parentObjectives"][0] < bound["safeCmaxLB"] - 1e-9 * max(1., bound["safeCmaxLB"]):
        raise ValueError("Purported safe bound exceeds a paid parent Cmax")
    return identity | {"request": request["request"], "family": request["family"], "cycle": request["cycle"],
        "tight": request["cycle"] < 3, "cap": request["cap"], **bound,
        "capBelowCertifiedSafeLB": impossible, "poolMissingAtCap": missing,
        "poolMissingButNotCertifiedImpossible": missing and not impossible,
        "poolMinC": json.dumps(minima), "perJobFA": json.dumps(family), "source": source}


def run(output=None):
    output = Path(output).resolve() if output else ROOT / "runs" / datetime.now().strftime("night-diagnostics-%Y%m%d-%H%M%S-%f")
    if output.parent != (ROOT / "runs").resolve() or not output.name.startswith("night-diagnostics-"):
        raise ValueError("Independent runs/night-diagnostics-* output required")
    roots = [ROOT / "runs" / name for name in CAMPAIGNS]
    before = {root.name: inventory(root) for root in roots}; sources = Sources()
    for name in ("AGENTS.md", "README.md", "docs/动态模型合同-v1.md", "docs/整厂共享组合的性质与边界.md",
                 "docs/四子群互补来源与专业分工三步结果-2026-11-02.md", "docs/模型合同.md"):
        sources.text(ROOT / name)
    tables = {name: [] for name in ("families", "request-bounds", "archive-coverage", "archive-family-fronts",
        "archive-fa-diversity", "single-factory-potentials", "single-request-summary")}
    for root in roots:
        status = sources.json(root / "final-status.json"); protocol = sources.json(root / "protocol.json")
        if status["completed"] != protocol["runs"]:
            raise ValueError("Incomplete historical campaign")
        for spec in protocol["instances"]:
            stem = spec["stem"]; model = load_materialized(root / "inputs" / stem, stem, sources)
            for seed in protocol["algorithm_seeds"]:
                identity = {"campaign": root.name, "instance": stem, "seed": seed}
                matches = list((root / "trials").glob("*/" + stem + "/" + str(seed) + "/SHARE_SPECIAL"))
                if len(matches) != 1:
                    raise ValueError("Missing unique frozen SHARE_SPECIAL owner")
                folder = matches[0]; trace_path = folder / "cooperation-evidence.jsonl"
                trace = sources.lines(trace_path); requests = trace[1:]
                families = family_contexts(requests, model)
                for family, fa in families.items():
                    tables["families"].append(identity | {"family": family, "perJobFA": json.dumps(fa),
                        "jobsPerFactory": json.dumps([fa.count(f) for f in range(model["factories"])]),
                        **safe_bound(model, fa), "source": str(trace_path), "inputSource": model["source"],
                        "setupSource": model["setupSource"], "fatigueSource": model["fatigueSource"]})
                for request in requests:
                    request_replay(request)
                    tables["request-bounds"].append(request_bounds(request, families[request["family"]], model, identity, str(trace_path)))
                    candidates, summary = single_factory_potentials(request, identity, str(trace_path))
                    tables["single-factory-potentials"].extend(candidates); tables["single-request-summary"].append(summary)
                for label in protocol["variants"]:
                    archive = folder.parent / label
                    row, fronts, diversity = archive_coverage(archive, identity | {"variant": label}, families, spec, model, sources)
                    row["recoveredFamilyCount"] = len(families)
                    tables["archive-coverage"].append(row); tables["archive-family-fronts"].extend(fronts)
                    tables["archive-fa-diversity"].extend(diversity)
    aggregate_tables(tables)
    unchanged = all(before[root.name] == inventory(root) for root in roots)
    if not unchanged:
        raise ValueError("Historical source root changed during audit")
    receipt = {"status": "ZERO_FE_NIGHT_DIAGNOSTICS_COMPLETE", "searchFE": 0, "decodeFE": 0,
        "optimizerStarted": False, "potentialObjectivesFedBackToSearch": False,
        "historicalRootsUnchangedBySizeAndMtime": unchanged,
        "historicalRootFileCounts": {name: len(files) for name, files in before.items()},
        "familyContexts": len(tables["families"]), "requests": len(tables["request-bounds"]),
        "numericSingleFactorySubstitutions": len(tables["single-factory-potentials"]),
        "samplePolicy": "first8+last8 requests; no random sample or full-history reconstruction",
        "causalWholeGeneLossIdentified": False, "campaignsPooledAsIndependentReplicates": False,
        "safeLB": "max(job path min-b sum, factory-stage min-b load/min(M,W)); beta>=0,u>=0; optimistic necessary condition only"}
    output.mkdir(exist_ok=False)
    for name, rows in tables.items():
        if rows:
            csv_write(output / (name + ".csv"), rows)
    csv_write(output / "sources.csv", sources.unchanged()); json_write(output / "receipt.json", receipt)
    json_write(output / "gate-suggestions.json", suggestions(tables))
    write_report(output, tables, receipt)
    target = output / "analysis-source"; target.mkdir()
    for path in Path(__file__).parent.glob("*.py"):
        shutil.copy2(path, target / path.name)
    print(output)
    return output


def aggregate_tables(tables):
    coverage_fields = [key for key in tables["archive-coverage"][0] if key not in ("campaign", "instance", "seed", "variant", "source")]
    tables["coverage-instances"] = aggregate(tables["archive-coverage"], ("campaign", "instance", "variant"), coverage_fields)
    for row in tables["coverage-instances"]:
        group = [item for item in tables["archive-coverage"] if all(item[key] == row[key] for key in ("campaign", "instance", "variant"))]
        row["exclusiveHVResolvedSeeds"] = sum(item["nonFamilyExclusiveHVFraction"] is not None for item in group)
    tables["coverage-summary"] = aggregate(tables["coverage-instances"], ("campaign", "variant"), coverage_fields)
    request_runs = []
    for group in {(row["campaign"], row["instance"], row["seed"]) for row in tables["request-bounds"]}:
        bounds = [row for row in tables["request-bounds"] if (row["campaign"], row["instance"], row["seed"]) == group]
        tight = [row for row in bounds if row["tight"]]
        singles = [row for row in tables["single-request-summary"] if (row["campaign"], row["instance"], row["seed"]) == group]
        row = dict(zip(("campaign", "instance", "seed"), group)) | {"capturedRequests": len(bounds), "capturedTightRequests": len(tight),
            "impossibleTightFraction": sum(row["capBelowCertifiedSafeLB"] for row in tight) / len(tight) if tight else None,
            "missingTightFraction": sum(row["poolMissingAtCap"] for row in tight) / len(tight) if tight else None,
            "missingNotCertifiedImpossibleTightFraction": sum(row["poolMissingButNotCertifiedImpossible"] for row in tight) / len(tight) if tight else None}
        for field in ("anyMaterialParetoImprovement", "anyMaterialParetoAtCap", "anySingleMGainAtLeast01Percent", "anySingleEGainAtLeast01Percent", "anySingleWGainAtLeast01Percent", "allFactoryAssemblyFeasible"):
            row[field + "Fraction"] = sum(item[field] for item in singles) / len(singles) if singles else None
        request_runs.append(row)
    tables["request-run-summary"] = sorted(request_runs, key=lambda row: (row["campaign"], row["instance"], row["seed"]))
    fields = [key for key in request_runs[0] if key not in ("campaign", "instance", "seed")]
    tables["request-instance-summary"] = aggregate(request_runs, ("campaign", "instance"), fields)
    tables["request-summary"] = aggregate(tables["request-instance-summary"], ("campaign",), fields)
    cycle_fields = ["anyMaterialParetoImprovement", "anyMaterialParetoAtCap", "anySingleMGainAtLeast01Percent", "anySingleEGainAtLeast01Percent", "anySingleWGainAtLeast01Percent", "allFactoryAssemblyFeasible", "bestSingleGainMPercent", "bestSingleGainEPercent", "bestSingleGainWPercent", "allFactoryGainMPercent", "allFactoryGainEPercent", "allFactoryGainWPercent"]
    by_seed = aggregate(tables["single-request-summary"], ("campaign", "instance", "seed", "cycle"), cycle_fields)
    by_instance = aggregate(by_seed, ("campaign", "instance", "cycle"), cycle_fields)
    tables["single-cycle-seeds"] = by_seed; tables["single-cycle-instances"] = by_instance
    tables["single-cycle-summary"] = aggregate(by_instance, ("campaign", "cycle"), cycle_fields)
    origins = {"coverage-instances": "archive-coverage", "coverage-summary": "coverage-instances",
        "request-run-summary": "request-bounds and single-request-summary", "request-instance-summary": "request-run-summary",
        "request-summary": "request-instance-summary", "single-cycle-seeds": "single-request-summary",
        "single-cycle-instances": "single-cycle-seeds", "single-cycle-summary": "single-cycle-instances"}
    for name, origin in origins.items():
        for row in tables[name]:
            row["sourceTable"] = origin + ".csv; matching group keys; equal within-level averaging"
