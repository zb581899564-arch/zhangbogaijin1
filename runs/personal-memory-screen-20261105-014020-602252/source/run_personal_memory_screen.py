"""Prospective new-seed screen of the simplest ordinary control from the failed context-scoring probe."""
from datetime import datetime
from pathlib import Path
import shutil
import time

import numpy as np

from paired_survival_bench import FROZEN,prepare,run_cell,class_hashes
from pool_phase_build import OBS
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,hypervolume,igd_plus,nondominated,controller_lock
from run_paired_qgs_guidance import replace

BASIS=ROOT/"runs/group-survival-gate-20261104-234602-311536"
SOURCE=ROOT/"runs/survival-context-factorial-20261105-002440-955879"
STEMS=("20_8_5_1","100_2_3_1")
SEEDS=(10510003,10510033,10510063)
METHODS={"OLD_FULL":("OLDEST","SHARE_JOB_ALIGNED","FULL_ROLE",False),
         "LATEST_FULL":("LATEST","SHARE_JOB_ALIGNED","FULL_ROLE",False),
         "CURRENT_FULL":("CURRENT","SHARE_JOB_ALIGNED","FULL_ROLE",False),
         "RANDOM_FULL":("UNIFORM","SHARE_JOB_ALIGNED","FULL_ROLE",False),
         "LATEST_SYNC":("LATEST","SYNC_JOB_ALIGNED","FULL_ROLE",False),
         "LATEST_UNIFORM":("LATEST","SHARE_JOB_ALIGNED_UNIFORM","FULL_ROLE",False),
         "LI_MATCHED_DEEP":("OLDEST","BASELINE","PAIR",True),
         "LI_LATEST":("LATEST","BASELINE","PAIR",True),
         "NSGA":("OLDEST","NSGA2_4V","PAIR",False),
         "OLD_FORCE":("OLDEST","SHARE_JOB_ALIGNED","PAIR",False)}


