# 独立 pilot 评价 API

本包只分析已经保存的目标值，不调用 Decoder，不创建实验、不修改现有指标或冻结运行。
HV、IGD+ 和双向精确 C 复用 `research/dynamic_benchmark/metrics.py` 与
`research/dynamic_benchmark/tri_indicators.py`。传统 IGD、EAF、配对描述与阶段贡献分别独立实现。
三目标顺序恒为 `[Cmax, TEC, TWC]`，全部最小化。

## 执行与验收

所有数值检查、统计和分析只在 Linux 运行。本机只开发及读回代码。
从 Linux 项目根目录执行：

```bash
python -m research.pilot_evaluation check
```

该入口在非 Linux 平台直接拒绝。十组小型数学夹具包括独立矩形并集容斥 HV、
IGD 的参考集到前沿方向、IGD+ 支配方向、精确 C 等号/不相交、引用来源和未来信息拒绝、
完整极值向量、逐 seed 与实例层配对、已知 EAF 集合、固定 3D 切片及阶段 telescope。
成功时输出 JSON `status=PASS`；夹具通过只说明这些数学和输入边界，不是科学性能证据。
这里不记录尚未实际运行的验收结果。

## 目标矩阵、尺度与参考集

公共输入必须是有限 `N×3` 目标矩阵；EAF 的 2D 数学函数使用 `N×2`。
不接受把一维数组或错误形状静默 reshape 为合法矩阵。空矩阵可传 `[]`，
缺失/失败运行必须由调用者单独报告，不能静默遗漏。

```python
from research.pilot_evaluation import (
    ObjectiveScale, shared_final_reference, evaluate_front, exact_coverage,
)

scale = ObjectiveScale(lower=(0, 0, 0), upper=(100, 1000, 1000))
# 示例尺度仅演示 API。实际必须使用协议事先冻结的同实例数值。
reference = shared_final_reference(final_fronts)
metrics = evaluate_front(candidate_front, reference, scale, hv_reference=(1.5, 1.5, 1.5))
coverage = exact_coverage(candidate_front, control_front)
```

- `final_fronts`：同一个实例、同一终止预算、全部登记方法与 seed 的
  `{unique_run_id: raw_objective_matrix}`。`shared_final_reference` 对联合目标向量去重并取非支配集，
  保留 source IDs；拒绝空 final run。它是经验参考，不能称真实 Pareto 前沿。
- `ObjectiveScale(lower, upper)`：三维冻结仿射尺度 `(x-lower)/(upper-lower)`，不裁剪盒外点。
  现有按最大值归一化可令 lower 全零、upper 等于原 scale。HV reference 必须已在归一化坐标中。
- `evaluate_front`：返回 `HV`、`IGDplus`、`IGD`、`extremes`。
  `extremes` 对每一物理目标给出全部并列最小点的完整 raw/normalized 三向量与 tie count。
- `igd(front, reference)`：`mean_r min_a ||a-r||2`。`igd_plus` 仍用现有正部距离。
  空 front 的距离为无穷；空 reference 拒绝；`evaluate_front` 需要非空 front 才能给极值。
- `exact_coverage(candidate, control)`：`C_A_B` 即 candidate 覆盖 control，反向同时返回。
  相等计双向覆盖、精确比较、不加 epsilon，去重后的分母和覆盖点数全部保留；空集拒绝。
- 原始数学距离函数允许离线传普通 reference 矩阵。在线调用必须 `online=True`，
  此时只接受带来源及 `available_at` 的 `ReferenceSet(..., offline_only=False, available_at=step)`，
  并要求 `current_step >= available_at`。最终前沿并集永远标记 offline-only 并拒绝在线使用。
  来源与时间的真实性仍由调用者提供；接口不会推断文件内容来自何时。

## 配对描述

```python
from research.pilot_evaluation import paired_summary

summary = paired_summary(paired_rows, metric="IGDplus", higher_is_better=False)
```

每行 schema：`{instance: str, seed: int|str, candidate: finite_number, control: finite_number}`。
调用者应事先按 instance/seed 内连接并单列缺失配对；本函数拒绝重复键、不丢弃失败行。
`metric` 使用 `HV`、`IGDplus`、`IGD` 或其他明确名称；HV 为最大化，IGD/IGDplus 为最小化。

返回 `by_instance`：完整 raw 配对、双方 median/range、配对改善 median/range、逐 seed wins/ties/losses。
改善量统一为正值有利 candidate；`candidate_minus_control` 原差值另保留。
IGD+ 附 `2*(control-candidate)/(abs(control)+abs(candidate))`，两者零时为零，
范围 `[-2,2]`；乘 100 才是对称百分数。它不是传统相对 control 的百分比。
顶层只等权汇总各实例的配对改善中位数、方向和 IGD+ 效应中位数，不把 seed 当独立实例，
不作显著性/非劣性结论、不实现推进门槛。`tie_tolerance` 默认精确零，若更改须事前固定。

## 精确 EAF 与固定三维切片

