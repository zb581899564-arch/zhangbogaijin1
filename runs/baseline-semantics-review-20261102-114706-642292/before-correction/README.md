# 张博改进：分布式异构混合流水车间调度研究

**原因审计更新（2026-11-02）：** [NSGA-II差距审计](docs/NSGA-II差距原因审计-2026-11-02.md)发现第四章v2的环境选择为100选100，且原文正文要求的局搜前后合并池未落实；两点交叉、共享随机数等更新规则也与当前重建不等价。810项HV独立复核和270次计费/输入核对未发现口径错误。本轮未调参或重跑优化器，应先补齐基线语义验收，再讨论保留四子群与共享的改进；旧分数仅代表冻结v2配置。

**当前状态（2026-11-02）：** 新版第4步[经典对照验收](docs/新版第4步验收-2026-11-02.md)及第5步270次正式初筛完成，用时56分38秒。SHARE对A0平均+1.90%、对SYNC+3.53%，但对本轮整体最强经典NSGA-II平均−7.68%，六实例实质落后；VALUE_SHARE未显示额外收益。两个冻结配置均未满足扩量条件，第6步按预定停止分支未启动正式实验。见[完整结果与分支](docs/新版第5步结果与第6步分支-2026-11-02.md)及[九版本比较](runs/expansion-screen-20261102-001934-525927/analysis/initial/supplement/method-matrix.md)。结论限于当前配置和开发初筛，不扩大为四子群方向判断。

**新版第5步执行依据：** [扩量初筛标准v1](docs/实验比较协议.md)纳入NSGA-II、SPEA2、离散MOEA/D及NSGA-II+VNS；8个性能版本另加SYNC消融，270次单套限时运行中同时取FE检查点，正式搜索39分钟。整个性能初筛上限90分钟（首次经典接入与工程验收另计），本轮无复核资格。规则见[配置](research/dynamic_benchmark/expansion_screen_v1.json)，不对旧540次结果追溯分色。执行顺序与后续条件见[七步计划v2](docs/后续七步计划-2026-11-01.md)。

保留静态基线：**A0-sourced-reconstruction-v2**。两章已接入真实三目标、严格FE、统一随机源和完整调度时间轴，根据论文补全的HMOPSO-QLS/QGS必要验收通过。原始材料保持不动；新动态模型与联合重组器单独命名和运行，动态完整算法开发初筛已完成，正式独立确认尚未开展。

独立疲劳机制已完成[v1同池验证](docs/动态疲劳机制验证-v1.md)、[v2拓扑诊断](docs/动态疲劳拓扑诊断-v2.md)、[v3成本/复用](docs/动态疲劳成本与复用-v3.md)、[v4精确增量](docs/动态疲劳增量重算-v4.md)、[v5扩展验证](docs/动态疲劳扩展验证-v5.md)。v5覆盖全部36合格实例、3个新seed和0.5/2秒预算，15552个逐位比较、2916条链及108对同轨迹对照通过。增量＋时间相对完整首阶段和廉价时间的总体同时间收益稳定；对随机有总体优势，但20工件长预算会落后。疲劳伴随仍是强对照，强快TEC均值略优、均衡方向出现探索性正信号。当前不接入Java整套算法。

最新[v6教师结构学习](docs/教师结构学习验证-v6.md)完成13分层实例/5新seed、520严格同池案例及5200条运行。接收端评分提高同FE收益，但0.5秒下时间边界未胜直接继承，随机均值更高；没有通过独立同时间优势门槛。全部教师评价与轨迹/缓存成本均计费，当前不把该版本接入整套算法。

随后[v7协调障碍诊断](docs/协调障碍诊断-v7.md)已完成8个合成微例、76800状态×3模式、96个景观和348次17FE普通对照。强单工件无改善而两工件联合改善的封闭平台障碍存在，但beta0也有；动态疲劳会改变障碍位置。当前机器/工人链配对会遗漏跨厂机会，未显示相对普通复合的独立优势。共享解码器和整套算法未改；见[v1–v6与四向量控制范围](docs/v1-v6证据与四向量可控范围.md)。

随后[v8普通跨厂交换与重绑定](docs/普通跨厂交换与重绑定-v8.md)完成8解释实例＋4新seed确认实例、5184次局部链及同池/预算审计。交换重绑定在障碍并集层33FE/20ms有条件收益，但保持逐厂数量导致覆盖缺口，均匀层三个预算均落后普通复合；疲劳边界在确认主单元未胜时间边界。保留普通复合作强对照，交换重绑定仅作补充候选，不接入整套算法。

