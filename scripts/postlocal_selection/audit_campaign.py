"""Exact engineering bridge/cutoff and paired science evidence reconciliation."""
from audit_core import read_json, require


def costs(rows):
    return dict(runs=len(rows), attempted=sum(r["attemptedFE"] for r in rows),
                successful=sum(r["successfulFE"] for r in rows), failed=sum(r["failedFE"] for r in rows))


def engineering(root, plan, rows):
    require(len(rows) == 20, "Engineering requires exactly twenty preserved trajectories")
    checks = []
    for stem in plan["instances"]:
        context = [r for r in rows if r["instance"] == stem]
        require(all(r["sourceSeed"] == plan["seeds"][0] for r in context), "Wrong engineering source seed")
        by_label = {r["label"]: r for r in context}
        budget = plan["passFE"][stem]
        cutoffs = [1, 2, budget, 2 * budget, 3 * budget - 1]
        labels = {"RAW_NATIVE", "RAW_ROLE", "POST_ROLE", "POST_PARETO", "FAIL_2"}
        labels.update("CUT_" + str(value) for value in cutoffs)
        require(set(by_label) == labels and len(context) == len(labels), "Missing/duplicate engineering case")
        native, raw = by_label["RAW_NATIVE"], by_label["RAW_ROLE"]
        require(native["nativeObserver"] and not raw["nativeObserver"] and
                native["paidSHA256"] == raw["paidSHA256"], "Native singleton/adapter bridge differs")
        base = root / "engineering" / stem / str(plan["seeds"][0])
        for artifact in ("after.json", "front.json", "selected.json"):
            require(read_json(base / "RAW_NATIVE" / artifact) == read_json(base / "RAW_ROLE" / artifact),
                    "Native/adapter final artifact differs: " + artifact)
        post, pareto = by_label["POST_ROLE"], by_label["POST_PARETO"]
        require(post["prefix2BSHA256"] == pareto["prefix2BSHA256"], "POST arms differ before selection")
        for index in (0, 1):
            left = read_json(base / "POST_ROLE" / "passes.json")[index]
            right = read_json(base / "POST_PARETO" / "passes.json")[index]
            require(left["afterPopulation"] == right["afterPopulation"] and
                    left["internalArchive"] == right["internalArchive"] and
                    left["publicArchive"] == right["publicArchive"], "POST polish working states/archives differ")
        for limit in cutoffs:
            cut = by_label["CUT_" + str(limit)]
            require(cut["feLimit"] == cut["successfulFE"] == limit and
                    cut["paidSHA256"] == post["paidPrefixes"][str(limit)], "Cutoff is not exact full-run paid prefix")
        failure = by_label["FAIL_2"]
        require(failure["paidSHA256"] == post["paidPrefixes"]["1"] and
                failure["proposalPrefixes"]["2"] == post["proposalPrefixes"]["2"],
                "Injected failure is not the exact first-two-proposal prefix")
        require(all(row["existingTimelinePhysicsQACount"] == row["successfulFE"] for row in context),
                "Engineering physics QA did not check every successful candidate")
        require(sum(row["existingImportFullQACount"] for row in context) == 200,
                "Engineering input full QA not exactly once per context")
        checks.append(dict(instance=stem, nativeObserverAdapterSamePaidStream=True,
                           postFirstTwoPassesSamePaidStreamAndStates=True, cutoffPrefixes=cutoffs,
                           expectedFailurePartialReplay=True))
    total = costs(rows)
    require(total["attempted"] == plan["engineeringAttemptedFE"] and
            total["failed"] == plan["engineeringExpectedFailures"], "Engineering protocol cost differs")
    return dict(passed=True, checks=checks, costs=total)


def science(root, plan, rows):
    require(len(rows) == 18, "Science requires exactly eighteen complete trajectories")
    checks, contexts = [], set()
    for stem in plan["instances"]:
        for seed in plan["seeds"]:
            context = [r for r in rows if r["instance"] == stem and r["sourceSeed"] == seed]
            require(len(context) == 3 and {r["label"] for r in context} == set(plan["arms"]),
                    "Missing/extra science arm in context")
            require(all(r["complete"] and r["failedFE"] == 0 and not r["nativeObserver"] and
                        r["successfulFE"] == 3 * plan["passFE"][stem] and
                        r["existingTimelinePhysicsQACount"] == 0 for r in context),
                    "Partial, native-control or physics-QA arm entered science")
            by_mode = {r["mode"]: r for r in context}
            require(by_mode["POST_ROLE"]["prefix2BSHA256"] == by_mode["POST_PARETO"]["prefix2BSHA256"],
                    "Science POST arms have unequal paid polish prefix")
            if seed == plan["seeds"][0]:
                for row in context:
                    prior = read_json(root / "engineering" / stem / str(seed) / row["mode"] / "receipt.json")
                    require(prior["paidSHA256"] == row["paidSHA256"], "Disabling offline physics QA changed search")
            expected_imports = 0 if seed == plan["seeds"][0] else 200
            require(sum(r["existingImportFullQACount"] for r in context) == expected_imports,
                    "Science context imported-objective QA count differs")
            contexts.add((stem, seed))
            checks.append(dict(instance=stem, sourceSeed=seed, equalThreePassPaidBudget=True,
                               postFirstTwoPassesSamePaidStream=True,
                               matchesEngineeringWithQAOff=seed == plan["seeds"][0]))
    require(len(contexts) == len(plan["instances"]) * len(plan["seeds"]), "Science context coverage differs")
    total = costs(rows)
    require(total["attempted"] == total["successful"] == plan["scienceFE"] and total["failed"] == 0,
            "Science planned fixed FE differs")
    return dict(passed=True, checks=checks, costs=total)
