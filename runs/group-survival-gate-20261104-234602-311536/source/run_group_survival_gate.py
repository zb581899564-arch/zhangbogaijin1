"""Test set-level global survival separately from CENTER group-reward normalization and duplicates."""
from datetime import datetime
from pathlib import Path
import shutil
import time

import numpy as np

from paired_survival_bench import prepare,run_cell,class_hashes,ANCHOR
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,hypervolume,igd_plus,nondominated,controller_lock
from run_paired_qgs_guidance import replace

BASIS=ROOT/"runs/batch-survival-study-20261104-222516-378030"
STEMS=("20_8_5_1","100_2_3_1")
SEEDS=(9580003,)
METHODS={"FORCE":("PAIR","INDIVIDUAL","FORCE"),"PAIR_OLD":("PAIR","INDIVIDUAL","ROLE_CROWD"),
         "PAIR_GROUP":("PAIR","GROUP","ROLE_CROWD"),"FULL_ROLE":("FULL_ROLE","GROUP","ROLE_CROWD"),
         "FULL_DUP":("FULL_DUP","GROUP","ROLE_CROWD"),"FULL_ALL":("FULL_ALL","GROUP","ROLE_CROWD"),
         "NSGA":("PAIR","INDIVIDUAL","FORCE"),"LI_MATCHED_DEEP":("PAIR","INDIVIDUAL","FORCE")}


