# v9 固定50/50普通邻域混合

主单元：8个全新N=4合成实例、强快疲劳TEC。beta0/慢恢复与4个解释实例全部保留在summary.json，不据单一预算选比例。

## 精确固定父本覆盖/概率

交换重绑定为普通N2子集，混合保留N2支持集，不产生普通复合之外的新终点。概率对应固定父本重复抽样，非在线链效果。

|规则|可改善/严格父本|N2改善终点覆盖均值|P16均值|P32均值|
|---|---|---|---|---|
|plain|142/142|100.000%|14.722%|25.594%|
|swap_rebind|107/142|29.968%|49.349%|60.635%|
|mix_iid|142/142|100.000%|38.953%|53.529%|
|mix_alternate|142/142|100.000%|39.364%|53.771%|

## 同FE与同时间

并集障碍父本未必在每个模式都严格；各记录标明parent_strict。改善是相对初始TEC百分数，每父本平均3seed。

|父本层|预算|规则|平均改善%|完整FE均值|实际ms均值|最大超时ms|两算子均有接收/运行数|
|---|---|---|---|---|---|---|---|
|barrier|33FE|mix_iid|1.7200|33.00|8.861|0.000|4/24|
|barrier|33FE|swap_rebind|1.7197|33.00|6.638|0.000|0/24|
|barrier|33FE|plain|0.5478|33.00|8.710|0.000|0/24|
|barrier|33FE|mix_alternate|1.6780|33.00|8.932|0.000|5/24|
|barrier|0.02s|plain|1.7348|80.29|20.116|0.694|0/24|
|barrier|0.02s|mix_iid|2.7803|79.88|20.497|8.831|9/24|
|barrier|0.02s|mix_alternate|2.8290|79.75|20.218|0.589|10/24|
|barrier|0.02s|swap_rebind|2.2860|97.04|20.101|0.264|0/24|
|barrier|0.08s|mix_alternate|3.6612|328.17|80.140|0.522|17/24|
|barrier|0.08s|mix_iid|3.8525|310.88|80.110|0.333|15/24|
|barrier|0.08s|swap_rebind|2.5520|412.67|80.122|0.269|0/24|
|barrier|0.08s|plain|3.4870|309.46|80.137|0.343|0/24|
|uniform|33FE|mix_alternate|17.6996|33.00|9.733|0.000|18/24|
|uniform|33FE|swap_rebind|15.4027|33.00|7.435|0.000|0/24|
|uniform|33FE|plain|16.8911|33.00|9.643|0.000|0/24|
|uniform|33FE|mix_iid|17.5732|33.00|8.761|0.000|23/24|
|uniform|0.02s|mix_iid|19.1106|73.33|20.145|0.409|23/24|
|uniform|0.02s|mix_alternate|19.3961|75.67|20.160|0.335|20/24|
|uniform|0.02s|swap_rebind|17.0824|96.46|20.101|0.285|0/24|
|uniform|0.02s|plain|18.6693|70.88|20.160|0.502|0/24|
|uniform|0.08s|swap_rebind|17.3093|392.42|80.105|0.210|0/24|
|uniform|0.08s|plain|20.4152|288.04|80.147|0.449|0/24|
|uniform|0.08s|mix_alternate|20.7173|303.83|80.147|0.453|22/24|
|uniform|0.08s|mix_iid|20.5098|310.17|80.134|0.489|24/24|

## 实例配对差：混合减单用

8实例为配对单元，均值差为百分点，未把seed或状态当独立样本。

|父本层|预算|混合|单用|平均差百分点|8实例胜/平/负|
|---|---|---|---|---|---|
|barrier|33FE|mix_iid|plain|1.1722|7/0/1|
|barrier|33FE|mix_iid|swap_rebind|0.0004|2/0/6|
|barrier|33FE|mix_alternate|plain|1.1302|7/0/1|
|barrier|33FE|mix_alternate|swap_rebind|-0.0417|2/1/5|
|barrier|0.02s|mix_iid|plain|1.0455|5/0/3|
|barrier|0.02s|mix_iid|swap_rebind|0.4943|5/0/3|
|barrier|0.02s|mix_alternate|plain|1.0942|7/0/1|
|barrier|0.02s|mix_alternate|swap_rebind|0.5430|6/0/2|
|barrier|0.08s|mix_iid|plain|0.3656|7/0/1|
|barrier|0.08s|mix_iid|swap_rebind|1.3005|7/0/1|
|barrier|0.08s|mix_alternate|plain|0.1742|5/0/3|
|barrier|0.08s|mix_alternate|swap_rebind|1.1091|8/0/0|
|uniform|33FE|mix_iid|plain|0.6820|6/0/2|
|uniform|33FE|mix_iid|swap_rebind|2.1705|5/0/3|
|uniform|33FE|mix_alternate|plain|0.8084|7/0/1|
|uniform|33FE|mix_alternate|swap_rebind|2.2969|6/0/2|
|uniform|0.02s|mix_iid|plain|0.4413|6/0/2|
|uniform|0.02s|mix_iid|swap_rebind|2.0283|7/0/1|
|uniform|0.02s|mix_alternate|plain|0.7268|7/0/1|
|uniform|0.02s|mix_alternate|swap_rebind|2.3138|6/0/2|
|uniform|0.08s|mix_iid|plain|0.0946|3/0/5|
|uniform|0.08s|mix_iid|swap_rebind|3.2004|7/0/1|
|uniform|0.08s|mix_alternate|plain|0.3020|6/0/2|
|uniform|0.08s|mix_alternate|swap_rebind|3.4079|7/0/1|

## 验证与成本

局部链2592条，新完整调用852427次，其中搜索407267次，新普查442368次；复用旧普查221184行。主实验含源码冻结162.735秒，审计另列audit.json。

全部返回解独立重算并检查可行性；所有晚完成子本计费而不接收。实验为合成微例TEC局部机制诊断，覆盖事实不等于新颖性、整体多目标性能或疲劳信息贡献。没有修改共享物理核心或整套算法。
