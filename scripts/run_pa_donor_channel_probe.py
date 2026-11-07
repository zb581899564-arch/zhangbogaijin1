"""Fixed, bounded direct-donor ablation; all original working acceptance rules remain."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock
from pa_capability_support import SOURCE, run_case, initial_key, fees
from pa_donor_channel_build import build, INTERFACE, PROPERTY
from pa_donor_channel_replay import audit
from pa_specialist_bridge_analysis import analyze
from research.semantic_repair.evidence import digest

ENGINE = ROOT / "runs/pa-population-engineering-20261105-164116-698339"
RECOVERY = ROOT / "runs/pa-donor-channel-probe-20261105-215450-025540"
METHODS = {f"{model}_{mode}": (arm, mode) for model, arm in (("JOINT", "PA_JOINT"), ("RELABEL", "PA_RELABEL"))
           for mode in ("LIVE", "REVERT_BRIDGE", "REVERT_COMMON")}
METHODS.update({name: (name, "LIVE") for name in ("NSGA2_DEEP", "FULL_SHARED_DEEP", "LI_RECON_DEEP")})


def protocol():
    old = read(ROOT / "runs/pa-base-qualification-20261105-180835-751659/protocol.json")
    comparisons = [(f"{model}_LIVE", f"{model}_{mode}") for model in ("JOINT", "RELABEL")
                   for mode in ("REVERT_BRIDGE", "REVERT_COMMON")]
    comparisons += [(f"{model}_LIVE", control) for model in ("JOINT", "RELABEL")
                    for control in ("NSGA2_DEEP", "FULL_SHARED_DEEP", "LI_RECON_DEEP")]
    return {"version": "DIRECT_SPECIALIST_DONOR_INCREMENT-v1", "seeds": [14130003, 14130037],
        "instances": [{"stem": s["stem"], "normalization": s["normalization"],
                       "feLimit": 100 + 200 * (2 * int(s["stem"].split("_")[0]) - 1)} for s in old["instances"]],
        "methods": METHODS, "comparisons": comparisons,
        "intervention": "Only cross-role donors from specialists may revert their latest accepted increment to the same slot's previous paid state. BRIDGE=own accepts,CENTERwouldreject at birth;COMMON=both accept. Initial/CENTER/same-role donors staylive.",
        "notChanged": "Original working acceptance, continuation policy, current working samples for model learning, same donor-slot RNG, subset order, four roles, full fees and common external archive",
        "feedback": "Closed-loop paths naturally differ; no claim that candidate streams or future working trajectories remain equal",
        "neutralHistoryView": "Previous paid state gets a physical-neutral per-generation reencoding from independent gen/slot/seed RNG; never advances working RNG. LIVE maintains the same cache and bookkeeping.",
        "commonControlLimit": "COMMON rollback checks general donor freshness, but opportunities/age distributions need not match. It is not a perfectly matched sham or proof of uniquely role-specific value.",
        "engineering": "Three modes on both known two-generation fixtures with all channel transitions reconstructed; LIVE paidSHA/front equals original. Four LIVEcutoffs1/2/101/139 match known prefixes before science.",
        "engineeringEvidenceFE": 143643, "scientificFE": 860400, "maximumNewSearchFE": 996143,
        "totalPaidEvidenceFE": 1004043, "reusedEngineeringFE": 7900,
        "engineeringRecovery": {"root": str(RECOVERY), "cause": "Python audit paid counter shadowed the paid event method; fixed handler name, no Java/search/seed change",
            "alreadyExecuted": "20_8_5_1 ENGINEERING-LIVE 7900FE, independently reconstructed after handler fix; reuse once, not rerun or count as new science",
            "effectiveIdentity": "New controller/fixed Python audit + byte-identical Java classes + retained original failure and reused receipt"},
        "sampling": "All36scientific runs, both models, two development instances and two fresh seeds; no winner stopping, seed replacement, model selection or skipped negative cells",
        "metrics": "Joint HV1.5,sensitivity1.25/2,IGD+NDunion of9methods x2seeds perinstance,exact weak bidirectionalC on unique raw objectives including equality",
        "effectMargins": "Descriptive mechanism study only; no numerical method-qualification/expansion margins, no significance claim or new gate",
        "conflicts": "All raw and paired effects, medians and per-seed directions; no overall winner if metrics disagree, no weighted score or metric vote",
        "time": "Seconds recorded, no TIMEcomparison or speedup claim; engineering logs and science costs kept separate",
        "limits": "Direct effect of latest donor increment conditional on still-shared working model; not all bridge information removed, no proof beyond same-slot continuation/no-role restart/random origin",
        "ordinaryAdaptationOnly": True, "oldStoppedDecisionsReopened": False, "defaultMainlineChanged": False, "goalAchieved": False}


def run_engineering(root, cp, plan, completed):
    results = []
    expected = {r["stem"]: r for r in read(INTERFACE / "analysis.json")["equivalence"]}
    for spec in plan["instances"]:
        stem = spec["stem"]
        initial = None
        for mode in ("LIVE", "REVERT_BRIDGE", "REVERT_COMMON"):
            label = "ENGINEERING-" + mode
            folder = root / stem / label
            reused = stem == "20_8_5_1" and mode == "LIVE"
            if reused:
                out = RECOVERY / stem / label
                receipt, = rows(out / "run-receipt.jsonl")
                independent = read(out / "independent-channel-replay.json")
                assert independent["allPaidGenomesAndAcceptancesReconstructed"] and receipt["failed"] == 0
                assert receipt["successful"] == receipt["attempted"] == 7900
            else:
                out, receipt = run_case(root, cp, stem, "PA_JOINT", label, spec["feLimit"], 13630003,
                    audit=True, source_tsv=SOURCE / stem / "11730007/sources.tsv", vm_settings={PROPERTY: mode,
                        "research.pa.traceIdentity": "true", "research.pa.donorAuditPath": str(folder / "channel-events.jsonl")})
                independent = audit(out, ENGINE / stem / "main/audit/catalog.jsonl", mode)
            completed.append((out, receipt))
            key = initial_key(out)
            if initial is None: initial = key
            else: assert initial == key
            if mode == "LIVE":
                assert receipt["paidSHA256"] == expected[stem]["paidSHA256"]
                assert independent["channelCounts"].get("channel.reverted.BRIDGE", 0) == independent["channelCounts"].get("channel.reverted.COMMON", 0) == 0
            else:
                category = mode.removeprefix("REVERT_")
                assert independent["channelCounts"]["channel.reverted." + category] > 0
            assert receipt["search"]["completeGenerations"] == 2
            results.append({"stem": stem, "mode": mode, "run": str(out), "reused": reused, **independent})
    old_prefix = read(ENGINE / "20_8_5_1/main/audit/independent-replay.json")["prefixPaidSHA256"]
    for limit in (1, 2, 101, 139):
        label = "CUTOFF-" + str(limit)
        folder = root / "20_8_5_1" / label
        out, receipt = run_case(root, cp, "20_8_5_1", "PA_JOINT", label, limit, 13630003, audit=True,
            source_tsv=SOURCE / "20_8_5_1/11730007/sources.tsv", vm_settings={PROPERTY: "LIVE",
                "research.pa.traceIdentity": "true", "research.pa.donorAuditPath": str(folder / "channel-events.jsonl")})
        completed.append((out, receipt))
        result = audit(out, ENGINE / "20_8_5_1/main/audit/catalog.jsonl", "LIVE")
        assert receipt["paidSHA256"] == old_prefix[str(limit)]
        results.append({"stem": "20_8_5_1", "cutoff": limit, **result})
    write_once(root / "engineering.json", {"passed": True, "runs": results})


def run_science(root, cp, plan, completed):
    for i, spec in enumerate(plan["instances"]):
        for j, seed in enumerate(plan["seeds"]):
            labels = list(METHODS); shift = (i + j) % len(labels)
            expected = None
            for label in labels[shift:] + labels[:shift]:
                arm, mode = METHODS[label]
                out, receipt = run_case(root, cp, spec["stem"], arm, f"{seed}/{label}", spec["feLimit"], seed,
                    vm_settings={PROPERTY: mode})
                completed.append((out, receipt))
                key = initial_key(out)
                if expected is None: expected = key
                else: assert key == expected
                assert receipt["decoder"]["dynamic.evaluations"] == spec["feLimit"]
                if arm.startswith("PA_"):
                    assert receipt["search"]["completeGenerations"] == 2
                    assert receipt["search"]["channel.mode"] == mode


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        root = ROOT / "runs" / datetime.now().strftime("pa-donor-channel-probe-%Y%m%d-%H%M%S-%f")
        root.mkdir(); plan = protocol(); write_once(root / "protocol.json", plan)
        print("PA_DONOR_CHANNEL_ROOT", root, flush=True); completed = []
        try:
            for spec in plan["instances"]:
                shutil.copytree(SOURCE / spec["stem"] / "inputs", root / spec["stem"] / "inputs")
            cp = build(root)
            assert read(root / "class-hashes.json") == read(RECOVERY / "class-hashes.json")
            for name in ("run_pa_donor_channel_probe.py", "pa_donor_channel_build.py", "pa_donor_channel_replay.py",
                         "pa_capability_support.py", "pa_specialist_bridge_analysis.py", "pa_population_state_checks.py", "pa_role_policy_audit.py"):
                shutil.copy2(Path(__file__).with_name(name), root / "source" / name)
            write_once(root / "controller-identities.json", {p.name: digest(p) for p in (root / "source").glob("*.py")})
            run_engineering(root, cp, plan, completed)
            print("PA_DONOR_CHANNEL_ENGINEERING_PASSED", flush=True)
            run_science(root, cp, plan, completed)
            result = analyze(root, plan)
            result["scope"] = "Two-generation direct latest-donor increment contrast; original working acceptance unchanged, indirect shared model remains"
            for instance in result["instances"]:
                for row in instance["observations"]:
                    folder = root / instance["stem"] / str(row["seed"]) / row["method"]
                    receipt, = rows(folder / "run-receipt.jsonl")
                    row["channel"] = {k: v for k, v in receipt["search"].items() if k.startswith("channel.")}
            result.update(fees(completed))
            result["reusedEngineeringFE"] = plan["reusedEngineeringFE"]
            result["newSearchFE"] = result["successfulFE"] - plan["reusedEngineeringFE"]
            assert result["successfulFE"] == result["attemptedFE"] == plan["totalPaidEvidenceFE"] and result["failedAttempts"] == 0
            assert result["newSearchFE"] == plan["maximumNewSearchFE"]
            write_once(root / "analysis.json", result)
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error), "runs": len(completed), **fees(completed)})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", "runs": len(completed), **fees(completed),
            "reusedEngineeringFE": plan["reusedEngineeringFE"], "newSearchFE": plan["maximumNewSearchFE"], "goalAchieved": False})
        print("PA_DONOR_CHANNEL_COMPLETE", fees(completed), flush=True)


if __name__ == "__main__":
    main()
