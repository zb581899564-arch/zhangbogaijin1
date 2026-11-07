"""Short prospective probe of accepted-information timing, before any full-budget variant."""
from datetime import datetime
from pathlib import Path
import shutil
import time

import numpy as np

from paired_survival_bench import prepare, class_hashes, ANCHOR
from context_release_build import BASIS
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, hypervolume, controller_lock
from run_paired_qgs_guidance import replace

STEMS=("20_8_5_1","100_2_3_1")
SEEDS=(9760003,9760033)
MODES=("GEN","ROLE_END","BATCH")


def build(root):
    src,classes=root/"source",root/"classes";src.mkdir();classes.mkdir()
    cp=(BASIS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
    body=(BASIS/"source/CanonicalHmopso.java").read_text(encoding="utf-8")
    body=replace(body,"            if (audit != null) audit.feedbackQgs(direction, step, action, leader);",
                 "            GuideFeedback.selected(leader, direction, step, action);\n"
                 "            if (audit != null) audit.feedbackQgs(direction, step, action, leader);")
    body=replace(body,"            List<Particle> next = global(current, direction, leader);",
                 "            List<Particle> next = global(current, direction, leader);\n"
                 "            GuideFeedback.afterBatch(state, next, direction, step);")
    (src/"CanonicalHmopso.java").write_text(body,encoding="utf-8")
    entry=(BASIS/"source/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry=replace(entry,"            if (digest != null) digest.update(paid, s);",
                  "            org.uma.jmetal.util.research.search.GuideFeedback.evaluated(s, paid);\n"
                  "            if (digest != null) digest.update(paid, s);")
    entry=replace(entry,"        obs.write(out);","        obs.write(out);\n"
                  "        append(out.resolve(\"guides.jsonl\"), org.uma.jmetal.util.research.search.GuideFeedback.diagnostics());")
    (src/"PddrIsolationRun.java").write_text(entry,encoding="utf-8")
    shutil.copy2(ROOT/"src/algorithms/diagnostics/GuideFeedback.java",src)
    shutil.copy2(Path(__file__),src)
    execute(["javac","-encoding","UTF-8","--release","8","-cp",cp,"-d",str(classes),*map(str,src.glob("*.java"))],root/"compile.log")
    write_once(root/"class-hashes.json",class_hashes(classes));cp=f"{classes};{cp}"
    (root/"classpath.txt").write_text(cp,encoding="utf-8");return cp


def run(root,cp,stem,seed,mode):
    out=root/stem/str(seed)/mode;out.mkdir();inp=root/stem/"inputs"
    cmd=["java","-Xms32m","-Xmx2g","-Dresearch.batch.mode=ROLE_CROWD",f"-Dresearch.guide.mode={mode}",
         "-cp",cp,"research.dynamic.PddrIsolationRun",str(inp/f"{stem}.txt"),str(inp/"RECONSTRUCTED-setup.txt"),
         str(inp/"fatigue-input.txt"),str(out),"SHARE_JOB_ALIGNED","AUDIT",str(out.parent/"ledger.csv"),"5100",str(seed),"100","5100"]
    write_once(out/"command.json",cmd);print("GUIDE_CELL",stem,seed,mode,flush=True)
    execute(cmd,out/"process.log")
    receipt,=rows(out/"run-receipt.jsonl")
    assert receipt["attempted"]==receipt["successful"]==receipt["decoder"]["dynamic.evaluations"]==5100 and receipt["failed"]==0
    assert receipt["search"]["initialization.evaluations"]==100 and receipt["search"]["global.evaluations"]==5000
    assert read(out/"summary.json")["offlineValidationDecodes"]==len(rows(out/"solutions.jsonl"))
    write_once(out/"verified.json",{"successfulFE":5100,"failed":0,"finalQA":True})
    return out


def engineering(root,cp):
    from run_dynamic_deep_roles import BRIDGE
    work=root/"engineering";work.mkdir();shutil.copytree(BRIDGE/"inputs",work/"20_2_3_1/inputs")
    folder=work/"20_2_3_1/8111009";folder.mkdir();shutil.copy2(ANCHOR/"ledger.csv",folder/"ledger.csv")
    original=(BASIS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
    old=run(work,original,"20_2_3_1",8111009,"OLD")
    new=run(work,cp,"20_2_3_1",8111009,"GEN")
    assert rows(old/"run-receipt.jsonl")[0]["paidSHA256"]==rows(new/"run-receipt.jsonl")[0]["paidSHA256"]
    for name in ("solutions.jsonl","initial-population.jsonl"):
        assert (old/name).read_bytes()==(new/name).read_bytes()
    assert [r["front"] for r in rows(old/"anytime.jsonl")]==[r["front"] for r in rows(new/"anytime.jsonl")]
    write_once(root/"engineering-gate.json",{"status":"PASS","successfulFE":10200,"paidSequenceAndFinalGenomesIdentical":True})


def analyze(root):
    results=[]
    for spec in read(root/"protocol.json")["instances"]:
        stem,norm=spec["stem"],spec["normalization"];metrics={}
        for seed in SEEDS:
            for mode in MODES:
                path=root/stem/str(seed)/mode;front=rows(path/"anytime.jsonl")[-1]["front"]
                data,=rows(path/"guides.jsonl");selected=[x for x in data["selections"] if x["action"]==2 and x["atFE"]>=850]
                metrics[(seed,mode)]={"HV":float(hypervolume((np.asarray(front)-norm["lower"])/norm["scale"],(1.5,)*3)),
                    "newGuideFraction":sum(x["firstPaidFE"]>100 for x in selected)/len(selected),
                    "crossRoleNewGuides":sum(x["firstPaidFE"]>100 and x["originRole"]!=x["role"] for x in selected),
                    "meanFirstDiscoveryAgeFE":float(np.mean([x["ageFE"] for x in selected])),
                    "searchSeconds":rows(path/"run-receipt.jsonl")[0]["searchSeconds"],"refreshSeconds":data["refreshSeconds"]}
        effects={m:[100*(metrics[(s,"BATCH")]["HV"]/metrics[(s,m)]["HV"]-1) for s in SEEDS] for m in ("GEN","ROLE_END")}
        passed=np.median(effects["GEN"])>=.5 and np.median(effects["ROLE_END"])>=0 and all(metrics[(s,"BATCH")]["newGuideFraction"]>=.2 for s in SEEDS)
        results.append({"stem":stem,"cells":[{"seed":s,"mode":m,**v} for (s,m),v in metrics.items()],
                        "batchEffectsPct":effects,"eligible":bool(passed)})
    wins=sum(e>0 for r in results for e in r["batchEffectsPct"]["GEN"])
    write_once(root/"comparison.json",{"instances":results,"positivePairedCells":wins,
               "worthFullGate":all(x["eligible"] for x in results) and wins>=3});return read(root/"comparison.json")


def main():
    root=ROOT/"runs"/datetime.now().strftime("guide-feedback-probe-%Y%m%d-%H%M%S-%f")
    root.mkdir();print("GUIDE_ROOT",root,flush=True);done=[];start=time.monotonic()
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs,order=prepare(root,STEMS,SEEDS,MODES)
            write_once(root/"protocol.json",{"instances":specs,"seeds":SEEDS,"modes":MODES,"order":order,"FEPerCell":5100,
                "hypothesis":"Earlier insertion of internally accepted schedules makes paid cross-role knowledge usable during QGS. "
                             "Existing proposals, per-group acceptance, Q parameters, fixed families, compose rule and global order unchanged.",
                "modesDescription":{"GEN":"Original generation-end remember only","ROLE_END":"Also offer the final accepted personal histories after each role's 50 batches",
                                    "BATCH":"Also offer accepted current states after each batch; rejected children never offered by this rule"},
                "provenance":"Exact four-vector first paid occurrence, not last snapshot-payment age. Captured for every selected guide; action2/new-guide/cross-role summaries separate.",
                "gate":"On both instances median BATCH/GEN HV gain >=0.5%, BATCH/ROLE_END >=0, each seed >=20% new (non-initial) action2 guides after FE850; "
                       "at least3/4 paired HV wins over GEN. Failure stops these timing rules; success merely authorizes a fresh500k closed-loop protocol.",
                "searchFE":61200,"engineeringFE":10200,"scope":"Global-stage mechanism probe; no whole-run, time-advantage or novelty claim."})
            cp=build(root);engineering(root,cp)
            for spec in order:run(root,cp,spec["stem"],spec["seed"],spec["arm"]);done.append(spec)
            result=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulFE":len(done)*5100,"engineeringFE":10200,
                                   "worthFullGate":result["worthFullGate"],"wallSeconds":time.monotonic()-start})
    print("GUIDE_COMPLETE",result,flush=True)


if __name__=="__main__":main()
