"""Summaries preserve profile/target separation and paired instance structure."""
from __future__ import annotations

import numpy as np
from .statistics import paired_bootstrap


def mean_present(rows, field):
    values = [row[field] for row in rows if row[field] is not None]
    return float(np.mean(values)) if values else None


def summarize(rows, cases, accounting, protocol):
    fields = protocol["metrics"] + ["cost_proxy_ms", "accepted_gain_per_proxy_ms"]
    groups, comparisons = [], []
    for profile in protocol["profiles"]:
        for target in protocol["targets"]:
            subset = [r for r in rows if r["profile"] == profile["name"] and r["target"] == target]
            for method in protocol["methods"]:
                selected = [r for r in subset if r["method"] == method]
                groups.append({"profile": profile["name"], "target": target, "method": method,
                               "parents": len(selected), **{field: mean_present(selected, field) for field in fields},
                               "defined_rank_cases": sum(r["rank_spearman"] is not None for r in selected)})
            for right in ("time_only", "random"):
                for metric in ("accepted_gain", "accepted_gain_per_proxy_ms"):
                    comparisons.append({"profile": profile["name"], "target": target,
                                        "left": "fatigue_adjoint", "right": right, "metric": metric,
                                        **paired_bootstrap(subset, "fatigue_adjoint", right, metric)})
    return {"status": "complete", "parents": len(cases), "candidate_truth_evaluations": len(cases) * protocol["candidate_count"],
            "full_decode_accounting": dict(accounting), "groups": groups, "paired_comparisons": comparisons,
            "cases": cases, "interpretation_limits": [
                "synthetic fatigue and reconstructed setup/standby; not author benchmark replication",
                "random parents, first-stage same-factory two-job edits only",
                "all-candidate truth and diagnostic timing are offline costs, not optimizer FE",
                "cost efficiency is one-decision proxy; no equal-time optimizer or Pareto/HV claim",
                "six instance clusters, descriptive intervals; correlated objective directions not independent trials"]}


def markdown_report(summary):
    lines = ["# 动态疲劳机制诊断 v1", "", "这是独立机制验证，不涉及整套算法改动。三个选择器对同一候选池评分；先固定预测与平局集合，再完整重解码全部候选核验。", "",
             f"完成 {summary['parents']} 个父本/疲劳场景，完整核验 {summary['candidate_truth_evaluations']} 个候选。三目标的归一化尺度固定为各自父本目标值；收益为相对于父本的标量下降量。", "",
             "`accepted_gain` 是统一拒绝变差后的期望收益；random 为均匀选择全部候选的精确期望，预测平局也均匀处理。`time_only` 在 Cmax 方向是普通关键路径，其他目标是对应的时间通道控制。", "",
             "|场景|方向|方法|Spearman|改善概率|接受收益 %|成本代理 ms|收益/成本 %/ms|", "|---|---|---|---:|---:|---:|---:|---:|"]
    for row in summary["groups"]:
        rank = "—" if row["rank_spearman"] is None else f"{row['rank_spearman']:.3f}"
        lines.append(f"|{row['profile']}|{row['target']}|{row['method']}|{rank}|{row['improvement_probability']:.3f}|{100*row['accepted_gain']:.4f}|{row['cost_proxy_ms']:.3f}|{100*row['accepted_gain_per_proxy_ms']:.4f}|")
    lines += ["", "配对差及分层 bootstrap 95% 区间见 summary.json 的 paired_comparisons；按场景和方向分开，未把四个方向当作独立重复。这里只作机制诊断。", "",
              "## 成本口径", "", "指导选择代理成本：父本与子本各一次 trace 解码，加候选生成、伴随、局部 defect、评分与选择；随机：父子各一次 minimal 解码、候选生成与均匀选择。分量分别取5次预热后测量的中位数。没有模拟完整搜索，也没有将全候选事后核验免费计入在线算法。", "",
              "全解码调用（包含每项一次预热）：", ""]
    lines.extend(f"- {purpose}: {count}" for purpose, count in summary["full_decode_accounting"].items())
    lines += ["", "## 边界", "", "- SUT 是固定 seed 的 U[1,9] 重建，standby=1；疲劳参数为合成强弱场景，无实测人体数据。", "- 最早开工、append-only、后阶段 ECT/FAM；没有插空、右移、主动休息或疲劳硬阈值。", "- 局部 defect 使用旧前驱状态和旧伴随，后续重排/资源切换会造成预测误差；导数正确不保证大幅离散编辑预测正确。", "- 时间来自本机 Python 原型，只能评估本实现，不能直接当作 Java 或完整优化器开销。", "- 未比较 HV/IGD+，未调整原 Java 基线，不能据此宣称达到期刊发表标准。", ""]
    return "\n".join(lines)
