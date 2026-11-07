"""Post-hoc presentation of all saved strata; no new fits or decoder calls."""
from collections import defaultdict
from pathlib import Path
import json
import sys
import numpy as np
from .experiment import save


def combined_errors(summary):
    indexed = defaultdict(list)
    for row in summary["error_strata"]:
        indexed[row["pool"], row["target"], row["stratum"]].append(row)
    result = []
    for (pool, target, stratum), rows in indexed.items():
        count = sum(r["candidates"] for r in rows)
        denominator = sum(r["mean_abs_actual"] * r["candidates"] for r in rows)
        methods = {}
        for method in rows[0]["methods"]:
            error_sum = sum(r["methods"][method]["candidate_mae"] * r["candidates"] for r in rows)
            methods[method] = {"mae": error_sum / count, "wape": error_sum / denominator if denominator > 1e-14 else None}
        components = {k: sum(r["mean_abs_error_components"][k] * r["candidates"] for r in rows) / count
                      for k in rows[0]["mean_abs_error_components"]}
        total = sum(components.values())
        result.append({"pool": pool, "target": target, "stratum": stratum, "candidates": count,
                       "methods": methods, "components": components,
                       "component_abs_fraction": {k: v / total if total else None for k, v in components.items()}})
    return result


def combined_selections(summary):
    indexed = defaultdict(list)
    for row in summary["selection_groups"]:
        indexed[row["pool"], row["target"], row["method"]].append(row)
    result = []
    for (pool, target, method), rows in indexed.items():
        result.append({"pool": pool, "target": target, "method": method,
                       "accepted_gain": float(np.mean([r["accepted_gain"] for r in rows])),
                       "rank_spearman": float(np.mean([r["rank_spearman"] for r in rows])) if method != "random" else None,
                       "cost_by_q": {q: float(np.mean([r["cost_ms_by_q"][q] for r in rows])) for q in rows[0]["cost_ms_by_q"]},
                       "rate_by_q": {q: float(np.mean([r["rate_by_q"][q] for r in rows])) for q in rows[0]["rate_by_q"]}})
    return result


def markdown(value):
    lines = ["# 动态疲劳拓扑诊断 v2", "", "以下为全部三档疲劳场景的描述性合并；分场景结果和配对区间见summary.json。固定协议与所有预测在真值之前保存，未改整套算法。", "",
             "## 均衡方向分层预测误差", "", "WAPE=总绝对误差/总绝对真实变化；表内按百分比显示，超过100%表示误差总量大于真实变化总量。probe按全图，合法编辑按后阶段图分类。cut是额外计算的诊断对照，没有当作廉价选择器。", "",
             "|池|分层|数量|疲劳伴随WAPE %|时间通道WAPE %|cut WAPE %|", "|---|---|---:|---:|---:|---:|"]
    for row in value["combined_errors"]:
        if row["target"] != "balanced":
            continue
        display = lambda m: "—" if row["methods"][m]["wape"] is None else f"{100*row['methods'][m]['wape']:.6f}"
        lines.append(f"|{row['pool']}|{row['stratum']}|{row['candidates']}|{display('fatigue_adjoint')}|{display('time_only')}|{display('cut')}|")
    lines += ["", "## 同一完整池内的均衡方向选择", "", "收益为统一拒绝变差后的期望归一化下降。成本是组件代理，q只在父本不变时成立；probe是敏感性干预，不能作为合法搜索收益。", "",
              "|池|方法|接受收益 %|成本q=1 ms|收益率q=1 %/ms|收益率q=16 %/ms|", "|---|---|---:|---:|---:|---:|"]
    for row in value["combined_selections"]:
        if row["target"] == "balanced":
            lines.append(f"|{row['pool']}|{row['method']}|{100*row['accepted_gain']:.7f}|{row['cost_by_q']['1']:.4f}|{100*row['rate_by_q']['1']:.7f}|{100*row['rate_by_q']['16']:.7f}|")
    lines += ["", "解释及研究判断见[结果文档](../../docs/动态疲劳拓扑诊断-v2.md)。六个实例簇、许多相关比较均作描述；未验证长期搜索效果、自动拓扑门控、实际父本复用频率或HV/IGD+。", ""]
    return "\n".join(lines)


def run(path):
    summary = json.loads((path / "summary.json").read_text(encoding="utf-8"))
    value = {"scope": "post-hoc descriptive presentation of all frozen error/selection groups",
             "combined_errors": combined_errors(summary), "combined_selections": combined_selections(summary)}
    save(path / "review.json", value)
    with (path / "report.md").open("x", encoding="utf-8") as stream:
        stream.write(markdown(value))
    print("Saved descriptive review and report; no new decodes.")


if __name__ == "__main__":
    run(Path(sys.argv[1]))
