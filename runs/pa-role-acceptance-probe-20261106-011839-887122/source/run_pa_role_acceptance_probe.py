"""Complete-loop role-acceptance isolation; not a revival of failed qualification or donor pools."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock
from pa_role_acceptance_support import build, native_case, analyze, SOURCE, INTERFACE
from pa_capability_support import run_case, initial_key
from frozen_classpath_identity import verify_capture
from research.semantic_repair.evidence import digest

METHODS = {"FOUR_JOINT": ("PA_JOINT", "FOUR"), "CENTER_JOINT": ("PA_JOINT", "CENTER"),
           "FOUR_RELABEL": ("PA_RELABEL", "FOUR"), "CENTER_RELABEL": ("PA_RELABEL", "CENTER"),
           "NSGA_DEEP": ("NSGA2_DEEP", "FOUR")}


def protocol():
    previous = read(ROOT / "runs/pa-paid-donor-probe-20261106-001143-747475/protocol.json")
    return {"version": "PA_COMPLETE_ROLE_ACCEPTANCE_ISOLATION-v1", "registered": "2026-11-06",
            "instances": previous["instances"], "seeds": [14590003, 14590037], "methods": METHODS,
            "primary": "FOUR_JOINTvsCENTER_JOINT", "robustness": "FOUR_RELABELvsCENTER_RELABEL",
            "change": "OnlyinitialPaIndividualrole metadata becomesCENTER; storedgenes/initialization/generationmodel/FOS/mixing/donoravailability/order and budget unchanged",
            "effectivePreferences": "FOUR15/55/15/15 extreme/center, CENTER100middlePareto+privatearchiveacceptance. All source initializer roles stillprepare identical genotypes",
            "whyDistinct": "Earlier specialistbridge blocked scalarstates using an additionalCENTERcondition, not allCENTER; priorS/Uchanged the originalQGSsource, not this receiving population. This tests complete-loop necessity, not role-conditionedtrees",
            "modelScope": "OrdinaryPA has original fourroleacceptance but no originalQGS/conditionalsharing integration; no claimfinalalgorithm or role novelty",
            "initials": "All5arms same100rawvectors/objectives perinstance/seed; everyinitial and subsequent attempt fullypaid",
            "engine": "Twoinstances, FOURandCENTERtwofullnativegenerations, allpaidfulltimelineQA and independentreconstruction. FOURfullpaidSHA mustequal the retained13630003NONEreference",
            "engineeringFE": 95600, "scienceFE": 1000000, "maximumActualFE": 1095600,
            "budget": "Eachscientificarm50000successfulactualFE, zero failures; all20runspaid, no archivedprefixreused as independent samples",
            "roleEvidence": "For both modelversions at bothinstances: medianHV1.5effect>=0.5%, medianIGD+symmetricworsening<=0, medianC_AB-C_BA>=0; perseedHV>=-1%,IGD<=5%,Cdelta>=-0.02;medianHV1.25and2direction>=0",
            "notQualification": "StrongNSGAcomparison and JOINTvsRELABEL jointindicators recorded, but no result revives oldordinary500kqualification/learning claim; no newTIMEarm in this mechanismstudy",
            "indicators": "Frozencommonperinstancenorm; HV1.5with1.25/2; IGD+commonNDunion of all5methods/seeds; exactweakdeduplicatedbidirectionalC, equalitycounts; no metricvote",
            "stopping": "Completeall20prespecifiedruns unless engineering/evaluation failure. No role-count/acceptance/seed/modeltuning or pickingRELABELasnewprimary",
            "defaultMainlineChanged": False, "goalAchieved": False}


def counts(root):
    common = [(p.parent, rows(p)[0]) for p in root.rglob("run-receipt.jsonl")]
    native = [rows(p)[0] for p in root.glob("*/ENGINE-*/audit/receipt.jsonl")]
    qa = sum(read(p / "checkpoint-validation.json")["uniqueOfflineDecodes"] for p, _ in common
             if (p / "checkpoint-validation.json").exists())
    return {"commonRuns": len(common), "nativeRuns": len(native),
            "actualAttemptedFE": sum(r["attempted"] for _, r in common) + sum(r["attemptedFE"] for r in native),
            "actualSuccessfulFE": sum(r["successful"] for _, r in common) + sum(r["successfulFE"] for r in native),
            "failedFE": sum(r["failed"] for _, r in common) + sum(r["failedFE"] for r in native),
            "extraFullDecoderQA": qa + sum(r["fullDecoderQA"] for r in native)}


def decision(analysis):
    checked = []
    for instance in analysis["instances"]:
        tests = []
        for row in instance["comparisons"][:2]:
            passed = row["medianHVEffectPct"]["1.5"] >= .5 and row["medianIGDplusSymmetricWorseningPct"] <= 0
            passed = passed and row["medianC_A_B"] - row["medianC_B_A"] >= 0
            passed = passed and all(row["medianHVEffectPct"][str(r)] >= 0 for r in (1.25, 2.))
            passed = passed and all(p["HVEffectPct"]["1.5"] >= -1 and p["IGDplusSymmetricWorseningPct"] <= 5
                                    and p["coverage"]["C_A_B"] - p["coverage"]["C_B_A"] >= -.02 for p in row["pairs"])
            tests.append({"A": row["A"], "B": row["B"], "pass": bool(passed)})
        checked.append({"stem": instance["stem"], "tests": tests, "pass": all(p["pass"] for p in tests)})
    return {"instances": checked, "consistentRoleAcceptanceSignal": all(p["pass"] for p in checked),
            "oldQualificationRevived": False, "goalAchieved": False}


def validate_identity(root, cp):
    captured = 0
    for path in root.rglob("loaded-identity.jsonl"):
        capture, = rows(path)
        verify_capture(capture, cp)
        assert capture["javaVersion"] == "17.0.12"
        captured += 1
    assert captured == 24
    for name, old in read(root / "source-hashes.json").items():
        assert digest(root / "source" / name) == old
    for name in ("PaPopulation.java", "PaPaidEvaluation.java", "PaCapabilitySearch.java"):
        paths = list((ROOT / "src").rglob(name))
        assert len(paths) == 1 and digest(paths[0]) == digest(INTERFACE / "source" / name)
    write_once(root / "identity-and-defaults.json", {"recordedRuntimeCapturesChecked": captured,
               "allRecordedClassesMatchDeclaredClasspath": True, "productionDefaultsUnchanged": True})


def science(root, cp, plan):
    for i, spec in enumerate(plan["instances"]):
        stem = spec["stem"]
        for j, seed in enumerate(plan["seeds"]):
            expected = None
            cases = list(METHODS.items())
            shift = (i + j) % len(cases)
            for name, (arm, mode) in cases[shift:] + cases[:shift]:
                folder, receipt = run_case(root, cp, stem, arm, f"{seed}/{name}", 50000, seed,
                                           vm_settings={"research.pa.preferenceMode": mode})
                key = initial_key(folder)
                if expected is None:
                    expected = key
                else:
                    assert key == expected
                if arm.startswith("PA_"):
                    assert receipt["search"]["preference.mode"] == mode
                    desired = {"MAKESPAN": 15, "CENTER": 55, "ENERGY": 15, "WORKER_COST": 15} if mode == "FOUR" else {"CENTER": 100}
                    for role in ("MAKESPAN", "CENTER", "ENERGY", "WORKER_COST"):
                        assert receipt["search"]["preference.initial." + role] == desired.get(role, 0)


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        root = ROOT / "runs" / datetime.now().strftime("pa-role-acceptance-probe-%Y%m%d-%H%M%S-%f")
        root.mkdir(); plan = protocol(); write_once(root / "protocol.json", plan)
        print("PA_ROLE_ACCEPTANCE_ROOT", root, flush=True)
        try:
            for spec in plan["instances"]:
                shutil.copytree(SOURCE / spec["stem"] / "inputs", root / spec["stem"] / "inputs")
            cp = build(root)
            for name in (Path(__file__).name, "pa_role_acceptance_support.py", "pa_capability_support.py"):
                shutil.copy2(Path(__file__).with_name(name), root / "source" / name)
            write_once(root / "controller-hashes.json", {p.name: digest(p) for p in (root / "source").glob("*.py")})
            native = [native_case(root, cp, spec["stem"], mode) for spec in plan["instances"] for mode in ("FOUR", "CENTER")]
            write_once(root / "engineering.json", {"passed": True, "results": native})
            print("PA_ROLE_ACCEPTANCE_ENGINEERING_PASSED", flush=True)
            science(root, cp, plan)
            analysis = analyze(root, plan)
            fees = counts(root)
            assert fees["actualSuccessfulFE"] == fees["actualAttemptedFE"] == 1095600 and fees["failedFE"] == 0
            validate_identity(root, cp)
            outcome = decision(analysis)
            write_once(root / "analysis.json", {**analysis, "decision": outcome, **fees})
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error), **counts(root)})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", "decision": outcome, **fees, "goalAchieved": False})
        print("PA_ROLE_ACCEPTANCE_COMPLETE", outcome, fees, flush=True)


if __name__ == "__main__":
    main()
