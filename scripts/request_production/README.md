# 真实共享请求约束供体生产：隔离入口

本模块只服务 `linux-request-conditioned-production-20261106-01` 条件探针，不修改生产算法接口。结果、停止决定和全部费用位于该运行的 `linux-results/`。所有编译、搜索、解码、独立复核和统计在 Linux 执行；Windows 只编辑、传输和验证收到的文件。

依赖固定的 Linux `linux-mature-donor-20261106-01`、其继承的 `linux-pilot-evaluation-20261106-01`，以及项目 runtime 的 JDK17/Python3.11。具体 classpath、实际类 SHA、源输入、依赖和代码身份见运行产物。不能把另一个 checkout 的同名类直接混入。

主要模块：

- `source_protocol.py`、`source_run.py`、`build_capture.py`：冻结并补录原六源前缀，逐项核对已有证据。
- `prepare_contexts.py`、`amend.py`：核查真实请求和原池，按探针运行前的明确修订生成 `inputs-v2`。原首四采样与原协议保留。
- `build_probe.py`、`campaign.py`：隔离构建，先20条工程验收，再72条科学轨迹。独立工程审计不通过时不能运行科学批次。
- `audit_inputs.py`、`audit_moves.py`、`audit_pool.py`、`audit_probe.py`：独立重建输入、精确RNG和GOM候选、接受及原池更新、末次组装和全部付费档案。
- `analyze.py`、`diagnose_supply.py`：完整批次后统一计算三指标、真实目标极值及物理重复诊断；不反馈搜索。
- `report_results.py`、`finalize.py`、`receive.py`：冻结本轮停止决定、核对费用、归档及跨机完整性验证。

Java代码在 `src/algorithms/diagnostics/request_production/`。原FactoryPool直接复用，不新增选择器。每条科学轨迹为511生产FE加1原共享组合FE；不可行时最后一次重评原请求父代，照常计费。M1/C2/E1/W1五个家族受体按共同轮转执行，属于固定模型条件探针，不等于完整原GOM pass。

`CREATE_NEW`/独立输出目录保护冻结记录；失败不得覆盖或更换seed补结果。完整CLI及真实调用参数已逐条保存在运行目录的 `command.json`。本模块不提供后台启动、自动扩量或Goal恢复功能。
