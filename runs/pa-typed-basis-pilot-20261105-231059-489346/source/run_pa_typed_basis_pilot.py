"""Lean parity then fixed100k and conditional true-time tri-indicator pilot; no parameter search."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock
from pa_capability_support import SOURCE, run_case, initial_key, fees
from pa_specialist_bridge_analysis import analyze
from pa_typed_basis_gates import readiness
from research.semantic_repair.evidence import digest
from frozen_classpath_identity import verify_capture

ENGINE = ROOT / "runs/pa-typed-basis-engineering-20261105-223547-202723"
METHODS = {"ATOM": ("PA_JOINT", "ATOM"), "TYPED": ("PA_JOINT", "TYPED"),
    "SHAM_BLOCK": ("PA_JOINT", "SHAM_BLOCK"), "TYPED_RELABEL": ("PA_RELABEL", "TYPED"),
    **{name: (name, "ATOM") for name in ("NSGA2_PLAIN", "NSGA2_DEEP", "FULL_SHARED_DEEP", "LI_RECON_DEEP")}}


def protocol():
    old = read(ROOT / "runs/pa-base-qualification-20261105-180835-751659/protocol.json")
    return {"version": "TYPED_BASIS_PILOT-v1", "registeredAfterEngineeringOnly": True,
        "engineeringEffectiveIdentity": read(ENGINE / "ACCEPTANCE.json"), "seeds": [14230003, 14230037],
        "instances": [{"stem": s["stem"], "normalization": s["normalization"], "feLimit": 100000,
                       "time_seconds": 4 if s["stem"] == "20_8_5_1" else 5} for s in old["instances"]],
        "methods": METHODS, "primary": "TYPED=JOINTmodel, fixed before any fresh performance result; do not selectRELABELorSHAMlater",
        "comparisons": [("TYPED", other) for other in METHODS if other != "TYPED"],
        "phases": ["Six lean-parity runs335400FE", "All32FE100Kruns3200000FE", "All32TIMEruns only if entireFE100Kreadinesspasses"],
        "plannedFEbeforeOptionalTime": 3535400, "timeSafetyFE": 5000000,
        "timeSearchSecondsIfRun": 144, "runOrdering": "OneJVM, cyclic method rotation within each instance/seed block; no partial winner stopping",
        "initialization": "Newseed fresh100solutions, common acrossall8methods; constructors and all search costs insideRunContextclock",
        "metrics": "HV1.5with1.25/2sensitivities;IGD+usesNDunionofall8methods x2seeds perinstance,independentlyperphase; exactweakbidirectionalC, objective-deduplicated, equalityincluded",
        "componentGate": "BOTHinstances vsSHAM:medianHV>=0.5%,medianIGD+worsening<=0,medianC(A,B)-C(B,A)>=0; perseedHV>=-1%,IGD+<=5%,Cdelta>=-0.02; sensitivityHVmedian>=0",
        "preservationGate": "vsATOM:medianHV>=0,IGD+<=5%,Cdelta>=-0.02; perseedHV>=-1%,IGD+<=10%,Cdelta>=-0.05; sensitivityHVmedian>=0",
        "classicGate": "vsEACHplain/deepNSGA:medianHV>=-1%,IGD+<=5%,Cdelta>=-0.02; perseedHV>=-5%,IGD+<=15%,Cdelta>=-0.1; sensitivityHVmedian>=-1%",
        "oldControlGate": "vsEACHoldshared/Lireconstruction:medianHV>=1%,IGD+<=0,Cdelta>=0; perseedHV>=0,IGD+<=10%,Cdelta>=-0.05; sensitivityHVmedian>=0",
        "gateMeaning": "Project resource/benefit margins, not literature constants, statistical significance or contribution review. All3indicators constrain decision; C=0/0 allowed neutral, no weighted score/vote",
        "ifFEfails": "Stop this fixed typed-basis pilot, noTIME, no new seeds/weights/field rates/donor rules orposthocbetter method selection to rescue",
        "ifpasses": "TIMEuses same joint gates; passing only supports ordinary basis for later four-role/QGS/shared work, not final innovative algorithm",
        "learningClaim": "RELABELordinarynull reported; failed old learned-tree claim remains unsupported regardless of this adaptation's quality",
        "scope": "Two reused development instances,2newseeds, ordinary noLS PA variants; originalQGS/shared not integrated, controls retained",
        "defaultMainlineChanged": False, "goalAchieved": False}


def parity(root, cp, completed):
    checked = []
    for stem in ("20_8_5_1", "100_2_3_1"):
        for basis in ("ATOM", "TYPED", "SHAM_BLOCK"):
            old, = rows(ENGINE / stem / basis / "audit/receipt.jsonl")
            out, receipt = run_case(root, cp, stem, "PA_JOINT", "PARITY-" + basis, old["successfulFE"], 13630003,
                audit=True, source_tsv=SOURCE / stem / "11730007/sources.tsv", vm_settings={"research.pa.typedBasis": basis})
            completed.append((out, receipt))
            assert receipt["paidSHA256"] == old["paidSHA256"] and receipt["search"]["completeGenerations"] == 2
            checked.append({"stem": stem, "basis": basis, "successfulFE": receipt["successful"],
                            "paidSHA256": receipt["paidSHA256"], "heavyAndLeanPaidTrajectoryEqual": True})
    write_once(root / "lean-parity.json", checked)


def phase(root, cp, plan, label, completed):
    for i, spec in enumerate(plan["instances"]):
        for j, seed in enumerate(plan["seeds"]):
            labels = list(METHODS); shift = (i + j) % len(labels); expected = None
            for method in labels[shift:] + labels[:shift]:
                arm, basis = METHODS[method]
                limit = plan["timeSafetyFE"] if label == "TIME" else spec["feLimit"]
                seconds = spec["time_seconds"] if label == "TIME" else float("inf")
                out, receipt = run_case(root, cp, spec["stem"], arm, f"{seed}/{label}-{method}", limit, seed, seconds,
                    vm_settings={"research.pa.typedBasis": basis})
                completed.append((out, receipt))
                key = initial_key(out)
                if expected is None: expected = key
                else: assert key == expected
                if label == "TIME": assert key == initial_key(root / spec["stem"] / str(seed) / ("FE100K-" + method))
                assert receipt["decoder"]["dynamic.evaluations"] == receipt["successful"]
                loaded, = rows(out / "loaded-identity.jsonl"); verify_capture(loaded, cp)
    result = analyze(root, plan, phase=label, kind="TIME" if label == "TIME" else "FE")
    result["scope"] = "Fixed ordinary typed-variable basis,2developmentinstances and2freshseeds; no novelty/oldgate revival"
    gate = readiness(result)
    write_once(root / (label.lower() + "-analysis.json"), result)
    write_once(root / (label.lower() + "-readiness.json"), gate)
    print("PA_TYPED_PILOT_PHASE", label, gate["pass"], flush=True)
    return result, gate


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        assert read(ENGINE / "ACCEPTANCE.json")["engineeringPass"]
        root = ROOT / "runs" / datetime.now().strftime("pa-typed-basis-pilot-%Y%m%d-%H%M%S-%f")
        root.mkdir(); plan = protocol(); write_once(root / "protocol.json", plan)
        print("PA_TYPED_BASIS_PILOT_ROOT", root, flush=True); completed = []
        try:
            cp = (ENGINE / "classpath.txt").read_text("utf-8-sig").strip()
            (root / "classpath.txt").write_text(cp, encoding="utf-8")
            source = root / "source"; source.mkdir()
            for name in ("run_pa_typed_basis_pilot.py", "pa_typed_basis_gates.py", "pa_specialist_bridge_analysis.py", "pa_capability_support.py", "frozen_classpath_identity.py"):
                shutil.copy2(Path(__file__).with_name(name), source / name)
            write_once(root / "controller-hashes.json", {p.name: digest(p) for p in source.iterdir()})
            for spec in plan["instances"]: shutil.copytree(SOURCE / spec["stem"] / "inputs", root / spec["stem"] / "inputs")
            parity(root, cp, completed)
            fe, fe_gate = phase(root, cp, plan, "FE100K", completed); phases = [fe]; gates = [fe_gate]
            if fe_gate["pass"]:
                timed, time_gate = phase(root, cp, plan, "TIME", completed); phases.append(timed); gates.append(time_gate)
            decision = "ORDINARY_TYPED_BASIS_PROMISING_ONLY" if len(gates) == 2 and all(g["pass"] for g in gates) else "STOP_FIXED_TYPED_BASIS_PILOT"
            write_once(root / "analysis.json", {"phases": phases, "readiness": gates, "decision": decision, **fees(completed),
                "defaultMainlineChanged": False, "finalResearchAlgorithmProved": False, "goalAchieved": False})
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error), "completedRuns": len(completed), **fees(completed)})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", "decision": decision, **fees(completed), "goalAchieved": False})
        print("PA_TYPED_BASIS_PILOT_COMPLETE", decision, fees(completed), flush=True)


if __name__ == "__main__":
    main()
