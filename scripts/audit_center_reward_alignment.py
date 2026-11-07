"""Read-only alignment of actual accepted CENTER batch geometry and the actual group-mean Q reward."""
import csv
from datetime import datetime
from pathlib import Path
import shutil

import numpy as np

from run_long_budget_bridge import ROOT,rows,write_once,hypervolume

SOURCE=ROOT/"runs/shared-survival-observation-20261105-004523-286623"
STEMS=("20_8_5_1","100_2_3_1")


def measure(path,multiplier):
    initial=np.asarray([s["objectives"] for s in rows(path/"initial-population.jsonl")]);ref=initial.max(axis=0)*multiplier
    groups={}
    with (path/"global-pools.csv").open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            if row["role"]=="CENTER":groups.setdefault(int(row["batch"]),[]).append(row)
    result=[]
    for batch,pool in groups.items():
        parents=sorted((r for r in pool if r["isChild"]=="false"),key=lambda r:int(r["index"]))
        selected=sorted((r for r in pool if int(r["selectedOrder"])>=0),key=lambda r:int(r["selectedOrder"]))
        values=lambda records:np.asarray([[float(r[k]) for k in ("cmax","tec","twc")] for r in records])
        before,after=values(parents),values(selected);assert len(before)==len(after)==55
        mean_before,mean_after=before.mean(axis=0),after.mean(axis=0)
        old_reward=float(np.sum((mean_before-mean_after)/np.where(mean_before==0,1,np.abs(mean_before))))
        old_hv=float(hypervolume(before/ref,(1.,1.,1.)));new_hv=float(hypervolume(after/ref,(1.,1.,1.)))
        delta=100*(new_hv-old_hv);meaningful=abs(delta)>=1e-6
        conflict=meaningful and ((delta>0 and old_reward<=1e-12) or (delta<0 and old_reward>=-1e-12))
        result.append({"batch":batch,"generation":int(pool[0]["generation"]),"meanReward":old_reward,
                       "groupHVDeltaPctOfReferenceBox":delta,"meaningful":meaningful,"conflict":bool(conflict)})
    meaningful=[r for r in result if r["meaningful"]];conflicts=[r for r in meaningful if r["conflict"]]
    return {"referenceMultiplier":multiplier,"initialReference":ref.tolist(),"batches":result,"meaningfulBatches":len(meaningful),
            "conflictBatches":len(conflicts),"conflictFraction":len(conflicts)/len(meaningful) if meaningful else None,
            "positiveHVNonpositiveReward":sum(r["groupHVDeltaPctOfReferenceBox"]>0 for r in conflicts),
            "negativeHVNonnegativeReward":sum(r["groupHVDeltaPctOfReferenceBox"]<0 for r in conflicts)}


def main():
    root=ROOT/"runs"/datetime.now().strftime("center-reward-alignment-%Y%m%d-%H%M%S-%f");root.mkdir()
    write_once(root/"protocol.json",{"source":str(SOURCE),"arms":["SHARE_FULL_ON"],"searchFE":0,"decoderCalls":0,
        "question":"Does the CENTER group-mean Q reward disagree in sign with accepted-group hypervolume change under the actual FULL_ROLE policy?",
        "reference":"1.1 times per-objective max of the100 paid initial points, lower zero, box-normalized. Multiplier1.5 only a fixed sensitivity check; no search parameter chosen from outcomes.",
        "definitions":"Meaningful group-HV change >=1e-6 percent of reference box. Reward epsilon1e-12 handles floating sums. Conflict includes positiveHV/nonpositive reward or negativeHV/nonnegative reward.",
        "gate":"Both instances need >=20% conflict among meaningful CENTER updates at BOTH fixed references, >=20 meaningful batches per instance. Only then consider a separately frozen reward-alignment hypothesis; otherwise no reward rewrite.",
        "limits":"Observed objective/reward alignment only, not evidence a different reward would improve learning, survive high exploration, produce final benefits or be novel. Scalar roles intentionally keep single-objective duties."})
    shutil.copy2(Path(__file__),root/"source.py");results=[]
    for stem in STEMS:
        path=SOURCE/stem/"9940003/SHARE_FULL_ON";scores=[measure(path,r) for r in (1.1,1.5)]
        passed=all(s["meaningfulBatches"]>=20 and s["conflictFraction"]>=.2 for s in scores)
        results.append({"stem":stem,"measurements":scores,"supported":passed})
    result={"instances":results,"bothInstancesSupported":all(r["supported"] for r in results),"newSearchFE":0,"newDecoderCalls":0}
    write_once(root/"analysis.json",result);write_once(root/"status.json",{"status":"COMPLETE","rewardMismatchSupported":result["bothInstancesSupported"],"searchFE":0,"decoderCalls":0})
    print("REWARD_ALIGNMENT_ROOT",root)
    print([{ "stem":r["stem"],"supported":r["supported"],"measurements":[{k:v for k,v in s.items() if k!="batches"} for s in r["measurements"]]} for r in results])


if __name__=="__main__":main()
