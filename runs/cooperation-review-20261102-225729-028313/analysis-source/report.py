"""Render the identification limits beside the observed historical evidence."""


def table(headers, rows):
    return ["|" + "|".join(headers) + "|", "|" + "|".join("---" for _ in headers) + "|"] + [
        "|" + "|".join(str(value) for value in row) + "|" for row in rows]


def report(output, project, overall, effects, tables, receipt):
    def pct(value):
        return f"{100 * value:.2f}%" if value is not None else "缺失"

    def lookup(campaign, candidate, control, instance):
        return next(row for row in effects if row["campaign"].startswith(campaign)
                    and row["candidate"] == candidate and row["control"] == control and row["instance"] == instance)

    lines = ["# 历史共享来源与适用边界：零新增FE复核", "",
        "结论：历史同期消融支持共享模块在两个二阶段、三工厂开发实例上有明显增量；来源计数和有限组合样本确认多个目标群的记录被使用。它们不能识别目标专业分工的必要性、某个工厂缺少哪类知识，或某来源对最终HV的因果贡献。当前不足以通过固定需求反馈的实施门槛。", "",
        "## 范围与复算口径", "",
        "仅读取四个既有完成根。HV参考点1.5，实例内五个配对seed先分别求候选/对照HV均值，再计算百分比；最后六实例等权。T仅在每个同期campaign内比较，旧轮不拼接墙钟分数。FE15000的多轮旧控制存在精确重复，四轮不能当作独立重复实验。未计算新HV、未解码、未启动优化器。", "",
        "实例名为工件数_阶段数_工厂数_序号，20_2_3_1与100_2_3_1都是二阶段、三工厂。两例共享同一阶段/工厂结构，只构成当前开发资料中的条件信号，不能分离阶段数、工厂数、规模或数据难度的作用。", "",
        "## 每轮同轮内部效应", ""]
    lines += table(["campaign", "比较", "含义", "同T均值%", "同T中位数%", "同FE均值%", "实质胜/负"], [
        [row["campaign"].split("-2026")[0], row["candidate"] + "/" + row["control"], row["kind"],
         f'{row["meanTPercent"]:+.4f}', f'{row["medianTPercent"]:+.4f}',
         f'{row["meanFE15000Percent"]:+.4f}', f'{row["practicalWinsT"]}/{row["practicalLossesT"]}'] for row in overall])
    lines += ["", "sharing_module是相同固定FA家族组织下开启池与组合的增量；net_configuration同时包含家族组织，不能归因给共享本身。实质胜/负沿用≥1%且至少3/5seed同向，只是描述性标准，不是显著性检验。", "",
              "## 实例级共享增量", ""]
    rows = []
    for instance in sorted({row["instance"] for row in effects}):
        a = lookup("sync-job-audit", "SHARE_JOB", "SYNC_JOB", instance)
        b = lookup("center-last", "SHARE_ORIGINAL", "SYNC_ORIGINAL", instance)
        c = lookup("center-last", "SHARE_LAST", "SYNC_LAST", instance)
        rows.append([instance, f'{a["effectTPercent"]:+.3f}', f'{b["effectTPercent"]:+.3f}',
                     f'{c["effectTPercent"]:+.3f}', f'{b["effectFE15000Percent"]:+.3f}', f'{c["effectFE15000Percent"]:+.3f}'])
    lines += table(["实例", "sync审计T%", "原顺序T%", "中央最后T%", "原顺序FE%", "中央最后FE%"], rows)
    lines += ["", "## 来源群、实际组合与预算费用", "",
        "以下只用center-last完整计数：每运行先求比例，再实例内平均五seed，再六实例等权；使用次数会重复计算同一记录，不能理解为独立新编码数。producer是保留记录这次入池的付费来源群，不等于独占发明者，也不等于该记录最擅长的局部目标。重复offer不刷新来源；退出池后再次进入可获得新付费来源。", ""]
    columns = [("validPaidAssemblies", "截止有效组合"), ("admissionRate", "曾外部入档率"),
        ("sameGenerationFraction", "同代片段占比"), ("lateFreshFraction", "同代E/W占比"),
        ("meanAgeFE", "片段年龄FE"), ("full.eligibleCenterOpportunities", "完整代机会累计"),
        ("partial.eligibleCenterOpportunities", "部分代机会累计"), ("full.paidAssemblies", "完整代已付费组合累计"),
        ("partial.paidAssemblies", "部分代已付费组合累计"), ("full.meanPaidPerGeneration", "每完整代组合均值"),
        ("cooperationSeconds", "共享相关记录耗时秒")]
    summary = {row["variant"]: row for row in tables["composition-summary"]}
    lines += table(["指标", "原顺序SHARE", "中央最后SHARE"], [
        [label] + [pct(summary[variant][field]) if "Fraction" in field or field == "admissionRate" else f'{summary[variant][field]:.3f}'
                   for variant in ("SHARE_ORIGINAL", "SHARE_LAST")] for field, label in columns])
    lines += ["", "每次组合实际评价计1FE；完整代400次eligible机会与实际组合数不同，部分代可因截止位置而减少机会。poolAccepted/poolRejected/poolTruncated按记录事件计，不是唯一记录个数；完整/部分代仅拆分组合机会与组合评价FE，不能从现有字段恢复各代全部局搜FE或精确的边际CPU成本。共享耗时存在嵌套及间接开销，不与其他计时机械相加。", ""]
    lines += table(["实例", "顺序", "M来源%", "C来源%", "E来源%", "W来源%", "初始化%"], [
        [row["instance"], row["variant"].replace("SHARE_", "")] +
        [pct(row["producerFraction." + producer]) for producer in ("MAKESPAN", "CENTER", "ENERGY", "WORKER_COST", "INITIALIZATION")]
        for row in tables["composition-instances"]])
    lines += ["", "## 有限样本内的跨群混合", "",
        "只有每运行首16+末16个截止有效付费组合，属于固定窗口样本，没有随机抽样概率。以下比例只描述这些窗口，不能估计全部组合混合率、全部阶段/家族贡献或群质量排名。不同producer混合表示多个来源群被选中；相同producer也可能来自多次评价，不同producer也可能提供目标等价的记录。", ""]
    rows = []
    for variant, row in summary.items():
        rows.append([variant, f'{row["sampleAssemblies"]:.0f}', pct(row["sampleCoverage"]),
            pct(row["sampleFraction.multipleSearchProducers"]), pct(row["sampleFraction.multiplePaidEvaluations"]),
            pct(row["sampleFraction.externalAdmission"]), pct(row["sampleFraction.objectivePresentAtCutoff"])])
    lines += table(["配置", "每运行样本数", "样本/全量均值", "多个搜索群", "多个付费来源", "曾外部入档", "目标向量仍在截止前沿"], rows)
    lines += ["", "目标向量仍在截止前沿仅是原始浮点目标三元组精确匹配，不能证明此样本基因型独占留存、正的独占HV、后代贡献或反事实移除共享后的性能。PropagationLedger为每次共享生成分配origin事件ID，仅在编码保持不变时跟踪；同编码可多次生成不同ID，因此曾入人口/教师的origin计数并非全局去重基因型数，也只是传播事件。origin容量上限和overCap保留在propagation-runs.csv。externalArchiveAdmission事件可能在之后被支配；不把曾入档率写成最终HV贡献率。", "",
        "sample-strata.csv保留每运行样本的producer组合、stage组合、family和首/末窗口分层。sample-fragments.csv保留每个被采样片段的factory、paidFE、generation、stage、producer与年龄。全量fromProducer计数没有同样完整的stage/family联合分布。", "",
        "## 可观察互补性与不可识别内容", "",
        "可观察：存在跨群记录被实际组合与直接传播的事实；两个实例有较大同轮共享增量；中央后移增加本代E/W记录使用，却没有带来清楚的总体共享时序收益。这支持继续审查条件性的共享来源，尚不能证明目标专业群产生了不可替代的互补知识。", "",
        "不可识别：未入选的当前池记录、已拒绝/截断记录及历史全池；每片段(c_f,e_f,w_f)及所需T/eta/尺度；单厂缺口与独占补齐者；来源相同/不同的记录是否局部目标等价；没有共享时的同请求反事实；完整的全量混合率；最终HV的来源分解和后代因果贡献。固定池容量8意味着当前池缺失不等于搜索从未找到。", "",
        "## 只收敛一个新增有界采集问题", "",
        "在预先限定的实际请求中，给定相同FA上下文、cap、eta和目标尺度，是否存在一个具体工厂的可行/局部目标改进缺口，而该缺口能由某类目标偏好来源的已付费记录补齐？", "",
        "现有记录不含该请求时完整保留池与局部目标，不能回答。建议只观察已付费记录，不额外解码：预定少量请求窗口导出全部当前池，保留record/context/family/factory标识、局部四向量与(c,e,w)、producer/stage/paidFE/generation、重复/拒绝/支配/容量截断原因、请求cap/eta/两尺度、父本目标、选择/预测/实际结果及截止有效性。完整计数记录请求可行性和各厂cap缺口；有界窗口保留逐厂原因与多来源等价性。来源标签不是唯一知识产权，重复记录来源歧义需公开。", "",
        "先用匹配的专业分工vs四组同综合偏好的消融确定专业分工整体是否有用，再看有界池证据能否指出一个可操作且反复出现的缺口。只有明确缺口后才值得预先定义固定需求反馈验证；当前不支持启动反馈优化，不增加RL。此报告不定义或启动后续实验。", "",
        "## 复算与来源", "",
        "入口：E:/conda/python.exe -B -m research.cooperation_review --output <新的独立目录>。所有CSV来源路径可逐行追溯；sources.csv是读入文件的大小/mtime清单，receipt.json记录零新增FE与只读检查。元数据检查不作为密码学完整性证明。", "",
        f'本次新增搜索FE={receipt["newSearchFE"]}，新增解码FE={receipt["newDecodeFE"]}；四历史根文件元数据前后相同={receipt["historicalRootsUnchanged"]}。', ""]
    for name in receipt["historicalRoots"]:
        lines.append(f'- [{name}]({(project / "runs" / name).as_posix()})')
    lines += ["", "表文件：effects-seeds.csv、effects-instances.csv、effects-summary.csv、propagation-runs.csv、composition-runs.csv、composition-instances.csv、composition-summary.csv、composition-generations.csv、sample-assemblies.csv、sample-fragments.csv、sample-strata.csv。未改Java、旧runs或现有文档。", ""]
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
