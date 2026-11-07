"""Descriptive census summaries; no state-level significance or optimizer claims."""
from collections import defaultdict
import json
import numpy as np
from .audit import audit
from .records import read, save


def grouped(rows, keys):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in keys)].append(row)
    return groups


def summarize(output):
    census = list(read(output/"census.jsonl"))
    controls = list(read(output/"controls.jsonl"))
    pairs = list(read(output/"paired.jsonl"))
    result = {"census": [], "paired": [], "controls": []}
    for (jobs, model, target), rows in grouped(census, ("jobs", "model", "target")).items():
        record = {"jobs": jobs, "model": model, "target": target, "instances": len(rows)}
        for name in ("states", "N1_local_states", "weak_N2_states", "strict_N2_states", "weak_with_neutral_exit", "strict_components"):
            record[name] = sum(r[name] for r in rows)
        record["instances_with_strict"] = sum(r["strict_N2_states"] > 0 for r in rows)
        result["census"].append(record)
    for (jobs, model, target), rows in grouped(pairs, ("jobs", "dynamic_model", "target")).items():
        record = {"jobs": jobs, "dynamic_model": model, "target": target}
        for kind in ("weak", "strict"):
            record[kind] = {k: sum(r[kind][k] for r in rows) for k in rows[0][kind]}
        result["paired"].append(record)
    for (jobs, model, method), rows in grouped(controls, ("jobs", "model", "method")).items():
        record = {"jobs": jobs, "model": model, "method": method, "trials": len(rows),
                  "actual_successes": sum(r["gain"] > 1e-10 for r in rows),
                  "median_ms": float(np.median([r["elapsed_ns"]/1e6 for r in rows])),
                  "mean_gain": float(np.mean([r["gain"] for r in rows])),
                  "mean_exact_p16": float(np.mean([r["offline_exact_distribution"]["budget_success"] for r in rows]))}
        strict = [r for r in rows if r["parent_strict"]]
        record["strict_trials"] = len(strict)
        record["strict_actual_successes"] = sum(r["gain"] > 1e-10 for r in strict)
        record["strict_mean_exact_p16"] = float(np.mean([r["offline_exact_distribution"]["budget_success"] for r in strict])) if strict else None
        result["controls"].append(record)
    witnesses = list(read(output/"witnesses.jsonl"))
    result["witnesses"] = len(witnesses)
    candidates = [w for w in witnesses if w["target"] == "TEC" and w["category"] == "dynamic_only"]
    result["example"] = (candidates or witnesses or [None])[0]
    result["completion"] = json.loads((output/"completion.json").read_text(encoding="utf-8"))
    return result


def write_report(output, summary):
    counts = summary["completion"]["counts"]
    lines = ["# v7 协调障碍有限空间诊断", "", "下表按规模汇总4个预定合成实例。状态为有限空间普查，不能作为独立统计样本。", "",
             "|N|模式|目标|状态|N1局部|弱N2|封闭平台严格N2|有中性出口|有严格障碍实例数|", "|---|---|---|---|---|---|---|---|---|"]
    for row in summary["census"]:
        lines.append("|"+"|".join(str(row[k]) for k in ("jobs", "model", "target", "states", "N1_local_states", "weak_N2_states", "strict_N2_states", "weak_with_neutral_exit", "instances_with_strict"))+"|")
    lines += ["", "## 同父本TEC严格障碍的出现/消失", "", "|N|动态模式|仅beta0|仅动态|共有|均无|", "|---|---|---|---|---|---|"]
    for row in summary["paired"]:
        if row["target"] == "TEC":
            lines.append("|"+"|".join(map(str, (row["jobs"], row["dynamic_model"], *row["strict"].values())))+"|")
    lines += ["", "## 条件面板17FE普通控制", "", "面板来自三个模式TEC弱障碍并集；同实例/父本在三模式匹配。以下是条件诊断，不是全空间发生率或同时间算法优势。", "",
              "|N|模式|方法|成功/次数|17FE中位ms|精确P16均值|严格父本成功/次数|严格父本精确P16均值|", "|---|---|---|---|---|---|---|---|"]
    for r in summary["controls"]:
        p = "NA" if r["strict_mean_exact_p16"] is None else f"{r['strict_mean_exact_p16']:.4f}"
        lines.append(f"|{r['jobs']}|{r['model']}|{r['method']}|{r['actual_successes']}/{r['trials']}|{r['median_ms']:.3f}|{r['mean_exact_p16']:.4f}|{r['strict_actual_successes']}/{r['strict_trials']}|{p}|")
    lines += ["", "## 成本与证据", "", f"完整解码共{counts['total_full_calls']}次；其中普查{counts['census_full']}次、普通控制{counts['control_trials']}×17次；证书{summary['witnesses']}条。实验含源码冻结总墙钟{summary['completion']['wall_ns']/1e9:.3f}秒，读回审计另记audit.json。", "", "```json", json.dumps(counts, indent=2), "```", "",
              "beta0也可能有协调障碍；dynamic-only只表示同一父本分类发生变化。两步障碍可被普通复合覆盖，不构成新算子独立贡献。标量障碍的Pareto检查只覆盖证书。完整物理/输入/分类/合法路径见npz与jsonl，在线抽样不读取普查表。未修改共享解码器、Java或整套算法。"]
    (output/"report.md").write_text("\n".join(lines)+"\n", encoding="utf-8")


def finish(output):
    audit_result = audit(output)
    summary = summarize(output)
    save(output/"summary.json", summary)
    write_report(output, summary)
    print(f"AUDIT {audit_result['status']} REPORT {output/'report.md'}", flush=True)
