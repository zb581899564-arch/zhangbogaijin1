"""Factorial global-schedule/accepted-feedback mechanism probe with exact serial replay first."""
from datetime import datetime
from pathlib import Path
import shutil
import time

import numpy as np

from paired_survival_bench import run_cell
from qgs_epoch_build import BASIS,build
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,hypervolume,controller_lock

STEMS=("20_8_5_1","100_2_3_1")
SEEDS=(10620007,10620037)
ARMS={"SERIAL_STALE":("SERIAL",False),"SERIAL_FRESH":("SERIAL",True),
      "SWEEP_STALE":("SWEEP",False),"SWEEP_FRESH":("SWEEP",True),"NSGA":("SERIAL",False)}


def flags(arm,audit=False):
    layout,fresh=ARMS[arm];classic=arm=="NSGA"
    return {"research.qgs.layout":layout,"research.qgs.fresh":str(fresh).lower(),"research.personal.mode":"OLDEST",
            "research.globalFlow.trace":"true","research.memory.audit":str(audit).lower(),
            "research.group.mode":"PAIR" if classic else "FULL_ROLE","research.reward.mode":"INDIVIDUAL" if classic else "GROUP",
            "research.batch.mode":"FORCE" if classic else "ROLE_CROWD"}


def engineering(root,cp):
    execute(["java","-cp",cp,"org.uma.jmetal.util.research.search.QgsEpochScheduleChecks"],root/"schedule-checks.log")
    work=root/"engineering";work.mkdir();stem="20_8_5_1";seed=9940003
    old=BASIS/"engineering"/stem/str(seed)/"OLD_FULL"
    shutil.copytree(BASIS/stem/"inputs",work/stem/"inputs");folder=work/stem/str(seed);folder.mkdir()
    shutil.copy2(old.parent/"ledger.csv",folder/"ledger.csv")
    out=run_cell(work,cp,{"stem":stem,"seed":seed,"arm":"SERIAL_STALE"},flags("SERIAL_STALE",True))
    for name in ("solutions.jsonl","initial-population.jsonl","local-ledger.csv"):
        assert (out/name).read_bytes()==(old/name).read_bytes(),name
    assert [r["front"] for r in rows(out/"anytime.jsonl")]==[r["front"] for r in rows(old/"anytime.jsonl")]
    a,b=rows(out/"run-receipt.jsonl")[0],rows(old/"run-receipt.jsonl")[0]
    assert a["paidSHA256"]==b["paidSHA256"] and a["search"]==b["search"]
    assert read(out/"group.jsonl")==read(old/"group.jsonl")
    write_once(root/"engineering-gate.json",{"status":"PASS","successfulFE":500000,"sameFullPaidSequence":True,
               "sameFrozenGenesFrontsLedgerCounters":True,"persistentFourQAgentsFixture":True})


def short_run(root,cp,stem,seed,arm):
    path=root/stem/str(seed)/arm;path.mkdir();inp=root/stem/"inputs"
    cmd=["java","-Xms32m","-Xmx2g",*("-D"+k+"="+str(v) for k,v in flags(arm,True).items()),"-cp",cp,"research.dynamic.PddrIsolationRun",
         str(inp/f"{stem}.txt"),str(inp/"RECONSTRUCTED-setup.txt"),str(inp/"fatigue-input.txt"),str(path),
         "NSGA2_4V" if arm=="NSGA" else "SHARE_JOB_ALIGNED","LINEAR",str(path.parent/"ledger.csv"),"5100",str(seed),"100","5100"]
    write_once(path/"command.json",cmd);print("QGS_EPOCH_CELL",stem,seed,arm,flush=True);execute(cmd,path/"run.log")
    receipt,=rows(path/"run-receipt.jsonl")
    assert receipt["successful"]==receipt["attempted"]==receipt["decoder"]["dynamic.evaluations"]==5100 and receipt["failed"]==0
    assert receipt["search"]["initialization.evaluations"]==100 and receipt["search"]["global.evaluations"]==5000
    if arm!="NSGA":
        assert all(receipt["search"][f"qgs.g{i}.updates"]==50 for i in (1,2,3,4))
    prior=[p/"initial-population.jsonl" for p in path.parent.iterdir() if p.is_dir() and (p/"initial-population.jsonl").exists()]
    assert all(p.read_bytes()==prior[0].read_bytes() for p in prior)
    assert read(path/"summary.json")["offlineValidationDecodes"]==len(rows(path/"solutions.jsonl"))
    write_once(path/"verified.json",{"successfulFE":5100,"same100InitialGenomesAndObjectives":True,"fullReturnQA":True})


def backward_edges(flow,receiver,allowed):
    total=0
    for edge,n in flow["action2CreatorEdges"].items():
        epoch,target,producer,when=edge.split(":")
        if epoch=="1" and target==receiver and producer in allowed and when=="SAME_EPOCH":total+=n
    return total


