"""Prospective gate: finite-pool-based context release versus retaining/all/random release."""
from datetime import datetime
from pathlib import Path
import shutil
import time

import numpy as np

from paired_survival_bench import prepare, run_cell, ANCHOR
from context_release_build import BASIS, build
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, hypervolume, igd_plus, nondominated, controller_lock

STEMS = ("20_8_5_1", "100_2_3_1")
SEED = 9670003
METHODS = {"BOUND": ("BOUND", True), "KEEP": ("KEEP", True), "ALL": ("ALL", True),
           "RANDOM_MATCHED": ("RANDOM_MATCHED", True), "BOUND_NOCOMPOSE": ("BOUND", False),
           "FORCE": ("KEEP", True), "NSGA": ("KEEP", True), "LI_MATCHED_DEEP": ("KEEP", True)}


def run(root, cp, spec):
    arm = spec["arm"]; release, compose = METHODS[arm]
    flags = {"research.release.mode": release, "research.release.compose": str(compose).lower(),
             "research.batch.mode": "FORCE" if arm in ("FORCE", "NSGA", "LI_MATCHED_DEEP") else "ROLE_CROWD"}
    if arm == "RANDOM_MATCHED":
        flags["research.release.plan"] = str(root / spec["stem"] / str(spec["seed"]) / "release-plan.csv")
    out = run_cell(root, cp, spec, flags)
    release_log, = rows(out / "release.jsonl")
    if arm == "BOUND":
        plan = ["generation,count"] + [f'{e["generation"]},{len(e["releasedNow"])}' for e in release_log["events"]]
        (out.parent / "release-plan.csv").write_text("\n".join(plan) + "\n", encoding="utf-8")
    if arm == "RANDOM_MATCHED":
        expected, = rows(out.parent / "BOUND/release.jsonl")
        assert [(e["generation"],e["paidFE"],len(e["releasedNow"])) for e in release_log["events"]] == [
            (e["generation"],e["paidFE"],len(e["releasedNow"])) for e in expected["events"]]
    return out


def engineering(root, cp):
    from run_dynamic_deep_roles import BRIDGE
    execute(["java", "-cp", cp, "org.uma.jmetal.util.research.cooperation.ContextReleaseChecks",
             str(BRIDGE / "inputs"), str(BRIDGE / "inputs/RECONSTRUCTED-setup.txt")], root / "checks.log")
    work = root / "engineering"; work.mkdir()
    controls = [("20_2_3_1",8111009,"FORCE",ANCHOR/"SPECIAL-LINEAR",BRIDGE/"inputs"),
                ("20_8_5_1",9280009,"KEEP",BASIS/"20_8_5_1/9280009/ROLE_CROWD",BASIS/"20_8_5_1/inputs")]
    for stem, seed, arm, prior, inp in controls:
        shutil.copytree(inp, work/stem/"inputs"); folder = work/stem/str(seed); folder.mkdir()
        shutil.copy2(ANCHOR/"ledger.csv" if seed==8111009 else prior.parent/"ledger.csv",folder/"ledger.csv")
        out = run(work, cp, {"stem":stem,"seed":seed,"arm":arm})
        assert (out/"solutions.jsonl").read_bytes() == (prior/"solutions.jsonl").read_bytes()
        assert [x["front"] for x in rows(out/"anytime.jsonl")] == [x["front"] for x in rows(prior/"anytime.jsonl")]
    write_once(root/"engineering-gate.json", {"status":"PASS","successfulFE":1000000,"unchangedKeepAndForce":True})


