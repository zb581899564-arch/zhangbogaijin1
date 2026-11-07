"""Fresh full-budget screen of the ordinary cost-neutral control, with matched generic enhancements."""
from datetime import datetime
from pathlib import Path
import shutil
import time

import numpy as np

from paired_survival_bench import prepare,run_cell
from run_makespan_continuation_probe import build
from run_personal_memory_screen import engineering
from run_long_budget_bridge import ROOT,read,rows,write_once,hypervolume,igd_plus,nondominated,controller_lock

STEMS=("20_8_5_1","100_2_3_1")
SEEDS=(10950003,10950033,10950063)
METHODS={"STRICT_FULL":("STRICT","SHARE_JOB_ALIGNED","FULL_ROLE",False),
         "COST_FULL":("COST_LEX","SHARE_JOB_ALIGNED","FULL_ROLE",False),
         "PARETO_FULL":("PARETO_SAFE","SHARE_JOB_ALIGNED","FULL_ROLE",False),
         "COST_SYNC":("COST_LEX","SYNC_JOB_ALIGNED","FULL_ROLE",False),
         "COST_UNIFORM":("COST_LEX","SHARE_JOB_ALIGNED_UNIFORM","FULL_ROLE",False),
         "LI_STRICT":("STRICT","BASELINE","PAIR",True),
         "LI_COST":("COST_LEX","BASELINE","PAIR",True),
         "NSGA_STRICT":("STRICT","NSGA2_4V","PAIR",False),
         "NSGA_COST":("COST_LEX","NSGA2_4V","PAIR",False),
         "FORCE_STRICT":("STRICT","SHARE_JOB_ALIGNED","PAIR",False)}


def run(root,cp,spec):
    spec=dict(spec);arm=spec["arm"];tie,mode,group,li=METHODS[arm]
    spec.update(mode=mode,liLegacy=li,commonInitials=li)
    out=run_cell(root,cp,spec,{"research.makespan.tie":tie,"research.personal.mode":"OLDEST",
        "research.group.mode":group,"research.reward.mode":"GROUP" if group=="FULL_ROLE" else "INDIVIDUAL",
        "research.batch.mode":"ROLE_CROWD" if group=="FULL_ROLE" else "FORCE","research.memory.audit":"false"})
    assert rows(out/"makespan-tie.jsonl")[0]["mode"]==tie


def analyze(root):
    results=[];cells=[]
    for spec in read(root/"protocol.json")["instances"]:
        stem=spec["stem"];norm=spec["normalization"];normalize=lambda x:(np.asarray(x)-norm["lower"])/norm["scale"]
        paths={(s,a):root/stem/str(s)/a for s in SEEDS for a in METHODS}
        fronts={k:rows(p/"anytime.jsonl")[-1]["front"] for k,p in paths.items()}
        empirical=nondominated(np.vstack([normalize(f) for f in fronts.values()]));metrics={}
        for (seed,arm),path in paths.items():
            timer=next(x for x in rows(path/"time.jsonl") if abs(x["checkpoint"]-spec["time_seconds"])<1e-9)
            value={"HV":{str(r):float(hypervolume(normalize(fronts[(seed,arm)]),(r,)*3)) for r in (1.25,1.5,2)},
                "IGDplus":float(igd_plus(normalize(fronts[(seed,arm)]),empirical)),
                "timeHV":float(hypervolume(normalize(timer["front"]),(1.5,)*3)),
                "tiePolicy":rows(path/"makespan-tie.jsonl")[0]}
            metrics[(seed,arm)]=value;cells.append({"stem":stem,"seed":seed,"arm":arm,**value})
        effects={a:[100*(metrics[(s,"COST_FULL")]["HV"]["1.5"]/metrics[(s,a)]["HV"]["1.5"]-1) for s in SEEDS] for a in METHODS if a!="COST_FULL"}
        medians={a:float(np.median(v)) for a,v in effects.items()}
        gate=medians["STRICT_FULL"]>=1 and sum(x>0 for x in effects["STRICT_FULL"])>=2 and medians["NSGA_COST"]>=-1 \
            and medians["PARETO_FULL"]>=0 and all(medians[a]>0 for a in ("LI_COST","LI_STRICT","FORCE_STRICT"))
        robust=all(np.median([metrics[(s,"COST_FULL")]["HV"][str(r)]-metrics[(s,"STRICT_FULL")]["HV"][str(r)] for s in SEEDS])>0 for r in (1.25,2))
        results.append({"stem":stem,"effectsPct":effects,"medianEffectsPct":medians,"efficacyPrimaryPass":bool(gate and robust),
                        "fourDutyMedianBenefit":medians["COST_UNIFORM"],"sharingMedianBenefit":medians["COST_SYNC"]})
    cooperation=all(r["fourDutyMedianBenefit"]>=1 for r in results) and max(r["sharingMedianBenefit"] for r in results)>=.2 \
        and min(r["sharingMedianBenefit"] for r in results)>=-.5
    result={"instances":results,"cells":cells,"efficacyPrimaryPass":all(r["efficacyPrimaryPass"] for r in results),
            "cooperationScreenPass":bool(cooperation),"decision":"REVIEW_AUXILIARIES_BEFORE_CONFIRMATION" if all(r["efficacyPrimaryPass"] for r in results) else "STOP_MAKESPAN_COST_TIE_SCREEN"}
    write_once(root/"comparison.json",result);return result


