"""Paired nondomination/crowding for CENTER, retaining each particle lineage and all four roles."""
from datetime import datetime
from pathlib import Path
import shutil
import time

import numpy as np

from paired_survival_bench import prepare, run_cell, class_hashes, ANCHOR
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, hypervolume, igd_plus, nondominated, controller_lock
from run_role_retention_screen import build as prior_build
from run_paired_qgs_guidance import replace

INSTANCES = ("20_8_5_1", "100_2_3_1")
SEEDS = (9280009, 9280039, 9280071)
ARMS = ("FORCE", "ROLE_GREEDY", "ROLE_RANK", "ROLE_CROWD", "ALL_CROWD", "NSGA", "LI_MATCHED_DEEP")


def build(root):
    cp = prior_build(root); src, classes = root / "source", root / "classes"
    body = (ROOT / "runs/dynamic-deep-local-20261103-184901-271850/source/CanonicalHmopso.java").read_text(encoding="utf-8")
    body = replace(body, "        if (updatePolicy != null) updatePolicy.endBatch(preference);\n        return result;",
                   "        if (updatePolicy != null) updatePolicy.endBatch(preference);\n"
                   "        return GlobalBatchPolicy.select(group, result, preference);")
    (src / "CanonicalHmopso.java").write_text(body, encoding="utf-8")
    for name in ("GlobalBatchPolicy", "GlobalBatchChecks"):
        shutil.copy2(ROOT / f"src/algorithms/diagnostics/{name}.java", src)
    entry = (src / "PddrIsolationRun.java").read_text(encoding="utf-8")
    entry = replace(entry, "        obs.write(out);", "        obs.write(out);\n"
                    "        append(out.resolve(\"batch.jsonl\"), org.uma.jmetal.util.research.search.GlobalBatchPolicy.diagnostics());")
    entry = replace(entry, "4.0/12, 6.0/12", "4.0/12, 5.0/12, 6.0/12")
    (src / "PddrIsolationRun.java").write_text(entry, encoding="utf-8")
    shutil.copy2(Path(__file__), src); shutil.copy2(Path(__file__).with_name("paired_survival_bench.py"), src)
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", cp, "-d", str(classes),
             str(src / "GlobalBatchPolicy.java"), str(src / "GlobalBatchChecks.java"),
             str(src / "CanonicalHmopso.java"), str(src / "PddrIsolationRun.java")], root / "batch-compile.log")
    write_once(root / "batch-class-hashes.json", class_hashes(classes))
    return cp


def engineering(root, cp):
    from run_dynamic_deep_roles import BRIDGE
    execute(["java", "-cp", cp, "org.uma.jmetal.util.research.search.GlobalBatchChecks", str(BRIDGE / "inputs"),
             str(BRIDGE / "inputs/RECONSTRUCTED-setup.txt")], root / "batch-checks.log")
    work = root / "engineering"; work.mkdir()
    shutil.copytree(BRIDGE / "inputs", work / "20_2_3_1/inputs")
    folder = work / "20_2_3_1/8111009"; folder.mkdir()
    shutil.copy2(ANCHOR / "ledger.csv", folder / "ledger.csv")
    for arm, prior in (("FORCE", ANCHOR / "SPECIAL-LINEAR"),
                       ("ROLE_GREEDY", ROOT / "runs/global-retention-gate-20261104-212142-925160/ROLE_GREEDY")):
        path = run_cell(work, cp, {"stem":"20_2_3_1","seed":8111009,"arm":arm})
        assert (path / "solutions.jsonl").read_bytes() == (prior / "solutions.jsonl").read_bytes()
        assert [r["front"] for r in rows(path / "anytime.jsonl")] == [r["front"] for r in rows(prior / "anytime.jsonl")]
    write_once(root / "engineering-gate.json", {"status":"PASS","successfulFE":1000000,"baselineAndGreedyFEcurvesAndFinalGenomesUnchanged":True})


