"""Read-only supplement of all registered PA capability terminal fronts."""
from pathlib import Path

import numpy as np

from run_long_budget_bridge import read, rows, hypervolume, igd_plus, nondominated
from research.dynamic_benchmark.tri_indicators import (
    bidirectional_coverage, directional_description, objective_set,
)
from research.semantic_repair.evidence import digest

PRIMARY = "PA_JOINT"


def require_close(actual, expected, context):
    if not np.allclose(actual, expected, rtol=1e-12, atol=1e-12):
        raise ValueError("Frozen metric mismatch: " + context)


def terminal_front(source, stem, seed, phase, arm, endpoint, identities):
    path = source / stem / str(seed) / (phase + "-" + arm) / "anytime.jsonl"
    identities[str(path)] = digest(path)
    point, = [r for r in rows(path) if r["checkpointKind"] == "FE"
              and r["checkpoint"] == endpoint and r["reached"]]
    if point["fe"] != endpoint:
        raise ValueError("Endpoint archive FE mismatch: " + str(path))
    result = objective_set(point["front"])
    if not len(result):
        raise ValueError("Missing nonempty endpoint front: " + str(path))
    return result


def collect_instance(source, phase, spec, plan, frozen, identities):
    stem, norm = spec["stem"], spec["normalization"]
    endpoint = plan["fe100k"] if phase == "FE100K" else plan["fe500k"]
    arms = list(plan["arms"])
    raw, normalized = {}, {}
    for seed in plan["seeds"]:
        for arm in arms:
            key = seed, arm
            raw[key] = terminal_front(source, stem, seed, phase, arm, endpoint, identities)
            normalized[key] = (raw[key] - norm["lower"]) / norm["scale"]
    # Match the source experiment's reference rule, independently per budget.
    reference = nondominated(np.vstack(list(normalized.values())))
    old = {(r["seed"], r["arm"]): r for r in frozen["observations"]}
    observations = []
    for (seed, arm), front in normalized.items():
        previous = old[seed, arm]
        for ref in (1.25, 1.5, 2.):
            require_close(hypervolume(front, (ref,) * 3), previous["HV"][str(ref)], f"{stem}/{seed}/{arm}/HV{ref}")
        require_close(igd_plus(front, reference), previous["IGDplus"], f"{stem}/{seed}/{arm}/IGD+")
        require_close(raw[seed, arm].min(axis=0), previous["objectiveMin"], f"{stem}/{seed}/{arm}/extremes")
        observations.append(previous)
    comparisons = []
    for old_comparison in frozen["comparisons"]:
        control = old_comparison["control"]
        pairs = []
        for previous in old_comparison["pairs"]:
            seed = previous["seed"]
            c = bidirectional_coverage(raw[seed, PRIMARY], raw[seed, control])
            description = directional_description(previous["HVEffectPct"]["1.5"],
                previous["IGDplusSymmetricWorseningPct"], c["C_A_B"], c["C_B_A"])
            pairs.append({**previous, "coverage": c, "directions": description})
        med_ab = float(np.median([r["coverage"]["C_A_B"] for r in pairs]))
        med_ba = float(np.median([r["coverage"]["C_B_A"] for r in pairs]))
        median_description = directional_description(old_comparison["medianHVEffectPct"]["1.5"],
            old_comparison["medianIGDplusSymmetricWorseningPct"], med_ab, med_ba)
        comparisons.append({"control": control, "pairs": pairs,
            "medianHVEffectPct": old_comparison["medianHVEffectPct"],
            "medianIGDplusSymmetricWorseningPct": old_comparison["medianIGDplusSymmetricWorseningPct"],
            "median_C_A_B": med_ab, "median_C_B_A": med_ba,
            "medianDirections": median_description,
            "pairDirectionalLabels": [r["directions"]["label"] for r in pairs]})
    return {"stem": stem, "endpointFE": endpoint, "normalization": norm,
        "empiricalReferenceSize": len(reference), "observations": observations,
        "comparisons": comparisons, "recomputedFrozenHV_IGDplusConsistent": True}


