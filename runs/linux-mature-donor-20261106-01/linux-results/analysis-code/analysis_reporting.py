"""Portable raw tables and a bounded Chinese interpretation of the probe."""
import csv
from pathlib import Path


def write_csv(path, rows):
    with Path(path).open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_tables(output, result):
    observations, pairs, donors = [], [], []
    for case in result["instances"]:
        for row in case["observations"]:
            for endpoint in ("finalArchive", "workingPopulation"):
                m = row[endpoint]
                observations.append(dict(instance=case["instance"], seed=row["seed"], arm=row["arm"], endpoint=endpoint,
                    newFE=row["successfulFE"], searchSeconds=row["searchSeconds"], prepareSeconds=row["prepareSeconds"],
                    size=m["frontSize"], HV1_5=m["HV"]["1.5"], HV1_25=m["HV"]["1.25"], HV2_0=m["HV"]["2.0"],
                    IGDplus=m["IGDplus"], IGD=m["IGD"],
                    archiveHVAboveA0=row["gain"]["HVAboveA0"]["1.5"],
                    archiveHVAboveA0PerFE=row["gain"]["HVAboveA0PerNewFE"]["1.5"],
                    archiveHVAboveA0PerSearchSecond=row["gain"]["HVAboveA0PerSearchSecond"]["1.5"]))
            for group_source, values in row["supply"]["byReceiverDomainAndSource"].items():
                domain, source = group_source.split("/")
                donors.append(dict(instance=case["instance"], seed=row["seed"], arm=row["arm"],
                                   receiverDomain=domain, disjointSource=source, **values))
        for comparison in case["comparisons"]:
            for p in comparison["pairs"]:
                pairs.append(dict(instance=case["instance"], seed=p["seed"], endpoint=comparison["endpoint"],
                    candidate=comparison["candidate"], control=comparison["control"],
                    HVEffectPct1_5=p["HVEffectPct"]["1.5"], HVEffectPct1_25=p["HVEffectPct"]["1.25"],
                    HVEffectPct2_0=p["HVEffectPct"]["2.0"],
                    IGDplusSymmetricImprovementPct=p["IGDplusSymmetricImprovementPct"],
                    IGDImprovement=p["IGDImprovement"], Cdelta=p["Cdelta"], **p["coverage"]))
    write_csv(output / "observations.csv", observations)
    write_csv(output / "paired-comparisons.csv", pairs)
    write_csv(output / "donor-events.csv", donors)


def summary_text(value, suffix=""):
    if "median" not in value:
        return "不可计算（控制HV为0）"
    low, high = value["range"]
    return f'{value["median"]:+.6g}{suffix} [{low:+.6g}, {high:+.6g}]; {value["wins"]}/{value["ties"]}/{value["losses"]}'


def write_markdown(output, result):
    lines = ["# 成熟接收者的已付费供体探针", "",
        "本报告比较同一成熟 P100、同一 P 学习模型和同一 POST_GLOBAL 已付费档案 A0 上的一个完整局搜 pass。",
        "四臂 R/G/S/UNION 仅改变供体池；这不是完整 500k 算法比较。n=3 仅报告配对描述，不生成 EAF、显著性或独立创新结论。", "",
        "每例 IGD+/IGD 参考集为其四臂×三 seed 的最终档案精确非支配并集；工作态终点使用同一参考。归一化沿用 protocol.json 的冻结值，不重新拟合。",
        "HV 主参考为 1.5，并报告 1.25、2.0。双向 C 为精确弱支配，目标去重，相等双向覆盖；CSV/JSON 保留覆盖分子及分母。", "",
        "searchSeconds 是实际记录耗时，可能含逐子代 QA 与日志开销；prepareSeconds 单列。ΔHV/秒是此 pass 的描述性费用效率，不证明同时间优势。", ""]
    for case in result["instances"]:
        lines.extend([f'## {case["instance"]}', "",
            f'最终经验参考点数：{len(case["reference"])}。单 pass 新 FE：{case["observations"][0]["successfulFE"]}。', ""])
        for item in case["captures"]:
            receipt = item["receipt"]
            lines.append(f'- source seed {item["seed"]}：成熟 PRE_GLOBAL FE {receipt["beforeGlobalFE"]}；'
                         f'POST_GLOBAL FE {receipt["afterGlobalFE"]}；其中 G {receipt["ordinaryPaidCandidates"]}、S {receipt["sharedPaidCandidates"]}。')
        lines.extend(["", "源运行费用属于原来源账本，不计作本 pass 的新 FE，也不被抹去。完整运行总账由控制器另存。", ""])
        for endpoint, title in (("finalArchive", "共同已付费档案终点"), ("workingPopulation", "工作态非支配终点")):
            lines.extend([f"### {title}", "", "数值为配对中位数 [最小, 最大]；后列胜/平/负。正号均偏向候选。", "",
                "| 候选/控制 | HV 1.5 相对变化% | IGD+ 对称改善% | C差 |", "|---|---|---|---|"])
            for row in case["comparisons"]:
                if row["endpoint"] == endpoint:
                    lines.append(f'| {row["candidate"]}/{row["control"]} | {summary_text(row["HVEffectPct"]["1.5"])} | '
                                 f'{summary_text(row["IGDplusSymmetricImprovementPct"])} | {summary_text(row["Cdelta"])} |')
            lines.append("")
        lines.extend(["UNION/G 表示在全局 G 供给之上加入 S 的增量；UNION/S 表示 G 的增量。指标有分歧时须报告权衡，不按多数投票归纳优势。", "",
            "| seed | 臂 | 新增FE | 搜索秒 | 准备秒 | A0上新增HV(1.5) | 每新增FE | 每搜索秒 |", "|---|---|---:|---:|---:|---:|---:|---:|"])
        for row in case["observations"]:
            gain = row["gain"]
            lines.append(f'| {row["seed"]} | {row["arm"]} | {row["successfulFE"]} | {row["searchSeconds"]:.6g} | '
                f'{row["prepareSeconds"]:.6g} | {gain["HVAboveA0"]["1.5"]:.8g} | '
                f'{gain["HVAboveA0PerNewFE"]["1.5"]:.8g} | {gain["HVAboveA0PerSearchSecond"]["1.5"]:.8g} |')
        lines.extend(["", "供体逐 seed/臂/固定20与自由80的抽中、接受、入档计数见 donor-events.csv。G、S、GS 为互斥统计类别；GS 不重复加入 G 与 S。", ""])
        for row in case["observations"]:
            if row["arm"] == "UNION":
                supply = row["supply"]
                lines.append(f'- seed {row["seed"]}：自由80原始共享候选 {supply["free80SharedRaw"]}，去重后可用 S/GS 供体 {supply["free80SharedAvailable"]}。')
        lines.extend(["", "自由80没有可用共享供体时，未抽中 S 不构成共享无效的证据。", ""])
    lines.extend(["## 证据边界", "", "本报告只计算离线指标，不调用解码器，也不新增搜索 FE。独立审计另存 audit-* 目录；本文件本身不代表审计通过。",
                  "模型学习仅使用 P 的来源约束和成熟捕获是否为首次越过阈值，须结合控制器/Java 来源与观察等价证据核验；不从指标反推这些前提。", ""])
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
