# 动态疲劳机制诊断 v1

这是独立机制验证，不涉及整套算法改动。三个选择器对同一候选池评分；先固定预测与平局集合，再完整重解码全部候选核验。

完成 90 个父本/疲劳场景，完整核验 1440 个候选。三目标的归一化尺度固定为各自父本目标值；收益为相对于父本的标量下降量。

`accepted_gain` 是统一拒绝变差后的期望收益；random 为均匀选择全部候选的精确期望，预测平局也均匀处理。`time_only` 在 Cmax 方向是普通关键路径，其他目标是对应的时间通道控制。

|场景|方向|方法|Spearman|改善概率|接受收益 %|成本代理 ms|收益/成本 %/ms|
|---|---|---|---:|---:|---:|---:|---:|
|weak|Cmax|fatigue_adjoint|0.077|0.440|2.7211|10.537|0.3815|
|weak|Cmax|time_only|0.087|0.440|2.7211|10.079|0.3976|
|weak|Cmax|random|—|0.202|0.6245|5.578|0.1709|
|weak|TEC|fatigue_adjoint|0.249|0.667|1.0185|10.505|0.1345|
|weak|TEC|time_only|0.254|0.667|1.0185|10.042|0.1406|
|weak|TEC|random|—|0.512|0.3643|5.578|0.0960|
|weak|TWC|fatigue_adjoint|0.226|0.600|0.0734|10.491|0.0088|
|weak|TWC|time_only|0.188|0.600|0.0614|10.042|0.0057|
|weak|TWC|random|—|0.433|0.0443|5.578|0.0108|
|weak|balanced|fatigue_adjoint|0.130|0.700|1.1713|10.495|0.1642|
|weak|balanced|time_only|0.147|0.667|1.1613|10.040|0.1686|
|weak|balanced|random|—|0.519|0.3070|5.578|0.0832|
|strong_slow_recovery|Cmax|fatigue_adjoint|0.055|0.404|2.5659|10.619|0.3436|
|strong_slow_recovery|Cmax|time_only|0.059|0.470|2.5981|10.194|0.3532|
|strong_slow_recovery|Cmax|random|—|0.225|0.6981|5.500|0.1841|
|strong_slow_recovery|TEC|fatigue_adjoint|0.241|0.833|1.0869|10.582|0.1495|
|strong_slow_recovery|TEC|time_only|0.232|0.767|0.9795|10.197|0.1359|
|strong_slow_recovery|TEC|random|—|0.523|0.3724|5.500|0.1005|
|strong_slow_recovery|TWC|fatigue_adjoint|0.177|0.567|0.2166|10.579|0.0281|
|strong_slow_recovery|TWC|time_only|0.134|0.567|0.1846|10.153|0.0310|
|strong_slow_recovery|TWC|random|—|0.463|0.0962|5.500|0.0256|
|strong_slow_recovery|balanced|fatigue_adjoint|0.153|0.700|1.1798|10.609|0.1605|
|strong_slow_recovery|balanced|time_only|0.134|0.767|1.1540|10.177|0.1628|
|strong_slow_recovery|balanced|random|—|0.502|0.3350|5.500|0.0892|
|strong_fast_recovery|Cmax|fatigue_adjoint|0.072|0.444|2.1283|10.520|0.2404|
|strong_fast_recovery|Cmax|time_only|0.027|0.404|2.0086|9.986|0.2408|
|strong_fast_recovery|Cmax|random|—|0.212|0.6175|5.483|0.1580|
|strong_fast_recovery|TEC|fatigue_adjoint|0.183|0.733|1.1189|10.457|0.1539|
|strong_fast_recovery|TEC|time_only|0.184|0.767|1.2181|9.977|0.1673|
|strong_fast_recovery|TEC|random|—|0.508|0.3993|5.483|0.1142|
|strong_fast_recovery|TWC|fatigue_adjoint|0.261|0.667|0.5292|10.415|0.0805|
|strong_fast_recovery|TWC|time_only|0.213|0.667|0.4515|10.006|0.0760|
|strong_fast_recovery|TWC|random|—|0.473|0.1619|5.483|0.0421|
|strong_fast_recovery|balanced|fatigue_adjoint|0.129|0.700|0.9762|10.435|0.1147|
|strong_fast_recovery|balanced|time_only|0.091|0.767|0.9591|9.976|0.1176|
|strong_fast_recovery|balanced|random|—|0.487|0.3275|5.483|0.0870|

配对差及分层 bootstrap 95% 区间见 summary.json 的 paired_comparisons；按场景和方向分开，未把四个方向当作独立重复。这里只作机制诊断。

## 成本口径

指导选择代理成本：父本与子本各一次 trace 解码，加候选生成、伴随、局部 defect、评分与选择；随机：父子各一次 minimal 解码、候选生成与均匀选择。分量分别取5次预热后测量的中位数。没有模拟完整搜索，也没有将全候选事后核验免费计入在线算法。

全解码调用（包含每项一次预热）：

- parent_for_prediction: 90
- offline_all_candidate_truth: 1440
- timing_plain: 540
- timing_trace: 540

## 边界

- SUT 是固定 seed 的 U[1,9] 重建，standby=1；疲劳参数为合成强弱场景，无实测人体数据。
- 最早开工、append-only、后阶段 ECT/FAM；没有插空、右移、主动休息或疲劳硬阈值。
- 局部 defect 使用旧前驱状态和旧伴随，后续重排/资源切换会造成预测误差；导数正确不保证大幅离散编辑预测正确。
- 时间来自本机 Python 原型，只能评估本实现，不能直接当作 Java 或完整优化器开销。
- 未比较 HV/IGD+，未调整原 Java 基线，不能据此宣称达到期刊发表标准。
