# 有界搜索机制验证：开发证据

H1分开衡量代初P在G/L形成前的精英丢失、G/L池内保留及实际闭环结果。
P∪G∪L相对G∪L的HV增量仅为离线oracle，不表示PARENT闭环收益。

完整运行 54；有效完整代快照 162；排除partial快照 54。

分支gate：RESOLVED，triggered=False。

|比较|同T平均HV变化%|同FE15000平均HV变化%|
|---|---:|---:|
|SO__vs__NSGA|-12.1029|-12.2100|
|SHARE__vs__NSGA|-8.5379|-10.1268|
|SHARE__vs__SO|4.1349|2.3803|

H2：COMPLETE_MATCHED_MATRIX。按instance/origin/phase及相同case×rep配对。
四核使用相同父本/引导/固定reference；CLASSIC_GLOBAL为主普通控制，CLASSIC_PERSONAL为辅助。
NSGA快照的personal为parentA自身，global为真实parentB；自交辅助与真实第二亲控制分别解释。
candidate与paid-batch增量分开；生成及评价费用单列。不能以不同闭环轨迹的入档率推断核的固有因果。

global direction×step的HV趋势为同代固定P下的观察，不能跨不同父本轨迹作因果结论。
IGD+参考为本次已登记分析阶段全部方法/seed的截止有效T档案ND并集；近似、离线且不反馈搜索。
若父代分支未触发，应依controller分支回执记SKIPPED，而非缺失实验。
本报告不评判ESWA资格，不判定整框架方向死亡，也不将离线oracle当闭环效果。
