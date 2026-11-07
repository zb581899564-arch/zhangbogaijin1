"""Cross two previously isolated architecture factors without changing their frozen implementation."""
from datetime import datetime
from pathlib import Path
import shutil
import time

import numpy as np

from paired_survival_bench import prepare, run_cell, class_hashes
from run_long_budget_bridge import ROOT, read, rows, write_once, hypervolume, igd_plus, nondominated, controller_lock

BASIS=ROOT/"runs/group-survival-gate-20261104-234602-311536"
STEMS=("20_8_5_1","100_2_3_1")
SEED=9940003
METHODS={"SHARE_PAIR":("SHARE_JOB_ALIGNED","PAIR"),"SHARE_FULL":("SHARE_JOB_ALIGNED","FULL_ROLE"),
         "SYNC_PAIR":("SYNC_JOB_ALIGNED","PAIR"),"SYNC_FULL":("SYNC_JOB_ALIGNED","FULL_ROLE"),
         "FREE_PAIR":("BASELINE_JOB_ALIGNED","PAIR"),"FREE_FULL":("BASELINE_JOB_ALIGNED","FULL_ROLE"),
         "NSGA":("NSGA2_4V","PAIR"),"LI_MATCHED_DEEP":("BASELINE","PAIR")}


def run(root,cp,spec):
    spec=dict(spec);arm=spec["arm"];mode,selection=METHODS[arm];spec["mode"]=mode
    if arm.startswith("FREE_"):spec["commonInitials"]=True
    flags={"research.group.mode":selection,"research.reward.mode":"GROUP" if selection=="FULL_ROLE" else "INDIVIDUAL",
           "research.batch.mode":"FORCE" if arm in ("NSGA","LI_MATCHED_DEEP") else "ROLE_CROWD"}
    return run_cell(root,cp,spec,flags)


def analyze(root):
    results=[]
    for spec in read(root/"protocol.json")["instances"]:
        stem,norm=spec["stem"],spec["normalization"];normed=lambda x:(np.asarray(x)-norm["lower"])/norm["scale"]
        paths={a:root/stem/str(SEED)/a for a in METHODS}
        fronts={a:rows(p/"anytime.jsonl")[-1]["front"] for a,p in paths.items()}
        reference=nondominated(np.vstack([normed(f) for f in fronts.values()]));metrics={}
        for arm,p in paths.items():
            timer=next(x for x in rows(p/"time.jsonl") if abs(x["checkpoint"]-spec["time_seconds"])<1e-9)
            metrics[arm]={"HV":{str(r):float(hypervolume(normed(fronts[arm]),(r,)*3)) for r in (1.25,1.5,2)},
                          "IGDplus":float(igd_plus(normed(fronts[arm]),reference)),
                          "timeHV":float(hypervolume(normed(timer["front"]),(1.5,)*3)),"group":rows(p/"group.jsonl")[0]}
        hv=lambda a:metrics[a]["HV"]["1.5"]
        effects={a:100*(hv("FREE_FULL")/hv(a)-1) for a in METHODS if a!="FREE_FULL"}
        within={s:100*(hv(s+"_FULL")/hv(s+"_PAIR")-1) for s in ("SHARE","SYNC","FREE")}
        passed=effects["FREE_PAIR"]>=1 and effects["SHARE_FULL"]>=1 and effects["NSGA"]>=-1 and effects["LI_MATCHED_DEEP"]>0
        robust=all(metrics["FREE_FULL"]["HV"][str(r)]>metrics["FREE_PAIR"]["HV"][str(r)] for r in (1.25,2))
        results.append({"stem":stem,"metrics":metrics,"freeFullEffectsPct":effects,"withinStructureFullVsPairPct":within,
                        "setSelectionInteractionFreeMinusSyncPP":within["FREE"]-within["SYNC"],"eligible":passed and robust})
    write_once(root/"comparison.json",results);return results


def main():
    root=ROOT/"runs"/datetime.now().strftime("survival-context-factorial-%Y%m%d-%H%M%S-%f")
    root.mkdir();print("SURVIVAL_CONTEXT_ROOT",root,flush=True);done=[];start=time.monotonic()
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs,order=prepare(root,STEMS,(SEED,),tuple(METHODS))
            write_once(root/"protocol.json",{"instances":specs,"seed":SEED,"methods":METHODS,"order":order,
                "question":"Is the previous set-survival benefit suppressed by fixed-family scaffolding? One factorial, no weight/threshold/interval scan.",
                "identity":"Direct reuse of frozen group-survival-gate classpath. GEN-end guide timing restored; no context-release or early-guide code used.",
                "factors":"PAIR per-lineage ROLE_CROWD versus FULL_ROLE unrestricted lineage survival plus permutation-invariant group reward. "
                          "SHARE/SYNC preserve20 protected family members and stratified quotas; FREE removes the scaffold but preserves four target duties and JOB_ALIGNED.",
                "limits":"Architecture factor includes hardFA, categories and stratified grouping; not FA locking alone. Full factor includes its required group reward. "
                         "FREE has no composition and cannot be called retained sharing. SHARE minus SYNC separately isolates actual composition within protected architecture. "
                         "A FREE_FULL pass only supports a performance substrate, and does not establish cooperative originality or fully satisfy the research goal.",
                "fairness":"All methods use exactly the same100 four-vector initials and objectives, unchanged50 steps per physical role, "
                           "same500000 successfulFE and original physical local ledger. Search RNG outcomes may differ after initialization.",
                "gate":"On both instances FREE_FULL >=1% vs FREE_PAIR and SHARE_FULL, >=-1% vs matched NSGA-II, >Li matched-depth; "
                       "FREE_FULL/FREE_PAIR direction remains positive at references1.25/2. Failure stops this combination without scanning quotas or seeds.",
                "searchFE":8000000,"newEngineeringFE":0,"priorEngineering":"Frozen paired/full classes have exact old-control replay and quota fixtures; "
                    "this campaign introduces no source edits. All new configurations must still pass full return-genome QA and identical FE/initialization checks.",
                "timeScope":"Exploratory time checkpoints only, no independent same-time superiority claim.",
                "scope":"Prospective interaction diagnostic; no final efficacy, original-author replication or journal qualification claim."})
            expected=read(BASIS/"class-hashes.json");actual=class_hashes(BASIS/"classes");assert actual==expected
            write_once(root/"frozen-class-verification.json",{"status":"PASS","classHashes":actual,"sourceRun":str(BASIS)})
            cp=(BASIS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
            (root/"classpath.txt").write_text(cp,encoding="utf-8");shutil.copy2(Path(__file__),root/"source.py")
            for spec in order:run(root,cp,spec);done.append(spec)
            results=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulFE":len(done)*500000,"newEngineeringFE":0,
                                   "worthIndependentSubstrateScreen":all(x["eligible"] for x in results),"wallSeconds":time.monotonic()-start})
    print("SURVIVAL_CONTEXT_COMPLETE",[{"stem":x["stem"],"effects":x["freeFullEffectsPct"],"eligible":x["eligible"]} for x in results],flush=True)


if __name__=="__main__":main()
