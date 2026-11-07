# 局搜后筛选隔离探针

仅用于 `linux-postlocal-selection-20261106-01` 的冻结条件实验，不是默认算法入口。科学协议见运行目录 `protocol.json`，中文说明见 `docs/当前创新主张与局搜后筛选验证协议-2026-11-06.md`。

- `prepare.py`：从旧源记录取每个真实职责首批 P/C，保留重复；不运行搜索或解码。
- `protocol.py`、`build.py`、`run.py`：冻结协议、编译隔离类、工程通过后顺序执行三臂。
- `audit.py` 及其命名模块：独立复算输入来源、模型、供体混合、接受、选择、档案、截止和费用；只核工程证据。
- `analyze.py`：完整科学批次及审计通过后，统一构造参考集并计算全部预登记指标。
- `plot.py`：展示全部配对值，两个实例共用坐标，不从中途结果挑选样本。
- `finalize.py`：记录全部费用、继承身份与决定，然后打包不可变证据。

所有搜索、解码 QA、审计、统计与绘图必须在 Linux 执行。Windows 仅开发、传输、验收文件完整性和查看。

## 复算命令形态

在 Linux 指向保存的运行目录和 Python 3.11 环境。首次运行示例：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python audit.py --root "$RUN" --stage engineering
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python audit.py --root "$RUN" --stage science
python analyze.py --root "$RUN" --anchor "$ANCHOR" --donor "$DONOR" --output "$NEW_REPORT"
```

审计也支持 `--run "$CASE" --input "$CONTEXT" --root "$RUN" --output "$NEW_AUDIT"`。所有输出采用新建模式，复算必须指定新文件/目录；不能覆盖冻结结果。

`RAW_ROLE` 先按原职责筛选再做三轮局搜；`POST_ROLE` 和 `POST_PARETO` 分别改善 P/C 后筛选并继续一轮局搜，总费用均为三轮。POST 两臂改善前缀逐项一致，所有已付费结果计入公共档案。普通 Pareto 控制仅替换筛选偏好，保留局搜四职责和原家族配额。

继承的运行包须另外保存：原 Linux pilot 的输入、代码、依赖和指标实现；成熟供体包的源快照与类。新包中的 `inherited-identity/index.json` 说明这些依赖，不宣称单个新 ZIP 是完整运行时。

六份首批实际均无直接共享提议，故不能用本轮结果评判共享提议的独立价值。三份已有开发 seed、短程条件实验、带观察开销的时间，也不能替代新 seed 完整算法或真实限时验证。
