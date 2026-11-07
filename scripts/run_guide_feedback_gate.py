"""Fresh-seed full-budget continuation of the pre-qualified accepted-guide timing probe."""
from datetime import datetime
from pathlib import Path
import shutil
import time

import numpy as np

from paired_survival_bench import prepare, run_cell
from context_release_build import BASIS
from run_guide_feedback_probe import build
from run_long_budget_bridge import ROOT, read, rows, write_once, hypervolume, igd_plus, nondominated, controller_lock

STEMS=("20_8_5_1","100_2_3_1")
SEED=9850003
METHODS={"GEN":("GEN","SHARE_JOB_ALIGNED"),"BATCH":("BATCH","SHARE_JOB_ALIGNED"),
         "ROLE_END":("ROLE_END","SHARE_JOB_ALIGNED"),"BATCH_SYNC":("BATCH","SYNC_JOB_ALIGNED"),
         "BATCH_UNIFORM":("BATCH","SHARE_JOB_ALIGNED_UNIFORM"),"FORCE":("GEN","SHARE_JOB_ALIGNED"),
         "NSGA":("GEN","NSGA2_4V"),"LI_MATCHED_DEEP":("GEN","BASELINE")}


def run(root,cp,spec):
    spec=dict(spec);arm=spec["arm"];timing,mode=METHODS[arm];spec["mode"]=mode
    flags={"research.guide.mode":timing,"research.guide.trace":"false",
           "research.batch.mode":"FORCE" if arm in ("FORCE","NSGA","LI_MATCHED_DEEP") else "ROLE_CROWD"}
    return run_cell(root,cp,spec,flags)


def engineering(root,cp):
    work=root/"engineering";work.mkdir();stem="20_8_5_1";seed=9280009
    prior=BASIS/stem/str(seed)/"ROLE_CROWD"
    shutil.copytree(BASIS/stem/"inputs",work/stem/"inputs");folder=work/stem/str(seed);folder.mkdir()
    shutil.copy2(prior.parent/"ledger.csv",folder/"ledger.csv")
    out=run(work,cp,{"stem":stem,"seed":seed,"arm":"GEN"})
    assert (out/"solutions.jsonl").read_bytes()==(prior/"solutions.jsonl").read_bytes()
    assert [x["front"] for x in rows(out/"anytime.jsonl")] == [x["front"] for x in rows(prior/"anytime.jsonl")]
    write_once(root/"engineering-gate.json",{"status":"PASS","successfulFE":500000,"unchangedGEN":True})


def analyze(root):
    results=[]
    for spec in read(root/"protocol.json")["instances"]:
        stem,norm=spec["stem"],spec["normalization"];normed=lambda x:(np.asarray(x)-norm["lower"])/norm["scale"]
        paths={a:root/stem/str(SEED)/a for a in METHODS}
        fronts={a:rows(p/"anytime.jsonl")[-1]["front"] for a,p in paths.items()}
        reference=nondominated(np.vstack([normed(x) for x in fronts.values()]));metrics={}
        for a,p in paths.items():
            timer=next(x for x in rows(p/"time.jsonl") if abs(x["checkpoint"]-spec["time_seconds"])<1e-9)
            metrics[a]={"HV":{str(r):float(hypervolume(normed(fronts[a]),(r,)*3)) for r in (1.25,1.5,2)},
                        "IGDplus":float(igd_plus(normed(fronts[a]),reference)),"timeHV":float(hypervolume(normed(timer["front"]),(1.5,)*3)),
                        "guide":rows(p/"guides.jsonl")[0]}
        effects={a:100*(metrics["BATCH"]["HV"]["1.5"]/m["HV"]["1.5"]-1) for a,m in metrics.items() if a!="BATCH"}
        passed=effects["GEN"]>=1 and effects["NSGA"]>=-1 and all(effects[a]>0 for a in ("ROLE_END","BATCH_SYNC","BATCH_UNIFORM","FORCE","LI_MATCHED_DEEP"))
        robust=all(metrics["BATCH"]["HV"][str(r)]>metrics["GEN"]["HV"][str(r)] for r in (1.25,2))
        results.append({"stem":stem,"metrics":metrics,"batchEffectsPct":effects,"referenceDirectionStable":robust,
                        "eligible":passed and robust})
    write_once(root/"comparison.json",results);return results


def main():
    root=ROOT/"runs"/datetime.now().strftime("guide-feedback-gate-%Y%m%d-%H%M%S-%f")
    root.mkdir();print("GUIDE_GATE_ROOT",root,flush=True);done=[];start=time.monotonic()
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs,order=prepare(root,STEMS,(SEED,),tuple(METHODS))
            write_once(root/"protocol.json",{"instances":specs,"seed":SEED,"methods":METHODS,"order":order,"candidate":"BATCH",
                "basis":"guide-feedback-probe-20261105-001115-004809 passed pre-fixed global-stage gate, four paired HV wins; new seed here.",
                "changed":"Only earlier internal Pareto offers of accepted current states after each QGS batch. Original generation-end history offers remain. "
                          "No rejected child is promoted by the new rule. Original Q actions/feedback, proposals, fixed families, cap/eta, shared pool and local ledger unchanged.",
                "controls":"GEN original timing with ROLE_CROWD; ROLE_END refresh at each role end; BATCH_SYNC no composition; BATCH_UNIFORM all four preferences CENTER "
                           "but Q table retained; FORCE original global current survival; correct Li v2 and NSGA-II both with matched deep local search.",
                "recording":"Full-genome guide provenance disabled for performance. Trace-disabled observer only tracks current FE; refresh cost remains in search clock.",
                "gate":"Both instances BATCH >=1% vs GEN, >0 vs ROLE_END/SYNC/UNIFORM/FORCE/Li, >=-1% vs matched NSGA-II. "
                       "Direction vs GEN unchanged at references1.25/2. Failure ends this timing variant without scanning intervals or seeds to rescue it.",
                "actualFEPerCell":500000,"searchFE":8000000,"engineeringFE":500000,
                "timeScope":"Shared time cuts exploratory; genuine independent TIME_LIMIT runs still required for a same-time superiority claim.",
                "scope":"Fresh-seed development gate, not independent confirmation, paper originality or original-author score reproduction."})
            cp=build(root);shutil.copy2(Path(__file__),root/"source");engineering(root,cp)
            for spec in order:run(root,cp,spec);done.append(spec)
            result=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulFE":len(done)*500000,"engineeringFE":500000,
                                   "worthFreshScreen":all(x["eligible"] for x in result),"wallSeconds":time.monotonic()-start})
    print("GUIDE_GATE_COMPLETE",[{"stem":x["stem"],"effects":x["batchEffectsPct"],"eligible":x["eligible"]} for x in result],flush=True)


if __name__=="__main__":main()