def analyze_source(source, phase, identities):
    for name in ("protocol.json", "status.json", "analysis.json", phase.lower() + "-analysis.json"):
        path = source / name
        identities[str(path)] = digest(path)
    clarification = source / "PROTOCOL_SCOPE_CLARIFICATION.json"
    if clarification.exists():
        identities[str(clarification)] = digest(clarification)
    if read(source / "status.json")["status"] != "COMPLETE":
        raise ValueError("Source run is not complete")
    plan, frozen = read(source / "protocol.json"), read(source / (phase.lower() + "-analysis.json"))
    by_stem = {row["stem"]: row for row in frozen["instances"]}
    instances = [collect_instance(source, phase, spec, plan, by_stem[spec["stem"]], identities)
                 for spec in plan["instances"]]
    return {"source": str(source), "phase": phase, "instances": instances,
            "originalDecisionUnchanged": read(source / "analysis.json")["decision"]}


LABELS = {"ALIGNED_TOWARD_A": "三项方向支持A", "ALIGNED_TOWARD_B": "三项方向支持B",
          "MIXED_DIRECTIONS": "指标存在分歧", "NO_DIRECTIONAL_DIFFERENCE": "无方向差异"}


def render_report(result):
    lines = ["# HV、IGD+与双向C：已付费终点补充分析", "",
        "A固定为PA_JOINT；只读取两轮原来登记的全部终点，不挑实例、seed或对照。新增搜索FE与解码调用均为0。", "",
        "HV列为主参考1.5的配对相对增量（正为A好）；IGD+列为200(IA−IB)/(IA+IB)的对称恶化量（负为A好，非传统相对百分比）。C列为覆盖率百分数；C(A,B)表示B中被A弱支配的比例。", "",
        "每格为两个配对seed的中位数，原始值、逐seed方向与三目标极值在analysis.json。C使用去重后的原始目标向量、精确≤，相等计覆盖；两个方向不互补。C比较描述覆盖不对称，不等于完整前沿质量的总排序。", "",
        "下表方向只描述数值正负，不是新门槛或显著性结论；不得投票、加权合分，或由小数差异宣称实质优势。原冻结判定全部保留，后续实验须事前登记三指标判据。", ""]
    for source in result["sources"]:
        lines.extend(["## " + source["phase"], "", "原冻结决定：`" + source["originalDecisionUnchanged"] + "`。", ""])
        for instance in source["instances"]:
            lines.extend(["### " + instance["stem"], "",
                "|B对照|ΔHV % ↑|IGD+对称恶化 % ↓|C(A,B) % ↑|C(B,A) % ↓|中位方向|逐seed方向|",
                "|---|---:|---:|---:|---:|---|---|"])
            for row in instance["comparisons"]:
                labels = " / ".join(LABELS[x] for x in row["pairDirectionalLabels"])
                values = (row["control"], row["medianHVEffectPct"]["1.5"], row["medianIGDplusSymmetricWorseningPct"],
                    100 * row["median_C_A_B"], 100 * row["median_C_B_A"], LABELS[row["medianDirections"]["label"]], labels)
                lines.append("|%s|%+.3f|%+.3f|%.3f|%.3f|%s|%s|" % values)
            lines.append("")
    lines.extend(["## 物理目标与边界", "",
        "analysis.json的observations逐臂逐seed保留Cmax、TEC、TWC的各自最小值。三者可能来自不同调度，不拼成虚构的单个最优解；它们只辅助解释前沿，不能替代三项集合指标。", "",
        "仅两个既有开发实例、每轮两个新seed，无独立测试或显著性证明。原TIME阶段未运行，因此本补充不作同时间优势结论。当前PA是未集成原QGS/条件共享的普通适配，不代表最终四子群创新算法。", "",
        "C定义依据：Zitzler (1999), Definition 9（原文为最大化，本项目按最小化使用≤）：https://sop.tik.ee.ethz.ch/publicationListFiles/zitz1999a.pdf", ""])
    return "\n".join(lines)
