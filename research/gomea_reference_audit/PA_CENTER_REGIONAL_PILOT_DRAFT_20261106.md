# 固定区域中央：下一性能设计草案

2026-11-06。DRAFT_NOT_A_RUN_CONTRACT。前置199760FE工程通过；本文件不授权跳过入口/桥接检查或直接评价质量，尚无新性能数据。

主候选固定REGIONAL；NO_SPECIALIST只作45个边界偏好消融，不晋升控制。两例仍20_8_5_1、100_2_3_1；拟新seed15910003/15910037、每臂100000实际FE。原128初始尺度和三指标规范保持，不依据本轮结果重定阈值。

拟9臂：REGIONAL、NO_SPECIALIST、原PA_JOINT、PA_EQUAL、NSGA2_DEEP、原NSGA_CTX_GOM、FULL_SHARED_DEEP、LI_RECON_DEEP、普通MOEAD_4V。科学预算3600000FE。普通MOEAD沿有来源的原setting0，不为候选调参；外部指标统一尺度，算法内部正规化保持其原定义。NSGA_CTX_GOM使用原GOM接受，不能称为已经匹配新的区域接受政策。

轻量入口复用已验收的CenterTargets/CenterAssignment/PaRegionalPolicy/PaPopulation字节。REGIONAL/NO_SPECIALIST/OFF须在相同已知工程输入下两完整代复现重观察的整条付费SHA与前沿；所有旧控制的入口更换亦须验证整轨迹与初始解。具体桥接费用与执行顺序在正式合同登记，失败计费保留。

普通MOEAD需要先完成显式路由和实际计费检查：当前PaCapabilitySearch未知臂会落到NSGA；冻结ClassicAlgorithm的MOEAD分支没有深局搜调用。核对其原算法定义、初始化、权重/尺度/理想点更新、同一共享档案与真实FE，保存实际类身份，按普通MOEAD命名。不可直接使用新标签假装已接入。

拟沿用既有投入标准：对原PA、旧共享/Li要求中位HV至少+1%，IGD+/C不反向，参考点及逐seed退化有底线；对NO_SPECIALIST要求独立机制幅度0.5%，其余强普通控制用事前不劣界限。需全部对照、两例及seed保护同时满足；不是显著性或期刊资格。正式合同须给齐数值、共同经验IGD+参考、精确C分子分母、轮换顺序、全费用和停止分支后再执行。

本轮只检验普通区域基座能力与专业接受增量，不主张已经接回原QGS/固定FA家族/条件共享。若候选未达到条件，不改方向网格、分配、接受等号、理想点、预算或seed追正，不挑NO_SPECIALIST等控制作新候选；已有四职责/共享正证据及全部旧停止保持。

执行补充：正式[PA_CENTER_REGIONAL_PILOT_V1](PA_CENTER_REGIONAL_PILOT_V1.json)及0FE编译修订已登记，全部桥接266664FE通过，九臂新seed矩阵正在运行。下方原草案不作为替代运行合同。

执行补充：九臂3866664FE已完成并独立审计，固定REGIONAL未满足跨例三指标条件、停止扩量；详见[完整结果](../../docs/中央固定折中方向九臂三指标结果-2026-11-06.md)。旧协议保留。
