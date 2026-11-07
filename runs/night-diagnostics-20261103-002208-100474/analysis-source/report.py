"""Keep coverage, certified bounds and numeric potentials distinct from causality."""


def pct(value):
    return "缺失" if value is None else f"{100 * value:.2f}%"


def write_report(output, tables, receipt):
    lines = ["# H1/H2夜间零新增FE诊断", "",
        "只读取两轮已经完成的SHARE_SPECIAL池请求窗口及同轮已付费返回档案，不混合跨轮墙钟或当作独立确认。所有潜在组合都是离线数值，不进入搜索、教师、档案或质量评价。新增searchFE=0、decodeFE=0。", "",
        "## H1：固定FA覆盖与返回档案", "",
        "从每个family的逐厂完整jobs集合恢复按job索引的FA；相同family在全部捕获请求中的FA必须一致。solutions中FA按JS位置对齐，先转为按job索引再比较。不同工厂异构，工厂标签不作置换等价。", "",
        "下表仅本轮SHARE_SPECIAL自己的截止档案。其他同期方法也按同一组家族FA作离线覆盖分类，完整结果见archive-coverage/coverage-instances。非家族FA的返回解说明有与当前固定上下文不同的已付费FA；不能据此恢复全部自由粒子访问史、祖先或未留存FA。", "",
        "|campaign|实例|家族FA匹配解占比|非家族唯一FA均值|家族子前沿HV/全HV|非家族独占HV/全HV|", "|---|---|---:|---:|---:|---:|"]
    for row in tables["coverage-instances"]:
        if row["variant"] == "SHARE_SPECIAL":
            lines.append("|" + "|".join([row["campaign"].split("-2026")[0], row["instance"], pct(row["matchedSolutionFraction"]),
                f'{row["nonFamilyUniqueFA"]:.2f}', pct(row["matchedFamilyHVFraction"]), pct(row["nonFamilyExclusiveHVFraction"])]) + "|")
    lines += ["", "HV使用各轮事前归一化与参考点1.5。返回solutions偶有截止后的目标：先与T档案目标逐项精确匹配，只分类匹配到的编码；若T目标缺少返回编码，保留unknown且独占HV比例不判。archive-coverage保留排除数量、未知编码数与已知编码覆盖HV。家族与非家族子集HV有重叠，不能相加；编码覆盖完整时，非家族独占部分定义为HV(全T档案)−HV(家族子集)。这不是来源的因果HV分解。family-fronts与FA-diversity表保留每family/每实际FA的解数和HV；同一FA可能由自由粒子命中，匹配不等于家族谱系归因。", "",
        "## 紧cap：安全下界与池内暂缺", "",
        "直接读取物化ST、机器速度MS、逐阶段工人效率WE、SUT和疲劳参数；不重新生成SUT或调用解码器。合法机器/工人同厂同阶段可独立组合，因此min合法b=(ST/max MS+SUT)/max WE。参数验证alpha/mu/beta≥0、h0∈[0,1]，动态疲劳u≥0，故实际d=b(1+beta*u)≥min b。", "",
        "固定FA的安全必要下界为 max(max_job Σ_stage min b, max_factory,stage Σ_assigned jobs min b / min(M,W))。前项来自单工件阶段串行；后项来自该阶段同时占用机器和工人的工序并发数最多min(M,W)。分别对资源/时间作乐观放松后仍为下界，取max仍安全。每个已付费父本Cmax均检查不低于该值。该下界较弱；cap≥LB不能证明存在满足cap的合法首阶段编码或当前解码器可达日程。", "",
        "|campaign|捕获紧cap请求/运行|cap低于安全LB|紧cap池缺厂|缺厂且未证不可能|", "|---|---:|---:|---:|---:|"]
    for row in tables["request-summary"]:
        lines.append("|" + "|".join([row["campaign"].split("-2026")[0], f'{row["capturedTightRequests"]:.2f}',
            pct(row["impossibleTightFraction"]), pct(row["missingTightFraction"]), pct(row["missingNotCertifiedImpossibleTightFraction"])]) + "|")
    lines += ["", "比例先每seed在捕获窗口内求值，再实例内平均五seed，最后六实例等权。窗口为首8+末8请求，不是全量估计；某seed没有紧cap样本则保持缺失。低于LB仅认证该固定FA下愿望不可能；高于LB而当前池缺厂既可能是暂缺，也可能仍不可达，当前无法区分。不得据此复活已结束的cap反馈。", "",
        "## H2：单个完整工厂替换的有限池潜力", "",
        "对每个捕获请求，以父本其他厂保持不变，枚举一个当前池完整厂记录替换。用max(c_f)、sum(e_f)、sum(w_f)计算潜在完整三目标；按局部jobs/machines/workers判断编码是否真的变化。0.1%为本次描述潜力的尺度，非论文常数。M/E/W各自最优可能来自不同替换，不声称同一个候选同时取得三个最佳值。", "",
        "|campaign|请求有M改善≥0.1%|有E改善≥0.1%|有W改善≥0.1%|有三目标不劣且实质改善|同cap下上述改善|", "|---|---:|---:|---:|---:|---:|"]
    for row in tables["request-summary"]:
        lines.append("|" + "|".join([row["campaign"].split("-2026")[0]] + [pct(row[field]) for field in (
            "anySingleMGainAtLeast01PercentFraction", "anySingleEGainAtLeast01PercentFraction",
            "anySingleWGainAtLeast01PercentFraction", "anyMaterialParetoImprovementFraction", "anyMaterialParetoAtCapFraction")]) + "|")
    lines += ["", "single-factory-potentials.csv保留全部潜在三目标、相对父本变化、来源FE/群/阶段、cap是否满足；single-request-summary记录当前请求全厂组合的对应改善。single-cycle-seeds/instances/summary按九个cycle分层并逐层先seed后实例；没有覆盖的cycle不填0。", "",
        "单厂替换允许父本其他厂记录，即使它们已不在当前保留池；原九查询全厂组合只从截断后池选择。因此两者候选支持集不同，不能把单厂加父本的潜力胜过全厂池选择归因于选择器错误。当前有限池数值潜力也可能重复历史编码或完整来源，不当作免费实际候选、首次新知识、最终HV或新性能证据。", "",
        "现有快照没有实际逐基因交叉前的源整厂块与子代修复前/后的逐厂保留关系，不能识别H2所说的传递损失是否发生、发生率或因果影响。它们只能检验完整厂替换是否存在可测试的支持空间。", "",
        "## 建议主Agent在新性能前冻结的门槛", "",
        "H1资源投入建议：全部四family上下文可识别；至少3/6实例各至少3/5seed在原SHARE截止档案有≥4个非家族FA，且非家族独占HV占比≥1%。满足只支持一次有费用与匹配控制的上下文覆盖试验，不证明刷新必有收益。若门槛不满足，不靠挑实例或调整阈值追结果。", "",
        "H2资源投入建议：至少3/6实例各至少3/5seed捕获到一个编码改变、三目标不劣且至少一目标改善≥0.1%的单整厂替换。它只允许验证整厂传递这一单因素。工程/有界采集应另外明确：实际源厂块标识、FA上下文、来源父本、交叉后及修复后保留率、实际付费候选与完整重放一致性；缺少此信息时不能把质量变化写成已证实的基因完整性损失。", "",
        "以上门槛是基于旧已付费证据的前置建议，不利用夜间新性能择优；主Agent另行冻结。保留四目标角色、JOB_ALIGNED、原Q与原共享，不增加RL，不重启已结束顺序/cap反馈调参。", "",
        "## 复算与边界", "",
        "入口：E:/conda/python.exe -B -m research.night_diagnostics。每次只写新的runs/night-diagnostics-*；原始source路径逐行保留，sources.csv记录读入文件元数据；receipt.json记录0FE和旧根前后检查，元数据检查不冒充内容哈希证明。", "",
        f'恢复family上下文={receipt["familyContexts"]}，捕获请求={receipt["requests"]}，数值单厂替换条目={receipt["numericSingleFactorySubstitutions"]}。旧根大小/修改时间前后不变={receipt["historicalRootsUnchangedBySizeAndMtime"]}。', ""]
    with (output / "report.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
