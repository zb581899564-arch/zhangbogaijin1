"""Read-only phase/cost accounting of the accepted-guide gate; no search evaluations."""
import argparse
from pathlib import Path

import numpy as np

from run_long_budget_bridge import read, rows, write_once, hypervolume


def phase_metrics(root):
    protocol=read(root/"protocol.json");result=[]
    for spec in protocol["instances"]:
        stem,norm=spec["stem"],spec["normalization"]
        paths={a:root/stem/str(protocol["seed"])/a for a in protocol["methods"]}
        curves={a:rows(p/"anytime.jsonl") for a,p in paths.items()}
        measures={}
        for arm,curve in curves.items():
            measures[arm]={int(c["checkpoint"]):{
                "HV":float(hypervolume((np.asarray(c["front"])-norm["lower"])/norm["scale"],(1.5,)*3)),
                "minimumCmax":float(np.min(np.asarray(c["front"])[:,0]))} for c in curve}
        effects=[]
        for fe in sorted(measures["BATCH"]):
            hv=measures["BATCH"][fe]["HV"]
            effects.append({"FE":fe,"batchVsGENPct":100*(hv/measures["GEN"][fe]["HV"]-1),
                            "batchVsNSGAPct":100*(hv/measures["NSGA"][fe]["HV"]-1)})
        result.append({"stem":stem,"measures":measures,"effects":effects})
    return result


def costs(root):
    receipts=list(root.glob("*/*/*/run-receipt.jsonl"))+list(root.glob("engineering/*/*/*/run-receipt.jsonl"))
    successful=failed=qa=0;search_seconds=refresh_seconds=0
    for p in receipts:
        row,=rows(p);successful+=row["successful"];failed+=row["failed"];search_seconds+=row["searchSeconds"]
        summary=p.parent/"summary.json"
        if summary.exists():qa+=read(summary)["offlineValidationDecodes"]
        guides=p.parent/"guides.jsonl"
        if guides.exists():refresh_seconds+=rows(guides)[0]["refreshSeconds"]
    return {"receiptCount":len(receipts),"successfulFEIncludingEngineering":successful,"failedFE":failed,
            "offlineFullDecoderQA":qa,"sumSearchSeconds":search_seconds,"sumDirectRefreshSeconds":refresh_seconds,
            "scope":"Receipt sums within this gate only; short-probe failure and other runs accounted separately. Refresh timing excludes indirect downstream guide/archive costs, which remain in searchSeconds."}


def main():
    parser=argparse.ArgumentParser();parser.add_argument("root",type=Path);args=parser.parse_args()
    out={"scope":"Zero new FE post-hoc phase explanation; original final endpoint and gate unchanged.",
         "phaseMetrics":phase_metrics(args.root),"costs":costs(args.root)}
    write_once(args.root/"phase-diagnostics.json",out)
    print({"costs":out["costs"],"phases":[{"stem":r["stem"],"effects":r["effects"]} for r in out["phaseMetrics"]]})


if __name__=="__main__":main()
