# 首阶段真实重算与实际伴随复用 v3

独立局部链，固定24次子本评价及0.25秒两种预算。所有搜索耗时均实测；JSON磁盘输出、公共输入加载、独立组件校准和离线QA另计。截止后完成的改进未计入限时收益，超时尾部耗时计入实际收益率。

## 预先指定主要单元：强疲劳快恢复、TEC、0.25秒

|方法|最终收益 %|完整耗时 ms|准时完成决策|实际平均q|q>=4的epoch比例 %|首阶段时间占比 %|
|---|---:|---:|---:|---:|---:|---:|
|cut_fatigue|13.4754|253.396|41.53|2.137|9.38|41.86|
|cut_time|13.3999|252.618|42.67|2.230|10.73|42.93|
|local_time|13.3781|252.399|66.00|3.418|20.07|0.00|
|random|11.9672|251.059|136.37|—|—|0.00|

主要单元的完整疲劳边界法配对差（六实例×五seed分层bootstrap2000，描述性）：

|对照|指标|平均差|95%区间|
|---|---|---:|---|
|cut_time|gain|0.00075509|[-0.00233871, 0.00389218]|
|cut_time|gain_per_second|0.00124652|[-0.01228603, 0.01538414]|
|local_time|gain|0.00097278|[-0.00701087, 0.00786028]|
|local_time|gain_per_second|0.00218686|[-0.02907206, 0.02966316]|
|random|gain|0.01508208|[0.00326938, 0.02670546]|
|random|gain_per_second|0.05556250|[0.01039781, 0.09914843]|

## 全部场景与预算

|预算|疲劳场景|方向|方法|最终收益 %|耗时 ms|收益 %/s|实际q|
|---|---|---|---|---:|---:|---:|---:|
|steps|weak|TEC|cut_fatigue|12.3895|194.215|92.8941|1.356|
|steps|weak|TEC|cut_time|12.3092|188.210|94.5200|1.369|
|steps|weak|TEC|local_time|10.6113|125.228|121.1047|1.769|
|steps|weak|TEC|random|5.2408|55.884|141.3686|—|
|time|weak|TEC|cut_fatigue|12.8618|253.079|50.8673|2.109|
|time|weak|TEC|cut_time|12.9010|254.099|50.8617|2.127|
|time|weak|TEC|local_time|13.3646|252.496|52.9701|3.076|
|time|weak|TEC|random|10.9626|251.074|43.6990|—|
|steps|weak|balanced|cut_fatigue|10.0928|191.601|74.2250|1.532|
|steps|weak|balanced|cut_time|10.1012|186.014|75.7560|1.538|
|steps|weak|balanced|local_time|9.0803|121.941|101.5748|1.973|
|steps|weak|balanced|random|5.1565|55.915|135.3903|—|
|time|weak|balanced|cut_fatigue|9.9722|253.446|39.3908|2.352|
|time|weak|balanced|cut_time|9.9444|254.135|39.1579|2.425|
|time|weak|balanced|local_time|10.4113|252.787|41.1921|3.821|
|time|weak|balanced|random|9.0946|251.200|36.2388|—|
|time|strong_slow_recovery|TEC|cut_fatigue|12.3935|253.188|49.0447|2.257|
|time|strong_slow_recovery|TEC|cut_time|12.3308|252.981|48.7770|2.189|
|time|strong_slow_recovery|TEC|local_time|12.7385|252.244|50.5702|3.220|
|time|strong_slow_recovery|TEC|random|10.7326|251.048|42.7911|—|
|steps|strong_slow_recovery|TEC|cut_fatigue|12.0995|192.794|90.7043|1.417|
|steps|strong_slow_recovery|TEC|cut_time|11.9396|188.727|90.7765|1.374|
|steps|strong_slow_recovery|TEC|local_time|10.4613|125.171|120.5792|1.743|
|steps|strong_slow_recovery|TEC|random|5.3939|56.093|144.0817|—|
|time|strong_slow_recovery|balanced|cut_fatigue|9.7909|253.166|38.7466|2.574|
|time|strong_slow_recovery|balanced|cut_time|9.8847|254.701|38.8813|2.722|
|time|strong_slow_recovery|balanced|local_time|9.7496|251.923|38.7101|3.889|
|time|strong_slow_recovery|balanced|random|8.9573|251.294|35.6604|—|
|steps|strong_slow_recovery|balanced|cut_fatigue|9.5368|191.148|68.8643|1.622|
|steps|strong_slow_recovery|balanced|cut_time|9.5764|185.199|71.5916|1.682|
|steps|strong_slow_recovery|balanced|local_time|8.6935|122.139|101.4253|2.011|
|steps|strong_slow_recovery|balanced|random|5.1548|56.212|133.3421|—|
|steps|strong_fast_recovery|TEC|cut_fatigue|12.8704|193.119|97.6939|1.377|
|steps|strong_fast_recovery|TEC|cut_time|12.8092|186.874|99.6576|1.415|
|steps|strong_fast_recovery|TEC|local_time|10.9224|123.668|128.1277|1.814|
|steps|strong_fast_recovery|TEC|random|5.8711|57.153|158.0253|—|
|time|strong_fast_recovery|TEC|cut_fatigue|13.4754|253.396|53.2514|2.137|
|time|strong_fast_recovery|TEC|cut_time|13.3999|252.618|53.1268|2.230|
|time|strong_fast_recovery|TEC|local_time|13.3781|252.399|53.0327|3.418|
|time|strong_fast_recovery|TEC|random|11.9672|251.059|47.6952|—|
|steps|strong_fast_recovery|balanced|cut_fatigue|9.1653|187.820|69.1022|1.760|
|steps|strong_fast_recovery|balanced|cut_time|9.0810|184.714|68.1343|1.765|
|steps|strong_fast_recovery|balanced|local_time|8.0957|117.338|95.9468|2.300|
|steps|strong_fast_recovery|balanced|random|5.1563|55.777|144.2710|—|
|time|strong_fast_recovery|balanced|cut_fatigue|9.2485|253.980|36.4766|2.700|
|time|strong_fast_recovery|balanced|cut_time|9.2273|252.566|36.5883|2.932|
|time|strong_fast_recovery|balanced|local_time|9.4702|252.182|37.5991|4.389|
|time|strong_fast_recovery|balanced|random|8.7431|251.183|34.8362|—|

## 独立组件校准

每个16候选初始池核对数值首阶段与旧日志版一致，组件一次预热+5次测量；这些重复不反馈搜索。

|组件|各case中位数的平均 ms|
|---|---:|
|fast_stage0_pool|3.26754|
|reference_stage0_pool|7.95728|
|generation|1.13782|
|plain_full|0.93621|
|trace_full|1.79640|

## 实际缓存消融

30对强疲劳快恢复TEC固定24步的缓存/每步重建轨迹全部一致：True。平均实际q=1.595，平均少建6.567次伴随；每步重建/缓存总时间比的中位数=1.049，平均总时间节省=14.005ms。

完整epoch分布及接受终止/预算右删失统计保存在summary.json。最终解释见[研究结果](../../docs/动态疲劳成本与复用-v3.md)。这不是整套算法或HV/IGD+结论，疲劳参数与缺失数据均为公开合成/重建。
