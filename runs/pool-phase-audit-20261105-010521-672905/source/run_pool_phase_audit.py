"""Exact replay with phase snapshots, then nine-policy same-background diagnostics and full assembly QA."""
from datetime import datetime
from pathlib import Path
import shutil
import time

from paired_survival_bench import run_cell
from pool_phase_build import OBS,build
from pool_phase_analysis import analyze
from run_long_budget_bridge import ROOT,read,rows,write_once,controller_lock

SOURCE=ROOT/"runs/survival-context-factorial-20261105-002440-955879"
SEED=9940003
STEMS=("20_8_5_1","100_2_3_1")


def equivalent(out,stem):
    old=OBS/stem/str(SEED)/"SHARE_FULL_OFF";frozen=SOURCE/stem/str(SEED)/"SHARE_FULL"
    assert rows(out/"run-receipt.jsonl")[0]["paidSHA256"]==rows(old/"run-receipt.jsonl")[0]["paidSHA256"]
    for name in ("solutions.jsonl","initial-population.jsonl","local-ledger.csv"):
        assert (out/name).read_bytes()==(frozen/name).read_bytes(),name
    assert [r["front"] for r in rows(out/"anytime.jsonl")]==[r["front"] for r in rows(frozen/"anytime.jsonl")]
    assert rows(out/"run-receipt.jsonl")[0]["search"]==rows(frozen/"run-receipt.jsonl")[0]["search"]
    assert read(out/"group.jsonl")==read(frozen/"group.jsonl")
    write_once(out/"observation-equivalence.json",{"status":"PASS","fullPaidSequenceAndOriginalEvidenceUnchanged":True})


def main():
    root=ROOT/"runs"/datetime.now().strftime("pool-phase-audit-%Y%m%d-%H%M%S-%f")
    root.mkdir();print("POOL_PHASE_ROOT",root,flush=True);done=[];start=time.monotonic()
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs=read(SOURCE/"protocol.json")["instances"]
            for stem in STEMS:
                shutil.copytree(SOURCE/stem/"inputs",root/stem/"inputs");folder=root/stem/str(SEED);folder.mkdir()
                shutil.copy2(SOURCE/stem/str(SEED)/"ledger.csv",folder/"ledger.csv")
            write_once(root/"protocol.json",{"instances":specs,"seed":SEED,"replayFE":1000000,"newPerformanceArms":0,
                "phases":"First-generation GLOBAL_END, MAKESPAN/CENTER/ENERGY/WORKER_COST_LOCAL_END and second-generation CENTER entry.",
                "receivers":"Eight protected CENTER particles at first global end and eight at second-generation decomposition. Two per family, no benefit-based resampling.",
                "sourceMetadata":"Only paidFE/stage/role fields added to FactoryRecord; same/dominance/truncation/choice ignore them. All snapshots read retained records and paid archives only.",
                "equivalence":"Each500k must match frozen full paid genome/objective SHA256, original final/initial genes, complete ledger including restarts, checkpoint fronts and search/group counters.",
                "policies":"Exactly original cap factors0.9/1/1.1 and eta0/1/4, per-factory energy/worker score with frozen initialization scales and first-in tie. No new selection rule.",
                "score":"For each snapshot, receiver and policy score single-candidate HV gain versus own-phase archive, and versus the identical archive at G2_CENTER_ENTRY. "
                        "Common-background comparison isolates pool changes. Best-of-nine is diagnostic upper opportunity, never a free implemented decision.",
                "gate":"Each instance needs at least two families with >=0.1% common-archive single-candidate HV gain and >=0.1 percentage-point advantage over GLOBAL_END pool "
                       "for the identical later receiver in MAKESPAN/CENTER/ENERGY_LOCAL_END. Worker-end and G2 opportunities are secondary because they are already near next global sharing. "
                       "If either instance fails, no earlier-composition integration or phase/eta/cap scans.",
                "QA":"Every unique assembled four-vector genome from all predefined nine-policy cases receives offline full decoding and timeline validation. Count these diagnostic calls separately; none enter search.",
                "limits":"Later receivers paired with earlier pools are offline conditioning, not available early to an online policy. No claims of specialization-only supply, generalization, "
                         "novelty or same-time superiority. Exact replay fees, return QA and new-assembly diagnostic decodes all reported."})
            cp=build(root)
            for stem in STEMS:
                out=run_cell(root,cp,{"stem":stem,"seed":SEED,"arm":"CAPTURE"},{"research.group.mode":"FULL_ROLE",
                             "research.reward.mode":"GROUP","research.batch.mode":"ROLE_CROWD","research.survival.trace":"false"})
                equivalent(out,stem);done.append(stem)
            result=analyze(root,cp)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    qa=sum(read(root/s/str(SEED)/"CAPTURE/summary.json")["offlineValidationDecodes"] for s in STEMS)
    write_once(root/"status.json",{"status":"COMPLETE","successfulReplayFE":len(done)*500000,"failedEvaluationFE":0,
        "returnFullDecoderQA":qa,"assemblyDiagnosticDecodes":result["offlineAssemblyDiagnosticDecodes"],
        "phaseOpportunitySupported":result["bothInstancesSupported"],"wallSeconds":time.monotonic()-start})
    print("POOL_PHASE_COMPLETE",result,flush=True)


if __name__=="__main__":main()
