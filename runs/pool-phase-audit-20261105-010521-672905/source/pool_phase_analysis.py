"""Same-receiver, same-background phase comparisons using only the frozen nine assembly policies."""
from itertools import product

import numpy as np

from run_long_budget_bridge import read,rows,write_once,hypervolume,execute

EARLY=("MAKESPAN_LOCAL_END","CENTER_LOCAL_END","ENERGY_LOCAL_END")


def construct(pool,receiver,cap_factor,eta):
    family=next(f for f in pool["families"] if f["family"]==receiver["family"])
    chosen=[];cap=receiver["objectives"][0]*cap_factor
    for records in family["factories"]:
        eligible=[r for r in records if r["objectives"][0]<=cap]
        if not eligible:return None
        score=lambda r:r["objectives"][1]/pool["energyScale"]+eta*r["objectives"][2]/pool["wageScale"]
        chosen.append(min(eligible,key=score))
    genes={k:[] for k in ("JS","FA","MA","WA")};objectives=[0.0,0.0,0.0]
    for f,r in enumerate(chosen):
        genes["JS"].extend(r["jobs"]);genes["FA"].extend([f]*len(r["jobs"]))
        genes["MA"].extend(r["machines"]);genes["WA"].extend(r["workers"])
        objectives[0]=max(objectives[0],r["objectives"][0]);objectives[1]+=r["objectives"][1];objectives[2]+=r["objectives"][2]
    assert sorted(genes["JS"])==list(range(len(receiver["JS"])))
    assert all(family["factoryByJob"][j]==f for j,f in zip(genes["JS"],genes["FA"]))
    return {**genes,"objectives":objectives,"capFactor":cap_factor,"eta":eta,
            "sourcePaidFE":[r["paidFE"] for r in chosen],"sourceStages":[r["stage"] for r in chosen],
            "sourceRoles":[r["producer"] for r in chosen]}


def candidate_cases(data):
    cases=[];unique={}
    for cohort,receivers in (("first",data["firstReceivers"]),("later",data["laterReceivers"])):
        for phase in data["snapshots"]:
            for index,parent in enumerate(receivers):
                choices=[]
                for cap,eta in product((.9,1.,1.1),(0.,1.,4.)):
                    candidate=construct(phase["pool"],parent,cap,eta)
                    if candidate is None:continue
                    assert all(fe<=phase["paidFE"] for fe in candidate["sourcePaidFE"])
                    key=tuple(tuple(candidate[k]) for k in ("JS","FA","MA","WA"))
                    if key not in unique:unique[key]=candidate
                    else:assert np.allclose(unique[key]["objectives"],candidate["objectives"],rtol=1e-12,atol=1e-9)
                    choices.append(candidate)
                cases.append({"cohort":cohort,"phase":phase["phase"],"phaseFE":phase["paidFE"],"receiver":index,
                              "family":parent["family"],"choices":choices})
    return cases,list(unique.values())


def check_assemblies(root,cp,stem,candidates):
    inp=root/stem/"inputs";path=root/stem/"assembly-cases.tsv"
    lines=["id\tobjectives\tJS\tFA\tMA\tWA"]
    for i,c in enumerate(candidates):
        lines.append("\t".join([str(i),",".join(map(str,c["objectives"])),*(",".join(map(str,c[k])) for k in ("JS","FA","MA","WA"))]))
    path.write_text("\n".join(lines)+"\n",encoding="utf-8")
    output=root/stem/"assembly-qa.json"
    execute(["java","-Xmx2g","-cp",cp,"research.dynamic.PoolAssemblyCheckRun",str(inp/f"{stem}.txt"),
             str(inp/"RECONSTRUCTED-setup.txt"),str(inp/"fatigue-input.txt"),str(path),str(output)],root/stem/"assembly-qa.log")
    report=read(output);assert report["status"]=="PASS" and report["passedOfflineDecodes"]==len(candidates)
    return report


def score_cases(spec,data,cases):
    norm=spec["normalization"];normed=lambda x:(np.asarray(x)-norm["lower"])/norm["scale"]
    snapshots={s["phase"]:s for s in data["snapshots"]};common=snapshots["G2_CENTER_ENTRY"]["knownArchive"]
    backgrounds={s["phase"]:s["knownArchive"] for s in data["snapshots"]};backgrounds["COMMON"]=common
    arrays={k:normed(v) for k,v in backgrounds.items()};base={k:float(hypervolume(v,(1.5,)*3)) for k,v in arrays.items()}
    def gain(candidate,key):
        x=normed(candidate);b=arrays[key]
        if np.any(np.all(b<=x,axis=1)):return 0.
        return max(0.,100*(float(hypervolume(np.vstack([b,x]),(1.5,)*3))/base[key]-1))
    results=[]
    for case in cases:
        scores=[{**c,"commonArchiveGainPct":gain(c["objectives"],"COMMON"),"ownPhaseArchiveGainPct":gain(c["objectives"],case["phase"])} for c in case["choices"]]
        results.append({k:v for k,v in case.items() if k!="choices"}|{"policies":scores,
            "bestCommonGainPct":max((s["commonArchiveGainPct"] for s in scores),default=0.),
            "bestOwnPhaseGainPct":max((s["ownPhaseArchiveGainPct"] for s in scores),default=0.)})
    initial={(r["cohort"],r["receiver"]):r["bestCommonGainPct"] for r in results if r["phase"]=="GLOBAL_END"}
    material={r["family"] for r in results if r["cohort"]=="later" and r["phase"] in EARLY and r["bestCommonGainPct"]>=.1
              and r["bestCommonGainPct"]-initial[(r["cohort"],r["receiver"]) ]>=.1}
    summary=[]
    for cohort in ("first","later"):
        for phase in snapshots:
            subset=[r for r in results if r["cohort"]==cohort and r["phase"]==phase]
            summary.append({"cohort":cohort,"phase":phase,"phaseFE":snapshots[phase]["paidFE"],
                "materialCommonFamilies":sorted({r["family"] for r in subset if r["bestCommonGainPct"]>=.1}),
                "materialOwnPhaseFamilies":sorted({r["family"] for r in subset if r["bestOwnPhaseGainPct"]>=.1}),
                "maxCommonGainPct":max(r["bestCommonGainPct"] for r in subset),"maxOwnPhaseGainPct":max(r["bestOwnPhaseGainPct"] for r in subset)})
    return {"stem":spec["stem"],"phaseSummary":summary,"earlyMaterialFamilies":sorted(material),"supported":len(material)>=2,"cases":results}


def analyze(root,cp):
    protocol=read(root/"protocol.json");results=[];qa=0
    for spec in protocol["instances"]:
        stem=spec["stem"];data,=rows(root/stem/str(protocol["seed"])/"CAPTURE/pool-phases.jsonl")
        cases,candidates=candidate_cases(data);report=check_assemblies(root,cp,stem,candidates);qa+=len(candidates)
        result=score_cases(spec,data,cases);write_once(root/stem/"opportunities.json",result)
        results.append({k:v for k,v in result.items() if k!="cases"})
    out={"instances":results,"bothInstancesSupported":all(r["supported"] for r in results),"offlineAssemblyDiagnosticDecodes":qa,
         "scope":"Best of nine is an offline opportunity bound requiring up to nine paid candidates in a future policy; not an implemented selector or performance gain. "
                 "Later receivers at earlier phases are offline counterfactual conditioning only. Own-phase and common-background results are separate."}
    write_once(root/"analysis.json",out);return out
