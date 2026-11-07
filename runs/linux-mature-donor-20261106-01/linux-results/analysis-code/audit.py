"""Linux-only independent causal replay and offline metric audit."""
from analysis_common import (arguments, capture_folder, initialize, protocol, read_json,
                             record_failure, require, run_folder, write_json)


def audit_case(root, spec, seed, arms):
    from collections import Counter
    from audit_capture import capture_data, verify_imports
    from audit_replay import replay
    stem = spec["stem"]
    jobs, factories = int(stem.split("_")[0]), int(stem.split("_")[2])
    captured = capture_data(capture_folder(root, stem, seed), jobs, factories)
    common, checks = None, []
    for arm in arms:
        folder = run_folder(root, stem, seed, arm)
        current = {name: read_json(folder / f"{name}.json") for name in ("before", "models", "views")}
        if common is None:
            common = current
        require(current == common, f"Arm changed initial states, fixed models or external neutral views: {stem}/{seed}/{arm}")
        catalog = verify_imports(current["before"], current["views"], captured, jobs, factories)
        checked = replay(folder, captured, current["before"], current["models"], current["views"],
                         catalog, jobs, factories, seed, arm)
        checks.append(checked)
        print(f'REPLAY_PASS {stem} {seed} {arm} {checked["successfulFE"]}', flush=True)
    require(len({r["scheduleSHA256"] for r in checks}) == 1,
            "Masks, receiver visitation or proposal RNG schedule differs between arms")
    raw = Counter(("free80" if r["family"] < 0 else "fixed20", r["source"])
                  for r in captured["initial"])
    from audit_capture import points_tsv
    raw.update(("free80" if r["family"] < 0 else "fixed20", r["source"])
               for r in points_tsv(capture_folder(root, stem, seed) / "points.tsv")[100:])
    unique = Counter(("free80" if r["family"] < 0 else "fixed20", r["source"])
                     for r in captured["expectedExternal"])
    return dict(instance=stem, sourceSeed=seed, capture=captured["receipt"], runs=checks,
                rawCaptureCounts={f"{g}/{s}": n for (g, s), n in sorted(raw.items())},
                uniqueExternalCounts={f"{g}/{s}": n for (g, s), n in sorted(unique.items())},
                initialModelsViewsAndProposalScheduleEqual=True,
                externalDeduplicationAndPaidAvailabilityVerified=True)


def verify_analysis_scope(analysis, total):
    require(analysis["scientificNewFE"] == total, "Reported complete-pass FE total differs")
    for key in ("EAFProduced", "independentInnovationClaim", "sameTimeAdvantageProved",
                "physicalObjectivesIndependentlyDecoded"):
        require(analysis[key] is False, f"Unsupported scope claim: {key}")
    require(analysis["newSearchFE"] == analysis["newDecoderCalls"] == 0, "Offline report claims new search")


def verify_supply_reports(analysis, cases):
    for case in cases:
        report = next(r for r in analysis["instances"] if r["instance"] == case["instance"])
        captured = [r for r in report["captures"] if r["seed"] == case["sourceSeed"]]
        require(len(captured) == 1 and captured[0]["receipt"] == case["capture"], "Reported capture ledger differs")
        for run in case["runs"]:
            row = next(r for r in report["observations"] if r["seed"] == case["sourceSeed"] and r["arm"] == run["arm"])
            supply = row["supply"]
            require(supply["byReceiverDomainAndSource"] == run["byReceiverDomainAndSource"], "Reported donor draw/accept/admission counts differ")
            for key in ("rawCaptureCounts", "uniqueExternalCounts"):
                require(supply[key] == case[key], f"Reported {key} differs")
            for source in ("R", "G", "S", "GS"):
                expected = {key: sum(run["byReceiverDomainAndSource"][f"{g}/{source}"][key] for g in ("free80", "fixed20"))
                            for key in ("proposals", "accepted", "admitted", "equal", "dominated", "fallback")}
                require(supply["byDisjointDonorSource"][source] == expected, "GS was double-counted or source totals differ")
            for domain in ("free80", "fixed20"):
                expected = {key: sum(run["byReceiverDomainAndSource"][f"{domain}/{s}"][key] for s in ("R", "G", "S", "GS"))
                            for key in ("proposals", "accepted", "admitted", "equal", "dominated", "fallback")}
                require(supply["byReceiverDomain"][domain] == expected, "Receiver-domain totals differ")
            require(supply["free80SharedRaw"] == case["rawCaptureCounts"].get("free80/S", 0)
                    and supply["free80SharedAvailable"] == sum(case["uniqueExternalCounts"].get(f"free80/{s}", 0) for s in ("S", "GS")),
                    "Shared-free80 availability was misreported")


def main():
    args = arguments(__doc__, audit=True)
    output = initialize(args, "audit")
    try:
        plan = protocol(args.root)
        result = read_json(args.analysis.resolve(strict=True)) if args.analysis else None
        if result:
            require({c["instance"] for c in result["instances"]} == {s["stem"] for s in plan["instances"]}
                    and len(result["instances"]) == 2, "Analysis instance registry differs")
        cases, metric_checks = [], []
        for spec in plan["instances"]:
            cases.extend(audit_case(args.root, spec, seed, plan["arms"]) for seed in plan["seeds"])
            from audit_metrics import audit_instance_metrics
            reported = next(c for c in result["instances"] if c["instance"] == spec["stem"]) if result else None
            metric_checks.append(audit_instance_metrics(args.root, spec, plan, reported))
        total = sum(r["successfulFE"] for c in cases for r in c["runs"])
        if result:
            verify_analysis_scope(result, total)
            verify_supply_reports(result, cases)
        evidence = dict(passed=True, cases=cases, metricChecks=metric_checks, successfulProbeFE=total,
            newSearchFE=0, newDecoderCalls=0, analysisPath=str(args.analysis.resolve()) if args.analysis else None,
            exactAcceptanceArchiveStateAndCausalDonorReplayVerified=True,
            allPoolsAndRandomDrawsIndependentlyReconstructed=True,
            physicalObjectivesIndependentlyDecoded=False,
            limitations=["No independent physical objective decoder was run; Java per-child physics QA is separate evidence",
                "Frozen model equality and valid full FOS are checked; model learning itself is not independently retrained",
                "Mature complete capture and all paid availability are checked; first eligible PRE_GLOBAL and observer equivalence require controller/source evidence",
                "An empirical final union is offline only; n=3 is descriptive and no EAF or equal-time advantage is claimed"])
        write_json(output / "audit.json", evidence)
        print(f'INDEPENDENT_AUDIT_PASS {output / "audit.json"}', flush=True)
    except Exception as error:
        record_failure(output, error)
        raise


if __name__ == "__main__":
    main()
