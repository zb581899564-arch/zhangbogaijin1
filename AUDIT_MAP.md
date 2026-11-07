# 代码与证据复核索引

> 2026-11-07：最新入口为`src/algorithms/diagnostics/working_branch/`与`scripts/working_branch/`，有效运行见`runs/linux-working-branch-probe-20261107-01/linux-results/`，其中build-02、source-02、code-02为生效身份；完整大文件见[snapshot清单与恢复](snapshot/README.md)。原五项审核要求见[更新提示词](PRO_REVIEW_PROMPT.md)，下方保留11月3日历史索引。

## 先核查这些路径

| 对象 | 实际文件与关键入口 |
|---|---|
| 基线与算法注册 | [DynamicSearch.java](src/java/dynamicentries/DynamicSearch.java) 的 `create`；[LongBudgetRun.java](src/java/dynamicentries/LongBudgetRun.java)；本轮实际加载的副本见对应 `runs/<id>/source`，不要拿默认类推断隔离版。 |
| 主循环与 QGS | [CanonicalHmopso.java](src/java/search/CanonicalHmopso.java) 的 `run`、`qgs`、`decompose`；同目录 `SearchState`、`SearchConfig`、`Direction`、`QTable`、`Particle`、`SurvivorSelection`。 |
| 编码与选择 | [SchedulingEncoding.java](src/java/integration/SchedulingEncoding.java)、[JobAlignedPolicy.java](src/algorithms/mechanism/JobAlignedPolicy.java)、[ClassicAlgorithm.java](src/algorithms/classic/ClassicAlgorithm.java)、[ClassicVariation.java](src/algorithms/classic/ClassicVariation.java)、[NsgaSelection.java](src/algorithms/classic/NsgaSelection.java)。 |
| 家族、共享及 UNIFORM | [CooperationSupport.java](src/algorithms/cooperation/CooperationSupport.java) 的 `preference`、`grouping`、`compose`；[FamilyContexts.java](src/algorithms/cooperation/FamilyContexts.java)、[FactoryPool.java](src/algorithms/cooperation/FactoryPool.java)。 |
| 物理与计费 | [DynamicDecoder.java](src/java/model/DynamicDecoder.java)、[DynamicEvaluation.java](src/java/integration/DynamicEvaluation.java)、[BudgetedProblem.java](src/java/runtime/BudgetedProblem.java)、[RunContext.java](src/java/runtime/RunContext.java)、[AnytimeRecorder.java](src/java/dynamicentries/AnytimeRecorder.java)。 |
| 局搜预算审计 | 原 [LocalSearch.java](src/java/search/LocalSearch.java)，[QgsLocalLedger.java](src/algorithms/diagnostics/QgsLocalLedger.java)、[DeepLocalVisits.java](src/algorithms/diagnostics/DeepLocalVisits.java)、[深局搜入口](scripts/run_dynamic_deep_local.py)、[分工消融入口](scripts/run_dynamic_deep_roles.py)。 |
| 复算与比较 | [指标实现](research/dynamic_benchmark/metrics.py)；[比较协议](docs/实验比较协议.md)；[本包独立复算](review_tools/verify_evidence.py)。 |

## 证据目录

最近各目录保留冻结输入、源文件及差异、检查点、运行命令／回执、前沿和已有局搜账本。历史绝对路径只用于溯源。

| 实验 | 运行目录 | 先核对 |
|---|---|---|
| 动态四目标分工 | [dynamic-deep-roles](runs/dynamic-deep-roles-20261103-212007-121034/) | `protocol.json`、`validation.json`、`phase-gaps.json`；各臂 `archive-admissions.csv`、`local-ledger.csv`、`anytime.jsonl`、`run-receipt.jsonl`。 |
| 动态深局搜三臂 | [dynamic-deep-local](runs/dynamic-deep-local-20261103-184901-271850/) | `comparison.json`、`validation.json`、`reused-arms.json`，配额记录臂与正式臂分开；[首次失败](runs/dynamic-deep-local-20261103-184734-192821/status.json)。 |
| 静态 Q 引导等配额 | [paired-static-qgs-guidance](runs/paired-static-qgs-guidance-20261103-184258-768853/) | `validation.json`、`comparison.json`、记录与重放的账本、`source`。 |
| 静态深局搜与发表材料溯源 | [static-qgs-paper-ls-audit](runs/static-qgs-paper-ls-audit-20261103-171052-582206/) | `provenance.json`、`source/variant.diff`、`stage-ledger.json`、`comparison.json`。 |
| 原计费与静态三方 | [historical-nsga-comparison](runs/historical-nsga-comparison-20261103-155556-328249/) | `source/NSGAII-adaptation.diff` 和 `comparison.json`。 |
| 静态/无时长反馈/动态桥接 | [long-budget-bridge](runs/long-budget-bridge-20261103-082221-744929/) | `inputs`、`protocol.json`、`comparison.json` 和各臂回执。 |
| 多实例完整算法与消融 | [270 次初筛](runs/expansion-screen-20261102-001934-525927/analysis/initial/)、[先前四角色对照](runs/cooperation-roles-20261102-231315-641007/analysis/)、[H1](runs/night-research-H1-20261103-010138-848045/analysis/)、[H2](runs/night-research-H2-20261103-015940-032363/analysis/) | 机器汇总、审计、决策、配对指标；本包未收大批原始时间轴或全部轨迹。 |
| v1–v10 局部机制 | [研究路线](docs/研究路线.md)、[v10](runs/fatigue-scale-performance-v10-20261101-003849-681912/report.md) | 运行前协议、summary、audit、负结果。不要拿局部链当完整算法性能。 |

## 本地复核

Python 3.10+，指标复算需要 NumPy。无需网络、Java 或未随包附带的研究运行树：

```text
python review_tools/verify_evidence.py
```

复算核查本包清单、近两轮三臂/双臂回执、解码器计数、相同的 100 个初始解和匹配配额，从检查点前沿重新计算 HV，并用每条档案准入轨迹重建 SPECIAL/UNIFORM 的检查点前沿。脚本不做新搜索，不会伪称复现 Java 结果。它也不代替对算法、实验公平性或发表版身份的审核。

**完整 Java 搜索重跑**：本包不带完整章节 Maven 工程和历史编译缓存。已有授权的原研究工作区可用 JDK17、Maven3.8.9、Python 和对应离线依赖，从 `scripts/dynamic_build.py`、`scripts/baseline_build.py` 及 [原项目说明](PROJECT_README.md) 重建，隔离试验按原脚本指定的冻结 classpath 顺序。由本包独立恢复时，需先取得同版本完整兼容工程和依赖，按运行的源码与冻结输入重建到新目录，不能拿本机命令字符串或当期生产类当成已复跑证明。若审核者无法取得它们，仍可审查源、复算结果和提出最小复现实验。
