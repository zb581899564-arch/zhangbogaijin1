"""Split final-region associations into direct compositions and proper paid descendants."""
import argparse

import numpy as np

from run_long_budget_bridge import read,rows,write_once,hypervolume


def decompose(root):
    protocol=read(root/"protocol.json");out=[]
    for spec in protocol["instances"]:
        stem,norm=spec["stem"],spec["normalization"]
        def hv(points):
            if not points:return 0.0
            values=np.asarray([p["objectives"] for p in points])
            return float(hypervolume((values-norm["lower"])/norm["scale"],(1.5,)*3))
        for arm in protocol["arms"]:
            data,=rows(root/stem/str(protocol["seed"])/(arm+"_ON")/"shared-survival.jsonl")
            final=data["finalPoints"];total=hv(final)
            direct=[p for p in final if p["directComposition"]]
            descendant=[p for p in final if p["lastComposedAncestorFE"]>0 and p["paidFE"]>p["lastComposedAncestorFE"]]
            out.append({"stem":stem,"arm":arm,"finalPointCount":len(final),"directComposedFinalPoints":len(direct),
                "properDescendantFinalPoints":len(descendant),
                "directCompositionExclusiveHVAssociationPct":100*(total-hv([p for p in final if not p["directComposition"]]))/total,
                "properDescendantExclusiveHVAssociationPct":100*(total-hv([p for p in final if p not in descendant]))/total,
                "directComposedFinalPaidFE":[p["paidFE"] for p in direct]})
    return {"scope":"Zero new evaluations. Direct and descendant HV removal contributions overlap and must not be summed. These are final-region associations, not counterfactual performance effects.","cells":out}


def main():
    from pathlib import Path
    parser=argparse.ArgumentParser();parser.add_argument("root",type=Path);args=parser.parse_args()
    result=decompose(args.root);output=args.root/"final-association-decomposition.json"
    if output.exists():assert read(output)==result
    else:write_once(output,result)
    print("ENDPOINT_DECOMPOSITION_VERIFIED",len(result["cells"]))


if __name__=="__main__":main()
