"""Separate family scaffolding, sharing, and proposal semantics before designing a softer context architecture."""
from datetime import datetime
from pathlib import Path
import shutil
import time

import numpy as np

from paired_survival_bench import prepare,run_cell
from run_long_budget_bridge import ROOT,read,rows,write_once,hypervolume,igd_plus,nondominated,controller_lock

BASIS=ROOT/"runs/batch-survival-study-20261104-222516-378030"
STEMS=("20_8_5_1","100_2_3_1")
SEEDS=(9490009,)
METHODS={
    "FIXED_FORCE":dict(mode="SHARE_JOB_ALIGNED",policy="FORCE"),
    "FIXED_SHARE":dict(mode="SHARE_JOB_ALIGNED",policy="ROLE_CROWD"),
    "FIXED_SYNC":dict(mode="SYNC_JOB_ALIGNED",policy="ROLE_CROWD"),
    "FREE_JOB":dict(mode="BASELINE_JOB_ALIGNED",policy="ROLE_CROWD",commonInitials=True),
    "FREE_PAPER_SO":dict(mode="BASELINE",policy="ROLE_CROWD",commonInitials=True),
    "FREE_PAPER_V2":dict(mode="BASELINE",policy="ROLE_CROWD",commonInitials=True,liLegacy=True),
    "LI_MATCHED_DEEP":dict(mode="BASELINE",policy="FORCE",commonInitials=True,liLegacy=True),
    "NSGA":dict(mode="NSGA2_4V",policy="FORCE"),
}


def analyze(root):
    result=[]
    for spec in read(root/"protocol.json")["instances"]:
        stem,norm=spec["stem"],spec["normalization"];normal=lambda x:(np.asarray(x)-norm["lower"])/norm["scale"]
        fs={a:rows(root/stem/str(SEEDS[0])/a/"anytime.jsonl")[-1]["front"] for a in METHODS}
        ref=nondominated(np.vstack([normal(x) for x in fs.values()]));metrics={}
        for a,front in fs.items():
            path=root/stem/str(SEEDS[0])/a
            t=next(x for x in rows(path/"time.jsonl") if abs(x["checkpoint"]-spec["time_seconds"])<1e-9)
            metrics[a]={"HV":float(hypervolume(normal(front),(1.5,)*3)),"IGDplus":float(igd_plus(normal(front),ref)),
                        "timeHV":float(hypervolume(normal(t["front"]),(1.5,)*3)),
                        "config":rows(path/"run-receipt.jsonl")[0]["configuration"]}
        pairs={"familyScaffoldingNet":("FIXED_SYNC","FREE_JOB"),"sharingUnderFixedScaffolding":("FIXED_SHARE","FIXED_SYNC"),
               "fixedSharingNetVsFree":("FIXED_SHARE","FREE_JOB"),"alignedVsPaperSO":("FREE_JOB","FREE_PAPER_SO"),
               "paperSOvsV2":("FREE_PAPER_SO","FREE_PAPER_V2"),"V2SelectionImprovement":("FREE_PAPER_V2","LI_MATCHED_DEEP")}
        effects={name:100*(metrics[a]["HV"]/metrics[b]["HV"]-1) for name,(a,b) in pairs.items()}
        result.append({"stem":stem,"metrics":metrics,"diagnosticEffectsPct":effects,
                       "vsNSGApct":{a:100*(m["HV"]/metrics["NSGA"]["HV"]-1) for a,m in metrics.items()}})
    write_once(root/"comparison.json",result);return result


def main():
    root=ROOT/"runs"/datetime.now().strftime("context-tax-audit-%Y%m%d-%H%M%S-%f")
    root.mkdir();print("CONTEXT_TAX_ROOT",root,flush=True);start=time.monotonic();done=[]
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs,order=prepare(root,STEMS,SEEDS,tuple(METHODS))
            write_once(root/"protocol.json",{"instances":specs,"seeds":SEEDS,"methods":METHODS,"order":order,
                "evidence":"Paid M proposal competitions did not improve the many-stage gap. An accidentally crowd-enhanced "
                           "unprotected Li control suggested that protected FA contexts or reconstruction semantics may impose a tax.",
                "question":"Separate original fixed-context sharing gains from family constraints+quota+stratification cost; "
                           "separate that architecture effect from JOB_ALIGNED vs paper-SO and legacy-v2 proposal/survival differences.",
                "invariants":"Same paid initial vectors, physical LS ledger, original four objective roles, common linear PDDR "
                             "and dynamic decoder. FREE variants are explicitly ablations with no protected contexts, not claims "
                             "to retain the old sharing effect. No candidate is chosen as a winner before this diagnostic.",
                "identity":"LI_MATCHED_DEEP is reconstructed-v2 plus matched deep LS; FREE_PAPER_V2 adds only the new global "
                           "batch selection to that enhanced control. SO vs v2 changes two disclosed semantics, not a pure kernel factor.",
                "actualFEPerCell":500000,"totalSearchFE":8000000,"scope":"One-seed architecture attribution, not final efficacy or journal novelty."})
            shutil.copy2(Path(__file__),root)
            cp=(BASIS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
            (root/"classpath.txt").write_text(cp,encoding="utf-8")
            for cell in order:
                design=METHODS[cell["arm"]];job={**cell,**{k:v for k,v in design.items() if k!="policy"}}
                run_cell(root,cp,job,{"research.batch.mode":design["policy"]});done.append(cell)
            result=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulFE":8000000,"completed":len(done),"wallSeconds":time.monotonic()-start})
    print("CONTEXT_TAX_COMPLETE",[{"stem":x["stem"],"effects":x["diagnosticEffectsPct"],"vsNSGA":x["vsNSGApct"]} for x in result],flush=True)


if __name__=="__main__":main()
