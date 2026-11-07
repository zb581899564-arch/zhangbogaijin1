"""Render every frozen cell, including negative and migration results."""
import json
from .records import save


NAMES = {"direct": "直接继承", "cheap": "廉价评分", "time": "时间边界", "fatigue": "疲劳边界", "random": "随机"}


def run(output):
    s = json.loads((output/"summary.json").read_text(encoding="utf-8"))
    c = s["completion"]
    lines = ["# 接收状态条件化教师结构学习 v6", "",
        "教师为付费top2-of8独立精英编码，未运行整套PSO。全部选择规则共享同池生成/合法性/去重；所有选中子本在接收端完整真实解码。FA迁移边界仍冻结旧后阶段拓扑。", "",
        "## 完整性与费用", "", f"完成{c['calls']['runs']}条运行，520个同池case。初始与8次教师完整评价均计入每条run；snapshot为10FE，固定24决策为33FE，限时FE自然不同。", "",
        f"在线搜索实际合计{c['algorithm_elapsed_ns_sum']/1e9:.3f}s，整轮墙钟{c['experiment_wall_ns']/1e9:.3f}s，JSON序列化/写入/flush累计{c['json_io_ns']/1e9:.3f}s。离线真值、最终QA与池再生不反馈搜索，调用数在completion.json。", "",
        "## 主比较：FA固定、2工件、TEC", "",
        "12项为同池一次选择/固定24/0.5秒三个层级的4个预定对照，统一Holm修正。区间为10000次实例→seed层级bootstrap95，未修正；精确单侧配对检验枚举2^13种实例符号。", "",
        "|层级|比较|收益差(pp)|95%区间(pp)|实例胜/平/负|Holm p|", "|---|---|---:|---|---|---:|"]
    for r in s["primary_comparisons"]:
        lo, hi = r["bootstrap_95_interval"]
        lines.append(f"|{r['mode']}|{NAMES[r['left']]}−{NAMES[r['right']]}|{100*r['mean_difference']:+.4f}|[{100*lo:+.4f},{100*hi:+.4f}]|{r['wins']}/{r['ties']}/{r['losses']}|{r['holm_adjusted_p']:.6g}|")
    lines += ["", "## 所有实际运行单元", ""]
    for g in s["groups"]:
        lines += [f"### {g['mode']} / {g['target']} / {g['regime']} / block={g['block_size']}", "",
            "|方法|改善(%)|Cmax/TEC/TWC改善(%)|平均实际ms|完整FE|准时决策|教师bank时间占比(%)|", "|---|---:|---|---:|---:|---:|---:|"]
        for r in g["methods"]:
            objective = "/".join(f"{100*x:.3f}" for x in r["mean_objective_gains"])
            lines.append(f"|{NAMES[r['method']]}|{100*r['gain']:.4f}|{objective}|{r['elapsed_ns']/1e6:.3f}|{r['full_decodes']:.2f}|{r['on_time_decisions']:.2f}|{100*r['phase_time_fractions'].get('teacher_bank',0):.2f}|")
        lines.append("")
    lines += ["## 同池真值：平局期望与预测误差（探索性）", "",
        "只在全部五方法选择后计算池中所有候选真值。实际选择收益为主指标，均匀平局期望用于解释选择波动；direct自身教师目标不是接收端delta，故不报告其delta MAE。", ""]
    for g in s["shared_pool_mechanism"]:
        lines += [f"### {g['target']} / {g['regime']} / block={g['block_size']}", "",
            f"同池case={g['pools']}，平均唯一候选={g['mean_candidates']:.3f}，fallback noop比例={100*g['noop_fraction']:.3f}%，拒绝非法proposal={g['illegal_proposals']}。", "",
            "|方法|实际接受收益(%)|均匀平局期望(%)|平均排序相关|delta MAE|", "|---|---:|---:|---:|---:|"]
        for r in g["methods"]:
            corr = "NA" if r["rank_spearman"] is None else f"{r['rank_spearman']:.4f}"
            error = "NA" if r["mean_abs_prediction_error"] is None else f"{r['mean_abs_prediction_error']:.6f}"
            lines.append(f"|{NAMES[r['method']]}|{100*r['realized_gain']:.4f}|{100*r['accepted_gain']:.4f}|{corr}|{error}|")
        lines.append("")
    lines += ["## 结论边界", "", "仅13实例簇、5个新seed、每单元一次计时；仅强快恢复合成疲劳。所有非主单元对比、排序相关及收益率区间均为探索性。教师bank冻结，不等同于完整PSO不断更新的历史。模型与SUT/standby来源边界沿用v1–v5。不得由此直接推断完整协同进化、HV/IGD+或发表级总体优势。", ""]
    with (output/"report.md").open("x", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(output/"report.md")
