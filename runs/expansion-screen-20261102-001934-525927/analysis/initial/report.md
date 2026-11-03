# 扩量初筛实际结果

阶段：initial；判定：RED。
主参考点1.5；敏感性点1.25/2.0；先平均同实例seed，再以实例配对。
这是六个开发实例的资源投入判断，不能据此宣称未见实例泛化、创新资格或ESWA发表条件。

|候选|判定|对照|平均HV相对变化|中位数|实质胜/负|最差实例变化|
|---|---|---|---:|---:|---|---:|
|SHARE|RED|BASELINE|+1.903%|+1.212%|3/1|-2.664%|
|SHARE|RED|NSGA2_4V|-7.682%|-7.046%|0/6|-15.374%|
|SHARE|RED|TAIL|+1.334%|+1.404%|4/1|-2.448%|
|SHARE|RED|SYNC|+3.532%|+2.074%|5/0|-0.595%|

SHARE未满足的绿灯项：versus_BASELINE, versus_strongest_external, tail_guard_strongest_external, igdplus_guard_strongest_external, sensitivity_1.25, sensitivity_2.0
SHARE触发的红灯项：strongest_external

|VALUE_SHARE|RED|BASELINE|+1.898%|+0.456%|3/1|-2.449%|
|VALUE_SHARE|RED|NSGA2_4V|-7.686%|-7.741%|0/6|-15.187%|
|VALUE_SHARE|RED|TAIL|+1.327%|+0.646%|2/1|-2.233%|
|VALUE_SHARE|RED|SHARE|-0.011%|+0.002%|0/0|-0.771%|

VALUE_SHARE未满足的绿灯项：versus_BASELINE, versus_strongest_external, versus_matched_parent, tail_guard_strongest_external, igdplus_guard_strongest_external, sensitivity_1.25, sensitivity_2.0
VALUE_SHARE触发的红灯项：strongest_external

## 继续范围

允许进入下一步的候选：
所有逐项数值见criterion-receipt.csv，配对seed差值见paired-seed-differences.csv。
最强经典是一个整体实际方法，未逐实例拼虚拟对手；不使用p值硬门槛。

锁定C*：NSGA2_4V
按冻结规则可复核候选：None

## 费用与工程审计

```json
{
  "status": "passed",
  "runs": 270,
  "genuineFailures": 0,
  "attempted": 18019206,
  "successful": 18019068,
  "timeInterruptedAttempts": 138,
  "maxOvershootSeconds": 0.005597500000000366,
  "offlineValidationDecodes": 46418,
  "assembliesValidated": 38430,
  "fixedFEReached": 270
}
```

搜索时间包含初始化、候选、解码、训练、共享、选择、档案和监测；输入读取、JVM启动、导出和QA另外计入整个初筛墙钟。
嵌套计时不可重复相加；达到FE点为诊断，未达为删失，不补造分数。
旧540次只作开发背景，未混入此轮质量计算。