def analyze(root):
    p = read(root / "protocol.json"); cells=[]; summaries=[]
    for spec in p["instances"]:
        stem,norm,cut=spec["stem"],spec["normalization"],spec["time_seconds"]
        normed=lambda x:(np.asarray(x)-norm["lower"])/norm["scale"]
        fronts={(s,a):rows(root/stem/str(s)/a/"anytime.jsonl")[-1]["front"] for s in SEEDS for a in ARMS}
        ref=nondominated(np.vstack([normed(x) for x in fronts.values()])); metrics={}
        for s in SEEDS:
            for a in ARMS:
                path=root/stem/str(s)/a; timer=next(r for r in rows(path/"time.jsonl") if abs(r["checkpoint"]-cut)<1e-9)
                m={"HV":{str(r):float(hypervolume(normed(fronts[(s,a)]),(r,)*3)) for r in (1.25,1.5,2)},
                   "timeHV":float(hypervolume(normed(timer["front"]),(1.5,)*3)),"timeFE":timer["fe"],
                   "IGDplus":float(igd_plus(normed(fronts[(s,a)]),ref)),"batch":rows(path/"batch.jsonl")[0]}
                metrics[(s,a)]=m; cells.append({"stem":stem,"seed":s,"arm":a,**m})
        effects={a:[100*(metrics[(s,"ROLE_CROWD")]["HV"]["1.5"]/metrics[(s,a)]["HV"]["1.5"]-1) for s in SEEDS] for a in ARMS if a!="ROLE_CROWD"}
        primary=np.median(effects["FORCE"])>=1 and sum(x>0 for x in effects["FORCE"])>=2 \
            and np.median(effects["NSGA"])>=-1 and all(np.median(effects[a])>0 for a in ("ROLE_GREEDY","ROLE_RANK","ALL_CROWD"))
        summaries.append({"stem":stem,"candidateEffectsPct":effects,"medianEffectsPct":{a:float(np.median(x)) for a,x in effects.items()},"primaryPass":bool(primary)})
    out={"instances":summaries,"cells":cells,"primaryGate":"CHECK_AUXILIARIES" if all(x["primaryPass"] for x in summaries) else "STOP_ROLE_CROWD_SCREEN"}
    write_once(root/"comparison.json",out); return out


def main():
    root=ROOT/"runs"/datetime.now().strftime("batch-survival-study-%Y%m%d-%H%M%S-%f")
    root.mkdir(); print("BATCH_ROOT",root,flush=True); start=time.monotonic(); done=[]
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs,order=prepare(root,INSTANCES,SEEDS,ARMS)
            write_once(root/"protocol.json",{"candidate":"ROLE_CROWD","instances":specs,"seeds":SEEDS,"arms":ARMS,"order":order,
                "evidence":"Prior ROLE_GREEDY improved all six new-seed cells vs FORCE and Li-matched, but missed NSGA "
                           "by ~3% in the many-stage instance. Explicit CENTER neutral-solution diversity is the next separate hypothesis.",
                "mechanism":"Generate unchanged proposals for the whole QGS batch; preserve one survivor per original "
                            "parent/lineage/family. Boundaries retain their objective-greedy comparison; CENTER uses "
                            "nondomination rank then unique-objective normalized crowding in parents+children. Exact ties keep parent.",
                "controls":"ROLE_RANK removes crowding; ALL_CROWD removes objective-specific boundary retention. "
                           "FORCE and ROLE_GREEDY must reproduce old fixed-FE controls in engineering. No Q changes, new "
                           "operators, probability tuning or quota changes. All successful children enter the paid result archive.",
                "actualFEPerCell":500000,"totalSearchFE":len(order)*500000,"engineeringFE":1000000,
                "gate":"Each instance candidate median >=1% vs FORCE with 2/3 positive seeds; positive medians vs ROLE_GREEDY, "
                       "ROLE_RANK and ALL_CROWD; no worse than -1% vs NSGA. If primary fails do not change seeds or thresholds.",
                "time":"Primary4s/5s cuts explicitly captured, all common costs included; reference1.25/1.5/2 and IGD+ are safeguards.",
                "LiIdentity":"LI_MATCHED_DEEP is v2-reconstructed QGS with a matched deep-LS enhancement, not the published author run."})
            cp=build(root); engineering(root,cp)
            for spec in order: run_cell(root,cp,spec); done.append(spec)
            result=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)}); raise
    write_once(root/"status.json",{"status":"COMPLETE","completed":len(done),"successfulSearchFE":len(done)*500000,
                                  "engineeringFE":1000000,"wallSeconds":time.monotonic()-start,"primaryGate":result["primaryGate"]})
    print("BATCH_COMPLETE",result["instances"],flush=True)


if __name__=="__main__": main()
