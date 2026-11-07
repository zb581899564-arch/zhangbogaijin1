"""Read-only closeout of the preregistered three-gate branch; no optimizer is launched."""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once

OPPORTUNITY = ROOT / "runs/three-gates-opportunity-20261104-141216-202951"
MODULE = ROOT / "runs/three-gates-module-20261104-142126-461754"
LINKED = ROOT / "runs/three-gates-linked-20261104-142820-433007"


def witnesses():
    result = {}
    for arm in ("BASE", "RANDOM", "LINKED", "NSGA"):
        if arm == "NSGA":
            result[arm] = {"instrumented": False, "reason": "Canonical particle-history/survival hooks apply only "
                           "to HMOPSO. Raw inherited stage attributes must not classify NSGA global events."}
            continue
        data, = rows(LINKED / arm / "bundle-witness.jsonl")
        counts = data["counts"]
        summed = lambda suffix: sum(v for k, v in counts.items() if k.endswith(suffix))
        result[arm] = {"globalPaid": summed(".globalPaid"),
                       "dominatesParent": summed(".dominatesParent"),
                       "dominatedByParent": summed(".dominatedByParent"),
                       "representedInPbestHistory": summed(".retainedInPbestHistory"),
                       "selectedAsPbest": summed(".selectedAsPbest"),
                       "firstGlobalAdmissions": counts.get("gen1.archiveAdmission.global"),
                       "secondGlobalAdmissions": counts.get("gen2.archiveAdmission.global"),
                       "selection": data["completedSelections"]}
    return result


def main():
    root = ROOT / "runs" / datetime.now().strftime("three-gates-closeout-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    for p in (OPPORTUNITY, MODULE, LINKED):
        assert read(p / "status.json")["status"] == "COMPLETE"
    receipt = read(MODULE / "receipt.json")
    assert receipt["attempted"] == receipt["successful"] == 5680 and receipt["failed"] == 0
    comparison = read(LINKED / "comparison.json")
    assert comparison["gate2"] == "STOP" and comparison["gate3"] == "NOT_TRIGGERED"
    paid, qa, search_seconds, process_seconds = 5680, 0, {}, {}
    for arm in ("BASE", "RANDOM", "LINKED", "NSGA"):
        folder = LINKED / arm
        r, = rows(folder / "run-receipt.jsonl")
        assert r["attempted"] == r["successful"] == r["decoder"]["dynamic.evaluations"] == 500000
        assert r["failed"] == 0
        assert {s: r["search"][s + ".evaluations"] for s in ("initialization", "global", "inter", "intra")} == {
            "initialization": 100, "global": 10000, "inter": 549, "intra": 489351}
        curve = rows(folder / "anytime.jsonl")
        assert curve[-1]["fe"] == 500000 and all(x["reached"] for x in curve)
        final_objectives = {tuple(x["objectives"]) for x in rows(folder / "solutions.jsonl")}
        assert {tuple(x) for x in curve[-1]["front"]} == final_objectives
        # Physical operations must reconcile even when an evaluation reuses exact immutable prefixes.
        assert r["decoder"]["dynamic.recomputedOperations"] + r["decoder"]["dynamic.reusedOperations"] == 40 * 500000
        paid += r["successful"]
        qa += read(folder / "summary.json")["offlineValidationDecodes"]
        search_seconds[arm] = r["searchSeconds"]
        process_seconds[arm] = read(folder / "process.json")["wallSeconds"]
    for name, expected in read(LINKED / "class-hashes.json").items():
        assert sha256((LINKED / "classes" / name).read_bytes()).hexdigest() == expected
    audit = {"opportunity": str(OPPORTUNITY), "moduleProbe": str(MODULE), "candidateTrial": str(LINKED),
             "gate1": {"status": "DIAGNOSIS_COMPLETE_ONE_CANDIDATE_TESTED", "originality": "NOT_ESTABLISHED",
                       "mainFinding": "NSGA advantage concentrated at low Cmax; all-module oracle exchange "
                                      "recovers targets while partial module mixing usually destroys them. "
                                      "This supports coupling, not a guarantee that moved-job linkage is the right rule."},
             "gate2": {"status": "STOP", "reason": "Candidate HV at 500k is -1.697% vs BASE, -1.171% vs RANDOM, "
                       "-2.940% vs matched NSGA; direction remains negative at both alternative reference points.",
                       "comparison": comparison, "witness": witnesses()},
             "gate3": {"status": "NOT_TRIGGERED", "executedRuns": 0,
                       "reason": "Preregistered conditional branch requires gate2 positive evidence; none obtained."},
             "budget": {"paidOptimizationFE": 2000000, "paidAttributionFE": 5680, "allPaidFE": paid,
                        "failedEvaluations": 0, "fullModuleDecodeOperations": 227200,
                        "originalEndpointReplaysIncludedInModuleFE": 710, "offlineFinalQAFullDecodes": qa,
                        "totalPhysicalEvaluationCallsIncludingQA": paid + qa,
                        "searchSeconds": search_seconds, "JVMWallSeconds": process_seconds,
                        "candidateCampaignWallSeconds": read(LINKED / "status.json")["wallSeconds"],
                        "moduleProbeSearchSeconds": receipt["searchSeconds"],
                        "notMeasured": "Module compile/process wall and complete agent reasoning time are not reconstructed."},
             "limits": ["Single development instance and seed; no general four-subgroup rejection.",
                        "All-module exchange uses final oracle NSGA donors only for diagnosis, never search feedback.",
                        "Module effects with FA changes include deterministic legality repair; not pure continuous-factor causal effects.",
                        "InheritedJobs counts tuple-copy writes, not distinct net changes after family restoration.",
                        "Witnesses count exact genotype representation, not a newly inserted historical identity.",
                        "All global candidates become current particles; history/pbest and final survival are different events.",
                        "Generation-2 discoveries are not causal credit to a particular generation-1 source.",
                        "NSGA does not use the canonical particle-witness hooks; inherited raw stage tags are not "
                        "a valid NSGA stage decomposition and are excluded from attribution.",
                        "Timing includes read-only witnesses; the four-subgroup witness does more work than the NSGA witness. "
                        "Do not claim an uninstrumented same-time cross-algorithm ranking. Terminal FE failure decides the stop.",
                        "No beta=0 mechanism control was triggered; fatigue-specific contribution remains unproven."],
             "retainedEngineeringFailures": [
                 {"directory": "runs/three-gates-module-20261104-142051-923394", "phase": "javac interface mismatch", "FE": 0},
                 {"directory": "runs/three-gates-module-20261104-142113-766424", "phase": "javac interface mismatch", "FE": 0}],
             "nextRoute": "Retain four roles and existing sharing. Stop moved-job linkage, schedule allocation sweeps, "
                          "and failed pool selector/adjoint/reference variants. No further candidate is auto-selected. "
                          "A future proposal must show recipient-compatible schedule construction and incremental value "
                          "over ordinary joint operators before requesting broader experiments.",
             "scope": {"productionChanged": False, "originalMaterialsChanged": False,
                       "formalExpansionStarted": False, "publicPushPerformed": False}}
    write_once(root / "closeout.json", audit)
    shutil.copy2(Path(__file__), root)
    print("THREE_GATES_CLOSEOUT", root)
    print("PAID_FE", paid, "QA", qa, "DECISION", comparison["gate2"], comparison["gate3"])


if __name__ == "__main__":
    main()