def analyze(root):
    results = []
    for spec in read(root/"protocol.json")["instances"]:
        stem, norm = spec["stem"], spec["normalization"]
        normed = lambda x:(np.asarray(x)-norm["lower"])/norm["scale"]
        paths = {a:root/stem/str(SEED)/a for a in METHODS}
        fronts = {a:rows(p/"anytime.jsonl")[-1]["front"] for a,p in paths.items()}
        reference = nondominated(np.vstack([normed(f) for f in fronts.values()])); metrics = {}
        for arm,path in paths.items():
            timer = next(x for x in rows(path/"time.jsonl") if abs(x["checkpoint"]-spec["time_seconds"])<1e-9)
            metrics[arm] = {"HV":{str(r):float(hypervolume(normed(fronts[arm]),(r,)*3)) for r in (1.25,1.5,2)},
                            "timeHV":float(hypervolume(normed(timer["front"]),(1.5,)*3)),
                            "IGDplus":float(igd_plus(normed(fronts[arm]),reference)),"release":rows(path/"release.jsonl")[0]}
        effects = {a:100*(metrics["BOUND"]["HV"]["1.5"]/m["HV"]["1.5"]-1) for a,m in metrics.items() if a!="BOUND"}
        passed = effects["KEEP"]>=1 and effects["NSGA"]>=-1 and all(effects[a]>0 for a in ("ALL","RANDOM_MATCHED","BOUND_NOCOMPOSE"))
        results.append({"stem":stem,"metrics":metrics,"boundEffectsPct":effects,"eligible":passed})
    write_once(root/"comparison.json",results); return results


def main():
    root = ROOT/"runs"/datetime.now().strftime("context-release-gate-%Y%m%d-%H%M%S-%f")
    root.mkdir(); print("RELEASE_ROOT",root,flush=True); start=time.monotonic(); done=[]
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs,_ = prepare(root, STEMS, (SEED,), tuple(METHODS))
            order = [{"stem":s,"seed":SEED,"arm":a} for s in STEMS for a in METHODS]
            write_once(root/"protocol.json", {"candidate":"BOUND","instances":specs,"seed":SEED,"methods":METHODS,"order":order,
                "decision":"Only after each complete global phase. Release every still-protected family whose current retained-pool "
                           "component-minimum optimistic bound is weakly dominated by a previously paid external archive point. "
                           "Conservative 32-ULP downward slack. Irreversible, no threshold/timing tuning. No future-search bound claimed.",
                "preserved":"Four objectives/duties, original QGS/JOΒ_ALIGNED, original local ledger, pool choose/cap/eta. "
                            "Released particles become free; still-protected categories retain five slots and 1/2/1/1 role slots. "
                            "Exact-FA-compatible free particles may still supply/request the old pool; no incompatible joins.",
                "randomControl":"BOUND runs first; its per-generation release counts alone specify RANDOM_MATCHED. A separate seeded "
                                "RNG randomizes family identities without advancing search RNG. Control uses no candidate HV or final result.",
                "controls":"ALL releases all after first global; KEEP retains old architecture; BOUND_NOCOMPOSE updates the same pools "
                           "but never composes, isolating contribution of actual sharing. FORCE old shared, NSGA and Li matched-depth retained.",
                "gate":"Both instances: >=1% vs KEEP, >0 vs ALL/RANDOM_MATCHED/BOUND_NOCOMPOSE, >=-1% vs NSGA. If no selective release "
                       "or no independent sharing gain, no special cooperative claim. Failure stops this rule, without threshold scans.",
                "searchFE":8000000,"engineeringFE":1000000,"sameFEPerCell":500000,
                "timeScope":"Common-time checkpoints diagnostic; fresh genuine TIME_LIMIT confirmation required before a time advantage claim.",
                "scope":"Prospective development gate, not independent confirmation or novelty proof."})
            cp=build(root);engineering(root,cp)
            for spec in order:run(root,cp,spec);done.append(spec)
            results=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulFE":len(done)*500000,"engineeringFE":1000000,
                                   "worthFreshScreen":all(x["eligible"] for x in results),"wallSeconds":time.monotonic()-start})
    print("RELEASE_COMPLETE",[{"stem":x["stem"],"effects":x["boundEffectsPct"],"eligible":x["eligible"]} for x in results],flush=True)


if __name__=="__main__":main()
