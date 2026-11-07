"""Complete scalar-scale results, with primary family separated from controls."""
from collections import defaultdict
import json
import numpy as np
from .records import read, save
from .protocol import PROTOCOL
from .statistics import effects, holm
from .audit import audit


def summarize(output):
    groups, parents, strata = defaultdict(list), {}, defaultdict(list)
    for row in read(output,"search"):
        key = (row["model"],row["target"],row["mode"],row["seconds"],row["method"])
        parents[(row["instance"],row["parent_seed"],*key)] = row["gain"]*100
        groups[key].append({k:v for k,v in row.items() if k!="steps"} | {
            "noop_rate":np.mean([s["noop"] for s in row["steps"]]) if row["steps"] else 0.})
        for axis in ("jobs","factories","stages"):
            strata[(axis,row[axis],*key)].append((row["instance"],row["gain"]*100,row["full_decodes"]))
    summary, contrasts = [], []
    for key, rows in groups.items():
        summary.append(dict(zip(("model","target","mode","seconds","method"),key)) | {
            "runs":len(rows),"mean_gain_pct":float(np.mean([r["gain"]*100 for r in rows])),
            "mean_gain_per_second":float(np.mean([r["gain_per_second"] for r in rows])),
            "mean_full_FE":float(np.mean([r["full_decodes"] for r in rows])),
            "mean_ms":float(np.mean([r["elapsed_ns"]/1e6 for r in rows])),
            "maximum_overrun_ms":max(r["overrun_ns"]/1e6 for r in rows),
            "mean_noop_rate":float(np.mean([r["noop_rate"] for r in rows]))})
    names = sorted({r[0] for r in parents})
    for cell_no,(model,target,mode,seconds) in enumerate(sorted({k[:4] for k in groups},key=str)):
        for a in ("mix_iid","mix_alternate"):
            for b in ("plain","swap_rebind"):
                differences = [[parents[(name,seed,model,target,mode,seconds,a)]-parents[(name,seed,model,target,mode,seconds,b)]
                                for seed in PROTOCOL["parent_seeds"]] for name in names]
                primary = model=="strong_fast_recovery" and target=="TEC"
                contrast = {"model":model,"target":target,"mode":mode,"seconds":seconds,"a":a,"b":b,
                    "primary":primary,"instances":names,
                    **effects(differences,PROTOCOL["statistics"]["seed"]+cell_no*101+len(contrasts))}
                contrasts.append(contrast)
    main = [c for c in contrasts if c["primary"]]
    assert len(main)==12
    holm(main)
    stratum_rows = [dict(zip(("axis","value","model","target","mode","seconds","method"),key)) | {
        "instances":len({r[0] for r in values}),"mean_gain_pct":float(np.mean([r[1] for r in values])),
        "mean_full_FE":float(np.mean([r[2] for r in values]))} for key,values in strata.items()]
    return {"search":summary,"contrasts":contrasts,"strata":stratum_rows,
            "completion":json.loads((output/"completion.json").read_text(encoding="utf-8"))}


def write(output,summary):
    lines=["# v10 全36合格实例普通混合规模验证","","主单元为强快TEC；36实例为配对单元，每实例先平均3父本。beta0、强慢和均衡完整保留，不以其探索结果换主单元。","",
        "|模型|目标|预算|方法|平均改善%|平均完整FE|实际ms均值|最大超时ms|平均noop率|","|---|---|---|---|---|---|---|---|---|"]
    for r in summary["search"]:
        budget="65FE" if r["mode"]=="FE" else str(r["seconds"])+"s"
        lines.append(f"|{r['model']}|{r['target']}|{budget}|{r['method']}|{r['mean_gain_pct']:.4f}|{r['mean_full_FE']:.2f}|{r['mean_ms']:.3f}|{r['maximum_overrun_ms']:.3f}|{r['mean_noop_rate']:.5f}|")
    lines += ["","## 主比较12项","","|预算|A|B|平均差pp|配对层次95%区间|实例胜/平/负|Holm p|","|---|---|---|---|---|---|---|"]
    for r in summary["contrasts"]:
        if r["primary"]:
            budget="65FE" if r["mode"]=="FE" else str(r["seconds"])+"s"
            lines.append(f"|{budget}|{r['a']}|{r['b']}|{r['mean_difference_pp']:.4f}|{r['CI95_pp']}|{r['wins']}/{r['ties']}/{r['losses']}|{r['holm_p']:.6f}|")
    lines += ["","全部模型共4320局部链，完整返回解独立核验；数据含重建SUT/standby，参数为合成疲劳场景。只支持共同动态解码器下的局部标量链判断，不是作者成绩复现、完整多目标或新颖性结论。所有尾步超时计费且不接收，实际耗时包含超时；gain/sec与全部费用见summary/completion。"]
    (output/"report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def finish(project,output):
    result=audit(project,output)
    summary=summarize(output)
    save(output/"summary.json",summary)
    write(output,summary)
    print(f"AUDIT {result['status']} REPORT {output/'report.md'}",flush=True)
