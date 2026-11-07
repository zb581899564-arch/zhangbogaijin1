"""Write the decision and transparent cost clarification; preserve all original records."""
import argparse
from common import *


def main(root):
    accounting = read(root/'accounting.json')
    source, = rows(root/'pa-source/run-receipt.jsonl')
    effective = dict(accounting)
    effective.pop('allFullDecoder', None)
    effective.update(candidateAndImportQAFullDecoder=True, sourceUsesFrozenExactIncrementalDecoder=True,
       sourceDecoder=source['decoder'], supersedes='accounting.json metadata field allFullDecoder only',
       clarification='Original accounting allFullDecoder described candidate/import QA too broadly; source PA uses frozen incremental decoding. FE/QA counts unchanged.')
    write(root/'accounting-v2.json', effective)
    updates = []
    for name, anchor in [('GomLocalProgram','if (keep) w.values.set(slot, state);'),
                         ('PaPopulation','if (accepted) population.set(i, child);')]:
        path = OLD/'build-01/source'/(name+'.java');text=path.read_text()
        assert text.count(anchor)==1
        updates.append(dict(source=str(path),sha256=sha(path),anchor=anchor,
                            line=next(i for i,l in enumerate(text.splitlines(),1) if anchor in l)))
    write(root/'update-semantics.json',dict(evidence=updates,
          conclusion='Both commit an accepted local child immediately; no support for a blanket delayed-update explanation.',
          limitation='Outer lifecycle, population/family domains and model relearning remain different; not causally isolated here.',
          probe='All three arms freeze parents and models, so continuation and adaptation cannot cause their difference.'))
    audit=read(root/'independent-audit.json');numeric=read(root/'analysis/numeric-audit.json')
    comp=[r for r in read(root/'analysis/comparisons.json') if r['background']=='A0' and r['comparison']=='PA_RESOURCE_vs_S_RESOURCE']
    summaries=read(root/'analysis/summaries.json');trigger=read(root/'analysis/triggers.json')
    quality=read(root/'analysis/entry-quality.json');decision=read(root/'analysis/decision.json')
    support=read(root/'prepared/support-triage.json')
    main_table=[]
    for c in comp:
        a,b=c['C_A_B'],c['C_B_A']
        main_table.append(f"| {c['context']} | {c['HVpercent']:+.6f}% | {c['IGDplusImprovementPercent']:+.6f}% | {a['covered']}/{a['denominator']} ({a['C']:.4%}) | {b['covered']}/{b['denominator']} ({b['C']:.4%}) |")
    capacity=[]
    for s in summaries:
        if s['background']=='A0':
            capacity.append(f"| {s['context']} | {s['arm']} | {s['freshCandidates']} | {s['relativeGainHVpercent']:.6f}% | {s['final']['IGDplus']:.10g} |")
    costs={kind:sum(read(p)['seconds'] for p in (root/kind).glob('*/process.json')) for kind in ('qa','paid')}
    text='''# 中段资源供给反事实结果（2026-11-07）

本轮工程核查与最小反事实已完成。按事前门槛，**停止把“中段单独替换资源来源”作为当前推进方向**；保留一个晚入口的局部信号，不把它扩大成稳定算法收益。四子群、QGS、家族、原共享和默认主线未改，没有扩实例、优化seed或恢复Goal，也没有后续后台实验。

## 三个因素分别查到了什么

入口：SHARE的实际POST_GLOBAL时点为104540、179120、228840；配对PA模型入口分别为99600、159300、219000（滞后4940、19820、9840 FE），不使用未来供体。PA入口群体HV高约1.696%、3.378%、4.562%，但双向C在前两个时点仍反向，只有末时点三指标同向。因此入口不同已经存在，不能把自然轨迹差值归成单一资源或更新原因。

资源支持：三个时点全部100个工件都有PA支持、当前SHARE自由80未支持的元组；按job计的额外种类分别1416、1120、881。PA资源候选有493、486、478/512个物理结果不同于S控制，触发充分。但广泛的新选项并未在两个以上时点转化成实质新增前沿容量。

更新：冻结源码确认GOM和PA局搜都在接受后立即写入工作态，并可被后继步骤使用。不能解释为“四子群局搜一律延迟更新”。跨轮入口、外层生命周期、自由/固定域和模型重学仍不同，本轮没有因果分离它们。本探针固定所有父代、供体及模型，排除了候选之间的更新连锁。

## 最小干预及与旧失败的区别

实例100_2_3_1、旧seed14910003。三时点各按原四职责取自由域4个父代，共16个，每个32个不同原FOS掩码。每臂每时点512次真实评价，总4608。S_RESOURCE使用原S资源；PA_RESOURCE只换同期PA完整FMW资源；PA_SHUFFLED打乱逐job供体行关联，保留相同79行可选池内各job的资源支持和频数。所有臂使用同一S父代、S顺序键、掩码、抽样行和冻结模型。有限32次样本不保证逐次实现频数相同。

这不是PRE_FIRST换轮次：没有更换接收者或重学模型；不是R+G+S调供体比例：池大小、顺序信息都不变；不是固定FA两工件编辑换名：自由域允许完整合法跨FA元组，使用既有FOS。旧ALL/OWN/SYNC、字段解绑、家族刷新和后筛选停止均保持。固定家族20不是本次实验对象，不宣称检验了整个四群协作。

PA资源来源额外花了250000 FE，不能当免费组件。本轮三臂同预算只指条件候选查询各1536 FE；不是三套完整算法同总成本比赛，也不比较同时间质量。

## 主结果：相对共同已付费档案的容量

A0为截至S入口时两条轨迹已付费档案并集，防止把已经存在的PA质量算作新增收益。所有时点/方法使用同一离线参考集（1102点），原归一化和HV参考1.5；参考1.25、2.0下PA对S的HV方向未翻转。IGD+列为对称改善百分比，正为好。双向C相等也计覆盖，不互补；高覆盖主要来自共享A0。

| 入口FE | PA资源对S资源HV | IGD+改善 | C(PA,S) | C(S,PA) |
|---|---:|---:|---:|---:|
'''+ '\n'.join(main_table)+'''

末入口IGD+从0.00002533209366降到0.00001664029558，绝对减少约0.00000869179808。41.42%的对称改善基于很小的距离，不能称整体性能提升41%。传统IGD末入口也改善20.013%，但其余时点接近零且中点微退。

| 入口FE | 处理臂（均512 FE） | A0未覆盖的候选数 | 相对A0的HV新增 | 末IGD+ |
|---|---|---:|---:|---:|
'''+ '\n'.join(capacity)+'''

PA_RESOURCE相对打乱对照，仅末入口有明显IGD+线索（+28.934%），HV只有+0.003690%，传统IGD反而−1.762%；早入口打乱对照略好。因此不主张跨job完整资源关联已证明必要。S单侧档案背景下的PA对S HV分别+0.146861%、+0.090808%、+0.090883%；换成共同A0后大幅缩小，说明其中不少是追及已知质量，而非新前沿容量。

## 验收、费用与保留的限制

- 新PA前缀250000成功FE，付费CSV所有列逐条匹配已有Linux前缀；初始解、8个共同检查点及原关键加载类身份一致。未换seed或补跑。
- 4608候选成功FE、0失败，600导入QA目标逐位相同；1536个S原生成提议与冻结Java PaMixingMove精确一致，夹具0FE。
- 5208份完整时间轴、1041600工序独立核验，工序聚合误差0；225个加载类检查，4800组逐job打乱边际检查；27次独立HV复算最大差约7.11e-15。IGD+方向、弱C相等和互不覆盖夹具通过。
- 总实际新FE254608；额外QA2729（PA检查点2129、来源导入600）。所有搜索/数学/验证在Linux执行，单JVM顺序，无评价补量。
- PA源沿用精确增量解码：重算29530307、复用20469693工序；新候选和600导入QA使用完整解码。原accounting.json的allFullDecoder字段过宽，**accounting-v2.json为有效说明**；原账本保留，FE/QA没有改变。
- 原数据提取器把自由家族的null与旧-1直接比较而停止；在0候选FE时按实际语义归一化后通过，原失败日志和extract-v2均保留。没有因此换样或重跑PA来源。
'''+f"- 实测进程墙钟：PA来源{read(root/'pa-source/process.json')['seconds']:.3f}s（搜索钟{source['searchSeconds']:.3f}s），600导入QA各JVM合计{costs['qa']:.3f}s，4608候选各JVM合计{costs['paid']:.3f}s；离线指标约{numeric['seconds']:.3f}s。原轨迹观察计时10.746s，新增完整模型写出没有独立计时，它包含在来源墙钟中；不能把10.746s当全部观察成本。保留负载日志，不作同时间结论。\n"+'''

## 停止决定与后续边界

预定要求至少两个时点有HV≥0.1%或IGD+≥5%的实质信号且无重大反向。只有228840达到距离信号，资源来源关未通过；关联关同样只见一个时点线索。停止该资源来源单独接入/扩量，不调供体比例、掩码数或入口去追正。

本轮缩小的是一个条件假设：在这些S入口、S顺序及S模型下，换入PA资源支持没有稳定实质容量。它没有证明资源不重要，也没有查清全部中段因果。未解决项是入口形成与跨轮模型/状态演化的联合历史；先利用已付费轨迹追踪结构何时形成、何时丢失，并核对旧PRE_FIRST、模型/家族与同步试验的覆盖范围，才能提出下一项独立干预。此处没有自动启动下一轮，也不将该建议视为新机制已立项。

复算入口：source/scripts/extract-v2.py、generate.py、audit.py、analyze.py；来源/执行证据见source-gate.json、build/identity.json、prepared/、paid/、qa/。有效费用见accounting-v2.json；三指标表、前沿、逐候选和分职责容量见analysis/。旧source/scripts/extract.py及全部失败日志保持可追溯。
'''
    (root/'REPORT.zh-CN.md').write_text(text,encoding='utf-8')
    write(root/'final-state.json',dict(completed=True,scientificDecision=decision,defaultMainlineChanged=False,
          extraExperimentsStarted=False,sourceObservationCostSeparatelyComplete=False,accounting='accounting-v2.json'))
    print('FINALIZED',decision['decision'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);args=p.parse_args();linux();main(args.root)