def main():
    root=ROOT/"runs"/datetime.now().strftime("makespan-tie-screen-%Y%m%d-%H%M%S-%f");root.mkdir()
    print("MAKESPAN_TIE_SCREEN_ROOT",root,flush=True);done=[];start=time.monotonic()
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs,order=prepare(root,STEMS,SEEDS,tuple(METHODS))
            write_once(root/"protocol.json",{"instances":specs,"seeds":SEEDS,"methods":METHODS,"order":order,"candidate":"COST_FULL",
                "basis":"FACTORY_LEX failed its old continuation gate and is stopped. Its pre-fixed COST_LEX ordinary control had substantially larger addedHV than STRICT and FACTORY_LEX on both development instances; this new protocol uses three fresh optimizer seeds and does not relabel the previous candidate passing.",
                "changed":"Only MAKESPAN local exact ties: lexicographically minimize TEC then TWC. Strict Cmax improvement remains primary and may trade other objectives as before. All CENTER/E/W rules unchanged. No modified global survival, Q reward/state/parameters, memory age, guide schedule, pool, proposal or quota.",
                "controls":"Original STRICT_FULL, dominance-safe neutral moves PARETO_FULL, no actual composition, unified objective preference, original FORCE sharing, Li v2 with STRICT and same COST_LEX, NSGA-II with STRICT and same COST_LEX. NSGA retains its global breeding and receives identical physical local roles/slots, as in prior matched-deep controls.",
                "engineering":"STRICT full500k exact paid sequence and frozen evidence must match before new performance data. Same paid initialization, 10000global/549inter/489351intra and complete physical ledger. Every returned front full decoder QA. No digest/trace in performance.",
                "efficacyGate":"Per instance: median >=1% over STRICT_FULL, >=2/3 positive pairs; median >=-1% against equally enhanced NSGA_COST; nonnegative vs PARETO_FULL; positive vs equally enhanced Li_COST, original Li_STRICT and original FORCE_STRICT. Positive median direction vs STRICT at refs1.25 and2. Failure stops this rule without lex-priority/tolerance/Q/seed scans.",
                "cooperationGate":"Separate: four duties vs uniform median >=1% on both; sharing vs SYNC median >=0.2% on at least one and >=-0.5% on the other. Generic improvement alone cannot establish four-group collaboration novelty.",
                "budget":"60 x500000 searchFE=30000000 plus500000 engineeringFE. Full QA, previous discovery and replay expenses separate. Same-time cuts are exploratory within FE-capped trajectories; true TIME_LIMIT independent confirmation still required.",
                "novelty":"Neutral lexicographic acceptance is a standard generic policy, not itself a paper contribution. Any viable result still requires mechanism attribution, recent-method comparison, untouched-instance confirmation and reproducible delivery. No mainline/public upload."})
            cp=build(root);engineering(root,cp)
            shutil.copy2(Path(__file__),root/"source/run_makespan_tie_screen.py")
            for spec in order:run(root,cp,spec);done.append(spec)
            result=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulSearchFE":len(done)*500000,"engineeringFE":500000,"failedEvaluationFE":0,
        "efficacyPrimaryPass":result["efficacyPrimaryPass"],"cooperationScreenPass":result["cooperationScreenPass"],"wallSeconds":time.monotonic()-start,
        "returnFullDecoderQA":sum(read(p)["offlineValidationDecodes"] for p in root.glob("*/*/*/summary.json"))})
    print("MAKESPAN_TIE_SCREEN_COMPLETE",[{k:v for k,v in x.items() if k!="effectsPct"} for x in result["instances"]],flush=True)


if __name__=="__main__":main()