最新[v9固定50/50混合](docs/普通邻域互补混合-v9.md)完成4解释实例＋8新seed确认实例、2592局部链及覆盖/预算审计。随机混合与严格交替保留普通复合支持集，主单元多数单元有正信号；但33FE障碍层对交换单用有预算稀释、80ms均匀层随机混合对普通复合仅小正均值且多数实例落后。保留为更强普通对照，不宣称新颖性或疲劳信息贡献，整套算法未改。见[本日验证记录](docs/验证记录-2026-11-01.md)。

历史v1–v10机制goal按[前三关记录](docs/前三关结论-2026-11-01.md)收束：[v10规模验证](docs/规模泛化-v10.md)完成36合格实例/4320局部链，未建立相对普通复合优势；该系列的[第三关](docs/独立机制准入判断-2026-11-01.md)未启动新机制实验。旧[近邻审查](docs/gate2_literature_20261101/contribution_verdict.md)及其当时的全文缺口作为历史证据保留，后续已定位的相关全文见[资料阅读记录](docs/research/2026-11-01-方案收敛/资料阅读与设计依据.md)；该旧判断不是本轮四子群完整算法的准入标准。多厂一般空间不能套用v9子集结论，见[支持边界](docs/规模泛化支持集边界-v10.md)。

本版本是有来源记录的规范重建。作者benchmark的原始SUT、standby参数和部分论文实现细节无法从当前材料唯一恢复，不能冒称已复现论文成绩表。

## 使用

在本目录打开PowerShell。使用现有JDK17、Maven3.8.9、Python，依赖从本机Maven缓存离线读取。

```powershell
# 第三章，standby=1为显式沿用旧代码的重建假设
python scripts/run_baseline.py --chapter 3 --fe 6500 --seed 271828 --standby-power 1

# 第四章，明确生成重建SUT，不是作者原数据
python scripts/run_baseline.py --chapter 4 --fe 6500 --seed 271828 --standby-power 1 --reconstruct-setup-seed 314159
```

默认实例为 `20_2_3_1.txt`，用 `--instance` 指定本章data目录内的文件。第四章已有可追溯设置时间时改用 `--setup-file <文件>`，格式见[模型合同](docs/模型合同.md)。不提供SUT时直接拒绝，不回退到处理时间的10%。

第四章9个不满足ESWA式(8)的原始实例默认拒绝；`--diagnostic-model-exception` 仅用于显式诊断并在输出标记。其余36个满足该资源条件，但仍须记录SUT与standby来源。

每次运行写入新的 `runs/baseline-时间戳/`：配置、来源、真实搜索FE、阶段诊断、三目标前沿、四向量和完整时间轴。返回解额外离线重解码核验，次数单独报告，不反馈搜索。`--skip-build` 仅在源码未改且已成功构建后使用。

两章包名相同，每次运行单实例、单线程、独立JVM。旧兼容静态表仍存在，不支持同JVM多实例并发。旧批处理和已知有错的旧主搜索run()已明确拒绝，正式运行使用上述受控入口。

## 验证与阅读

```powershell
python scripts/verify_baseline.py --chapter 3
python scripts/verify_baseline.py --chapter 4
python scripts/check_entry_guards.py
```

验证覆盖90实例结构、270套编码的完整时间轴、Q更新与四群隔离、父本不变、九邻域、预算中途耗尽和相同seed完整返回解集。只有搜索模块变化时，可使用 `verify_baseline.py --chapter N --search-only` 进行相关复查。

