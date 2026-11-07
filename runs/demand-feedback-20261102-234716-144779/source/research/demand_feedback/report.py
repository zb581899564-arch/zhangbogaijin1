"""Describe the single fixed rule and retain its interpretation limits."""


def show(value, digits=4):
    return "缺失/删失" if value is None else f"{value:.{digits}f}"


def write_report(output, effects, signal, audit, tables):
    lines = ["# 固定需求反馈：90次同期单规则验证", "",
        "第二步事前知识门槛已满足。本轮只检验：DEMAND与SHAM都维护/查询同一类最近紧cap需求，DEMAND按当前保留池最大正缺口覆盖原随机厂，SHAM保留原随机厂。原SHARE不维护需求。其他专业分工、共享、Q、邻域、接受和预算保持。", "",
        "六合格开发实例、五个新seed、三个同期方法，全部90单元完整后解释质量。主HV参考点1.5，先实例内平均seed，再六实例等权；实质胜/负为≥1%且至少3/5seed同向，不等于显著性。", "",
        "|比较|同T均值%|同T中位数%|同FE15000均值%|同0.5T均值%|实质胜/负|", "|---|---:|---:|---:|---:|---:|"]
    for label, item in effects.items():
        t = item["T"]["1.5"]
        lines.append("|" + "|".join([label, show(t["mean_effect_percent"]), show(t["median_effect_percent"]),
            show(item["FE15000"]["allInstances"]["mean_effect_percent"]), show(item["halfTime"]["mean_effect_percent"]),
            f'{t["practical_wins"]}/{t["practical_losses"]}']) + "|")
    lines += ["", "逐实例/seed、参考点1.25/2.0、IGD+、探索性实例bootstrap和去最佳实例结果见effects.json。IGD+参考为本轮每实例3方法×5seed有效T档案ND并集，近似且不反馈搜索。FE未达点保留null；completePairsOnly限于完整配对实例的条件诊断。", "",
        "预定需求反馈描述性信号：**" + str(signal["supportedDescriptiveSignal"]) + "**。signal.json保存五项条件：DEMAND/SHAM同T均值≥1%、至少3个实质胜、同FE均值正，同时DEMAND/原SHARE同T均值和中位数均非负。只做这一固定规则，不改cap、阈值、反馈频率，不增加RL。", "",
        "本轮没有NSGA同期运行；第二步同期竞争差距仅作背景，不将其旧墙钟分数拼入本轮结果。", "",
        "## 实际需求查询与路由", "",
        "以下计数每运行统计，再实例内平均五seed，最后六实例等权。原SHARE的需求管理字段不存在，保留缺失，不填0伪造观察。", "",
        "|版本|紧cap记录|总查询|合格查询|有正缺口|实际覆盖随机厂|无缺口/已满足|", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in tables["demand-summary"]:
        lines.append("|" + "|".join([row["variant"]] + [show(row[field], 2) for field in (
            "tightRequestsRecorded", "queries", "eligibleQueries", "actionableQueries", "routedOverrides", "resolvedOrNoGapQueries")]) + "|")
    lines += ["", "合格查询限于有历史紧cap请求的MAKESPAN物理组家族粒子；target为(min保留c−cap)/cap最大正值，平局取最小厂id。SHAM保留原随机厂；DEMAND仅在存在target时覆盖。若target恰好等于原随机厂，有可行动缺口但不增加routedOverrides。", "",
        "demand-query-replay.csv核对目标厂、实际路由、request/query FE与代数先后及first8+last8 eligibleQuery边界；demand-factory-gaps.csv保存捕获查询的各厂缺口。窗口样本不是随机样本，不能据此估计全部缺口分布。queryFE表示查询时已有付费进度，查询不是新候选；截止可能发生在随后VNS付费评价前，不能把查询或改路次数当成付费候选、改进解或最终HV贡献。", "",
        "紧cap是0.9×父本Cmax的愿望条件，池中暂缺该cap下记录不表示父本不可行。当前保留池不能代表完整历史或被截断内容。共同保留池重放、来源/组合计数与反馈时序另表保存；标签撤回仅解释当前保留池，不能归因为整个群被删除。", "",
        "## 费用、截止与范围", "",
        f'成功搜索FE={audit["successfulFE"]}，尝试FE={audit["attemptedFE"]}，正常限时中断={audit["timeInterruptedAttempts"]}，返回解完整重放={audit["returnedSolutionsReplayed"]}；达到FE15000={audit["fixedFEReached"]}/90。', "",
        f'未完成整代的运行数={audit["withoutCompletedGeneration"]}；仍保留合法T前沿、FE删失和实际阶段覆盖，不重跑、不用缺失阶段推断质量。', "",
        "原execution.json保留公共校验费用；demand-validation.json另外记录需求轨迹校验耗时，分析恰好加一次，run-metrics/audit同时公开base与demand及合计controllerValidationSeconds。恢复核验和离线主分析也消耗原campaign时钟，不把这些费用冒充搜索内耗时。", "",
        "T包含需求维护、查询、局搜和共同观察；冻结、JVM、QA、导出与主分析全部计入原30分钟。嵌套计时不能机械相加。观察与独立路由/保留池重放新增FE均0；搜索FE与返回解离线QA分列。原始源码/二进制/输入/命令/失败均保留。", "",
        "这是开发期资料的一次固定规则检验，未启动正式第6步，不自动追加调参、机制或实验。", ""]
    with (output / "report.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
