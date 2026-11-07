"""Reconcile diagnostic costs and archive the complete immutable Linux evidence."""
import argparse
from pathlib import Path
import sys
import time
import zipfile
from common import BASE,SEEDS,linux,read,write,sha


def summary_markdown(root,report,boundary,totals):
    rows=['# 固定五供体支持域的穷举诊断（2026-11-06）','',
        '结论：停止在本次固定供体域内继续修改接受规则。保留四职责、QGS、原共享与默认主线。',
        '','本轮是条件容量诊断，不是新算法竞争实验；没有新实例、新seed或后台搜索。',
        '','## 付费穷举结果','',
        '|seed / 家族|不同厂内日程|完整闭包前沿|A0覆盖闭包|闭包覆盖A0|最佳单候选HV增益|',
        '|---|---:|---:|---:|---:|---:|']
    for r in report['results']:
        c=r['closures']['finite'];cv=c['standaloneVersusA0']['coverage']
        structure=read(root/'contexts/20_8_5_1'/str(r['seed'])/'structure.json')
        rows.append(f"|{r['seed']} / {structure['family']}|{structure['uniqueLocalCandidates']}|{c['frontSize']}|{cv['coveredA']}/{cv['totalA']}|{cv['coveredB']}/{cv['totalB']}|{c['bestSingle']['1.5']['relativePct']:.9g}%|")
    rows+=['','三个来源将闭包加入各自请求前A0后，HV（1.25/1.5/2.0）、IGD+、传统IGD及双向C均不变。',
        'A0与加入闭包后的前沿完全相同，不能将两个方向均100%的C当成改进。现有共享池完整记录的组合闭包也没有额外HV。',
        '','## 各完整前沿的经典指标','',
        '|seed|前沿|HV(1.5)|IGD+|IGD|点数|','|---|---|---:|---:|---:|---:|']
    for r in report['results']:
        for name,m in [('A0',r['A0']),('五供体闭包',r['closures']['finite']['standalone']),('A0+闭包',r['closures']['finite']['withA0'])]:
            rows.append(f"|{r['seed']}|{name}|{m['HV']['1.5']:.10g}|{m['IGDplus']:.10g}|{m['IGD']:.10g}|{m['frontSize']}|")
    rows+=['','完整目标极值及各自对应向量见 analysis/report.json；共同参考集见 analysis/reference.json。',
        '','## 支持域与结论边界','',
        '|实例|seed|初始单资源元组工件数|成熟单资源元组工件数|初始FA不变|250k参考前沿同FA点数|',
        '|---|---|---:|---:|---|---:|']
    for r in boundary['results']:
        rows.append(f"|{r['instance']}|{r['seed']}|{r['initialSingleResourceJobs']}|{r['matureSingleResourceJobs']}|是|{r['sameFamilyFAReferencePoints']}|")
    rows+=['',
        '静态域枚举每个job从五个成熟供体取一个配对的资源元组与优先键。它忽略接受限制与活供体丢失，因而是当前固定域的表达上界，并非实际动态可达性证明。',
        '仅20工件的三个事前选定家族穷举；100工件只做成员关系和既有记录核查，不能外推无潜力。',
        '保留原FA同时更换资源或顺序可能有价值，也可能没有。本结果不能单独证明必须改FA；旧家族刷新、释放、档案重启及字段解绑停止决定仍保留。',
        '','## 工程与费用','',
        f"- 正式新评价：{totals['scienceSuccessful']}成功，0失败；没有把它们标作零FE离线分析。",
        f"- 工程尝试：{totals['engineeringAttempted']}，成功{totals['engineeringSuccessful']}，预期失败{totals['expectedFailures']}。",
        f"- 合计尝试{totals['totalAttempted']}，成功{totals['totalSuccessful']}；额外完整时间轴/见证解码{totals['additionalQADecodes']}。",
        f"- 代数DP展开{totals['algebraicExpandedStates']}个状态，单独列账，不等同实际完整解码或免费搜索算法。",
        '- FE1/2截止、失败计费与日志、观察开关的前缀摘要一致；每次成功正式评价完整时间轴复核。',
        '- 75组原始局部目标逐位复现；14320组未改工厂目标不变；所有付费四向量逐条对账。',
        '- 28个确定性组合见证完整解码通过；代数求和与完整求和最大差约3.64e-11，不宣称浮点逐位相同。',
        '- 首次Java编译因检查型异常声明失败，0FE；原源码/编译日志保留，修订仅补声明。',
        '- 实验使用同一Linux、原冻结依赖及模型；本轮经明确授权临时连接100.127.244.47:22，严格指纹校验，未改网络配置。',
        '','## 下一问题','',
        '先核验保持FA时，生成不在当前五供体支持域内的新合法资源—顺序结构是否有容量。若连容量都不足，再区分FA限制；不能直接将此次负结果改写成家族刷新依据。',
        '任何后续实现先与旧TYPED、DEMAND、cap优先接受和ELITE/RANDOM刷新逐项去重，再登记普通生成对照及全部解码成本。本轮未启动该新机制。',
        '','原始文件：protocol.json、oracle-protocol.json、preflight.json、science/、analysis/、domain-boundary-audit.json、build-02/identity.json。']
    (root/'RESULT.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')


def main(root):
    linux();science=read(root/'science-acceptance.json');engineering=read(root/'engineering-acceptance.json')
    report=read(root/'analysis/report.json');boundary=read(root/'domain-boundary-audit.json')
    assert science['passed'] and engineering['passed'] and boundary['passed']
    for r in report['results']:
        assert r['audit']['paidRows']==read(root/'science'/str(r['seed'])/'receipt.json')['successful']
        for c in r['closures'].values():
            assert c['withA0']['front']==r['A0']['front']
            assert c['withA0']['IGDplus']==r['A0']['IGDplus'] and c['withA0']['IGD']==r['A0']['IGD']
    totals=dict(scienceSuccessful=science['successful'],engineeringAttempted=engineering['attempted'],
        engineeringSuccessful=engineering['successful'],expectedFailures=engineering['failed'],
        totalAttempted=science['attempted']+engineering['attempted'],
        totalSuccessful=science['successful']+engineering['successful'],
        additionalQADecodes=science['fullTimelineQA']+engineering['fullTimelineQA']+report['additionalWitnessDecodes'],
        algebraicExpandedStates=sum(c['algebraicExpandedStates'] for r in report['results'] for c in r['closures'].values()))
    assert (totals['totalAttempted'],totals['totalSuccessful'],totals['additionalQADecodes'])==(3587,3586,3612)
    write(root/'delivery-acceptance.json',dict(passed=True,totals=totals,decision=report['decision'],
        engineeringPassed=True,materialCapacityPassed=False,mainlineChanged=False,newSeedCount=0,newInstanceCount=0))
    summary_markdown(root,report,boundary,totals)
    manifest={str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    write(root/'delivery-manifest.json',manifest)
    archive=root.parent/(root.name+'-delivery.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for name in [*manifest,'delivery-manifest.json']:z.write(root/name,name)
    write(root.parent/(root.name+'-delivery.json'),dict(archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),files=len(manifest)))
    print('DELIVERY_ACCEPTED',totals,archive.stat().st_size,sha(archive),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);main(p.parse_args().root)
