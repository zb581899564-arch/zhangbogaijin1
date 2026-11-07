"""Concise full-factor report with all source and attribution limits."""


def show(value, digits=4):
    return "缺失/删失" if value is None else f"{value:.{digits}f}"


def write_report(output, protocol, effects, interactions, signal, decision, audit, tables):
    lines = ["# 目标专业分工：150次同期2×2验证", "",
        "结果仅针对整个目标专业偏好因素：分组、教师/pbest、Q奖励和局搜准则。四个物理组、15/55/15/15规模、独立Q表和每组50步保持；UNIFORM是四组都使用CENTER偏好，不是单群或群数消融。", "",
        "六开发实例各五个新seed，全部150单元完成后才构造本轮经验参考并解释质量。HV参考点1.5，先实例内五seed求HV均值，再实例等权；实质胜要求≥1%且≥3/5seed同向，不是统计显著。NSGA setting0同期全表报告。", "",
        "|比较|同T均值%|同T中位数%|同FE15000均值%|同0.5T均值%|实质胜/负|", "|---|---:|---:|---:|---:|---:|"]
    for label, item in effects.items():
        t = item["T"]["1.5"]
        lines.append("|" + "|".join([label, show(t["mean_effect_percent"]), show(t["median_effect_percent"]),
            show(item["FE15000"]["allInstances"]["mean_effect_percent"]), show(item["halfTime"]["mean_effect_percent"]),
            f'{t["practical_wins"]}/{t["practical_losses"]}']) + "|")
    lines += ["", "完整逐实例/seed、参考点1.25/2.0、IGD+、探索性实例bootstrap和去最佳实例结果见effects.json。FE未达点保持null，completePairsOnly只是完整配对实例上的条件诊断。", "",
        "交互为(SHARE_SPECIAL−SYNC_SPECIAL)−(SHARE_UNIFORM−SYNC_UNIFORM)，保留每seed原HV差，实例百分比使用SYNC_UNIFORM实例均值归一化。", "",
        "|交互预算|六实例平均%|正向实例数|", "|---|---:|---:|"]
    for field, item in interactions.items():
        lines.append(f'|{field}|{show(item["meanInteractionPercent"])}|{item["positiveInstances"]}|')
    lines += ["", "专业分工预定描述性信号：" + str(signal["supportedDescriptiveSignal"]) + "。逐条条件见signal.json；不替代正式扩量标准，也不据此否定四组上的其他可检验假设。", "",
        "## 保留池重放与知识门槛", "",
        "独立choose重放只读取已付费保留记录，遵循相同cap、eta、尺度和同分首项规则；组合三目标为max厂跨度、sum能耗、sum人工成本。没有新解码或免费候选。所有有界请求都核验来源FE/上下文、选择记录、组合预测和父本去重结果。", "",
        "真正互补快照要求至少两个不同付费FE，且相同加权分数同时优于父本和所有当前保留记录所携带的满足cap的最佳完整来源至少0.1%。wholeObjectives只表示来源当时完整日程的已付费目标，不表示当前各池仍能恢复那个完整基因型。没有可行whole基准只记补全可行性，不用缺失分母通过门槛。", "",
        "紧cap请求取0.9×父本Cmax，是低于当前父本跨度的愿望条件；保留池缺少满足该cap的厂记录不表示父本不可行。", "",
        "|配置|每运行请求均值|紧cap请求|紧cap缺工厂请求|有界请求数|真正互补样本|无whole基准可行样本|", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in tables["pool-summary"]:
        lines.append("|" + "|".join([row["variant"]] + [show(row[field], 2) for field in (
            "requests", "tightRequests", "tightRequestsMissingFactory", "capturedRequests", "genuineComplementaritySamples", "feasibilityCompletionSamples")]) + "|")
    lines += ["", "上表每运行先统计，再实例内平均seed，最后实例等权。首8+末8请求不是随机样本；真正互补样本数和来源混合只能解释捕获窗口，不能估计全量发生率。完整计数中的weightedImprovementAtLeast001只比较父本，不能代替真正互补门槛。", "",
        "第三步判断：**" + decision["status"] + "**；通过的实例数=" + str(decision["passingInstances"]) + "/6。逐seed四个条件、实际分母和通过快照request ID全部保存于step3-decision.json。", "",
        "|实例|同时满足全部条件的seed数|实例门槛|", "|---|---:|---|" ]
    lines += [f'|{row["instance"]}|{row["passingSeeds"]}/5|{row["passesInstanceGate"]}|' for row in decision["instances"]]
    lines += ["", "第三步性能未启动。门槛若未满足即按计划SKIPPED_NO_IDENTIFIED_ACTIONABLE_GAP收束；若满足，也只标记可实施一次固定规则验证，本模块不自动派发，不加RL。专业分工描述性信号和知识门槛分别报告，未在事后增加二者必须同时成立的条件。", "",
        "## 来源使用、标签撤回与解释边界", "",
        "pool-chosen-records.csv给出捕获请求的选择记录及物理来源；composition-run/generation-metrics保存全量来源使用、年龄与完整/部分代机会。producer-withdrawal.csv仅从这个当前保留池撤回某来源标签，再重放相同请求；不是删除整个目标群的反事实。记录可能由其他群重复产生，池外被拒绝/截断内容未知，标签依赖不等于独占知识或群因果效应。", "",
        "来源被使用、组合曾被外部档案接纳和最终HV贡献分开解释。first16+last16组合样本与first8+last8请求样本范围不同；不把元数据、来源混合、曾入档或局部加权改进称为最终HV贡献。", "",
        "## 实际费用与覆盖", "",
        f'成功搜索FE={audit["successfulFE"]}，尝试FE={audit["attemptedFE"]}，正常限时中断={audit["timeInterruptedAttempts"]}；返回解完整重放={audit["returnedSolutionsReplayed"]}，达到FE15000={audit["fixedFEReached"]}/150。', "",
        f'自有版本中未完成整代的运行数={audit["withoutCompletedGeneration"]}。首代内截止仍保留合法T档案及FE删失；coverage.csv公开实际QGS/局搜覆盖，未覆盖阶段不填0推断质量。已完成代仍检查每物理群50步和共享400机会；工程验收独立覆盖完整代与所有偏好路径。', "",
        "T含搜索、修复、Q、共享、档案和共同记录；JVM/输入/QA/导出计入原campaign45分钟。processWall和controllerValidation分列，嵌套计时不机械相加；共同观察的间接成本存在，不能拼接旧无观察墙钟成绩。", "",
        "独立离线保留池重放新增FE=0；观察extraFE=0。搜索FE与返回解离线QA费用不混报。审计、冻结源/二进制/输入、原时钟、命令和原始失败全部保留。本轮仍是36合格开发资料内的机制验证，未启动正式第6步。", ""]
    with (output / "report.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
