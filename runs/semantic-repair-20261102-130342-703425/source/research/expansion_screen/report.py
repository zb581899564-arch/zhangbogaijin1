"""Render the actual decision, including unmet criteria and all paired seed differences."""
import json
from research.dynamic_benchmark.io import csv_write
from .execution import write, read


def _number(value):
    return "未识别" if value is None else f"{value:+.3f}%"


def _tables(result):
    criteria, pairs = [], []
    for name, candidate in result.get("candidates", {}).items():
        for kind in ["green_conditions", "red_conditions"]:
            for group, detail in candidate.get(kind, {}).items():
                for condition, row in detail["conditions"].items():
                    criteria.append({"candidate":name, "kind":kind, "group":group, "condition":condition,
                                     "value":row["value"], "operator":row["operator"],
                                     "threshold":row["threshold"], "resolved":row["resolved"], "pass":row["pass"]})
        for comparison in candidate.get("comparisons", {}).values():
            if "instances" not in comparison:
                continue
            for instance in comparison["instances"]:
                for seed in instance["paired_seeds"]:
                    pairs.append({"candidate":name, "comparator":comparison["comparator"],
                                  "instance":instance["instance"], "instanceEffectPercent":instance["effect_percent"],
                                  "practicalWin":instance["practical_win"], "practicalLoss":instance["practical_loss"], **seed})
    return criteria, pairs


def render(root, result, phase="initial"):
    output = root / "analysis" / phase
    write(output/"decision.json", result, once=True)
    criteria, pairs = _tables(result)
    if criteria:
        csv_write(output/"criterion-receipt.csv", criteria)
    if pairs:
        csv_write(output/"paired-seed-differences.csv", pairs)
    lines = ["# 扩量初筛实际结果", "", "阶段："+phase+"；判定："+result["status"]+"。",
             "主参考点1.5；敏感性点1.25/2.0；先平均同实例seed，再以实例配对。",
             "这是六个开发实例的资源投入判断，不能据此宣称未见实例泛化、创新资格或ESWA发表条件。", "",
             "|候选|判定|对照|平均HV相对变化|中位数|实质胜/负|最差实例变化|",
             "|---|---|---|---:|---:|---|---:|"]
    for name, detail in result.get("candidates", {}).items():
        for label, comparison in detail.get("comparisons", {}).items():
            if "mean_effect_percent" not in comparison:
                continue
            lines.append(f"|{name}|{detail['color']}|{comparison['comparator']}|"
                         f"{_number(comparison['mean_effect_percent'])}|{_number(comparison['median_effect_percent'])}|"
                         f"{comparison['practical_wins']}/{comparison['practical_losses']}|{_number(comparison['worst_effect_percent'])}|")
        lines += ["", name+"未满足的绿灯项："+", ".join(detail.get("unmet_green_conditions", [])),
                  name+"触发的红灯项："+", ".join(detail.get("triggered_red_conditions", [])), ""]
    lines += ["## 继续范围", "", "允许进入下一步的候选："+", ".join(result.get("ready_for_step6", [])),
              "所有逐项数值见criterion-receipt.csv，配对seed差值见paired-seed-differences.csv。",
              "最强经典是一个整体实际方法，未逐实例拼虚拟对手；不使用p值硬门槛。", ""]
    if "external_selection" in result:
        lines.append("锁定C*："+str(result["external_selection"]["selected"]))
    if "followup" in result:
        lines.append("按冻结规则可复核候选："+str(result["followup"].get("selected_candidate")))
    audit = read(output/"audit.json")
    lines += ["", "## 费用与工程审计", "", "```json", json.dumps(audit, ensure_ascii=False, indent=2), "```", "",
              "搜索时间包含初始化、候选、解码、训练、共享、选择、档案和监测；输入读取、JVM启动、导出和QA另外计入整个初筛墙钟。",
              "嵌套计时不可重复相加；达到FE点为诊断，未达为删失，不补造分数。",
              "旧540次只作开发背景，未混入此轮质量计算。", ""]
    (output/"report.md").write_text("\n".join(lines), encoding="utf-8")
