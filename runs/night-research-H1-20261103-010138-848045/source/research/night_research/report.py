"""Compact reviewable result; all paired raw values remain in JSON/CSV."""


def _number(value):
    return "未定" if value is None else f"{value:.4f}" if isinstance(value, float) else str(value)


def write_report(output, protocol, effects, selection, decision, audit, factorial, mechanisms=None):
    rows = ["# 夜间冻结结构假设 " + protocol["hypothesis"], "",
        "候选：" + protocol["candidate"] + "；全局 C*：" + str(selection["selected"]) + "；准入：" + decision["status"] + "。", "",
        "六开发实例各五个新 seed，先实例内平均再实例等权。主 HV 参考点 1.5；敏感性 1.25/2.0。",
        "IGD+参考为当轮全部方法与新 seed 的末期有效 ND 并集，仅离线使用。15000FE 未达点保留删失。", "",
        "|比较|同T平均%|中位%|实质胜/负|最差%|去最佳平均%|同FE完整配对数|",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for label, value in effects.items():
        metric = value["T"]["1.5"]
        cells = [label, metric["mean_effect_percent"], metric["median_effect_percent"],
            str(metric["practical_wins"]) + "/" + str(metric["practical_losses"]), metric["worst_effect_percent"],
            metric["mean_after_removing_best_instance_percent"], value["FE15000"]["completePairsOnly"]["complete_pair_instances"]]
        rows.append("|" + "|".join(_number(cell) for cell in cells) + "|")
    if factorial:
        rows += ["", "|事前登记交互|同T均值%|同T中位%|同FE均值%|", "|---|---:|---:|---:|"]
        for name, value in factorial.items():
            rows.append("|" + "|".join([name, _number(value["T"]["meanInteractionPercent"]),
                _number(value["T"]["medianInteractionPercent"]), _number(value["FE15000"]["meanInteractionPercent"])]) + "|")
        rows += ["", "交互为事前登记的差中之差，分母与逐项公式见interactions.json；先实例内平均五seed，再实例等权。候选胜过静态基准不能单独证明两因素协同。"]
    if mechanisms and mechanisms["methodSummary"]:
        rows += ["", "|传递机制|实际付费次数|截止内次数|本厂完整率%（实例等权）|源时间轴匹配率%（实例等权）|待完成|",
            "|---|---:|---:|---:|---:|---:|"]
        for method in mechanisms["methodSummary"]:
            rates = [method[key] for key in ("instanceMeanLocalEncodingPreservedRate", "instanceMeanSourceTimelineMatchedRate")]
            cells = [method["variant"], method["paidTransfers"], method["deadlineValidPaidTransfers"],
                *[None if value is None else 100 * value for value in rates], method["pendingTransfers"]]
            rows.append("|" + "|".join(_number(cell) for cell in cells) + "|")
        rows += ["", "机制计数包含全部付费调用，迟于T的事件另列。保留率先在每实例合计五seed计数，再实例等权；无付费调用的实例保持未定。",
            "三对来源和本厂编码独立重建；时间轴及其他厂不变由已验收Java见证，未离线还原完整父本。逐owner与12格调用计数见factory-transfer-owners.csv和factory-transfer-opportunities.csv。"]
    rows += ["", "所有 v1 准入条件、IGD+保护、参考点敏感性和逐实例/seed原值见 decision.json、effects.json、paired-effects.csv。",
        "本轮 " + str(audit["runs"]) + " 个 owner 完整；达到 FE15000 的 owner 为 " + str(audit["fixedFEReached"]) + "。",
        "返回档案重放 " + str(audit["returnedSolutionsReplayed"]) + " 次，检查点额外重放 " + str(audit["offlineCheckpointValidationDecodes"]) + " 次，二者分别计费与报告。",
        "费用和删失见 audit.json、run-metrics.csv；失败 owner 与不完整 owner 不重跑。",
        "结论限于事前冻结开发配置，不代表新颖性、独立泛化或论文资格；未启动正式第6步，也不自动调参或延时。", ""]
    with (output / "report.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(rows))
