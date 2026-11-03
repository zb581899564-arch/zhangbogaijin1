# 第二关：来源与访问层级

检索与核验日期：2026-11-01。任务范围仅为原文审查；没有修改算法、重跑实验或更新旧结果。所有本轮文件位于本目录。

**结果：三篇指定的最接近论文尚无已取得全文，不能把本轮称为已完成这三篇的逐式审查。** 已实际阅读郭鹏等2023的出版方全文HTML、Xu等2025的33页OA PDF、Che等2024的54页作者预印本，并补充阅读一份同主题专利文字。这些来源能约束泛化创新主张，但不能填补三篇最接近论文的具体机制未知项。

## 访问分级

- A：出版方/作者公开完整PDF，已保存原件，相关页已渲染核验。
- B：出版方完整HTML，正文/公式/算法可读；未取得PDF。
- C：出版方摘要、highlights、公开section snippets；不能判断未显示的公式、算法、开销或不存在某机制。
- P：公开专利全文文字，单列披露；公式图未逐图核对，不能冒认期刊论文全文。
- U：用户提供的本地完整PDF，已读相关章节；不因此认定公开OA。

|ID|核验书目信息|级别与实际来源|本次读到的范围|缺口|
|---|---|---|---|---|
|S1|Song, Li, Du, Yu, Xu, Zheng, Li. COR 175 (2025), 106919. DOI 10.1016/j.cor.2024.106919|C：[出版方预览](https://www.sciencedirect.com/science/article/abs/pii/S0305054824003915)，Crossref原始JSON与OpenAlex原始JSON已存raw_metadata/|题名、作者、卷年、摘要、highlights、引言/节概述的公开索引片段|完整PDF、模型公式、实际编码/邻域定义、Q状态动作表、评价调用数均未取得；不能以专利代填|
|S2|Jianlin Zhang, Longbin Ma, Wu Zhao, Jie Cao, Zuohan Chen, Tianpeng Xu. EAAI 162 (2025), 112292. DOI 10.1016/j.engappai.2025.112292|C：[出版方预览](https://www.sciencedirect.com/science/article/abs/pii/S0952197625023000)，Crossref/OpenAlex JSON|题名、作者、卷年、摘要与公开片段|完整PDF、模型疲劳式、DQN状态动作/奖励、邻域与评价成本未知|
|S3|Lin Luo, Xuesong Yan, Dongcheng Li. ESWA 307 (2026), 131022. DOI 10.1016/j.eswa.2025.131022|C：[出版方预览](https://www.sciencedirect.com/science/article/abs/pii/S0957417425046378)，Crossref/OpenAlex JSON|题名、作者、卷年、摘要、highlights及公开片段|完整PDF、9个LLH定义、双学习更新、精确休息/阈值公式与开销未知|
|S4|郭鹏、郝东辉、郑鹏、王祺欣. 浙江大学学报(工学版)57(9) (2023), 1804–1813. DOI 10.3785/j.issn.1008-973X.2023.09.012|B：[出版方全文HTML](https://www.zjujournals.com/eng/article/2023/1008-973X/202309012.shtml)，[书目页](https://www.zjujournals.com/eng/CN/abstract/abstract45969.shtml)|§1.1–1.3、式(1)–(21)、§2.1–2.5、§3.4–3.5与表4/5；相关网页抽取快照见sources/web_extract_guo_patent.json|PDF链接存在，HEAD连接关闭，未下载；引用采用节/式锚点，不虚构PDF页码。§1.1“一道工序”和§2.1图3说明“每件2道工序”有文字不一致，不能替作者静默统一|
|S5|Ying Xu, Shulan Lin, Junqing Li. Machines 13(12) (2025), 1115. DOI 10.3390/machines13121115|A：[出版方PDF](https://mdpi-res.com/d_attachment/machines/machines-13-01115/article_deploy/machines-13-01115.pdf)，[期刊页](https://www.mdpi.com/2075-1702/13/12/1115)|保存33页原PDF及逐页文本；重点§3、§4.2–4.6、Algorithm 1/4、Fig.9、§5.1；p12/p16/p17已渲染目视核对|p17 OS1–OS4集合完全重复，确认是印刷原文而非抽取错误；作者意图的分组映射未知，不能据此写“忠实复现”|
|S6|Ethan Che, Jing Dong, Hongseok Namkoong. Differentiable Discrete Event Simulation for Queuing Network Control. arXiv:2409.03740v1 (2024)|A：[作者预印本PDF](https://arxiv.org/pdf/2409.03740)，[HTML](https://arxiv.org/html/2409.03740v1)|保存54页PDF及逐页文本；重点§3、§4.2.1/4.2.2，p19式(8)与PATHWISE公式；p19已渲染核对|对象为排队网络政策优化；不能把其样本效率数字移植为本调度实验的速度或性能证据|
|P1|云南师范大学. 一种考虑工人疲劳的分布式混合流水车间调度方法及系统. CN119668221B，2025-11-18；对应A版公开2025-03-21|P：[Google Patents公开文本](https://patents.google.com/patent/CN119668221B/zh)|实施例1、图2/图5文字说明、四维编码、六个QLS、九状态说明和1000迭代/30次运行披露；发明人含李俊青、宋昊楠、李佳珂|独立专利披露。书目/发明人有交集不足以认定与S1全文完全一致；疲劳公式图未逐图核验，不用于公式等同性判断|
|X1|Kunpeng Teng, Chao Lu, Caozheng Yan. SWEVO 105 (2026), 102411. DOI 10.1016/j.swevo.2026.102411|C：[出版方公开预览](https://www.sciencedirect.com/science/article/pii/S2210650226001318)，Crossref/OpenAlex JSON|摘要/§4概述显示四层编码、疲劳加权初始化、多邻域协作；它是分布式FJSP，不是DHFSP|未取得全文；尤其不能将ResearchGate页面下其他论文的ALNS摘要错认成本篇的方法|
|X2|李俊、杨方燕. 制造业自动化48(1) (2026), 52–62. DOI 10.3969/j.issn.1009-0134.2026.01.007|C：[出版方书目/摘要页](https://qikan.cmes.org/zzyzdh/CN/10.3969/j.issn.1009-0134.2026.01.007)|元数据、摘要；公开页显示PDF 1984KB，articleID=78083|未取得PDF/正文；INOA、实数编码、反向初始化等仅按摘要记录，不用于确切邻域比较|

## 对三篇指定论文已尝试的公开路径

1. DOI和完整题名检索、出版方`/science/article/pii/`及`/abs/pii/`直接打开：网页工具均403；搜索索引保留公开预览。403是当前访问失败，不能单凭它认定出版方所有访问都受付费限制。
2. Crossref逐DOI API读取：作者顺序、卷、年份、article number已核对，完整响应保留。S1按卷期为2025，S3按卷期为2026；DOI中的年份不是刊载年份。
3. OpenAlex逐DOI读取：三篇当前均`is_oa=false`、`oa_status=closed`、`best_oa_location=null`、`any_repository_has_fulltext=false`；这只是索引状态，不证明所有公开作者稿都不存在。
4. ResearchGate对应页：均显示No full-text available或Request full-text；未发消息请求作者，未使用需登录的索取/购买入口。
5. 题名加PDF/manuscript/repository/arXiv检索，并以作者/机构域名ynnu.edu.cn、lcu.edu.cn、lut.edu.cn、cug.edu.cn、humboldt.edu以及HAL/arXiv/ResearchSquare交叉检索；本次没有定位到能够核验内容的公开稿。没有把“没有定位到”当成新颖性证据。
6. Crossref披露的Elsevier text-mining API入口经网页读取失败；没有借凭据、代理变更或非授权来源获取正文。

## 下载与保存

- S5先HEAD确认3,881,283字节，再从出版方OA资产域下载；实际字节一致，PDF可解析33页。
- S6先HEAD确认5,948,809字节，再从arXiv下载；实际字节一致，PDF可解析54页。
- 均小于500,000,000字节，沿用既有网络；没有宣称已证实DIRECT，没有改代理/路由。
- 原件、提取文本、相关页图与download_log.json均保存在本目录；不传播到其他目录或外部。
- S4公开PDF的HEAD连接关闭，未将未知大小文件强行下载；全文核验使用公开HTML。

本轮检索还覆盖2025–2026 fatigue/dual-resource/DHFSP、ALNS、complementary neighborhood、fast evaluation。补充近邻不能替代S1–S3全文，不能据当前检索给出“首次”“无近似方法”的结论。

## 本地原论文的窄范围补充

L1：Wenqiang Zhang等，ESWA 306 (2026), 130934，DOI 10.1016/j.eswa.2025.130934。U级来源为用户提供的[原PDF](G:/ai/limingzhegaijin/李明哲-毕业材料/eswa2026-最新李明哲第四.pdf)，只读保留原位，没有复制/改写或称为公开OA。本轮核对p7四向量、p9 Table8、p12–13资源向量更新、p13 §4.4、p15 Algorithm5/6与Fig.7、p16 Algorithm7与Fig.8；复用已有p15/p16页图，没有批量渲染。详见[baseline_relation.md](baseline_relation.md)及其无解码结构反例。该补充不填补S1–S3的全文缺口。
