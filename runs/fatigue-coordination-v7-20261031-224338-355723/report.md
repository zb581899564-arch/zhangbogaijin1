# v7 协调障碍有限空间诊断

下表按规模汇总4个预定合成实例。状态为有限空间普查，不能作为独立统计样本。

|N|模式|目标|状态|N1局部|弱N2|封闭平台严格N2|有中性出口|有严格障碍实例数|
|---|---|---|---|---|---|---|---|---|
|3|beta0|Cmax|3072|167|142|58|84|4|
|3|beta0|TEC|3072|12|8|8|0|4|
|3|beta0|TWC|3072|8|4|4|0|2|
|3|beta0|balanced|3072|44|38|38|0|3|
|3|strong_fast|Cmax|3072|182|158|66|92|4|
|3|strong_fast|TEC|3072|18|14|14|0|4|
|3|strong_fast|TWC|3072|8|4|4|0|2|
|3|strong_fast|balanced|3072|59|48|48|0|4|
|3|strong_slow|Cmax|3072|182|158|66|92|4|
|3|strong_slow|TEC|3072|18|14|14|0|4|
|3|strong_slow|TWC|3072|8|4|4|0|2|
|3|strong_slow|balanced|3072|59|48|48|0|4|
|4|beta0|Cmax|73728|1824|1653|485|1168|4|
|4|beta0|TEC|73728|36|32|32|0|4|
|4|beta0|TWC|73728|44|38|38|0|4|
|4|beta0|balanced|73728|236|220|220|0|4|
|4|strong_fast|Cmax|73728|1633|1514|657|857|4|
|4|strong_fast|TEC|73728|88|84|84|0|4|
|4|strong_fast|TWC|73728|65|60|60|0|4|
|4|strong_fast|balanced|73728|464|442|442|0|4|
|4|strong_slow|Cmax|73728|1662|1545|665|880|4|
|4|strong_slow|TEC|73728|81|77|77|0|4|
|4|strong_slow|TWC|73728|38|34|34|0|4|
|4|strong_slow|balanced|73728|477|452|452|0|4|

## 同父本TEC严格障碍的出现/消失

|N|动态模式|仅beta0|仅动态|共有|均无|
|---|---|---|---|---|---|
|3|strong_fast|5|11|3|3053|
|3|strong_slow|5|11|3|3053|
|4|strong_fast|32|84|0|73612|
|4|strong_slow|32|77|0|73619|

## 条件面板17FE普通控制

面板来自三个模式TEC弱障碍并集；同实例/父本在三模式匹配。以下是条件诊断，不是全空间发生率或同时间算法优势。

|N|模式|方法|成功/次数|17FE中位ms|精确P16均值|严格父本成功/次数|严格父本精确P16均值|
|---|---|---|---|---|---|---|---|
|3|beta0|single_job|2/13|2.453|0.1972|0/7|0.0000|
|3|beta0|plain_composite|1/13|2.709|0.2226|0/7|0.1736|
|3|beta0|machine_pair|0/13|2.765|0.0800|0/7|0.0000|
|3|beta0|worker_pair|1/13|2.707|0.1291|0/7|0.0000|
|3|strong_fast|single_job|3/13|2.450|0.2111|0/9|0.0000|
|3|strong_fast|plain_composite|3/13|2.783|0.2697|1/9|0.1547|
|3|strong_fast|machine_pair|2/13|2.749|0.1453|0/9|0.0444|
|3|strong_fast|worker_pair|3/13|2.697|0.1833|1/9|0.0993|
|3|strong_slow|single_job|2/13|2.441|0.2111|0/9|0.0000|
|3|strong_slow|plain_composite|4/13|2.804|0.2697|1/9|0.1547|
|3|strong_slow|machine_pair|3/13|2.651|0.1453|0/9|0.0444|
|3|strong_slow|worker_pair|4/13|2.636|0.1833|1/9|0.0993|
|4|beta0|single_job|6/16|3.361|0.2785|0/6|0.0000|
|4|beta0|plain_composite|7/16|3.341|0.3577|3/6|0.3860|
|4|beta0|machine_pair|10/16|3.365|0.3801|3/6|0.4384|
|4|beta0|worker_pair|6/16|3.479|0.3210|3/6|0.4309|
|4|strong_fast|single_job|4/16|3.547|0.2748|0/8|0.0000|
|4|strong_fast|plain_composite|7/16|3.763|0.3731|1/8|0.1942|
|4|strong_fast|machine_pair|6/16|3.966|0.3751|1/8|0.1518|
|4|strong_fast|worker_pair|5/16|3.737|0.3522|1/8|0.1309|
|4|strong_slow|single_job|7/16|3.310|0.3853|0/6|0.0000|
|4|strong_slow|plain_composite|6/16|3.268|0.4304|1/6|0.3223|
|4|strong_slow|machine_pair|4/16|3.818|0.4403|1/6|0.3416|
|4|strong_slow|worker_pair|6/16|3.742|0.4279|2/6|0.3142|

## 成本与证据

完整解码共237680次；其中普查230400次、普通控制348×17次；证书136条。实验含源码冻结总墙钟37.429秒，读回审计另记audit.json。

```json
{
  "snapshot_ns": 84290700,
  "graph_ns": 1773509600,
  "reference_full": 8,
  "census_full": 230400,
  "census_ns": 27473785800,
  "sample_QA_full": 192,
  "sample_QA_ns": 81103900,
  "landscapes": 96,
  "landscape_ns": 4992536400,
  "witness_full": 816,
  "witnesses": 136,
  "witness_QA_ns": 700918800,
  "control_parent_full": 348,
  "control_child_full": 5568,
  "control_online_ns": 1134971800,
  "control_final_QA_full": 348,
  "control_QA_ns": 326999100,
  "probability_ns": 225554100,
  "control_trials": 348,
  "instances": 8,
  "total_full_calls": 237680
}
```

beta0也可能有协调障碍；dynamic-only只表示同一父本分类发生变化。两步障碍可被普通复合覆盖，不构成新算子独立贡献。标量障碍的Pareto检查只覆盖证书。完整物理/输入/分类/合法路径见npz与jsonl，在线抽样不读取普查表。未修改共享解码器、Java或整套算法。
