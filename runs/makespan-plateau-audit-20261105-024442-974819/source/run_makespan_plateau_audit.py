"""Read-only makespan-role audit of physical improvements hidden by max aggregation."""
from datetime import datetime
from pathlib import Path
import shutil

from paired_survival_bench import class_hashes,run_cell
from qgs_epoch_build import BASIS
from run_acceptance_plateau_audit import SOURCE,OBS,STEMS,SEED
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from run_paired_qgs_guidance import replace


def build(root):
    src,classes=root/"source",root/"classes";src.mkdir();classes.mkdir()
    cp=(BASIS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
    kernel=(ROOT/"src/algorithms/diagnostics/LocalPddrKernel.java").read_text(encoding="utf-8")
    kernel=replace(kernel,"        if (direction != Direction.CENTER || MODE == Mode.LEGACY)",
        "        if (direction == Direction.MAKESPAN) MakespanPlateauTrace.record(candidate,incumbent);\n"
        "        if (direction != Direction.CENTER || MODE == Mode.LEGACY)")
    (src/"LocalPddrKernel.java").write_text(kernel,encoding="utf-8")
    entry=(BASIS/"source/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry=replace(entry,"        obs.write(out);","        obs.write(out);\n"
        "        append(out.resolve(\"makespan-plateau.jsonl\"), org.uma.jmetal.util.research.search.MakespanPlateauTrace.diagnostics());")
    (src/"PddrIsolationRun.java").write_text(entry,encoding="utf-8")
    shutil.copy2(ROOT/"src/algorithms/diagnostics/MakespanPlateauTrace.java",src);shutil.copy2(Path(__file__),src)
    execute(["javac","-encoding","UTF-8","--release","8","-cp",cp,"-d",str(classes),*map(str,src.glob("*.java"))],root/"compile.log")
    write_once(root/"class-hashes.json",class_hashes(classes));cp=f"{classes};{cp}"
    (root/"classpath.txt").write_text(cp,encoding="utf-8");return cp


def run(root,cp,stem):
    out=run_cell(root,cp,{"stem":stem,"seed":SEED,"arm":"TRACE"},{"research.personal.mode":"OLDEST",
        "research.memory.audit":"true","research.group.mode":"FULL_ROLE","research.reward.mode":"GROUP","research.batch.mode":"ROLE_CROWD"})
    original=SOURCE/stem/str(SEED)/"SHARE_FULL"
    for name in ("solutions.jsonl","initial-population.jsonl","local-ledger.csv"):
        assert (out/name).read_bytes()==(original/name).read_bytes(),name
    assert [r["front"] for r in rows(out/"anytime.jsonl")]==[r["front"] for r in rows(original/"anytime.jsonl")]
    assert rows(out/"run-receipt.jsonl")[0]["paidSHA256"]==rows(OBS/stem/str(SEED)/"SHARE_FULL_OFF/run-receipt.jsonl")[0]["paidSHA256"]
    assert rows(out/"run-receipt.jsonl")[0]["search"]==rows(original/"run-receipt.jsonl")[0]["search"]
    trace=rows(out/"makespan-plateau.jsonl")[0]
    return {"stem":stem,**{k:v for k,v in trace.items() if k!="samples"},
        "tieFraction":trace["ties"]/max(1,trace["comparisons"]),
        "hiddenComponentwiseFraction":trace["componentwiseBetterTies"]/max(1,trace["comparisons"])}


def main():
    root=ROOT/"runs"/datetime.now().strftime("makespan-plateau-audit-%Y%m%d-%H%M%S-%f");root.mkdir()
    print("MAKESPAN_AUDIT_ROOT",root,flush=True);done=[]
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            write_once(root/"protocol.json",{"instances":STEMS,"seed":SEED,"replayFE":1000000,
                "question":"Does the MAKESPAN local duty reject substantial physical noncritical-factory improvements because only maximum factory completion is compared?",
                "gate":"Both instances: >=20% makespan-tied local comparisons, >=10% of all MAKESPAN comparisons componentwise improve factory completions with at least one strict reduction under equal global makespan. This only motivates a fresh paired continuation test.",
                "preserved":"All original decisions, evaluations, RNG, family/sharing rules and physical ledger. Read existing immutable DynamicSchedule only. Record lexicographic and stricter componentwise comparisons separately.",
                "engineering":"Each trajectory must match original full paid sequence SHA, final genes, FE checkpoints, ledger, initials and search counts. No extra decoder calls except return QA.",
                "limits":"Factory completion improvement is not external HV or a useful future continuation proof. This is a standard max-objective plateau diagnostic, not fatigue-specific novelty."})
            for stem in STEMS:
                shutil.copytree(SOURCE/stem/"inputs",root/stem/"inputs");folder=root/stem/str(SEED);folder.mkdir()
                shutil.copy2(SOURCE/stem/str(SEED)/"ledger.csv",folder/"ledger.csv")
            cp=build(root)
            for stem in STEMS:done.append(run(root,cp,stem))
            gate=all(x["tieFraction"]>=.2 and x["hiddenComponentwiseFraction"]>=.1 for x in done)
            write_once(root/"analysis.json",{"instances":done,"worthContinuationProbe":gate})
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulReplayFE":1000000,"failedEvaluationFE":0,
        "paidSequenceEquivalent":True,"worthContinuationProbe":gate,
        "returnFullDecoderQA":sum(read(p)["offlineValidationDecodes"] for p in root.glob("*/*/*/summary.json"))})
    print("MAKESPAN_AUDIT_COMPLETE",done,"eligible",gate,flush=True)


if __name__=="__main__":main()
