# 受影响工厂与不变前缀增量重算 v4

先通过独立旧seed的8640个C/v/费用逐位一致检查，再运行新seed性能实验。1800条链为独立局部机制验证，Java与整套多目标算法未改。

主要限时单元为强疲劳快恢复、TEC、0.25秒，每父本3次时钟重复；先在父本内平均，再做6实例×5seed配对统计，独立父本数仍为30。越界改善不计收益，尾部费用计入实际收益率。

## 主要单元的四种主方法

|方法|平均收益 %|实际耗时 ms|准时完成决策|缓存平均q|真实重算/等价完整工序 %|
|---|---:|---:|---:|---:|---:|
|random|11.0868|251.209|125.79|—|—|
|cut_fatigue|14.8152|253.135|53.28|2.282|18.97|
|cut_time|15.3013|252.581|54.82|2.298|18.99|
|local_time|14.1107|252.496|60.52|3.128|—|

## 主要单元的配对差

收益差按百分点显示；收益率差按百分点/秒。区间仅作机制描述。

|对照|指标|平均差|95%区间|
|---|---|---:|---|
|cut_time|gain|-0.48613|[-1.72884, 0.35803]|
|cut_time|gain_per_second|-2.02787|[-7.00335, 1.39195]|
|local_time|gain|0.70447|[-0.78618, 1.78086]|
|local_time|gain_per_second|2.65593|[-3.25828, 6.93925]|
|random|gain|3.72843|[1.46179, 6.13068]|
|random|gain_per_second|14.43169|[5.59798, 23.82431]|

## 同FE实现消融

每个方法30对完整/增量实现的分数和轨迹须逐项相同，计时包含各自缓存维护。

|方法|对数|全部一致|完整/增量总时间中位比|平均节省ms|完整/增量首阶段时间中位比|
|---|---:|---|---:|---:|---:|
|cut_fatigue|30|True|1.3406|60.947|2.8647|
|cut_time|30|True|1.3393|51.444|2.7346|

## 组件校准

16候选初始池，1次预热+5次重复；独立计时不反馈搜索。

|组件|平均ms|
|---|---:|
|incremental_stage0_pool|1.39711|
|full_stage0_pool|4.36262|
|prefix_build|0.07515|
|generation|1.25510|
|plain_full|1.11974|
|trace_full|2.14743|

## 全部预算/场景/方向

完整实现控制只有repeat0，不能与三次平均直接混用；同repeat实现比较另存summary.json。

|预算|场景|方向|方法|实际运行数|独立父本数|收益 %|耗时 ms|
|---|---|---|---|---:|---:|---:|---:|
|steps|weak|TEC|cut_fatigue|30|30|13.0684|153.529|
|steps|weak|TEC|cut_time|30|30|13.0989|149.129|
|steps|weak|TEC|local_time|30|30|11.4008|132.487|
|steps|weak|TEC|random|30|30|4.6428|59.662|
|time|weak|TEC|cut_time|30|30|14.6818|252.014|
|time|weak|TEC|local_time|30|30|13.7066|252.665|
|time|weak|TEC|random|30|30|11.1934|251.403|
|time|weak|TEC|cut_fatigue|30|30|14.6496|252.933|
|steps|weak|balanced|cut_time|30|30|10.2655|141.235|
|steps|weak|balanced|local_time|30|30|9.6324|132.066|
|steps|weak|balanced|random|30|30|4.7305|59.661|
|steps|weak|balanced|cut_fatigue|30|30|10.2036|150.425|
|time|weak|balanced|local_time|30|30|10.6105|252.694|
|time|weak|balanced|random|30|30|8.8971|251.056|
|time|weak|balanced|cut_fatigue|30|30|11.0031|252.727|
|time|weak|balanced|cut_time|30|30|11.0192|252.529|
|time|strong_slow_recovery|TEC|cut_time|30|30|14.2361|252.800|
|time|strong_slow_recovery|TEC|local_time|30|30|13.2978|252.532|
|time|strong_slow_recovery|TEC|random|30|30|11.0272|251.364|
|time|strong_slow_recovery|TEC|cut_fatigue|30|30|14.4530|253.572|
|steps|strong_slow_recovery|TEC|local_time|30|30|11.2387|131.942|
|steps|strong_slow_recovery|TEC|random|30|30|4.8273|59.535|
|steps|strong_slow_recovery|TEC|cut_fatigue|30|30|12.8601|145.755|
|steps|strong_slow_recovery|TEC|cut_time|30|30|12.5685|144.498|
|time|strong_slow_recovery|balanced|local_time|30|30|9.8534|252.421|
|time|strong_slow_recovery|balanced|random|30|30|8.4662|250.998|
|time|strong_slow_recovery|balanced|cut_fatigue|30|30|10.5747|252.395|
|time|strong_slow_recovery|balanced|cut_time|30|30|10.3833|252.858|
|steps|strong_slow_recovery|balanced|random|30|30|4.5483|60.563|
|steps|strong_slow_recovery|balanced|cut_fatigue|30|30|9.7927|150.823|
|steps|strong_slow_recovery|balanced|cut_time|30|30|9.7009|140.942|
|steps|strong_slow_recovery|balanced|local_time|30|30|9.1011|136.163|
|steps|strong_fast_recovery|TEC|local_time|30|30|11.6351|137.405|
|steps|strong_fast_recovery|TEC|random|30|30|5.0551|62.327|
|steps|strong_fast_recovery|TEC|cut_fatigue_full|30|30|13.4195|216.993|
|steps|strong_fast_recovery|TEC|cut_time_full|30|30|13.1040|201.675|
|steps|strong_fast_recovery|TEC|cut_fatigue|30|30|13.4195|156.045|
|steps|strong_fast_recovery|TEC|cut_time|30|30|13.1040|150.231|
|time|strong_fast_recovery|TEC|random|90|30|11.0868|251.209|
|time|strong_fast_recovery|TEC|cut_fatigue_full|30|30|13.6899|254.217|
|time|strong_fast_recovery|TEC|cut_time_full|30|30|13.7643|253.645|
|time|strong_fast_recovery|TEC|cut_fatigue|90|30|14.8152|253.135|
|time|strong_fast_recovery|TEC|cut_time|90|30|15.3013|252.581|
|time|strong_fast_recovery|TEC|local_time|90|30|14.1107|252.496|
|steps|strong_fast_recovery|balanced|random|30|30|4.3048|60.277|
|steps|strong_fast_recovery|balanced|cut_fatigue|30|30|9.2314|148.947|
|steps|strong_fast_recovery|balanced|cut_time|30|30|9.1506|143.459|
|steps|strong_fast_recovery|balanced|local_time|30|30|8.4681|131.135|
|time|strong_fast_recovery|balanced|cut_fatigue|30|30|10.2473|252.736|
|time|strong_fast_recovery|balanced|cut_time|30|30|10.1703|252.929|
|time|strong_fast_recovery|balanced|local_time|30|30|9.9460|252.864|
|time|strong_fast_recovery|balanced|random|30|30|7.9724|251.113|

完整解释见[研究结果](../../docs/动态疲劳增量重算-v4.md)。公共加载、磁盘输出、离线QA和组件校准不进入搜索时钟，额外调用分别记录；没有以免费真值选候选、免费缓存维护或越界改进抬高成绩。
