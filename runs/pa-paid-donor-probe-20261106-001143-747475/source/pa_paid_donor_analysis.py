"""Logical100k staged endpoints, with every source-prefix FE included and reused traces disclosed."""
import numpy as np

from run_long_budget_bridge import hypervolume,igd_plus,nondominated,write_once
from pa_paid_donor_data import at
from research.dynamic_benchmark.tri_indicators import bidirectional_coverage,directional_description


def endpoints(root,stem,seed):
    folder=root/stem/str(seed)
    pure,_=at(folder/"PURE",100000);base,_=at(folder/"PURE",50000)
    initial,_=at(folder/"INIT_GRAFT",50000)
    result={"PURE":np.asarray(pure["front"],float)}
    for source in ("S","U","N"):
        full,_=at(folder/("SOURCE_"+source),100000);prefix,_=at(folder/("SOURCE_"+source),50000)
        result["SELF_"+source]=np.asarray(full["front"],float)
        for method,front in (("NONE",base["front"]),("INIT",initial["front"])):
            result[method+"_"+source]=nondominated(np.vstack([prefix["front"],front]))
        for method in ("GRAFT","INHERIT"):
            receiver,_=at(folder/(method+"_"+source),50000)
            result[method+"_"+source]=nondominated(np.vstack([prefix["front"],receiver["front"]]))
    return result


def analyze(root,plan):
    results=[]
    for spec in plan["instances"]:
        stem,norm=spec["stem"],spec["normalization"]
        raw={(seed,label):front for seed in plan["seeds"] for label,front in endpoints(root,stem,seed).items()}
        normalized={key:(front-norm["lower"])/norm["scale"] for key,front in raw.items()}
        reference=nondominated(np.vstack(list(normalized.values())))
        values={key:{"seed":key[0],"method":key[1],"logicalTotalFE":100000,"frontSize":len(front),
            "HV":{str(r):hypervolume(front,(r,)*3) for r in (1.25,1.5,2.)},"IGDplus":igd_plus(front,reference),
            "objectiveMin":raw[key].min(axis=0).tolist()} for key,front in normalized.items()}
        comparisons=[]
        for control in ("NONE_S","INIT_S","INHERIT_S","SELF_S","PURE","GRAFT_U","GRAFT_N","SELF_N"):
            pairs=[]
            for seed in plan["seeds"]:
                a,b=values[seed,"GRAFT_S"],values[seed,control]
                assert all(v>1e-12 for v in b["HV"].values())
                hv={r:100*(a["HV"][r]/b["HV"][r]-1) for r in a["HV"]}
                den=a["IGDplus"]+b["IGDplus"];igd=200*(a["IGDplus"]-b["IGDplus"])/den if den else 0.
                c=bidirectional_coverage(raw[seed,"GRAFT_S"],raw[seed,control])
                pairs.append({"seed":seed,"HVEffectPct":hv,"IGDplusSymmetricWorseningPct":igd,"coverage":c,
                    "directions":directional_description(hv["1.5"],igd,c["C_A_B"],c["C_B_A"])})
            medhv={str(r):float(np.median([p["HVEffectPct"][str(r)] for p in pairs])) for r in (1.25,1.5,2.)}
            medigd=float(np.median([p["IGDplusSymmetricWorseningPct"] for p in pairs]))
            ab=float(np.median([p["coverage"]["C_A_B"] for p in pairs]));ba=float(np.median([p["coverage"]["C_B_A"] for p in pairs]))
            comparisons.append({"control":control,"pairs":pairs,"medianHVEffectPct":medhv,
                "medianIGDplusSymmetricWorseningPct":medigd,"medianC_A_B":ab,"medianC_B_A":ba,
                "directions":directional_description(medhv["1.5"],medigd,ab,ba)})
        results.append({"stem":stem,"observations":list(values.values()),"comparisons":comparisons})
    return {"instances":results,"logicalFEperEndpoint":100000,"sameTimeProved":False,
        "sourcePrefixesAndCommonReceiverTracesReusedAcrossControls":True,"independentUnits":"Instance/seed, not16logicalmethodrows or individualfrontpoints",
        "goalAchieved":False}


def readiness(analysis):
    checked=[]
    for instance in analysis["instances"]:
        controls={}
        for row in instance["comparisons"]:
            ordinary=row["control"] in ("GRAFT_N","SELF_N")
            minimum=-1 if ordinary else .5
            igd_limit=5 if ordinary else 0
            c_limit=-.02 if ordinary else 0
            passed=row["medianHVEffectPct"]["1.5"]>=minimum-1e-10 and row["medianIGDplusSymmetricWorseningPct"]<=igd_limit+1e-10
            passed=passed and row["medianC_A_B"]-row["medianC_B_A"]>=c_limit-1e-12
            passed=passed and all(row["medianHVEffectPct"][str(r)]>=(-1 if ordinary else 0)-1e-10 for r in (1.25,2.))
            passed=passed and all(p["HVEffectPct"]["1.5"]>=(-5 if ordinary else -1)-1e-10
                and p["IGDplusSymmetricWorseningPct"]<=(15 if ordinary else 5)+1e-10
                and p["coverage"]["C_A_B"]-p["coverage"]["C_B_A"]>=(-.1 if ordinary else -.02)-1e-12 for p in row["pairs"])
            controls[row["control"]]=bool(passed)
        checked.append({"stem":instance["stem"],"controls":controls,"pass":all(controls.values())})
    return {"instances":checked,"pass":all(r["pass"] for r in checked),
        "scope":"Further study of this fixed50k+50k/100slot staged mechanism only, not paper or finalalgorithm approval"}
