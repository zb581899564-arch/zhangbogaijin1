"""Short Chinese report: actual costs and metric disagreements before interpretation."""
from collections import defaultdict
from statistics import median


def fee_summary(costs):
    groups = defaultdict(list)
    for row in costs:
        groups[row["scope"]].append(row)
    return {scope: {"receiptCount": len(rows),
                    **{key: sum(row.get(key) or 0 for row in rows) for key in ("attempted", "successful", "failed")},
                    "searchSeconds": sum(row.get("searchSeconds") or 0 for row in rows),
                    "processSeconds": sum(row.get("processSeconds") or 0 for row in rows),
                    "checkpointUniqueOfflineDecodes": sum(row.get("checkpointUniqueOfflineDecodes") or 0 for row in rows),
                    "checkpointOfflineValidationSeconds": sum(row.get("checkpointOfflineValidationSeconds") or 0 for row in rows)}
            for scope, rows in groups.items()}


def _number(value, digits=3):
    return "未知" if value is None else f"{value:.{digits}f}"


def write_report(path, summary, final_rows, pairs, plan):
    fees = summary["actualFeesByScope"]
    lines = ["# 三臂阶段预算诊断", "", "本报告先列实际费用及指标分歧；不自动给出获胜方法、扩量决定或因果百分比。", "",
             "|范围|实际 attempted / successful / failed FE|搜索秒数合计|进程秒数合计|额外检查点完整解码|",
             "|---|---:|---:|---:|---:|"]
    for scope, row in fees.items():
        lines.append(f"|{scope}|{row['attempted']} / {row['successful']} / {row['failed']}|{row['searchSeconds']:.3f}|{row['processSeconds']:.3f}|{row['checkpointUniqueOfflineDecodes']}|")
    lines.extend(["", f"科学比较为 {len(plan['instances'])} 个既有开发实例 × {len(plan['seeds'])} 个配对 seed × 三臂，每次 {plan['fePerRun']:,} FE。",
                  "工程及时间截止验收费用单列，保留预期失败；离线 QA 不计作搜索 FE。完整实际记录见 `actual-costs.csv/json`。", "",
                  "|实例|方法|搜索秒数中位数 [范围]|HV 中位数|IGD+ 中位数|IGD 中位数|",
                  "|---|---|---:|---:|---:|---:|"])
    for spec in plan["instances"]:
        for arm in plan["arms"]:
            group = [row for row in final_rows if row["instance"] == spec["stem"] and row["arm"] == arm]
            seconds = [row["searchSecondsInclusive"] for row in group]
            lines.append(f"|{spec['stem']}|{arm}|{median(seconds):.3f} [{min(seconds):.3f}, {max(seconds):.3f}]|"
                         + "|".join(f"{median([row[key] for row in group]):.6f}" for key in ("HV", "IGDplus", "IGD")) + "|")
    lines.extend(["", "以下差值全部以左侧候选为正向；IGD+ 为对称改善百分数，C 为精确弱支配比例。表内均为三个配对 seed 的中位数。", "",
                  "|实例|配对|HV 相对改善 %|IGD+ 对称改善 %|C(候选,控制) / C(控制,候选)|中位方向分歧|seed 内分歧数|",
                  "|---|---|---:|---:|---:|---|---:|"])
    for comparison in pairs["comparisons"]:
        for row in comparison["byInstance"]:
            stats = row["statistics"]
            lines.append(f"|{row['instance']}|{comparison['candidate']} vs {comparison['control']}|"
                         f"{_number(stats['hvRelativeImprovementPercent']['median'])}|{_number(stats['igdPlusSymmetricImprovementPercent']['median'])}|"
                         f"{_number(100 * stats['C_A_B']['median'])}% / {_number(100 * stats['C_B_A']['median'])}%|"
                         f"{'有' if row['medianDirectionsDisagree'] else '未见混向'}|{row['signalSeedCounts']['metricDirectionsDisagree']} / {row['pairedSeeds']}|")
    threshold = plan["thresholds"]
    lines.extend(["", f"事前信号尺度：HV {threshold['hvSignalPercent']}%、IGD+ 对称改善 {threshold['igdPlusSymmetricSignalPercent']}%、C 反向差 {threshold['cReverseFlagPercentagePoints']} 个百分点。",
                  "每项的完整原值、范围、逐 seed 方向和至少两个 seed 同向情况见 `pairwise.json`；没有加权、多数票或显著性结论。GLOBAL_ONLY vs LOCAL_ONLY 为辅助比较。", "",
                  "阶段核对见 `stage-costs.csv` 与 `stage-telescopes.json`：INITIAL、GLOBAL、LOCAL 的按时序档案 HV 增量之和等于终点 HV；分享是 GLOBAL 内的子集，不能再次加总。",
                  "每 10000 FE 和每 inclusive 秒的 HV 增量仅描述已发生路径。净观测扣除时间只是算术参考；没有同时间质量比较。",
                  "共享独占耗时未记录，保留为空。cooperationSubsystemSecondsIncludesCommonLifecycle 同时含家族恢复、分组、池更新和组装，不能当共享独占时间，也不能再加到搜索总时间。", "",
                  "准入点来源见 `admission-provenance.csv/json`：acceptedLocal、completedStageWorking、SURVIVORS、nextGeneration、finalObjectiveRetained 分列。",
                  "工作/存活/下一轮主列按完整三目标向量比对；EncodingRetained 附列单独核对原始四向量 key，避免把中性重编码误判为目标点丢失。acceptedLocal 仅表示真实记录的那次局搜接受。",
                  "全局没有逐 QGS batch 的工作态快照；阶段出口不含某点不能说明它从未进入工作态。partial 缺出口或下一轮快照统一记未知，最终保留仅指目标向量成员。", "",
                  "每实例使用全部九份终点前沿的非支配并集作统一经验参考，仅离线用于评价；归一化与 HV reference 沿用冻结协议。",
                  "三个 seed 不绘制 50% EAF 或 EAF difference。图保留全部末前沿点、三个二维投影和三个目标的同实例共同轴范围；二维投影不代表三维优势。", "",
                  "绘图可复现源在 `analysis-source/`；图为 SVG（可编辑文字）、PDF 和 PNG。`figures/figure-qa.json` 的导出检查不能替代主代理的实际视觉检查与独立数值审计。", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
