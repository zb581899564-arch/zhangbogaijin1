"""Capture paid ROLE_CROWD states, then compare actual kernels on identical parent/guide triples."""
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, hypervolume, controller_lock
from run_paired_qgs_guidance import replace

BASIS=ROOT/"runs/batch-survival-study-20261104-222516-378030"
STEMS=("20_8_5_1","100_2_3_1")
KERNELS=("PAPER","JOB_ALIGNED","CLASSIC_GLOBAL","CLASSIC_PERSONAL")


def build(root):
    src,classes=root/"source",root/"classes";src.mkdir();classes.mkdir()
    cp=(BASIS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
    capture=(ROOT/"src/java/search/MechanismCapture.java").read_text(encoding="utf-8")
    capture=replace(capture, '''        int phase = index >= 10000 ? 2 : index >= 5000 ? 1 : 0;
        long anchor = new long[] {250, 5000, 10000}[phase];
        if (index < anchor || index >= anchor + 8 || elapsed.getAsDouble() > limit) return;''',
        '''        int phase = -1;
        long[] anchors = {200, 1500, 3750, 4500};
        for (int p = 0; p < anchors.length; p++) if (index >= anchors[p] && index < anchors[p] + 8) { phase = p; break; }
        if (phase < 0 || elapsed.getAsDouble() > limit) return;''')
    capture=replace(capture,'new String[] {"early", "middle", "late"}[phase]',
                    'new String[] {"MAKESPAN", "CENTER", "ENERGY", "WORKER_COST"}[phase]')
    (src/"MechanismCapture.java").write_text(capture,encoding="utf-8")
    entry=(BASIS/"source/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry=replace(entry,"        DynamicSearch search = DynamicSearch.create(mode, in, params, dynamic, context, cfg, false, 0, 0);",
                  "        org.uma.jmetal.util.research.search.MechanismCapture mechanism = new org.uma.jmetal.util.research.search.MechanismCapture(\n"
                  "                context.clock()::elapsedSeconds, context.budget()::successful, Double.POSITIVE_INFINITY, false, input.getFileName().toString());\n"
                  "        DynamicSearch search = DynamicSearch.create(mode, in, params, dynamic, context, cfg, false, 0, 0, null, mechanism);")
    entry=replace(entry,"        obs.write(out);","        obs.write(out);\n        for (Map<String,Object> r : mechanism.finish()) append(out.resolve(\"mechanism.jsonl\"), r);")
    entry=replace(entry,"            if (digest != null && changed)","            if (changed)")
    entry=replace(entry,"            if (digest != null)\n                Files.write(out.resolve(\"archive-admissions.csv\"), admissions, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);",
                  "            Files.write(out.resolve(\"archive-admissions.csv\"), admissions, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);")
    (src/"PddrIsolationRun.java").write_text(entry,encoding="utf-8")
    shutil.copy2(Path(__file__),src)
    execute(["javac","-encoding","UTF-8","--release","8","-cp",cp,"-d",str(classes),str(src/"MechanismCapture.java"),str(src/"PddrIsolationRun.java")],root/"compile.log")
    (root/"classpath.txt").write_text(f"{classes};{cp}",encoding="utf-8")
    return f"{classes};{cp}"


def capture(root,cp,stem):
    inp=BASIS/stem/"inputs";out=root/stem;out.mkdir()
    (out/"empty-ledger.csv").write_text("visit,group,round,factory,paid,restarts\n",encoding="utf-8")
    cmd=["java","-Xms32m","-Xmx2g","-Dresearch.batch.mode=ROLE_CROWD","-cp",cp,"research.dynamic.PddrIsolationRun",
         str(inp/f"{stem}.txt"),str(inp/"RECONSTRUCTED-setup.txt"),str(inp/"fatigue-input.txt"),str(out),
         "SHARE_JOB_ALIGNED","LINEAR",str(out/"empty-ledger.csv"),"5100","9280009","100","5100"]
    write_once(out/"capture-command.json",cmd);execute(cmd,out/"capture.log")
    r,=rows(out/"run-receipt.jsonl");assert r["successful"]==5100 and r["failed"]==0
    old=next(x for x in rows(BASIS/stem/"9280009/ROLE_CROWD/anytime.jsonl") if x["fe"]==5100)
    assert rows(out/"anytime.jsonl")[-1]["front"]==old["front"]
    cases=[x for x in rows(out/"mechanism.jsonl") if x["type"]=="kernel-case"]
    assert len(cases)==32
    lines=[]
    for c in cases:
        p=c["parent"];family=p["family"];csv=lambda v:",".join(map(str,v))
        f=[c["caseId"],str(-1 if family is None else family),"-" if p["fixedFactoryByJob"] is None else csv(p["fixedFactoryByJob"])]
        for key in ("parent","personal","global"):f.extend(csv(c[key][name]) for name in ("JS","FA","MA","WA","objectives"))
        assert len(f)==18;lines.append("\t".join(f))
    (out/"cases.tsv").write_text("\n".join(lines)+"\n",encoding="utf-8")
    cmd=["java","-Xms32m","-Xmx2g","-cp",cp,"research.dynamic.KernelProbeRun",str(inp/f"{stem}.txt"),
         str(inp/"RECONSTRUCTED-setup.txt"),str(inp/"fatigue-input.txt"),str(out/"cases.tsv"),str(out/"probe"),"8","9360001"]
    write_once(out/"probe-command.json",cmd);execute(cmd,out/"probe.log")
    return cases


def analyze(root,stem,cases):
    folder=root/stem;norm=next(x for x in read(BASIS/"protocol.json")["instances"] if x["stem"]==stem)["normalization"]
    scale=np.asarray(norm["scale"])
    admitted=np.loadtxt(folder/"archive-admissions.csv",delimiter=",",skiprows=1)
    raw=rows(folder/"probe/kernel-raw.jsonl");out=[]
    for case in cases:
        base=admitted[admitted[:,0]<=case["successfulFE"],1:]/scale;base_hv=hypervolume(base,(1.5,)*3)
        gains={};cost={}
        for k in KERNELS:
            batch=[r for r in raw if r["caseId"]==case["caseId"] and r["kernel"]==k];assert len(batch)==8
            pts=np.asarray([r["child"]["objectives"] for r in batch])/scale
            gains[k]=max(0.,hypervolume(np.vstack((base,pts)),(1.5,)*3)-base_hv)
            cost[k]=sum(r["generationNanos"]+r["evaluationNanos"] for r in batch)/1e9
        out.append({"case":case["caseId"],"window":case["phase"],"family":case["parent"]["family"],
                    "composed":case["composedSource"],"batchHVgain":gains,"batchSeconds":cost})
    primary=[x for x in out if x["family"] is None and not x["composed"]]
    groups=[]
    for window in ("MAKESPAN","CENTER","ENERGY","WORKER_COST"):
        group=[x for x in primary if x["window"]==window]
        groups.append({"window":window,"n":len(group),"meanGain":{k:float(np.mean([x["batchHVgain"][k] for x in group])) if group else None for k in KERNELS}})
    sums={k:sum(x["batchHVgain"][k] for x in primary) for k in KERNELS}
    wins=sum(g["n"]>0 and g["meanGain"]["CLASSIC_GLOBAL"]>g["meanGain"]["JOB_ALIGNED"]+1e-12 for g in groups)
    eligible=sums["CLASSIC_GLOBAL"]>1.1*sums["JOB_ALIGNED"]+1e-12 and wins>=3
    return {"stem":stem,"primaryCases":len(primary),"groups":groups,"summedBatchGain":sums,"classicWinsWindows":wins,
            "worthClosedLoop":eligible,"cases":out}


def main():
    root=ROOT/"runs"/datetime.now().strftime("strong-state-kernel-%Y%m%d-%H%M%S-%f")
    root.mkdir();print("STRONG_KERNEL_ROOT",root,flush=True);start=time.monotonic()
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            write_once(root/"protocol.json",{"source":str(BASIS),"instances":STEMS,"seed":9280009,
                "captureFEPerInstance":5100,"windows":[200,1500,3750,4500],"casesPerWindow":8,"kernelReps":8,
                "primary":"Free and non-composed proposals only; four actual unchanged kernels on same parent/pbest/leader, "
                          "same repair/family guard and paid original reference state before the captured proposal.",
                "gate":"CLASSIC_GLOBAL summed same8FE gain >1.1x JOB_ALIGNED and better in >=3/4 windows on each instance "
                       "to warrant a closed-loop kernel hypothesis. Source-dependent gains do not prove full algorithm efficacy.",
                "timing":"All capture, parent replays, candidates and QA charged; no pure wall-time superiority claim from this microprobe."})
            cp=build(root);results=[analyze(root,stem,capture(root,cp,stem)) for stem in STEMS]
            write_once(root/"comparison.json",results)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","error":str(exc)});raise
    receipts=[read(root/s/"probe/kernel-receipt.json") for s in STEMS]
    write_once(root/"status.json",{"status":"COMPLETE","captureFE":10200,"probeFE":sum(r["successfulFE"] for r in receipts),
                                   "wallSeconds":time.monotonic()-start,"worthClosedLoop":all(r["worthClosedLoop"] for r in results)})
    print("STRONG_KERNEL_COMPLETE",[{k:v for k,v in r.items() if k!="cases"} for r in results],flush=True)


if __name__=="__main__":main()
