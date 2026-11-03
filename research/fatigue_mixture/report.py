"""All primary strata/budgets, plus complete machine-readable controls."""
from .records import save
from .summary import summarize
from .audit import audit


def primary(row):
    return row["split"] == "confirmation" and row["model"] == "strong_fast"


def write(output, summary):
    lines = ["# v9 固定50/50普通邻域混合", "", "主单元：8个全新N=4合成实例、强快疲劳TEC。beta0/慢恢复与4个解释实例全部保留在summary.json，不据单一预算选比例。", "",
        "## 精确固定父本覆盖/概率", "", "交换重绑定为普通N2子集，混合保留N2支持集，不产生普通复合之外的新终点。概率对应固定父本重复抽样，非在线链效果。", "",
        "|规则|可改善/严格父本|N2改善终点覆盖均值|P16均值|P32均值|", "|---|---|---|---|---|"]
    for r in summary["coverage"]:
        if primary(r):
            lines.append(f"|{r['method']}|{r['covered_parents']}/{r['strict_parents']}|{100*r['mean_N2_improvement_coverage']:.3f}%|{100*r['mean_p16']:.3f}%|{100*r['mean_p32']:.3f}%|")
    lines += ["", "## 同FE与同时间", "", "并集障碍父本未必在每个模式都严格；各记录标明parent_strict。改善是相对初始TEC百分数，每父本平均3seed。", "",
        "|父本层|预算|规则|平均改善%|完整FE均值|实际ms均值|最大超时ms|两算子均有接收/运行数|", "|---|---|---|---|---|---|---|---|"]
    for r in summary["search"]:
        if primary(r):
            budget = "33FE" if r["mode"] == "FE" else f"{r['seconds']}s"
            lines.append(f"|{r['stratum']}|{budget}|{r['method']}|{r['mean_gain_pct']:.4f}|{r['mean_full_FE']:.2f}|{r['mean_ms']:.3f}|{r['max_overrun_ms']:.3f}|{r['both_families_accepted_runs']}/{r['runs']}|")
    lines += ["", "## 实例配对差：混合减单用", "", "8实例为配对单元，均值差为百分点，未把seed或状态当独立样本。", "",
        "|父本层|预算|混合|单用|平均差百分点|8实例胜/平/负|", "|---|---|---|---|---|---|"]
    for r in summary["comparisons"]:
        if primary(r):
            budget = "33FE" if r["mode"] == "FE" else f"{r['seconds']}s"
            lines.append(f"|{r['stratum']}|{budget}|{r['a']}|{r['b']}|{r['mean_difference_pp']:.4f}|{r['wins']}/{r['ties']}/{r['losses']}|")
    c = summary["completion"]["counts"]
    lines += ["", "## 验证与成本", "", f"局部链{c['search_runs']}条，新完整调用{c['total_new_full_calls']}次，其中搜索{c['search_full']}次，新普查{c['census_full']}次；复用旧普查{c['reused_census_rows']}行。主实验含源码冻结{summary['completion']['wall_ns']/1e9:.3f}秒，审计另列audit.json。", "",
        "全部返回解独立重算并检查可行性；所有晚完成子本计费而不接收。实验为合成微例TEC局部机制诊断，覆盖事实不等于新颖性、整体多目标性能或疲劳信息贡献。没有修改共享物理核心或整套算法。"]
    (output/"report.md").write_text("\n".join(lines)+"\n", encoding="utf-8")


def finish(output):
    result = audit(output)
    summary = summarize(output)
    save(output/"summary.json", summary)
    write(output, summary)
    print(f"AUDIT {result['status']} REPORT {output/'report.md'}", flush=True)
