"""Same finite children, identical per-parent teacher/noise marginals, different batch dependence."""
from collections import Counter

import numpy as np

from run_long_budget_bridge import read,rows,write_once,hypervolume


def groups(kind,rng):
    if kind=="COMMON":return np.tile(np.arange(16),(8,1))
    if kind=="LATIN":return (np.arange(16)[None,:]+np.arange(8)[:,None])%16
    return np.asarray([rng.permutation(16) for _ in range(8)])


def analyze(root):
    protocol=read(root/"protocol.json");results=[]
    for spec in protocol["instances"]:
        stem,norm=spec["stem"],spec["normalization"];cells=[]
        raw=[r for r in rows(root/stem/"probe/kernel-raw.jsonl") if r["kernel"]=="JOB_ALIGNED"]
        children={(r["caseId"],r["rep"]):r["child"]["objectives"] for r in raw}
        manifest=read(root/stem/"cases.json")["cohorts"]
        normed=lambda x:(np.asarray(x)-norm["lower"])/norm["scale"]
        for index,cohort in enumerate(manifest):
            base=normed(cohort["background"]);baseline=float(hypervolume(base,(1.5,)*3));stats={k:[] for k in ("COMMON","LATIN","RANDOM")}
            for rep in range(2):
                expected={f"c{index}-p{p}-g{g}" for p in range(8) for g in range(16)}
                for kind in stats:
                    mapping=groups(kind,np.random.default_rng(protocol["probeSeed"]+index*100+rep));used=[]
                    for batch in range(16):
                        ids=[f"c{index}-p{p}-g{mapping[p,batch]}" for p in range(8)];used.extend(ids)
                        points=normed([children[(key,rep)] for key in ids])
                        gain=max(0.,100*(float(hypervolume(np.vstack([base,points]),(1.5,)*3))/baseline-1))
                        stats[kind].append(gain)
                    assert set(used)==expected and all(n==1 for n in Counter(used).values()),"Changed per-parent marginals"
            means={k:float(np.mean(v)) for k,v in stats.items()};common=means["COMMON"]
            effect=lambda k:100*(means[k]/common-1) if common>1e-12 else None
            cells.append({"sourceSeed":cohort["sourceSeed"],"role":cohort["role"],"step":cohort["step"],"paidFE":cohort["paidFE"],
                          "uniqueSampledGuides":cohort["uniqueSampledGuides"],"meanAddedHVPctOfBackground":means,
                          "latinEffectPct":effect("LATIN"),"randomEffectPct":effect("RANDOM"),"batches":stats})
        informative=[c for c in cells if c["latinEffectPct"] is not None]
        latin=[c["latinEffectPct"] for c in informative];random=[c["randomEffectPct"] for c in informative]
        wins=sum(c["latinEffectPct"]>0 and c["randomEffectPct"]>0 for c in informative)
        center=[c for c in informative if c["role"]=="CENTER"]
        passed=len(informative)>=6 and np.median(latin)>=10 and np.median(random)>=5 and wins>=6 \
            and len(center)==2 and all(c["latinEffectPct"]>=0 for c in center)
        results.append({"stem":stem,"cells":cells,"informativeCohorts":len(informative),"bothIndependentControlsWin":wins,
                        "medianLatinEffectPct":float(np.median(latin)) if latin else None,"medianRandomEffectPct":float(np.median(random)) if random else None,
                        "supported":bool(passed)})
    out={"instances":results,"bothInstancesSupported":all(r["supported"] for r in results),
         "scope":"Paired offline regrouping of the same evaluated JOB_ALIGNED children. Marginal teacher multisets and per-parent construction seeds identical; "
                 "only dependence across the eight-parent group changes. No closed-loop or time-advantage claim; other evaluated kernels not substituted as winners."}
    write_once(root/"analysis.json",out);return out
