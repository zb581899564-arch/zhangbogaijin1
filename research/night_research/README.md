# 冻结夜间实验框架

本目录独立实现 setting-aware loader、330-owner H1与300-owner H2清单、单JVM编排、原始一小时与绝对07:00双截止、全返回档案QA检查、同轨迹双预算、同期指标和现行v1准入。每阶段需先由主代理确认诊断与工程验收通过，两个结构不组合，不启动额外疲劳矩阵。

```powershell
E:/conda/python.exe -B -m research.night_research check
E:/conda/python.exe -B -m research.night_research run <ENGINEERING> research/night_research/h1_context_v1.json
E:/conda/python.exe -B -m research.night_research resume <RUN_ROOT>
```

`ENGINEERING`须包含`acceptance.json`（`status=passed`）、相对项目根目录的SHA256 `source-manifest.json`及实际`classpath.txt`。程序冻结这些证据、Java/Python源码、输入、归一化、规则、执行清单和原始时钟。`prepare`可单独冻结，但从冻结开始计时；不能提前冻结后重新起表。

每个假设只允许一个已准备owner。完整owner可在原时钟内续接；任何已存在的不完整owner都会拒绝重跑。失败进程、部分文件、进程/验证费用和状态均保留。全矩阵未完成不判灯。`analyze`也受同一个原始时钟和绝对截止约束。

Java固定22参数：保留既有21参数的顺序，锁定各方法setting、`SCREEN`、`SemanticAudit=true`，参数17至20均为false。全部方法的`extra_args`统一为`["SNAPSHOT_GENOMES"]`，第22参数只开启共同的检查点编码证据；完整FeedbackAudit、CooperationEvidence、机制重放和保留父代均未启用。

每个reached检查点的每个目标点必须有严格匹配的四向量与出生FE/时间，`checkpoint-validation.json`必须与`summary.checkpointEvidence`完全一致。检查点独立完整重解码按目标三元组去重，额外次数和费用单列；原返回档案QA次数保持原义。迟于T的admission不能替代此前检查点编码。

ContextRenewal校验包括完整付费/个人历史计数闭合、first4+last4+partial界限、CENTER PDDR稳定排序、ELITE/RANDOM选择、当前free来源见证、FA新颖性、family轮换和epoch连续性。允许预算中断留下0至4个成功重评的partial；超过T的事件单列，不当作截止内贡献。事件只有有限来源见证，不冒称离线重建了整个当前population。

FactoryTransfer校验包括12格实际机会计数、每格每四次调用、六次随机draw、paid/pending闭合、first8+last8付费事件、来源paid FE与代数、ROLE严格较小选择和PACKET/MOSAIC按job拼接。独立重建的本厂编码必须同时等于beforeRepairLocal和actualLocal；actualLocal的untracked元数据不是来源付费记录。相同编码必有时间轴匹配见证，MOSAIC编码不同仍允许时间轴相同。其他厂未变与时间轴比较由Java见证，未声称离线重建整父本。报告单列实际付费、截止内付费和本厂保留率，不新增准入阈值。

主HV参考点1.5，敏感点1.25/2，IGD+逐实例使用当轮所有方法×五新seed末期有效档案ND并集。先seed平均再实例等权；FE15000未达点删失，完整配对单独列出。C*为一个全局经典方法。当前v1全部保护条件保持原值，映射基准均为同期SHARE_STATIC，H1匹配控制为SHARE_RANDOM，H2为ROLE_MOSAIC，强普通控制均为TAIL；交互另列，不替代准入条件。

H1共330次，预计搜索2860秒，其他全部工作只能使用一小时内剩余740秒。框架不因预算紧张省略QA、延长时钟、替换seed或启用自动复核。

H2共300次，预计搜索2600秒，其他工作使用同一小时内剩余1000秒。工程侧可调用`trials.load_trial(folder, instance, seed, label, spec)`一次验收共同预算/检查点和对应机制schema；正式`execution.load_run`另检查完整命令与进程费用receipt。维度统一使用`N_K_F_id`与物化`F K N`表头合同，工厂数来自文件名第三项。
