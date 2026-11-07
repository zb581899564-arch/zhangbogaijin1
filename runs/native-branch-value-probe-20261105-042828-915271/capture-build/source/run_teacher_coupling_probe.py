"""Frozen prospective test of common-teacher offspring correlation, before changing any search algorithm."""
from datetime import datetime
from pathlib import Path
import shutil
import time

import numpy as np

from teacher_cohort_build import build
from teacher_coupling_analysis import analyze
from pool_phase_build import OBS
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from research.search_mechanism.campaign import _case_fields

SOURCE=ROOT/"runs/survival-context-factorial-20261105-002440-955879"
STEMS=("20_8_5_1","100_2_3_1")
SEEDS=(10060007,10060031)
PROBE_SEED=10170011


def capture(root,cp,stem,seed,enabled):
    out=root/stem/str(seed)/("ON" if enabled else "OFF");out.mkdir();inp=root/stem/"inputs"
    cmd=["java","-Xms32m","-Xmx2g","-Dresearch.group.mode=FULL_ROLE","-Dresearch.reward.mode=GROUP","-Dresearch.batch.mode=ROLE_CROWD",
         f"-Dresearch.teacherCohort.capture={str(enabled).lower()}","-Dresearch.survival.trace=false","-cp",cp,"research.dynamic.PddrIsolationRun",
         str(inp/f"{stem}.txt"),str(inp/"RECONSTRUCTED-setup.txt"),str(inp/"fatigue-input.txt"),str(out),"SHARE_JOB_ALIGNED","LINEAR",
         str(out.parent/"ledger.csv"),"5100",str(seed),"100","5100"]
    write_once(out/"command.json",cmd);print("TEACHER_CAPTURE",stem,seed,enabled,flush=True);execute(cmd,out/"run.log")
    receipt,=rows(out/"run-receipt.jsonl");assert receipt["successful"]==receipt["attempted"]==5100 and receipt["failed"]==0
    if enabled:
        prior=out.parent/"OFF";assert receipt["paidSHA256"]==rows(prior/"run-receipt.jsonl")[0]["paidSHA256"]
        for name in ("solutions.jsonl","initial-population.jsonl","local-ledger.csv"):
            assert (out/name).read_bytes()==(prior/name).read_bytes()
        assert [r["front"] for r in rows(out/"anytime.jsonl")]==[r["front"] for r in rows(prior/"anytime.jsonl")]
        write_once(out/"observation-equivalence.json",{"status":"PASS","fullPaidPrefixUnchanged":True})
    return out


def run_probe(root,cp,stem):
    cohorts=[];lines=[]
    for seed in SEEDS:
        data,=rows(root/stem/str(seed)/"ON/teacher-cohorts.jsonl");assert data["rolesCaptured"]==4,"Missing pre-fixed action2 window; no resampling"
        for cohort in data["cohorts"]:
            index=len(cohorts);rng=np.random.default_rng(PROBE_SEED+index);library=cohort["guideLibrary"];guides=[]
            objective={"MAKESPAN":0,"ENERGY":1,"WORKER_COST":2}.get(cohort["role"])
            obj=np.asarray([g["objectives"] for g in library])
            assert all(not np.any(np.all(obj<=x,axis=1)&np.any(obj<x,axis=1)) for x in obj),"Guide archive is not ND"
            for _ in range(16):
                a,b=rng.integers(len(library),size=2)
                if objective is not None and library[b]["objectives"][objective]<library[a]["objectives"][objective]:a=b
                guides.append(library[a])
            for row in sorted(cohort["parents"],key=lambda r:r["parentIndex"]):
                for g,guide in enumerate(guides):
                    lines.append(_case_fields({"caseId":f"c{index}-p{row['parentIndex']}-g{g}","parent":row["parent"],"personal":row["personal"],"global":guide}))
            genome=lambda g:tuple(tuple(g[k]) for k in ("JS","FA","MA","WA"))
            cohorts.append({**cohort,"sourceSeed":seed,"sampledGuides":guides,"uniqueSampledGuides":len({genome(g) for g in guides})})
    path=root/stem/"cases.tsv";path.write_text("\n".join(lines)+"\n",encoding="utf-8")
    write_once(root/stem/"cases.json",{"cohorts":cohorts,"caseCount":len(lines),"operatorSeedRule":"splitmix(base + floor(caseIndex/16)*1009 + rep), constant per parent/rep across guides"})
    inp=root/stem/"inputs";output=root/stem/"probe"
    cmd=["java","-Xms32m","-Xmx2g","-cp",cp,"research.dynamic.KernelProbeRun",str(inp/f"{stem}.txt"),
         str(inp/"RECONSTRUCTED-setup.txt"),str(inp/"fatigue-input.txt"),str(path),str(output),"2",str(PROBE_SEED)]
    write_once(root/stem/"probe-command.json",cmd);execute(cmd,root/stem/"probe.log")
    receipt=read(output/"kernel-receipt.json");assert receipt["successfulFE"]==len(lines)*11 and receipt["failedFE"]==0
    return receipt


