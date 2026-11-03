# 张博改进：分布式异构混合流水车间调度研究

目标是在李明哲硕士论文及对应 JMS、ESWA 论文的基础上，形成有独立贡献、可复现的算法研究，以 ESWA 等期刊为投稿目标。当前完成材料对应、基线工程修复与首轮代码核查，尚无新方法优于基线的实验结论。

原始材料保留在上一级的 `李明哲-毕业材料/`，本目录独立存放工作副本、新代码、数据、研究文档和后续结果。未导入其他路径下的历史改进项目，也未将历史实验结论当作当前结果。

## 从这里开始

- [论文与代码对应表](docs/论文与代码对应表.md)：三份核心文献、对应章节和入口。
- [代码核查与修复记录](docs/代码核查与修复记录.md)：已修内容、证据和未解决的科学问题。
- [研究路线](docs/研究路线.md)：基线复现、候选创新及推进条件。
- [实验比较协议](docs/实验比较协议.md)：统一问题、预算、指标和统计方法。
- [验证记录](docs/验证记录-2026-10-31.md)：实际通过的检查及其限制。

## 目录

```text
张博改进/
├─ baselines/chapter3/    第三章 Java 工程副本（工程修复版）
├─ baselines/chapter4/    第四章 Java 工程副本（工程修复版）
├─ data/chapter3/         45 个实例，17 个表头已纠正并留有记录
├─ data/chapter4/         45 个实例
├─ src/java/support/     实例关联和输入检查的公共源码
├─ src/java/checks/      向量、复制、评价及短程搜索检查
├─ src/algorithms/       张博新算法的开发位置，尚未实现研究候选
├─ scripts/              源码准备、修复、数据校正与验证入口
├─ docs/sources/         论文文本提取和核对页图（本地阅读用）
├─ docs/patches/          与原始代码的可审阅差异
└─ runs/                 本次检查日志、以后各次实验的独立产物
```

两章拥有相同 Java 包名，应分别编译、分别启动 JVM，不能把两章的 classes 混入同一 classpath。原工程包含静态实例状态，目前也不支持在同一 JVM 内并行评价多个实例。

## 使用

在本目录打开 PowerShell。当前机器已用 JDK 17、Maven 3.8.9 和本机 Maven 缓存完成验证，无新增依赖下载。

```powershell
python scripts/run_checks.py --chapter 3
python scripts/run_checks.py --chapter 4
```

默认离线编译四个相关 Maven 模块，随后对该章 45 个实例各进行结构和重复评价检查。日志进入新的时间戳目录。换机器后若离线依赖缺失，需先按 Maven 错误准备依赖。

```powershell
python scripts/run_checks.py --chapter 3 --mode probe --skip-build
python scripts/run_checks.py --chapter 4 --mode probe --skip-build
```

`probe` 为小实例的一代搜索诊断，包含独立评价计数。**配置的 200 不是严格 FE 预算**；原算法内部存在额外评价和写死的循环次数，不可用此命令做性能对比。

原批处理 `ALLAlgorithmRun` 及旧 DOE/指标入口尚有硬编码路径和旧问题类引用，请先使用上述受控入口。只把活跃的第三章 `DHFSP`、第四章 `EDHHFSPW` 列为当前验证范围；上游通用问题、其他算法和旧样例未逐一验收。

`prepare_baselines.py` 仅用于首次准备，拒绝覆盖已存在的副本；`repair_baselines.py` 对新鲜副本执行一次，重复执行会报错。现有副本已经修复，无须再次执行。`normalize_instance_headers.py` 根据实际处理时间行数校正副本表头，详细变更保存在 `docs/data_header_repairs.json`。

## 当前边界

可以编译、解码和短程搜索，不等于已经忠实复现论文。正式实验前必须解决三目标与辅助工厂索引混存、真实 FE 计数、随机源统一，以及第四章设置时间和 WA 表示与期刊版本的差异。工程修复带来的变化单独报告，不计作论文的算法创新。
