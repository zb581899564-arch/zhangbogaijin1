"""Offline analysis of the frozen step4/5 experiment. No feedback to any search run."""
import csv
import json
from pathlib import Path
import sys
import numpy as np
from .metrics import nondominated, hypervolume, igd_plus, check_metrics
from .statistics import effect, holm


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")


def csv_write(path,rows):
    with path.open("w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def analyze(root):
    check_metrics()
    p=load(root/"protocol.json"); status=load(root/"status.json")
    variants=p["coreVariants"]+p["cooperationVariants"]
    expected=len(p["instances"])*len(p["seeds"])*len(variants)*2
    if status["completed"]!=expected: raise RuntimeError("Incomplete runs; no final analysis")
    output=root/"analysis";output.mkdir(exist_ok=False)
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
    targetrows=[]
    for r in rows:
        best=max(v["HV"] for v in rows if v["instance"]==r["instance"]);target=.95*best
        checkpoints=[c for c in curves if all(c[k]==r[k] for k in ["instance","budget","seed","variant"])]
        first=next((c for c in checkpoints if c["HV"]>=target),None)
        targetrows.append({**{k:r[k] for k in ["instance","budget","seed","variant"]},"targetHV":target,
                           "firstScheduledCheckpoint":first["checkpoint"] if first else "censored","kind":r["budget"]})
    csv_write(output/"target-attainment.csv",targetrows)
    audit={"status":"passed","runs":len(rows),"step4Runs":sum(r["variant"] in p["coreVariants"] for r in rows),
           "step5AdditionalRuns":sum(r["variant"] in p["cooperationVariants"] for r in rows),
           "genuineFailures":0,"timeInterruptedAttempts":sum(r["interruptedAttempts"] for r in rows),
           "outsideReference":sum(r["outsideReference"] for r in rows),"maximumOvershootSeconds":max(r["overshootSeconds"] for r in rows),
           "totalPaidFE":sum(r["attempted"] for r in rows),"totalSearchSeconds":sum(r["searchSeconds"] for r in rows),
           "offlineValidationDecodes":sum(r["summary"]["offlineValidationDecodes"] for r in allruns),
           "sharedAssembliesValidated":sum(r["assemblies"] for r in rows),"referenceSizes":{k:len(v) for k,v in references.items()}}
    dump(output/"audit.json",audit)
    report=["# 第四、第五步完整算法开发初筛","",f"{len(rows)}次完整运行；6实例×5seed×9版本×2预算。主目标Cmax/TEC/TWC，strong_fast合成疲劳参数。",
            "归一化在正式运行前冻结；IGD+参考集为全部九版本末期有效档案的经验并集，不是真前沿。时间结果使用截止时间内完成的档案；离线重放不反馈搜索。",
            "", "## 实例层平均HV差", "", "|步骤|预算|比较|平均HV差|平均相对%|实例胜/平/负|95%探索性区间|Holm p|", "|---|---|---|---:|---:|---|---|---:|"]
    for c in comparisons:
        report.append(f"|{c['step']}|{c['budget']}|{c['comparison']}|{c['meanDelta']:.6f}|{c.get('meanRelativePercent',float('nan')):.3f}|{c['wins']}/{c['ties']}/{c['losses']}|[{c['bootstrap95'][0]:.6f},{c['bootstrap95'][1]:.6f}]|{c['holmP']:.4f}|")
    report += ["", "## 解释边界", "", "这是开发实例初筛，5个seed是同一实例内的重复，配对单位只有6个实例。区间、单侧符号翻转检验与Holm校正仅用于探索性判断；不能替代第六步独立确认。",
               "四个FA家族在本轮固定不刷新，各占5粒子，80粒子保持自由。SYNC控制含相同配额、资源重绑定和固定FA限制，但不开池组合。共享组合按有限池精确可分解目标选厂方案；不声称全局最优或工资预算等价。",
               "完整基线和联合生成器的本轮结果不能用于倒推v1-v10局部机制，也不能由一个组件无优势否定四子群方向。",
               "", "## 费用审计", "", "```json",json.dumps(audit,ensure_ascii=False,indent=2),"```",""]
    (output/"report.md").write_text("\n".join(report),encoding="utf-8")
    dump(root/"status.json",{"status":"ANALYSIS_COMPLETE","completed":expected,"expected":expected,"analysis":"analysis/report.md"})
    print(json.dumps(audit,ensure_ascii=False,indent=2)); print(output)


if __name__=="__main__": analyze(Path(sys.argv[1]).resolve())