所有 EAF 映射都是**同一方法、同一实例、同一预算**的 `{seed: front}`，
不能把多个方法的 run 拼作更多 seed。比较方法必须由上层先核对同一 seed 集合。

```python
from research.pilot_evaluation import (
    attainment_probability, attainment_grid, eaf_report,
    fixed_quartile_thresholds, conditional_eaf_slices,
)

# 二维：P[至少一个解弱支配 query]，每个 seed 在每个 query 最多计一次。
probability = attainment_probability(fronts_2d, queries_2d)
report = eaf_report(fronts_2d, include_grid=True)

# 三维：先把统一参考与各前沿用同一个 scale 归一化。
thresholds = fixed_quartile_thresholds(normalized_common_reference, condition_axis=2)
# 阈值仅计算/冻结一次，全部方法原样复用，禁止按方法重新计算。
sections = conditional_eaf_slices(normalized_fronts_3d, condition_axis=2, thresholds=thresholds)
```

- `attainment_probability` 返回精确经验概率；空有效前沿仍占一个 seed 分母。
- `attainment_grid` 默认采用全部目标事件坐标，返回 `probability[y_index][x_index]`。
  默认网格各 knot 右上方的半开矩形内概率恒定，末格延伸到正无穷；最小 knot 之前为零。
  显式 `x`/`y` 时只保证这些坐标处概率精确，不能称覆盖全部跳点。
  超过 `max_cells` 会拒绝，不偷偷降采样。
- `attainment_boundary` 是数学函数，返回 `EAF>=0.5` 的非支配 corners 和水平/垂直 step vertices。
  第一个 corner 向上延伸，最后一个向右延伸；不线性平滑。
- **绘图/呈现统一使用 `eaf_report` 的资格判断**：少于五 seed 时返回
  `SUPPRESSED_FEWER_THAN_5_SEEDS`、`boundary=None`、`grid=None`。
  三 seed 只报告原始配对/范围，不能画 50% EAF 图。包本身不调用绘图库。
- 3D 切片使用共享参考的条件轴 `q25/q50/q75`（显式 linear quantile），
  保留 `objective[axis] <= threshold` 的点后展示另两轴，是精确的固定三维 attainment 截面。
  这是累积截面，非四个分箱，也非抛弃第三目标的无条件投影。空切片 seed 保留原分母。
  相同四分位数允许重复，不抖动阈值或人工拉开。

`eaf_difference(A, B, lower=(l0,l1), upper=(u0,u1))` 要求两方法具有相同 seed ID，
对双方使用同一显式二维归一化范围，并在双方全部事件 knot 的公共网格计算 `EAF_A-EAF_B`。
也可给定同一组归一化 `x/y` 坐标；这时为公共点上的精确概率差，不能称覆盖全部跳点。
正值仅表示 A 更常达成该二维点，不代表三目标优势。展示使用 `eaf_difference_report`，
少于五个配对 seed 返回 `grid=None`；本轮三 seed 不绘制差异图。

## 时序阶段 HV telescope

```python
from research.pilot_evaluation import stage_hv_telescope

ledger = stage_hv_telescope(
    chronological_events, scale=scale, hv_reference=(1.5, 1.5, 1.5),
    initial_front=[], until_event=100000, keep_events=True,
)
```

事件 schema：

```text
event: positive unique increasing integer
objectives: [Cmax, TEC, TWC]  # 原始物理目标，已经支付并完成的真实评价
stage: nonempty str         # 例如 initialization / evolution / local_search
source: nonempty str        # 明确日志来源标签，由调用者作固定映射
sharing: bool              # 是否属于本阶段中的分享事件，不能把字符串当布尔值
completed_at?: finite nonnegative number  # 若提供，每行都须提供且不倒退
```

输入必须已经按真实事件顺序排列，不在看过结果后重新排序。事件 ID 可有间隙；
无法取得目标的失败评价应在费用表单列，不能伪造目标事件。
`initial_front` 必须在事件流开始前已经可用，默认空；不要传最终前沿。
`until_event` 和 `until_time` 只消费符合截止的前缀，不将后续点加入档案。
时间单位不推测，必须与 `completed_at` 相同；有 time cutoff 则每行必须有时间。

每个已付费目标按时序加入累计非支配档案，`delta_hv=HV(after)-HV(before)`。
按 stage 汇总的增量之和等于 `final_hv-initial_hv`，返回逐事件增量及独立求和核对。
`by_stage[stage].sharing` 是该 stage 的子集，`by_source` 也是该 stage 的分解；
**不能将 sharing 再与阶段总和相加**。顶层禁止单列 `SHARING`/`SHARE` stage。
重复/被支配点增量为零；盒外点保留但不贡献盒内体积。浮点舍入范围内可能有极小负增量，
不截成零后掩盖 telescope 差值。阶段贡献依赖时间路径，仅为描述归属，不是机制因果效应。
大日志可 `keep_events=False` 避免重复输出 trace；不改变累计算法。