def main():
    root=ROOT/"runs"/datetime.now().strftime("teacher-coupling-probe-%Y%m%d-%H%M%S-%f")
    root.mkdir();print("TEACHER_COUPLING_ROOT",root,flush=True);done=[];start=time.monotonic()
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs=read(SOURCE/"protocol.json")["instances"]
            for stem in STEMS:
                shutil.copytree(SOURCE/stem/"inputs",root/stem/"inputs")
                for seed in SEEDS:
                    folder=root/stem/str(seed);folder.mkdir();(folder/"ledger.csv").write_text("visit,group,round,factory,paid,restarts\n",encoding="utf-8")
            write_once(root/"protocol.json",{"instances":specs,"sourceSeeds":SEEDS,"probeSeed":PROBE_SEED,"captureReplayFE":40800,"plannedProbeFE":22528,
                "hypothesis":"A single action2 guide shared across a QGS batch correlates offspring and reduces batch HV coverage, even with identical marginal guide quality and offspring set.",
                "source":"Unchanged FULL_ROLE four duties/fixed families/sharing; first actual QGS action2 batch at/after step24 in each role, eight equally spaced free parents. Four pre-fixed roles, two source seeds, two instances. Missing windows retained, never benefit-resampled.",
                "engineering":"Capture OFF vs ON entire5100 paid-prefix SHA, initial/final genes, physical ledger and checkpoint fronts must match.",
                "children":"Per cohort8 parents x16 sampled action2 archive-tournament guides x2 paired construction seeds. Actual four kernels evaluated by existing KernelProbeRun; only pre-fixed JOB_ALIGNED used for primary test. All3 parent/teacher replays and all4-kernel offspring charged; every child full-decoder QA.",
                "noise":"Same per-parent/rep construction seed across all16 guides, splitmix-derived independent parent streams. Thus repeated identical guides give identical children, without relying on correlated neighboring Java seeds.",
                "groupings":"COMMON: each batch shares guide index g; LATIN: parent p receives index(g+p)%16; RANDOM: independent fixed permutation of16 indices for each parent. Each grouping uses each identical evaluated child exactly once per parent/rep. All per-parent teacher/noise marginals are exactly equal.",
                "score":"Mean8-child union HV addition over the actual already-paid archive immediately before the native batch. No new result archive feeds search. Copying a known parent/guide earns no new HV.",
                "gate":"Both instances: at least6 informative cohorts; median LATIN improvement in mean added batchHV >=10%, RANDOM >=5%; both controls positive in >=6/8 cohorts; both source-seed CENTER cohorts LATIN nonnegative. Zero common-addedHV cohorts inconclusive, not denominator-filled. A pass only authorizes a fresh closed-loop protocol with full guide-selection cost.",
                "limits":"Conditional action2 candidate dependence, eight free parents only; not all Q actions, complete search, same-time superiority, fatigue specificity or novelty."})
            cp=build(root);oldcp=(OBS/"classpath.txt").read_text(encoding="utf-8-sig").strip();receipts=[]
            for stem in STEMS:
                for seed in SEEDS:
                    capture(root,oldcp,stem,seed,False);done.append((stem,seed,"OFF"))
                    capture(root,cp,stem,seed,True);done.append((stem,seed,"ON"))
                receipts.append(run_probe(root,cp,stem))
            result=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completedCaptures":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulCaptureReplayFE":len(done)*5100,
        "successfulProbeFE":sum(r["successfulFE"] for r in receipts),"failedEvaluationFE":0,
        "offlineCandidateQA":sum(r["offlineCandidateReplays"] for r in receipts),"worthClosedLoop":result["bothInstancesSupported"],"wallSeconds":time.monotonic()-start})
    print("TEACHER_COUPLING_COMPLETE",[{k:v for k,v in r.items() if k!="cells"} for r in result["instances"]],flush=True)


if __name__=="__main__":main()
