"""Separate reward-alignment hypothesis on the original serial schedule, without failed sweep/memory variants."""
from datetime import datetime
from pathlib import Path
import shutil
import time

import numpy as np

from paired_survival_bench import class_hashes
from run_personal_memory_screen import engineering
from qgs_epoch_build import BASIS,GROUP
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,hypervolume,controller_lock
from run_paired_qgs_guidance import replace

STEMS=("20_8_5_1","100_2_3_1")
SEEDS=(10730003,10730033)
ARMS=("MEAN","HV","ZERO","NSGA")


def build(root):
    src,classes=root/"source",root/"classes";src.mkdir();classes.mkdir()
    cp=(BASIS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
    body=(GROUP/"source/CanonicalHmopso.java").read_text(encoding="utf-8")
    body=replace(body,"        if (updatePolicy != null) updatePolicy.initialized(solutions(population));",
                 "        if (updatePolicy != null) updatePolicy.initialized(solutions(population));\n        CenterHypervolumeReward.initialize(solutions(population));")
    body=replace(body,"double reward = GroupReward.compute(current, next, preference);","double reward = CenterHypervolumeReward.compute(current, next, preference);")
    (src/"CanonicalHmopso.java").write_text(body,encoding="utf-8")
    entry=(BASIS/"source/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry=replace(entry,"        obs.write(out);","        obs.write(out);\n        append(out.resolve(\"center-utility.jsonl\"), org.uma.jmetal.util.research.search.CenterHypervolumeReward.diagnostics());")
    (src/"PddrIsolationRun.java").write_text(entry,encoding="utf-8")
    for name in ("CenterHypervolumeReward","CenterUtilityChecks"):
        shutil.copy2(ROOT/f"src/algorithms/diagnostics/{name}.java",src)
    shutil.copy2(Path(__file__),src)
    execute(["javac","-encoding","UTF-8","--release","8","-cp",cp,"-d",str(classes),*map(str,src.glob("*.java"))],root/"compile.log")
    write_once(root/"class-hashes.json",class_hashes(classes));cp=f"{classes};{cp}"
    (root/"classpath.txt").write_text(cp,encoding="utf-8");return cp


def run(root,cp,stem,seed,arm):
    out=root/stem/str(seed)/arm;out.mkdir();inp=root/stem/"inputs";classic=arm=="NSGA"
    flags={"research.center.reward":"MEAN" if classic else arm,"research.personal.mode":"OLDEST","research.memory.audit":"true",
           "research.group.mode":"PAIR" if classic else "FULL_ROLE","research.reward.mode":"INDIVIDUAL" if classic else "GROUP",
           "research.batch.mode":"FORCE" if classic else "ROLE_CROWD"}
    cmd=["java","-Xms32m","-Xmx2g",*("-D"+k+"="+v for k,v in flags.items()),"-cp",cp,"research.dynamic.PddrIsolationRun",
         str(inp/f"{stem}.txt"),str(inp/"RECONSTRUCTED-setup.txt"),str(inp/"fatigue-input.txt"),str(out),"NSGA2_4V" if classic else "SHARE_JOB_ALIGNED",
         "LINEAR",str(out.parent/"ledger.csv"),"5100",str(seed),"100","5100"]
    write_once(out/"command.json",cmd);print("CENTER_UTILITY_CELL",stem,seed,arm,flush=True);execute(cmd,out/"run.log")
    receipt,=rows(out/"run-receipt.jsonl")
    assert receipt["attempted"]==receipt["successful"]==receipt["decoder"]["dynamic.evaluations"]==5100 and receipt["failed"]==0
    if not classic:assert all(receipt["search"][f"qgs.g{i}.updates"]==50 for i in (1,2,3,4))
    initials=[p/"initial-population.jsonl" for p in out.parent.iterdir() if p.is_dir() and (p/"initial-population.jsonl").exists()]
    assert all(p.read_bytes()==initials[0].read_bytes() for p in initials)
    write_once(out/"verified.json",{"successfulFE":5100,"failedFE":0,"sameInitials":True,"fullReturnQA":True})


def analyze(root):
    results=[];wins={"MEAN":0,"ZERO":0}
    for spec in read(root/"protocol.json")["instances"]:
        stem,norm=spec["stem"],spec["normalization"];metrics={}
        for seed in SEEDS:
            for arm in ARMS:
                path=root/stem/str(seed)/arm;front=rows(path/"anytime.jsonl")[-1]["front"]
                metrics[(seed,arm)]={"HV":float(hypervolume((np.asarray(front)-norm["lower"])/norm["scale"],(1.5,)*3)),
                                     "utility":rows(path/"center-utility.jsonl")[0]}
        effects={a:[100*(metrics[(s,"HV")]["HV"]/metrics[(s,a)]["HV"]-1) for s in SEEDS] for a in ("MEAN","ZERO","NSGA")}
        for arm in wins:wins[arm]+=sum(x>0 for x in effects[arm])
        passed=np.median(effects["MEAN"])>=.5 and np.median(effects["ZERO"])>0 and np.median(effects["NSGA"])>=-2
        results.append({"stem":stem,"effectsPct":effects,"supported":bool(passed),"cells":[{"seed":s,"arm":a,**v} for (s,a),v in metrics.items()]})
    result={"instances":results,"pairedWins":wins,"worthClosedLoop":all(r["supported"] for r in results) and all(v>=3 for v in wins.values()),
            "scope":"Short-stage CENTER reward intervention, not complete search, time superiority or cooperative causal credit."}
    write_once(root/"analysis.json",result);return result


def main():
    root=ROOT/"runs"/datetime.now().strftime("center-utility-probe-%Y%m%d-%H%M%S-%f");root.mkdir();print("CENTER_UTILITY_ROOT",root,flush=True)
    done=[];start=time.monotonic()
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs=read(BASIS/"protocol.json")["instances"]
            for stem in STEMS:
                shutil.copytree(BASIS/stem/"inputs",root/stem/"inputs")
                for seed in SEEDS:
                    folder=root/stem/str(seed);folder.mkdir();(folder/"ledger.csv").write_text("visit,group,round,factory,paid,restarts\n",encoding="utf-8")
            write_once(root/"protocol.json",{"instances":specs,"seeds":SEEDS,"arms":ARMS,"candidate":"HV","diagnosticFE":81600,"engineeringFE":500000,
                "basis":"Pre-existing-batch alignment audit found about1/3 meaningful CENTER updates sign-conflicting at both fixed references. This supports testing reward utility, not changing reference parameters or rescuing the failed global sweep.",
                "changed":"Only CENTER Q reward: signed retained-group box-normalized HV(next)-HV(before). Scalar duties keep original reward. Initial reference1.1 x max of the100 paid initial objectives, lower zero; no outside evaluation/reference/training data. ZERO is no CENTER reward learning; MEAN exact original group reward.",
                "preserved":"Original serial50-step blocks and generation-end-only guide updates; oldest ND personal guide and original Q state/alpha/gamma/exploration; FULL_ROLE/group survival, roles/families/sharing/proposals/local quota all unchanged. No sweep, fresh-memory rule, new selector or extra Q table.",
                "engineering":"Closed-form exact3D boxes, duplicate/permutation/empty/outside-box cases, equal-centroid unequal-HV fixture; then original MEAN full500k exact paid-sequence and frozen evidence replay before new data.",
                "gate":"Both instances median HV reward >=0.5% vs MEAN, >ZERO, >=-2% vs NSGA at5100. At least3/4 paired positive over each MEAN/ZERO. Failure stops this utility rule, no reward scaling/reference/tie/state scans.",
                "limits":"Actual reward computation cost included; short stages do not prove500k, same-time, fatigue specificity or novelty. If qualified, fresh full-budget protocol must include Li with the same generic reward enhancement."})
            cp=build(root);execute(["java","-cp",cp,"org.uma.jmetal.util.research.search.CenterUtilityChecks"],root/"utility-checks.log");engineering(root,cp)
            for i,stem in enumerate(STEMS):
                for j,seed in enumerate(SEEDS):
                    offset=(i+j)%len(ARMS)
                    for arm in ARMS[offset:]+ARMS[:offset]:run(root,cp,stem,seed,arm);done.append((stem,seed,arm))
            result=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulDiagnosticFE":len(done)*5100,"engineeringFE":500000,
        "failedEvaluationFE":0,"worthClosedLoop":result["worthClosedLoop"],"wallSeconds":time.monotonic()-start})
    print("CENTER_UTILITY_COMPLETE",[{"stem":r["stem"],"effects":r["effectsPct"],"supported":r["supported"]} for r in result["instances"]],flush=True)


if __name__=="__main__":main()
