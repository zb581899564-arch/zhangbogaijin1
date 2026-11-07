"""Render saved v5 summaries only; does not run or tune an experiment."""
from pathlib import Path
import json
import sys


NAMES = {"cut_time": "增量＋时间", "cut_time_full": "完整首阶段＋时间", "local_time": "廉价时间",
         "cut_fatigue": "增量＋疲劳伴随", "random": "随机"}


def contrast_table(rows, adjusted):
    lines = ["|预算(s)|对照|收益差(pp)|未修正95%区间(pp)|实例胜/平/负|" + ("Holm p|" if adjusted else "单侧p（未修正）|"),
             "|---:|---|---:|---|---|---:|"]
    for r in rows:
        lo, hi = r["bootstrap_95_interval"]
        p = r["holm_adjusted_p"] if adjusted else r["one_sided_instance_signflip_p"]
        lines.append(f"|{r['budget_seconds']:g}|{NAMES[r['right']]}|{100*r['mean_difference']:+.4f}|[{100*lo:+.4f}, {100*hi:+.4f}]|"
                     f"{r['instance_wins']}/{r['instance_ties']}/{r['instance_losses']}|{p:.6g}|")
    return lines


def run(path):
    summary = json.loads((path / "summary.json").read_text(encoding="utf-8"))
    audit = json.loads((path / "audit.json").read_text(encoding="utf-8"))
    validation = json.loads((path / "validation_gate.json").read_text(encoding="utf-8"))["evidence"]
    c = summary["completion"]
    lines = ["# 精确增量＋时间通道扩展验证 v5", "",
             "本报告由保存的summary.json直接生成。全部预定正负单元均列出，不用结果筛选实例或seed；仅为共享动态疲劳解码器下的标量局部链。", "",
             "## 范围、正确性与费用", "",
             f"36个合格实例、每实例3个全新seed，共108个配对父本。先通过{validation['comparisons']}次C/v/直接费用逐位比较、{validation['parent_schedules']}个父本调度检查；"
             f"再完成{audit['chains']}条链、{audit['step_rows']}个真实决策、{audit['bitwise_trajectory_pairs']}对固定24步同轨迹检查。所有最终调度均离线完整解码核验。", "",
             f"搜索实际时间之和{c['algorithm_elapsed_ns_sum']/1e9:.3f}s；整轮墙钟{c['experiment_wall_ns']/1e9:.3f}s；"
             f"JSON序列化/写入计时{c['json_serialization_write_ns']/1e9:.3f}s。后两者不作为搜索预算，离线QA/候选再生无反馈。", "",
             "在线时钟含初始化、生成、缓存/伴随/前缀维护、全部候选评分、投影、真实选中子本完整解码、接受/失效与内存日志。末次非抢占决策越界改善不接受，越界时间进入gain/second分母。", "",
             "协议继承的两个未使用v4字段保留原字节，实际108父本与0.5/2秒预算以显式v5计划、逐链deadline为准，见protocol_metadata_clarification.json；没有更换案例或调整预算。", "",
             "## 主要单元：强疲劳快恢复、TEC", ""]
    for group in summary["groups"]:
        if group["profile"] != "strong_fast_recovery" or group["target"] != "TEC":
            continue
        lines += [f"### 预算{group['budget_seconds']:g}秒", "", "|方法|TEC改善(%)|Cmax/TWC改善(%)|实际平均(ms)|平均越界(ms)|准时决策|首阶段/缓存时间(%)|", "|---|---:|---|---:|---:|---:|---:|"]
        for r in group["methods"]:
            objective = r["mean_objective_gains"]
            lines.append(f"|{NAMES[r['method']]}|{100*r['mean_gain']:.4f}|{100*objective[0]:.3f}/{100*objective[2]:.3f}|{r['mean_elapsed_ms']:.3f}|{r['mean_overrun_ms']:.3f}|"
                         f"{r['mean_on_time_decisions']:.2f}|{100*r['stage0_time_fraction']:.2f}/{100*r['cache_time_fraction']:.2f}|")
        lines.append("")
    lines += ["主方法减去各对照；36个实例均值做配对单侧符号翻转，8项主比较统一Holm修正。区间为10000次实例→seed层级bootstrap，未作多重修正；3个seed不当作3个独立实例。", ""]
    lines += contrast_table(summary["primary_comparisons"], True)
    lines += ["", "实际收益率差含末次越界全部费用，单位pp/s；以下区间为描述性，不另作多重比较优势检验。", "",
              "|预算(s)|对照|收益率差(pp/s)|95%区间(pp/s)|", "|---:|---|---:|---|"]
    for r in summary["primary_rate_comparisons_descriptive"]:
        lo, hi = r["bootstrap_95_interval"]
        lines.append(f"|{r['budget_seconds']:g}|{NAMES[r['right']]}|{100*r['mean_difference']:+.4f}|[{100*lo:+.4f}, {100*hi:+.4f}]|")
    lines += ["", "主方法的实际递推/不变前缀/未变工厂工序比例，仍包含扫描、复制、汇总与投影费用：", "",
              "|预算(s)|实际递推(%)|前缀复用(%)|未变工厂(%)|", "|---:|---:|---:|---:|"]
    for group in summary["groups"]:
        if group["profile"] == "strong_fast_recovery" and group["target"] == "TEC":
            fractions = next(r for r in group["methods"] if r["method"] == "cut_time")["work_fractions"]
            lines.append(f"|{group['budget_seconds']:g}|{100*fractions['recomputed_ops']:.3f}|{100*fractions['reused_prefix_ops']:.3f}|{100*fractions['unchanged_factory_ops']:.3f}|")
    lines += ["", "## 固定FE实现对照", "", "```json", json.dumps(summary["implementation_ablation"], ensure_ascii=False, indent=2), "```", "",
              "## 预定规模和新实例分层（描述性）", "", "|预算(s)|分层|对照|收益差(pp)|实例胜/平/负|", "|---:|---|---|---:|---|"]
    for r in summary["predeclared_strata_descriptive"]:
        lines.append(f"|{r['budget_seconds']:g}|{r['stratum']}|{NAMES[r['right']]}|{100*r['mean_difference']:+.4f}|{r['instance_wins']}/{r['instance_ties']}/{r['instance_losses']}|")
    lines += ["", "## 补充单元（探索性，未进行主比较检验族的修正）", ""]
    for group in summary["groups"]:
        if group["profile"] == "strong_fast_recovery" and group["target"] == "TEC":
            continue
        lines += [f"### {group['profile']} / {group['target']}", "", "|方法|标量改善(%)|Cmax/TEC/TWC改善(%)|实际平均(ms)|", "|---|---:|---|---:|"]
        for r in group["methods"]:
            objective = "/".join(f"{100*v:.3f}" for v in r["mean_objective_gains"])
            lines.append(f"|{NAMES[r['method']]}|{100*r['mean_gain']:.4f}|{objective}|{r['mean_elapsed_ms']:.3f}|")
        selected = [r for r in summary["secondary_comparisons_exploratory"] if r["profile"] == group["profile"] and r["target"] == group["target"]]
        lines += [""] + contrast_table(selected, False) + [""]
    lines += ["## 限制", "", "SUT/standby为公开重建，疲劳参数为合成场景；每实例只有3seed、每计时单元只跑一次，无法消除所有系统时钟噪声。"
              "结果不等于原论文成绩复现，不代表原始完整多目标算法或HV/IGD+优势；实现提速本身不证明论文创新性。Java/PSO/QLS/QGS均未修改。", ""]
    with (path / "report.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
    print(path / "report.md")


if __name__ == "__main__":
    run(Path(sys.argv[1]))