def build(root):
    src,classes=root/"source",root/"classes";src.mkdir();classes.mkdir()
    cp=(BASIS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
    body=(FROZEN/"source/src/java/search/Particle.java").read_text(encoding="utf-8")
    body=replace(body,"return ParetoTools.copy(history.get(ParetoTools.order(history, direction).get(0)));",
                 "return PersonalMemoryPolicy.choose(current, history, direction);")
    (src/"Particle.java").write_text(body,encoding="utf-8")
    for name in ("PersonalMemoryPolicy","RuntimeClassIdentity"):
        shutil.copy2(ROOT/f"src/algorithms/diagnostics/{name}.java",src)
    entry=(BASIS/"source/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry=replace(entry,"digest = audit ? new PddrPaidDigest() : null;",
                  "digest = audit || Boolean.getBoolean(\"research.memory.audit\") ? new PddrPaidDigest() : null;")
    entry=replace(entry,'"paidSHA256", audit ? obs.digest.finish() : null);','"paidSHA256", obs.digest == null ? null : obs.digest.finish());')
    entry=replace(entry,"        obs.write(out);","        obs.write(out);\n"
                  "        append(out.resolve(\"memory.jsonl\"), org.uma.jmetal.util.research.search.PersonalMemoryPolicy.diagnostics());\n"
                  "        append(out.resolve(\"loaded-classes.jsonl\"), org.uma.jmetal.util.research.search.RuntimeClassIdentity.capture());")
    (src/"PddrIsolationRun.java").write_text(entry,encoding="utf-8")
    for name in ("run_personal_memory_screen.py","paired_survival_bench.py"):
        shutil.copy2(Path(__file__).with_name(name),src)
    execute(["javac","-encoding","UTF-8","--release","8","-cp",cp,"-d",str(classes),*map(str,src.glob("*.java"))],root/"compile.log")
    write_once(root/"class-hashes.json",class_hashes(classes));cp=f"{classes};{cp}"
    (root/"classpath.txt").write_text(cp,encoding="utf-8");return cp


def run(root,cp,spec,audit=False):
    spec=dict(spec);arm=spec["arm"];personal,mode,group,li=METHODS[arm]
    spec.update(mode=mode,liLegacy=li,commonInitials=li)
    force=arm in ("LI_MATCHED_DEEP","LI_LATEST","NSGA","OLD_FORCE")
    return run_cell(root,cp,spec,{"research.personal.mode":personal,"research.group.mode":group,
             "research.reward.mode":"GROUP" if group=="FULL_ROLE" else "INDIVIDUAL",
             "research.batch.mode":"FORCE" if force else "ROLE_CROWD","research.memory.audit":str(audit).lower()})


def engineering(root,cp):
    work=root/"engineering";work.mkdir();stem="20_8_5_1";seed=9940003
    shutil.copytree(SOURCE/stem/"inputs",work/stem/"inputs");folder=work/stem/str(seed);folder.mkdir()
    shutil.copy2(SOURCE/stem/str(seed)/"ledger.csv",folder/"ledger.csv")
    out=run(work,cp,{"stem":stem,"seed":seed,"arm":"OLD_FULL"},True)
    original=SOURCE/stem/str(seed)/"SHARE_FULL";digest_source=OBS/stem/str(seed)/"SHARE_FULL_OFF"
    for name in ("solutions.jsonl","initial-population.jsonl","local-ledger.csv"):
        assert (out/name).read_bytes()==(original/name).read_bytes()
    assert [r["front"] for r in rows(out/"anytime.jsonl")]==[r["front"] for r in rows(original/"anytime.jsonl")]
    assert rows(out/"run-receipt.jsonl")[0]["paidSHA256"]==rows(digest_source/"run-receipt.jsonl")[0]["paidSHA256"]
    assert rows(out/"run-receipt.jsonl")[0]["search"]==rows(original/"run-receipt.jsonl")[0]["search"]
    write_once(root/"engineering-gate.json",{"status":"PASS","successfulFE":500000,"oldestNDFastPathPaidSequenceAndFrozenEvidenceIdentical":True})


def analyze(root):
    results=[];cells=[]
    for spec in read(root/"protocol.json")["instances"]:
        stem,norm=spec["stem"],spec["normalization"];normed=lambda x:(np.asarray(x)-norm["lower"])/norm["scale"]
        paths={(s,a):root/stem/str(s)/a for s in SEEDS for a in METHODS}
        fronts={k:rows(p/"anytime.jsonl")[-1]["front"] for k,p in paths.items()}
        ref=nondominated(np.vstack([normed(f) for f in fronts.values()]));metrics={}
        for (seed,arm),p in paths.items():
            timer=next(x for x in rows(p/"time.jsonl") if abs(x["checkpoint"]-spec["time_seconds"])<1e-9)
            m={"HV":{str(r):float(hypervolume(normed(fronts[(seed,arm)]),(r,)*3)) for r in (1.25,1.5,2)},
               "IGDplus":float(igd_plus(normed(fronts[(seed,arm)]),ref)),"timeHV":float(hypervolume(normed(timer["front"]),(1.5,)*3)),
               "memory":rows(p/"memory.jsonl")[0]}
            metrics[(seed,arm)]=m;cells.append({"stem":stem,"seed":seed,"arm":arm,**m})
        effects={a:[100*(metrics[(s,"LATEST_FULL")]["HV"]["1.5"]/metrics[(s,a)]["HV"]["1.5"]-1) for s in SEEDS] for a in METHODS if a!="LATEST_FULL"}
        median={a:float(np.median(v)) for a,v in effects.items()}
        efficacy=median["OLD_FULL"]>=1 and sum(x>0 for x in effects["OLD_FULL"])>=2 and median["NSGA"]>=-1 \
            and all(median[a]>=0 for a in ("CURRENT_FULL","RANDOM_FULL","LI_LATEST")) and median["LI_MATCHED_DEEP"]>0 and median["OLD_FORCE"]>0
        robust=all(np.median([metrics[(s,"LATEST_FULL")]["HV"][str(r)]-metrics[(s,"OLD_FULL")]["HV"][str(r)] for s in SEEDS])>0 for r in (1.25,2))
        results.append({"stem":stem,"effectsPct":effects,"medianEffectsPct":median,"efficacyPrimaryPass":bool(efficacy and robust),
                        "fourRoleMedianBenefit":median["LATEST_UNIFORM"],"compositionMedianBenefit":median["LATEST_SYNC"]})
    coop=all(r["fourRoleMedianBenefit"]>=1 for r in results) and max(r["compositionMedianBenefit"] for r in results)>=.2 \
        and min(r["compositionMedianBenefit"] for r in results)>=-.5
    result={"instances":results,"cells":cells,"efficacyPrimaryPass":all(r["efficacyPrimaryPass"] for r in results),
            "conditionalCooperationScreenPass":bool(coop),"decision":"REVIEW_AUXILIARIES_BEFORE_CONFIRMATION" if all(r["efficacyPrimaryPass"] for r in results) else "STOP_LATEST_MEMORY_SCREEN"}
    write_once(root/"comparison.json",result);return result


def main():
    root=ROOT/"runs"/datetime.now().strftime("personal-memory-screen-%Y%m%d-%H%M%S-%f")
    root.mkdir();print("PERSONAL_MEMORY_SCREEN_ROOT",root,flush=True);done=[];start=time.monotonic()
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs,order=prepare(root,STEMS,SEEDS,tuple(METHODS))
            write_once(root/"protocol.json",{"instances":specs,"seeds":SEEDS,"methods":METHODS,"order":order,"candidate":"LATEST_FULL",
                "basis":"CONTEXT primary failed paired probe; its pre-fixed ordinary CURRENT/LATEST controls improved vs oldest on all four discovery source cells. New hypothesis and new seeds here; no previous gate relabeled.",
                "changed":"CENTER personalBest selects latest surviving ND insertion instead of oldest. No history reset, extra learning, new proposal, role/family/pool or local quota changes. Other directions keep their original best-objective rule.",
                "commonEngine":"OLDEST selects first ND insertion in O(1), mathematically identical to original stable PDDR sort over its own ND history. All methods use this same policy engine; original full500k paid-sequence equivalence required before performance.",
                "controls":"CURRENT and random ND memory; specialization-uniform with original Q table; no composition; original FORCE shared; original Li v2 with matched deep search; Li with the same generic latest-memory enhancement; matched NSGA-II. Li flags explicitly v2 and FORCE, not accidentally full-survival.",
                "efficacyGate":"Each instance median >=1% vs OLD_FULL with >=2/3 paired wins; median >=-1% vs NSGA; nonnegative vs CURRENT/RANDOM/Li_latest; positive vs original Li and original FORCE shared. Positive old-full direction at refs1.25/2. Exact CURRENT equivalence means no extra memory-value claim.",
                "cooperativeGate":"Separate from efficacy: four-duty vs uniform median >=1% on both; sharing vs SYNC median >=0.2% on at least one and >=-0.5% on the other. No claim universal sharing benefit. Failure here prevents a cooperative novelty claim even if baseline memory improves.",
                "budget":"60 x500000 successfulFE =30000000 searchFE, plus500000 engineeringFE. Failure stops this parameter-free policy; no tie/age-probability or seed scan.",
                "timeScope":"All generation/selection cost in search clock, no full trace/digest in performance. Existing common time cuts diagnostic; actual TIME_LIMIT independent runs still required.",
                "scope":"Three-seed development screen. Original baseline/author materials/default mainline unchanged; not faithful-author score reproduction, novelty proof or independent final confirmation."})
            cp=build(root);engineering(root,cp)
            for spec in order:run(root,cp,spec);done.append(spec)
            result=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulSearchFE":len(done)*500000,"engineeringFE":500000,
        "efficacyPrimaryPass":result["efficacyPrimaryPass"],"conditionalCooperationScreenPass":result["conditionalCooperationScreenPass"],"wallSeconds":time.monotonic()-start})
    print("PERSONAL_MEMORY_SCREEN_COMPLETE",[{k:v for k,v in r.items() if k!="effectsPct"} for r in result["instances"]],flush=True)


if __name__=="__main__":main()
