# 夜间冻结结构假设 H1

候选：SHARE_ELITE；全局 C*：NSGA2_4V；准入：RED。

六开发实例各五个新 seed，先实例内平均再实例等权。主 HV 参考点 1.5；敏感性 1.25/2.0。
IGD+参考为当轮全部方法与新 seed 的末期有效 ND 并集，仅离线使用。15000FE 未达点保留删失。

|比较|同T平均%|中位%|实质胜/负|最差%|去最佳平均%|同FE完整配对数|
|---|---:|---:|---:|---:|---:|---:|
|SHARE_ELITE__vs__SYNC_STATIC|3.7794|2.2689|3/0|-0.6242|2.6217|6|
|SHARE_ELITE__vs__SHARE_STATIC|1.2320|1.2676|4/1|-2.8907|0.6036|6|
|SHARE_ELITE__vs__SYNC_ELITE|3.8489|2.4718|5/1|-1.0986|2.6811|6|
|SHARE_ELITE__vs__SYNC_RANDOM|3.6913|2.4449|4/1|-1.4890|2.5412|6|
|SHARE_ELITE__vs__SHARE_RANDOM|0.9978|1.1188|3/0|-0.3403|0.6847|6|
|SHARE_ELITE__vs__TAIL|4.8194|4.7337|6/0|2.5381|4.2554|6|
|SHARE_ELITE__vs__NSGA2_4V|-6.2689|-6.2508|0/5|-13.5702|-7.3640|6|
|SHARE_ELITE__vs__SPEA2_4V|-5.4532|-4.8799|0/5|-12.6280|-6.4551|6|
|SHARE_ELITE__vs__MOEAD_4V|-4.9443|-3.5137|0/5|-12.2927|-5.7535|6|
|SHARE_ELITE__vs__NSGA2_VNS_4V|-6.1025|-6.0221|0/6|-13.4863|-7.0308|6|
|SHARE_STATIC__vs__NSGA2_4V|-7.4107|-6.9333|0/6|-13.7199|-8.1189|6|
|SHARE_STATIC__vs__SPEA2_4V|-6.5933|-6.3404|0/6|-12.7793|-7.4607|6|
|SHARE_STATIC__vs__MOEAD_4V|-6.1050|-5.3902|0/6|-12.4446|-6.9122|6|
|SHARE_STATIC__vs__NSGA2_VNS_4V|-7.2524|-6.2141|0/6|-13.6361|-7.7996|6|
|SYNC_ELITE__vs__SYNC_STATIC|-0.0786|0.1460|1/1|-1.6679|-0.3391|6|
|SYNC_ELITE__vs__SYNC_RANDOM|-0.1613|-0.1716|0/1|-1.0454|-0.3415|6|
|SHARE_RANDOM__vs__SHARE_STATIC|0.2350|0.5681|2/1|-4.3180|-0.2434|6|
|SYNC_RANDOM__vs__SYNC_STATIC|0.0819|0.2980|0/0|-0.8742|-0.0774|6|
|SHARE_RANDOM__vs__SYNC_RANDOM|2.6425|1.2046|3/1|-1.1526|1.6043|6|
|SHARE_STATIC__vs__SYNC_STATIC|2.5866|-0.4999|2/1|-1.3853|0.5379|6|

|事前登记交互|同T均值%|同T中位%|同FE均值%|
|---|---:|---:|---:|
|ELITE_refresh_x_sharing|1.2715|2.0768|0.0288|
|RANDOM_refresh_x_sharing|0.0597|0.7476|-0.2339|

交互为事前登记的差中之差，分母与逐项公式见interactions.json；先实例内平均五seed，再实例等权。候选胜过静态基准不能单独证明两因素协同。

所有 v1 准入条件、IGD+保护、参考点敏感性和逐实例/seed原值见 decision.json、effects.json、paired-effects.csv。
本轮 330 个 owner 完整；达到 FE15000 的 owner 为 330。
返回档案重放 49524 次，检查点额外重放 98265 次，二者分别计费与报告。
费用和删失见 audit.json、run-metrics.csv；失败 owner 与不完整 owner 不重跑。
结论限于事前冻结开发配置，不代表新颖性、独立泛化或论文资格；未启动正式第6步，也不自动调参或延时。
