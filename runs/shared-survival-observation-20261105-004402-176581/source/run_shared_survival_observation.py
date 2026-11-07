"""No new performance arms: exact on/off instrumentation replay of four frozen shared trajectories."""
from datetime import datetime
from pathlib import Path
import shutil
import time

from paired_survival_bench import run_cell
from shared_survival_build import build
from analyze_shared_survival_observation import analyze
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock

SOURCE=ROOT/"runs/survival-context-factorial-20261105-002440-955879"
STEMS=("20_8_5_1","100_2_3_1")
SEED=9940003
ARMS=("SHARE_PAIR","SHARE_FULL")


def run(root,cp,stem,arm,observed):
    tag=arm+("_ON" if observed else "_OFF")
    flags={"research.group.mode":"FULL_ROLE" if arm=="SHARE_FULL" else "PAIR",
           "research.reward.mode":"GROUP" if arm=="SHARE_FULL" else "INDIVIDUAL",
           "research.batch.mode":"ROLE_CROWD","research.survival.trace":str(observed).lower()}
    return run_cell(root,cp,{"stem":stem,"seed":SEED,"arm":tag},flags)


def equal_to_original(path,original):
    for name in ("solutions.jsonl","initial-population.jsonl","local-ledger.csv"):
        assert (path/name).read_bytes()==(original/name).read_bytes(),name
    assert [x["front"] for x in rows(path/"anytime.jsonl")]==[x["front"] for x in rows(original/"anytime.jsonl")]
    a,b=rows(path/"run-receipt.jsonl")[0],rows(original/"run-receipt.jsonl")[0]
    assert a["search"]==b["search"],"Original search counters changed"
    assert read(path/"group.jsonl")==read(original/"group.jsonl")


def main():
    root=ROOT/"runs"/datetime.now().strftime("shared-survival-observation-%Y%m%d-%H%M%S-%f")
    root.mkdir();print("SHARED_TRACE_ROOT",root,flush=True);done=[];start=time.monotonic()
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            source_protocol=read(SOURCE/"protocol.json")
            for stem in STEMS:
                shutil.copytree(SOURCE/stem/"inputs",root/stem/"inputs")
                folder=root/stem/str(SEED);folder.mkdir()
                shutil.copy2(SOURCE/stem/str(SEED)/"ledger.csv",folder/"ledger.csv")
            write_once(root/"protocol.json",{"source":str(SOURCE),"instances":source_protocol["instances"],"seed":SEED,"arms":ARMS,
                "replayFE":4000000,"newPerformanceArms":0,"scope":"Observation only of the four frozen PAIR/FULL shared trajectories. "
                    "Eight500k replays: disabled hooks first, enabled second. Both retain all original policies and the exact frozen local ledger.",
                "engineeringGate":"Zero-decoder provenance fixture; OFF matches original full final-genome and initial bytes, physical ledger with restarts, "
                                  "all FE frontier checkpoints and search/group counters. ON must match OFF paid SHA256 of the entire500k genome/objective sequence, "
                                  "and the same original evidence. Any mismatch stops interpretation.",
                "observation":"Mark direct composition at the original boolean composed branch. Track the successful paid parent copied into subsequent proposals, "
                              "last composed ancestor only. Record full2n batch pools, selected indices, lineage multiplicity, actual local entries, "
                              "generation-end population, subsequent external admissions and final archive points. Noninitial unknown parents are forbidden.",
                "interpretation":"Parent genealogy is neither gene-level inheritance nor causal credit. Teacher selection, resource donation and mixture provenance "
                                 "are not inferred from parent links. A later novel admission is not necessarily retained at the endpoint.",
                "diagnosticGate":"Only support the composed-sibling continuation path if FULL in both instances has at least one direct composed child selected "
                                 "alongside a same-lineage sibling AND at least one such root has a later archive-admitted descendant improving a root objective "
                                 "and a final archived descendant. Also report exclusive final-HV association after removal; >=0.1% in each instance is material. "
                                 "These association conditions authorize mechanism discussion, not a selector, efficacy expansion or rescue of old failed gates.",
                "costs":"Every replay is charged and reported. Digest and observer costs are diagnostic, not a new same-time performance comparison."})
            cp=build(root)
            from run_dynamic_deep_roles import BRIDGE
            execute(["java","-cp",cp,"org.uma.jmetal.util.research.search.SharedSurvivalChecks",str(BRIDGE/"inputs"),
                     str(BRIDGE/"inputs/RECONSTRUCTED-setup.txt")],root/"fixture.log")
            for stem in STEMS:
                for arm in ARMS:
                    original=SOURCE/stem/str(SEED)/arm
                    off=run(root,cp,stem,arm,False);equal_to_original(off,original);done.append(str(off.relative_to(root)))
                    on=run(root,cp,stem,arm,True);equal_to_original(on,original);done.append(str(on.relative_to(root)))
                    digest=lambda p:rows(p/"run-receipt.jsonl")[0]["paidSHA256"]
                    assert digest(off)==digest(on) and digest(off),"Paid trajectory changed"
                    write_once(on/"observation-equivalence.json",{"status":"PASS","sameFullPaidSequence":True,"sameOriginalEvidence":True,"paidSHA256":digest(on)})
            result=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulReplayFE":len(done)*500000,"failedEvaluationFE":0,
                                   "newPerformanceArms":0,"diagnosticAssociationSupported":result["bothInstancesSupported"],"wallSeconds":time.monotonic()-start})
    print("SHARED_TRACE_COMPLETE",result,flush=True)


if __name__=="__main__":main()