- [基线验收报告](docs/基线验收-v2.md)：实际证据和适用范围。
- [模型合同](docs/模型合同.md)：公式、四向量、SUT、工人占用及论文歧义。
- [预算与随机源](docs/预算与随机源.md)：失败计费、独立档案和单线程约束。
- [主算法论文一致性审查](docs/主算法论文一致性审查.md)：旧实现错误与公开重建约定。
- [动态疲劳机制验证](docs/动态疲劳机制验证-v1.md)、[模型与伴随](docs/动态疲劳模型与伴随.md)、[冻结协议](docs/动态疲劳机制验证协议-v1.md)。独立入口：`python -m research.fatigue_mechanism`，每次写新目录；不启动MOPSO。
- [拓扑诊断v2](docs/动态疲劳拓扑诊断-v2.md)、[v2协议](docs/动态疲劳拓扑诊断协议-v2.md)。独立入口：`python -m research.fatigue_topology`；随后用 `python -m research.fatigue_topology.analyze <新run目录>` 汇总，不覆盖旧实验。
- [真实成本与复用v3](docs/动态疲劳成本与复用-v3.md)、[v3协议](docs/动态疲劳成本与复用协议-v3.md)。独立入口：`python -m research.fatigue_reuse`；随后用 `python -m research.fatigue_reuse.analyze <新run目录>` 汇总。单线程局部链，接受即缓存失效。
- [精确增量重算v4](docs/动态疲劳增量重算-v4.md)、[v4协议](docs/动态疲劳增量重算协议-v4.md)。先运行 `python -m research.fatigue_incremental validate`，通过后 `python -m research.fatigue_incremental run <validation目录>`；汇总用 `python -m research.fatigue_incremental.analyze <performance目录>`。验证未通过或核心源码/实例改变会拒绝性能入口。
- [全部36实例扩展验证v5](docs/动态疲劳扩展验证-v5.md)、[v5协议](docs/动态疲劳扩展验证协议-v5.md)。入口为 `python -m research.fatigue_expansion validate`、`python -m research.fatigue_expansion run <validation目录>`、`python -m research.fatigue_expansion analyze <performance目录>`；全源码与实例校验后才运行。五条路线、两个主预算及全部补充/退化单元完整保留。
- [论文与代码对应表](docs/论文与代码对应表.md)、[研究路线](docs/研究路线.md)、[实验比较协议](docs/实验比较协议.md)。
- [研究推进评估](docs/研究推进评估-2026-10-31.md)：结合v1–v5与初步查新，区分已有证据、原idea未验证部分和ESWA目标所缺证据；未启动新实验。
- [教师结构学习v6](docs/教师结构学习验证-v6.md)、[v6冻结协议](docs/教师结构学习验证协议-v6.md)：先 `python -m research.fatigue_teacher validate`，通过后 `python -m research.fatigue_teacher run <validation目录>`；随后 `analyze <performance目录>`、`report <performance目录>`。FA固定/迁移、同池/同FE/同时间分开，保留全部负结果。
- [协调障碍v7](docs/协调障碍诊断-v7.md)、[v7协议](docs/协调障碍诊断协议-v7.md)、[六轮证据与四向量](docs/v1-v6证据与四向量可控范围.md)：`python -m research.fatigue_coordination`，独立有限空间普查和普通复合控制，不启动MOPSO。
- [普通交换与重绑定v8](docs/普通跨厂交换与重绑定-v8.md)、[v8协议](docs/普通跨厂交换与重绑定协议-v8.md)：`python -m research.fatigue_exchange`，覆盖、33FE、20/80ms及同池信息增量分开，自动冻结、审计和汇总。
- [普通邻域混合v9](docs/普通邻域互补混合-v9.md)、[v9协议](docs/普通邻域互补混合协议-v9.md)：`python -m research.fatigue_mixture`，单用/50%随机/严格交替，33FE及20/80ms分层验证，不启动整套算法。
- [规模验证v10](docs/规模泛化-v10.md)、[v10协议](docs/规模泛化协议-v10.md)：`python -m research.fatigue_scale validate`、`python -m research.fatigue_scale run <新validation目录>`；65FE/.5/2秒与全部36实例，单进程冻结/审计。完整goal证据见[三关收束](docs/前三关结论-2026-11-01.md)。

## 代码职责

```text
baselines/chapter3,chapter4/   两章独立工程与兼容入口
src/java/model/               数学模型、SUT、解码、时间轴和约束验证
src/java/runtime/             严格FE、独立非支配档案、统一随机源
src/java/search/              四群、离散PSO、个人历史、QLS/QGS与分层局搜
src/java/integration/         物理三目标、工厂元信息、合法编码和旧问题接入
src/java/normalized/          受控运行、导出和真实实例集成检查
src/java/*checks/             对应模块的必要检查
data/chapter3,chapter4/        数值副本；17个第三章表头已校正
scripts/                      源码迁移、构建、运行和验收
docs/                         模型合同、研究协议、审查、差异和历史
runs/                         各次独立产物，保留失败及旧诊断证据
research/fatigue_mechanism/    独立动态疲劳前向、伴随与同池机制诊断
research/fatigue_topology/     小扰动/合法编辑分层、阶段边界对照与误差分解
research/fatigue_reuse/        数值首阶段、实际缓存周期与等FE/时间局部链
research/fatigue_incremental/  精确工厂/前缀复用、先验证后计时、实现对照与重复统计
research/fatigue_expansion/    36实例新seed/长预算、五路线对照、实例层统计与分层边界
research/fatigue_teacher/      付费精英教师、合法块继承、接收端评分及独立同池/费用验证
src/algorithms/               未来整套新算法位置，尚未接入疲劳机制
```

公共模块以src/java内源码为准，构建时同步到对应章core。迁移顺序为 `prepare_baselines.py` → `repair_baselines.py` → `normalize_objectives.py` → `install_normalized_model.py`，仅用于新鲜副本，现有副本已经完成，重复迁移会拒绝。后续修改公共模块只同步和构建。表头修复单独由 `normalize_instance_headers.py` 执行并记录。

后续先冻结模型与重建数据，再恢复或适配公平经典对照。原交付NSGA-II/SPEA2含作者扩展，本次未将它们作为已验收经典算法。之后按协议研究改进，以ESWA等期刊为投稿目标；工程修复不计作新方法贡献。
