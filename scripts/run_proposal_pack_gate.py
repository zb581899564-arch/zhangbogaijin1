"""Same per-role FE: two complementary proposals vs two homogeneous proposals and one-proposal controls."""
from datetime import datetime
from pathlib import Path
import shutil
import time

import numpy as np

from run_long_budget_bridge import ROOT,read,rows,write_once,execute,hypervolume,controller_lock
from run_paired_qgs_guidance import replace
from paired_survival_bench import prepare,run_cell,class_hashes,ANCHOR

BASIS=ROOT/"runs/batch-survival-study-20261104-222516-378030"
STEMS=("20_8_5_1","100_2_3_1")
SEEDS=(9430003,)
ARMS=("FORCE","BASE","JA_PAIR","CG_PAIR","MIX_PAIR","CG_SINGLE","NSGA","LI_MATCHED_DEEP")


def build(root):
    src,classes=root/"source",root/"classes";src.mkdir();classes.mkdir()
    cp=(BASIS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
    body=(BASIS/"source/CanonicalHmopso.java").read_text(encoding="utf-8")
    body=replace(body,"        this.chapter = chapter; this.config = Objects.requireNonNull(config, \"config\").resolved(chapter);",
        "        this.chapter = chapter; this.config = Objects.requireNonNull(config, \"config\").resolved(chapter);\n"
        "        GlobalProposalPack.initialize(instance, this.config, ((BudgetedProblem<?>) problem)::checkpoint);")
    body=replace(body,"step < config.qIterations","step < GlobalProposalPack.steps(direction, config.qIterations)")
    original="""                child = updatePolicy == null ? operators.update(particle.current, personal, leader)
                        : updatePolicy.propose(particle.current, personal, leader, preference);"""
    body=replace(body,original,"""                child = GlobalProposalPack.first(particle.current, personal, leader, preference,
                        () -> updatePolicy == null ? operators.update(particle.current, personal, leader)
                            : updatePolicy.propose(particle.current, personal, leader, preference));""")
    body=replace(body,"            state.evaluate(child, \"global\", direction);",
        "            state.evaluate(child, \"global\", direction);\n"
        "            PermutationSolution<Integer> second = composed ? null : GlobalProposalPack.second(particle.current, personal, leader, preference);\n"
        "            if (second != null) state.evaluate(second, \"global\", direction);\n"
        "            child = GlobalProposalPack.choose(child, second);")
    (src/"CanonicalHmopso.java").write_text(body,encoding="utf-8")
    batch=(BASIS/"source/GlobalBatchPolicy.java").read_text(encoding="utf-8").replace('count("paid." + role.name())','count("pairedSurvivorComparisons." + role.name())')
    (src/"GlobalBatchPolicy.java").write_text(batch,encoding="utf-8")
    shutil.copy2(ROOT/"src/algorithms/diagnostics/GlobalProposalPack.java",src)
    entry=(BASIS/"source/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry=replace(entry,"        obs.write(out);","        obs.write(out);\n"
                  "        append(out.resolve(\"pack.jsonl\"), org.uma.jmetal.util.research.search.GlobalProposalPack.diagnostics());")
    (src/"PddrIsolationRun.java").write_text(entry,encoding="utf-8")
    shutil.copy2(Path(__file__),src)
    execute(["javac","-encoding","UTF-8","--release","8","-cp",cp,"-d",str(classes),*map(str,src.glob("*.java"))],root/"compile.log")
    write_once(root/"class-hashes.json",class_hashes(classes))
    cp=f"{classes};{cp}";(root/"classpath.txt").write_text(cp,encoding="utf-8")
    return cp


def run(root,cp,spec):
    # Reuse the common budget/initialization verifier; inject only this study's two independent mode flags.
    stem,seed,arm=(spec[k] for k in ("stem","seed","arm"))
    normal="FORCE" if arm in ("FORCE","NSGA","LI_MATCHED_DEEP") else "ROLE_CROWD"
    pack=arm if arm in ("JA_PAIR","CG_PAIR","MIX_PAIR","CG_SINGLE") else "BASE"
    return run_cell(root,cp,spec,{"research.pack.mode":pack,"research.batch.mode":normal})


def engineering(root,cp):
    from run_dynamic_deep_roles import BRIDGE
    work=root/"engineering";work.mkdir();shutil.copytree(BRIDGE/"inputs",work/"20_2_3_1/inputs")
    folder=work/"20_2_3_1/8111009";folder.mkdir();shutil.copy2(ANCHOR/"ledger.csv",folder/"ledger.csv")
    p=run(work,cp,{"stem":"20_2_3_1","seed":8111009,"arm":"FORCE"})
    assert (p/"solutions.jsonl").read_bytes()==(ANCHOR/"SPECIAL-LINEAR/solutions.jsonl").read_bytes()
    write_once(root/"engineering-gate.json",{"status":"PASS","successfulFE":500000,"unchangedFORCEFinalGenomesMatch":True})


def analyze(root,filename="comparison.json",li_prefix=None):
    reports=[]
    for spec in read(root/"protocol.json")["instances"]:
        stem,norm=spec["stem"],spec["normalization"];normal=lambda x:(np.asarray(x)-norm["lower"])/norm["scale"]
        metrics={}
        for arm in ARMS:
            path=(li_prefix if li_prefix is not None and arm=="LI_MATCHED_DEEP" else root)/stem/str(SEEDS[0])/arm
            end=rows(path/"anytime.jsonl")[-1]
            timed=next(r for r in rows(path/"time.jsonl") if abs(r["checkpoint"]-spec["time_seconds"])<1e-9)
            metrics[arm]={"HV":{str(r):float(hypervolume(normal(end["front"]),(r,)*3)) for r in (1.25,1.5,2)},
                          "timeHV":float(hypervolume(normal(timed["front"]),(1.5,)*3)),"pack":rows(path/"pack.jsonl")[0]}
        effects={a:100*(metrics["MIX_PAIR"]["HV"]["1.5"]/m["HV"]["1.5"]-1) for a,m in metrics.items() if a!="MIX_PAIR"}
        passed=effects["BASE"]>=1 and effects["NSGA"]>=-1 and all(effects[a]>0 for a in ("JA_PAIR","CG_PAIR","CG_SINGLE"))
        reports.append({"stem":stem,"metrics":metrics,"mixEffectsPct":effects,"eligible":passed})
    write_once(root/filename,reports);return reports


def main():
    root=ROOT/"runs"/datetime.now().strftime("proposal-pack-gate-%Y%m%d-%H%M%S-%f")
    root.mkdir();print("PACK_ROOT",root,flush=True);start=time.monotonic();done=[]
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs,order=prepare(root,STEMS,SEEDS,ARMS)
            write_once(root/"protocol.json",{"candidate":"MIX_PAIR","instances":specs,"seeds":SEEDS,"arms":ARMS,"order":order,
                "evidence":"M-only fixed CLASSIC passed one holdout instance but failed the other; no universal generator "
                           "replacement is supported. Test a paid complementary-pair hedge instead, with two homogeneous-pair controls.",
                "mechanism":"M generates two candidates from the same parent/pbest/Q-selected guide, pays both, chooses lower "
                            "Cmax (tie keeps first), then uses unchanged role-greedy batch survival. Halve M QGS updates50->25 "
                            "so M FE, all global FE, local FE and physical ledger remain exactly matched. Other roles unchanged.",
                "controls":"JA_PAIR and CG_PAIR have identical two-candidate quota; CG_SINGLE tests ordinary M-only fixed "
                           "classic replacement. BASE is improved ROLE_CROWD/JOB_ALIGNED, FORCE original shared; full NSGA and Li-matched retained.",
                "gate":"On both development instances MIX >=1% vs BASE, positive vs both homogeneous pairs and CG_SINGLE, "
                       "and >=-1% vs NSGA at500k. No rescue by changing candidate counts, thresholds or seeds.",
                "actualFEPerCell":500000,"totalSearchFE":8000000,"engineeringFE":500000,
                "scope":"One-seed development gate only; no independent performance or novelty claim."})
            cp=build(root);engineering(root,cp)
            for job in order:run(root,cp,job);done.append(job)
            result=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulFE":8000000,"engineeringFE":500000,
                                   "worthFreshScreen":all(x["eligible"] for x in result),"wallSeconds":time.monotonic()-start})
    print("PACK_COMPLETE",[{"stem":x["stem"],"effects":x["mixEffectsPct"],"eligible":x["eligible"]} for x in result],flush=True)


if __name__=="__main__":main()
