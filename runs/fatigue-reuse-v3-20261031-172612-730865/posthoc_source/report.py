"""Render all predeclared cells from saved v3 summaries, without new search."""
from pathlib import Path
import json
import sys


def render(summary):
    lines = ["# 首阶段真实重算与实际伴随复用 v3", "",
             "独立局部链，固定24次子本评价及0.25秒两种预算。所有搜索耗时均实测；JSON磁盘输出、公共输入加载、独立组件校准和离线QA另计。截止后完成的改进未计入限时收益，超时尾部耗时计入实际收益率。", "",
             "## 预先指定主要单元：强疲劳快恢复、TEC、0.25秒", "",
             "|方法|最终收益 %|完整耗时 ms|准时完成决策|实际平均q|q>=4的epoch比例 %|首阶段时间占比 %|",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for row in summary["groups"]:
        if (row["mode"], row["profile"], row["target"]) != ("time", "strong_fast_recovery", "TEC"):
            continue
        reuse = row["reuse"]
        q = "—" if reuse is None else f"{reuse['mean_q']:.3f}"
        fraction = "—" if reuse is None else f"{100*reuse['fraction_q_ge4']:.2f}"
        lines.append(f"|{row['method']}|{100*row['gain']:.4f}|{row['elapsed_ms']:.3f}|{row['on_time_decisions']:.2f}|{q}|{fraction}|{100*row['stage0_time_fraction']:.2f}|")
    lines += ["", "主要单元的完整疲劳边界法配对差（六实例×五seed分层bootstrap2000，描述性）：", "",
              "|对照|指标|平均差|95%区间|", "|---|---|---:|---|"]
    for row in summary["paired_comparisons"]:
        if (row["mode"], row["profile"], row["target"]) == ("time", "strong_fast_recovery", "TEC"):
            interval = row["bootstrap_95_interval"]
            lines.append(f"|{row['right']}|{row['metric']}|{row['mean_difference']:.8f}|[{interval[0]:.8f}, {interval[1]:.8f}]|")
    lines += ["", "## 全部场景与预算", "", "|预算|疲劳场景|方向|方法|最终收益 %|耗时 ms|收益 %/s|实际q|", "|---|---|---|---|---:|---:|---:|---:|"]
    for row in summary["groups"]:
        q = "—" if row["reuse"] is None else f"{row['reuse']['mean_q']:.3f}"
        lines.append(f"|{row['mode']}|{row['profile']}|{row['target']}|{row['method']}|{100*row['gain']:.4f}|{row['elapsed_ms']:.3f}|{100*row['gain_per_second']:.4f}|{q}|")
    lines += ["", "## 独立组件校准", "", "每个16候选初始池核对数值首阶段与旧日志版一致，组件一次预热+5次测量；这些重复不反馈搜索。", "", "|组件|各case中位数的平均 ms|", "|---|---:|"]
    for name, value in summary["calibration"].items():
        lines.append(f"|{name}|{value['mean_ms']:.5f}|")
    ablation = summary["reuse_ablation"]
    lines += ["", "## 实际缓存消融", "",
              f"{ablation['pairs']}对强疲劳快恢复TEC固定24步的缓存/每步重建轨迹全部一致：{ablation['all_trajectories_identical']}。平均实际q={ablation['mean_cached_q']:.3f}，平均少建{ablation['mean_builds_saved']:.3f}次伴随；每步重建/缓存总时间比的中位数={ablation['median_fresh_over_cached_time']:.3f}，平均总时间节省={ablation['mean_elapsed_saved_ms']:.3f}ms。", "",
              "完整epoch分布及接受终止/预算右删失统计保存在summary.json。最终解释见[研究结果](../../docs/动态疲劳成本与复用-v3.md)。这不是整套算法或HV/IGD+结论，疲劳参数与缺失数据均为公开合成/重建。", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    path = Path(sys.argv[1])
    summary = json.loads((path / "summary.json").read_text(encoding="utf-8"))
    with (path / "report.md").open("x", encoding="utf-8") as stream:
        stream.write(render(summary))
    print("Saved report from completed raw records.")
