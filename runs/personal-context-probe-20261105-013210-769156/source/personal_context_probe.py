"""Paired same-parent comparison of existing-history selection rules; no closed-loop search change."""
from datetime import datetime
import shutil
import time

import numpy as np

from teacher_cohort_build import build
from run_teacher_coupling_probe import capture
from pool_phase_build import OBS
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,hypervolume,controller_lock
from research.search_mechanism.campaign import _case_fields

SOURCE=ROOT/"runs/survival-context-factorial-20261105-002440-955879"
STEMS=("20_8_5_1","100_2_3_1")
SEEDS=(10280003,10280033)
PROBE_SEED=10390011
RULES=("OLDEST","CURRENT","LATEST","UNIFORM","CONTEXT")


def select_history(row,reference,seed):
    history=row["personalHistory"];assert history
    key=lambda s:tuple(tuple(s[k]) for k in ("JS","FA","MA","WA","objectives"))
    assert key(history[0])==key(row["personal"]),"CENTER personal teacher is not oldest surviving ND insertion"
    h=np.asarray([s["objectives"] for s in history]);ref=np.asarray(reference)
    assert all(not np.any(np.all(h<=x,axis=1)&np.any(h<x,axis=1)) for x in h)
    fitness=[]
    for x in h:
        dominates=np.sum(np.all(x<=ref,axis=1)&np.any(x<ref,axis=1))
        dominated=np.sum(np.all(ref<=x,axis=1)&np.any(ref<x,axis=1))
        fitness.append(float(dominated)+1./(int(dominates)+1))
    index=min(range(len(history)),key=lambda i:(fitness[i],-i))
    chosen={"OLDEST":history[0],"CURRENT":row["parent"],"LATEST":history[-1],
            "UNIFORM":history[int(np.random.default_rng(seed).integers(len(history)))],"CONTEXT":history[index]}
    return chosen,{"historySize":len(history),"contextIndex":index,"contextChangesOldest":key(chosen["CONTEXT"])!=key(chosen["OLDEST"]),
                   "contextChangesLatest":key(chosen["CONTEXT"])!=key(chosen["LATEST"]),"scores":fitness}


def probe(root,cp,stem):
    inputs=[];manifest=[]
    for seed in SEEDS:
        data,=rows(root/stem/str(seed)/"ON/teacher-cohorts.jsonl")
        centers=[c for c in data["cohorts"] if c["role"]=="CENTER"]
        assert len(centers)==1,"Missing predefined CENTER cohort; no replacement"
        cohort=centers[0]
        for row in sorted(cohort["parents"],key=lambda r:r["parentIndex"]):
            index=len(manifest);chosen,selection=select_history(row,cohort["groupReference"],PROBE_SEED+index)
            for rule in RULES:
                inputs.append(_case_fields({"caseId":f"p{index}-{rule}","parent":row["parent"],"personal":chosen[rule],"global":row["nativeLeader"]}))
            manifest.append({"sourceSeed":seed,"step":cohort["step"],"background":cohort["background"],"parent":row["parent"],"chosenPersonal":chosen,**selection})
    path=root/stem/"cases.tsv";path.write_text("\n".join(inputs)+"\n",encoding="utf-8")
    write_once(root/stem/"manifest.json",manifest);inp=root/stem/"inputs";output=root/stem/"probe"
    command=["java","-Xms32m","-Xmx2g","-cp",cp,"research.dynamic.KernelProbeRun",str(inp/f"{stem}.txt"),
             str(inp/"RECONSTRUCTED-setup.txt"),str(inp/"fatigue-input.txt"),str(path),str(output),"16",str(PROBE_SEED)]
    write_once(root/stem/"probe-command.json",command);execute(command,root/stem/"probe.log")
    receipt=read(output/"kernel-receipt.json");assert receipt["successfulFE"]==len(inputs)*67 and receipt["failedFE"]==0
    return receipt


