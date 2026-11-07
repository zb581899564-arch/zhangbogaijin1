"""Readable tables from frozen records; no additional search or tuning."""
from pathlib import Path
import json
import sys


def render(summary):
    lines = ["# 受影响工厂与不变前缀增量重算 v4", "",
             "先通过独立旧seed的8640个C/v/费用逐位一致检查，再运行新seed性能实验。1800条链为独立局部机制验证，Java与整套多目标算法未改。", "",
             "主要限时单元为强疲劳快恢复、TEC、0.25秒，每父本3次时钟重复；先在父本内平均，再做6实例×5seed配对统计，独立父本数仍为30。越界改善不计收益，尾部费用计入实际收益率。", "",
             "## 主要单元的四种主方法", "", "|方法|平均收益 %|实际耗时 ms|准时完成决策|缓存平均q|真实重算/等价完整工序 %|", "|---|---:|---:|---:|---:|---:|"]
    for row in summary["groups"]:
        if (row["mode"], row["profile"], row["target"]) != ("time", "strong_fast_recovery", "TEC") or row["method"].endswith("_full"):
            continue
        q = "—" if row["reuse"] is None else f"{row['reuse']['mean_q']:.3f}"
        fraction = row["work"]["recomputed_fraction"]
        work = "—" if fraction is None else f"{100*fraction:.2f}"
        lines.append(f"|{row['method']}|{100*row['gain']:.4f}|{row['elapsed_ns']/1e6:.3f}|{row['on_time_decisions']:.2f}|{q}|{work}|")
    lines += ["", "## 主要单元的配对差", "", "收益差按百分点显示；收益率差按百分点/秒。区间仅作机制描述。", "",
              "|对照|指标|平均差|95%区间|", "|---|---|---:|---|"]
    for row in summary["paired_comparisons"]:
        if (row["mode"], row["profile"], row["target"]) == ("time", "strong_fast_recovery", "TEC"):
            interval = row["bootstrap_95_interval"]
            lines.append(f"|{row['right']}|{row['metric']}|{100*row['mean_difference']:.5f}|[{100*interval[0]:.5f}, {100*interval[1]:.5f}]|")
    lines += ["", "## 同FE实现消融", "", "每个方法30对完整/增量实现的分数和轨迹须逐项相同，计时包含各自缓存维护。", "",
              "|方法|对数|全部一致|完整/增量总时间中位比|平均节省ms|完整/增量首阶段时间中位比|", "|---|---:|---|---:|---:|---:|"]
    for row in summary["implementation_ablation"]:
        lines.append(f"|{row['selector']}|{row['pairs']}|{row['all_trajectories_identical']}|{row['median_full_over_incremental_time']:.4f}|{row['mean_elapsed_saved_ms']:.3f}|{row['median_full_over_incremental_stage0']:.4f}|")
    lines += ["", "## 组件校准", "", "16候选初始池，1次预热+5次重复；独立计时不反馈搜索。", "", "|组件|平均ms|", "|---|---:|"]
    for name, value in summary["component_calibration"].items():
        lines.append(f"|{name}|{value['mean_ms']:.5f}|")
    lines += ["", "## 全部预算/场景/方向", "", "完整实现控制只有repeat0，不能与三次平均直接混用；同repeat实现比较另存summary.json。", "",
              "|预算|场景|方向|方法|实际运行数|独立父本数|收益 %|耗时 ms|", "|---|---|---|---|---:|---:|---:|---:|"]
    for row in summary["groups"]:
        lines.append(f"|{row['mode']}|{row['profile']}|{row['target']}|{row['method']}|{row['runs']}|{row['paired_parents']}|{100*row['gain']:.4f}|{row['elapsed_ns']/1e6:.3f}|")
    lines += ["", "完整解释见[研究结果](../../docs/动态疲劳增量重算-v4.md)。公共加载、磁盘输出、离线QA和组件校准不进入搜索时钟，额外调用分别记录；没有以免费真值选候选、免费缓存维护或越界改进抬高成绩。", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    path = Path(sys.argv[1])
    summary = json.loads((path / "summary.json").read_text(encoding="utf-8"))
    with (path / "report.md").open("x", encoding="utf-8") as stream:
        stream.write(render(summary))
    print("Saved report from completed records.")
