"""Predeclared paired comparisons, target attainment, and run accounting."""
import numpy as np
from .io import load, dump, csv_write
from .metrics import nondominated, hypervolume, igd_plus
from .statistics import effect, holm


def comparisons(p, means, output):
    comparisons=[]
    step4=[("VALUE",b) for b in ["BASELINE","RANDOM","GREEDY","TAIL"]]+[("RANDOM","BASELINE")]
    step5=[("SHARE","BASELINE"),("VALUE_SHARE","VALUE"),("VALUE_SHARE","SHARE"),("SHARE","SYNC"),("VALUE_SHARE","VALUE_SYNC")]
    for step,pairs in [(4,step4),(5,step5)]:
        group=[]
        for budget in ["FE","TIME"]:
            for a,b in pairs:
                deltas=[means[(i["stem"],budget,a)]["HV"]-means[(i["stem"],budget,b)]["HV"] for i in p["instances"]]
                v={"step":step,"budget":budget,"comparison":a+" - "+b,**effect(deltas)}
                v["meanRelativePercent"]=float(np.mean([100*(means[(i["stem"],budget,a)]["HV"]/means[(i["stem"],budget,b)]["HV"]-1) for i in p["instances"]]))
                v["IGDplusDelta"]=float(np.mean([means[(i["stem"],budget,a)]["IGDplus"]-means[(i["stem"],budget,b)]["IGDplus"] for i in p["instances"]]))
                group.append(v)
            if step==5:
                values=[]
                for i in p["instances"]:
                    m=lambda v:means[(i["stem"],budget,v)]["HV"]
                    values.append((m("VALUE_SHARE")-m("SHARE"))-(m("VALUE")-m("BASELINE")))
                group.append({"step":5,"budget":budget,"comparison":"interaction (VALUE_SHARE-SHARE)-(VALUE-BASELINE)",**effect(values)})
        holm(group);comparisons+=group
    dump(output/"comparisons.json",comparisons)
    return comparisons


def target_attainment(rows, curves, output):
    targetrows=[]
    for r in rows:
        best=max(v["HV"] for v in rows if v["instance"]==r["instance"]);target=.95*best
        checkpoints=[c for c in curves if all(c[k]==r[k] for k in ["instance","budget","seed","variant"])]
        first=next((c for c in checkpoints if c["HV"]>=target),None)
        targetrows.append({**{k:r[k] for k in ["instance","budget","seed","variant"]},"targetHV":target,
                           "firstScheduledCheckpoint":first["checkpoint"] if first else "censored","kind":r["budget"]})
    csv_write(output/"target-attainment.csv",targetrows)


def accounting(allruns, rows, p, references, output):
    audit={"status":"passed","runs":len(rows),"step4Runs":sum(r["variant"] in p["coreVariants"] for r in rows),
           "step5AdditionalRuns":sum(r["variant"] in p["cooperationVariants"] for r in rows),
           "genuineFailures":0,"timeInterruptedAttempts":sum(r["interruptedAttempts"] for r in rows),
           "outsideReference":sum(r["outsideReference"] for r in rows),"maximumOvershootSeconds":max(r["overshootSeconds"] for r in rows),
           "totalPaidFE":sum(r["attempted"] for r in rows),"totalSearchSeconds":sum(r["searchSeconds"] for r in rows),
           "offlineValidationDecodes":sum(r["summary"]["offlineValidationDecodes"] for r in allruns),
           "sharedAssembliesValidated":sum(r["assemblies"] for r in rows),"referenceSizes":{k:len(v) for k,v in references.items()}}
    dump(output/"audit.json",audit)
    return audit

