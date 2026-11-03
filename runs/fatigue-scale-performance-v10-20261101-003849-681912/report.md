# v10 全36合格实例普通混合规模验证

主单元为强快TEC；36实例为配对单元，每实例先平均3父本。beta0、强慢和均衡完整保留，不以其探索结果换主单元。

|模型|目标|预算|方法|平均改善%|平均完整FE|实际ms均值|最大超时ms|平均noop率|
|---|---|---|---|---|---|---|---|---|
|beta0|TEC|65FE|mix_alternate|8.1074|65.00|272.088|0.000|0.00000|
|beta0|TEC|65FE|swap_rebind|6.0187|65.00|270.256|0.000|0.00000|
|beta0|TEC|65FE|mix_iid|8.1208|65.00|272.928|0.000|0.00000|
|beta0|TEC|65FE|plain|8.9652|65.00|272.092|0.000|0.00000|
|beta0|TEC|0.5s|plain|12.7974|309.21|502.133|11.728|0.00000|
|beta0|TEC|0.5s|mix_iid|12.2398|305.34|502.161|11.241|0.00000|
|beta0|TEC|0.5s|swap_rebind|8.8336|319.29|501.972|9.634|0.00000|
|beta0|TEC|0.5s|mix_alternate|12.0508|305.95|501.990|11.400|0.00000|
|beta0|TEC|2.0s|swap_rebind|11.3526|1276.15|2002.171|16.112|0.00000|
|beta0|TEC|2.0s|plain|16.3153|1238.63|2001.952|9.278|0.00003|
|beta0|TEC|2.0s|mix_alternate|16.0811|1224.70|2001.983|9.825|0.00000|
|beta0|TEC|2.0s|mix_iid|15.9335|1222.02|2002.040|10.803|0.00001|
|strong_fast_recovery|TEC|65FE|plain|8.5035|65.00|272.071|0.000|0.00000|
|strong_fast_recovery|TEC|65FE|mix_iid|8.1846|65.00|272.803|0.000|0.00000|
|strong_fast_recovery|TEC|65FE|swap_rebind|6.3915|65.00|269.828|0.000|0.00000|
|strong_fast_recovery|TEC|65FE|mix_alternate|8.1751|65.00|272.439|0.000|0.00000|
|strong_fast_recovery|TEC|0.5s|plain|11.8651|309.53|502.203|10.315|0.00000|
|strong_fast_recovery|TEC|0.5s|mix_iid|11.7866|306.68|502.240|10.960|0.00000|
|strong_fast_recovery|TEC|0.5s|mix_alternate|11.8906|306.35|502.099|9.843|0.00000|
|strong_fast_recovery|TEC|0.5s|swap_rebind|9.1081|322.12|502.093|11.348|0.00000|
|strong_fast_recovery|TEC|2.0s|mix_alternate|15.7161|1225.57|2001.911|9.572|0.00000|
|strong_fast_recovery|TEC|2.0s|plain|15.8613|1235.76|2002.155|10.028|0.00000|
|strong_fast_recovery|TEC|2.0s|swap_rebind|11.8664|1282.26|2002.283|9.503|0.00000|
|strong_fast_recovery|TEC|2.0s|mix_iid|15.7445|1223.73|2002.073|11.623|0.00000|
|strong_slow_recovery|TEC|65FE|swap_rebind|6.0825|65.00|270.268|0.000|0.00000|
|strong_slow_recovery|TEC|65FE|mix_alternate|7.8832|65.00|272.574|0.000|0.00000|
|strong_slow_recovery|TEC|65FE|mix_iid|7.9001|65.00|272.130|0.000|0.00000|
|strong_slow_recovery|TEC|65FE|plain|8.4356|65.00|271.735|0.000|0.00000|
|strong_slow_recovery|TEC|0.5s|mix_iid|11.4185|306.30|502.019|10.100|0.00000|
|strong_slow_recovery|TEC|0.5s|swap_rebind|8.6498|320.75|502.193|11.466|0.00000|
|strong_slow_recovery|TEC|0.5s|plain|11.3855|309.47|502.123|10.756|0.00000|
|strong_slow_recovery|TEC|0.5s|mix_alternate|11.3485|306.21|502.021|10.673|0.00000|
|strong_slow_recovery|TEC|2.0s|mix_iid|14.7673|1223.37|2002.436|10.245|0.00000|
|strong_slow_recovery|TEC|2.0s|swap_rebind|10.9944|1281.25|2002.095|11.154|0.00000|
|strong_slow_recovery|TEC|2.0s|plain|14.6883|1236.95|2002.200|11.246|0.00000|
|strong_slow_recovery|TEC|2.0s|mix_alternate|14.7737|1222.17|2002.161|10.268|0.00000|
|strong_fast_recovery|balanced|0.5s|plain|12.9833|307.36|501.946|8.838|0.00000|
|strong_fast_recovery|balanced|0.5s|mix_alternate|13.1016|304.81|502.156|10.590|0.00000|
|strong_fast_recovery|balanced|0.5s|mix_iid|13.2008|304.76|502.026|11.104|0.00000|
|strong_fast_recovery|balanced|0.5s|swap_rebind|9.2615|320.62|502.252|10.697|0.00000|

## 主比较12项

|预算|A|B|平均差pp|配对层次95%区间|实例胜/平/负|Holm p|
|---|---|---|---|---|---|---|
|65FE|mix_iid|plain|-0.3189|[-0.7985218488879784, 0.19865015128278604]|15/0/21|1.000000|
|65FE|mix_iid|swap_rebind|1.7931|[1.0508938384464197, 2.573450878041838]|26/0/10|0.000160|
|65FE|mix_alternate|plain|-0.3284|[-0.8369463861843043, 0.1752276073457622]|16/0/20|1.000000|
|65FE|mix_alternate|swap_rebind|1.7836|[1.0113556288106424, 2.592355906409852]|27/0/9|0.000210|
|0.5s|mix_iid|plain|-0.0786|[-0.6636082661183473, 0.48962391465769306]|19/0/17|1.000000|
|0.5s|mix_iid|swap_rebind|2.6785|[1.732883306095705, 3.6970625630247445]|28/0/8|0.000120|
|0.5s|mix_alternate|plain|0.0255|[-0.5404162619489706, 0.5625416975680085]|20/0/16|1.000000|
|0.5s|mix_alternate|swap_rebind|2.7825|[1.8303427172012194, 3.7791431602684153]|32/0/4|0.000120|
|2.0s|mix_iid|plain|-0.1169|[-0.7476769382178645, 0.49240148230853215]|21/0/15|1.000000|
|2.0s|mix_iid|swap_rebind|3.8781|[2.727171010807882, 5.063686738395668]|30/0/6|0.000120|
|2.0s|mix_alternate|plain|-0.1452|[-0.8909382760043851, 0.5440741696361363]|17/0/19|1.000000|
|2.0s|mix_alternate|swap_rebind|3.8497|[2.790837304052523, 4.949898148518631]|30/0/6|0.000120|

全部模型共4320局部链，完整返回解独立核验；数据含重建SUT/standby，参数为合成疲劳场景。只支持共同动态解码器下的局部标量链判断，不是作者成绩复现、完整多目标或新颖性结论。所有尾步超时计费且不接收，实际耗时包含超时；gain/sec与全部费用见summary/completion。
