"""Test a newly localized M-only hypothesis on two other frozen state seeds; no full solver change."""
from datetime import datetime
from pathlib import Path
import shutil
import time

from run_long_budget_bridge import ROOT,read,rows,write_once,controller_lock
from run_strong_state_kernel_probe import build,capture,analyze,STEMS

SEEDS=(9280039,9280071)


def main():
    root=ROOT/"runs"/datetime.now().strftime("makespan-kernel-holdout-%Y%m%d-%H%M%S-%f")
    root.mkdir();print("M_KERNEL_ROOT",root,flush=True);start=time.monotonic()
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            write_once(root/"protocol.json",{"source":"strong-state-kernel-20261104-230726-286100",
                "scope":"The all-role replacement gate failed. Only the M window showed best-Cmax wins in5/7 "
                        "free-parent cases in each instance. Freeze a new M-only hypothesis; do not reclassify the failed all-role gate.",
                "instances":STEMS,"stateSeeds":SEEDS,"candidateReps":32,
                "primary":"For each instance across both other state seeds, CLASSIC_GLOBAL must win best-Cmax in "
                          "at least two thirds of M cases and have >1.1x total same32FE new-HV gain vs JOB_ALIGNED. "
                          "Other role results remain descriptive and cannot replace the primary window.",
                "next":"Only if both instances pass, a new paired full-budget M-only vs all-role vs original-kernel "
                       "study can start. Same-parent evidence alone is never final method efficacy."})
            cp=build(root);shutil.copy2(Path(__file__),root/"source")
            summaries=[];details=[];probe_fe=0
            for i,seed in enumerate(SEEDS):
                part=root/str(seed);part.mkdir()
                for stem in STEMS:
                    cases=capture(part,cp,stem,seed,32,9361001+i*10000)
                    report=analyze(part,stem,cases,32);details.append({"stateSeed":seed,**report})
                    raw=rows(part/stem/"probe/kernel-raw.jsonl")
                    for c in cases:
                        if c["phase"]!="MAKESPAN" or c["parent"]["family"] is not None or c["composedSource"]:continue
                        b={k:min(r["child"]["objectives"][0] for r in raw if r["caseId"]==c["caseId"] and r["kernel"]==k)
                           for k in ("JOB_ALIGNED","CLASSIC_GLOBAL")}
                        gain=next(x["batchHVgain"] for x in report["cases"] if x["case"]==c["caseId"])
                        summaries.append({"stem":stem,"stateSeed":seed,"case":c["caseId"],"bestCmax":b,"batchHVgain":gain})
                    probe_fe+=read(part/stem/"probe/kernel-receipt.json")["successfulFE"]
            decisions=[]
            for stem in STEMS:
                group=[x for x in summaries if x["stem"]==stem]
                wins=sum(x["bestCmax"]["CLASSIC_GLOBAL"]<x["bestCmax"]["JOB_ALIGNED"] for x in group)
                gains={k:sum(x["batchHVgain"][k] for x in group) for k in ("JOB_ALIGNED","CLASSIC_GLOBAL")}
                passed=3*wins>=2*len(group) and gains["CLASSIC_GLOBAL"]>1.1*gains["JOB_ALIGNED"]+1e-12
                decisions.append({"stem":stem,"n":len(group),"CmaxWins":wins,"summedBatchHVgain":gains,"pass":passed})
            write_once(root/"comparison.json",{"decisions":decisions,"M_cases":summaries,"allCases":details})
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","captureFE":20400,"probeFE":probe_fe,
                                   "worthFullLoop":all(x["pass"] for x in decisions),"wallSeconds":time.monotonic()-start})
    print("M_KERNEL_COMPLETE",decisions,flush=True)


if __name__=="__main__":main()
