"""Prerecorded small closed-loop ablation of specialist-only intermediate acceptance."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, write_once, controller_lock
from pa_capability_support import SOURCE, run_case, initial_key, fees
from pa_specialist_bridge_build import build, engineering, PROPERTY
from pa_specialist_bridge_analysis import analyze
from research.semantic_repair.evidence import digest

METHODS = {"JOINT_FREE": ("PA_JOINT", False), "JOINT_BLOCKED": ("PA_JOINT", True),
    "RELABEL_FREE": ("PA_RELABEL", False), "RELABEL_BLOCKED": ("PA_RELABEL", True),
    "NSGA2_DEEP": ("NSGA2_DEEP", False), "FULL_SHARED_DEEP": ("FULL_SHARED_DEEP", False),
    "LI_RECON_DEEP": ("LI_RECON_DEEP", False)}


def protocol():
    old = read(ROOT / "runs/pa-base-qualification-20261105-180835-751659/protocol.json")
    comparisons = [("JOINT_FREE", "JOINT_BLOCKED"), ("RELABEL_FREE", "RELABEL_BLOCKED")]
    comparisons += [(a, b) for a in ("JOINT_FREE", "JOINT_BLOCKED", "RELABEL_FREE", "RELABEL_BLOCKED")
                    for b in ("NSGA2_DEEP", "FULL_SHARED_DEEP", "LI_RECON_DEEP")]
    instances = [{"stem": s["stem"], "normalization": s["normalization"],
                  "feLimit": 100 + 200 * (2 * int(s["stem"].split("_")[0]) - 1)} for s in old["instances"]]
    return {"version": "SPECIALIST_INTERMEDIATE_ACCEPTANCE_CAUSAL-v1", "instances": instances,
        "seeds": [14030003, 14030037], "methods": METHODS, "comparisons": comparisons,
        "question": "Does allowing objective-specific improvement through globally dominated intermediates help the full mixed-population search?",
        "onlyIntervention": "BLOCKED requires specialist own strict improvement AND the originalCENTERacceptance; FREE is unchanged. CENTER, all four role labels, model, donors, generation, initializer and budget unchanged",
        "reasonTwoGenerations": "Minimum full update cycle in which late ENERGY/WORKER_COST states can feed next-generation CENTER; same actual FE for all compared methods within instance",
        "modelControl": "Run both pre-existingJOINT andRELABEL, no posthoc model selection and no claim of renewed learned-tree benefit",
        "engineeringFE": 95600, "scientificFE": 669200, "maximumNewSearchFE": 764800,
        "sampling": "All28scientific trajectories finish, no seed substitution or intermediate-win stopping",
        "metrics": "HVmain1.5,sensitivity1.25/2;IGD+empiricalNDunion of all7methods x2seeds perinstance;raw-objective weak bidirectionalC including equality",
        "effectMargins": "Descriptive one-shot mechanism diagnosis only: no practical/significance/pass thresholds and no algorithm qualification or expansion decision from this short horizon",
        "conflicts": "Report all three directions and per-seed conflicts, no vote/weighted score; any evidence limited to this ablation and horizon",
        "noTimeStage": "True search seconds recorded, but observation/audit strata not a matched TIME experiment",
        "stoppedVersionsRemainStopped": True, "newSelectorOrOperator": False, "defaultMainlineChanged": False,
        "scope": "Ordinary PA adaptation without originalQGS/sharing; shared/Li/classic arms retained as context, not final innovation performance",
        "goalAchieved": False}


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        root = ROOT / "runs" / datetime.now().strftime("pa-specialist-bridge-probe-%Y%m%d-%H%M%S-%f")
        root.mkdir()
        plan = protocol()
        write_once(root / "protocol.json", plan)
        print("PA_SPECIALIST_BRIDGE_ROOT", root, flush=True)
        completed = []
        try:
            for spec in plan["instances"]:
                shutil.copytree(SOURCE / spec["stem"] / "inputs", root / spec["stem"] / "inputs")
            cp = build(root)
            for name in ("run_pa_specialist_bridge_probe.py", "pa_specialist_bridge_build.py", "pa_specialist_bridge_analysis.py", "pa_capability_support.py"):
                shutil.copy2(Path(__file__).with_name(name), root / "source" / name)
            write_once(root / "controller-identities.json", {p.name: digest(p) for p in (root / "source").glob("*.py")})
            engineering(root, cp, plan, completed)
            print("PA_BRIDGE_ENGINEERING_PASSED", flush=True)
            for i, spec in enumerate(plan["instances"]):
                stem = spec["stem"]
                for j, seed in enumerate(plan["seeds"]):
                    labels = list(METHODS); shift = (i + j) % len(labels)
                    labels = labels[shift:] + labels[:shift]
                    expected = None
                    for label in labels:
                        arm, blocked = METHODS[label]
                        out, receipt = run_case(root, cp, stem, arm, f"{seed}/{label}", spec["feLimit"], seed,
                            vm_settings={PROPERTY: str(blocked).lower()})
                        completed.append((out, receipt))
                        key = initial_key(out)
                        if expected is None: expected = key
                        else: assert key == expected
                        if arm.startswith("PA_"):
                            assert receipt["search"]["completeGenerations"] == 2
                            blocks = receipt["search"]["blockedSpecialistOnly"]
                            if blocked: assert blocks > 0
                            else: assert blocks == 0
            result = analyze(root, plan)
            result.update(fees(completed))
            assert result["successfulFE"] == result["attemptedFE"] == plan["maximumNewSearchFE"]
            assert result["failedAttempts"] == 0
            write_once(root / "analysis.json", result)
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error), "runs": len(completed), **fees(completed)})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", "runs": len(completed), **fees(completed), "goalAchieved": False})
        print("PA_SPECIALIST_BRIDGE_COMPLETE", fees(completed), flush=True)


if __name__ == "__main__":
    main()
