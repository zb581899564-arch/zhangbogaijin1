"""Report primary confirmation outcomes and keep all other units in summary."""
from .audit import audit
from .summary import summarize
from .records import save


def primary(row):
    return row["split"] == "confirmation" and row["model"] == "strong_fast"


def write(output, summary):
    lines = ["# v8 普通交换/重绑定：独立机制诊断", "", "主单元：4个全新N=4合成实例，强快疲劳TEC。解释组与其他模式全部保留在summary.json。", "",
        "## 严格障碍的精确覆盖", "", "|规则|有改善的父本/全部严格父本|普通N2改善终点覆盖均值|精确P16均值|", "|---|---|---|---|"]
    for r in summary["coverage"]:
        if primary(r):
            lines.append(f"|{r['method']}|{r['covered_parents']}/{r['strict_parents']}|{100*r['mean_improving_N2_coverage']:.3f}%|{100*r['mean_p16']:.3f}%|")
    lines += ["", "## 同FE和真实时间分别报告", "", "均值为初始TEC相对改善，障碍层/均匀层分开；完整FE包含父本，部分首阶段调用另计。", "",
        "|父本层|预算|方法|平均改善%|平均完整FE|平均部分调用|平均ms|最大超时ms|", "|---|---|---|---|---|---|---|---|"]
    for r in summary["search"]:
        if primary(r):
            budget = "33FE" if r["mode"] == "FE" else f"{r['seconds']}s"
            lines.append(f"|{r['stratum']}|{budget}|{r['method']}|{r['mean_gain_pct']:.4f}|{r['mean_full_FE']:.2f}|{r['mean_partial_calls']:.2f}|{r['mean_ms']:.3f}|{r['max_overrun_ms']:.3f}|")
    lines += ["", "## 实例配对差", "", "先平均3seed，再在实例内平均父本；下表combined不把24次重复当24个实例。仅4实例，不作显著性主张。", "",
        "|预算|A|B|A-B平均百分点|实例胜/平/负|", "|---|---|---|---|---|"]
    for r in summary["comparisons"]:
        if primary(r) and r["stratum"] == "combined":
            budget = "33FE" if r["mode"] == "FE" else f"{r['seconds']}s"
            lines.append(f"|{budget}|{r['a']}|{r['b']}|{r['mean_difference_pp']:.4f}|{r['wins']}/{r['ties']}/{r['losses']}|")
    lines += ["", "## 真正同池快照", "", "同一8候选，真值只供离线分析；不反馈搜索。", "",
        "|父本层|选择规则|选中改善均值%|oracle regret均值百分点|", "|---|---|---|---|"]
    for r in summary["snapshots"]:
        if primary(r):
            lines.append(f"|{r['stratum']}|{r['method']}|{r['mean_selected_gain_pct']:.4f}|{r['mean_oracle_regret_pp']:.4f}|")
    counts = summary["completion"]["counts"]
    lines += ["", "## 成本和边界", "", f"新完整解码{counts['total_new_full_calls']}次，旧普查表复用{counts['reused_census_rows']}行；搜索{counts['search_runs']}次，搜索完整调用{counts['search_full']}次、部分调用{counts['search_partial']}次。主实验墙钟{summary['completion']['wall_ns']/1e9:.3f}秒，审计另记。", "",
        "每次最终返回解独立完整重算并验证。超时子本计费但不接收；全部时间结果和超时保留。输入/覆盖/快照/QA/磁盘写出在实验总成本中，按冻结口径不属于在线搜索时钟。beta0时间/疲劳固定FE轨迹必须相同。", "",
        "小实例局部链、条件障碍面板和TEC标量结果不代表完整多目标算法性能、一般疲劳价值或新颖性。没有修改共享解码器或Java算法。"]
    (output/"report.md").write_text("\n".join(lines)+"\n", encoding="utf-8")


def finish(output):
    result = audit(output)
    summary = summarize(output)
    save(output/"summary.json", summary)
    write(output, summary)
    print(f"AUDIT {result['status']} REPORT {output/'report.md'}", flush=True)
