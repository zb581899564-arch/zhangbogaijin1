# 固定FA家族与整厂共享组合

本模块是七步计划第五步的最小版本，接入点为公共搜索接口`SwarmSupport`。不增加局部算子或新的Q表。

2026-11-03新增的研究入口保持可选：`*_JOB_ALIGNED_UNIFORM`仅把四个物理组的搜索偏好统一为CENTER；原SPECIAL路径保持原目标角色。`CooperationEvidence`记录有界请求池及付费来源，不参与选择。`*_JOB_ALIGNED_DEMAND/SHAM`仅用于一次固定紧cap缺口厂选择验证，原随机厂抽取仍保留，SHAM不覆盖选择；没有新邻域或Q表。默认路径不启用这些研究变体。[实际结果](../../../docs/四子群互补来源与专业分工三步结果-2026-11-02.md)支持保留原角色，固定DEMAND未获清楚收益，结束该规则；旧运行和负结果保持。

- `FamilyContexts`：初始20粒子形成4个固定FA家族（每家族5粒子），按工件身份恢复FA并重绑定资源；提供家族在四群中的配额。80个自由粒子仍可跨厂探索。
- `FactoryRecord`：已付费动态日程的整厂首阶段顺序、机器、工人及真实三目标贡献。记录不可变。
- `FactoryPool`：同完整工件集合的有限非支配池，最多8条，保持极值及确定性多样性；给定T与eta进行池内精确最小化。
- `CooperationSupport`：观察所有已成功评价的家族候选，包括之后被局部搜索拒绝的候选；按冻结节奏生成组合编码。实际组合经过共同评价器计FE，预测只作一致性检查，不能直接进入档案。

联合生成器的`BlockContext`识别`cooperation.fixedFactoryByJob`并直接限制合法候选，防止正式评价前恢复FA导致构造轨迹失真。普通PSO和原普通邻域仍通过共同的评价前恢复钩子处理家族约束。

`SYNC`与`VALUE_SYNC`仅开启家族/配额/重绑定，不维护方案池；`SHARE`与`VALUE_SHARE`相应开启方案池和组合。此轮家族不刷新，不做跨上下文缓存迁移。

单次完整搜索：

```powershell
E:/conda/python.exe scripts/run_dynamic.py --mode VALUE_SHARE --fe 30000
```

完整冻结开发试验及离线统计：

```powershell
E:/conda/python.exe -m research.dynamic_benchmark.protocol
E:/conda/python.exe -m research.dynamic_benchmark.analyze <运行根目录>
```

默认输出全时间轴；完整对比入口省略大体积时间轴文件，但保留四向量、目标和全前沿离线完整重放。数值参数、实例、seed、预算、版本清单、快照及统计口径见`docs/第四五步实验协议-2026-11-01.md`。工程检查入口为`org.uma.jmetal.util.research.cooperation.CooperationChecks`。
