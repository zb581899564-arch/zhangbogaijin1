"""Collect deadline-valid archives and derive run/instance metric tables."""
import json
import numpy as np
from .io import load, dump, csv_write
from .metrics import nondominated, hypervolume, igd_plus
from .statistics import effect, holm


def collect_runs(root, p, output, variants):
    allruns=[]; references={}; anomalies=[]
    for inst in p["instances"]:
        stem=inst["stem"]; current=[]
        for budget in ["FE","TIME"]:
            for seed in p["seeds"]:
                for mode in variants:
                    folder=root/"trials"/stem/budget/str(seed)/mode
                    s=load(folder/"summary.json")
                    curves=[json.loads(line) for line in (folder/"anytime.jsonl").read_text(encoding="utf-8").splitlines()]
                    if s["status"]!="passed" or s["failed"]!=s["timeInterruptedAttempts"]: anomalies.append(str(folder))
                    if budget=="FE" and (s["attempted"]!=inst["feLimit"] or s["failed"]): anomalies.append("FE mismatch "+str(folder))
                    if budget=="TIME" and s["stopReason"]!="TIME_LIMIT": anomalies.append("Time mismatch "+str(folder))
                    for row in curves:
                        if budget=="TIME" and row["elapsedSeconds"]>row["checkpoint"]+1e-12: anomalies.append("Future archive "+str(folder))
                        if budget=="FE" and row["fe"]>row["checkpoint"]: anomalies.append("Future FE "+str(folder))
                    scale=np.array(inst["normalization"]["scale"])
                    front=np.array(curves[-1]["front"]).reshape(-1,3)/scale
                    if not len(front): anomalies.append("Empty front "+str(folder))
                    current.append(front)
                    allruns.append(dict(instance=stem,budget=budget,seed=seed,variant=mode,summary=s,curves=curves,scale=scale,front=front))
        references[stem]=nondominated(np.concatenate(current))
        dump(output/(stem+"-empirical-reference.json"),references[stem].tolist())
    if anomalies:
        dump(output/"audit-failures.json",anomalies);raise RuntimeError("Invalid runs; see audit-failures")
    return allruns, references


def metric_tables(allruns, references, p, output):
    rows=[]; curves=[]
    for run in allruns:
        s=run["summary"];reference=references[run["instance"]]
        prefix={k:run[k] for k in ["instance","budget","seed","variant"]}
        coop=s.get("cooperation",{});joint=s.get("joint",{})
        row={**prefix,"HV":hypervolume(run["front"]),"IGDplus":igd_plus(run["front"],reference),
             "deadlineValidFE":run["curves"][-1]["fe"],"attempted":s["attempted"],"successful":s["successful"],
             "searchSeconds":s["searchSeconds"],"overshootSeconds":s["deadlineOvershootSeconds"],
             "interruptedAttempts":s["timeInterruptedAttempts"],"archiveSize":len(run["front"]),
             "outsideReference":int(np.any(run["front"]>=1.1,axis=1).sum()),
             "generations":s["search"].get("generations.completed",0),
             "decodeSeconds":s["decoder"]["dynamic.decodeNanos"]/1e9,
             "guidedTrajectories":joint.get("completedTrajectories",0),
             "candidateTrials":joint.get("candidateStepTrials",0),
             "proposeSeconds":joint.get("proposeNanos",0)/1e9,
             "trainingSeconds":joint.get("trainingNanos",0)/1e9,
             "prefixSeconds":joint.get("prefixRestoreNanos",0)/1e9,
             "predictionSeconds":joint.get("predictionNanos",0)/1e9,
             "learnedActions":joint.get("learnedActions",0),
             "headUpdates":sum(h["updates"] for h in joint.get("perDirection",{}).values()),
             "cooperationSeconds":coop.get("cooperationSeconds",0),
             "paidPoolObservations":coop.get("paidObservations",0),
             "assemblies":coop.get("assembliesValidated",0),"poolRecords":coop.get("poolRecords",0),
             "minimumCmax":float(run["front"][:,0].min()*run["scale"][0]),
             "minimumTEC":float(run["front"][:,1].min()*run["scale"][1]),
             "minimumTWC":float(run["front"][:,2].min()*run["scale"][2])}
        rows.append(row)
        for index,c in enumerate(run["curves"]):
            f=np.array(c["front"]).reshape(-1,3)/run["scale"]
            curves.append({**prefix,"fraction":p["checkpoints"][index],"checkpoint":c["checkpoint"],"latestFE":c["fe"],
                           "latestSeconds":c["elapsedSeconds"],"HV":hypervolume(f),"IGDplus":igd_plus(f,reference)})
    csv_write(output/"run-metrics.csv",rows);csv_write(output/"curves.csv",curves)
    return rows, curves


def instance_means(rows, p, variants, output):
    aggregates=[]; means={}
    numeric=[k for k in rows[0] if k not in ["instance","budget","seed","variant"]]
    for inst in p["instances"]:
        for budget in ["FE","TIME"]:
            for mode in variants:
                subset=[r for r in rows if (r["instance"],r["budget"],r["variant"])==(inst["stem"],budget,mode)]
                a={"instance":inst["stem"],"budget":budget,"variant":mode,**{k:float(np.mean([r[k] for r in subset])) for k in numeric}}
                a["HVseedSD"]=float(np.std([r["HV"] for r in subset],ddof=1));aggregates.append(a)
                means[(inst["stem"],budget,mode)] = a
    csv_write(output/"instance-metrics.csv",aggregates)
    return means

