"""Observe frozen local comparisons without changing proposals, acceptance, RNG or budgets."""
from datetime import datetime
from pathlib import Path
import shutil

import numpy as np

from paired_survival_bench import class_hashes,run_cell
from qgs_epoch_build import BASIS
from run_paired_qgs_guidance import replace
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,hypervolume,controller_lock

SOURCE=ROOT/"runs/survival-context-factorial-20261105-002440-955879"
OBS=ROOT/"runs/shared-survival-observation-20261105-004523-286623"
STEMS=("20_8_5_1","100_2_3_1")
SEED=9940003


def build(root):
    src,classes=root/"source",root/"classes";src.mkdir();classes.mkdir()
    cp=(BASIS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
    body=(ROOT/"src/algorithms/diagnostics/LocalPddrKernel.java").read_text(encoding="utf-8")
    body=replace(body,"        return candidate < incumbent;",
        "        boolean keep = candidate < incumbent;\n"
        "        AcceptancePlateauTrace.record(c,i,reference,candidate,incumbent,keep);\n        return keep;")
    (src/"LocalPddrKernel.java").write_text(body,encoding="utf-8")
    entry=(BASIS/"source/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry=replace(entry,"        obs.write(out);","        obs.write(out);\n"
        "        append(out.resolve(\"acceptance-plateau.jsonl\"), org.uma.jmetal.util.research.search.AcceptancePlateauTrace.diagnostics());")
    (src/"PddrIsolationRun.java").write_text(entry,encoding="utf-8")
    shutil.copy2(ROOT/"src/algorithms/diagnostics/AcceptancePlateauTrace.java",src)
    shutil.copy2(Path(__file__),src)
    execute(["javac","-encoding","UTF-8","--release","8","-cp",cp,"-d",str(classes),*map(str,src.glob("*.java"))],root/"compile.log")
    write_once(root/"class-hashes.json",class_hashes(classes));cp=f"{classes};{cp}"
    (root/"classpath.txt").write_text(cp,encoding="utf-8");return cp


def replay(root,cp,stem,enabled):
    arm="ON" if enabled else "OFF"
    out=run_cell(root,cp,{"stem":stem,"seed":SEED,"arm":arm},{
        "research.acceptance.trace":str(enabled).lower(),"research.personal.mode":"OLDEST",
        "research.memory.audit":"true","research.group.mode":"FULL_ROLE",
        "research.reward.mode":"GROUP","research.batch.mode":"ROLE_CROWD"})
    original=SOURCE/stem/str(SEED)/"SHARE_FULL"
    for name in ("solutions.jsonl","initial-population.jsonl","local-ledger.csv"):
        assert (out/name).read_bytes()==(original/name).read_bytes(),name
    assert [x["front"] for x in rows(out/"anytime.jsonl")]==[x["front"] for x in rows(original/"anytime.jsonl")]
    assert rows(out/"run-receipt.jsonl")[0]["paidSHA256"]==rows(OBS/stem/str(SEED)/"SHARE_FULL_OFF/run-receipt.jsonl")[0]["paidSHA256"]
    assert rows(out/"run-receipt.jsonl")[0]["search"]==rows(original/"run-receipt.jsonl")[0]["search"]
    return out


def analyze(root):
    results=[]
    for spec in read(root/"protocol.json")["instances"]:
        stem=spec["stem"];norm=spec["normalization"]
        obs=rows(root/stem/str(SEED)/"ON/acceptance-plateau.jsonl")[0]
        refs=[np.asarray(r)/norm["scale"] for r in obs["references"]]
        base=[hypervolume(r,(1.5,)*3) for r in refs];samples=[]
        for sample in obs["samples"]:
            if not(sample["tradeoff"] and sample["tied"]):continue
            i=sample["reference"]
            joint=np.vstack([refs[i],np.asarray(sample["parent"])/norm["scale"]])
            before=hypervolume(joint,(1.5,)*3)
            gain=float(hypervolume(np.vstack([joint,np.asarray(sample["child"])/norm["scale"]]),(1.5,)*3)-before)
            samples.append({"comparison":sample["comparison"],"gain":gain,"referenceHV":float(base[i])})
        meaningful=sum(s["gain"]/(1.5**3)*100>=.0001 for s in samples)
        fraction=obs["tradeoffTies"]/max(1,obs["objectiveChanged"])
        results.append({"stem":stem,"comparisons":obs["comparisons"],"objectiveChanged":obs["objectiveChanged"],
            "ties":obs["ties"],"tradeoffs":obs["tradeoffs"],"tradeoffTies":obs["tradeoffTies"],
            "changedComparisonTieTradeoffFraction":fraction,"sampledRejectedTradeoffs":len(samples),
            "sampledMaterialReferenceGains":meaningful,"eligibleForContinuationProbe":fraction>=.2 and meaningful>=20,
            "samples":samples})
    result={"instances":results,"worthLocalAcceptanceProbe":all(r["eligibleForContinuationProbe"] for r in results),
        "limits":"Fixed-reference conditional geometry, not current external-archive gain, valuable continuation, fatigue specificity or PDDR bug proof."}
    write_once(root/"analysis.json",result);return result


def main():
    root=ROOT/"runs"/datetime.now().strftime("acceptance-plateau-audit-%Y%m%d-%H%M%S-%f");root.mkdir()
    print("ACCEPTANCE_AUDIT_ROOT",root,flush=True);done=[]
    try:
        with controller_lock(ROOT/"research/night_research","dispatch.lock"):
            specs=read(BASIS/"protocol.json")["instances"]
            write_once(root/"protocol.json",{"instances":specs,"seed":SEED,"arms":["OFF","ON"],"replayFE":2000000,
                "hypothesis":"Original fixed-reference local PDDR may reject materially different incomparable alternatives by tied scores, limiting continuation. No change to acceptance or proposals in this observation.",
                "sampling":"Every257th CENTER comparison starting at1, independent of quality and without RNG. Count all comparisons exactly. Score child gain against reference plus incumbent only; do not call this gain against the up-to-date external archive.",
                "gate":"On each instance at least20% of objective-changing comparisons must be rejected incomparable ties and >=20 systematically sampled ties must add >=0.0001% of normalized reference box. This permits only a new paired continuation hypothesis, not long-budget efficacy.",
                "engineering":"OFF and ON must reproduce frozen500k full paid sequence digest, front checkpoints, final genes, initial population, physical ledger and search counts. Failure stops interpretation.",
                "preserved":"Oldest ND personal guide, serial/stale QGS, FULL_ROLE/group reward, original roles/families/sharing, exact local PDDR and all ledger slots; no search RNG or evaluations added.",
                "limits":"Costs include all four500k replays, return fullQA separately. Trace overhead disqualifies these runs as performance timing evidence."})
            for stem in STEMS:
                shutil.copytree(SOURCE/stem/"inputs",root/stem/"inputs")
                folder=root/stem/str(SEED);folder.mkdir()
                shutil.copy2(SOURCE/stem/str(SEED)/"ledger.csv",folder/"ledger.csv")
            cp=build(root)
            for stem in STEMS:
                for enabled in (False,True):replay(root,cp,stem,enabled);done.append([stem,enabled])
            result=analyze(root)
    except BaseException as exc:
        write_once(root/"status.json",{"status":"INCOMPLETE_RETAINED","completed":done,"error":str(exc)});raise
    write_once(root/"status.json",{"status":"COMPLETE","successfulReplayFE":2000000,"failedEvaluationFE":0,
        "fullSequenceEquivalence":True,"returnFullDecoderQA":sum(read(p)["offlineValidationDecodes"] for p in root.glob("*/*/*/summary.json")),
        "worthLocalAcceptanceProbe":result["worthLocalAcceptanceProbe"]})
    print("ACCEPTANCE_AUDIT_COMPLETE",[{k:v for k,v in r.items() if k!="samples"} for r in result["instances"]],flush=True)


if __name__=="__main__":main()
