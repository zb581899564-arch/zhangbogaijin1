"""Fixed paid source cohorts, matched finite factory slots, and paired continuation scoring."""
import csv
import numpy as np

from run_long_budget_bridge import ROOT,rows,write_once,hypervolume

SOURCE=ROOT/"runs/teacher-coupling-probe-20261105-011608-145831"
SOURCE_SEEDS=(10060007,10060031)
REPS=(10840003,10840033)
ARMS=("STRICT","FACTORY_LEX","COST_LEX")
LOCAL_FE=514


def prepare(root,stem):
    folder=root/stem;cases=[];lines=[];cohorts=[]
    (folder/"probe/ledgers").mkdir(parents=True)
    for s,seed in enumerate(SOURCE_SEEDS):
        source=SOURCE/stem/str(seed)/"ON/teacher-cohorts.jsonl"
        cohort=next(c for c in rows(source)[0]["cohorts"] if c["role"]=="MAKESPAN")
        cohorts.append({"sourceSeed":seed,"source":str(source),"paidFE":cohort["paidFE"],"background":cohort["background"]})
        for p,row in enumerate(cohort["parents"]):
            parent=row["parent"];encoded=[",".join(map(str,parent["objectives"]))]+[",".join(map(str,parent[k])) for k in ("JS","FA","MA","WA")]
            for rep in REPS:
                noise=int(np.random.default_rng(rep+s*1009+p*37).integers(1,2**62))
                factories=np.random.default_rng(noise).integers(int(stem.split("_")[2]),size=8)
                for arm in ARMS:
                    id=f"s{s}-p{p}-r{rep}-{arm}"
                    lines.append("\t".join(map(str,[id,arm,noise,LOCAL_FE,*encoded])))
                    path=folder/"probe/ledgers"/(id+".csv")
                    with path.open("x",newline="",encoding="utf-8") as stream:
                        writer=csv.writer(stream,lineterminator="\n");writer.writerow(("visit","group","round","factory","paid","restarts"))
                        writer.writerow((1,1,-1,-1,2,0))
                        writer.writerows((1,1,i,int(f),64,0) for i,f in enumerate(factories))
                    cases.append({"id":id,"sourceSeed":seed,"parentIndex":p,"rep":rep,"mode":arm,
                                  "constructionSeed":noise,"parent":parent,"factorySlots":factories.tolist()})
    (folder/"cases.tsv").write_text("\n".join(lines)+"\n",encoding="utf-8")
    write_once(folder/"cases.json",{"cohorts":cohorts,"cases":cases})
    return len(cases)


def analyze(root,spec):
    stem=spec["stem"];norm=spec["normalization"];folder=root/stem
    plan=rows(folder/"probe/trials.jsonl");data=__import__('json').loads((folder/"cases.json").read_text(encoding="utf-8"))
    cases={c["id"]:c for c in data["cases"]};backgrounds={c["sourceSeed"]:c["background"] for c in data["cohorts"]}
    result={};paired={}
    for trial in plan:
        case=cases[trial["id"]];arm=case["mode"];parent=case["parent"]["objectives"]
        points=np.asarray([p["objectives"] for p in trial["front"]]);base=np.vstack([backgrounds[case["sourceSeed"]],parent])/norm["scale"]
        added=float(hypervolume(np.vstack([base,points/norm["scale"]]),(1.5,)*3)-hypervolume(base,(1.5,)*3))
        value={"CmaxGain":float((parent[0]-np.min(points[:,0]))/parent[0]),"addedHV":max(0,added),
               "retainedCmaxGain":float((parent[0]-trial["retained"]["objectives"][0])/parent[0]),"acceptedTies":trial["tiePolicy"]["acceptedTies"]}
        result.setdefault(arm,[]).append(value)
        paired[(case["sourceSeed"],case["parentIndex"],case["rep"],arm)]=value
        actual=list(csv.reader((folder/"probe/actual-ledgers"/trial["id"]/"local-ledger.csv").open(encoding="utf-8")))[1:]
        expected=list(csv.reader((folder/"probe/ledgers"/(trial["id"]+".csv")).open(encoding="utf-8")))[1:]
        assert [r[:-1] for r in actual]==[r[:-1] for r in expected]
    means={a:{k:float(np.mean([v[k] for v in values])) for k in ("CmaxGain","addedHV","retainedCmaxGain","acceptedTies")} for a,values in result.items()}
    parent_wins={a:0 for a in ("STRICT","COST_LEX")}
    for seed in SOURCE_SEEDS:
        for p in range(8):
            for control in parent_wins:
                diff=np.mean([paired[(seed,p,r,"FACTORY_LEX")]["CmaxGain"]-paired[(seed,p,r,control)]["CmaxGain"] for r in REPS])
                parent_wins[control]+=bool(diff>1e-12)
    f,b,c=(means[a] for a in ARMS[1:2]+ARMS[:1]+ARMS[2:])
    passed=b["CmaxGain"]>1e-9 and f["CmaxGain"]>=b["CmaxGain"]*1.1 and f["CmaxGain"]>c["CmaxGain"] \
        and all(n>=9 for n in parent_wins.values()) and f["addedHV"]>=b["addedHV"]
    return {"stem":stem,"means":means,"parentWinsOf16":parent_wins,"eligibleForClosedLoop":bool(passed),"trials":len(plan)}
