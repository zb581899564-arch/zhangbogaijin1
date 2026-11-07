# 成熟状态局搜后筛选隔离入口

本目录仅新增研究入口，未改默认主线或原 GOM/选择器。每个进程运行一个模式；Java 构建和搜索验证由 Linux 控制器执行。

入口为 `research.dynamic.PostLocalProbeRun`，七个参数依次为实例文件、setup 文件、fatigue 文件、输出目录、提取输入目录、模式、sourceSeed。

输入 `points.tsv` 无表头、严格十列：`P|C`、`index`、`sourcePaidByFE`、`role`、`family`、三个逗号分隔目标、JS、FA、MA、WA。P/C 各 100 行，各自 index 为 0–99；同 index 的角色和家族一致，同家族固定 FA 在全部输入中一致。P 保留 Direction 枚举顺序，角色配额从输入读取。整体必须为 free80 加四个 fixed5 家族。`background.tsv` 是共同 A0 的三个制表符分隔目标；A0 必须已经覆盖全部 P/C，导入不允许扩大它。

| 模式 | 第一、二个完整 pass | 选择 | 第三个完整 pass |
| --- | --- | --- | --- |
| RAW_ROLE | 原目标按 role 内 FULL_ROLE 选 100 后连续改善两次 | 改善前执行一次 | 所选并已改善的 100 人 |
| POST_ROLE | P100、C100 各改善一次 | 改善后 role 内 FULL_ROLE | 后选的 100 人 |
| POST_PARETO | 与 POST_ROLE 相同 | 改善后 role 内 FULL_ALL | 后选的 100 人 |

全部局搜调用原 `GomLocalProgram.improve`，保留四职责接受、活供体、完整 cohort 模型和原家族配额。每个 pass 费用为 `B = 100*(2*N-1)-20*(F-1)`，完整模式为 `3*B`。POST 的 P/C 私有接受档案分别从同一 A0 开始；RAW 的三个 pass 和 POST 的最终 pass 从该时刻公共已付费档案开始。公共档案一直累计所有成功付费点，包括被局搜拒绝和未被后选择的点。

原 `GomRunScope` 没有档案重置 API。本模块只适配其观测桥：以原 `PaInternalArchive.offer` 同时更新独立私有档案和公共档案，向原 scope 写入私有 flags、lastPaid 与 paid registry。原 view/model/proposal/accept 程序不复制。`research.postlocal.nativeObserver=true` 仅允许 RAW_ROLE，调用原 scope.observed，供完整三 pass 桥接等价验证。导入 registry 使用负的源费用标记；本探针成功 FE 从 1 计，不把历史点冒充本次费用。

随机合同：probeSeed 为 sourceSeed XOR `0x6c8e9cf5L`；RAW 第一 pass、POST P/C polish 各自重置到 probeSeed；RAW 第二 pass 为 probeSeed XOR `0x9e3779b97f4a7c15L`；全部模式最终 pass 为 probeSeed XOR `0x51d0a7e3L`。每个 pass 在原 GOM begin 前重置 `SeededRandom`。同种子不表示不同 cohort 的模型或提议相同。

工程开关：`research.pilot.physics` 逐付费解复核完整时间轴，`research.postlocal.importQA` 离线复核 200 个导入目标，`research.postlocal.limit` 设置不超过 3B 的真实预算，`research.pilot.failAt=2` 注入第二次已计费评价失败。

输出包括 `catalog.json`、`imports.json`、`events.jsonl`、完成选择后的 `selection.json`/`selected.json`、`passes.json`、`after.json`、`front.json`、`probe.json` 和 `receipt.json`，全部 CREATE_NEW。事件保留 native 记录，另增完整付费 raw 与公私 flags、pass 起止两份档案、种群和费用。`workingView` 是中性重编码视图，`raw` 是实际已评价的状态，两者不要求编码相等。部分截止与评价失败会保存当前合法工作态、原 proposal pending 和实际费用。恰在 B/2B 截止时可记录一个尚未进入 native begin 的下一 pass；是否创建新 workspace 需结合该 pass 的 native view 事件判断。

收据记录 source/probe/pass seeds、B/3B、实际费用、状态、完整付费 SHA、各 B 前缀（`prefix2BSHA256` 为首 2B）、物理/import QA 费用和实际加载类。模块静态审查完成不代表 Linux 构建、桥接、独立重放或科学比较通过；这些由控制器另存证据。
