"""Linux-only offline analysis; never runs or resumes a search algorithm."""
from analysis_common import (arguments, capture_folder, initialize, json_lines, protocol,
                             read_json, record_failure, require, run_folder, write_json)


def analyze_instance(root, spec, plan):
    from analysis_metrics import compare, frozen_scale, gain_metrics, metrics, reference_from
    from analysis_supply import supply_summary
    scale, stem = frozen_scale(spec), spec["stem"]
    fronts = {(seed, arm): read_json(run_folder(root, stem, seed, arm) / "front.json")
              for seed in plan["seeds"] for arm in plan["arms"]}
    reference, source_ids = reference_from(fronts)
    observations, captures = [], []
    for seed in plan["seeds"]:
        capture = capture_folder(root, stem, seed)
        captures.append(dict(seed=seed, receipt=read_json(capture / "capture.json")))
        background = metrics(read_json(capture / "background.json"), reference, scale)
        for arm in plan["arms"]:
            folder = run_folder(root, stem, seed, arm)
            receipt = read_json(folder / "receipt.json")
            require(receipt["successful"] == receipt["attempted"] == receipt["expectedFE"]
                    and receipt["failed"] == 0 and receipt.get("error") is None, "Incomplete or failed science run")
            require(sum(1 for _ in json_lines(folder / "steps.jsonl")) == receipt["successful"], "Incomplete step evidence")
            final = metrics(fronts[seed, arm], reference, scale)
            working = metrics([r["objectives"] for r in read_json(folder / "after.json")], reference, scale)
            observations.append(dict(seed=seed, arm=arm, successfulFE=receipt["successful"],
                searchSeconds=receipt["searchSeconds"], prepareSeconds=receipt.get("prepareSeconds", 0.0),
                A0=background, finalArchive=final, workingPopulation=working,
                gain=gain_metrics(final, background, receipt), supply=supply_summary(folder, capture)))
    comparisons = compare(observations, plan["seeds"], "finalArchive")
    comparisons.extend(compare(observations, plan["seeds"], "workingPopulation"))
    return dict(instance=stem, normalization=spec["normalization"], reference=reference.tolist(),
                referenceSourceIds=source_ids, referenceOfflineOnly=True,
                captures=captures, observations=observations, comparisons=comparisons)


def main():
    args = arguments(__doc__)
    output = initialize(args, "analyze")
    try:
        plan = protocol(args.root)
        cases = []
        for spec in plan["instances"]:
            print(f'ANALYZE_INSTANCE {spec["stem"]}', flush=True)
            cases.append(analyze_instance(args.root, spec, plan))
        result = dict(instances=cases, newSearchFE=0, newDecoderCalls=0,
            scientificNewFE=sum(row["successfulFE"] for case in cases for row in case["observations"]),
            scope="One mature fixed-model complete local pass, not a 500k algorithm comparison",
            EAFProduced=False, independentInnovationClaim=False, sameTimeAdvantageProved=False,
            physicalObjectivesIndependentlyDecoded=False, independentAuditPassed=False,
            hypothesisGate="Descriptive donor-supply probe; no post-hoc promotion gate")
        write_json(output / "analysis.json", result)
        from analysis_reporting import write_markdown, write_tables
        write_tables(output, result)
        write_markdown(output, result)
        write_json(output / "status.json", dict(status="COMPLETE", analysis=str(output / "analysis.json")))
        print(f'ANALYSIS_COMPLETE {output / "analysis.json"}', flush=True)
    except Exception as error:
        record_failure(output, error)
        raise


if __name__ == "__main__":
    main()