def analyze(root):
    results=[]
    for spec in read(root/"protocol.json")["instances"]:
        stem,norm=spec["stem"],spec["normalization"];parents=read(root/stem/"manifest.json")
        raw=[r for r in rows(root/stem/"probe/kernel-raw.jsonl") if r["kernel"]=="JOB_ALIGNED"]
        cells=[];sums={s:{r:0. for r in RULES} for s in SEEDS}
        for index,parent in enumerate(parents):
            base=(np.asarray(parent["background"])-norm["lower"])/norm["scale"];baseline=float(hypervolume(base,(1.5,)*3))
            means={}
            for rule in RULES:
                rows_=[r for r in raw if r["caseId"]==f"p{index}-{rule}"];assert len(rows_)==16
                values=[]
                for r in rows_:
                    point=(np.asarray(r["child"]["objectives"])-norm["lower"])/norm["scale"]
                    gain=0. if np.any(np.all(base<=point,axis=1)) else max(0.,100*(float(hypervolume(np.vstack([base,point]),(1.5,)*3))/baseline-1))
                    values.append(gain)
                means[rule]=float(np.mean(values));sums[parent["sourceSeed"]][rule]+=means[rule]
            cells.append({"parentIndex":index,"sourceSeed":parent["sourceSeed"],"historySize":parent["historySize"],
                          "contextChangesOldest":parent["contextChangesOldest"],"meanSingleCandidateGainPct":means})
        total={rule:sum(sums[s][rule] for s in SEEDS) for rule in RULES}
        effects={r:100*(total["CONTEXT"]/total[r]-1) if total[r]>1e-12 else None for r in RULES if r!="CONTEXT"}
        changed=sum(c["contextChangesOldest"] for c in cells)/len(cells)
        passed=effects["OLDEST"] is not None and effects["OLDEST"]>=10 and changed>=.25 \
            and all(total["CONTEXT"]>total[r] for r in ("CURRENT","LATEST","UNIFORM")) \
            and all(sums[s]["CONTEXT"]>sums[s]["OLDEST"] for s in SEEDS)
        results.append({"stem":stem,"parentCells":cells,"sourceSums":sums,"sumMeanGainPct":total,"contextEffectsPct":effects,
                        "contextChangedOldestFraction":changed,"supported":bool(passed)})
    result={"instances":results,"bothInstancesSupported":all(r["supported"] for r in results),
            "scope":"Same native global guide and parent, paired per-parent/rep construction noise. Only personal source changes. Conditional single-proposal value, not a search or time-performance result."}
    write_once(root/"analysis.json",result);return result


def main():
    root=ROOT/"runs"/datetime.now().strftime("personal-context-probe-%Y%m%d-%H%M%S-%f")
    root.mkdir();print("PERSONAL_CONTEXT_ROOT",root,flush=True);done=[];receipts=[];start=time.monotonic()
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs=read(SOURCE/"protocol.json")["instances"]
            for stem in STEMS:
                shutil.copytree(SOURCE/stem/"inputs",root/stem/"inputs")
                for seed in SEEDS:
                    folder=root/stem/str(seed);folder.mkdir();(folder/"ledger.csv").write_text("visit,group,round,factory,paid,restarts\n",encoding="utf-8")
            write_once(root/"protocol.json",{"instances":specs,"sourceSeeds":SEEDS,"rules":RULES,"primary":"CONTEXT","captureReplayFE":40800,"plannedProbeFE":10720,
                "hypothesis":"CENTER pbest chooses oldest surviving ND insertion because PDDR over its own ND archive ties. Score personal history against current peer-group objectives to recover context, retaining latest insertion only as equal-score tie-break.",
                "authority":"Controlled research variant; not a claim that original paper mandates a different tie-break or that this is a verified implementation bug.",
                "inputs":"Fresh source seeds; native first CENTER action2 at/after step24; eight free parents. Capture actual personal ND history and already-paid current peer group. OFF/ON full5100 paid-prefix and endpoint equivalence mandatory.",
                "rulesDescription":{"OLDEST":"Frozen original ND-history PDDR tie behavior","CURRENT":"Use current parent","LATEST":"Latest surviving ND insertion","UNIFORM":"One pre-fixed uniform ND-history sample","CONTEXT":"Minimize dominated-by-peers +1/(dominates-peers+1), ties latest. History internally ND, so this equals its PDDR scores in peers union history."},
                "pairing":"Actual native global guide unchanged. Same per-parent/rep splitmix construction seed for all five personal rules. Existing four actual kernels all evaluated and charged, only JOB_ALIGNED primary.16 reps per rule; all children full QA.",
                "score":"Mean single-child HV improvement over the actual paid pre-batch archive, summed equally over8 parents per source seed. Known teacher/parent copies earn zero. No free best-of16 selection.",
                "gate":"Both instances: CONTEXT changes >=25% of oldest choices, improves aggregate mean addition >=10% vs OLDEST, exceeds CURRENT/LATEST/UNIFORM, and both source seeds positive vs OLDEST. Zero OLDEST baseline inconclusive. Failure stops this context rule without tie/weight/seed scans.",
                "scope":"No mainline edit, closed-loop efficacy, same-time or novelty claim. A pass only permits a separately frozen whole-budget study including Li with the same generic memory enhancement."})
            cp=build(root,operator_block=5,extra_sources=("personal_context_probe.py",));oldcp=(OBS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
            for stem in STEMS:
                for seed in SEEDS:
                    capture(root,oldcp,stem,seed,False);done.append((stem,seed,"OFF"))
                    capture(root,cp,stem,seed,True);done.append((stem,seed,"ON"))
                receipts.append(probe(root,cp,stem))
            result=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completedCaptures":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","captureReplayFE":len(done)*5100,"probeFE":sum(r["successfulFE"] for r in receipts),
        "failedEvaluationFE":0,"offlineCandidateQA":sum(r["offlineCandidateReplays"] for r in receipts),"worthClosedLoop":result["bothInstancesSupported"],"wallSeconds":time.monotonic()-start})
    print("PERSONAL_CONTEXT_COMPLETE",[{k:v for k,v in r.items() if k!="parentCells"} for r in result["instances"]],flush=True)


if __name__=="__main__":main()