def analyze(root):
    results=[];wins={"SERIAL_STALE":0,"SERIAL_FRESH":0}
    for spec in read(root/"protocol.json")["instances"]:
        stem,norm=spec["stem"],spec["normalization"];metrics={}
        for seed in SEEDS:
            for arm in ARMS:
                path=root/stem/str(seed)/arm;front=rows(path/"anytime.jsonl")[-1]["front"]
                metrics[(seed,arm)]={"HV":float(hypervolume((np.asarray(front)-norm["lower"])/norm["scale"],(1.5,)*3)),
                                     "flow":rows(path/"global-flow.jsonl")[0]}
        effects={a:[100*(metrics[(s,"SWEEP_FRESH")]["HV"]/metrics[(s,a)]["HV"]-1) for s in SEEDS] for a in ARMS if a!="SWEEP_FRESH"}
        for arm in wins:wins[arm]+=sum(v>0 for v in effects[arm])
        flows=[metrics[(s,"SWEEP_FRESH")]["flow"] for s in SEEDS]
        reverse_m=[backward_edges(f,"MAKESPAN",("CENTER","ENERGY","WORKER_COST")) for f in flows]
        reverse_c=[backward_edges(f,"CENTER",("ENERGY","WORKER_COST")) for f in flows]
        passed=np.median(effects["SERIAL_STALE"])>=.5 and np.median(effects["SERIAL_FRESH"])>=.5 \
            and np.median(effects["SWEEP_STALE"])>0 and np.median(effects["NSGA"])>=-2 and all(v>0 for v in reverse_m) and sum(reverse_c)>0
        results.append({"stem":stem,"cells":[{"seed":s,"arm":a,**m} for (s,a),m in metrics.items()],
                        "sweepFreshEffectsPct":effects,"makespanReverseSelections":reverse_m,"centerReverseSelections":reverse_c,"supported":bool(passed)})
    result={"instances":results,"pairedPositiveCounts":wins,"worthClosedLoop":all(r["supported"] for r in results) and all(v>=3 for v in wins.values()),
            "scope":"First-global-stage mechanism screen; creator-role selections are availability/exposure, not gene transmission or causal credit. No same-time or complete-search claim."}
    write_once(root/"analysis.json",result);return result


def main():
    root=ROOT/"runs"/datetime.now().strftime("qgs-epoch-probe-%Y%m%d-%H%M%S-%f");root.mkdir()
    print("QGS_EPOCH_ROOT",root,flush=True);done=[];start=time.monotonic()
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs=read(BASIS/"protocol.json")["instances"]
            for stem in STEMS:
                shutil.copytree(BASIS/stem/"inputs",root/stem/"inputs")
                for seed in SEEDS:
                    folder=root/stem/str(seed);folder.mkdir();(folder/"ledger.csv").write_text("visit,group,round,factory,paid,restarts\n",encoding="utf-8")
            write_once(root/"protocol.json",{"instances":specs,"seeds":SEEDS,"arms":ARMS,"candidate":"SWEEP_FRESH","diagnosticFE":102000,"engineeringFE":500000,
                "hypothesis":"Global serial50-step blocks prevent later-role accepted knowledge influencing earlier roles in the first generation. Interleave one step per role with the same batch-current feedback rule to test bidirectional cooperation.",
                "factorial":"SERIAL/SWEEP x STALE/FRESH, plus matched NSGA global prefix. Every physical role retains its own Q table/observation for50 updates. Original order within sweep M/C/E/W, exactly50 sweeps. No refresh-interval, order or quota scan.",
                "preserved":"OLDEST personal semantics (common proven O1 ND tie engine), FULL_ROLE survival/group reward, four duties/15-55-15-15, Q parameters, JOB_ALIGNED, fixedFA families, pool cap/eta/frequency, original single deep local phase and physical ledger. Fresh offers only accepted current states, never rejected proposals.",
                "engineering":"Single-step refactor SERIAL_STALE must reproduce frozen OLD_FULL full500000 paid sequence SHA, front checkpoints, genes, physical ledger/restarts and search/group counts. Zero-decoder fixture checks persistent independent Q agents,50 updates and schedule ordering.",
                "provenance":"Annotate creator role/epoch before ordinary evaluation; this metadata does not enter model or search decisions. Selected action2 guide birth epoch/role recorded. It is snapshot origin, not proof of gene transfer or quality.",
                "gate":"Each instance median SWEEP_FRESH >=0.5% vs both serial variants, >SWEEP_STALE, >=-2% vs NSGA at5100; >=3/4 positive pairs vs each serial across instances. Each source seed M must select a same-epoch later-role guide; C must select E/W at least once per instance. Failure stops this schedule/feedback combination without order/interval scans.",
                "limits":"Short-stage gate, not the final >=-1%500k competitiveness standard. No mainline change, final confirmation or novelty claim. All replay/init/diagnostic FE and offline QA counted. Trace and digest costs separate from any performance claim."})
            cp=build(root);engineering(root,cp)
            for i,stem in enumerate(STEMS):
                for j,seed in enumerate(SEEDS):
                    arms=list(ARMS);offset=(i+j)%len(arms)
                    for arm in arms[offset:]+arms[:offset]:short_run(root,cp,stem,seed,arm);done.append((stem,seed,arm))
            result=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    qa=sum(read(p)["offlineValidationDecodes"] for p in root.glob("*/*/*/summary.json"))
    write_once(root/"status.json",{"status":"COMPLETE","successfulDiagnosticFE":len(done)*5100,"engineeringFE":500000,
            "failedEvaluationFE":0,"returnFullDecoderQA":qa,"worthClosedLoop":result["worthClosedLoop"],"wallSeconds":time.monotonic()-start})
    print("QGS_EPOCH_COMPLETE",[{"stem":r["stem"],"effects":r["sweepFreshEffectsPct"],"supported":r["supported"]} for r in result["instances"]],flush=True)


if __name__=="__main__":main()