def build(root):
    src,classes=root/"source",root/"classes";src.mkdir();classes.mkdir()
    cp=(BASIS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
    body=(BASIS/"source/CanonicalHmopso.java").read_text(encoding="utf-8")
    body=replace(body,"return GlobalBatchPolicy.select(group, result, preference);","return GlobalGroupPolicy.select(group, result, preference);")
    body=replace(body,"""            double reward = 0;
            for (int i = 0; i < current.size(); i++) reward += preference.reward(current.get(i).current, next.get(i).current);
            reward /= current.size();""","            double reward = GroupReward.compute(current, next, preference);")
    (src/"CanonicalHmopso.java").write_text(body,encoding="utf-8")
    for name in ("GroupReward","GlobalGroupPolicy","GroupSurvivalChecks"):
        shutil.copy2(ROOT/f"src/algorithms/diagnostics/{name}.java",src)
    entry=(BASIS/"source/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry=replace(entry,"        obs.write(out);","        obs.write(out);\n"
                  "        append(out.resolve(\"group.jsonl\"), org.uma.jmetal.util.research.search.GlobalGroupPolicy.diagnostics());")
    (src/"PddrIsolationRun.java").write_text(entry,encoding="utf-8")
    shutil.copy2(Path(__file__),src);shutil.copy2(Path(__file__).with_name("paired_survival_bench.py"),src)
    execute(["javac","-encoding","UTF-8","--release","8","-cp",cp,"-d",str(classes),*map(str,src.glob("*.java"))],root/"compile.log")
    write_once(root/"class-hashes.json",class_hashes(classes));cp=f"{classes};{cp}"
    (root/"classpath.txt").write_text(cp,encoding="utf-8");return cp


def run(root,cp,spec):
    group,reward,batch=METHODS[spec["arm"]]
    return run_cell(root,cp,spec,{"research.group.mode":group,"research.reward.mode":reward,"research.batch.mode":batch})


def engineering(root,cp):
    from run_dynamic_deep_roles import BRIDGE
    execute(["java","-Dresearch.group.mode=FULL_ROLE","-Dresearch.reward.mode=GROUP","-cp",cp,
             "org.uma.jmetal.util.research.search.GroupSurvivalChecks",str(BRIDGE/"inputs"),str(BRIDGE/"inputs/RECONSTRUCTED-setup.txt")],root/"checks.log")
    work=root/"engineering";work.mkdir()
    controls=[("20_2_3_1",8111009,"FORCE",ANCHOR/"SPECIAL-LINEAR",BRIDGE/"inputs"),
              ("20_8_5_1",9280009,"PAIR_OLD",BASIS/"20_8_5_1/9280009/ROLE_CROWD",BASIS/"20_8_5_1/inputs")]
    for stem,seed,arm,prior,inputs in controls:
        shutil.copytree(inputs,work/stem/"inputs");folder=work/stem/str(seed);folder.mkdir()
        shutil.copy2((ANCHOR/"ledger.csv") if seed==8111009 else prior.parent/"ledger.csv",folder/"ledger.csv")
        p=run(work,cp,{"stem":stem,"seed":seed,"arm":arm})
        assert (p/"solutions.jsonl").read_bytes()==(prior/"solutions.jsonl").read_bytes()
        assert [x["front"] for x in rows(p/"anytime.jsonl")]==[x["front"] for x in rows(prior/"anytime.jsonl")]
    write_once(root/"engineering-gate.json",{"status":"PASS","FE":1000000,"oldControlsUnchanged":True})


def analyze(root):
    results=[]
    for spec in read(root/"protocol.json")["instances"]:
        stem,norm=spec["stem"],spec["normalization"];normed=lambda x:(np.asarray(x)-norm["lower"])/norm["scale"]
        fronts={a:rows(root/stem/str(SEEDS[0])/a/"anytime.jsonl")[-1]["front"] for a in METHODS}
        empirical=nondominated(np.vstack([normed(x) for x in fronts.values()]));metrics={}
        for a,f in fronts.items():
            path=root/stem/str(SEEDS[0])/a;t=next(x for x in rows(path/"time.jsonl") if abs(x["checkpoint"]-spec["time_seconds"])<1e-9)
            metrics[a]={"HV":{str(r):float(hypervolume(normed(f),(r,)*3)) for r in (1.25,1.5,2)},
                        "timeHV":float(hypervolume(normed(t["front"]),(1.5,)*3)),"IGDplus":float(igd_plus(normed(f),empirical)),
                        "group":rows(path/"group.jsonl")[0]}
        effects={a:100*(metrics["FULL_ROLE"]["HV"]["1.5"]/m["HV"]["1.5"]-1) for a,m in metrics.items() if a!="FULL_ROLE"}
        passed=effects["PAIR_OLD"]>=1 and all(effects[a]>0 for a in ("PAIR_GROUP","FULL_DUP","FULL_ALL")) and effects["NSGA"]>=-1
        results.append({"stem":stem,"metrics":metrics,"fullRoleEffectsPct":effects,"eligible":passed})
    write_once(root/"comparison.json",results);return results


def main():
    root=ROOT/"runs"/datetime.now().strftime("group-survival-gate-%Y%m%d-%H%M%S-%f")
    root.mkdir();print("GROUP_ROOT",root,flush=True);start=time.monotonic();done=[]
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs,order=prepare(root,STEMS,SEEDS,tuple(METHODS))
            write_once(root/"protocol.json",{"candidate":"FULL_ROLE","instances":specs,"seeds":SEEDS,"methods":METHODS,"order":order,
                "mechanism":"Select n survivors from the paid2n batch, preserving original per-family counts. "
                            "Boundary groups prioritize their own objective, CENTER rank+crowding. Prefer objective-unique "
                            "points within each category, then fill duplicates only if necessary. Individual lineage quotas lifted.",
                "reward":"CENTER reward becomes relative change of group mean objectives to avoid arbitrary old/new "
                         "individual pairing. PAIR_GROUP isolates this from selection; PAIR_OLD reproduces the original reward.",
                "controls":"FULL_DUP removes duplicate avoidance; FULL_ALL uses multiobjective selection in every group. "
                           "FORCE, NSGA and Li matched-depth keep their original per-individual reward and selection.",
                "gate":"FULL_ROLE >=1% vs PAIR_OLD; positive vs PAIR_GROUP/FULL_DUP/FULL_ALL; >=-1% vs NSGA on both "
                       "development instances. A primary failure ends this rule without changing crowding or duplication thresholds.",
                "actualFEPerCell":500000,"totalSearchFE":len(order)*500000,"engineeringFE":1000000,
                "scope":"Development attribution, not final independent efficacy or novelty proof."})
            cp=build(root);engineering(root,cp)
            for spec in order:run(root,cp,spec);done.append(spec)
            result=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulFE":len(done)*500000,"engineeringFE":1000000,
                                   "worthFreshScreen":all(x["eligible"] for x in result),"wallSeconds":time.monotonic()-start})
    print("GROUP_COMPLETE",[{"stem":x["stem"],"effects":x["fullRoleEffectsPct"],"eligible":x["eligible"]} for x in result],flush=True)


if __name__=="__main__":main()
