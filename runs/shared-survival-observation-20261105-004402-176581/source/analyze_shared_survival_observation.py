"""Endpoint association and exact recorded-survival accounting; never estimates causal gain."""
import csv
from collections import Counter

import numpy as np

from run_long_budget_bridge import read,rows,write_once,hypervolume


def check_pools(path):
    groups={}
    with (path/"global-pools.csv").open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):groups.setdefault(int(row["batch"]),[]).append(row)
    totals=Counter()
    for records in groups.values():
        n=len(records)//2;selected=[r for r in records if int(r["selectedOrder"])>=0]
        assert len(records)==2*n and len(selected)==n
        assert sorted(int(r["selectedOrder"]) for r in selected)==list(range(n))
        assert Counter(r["category"] for r in records[:n])==Counter(r["category"] for r in selected)
        children=[r for r in records[n:] if r["directComposed"]=="true"]
        kept=[r for r in children if int(r["selectedOrder"])>=0]
        totals["globalChildren"]+=n;totals["composedChildren"]+=len(children);totals["composedChildrenSelected"]+=len(kept)
        multiplicity=Counter(r["lineage"] for r in selected)
        totals["composedChildrenSelectedAlongsideSibling"]+=sum(multiplicity[r["lineage"]]>1 for r in kept)
    assert totals["globalChildren"]==10000
    return dict(totals)


def analyze(root):
    protocol=read(root/"protocol.json");results=[];qa=0
    for spec in protocol["instances"]:
        stem,norm=spec["stem"],spec["normalization"];cells=[]
        normed=lambda x:(np.asarray(x)-norm["lower"])/norm["scale"]
        hv=lambda x:float(hypervolume(normed(x),(1.5,)*3)) if len(x) else 0.0
        for arm in protocol["arms"]:
            path=root/stem/str(protocol["seed"])/(arm+"_ON")
            data,=rows(path/"shared-survival.jsonl");pool=check_pools(path)
            assert data["successfulFE"]==500000 and data["counts"]["composedPaid"]==pool["composedChildren"]
            eligible=[r for r in data["roots"] if r["directChildSelectedWithSibling"] and r["admissionsImprovingAnyRootObjective"]>0 and r["finalPoints"]>0]
            ids={r["fe"] for r in eligible};final=data["finalPoints"]
            front=[p["objectives"] for p in final];remaining=[p["objectives"] for p in final if p["lastComposedAncestorFE"] not in ids]
            all_remaining=[p["objectives"] for p in final if p["lastComposedAncestorFE"]==0]
            total=hv(front);loss=100*(total-hv(remaining))/total
            cells.append({"arm":arm,"pool":pool,"roots":len(data["roots"]),"qualifyingSiblingRoots":len(ids),
                          "qualifyingRootFinalPoints":sum(p["lastComposedAncestorFE"] in ids for p in final),
                          "qualifyingSiblingExclusiveHVAssociationPct":loss,"allComposedAncestryExclusiveHVAssociationPct":100*(total-hv(all_remaining))/total,
                          "counts":data["counts"],"directObservationSeconds":data["directObservationSeconds"],
                          "supported":len(ids)>0 and loss>=.1})
            for flag in ("ON","OFF"):
                qa+=read(path.parent/(arm+"_"+flag)/"summary.json")["offlineValidationDecodes"]
        results.append({"stem":stem,"cells":cells,"fullPathSupported":next(c["supported"] for c in cells if c["arm"]=="SHARE_FULL")})
    result={"instances":results,"bothInstancesSupported":all(r["fullPathSupported"] for r in results),"offlineFullDecoderQA":qa,
            "scope":"Exact trajectories retained. HV removal is final-region association, not a counterfactual run or independent cooperative performance gain."}
    write_once(root/"analysis.json",result);return result
