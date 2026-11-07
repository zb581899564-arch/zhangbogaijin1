"""Test hidden factory improvement as continuation value, without changing a full optimizer."""
from datetime import datetime
from pathlib import Path
import shutil

from paired_survival_bench import class_hashes
from qgs_epoch_build import BASIS
from run_personal_memory_screen import engineering
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from run_paired_qgs_guidance import replace
from makespan_continuation_plan import SOURCE,SOURCE_SEEDS,REPS,ARMS,LOCAL_FE,prepare,analyze

STEMS=("20_8_5_1","100_2_3_1")


def build(root):
    src,classes=root/"source",root/"classes";src.mkdir();classes.mkdir()
    cp=(BASIS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
    kernel=(ROOT/"src/algorithms/diagnostics/LocalPddrKernel.java").read_text(encoding="utf-8")
    kernel=replace(kernel,"        if (direction != Direction.CENTER || MODE == Mode.LEGACY)",
        "        if (direction == Direction.MAKESPAN) return MakespanTiePolicy.better(candidate,incumbent);\n"
        "        if (direction != Direction.CENTER || MODE == Mode.LEGACY)")
    (src/"LocalPddrKernel.java").write_text(kernel,encoding="utf-8")
    ledger=(ROOT/"src/algorithms/diagnostics/QgsLocalLedger.java").read_text(encoding="utf-8")
    ledger=replace(ledger,"    static QgsLocalLedger instance() {","    public static void resetForProbe() { active = null; }\n\n    static QgsLocalLedger instance() {")
    (src/"QgsLocalLedger.java").write_text(ledger,encoding="utf-8")
    entry=(BASIS/"source/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry=replace(entry,"        obs.write(out);","        obs.write(out);\n"
        "        append(out.resolve(\"makespan-tie.jsonl\"), org.uma.jmetal.util.research.search.MakespanTiePolicy.diagnostics());")
    (src/"PddrIsolationRun.java").write_text(entry,encoding="utf-8")
    for name in ("MakespanTiePolicy","MakespanContinuationProbe"):
        shutil.copy2(ROOT/f"src/algorithms/diagnostics/{name}.java",src)
    for name in ("run_makespan_continuation_probe.py","makespan_continuation_plan.py"):
        shutil.copy2(Path(__file__).with_name(name),src)
    execute(["javac","-encoding","UTF-8","--release","8","-cp",cp,"-d",str(classes),*map(str,src.glob("*.java"))],root/"compile.log")
    write_once(root/"class-hashes.json",class_hashes(classes));cp=f"{classes};{cp}"
    (root/"classpath.txt").write_text(cp,encoding="utf-8");return cp


def main():
    root=ROOT/"runs"/datetime.now().strftime("makespan-continuation-probe-%Y%m%d-%H%M%S-%f");root.mkdir()
    print("MAKESPAN_CONTINUATION_ROOT",root,flush=True);done=[]
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs=read(BASIS/"protocol.json")["instances"]
            write_once(root/"protocol.json",{"instances":specs,"sourceSeeds":SOURCE_SEEDS,"continuationSeeds":REPS,"arms":ARMS,
                "hypothesis":"A neutral makespan move improving noncritical factory completion can support later global Cmax reduction. New hypothesis from fixed-timeline observations, not rescue of failed CENTER tie/reward/sweep or personal-memory mechanisms.",
                "sources":"Reuse all eight outcome-independently captured free MAKESPAN parents from each of two paid original FULL source cohorts per instance. Same parents, construction seed and eight factory slots for all three rules. No new source selection based on outcome.",
                "candidate":"Only exact MAKESPAN ties use decreasing sorted physical factory completion vector lexicographic order. COST_LEX control uses TEC then TWC; STRICT is original. All other decisions/operators unchanged. Cached paid schedules only, no adjoint or new decoder.",
                "budget":"2instances x2sourceSeeds x8parents x2reps x3rules x(1paid parent+514continuationFE)=98880FE; engineering original STRICT500000FE, full return and retained QA separate. Each continuation inter2FE +8factory slots64FE. No free starts or duplicate/cached-call exemptions.",
                "gate":"Each instance mean relative best-paid Cmax improvement >=1.1x STRICT, >COST_LEX; >=9/16 parents beat each control after averaging their two reps. Mean conditional addedHV against own pre-existing paid background >=STRICT. Zero reference improvement is inconclusive. Failure stops this secondary order without lex-order/tolerance/seed scan.",
                "engineering":"STRICT original full500k paid sequence and frozen evidence replay first. Zero-decoder descending-lex checks. Every trial exact515 paidFE zero failures, physically identical factory slots and full decoder QA for all returned and retained points.",
                "literature":["https://arxiv.org/abs/2212.09077","https://arxiv.org/abs/1805.03437"],
                "novelty":"Lexicographic makespan minimization is established; this is a feasibility/continuation control, not a standalone novel contribution. A pass only motivates fresh closed-loop comparison including generic and matched classical enhancements.",
                "limits":"Local role mechanism, not complete-search, same-time, fatigue specificity or independent confirmation. No mainline or sharing changes."})
            for stem in STEMS:shutil.copytree(SOURCE/stem/"inputs",root/stem/"inputs");prepare(root,stem)
            cp=build(root);execute(["java","-cp",cp,"org.uma.jmetal.util.research.search.MakespanTiePolicy"],root/"lex-checks.log")
            engineering(root,cp)
            for stem in STEMS:
                inp=root/stem/"inputs";out=root/stem/"probe"
                cmd=["java","-Xms32m","-Xmx2g","-cp",cp,"org.uma.jmetal.util.research.search.MakespanContinuationProbe",str(inp/f"{stem}.txt"),
                    str(inp/"RECONSTRUCTED-setup.txt"),str(inp/"fatigue-input.txt"),str(root/stem/"cases.tsv"),str(out)]
                write_once(root/stem/"command.json",cmd);execute(cmd,root/stem/"run.log")
                receipt=rows(out/"receipt.jsonl")[0];assert receipt["successfulFE"]==49440 and receipt["failedFE"]==0
                done.append(analyze(root,next(s for s in specs if s["stem"]==stem)))
            gate=all(r["eligibleForClosedLoop"] for r in done)
            write_once(root/"analysis.json",{"instances":done,"worthClosedLoop":gate})
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulProbeFE":98880,"engineeringFE":500000,"failedEvaluationFE":0,
        "fullDecoderQA":sum(rows(root/stem/"probe/receipt.jsonl")[0]["fullDecoderQA"] for stem in STEMS),"worthClosedLoop":gate})
    print("MAKESPAN_CONTINUATION_COMPLETE",done,"eligible",gate,flush=True)


if __name__=="__main__":main()
