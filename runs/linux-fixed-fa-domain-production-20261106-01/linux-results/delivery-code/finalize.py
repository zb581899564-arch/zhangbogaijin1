"""Reconcile all paid work and publish auditable Linux tables and an immutable archive."""
import argparse
from collections import Counter
import csv
from pathlib import Path
import platform
import sys
import zipfile
from common import BASE,SOURCE,MATURE,ARMS,STEMS,SEEDS,linux,read,write,sha


def csv_file(path,rows):
    with path.open('x',newline='',encoding='utf-8') as s:
        w=csv.DictWriter(s,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def tables(root,report):
    metrics=[];pairs=[];supply=[]
    for case in report['instances']:
        for o in case['observations']:
            s=o['supply'];row=dict(instance=case['instance'],seed=o['seed'],arm=o['arm'])
            for label in ('final','paidOnly','working'):
                m=s[label];metrics.append(dict(row,endpoint=label,HV=m['HV']['1.5'],HV125=m['HV']['1.25'],HV200=m['HV']['2.0'],
                    IGDplus=m['IGDplus'],IGD=m['IGD'],frontSize=m['frontSize'],Cmax=m['objectiveMinimum'][0],TEC=m['objectiveMinimum'][1],TWC=m['objectiveMinimum'][2]))
            counts=s['counts'];supply.append(dict(row,inside=counts.get('INSIDE',0),outsideResource=counts.get('OUTSIDE_RESOURCE',0),
                outsideOrder=counts.get('OUTSIDE_KEY_ORDER',0),outsideAccepted=counts.get('outsideAccepted',0),
                outsideAdmissions=counts.get('outsideArchiveAdmissions',0),physicalNoop=counts['physicalNoop'],
                bestSingleOutsideHVPct=s['bestSingleOutsideProduction']['1.5']['relativePct'],
                finalAboveA0HVPct=o['aboveA0']['HVEffectPct']['1.5'],chosenNewFactories=s['chosenNewFactoryRecords']))
        for comparison in case['comparisons']:
            for p in comparison['pairs']:
                c=p['coverage'];pairs.append(dict(instance=case['instance'],candidate=comparison['candidate'],control=comparison['control'],
                    seed=p['seed'],HVPct=p['HVEffectPct']['1.5'],IGDplusSymmetricImprovementPct=p['IGDplusSymmetricImprovementPct'],
                    C_A_B=c['C_A_B'],C_B_A=c['C_B_A'],coveredB=c['coveredB'],totalB=c['totalB'],coveredA=c['coveredA'],totalA=c['totalA']))
    for name,rows in [('metrics.csv',metrics),('pairs.csv',pairs),('supply.csv',supply)]:csv_file(root/'analysis'/name,rows)
    return supply


def summarize(root,report,totals,supply):
    text=['# 固定FA域外联合生产：结果（2026-11-06）','',
        '**决定：STOP_FIXED_TWO_JOB_DOMAIN_PRODUCER。** 固定两工件生成器没有达到事前容量门槛，不扩量、不改主线或旧停止决定。',
        '','## 完整对照结果','',
        '|实例|A / B|配对中位HV变化%|配对中位IGD+改善%|配对中位C差百分点|',
        '|---|---|---:|---:|---:|']
    for c in report['instances']:
        for p in c['comparisons']:
            text.append(f"|{c['instance']}|{p['candidate']} / {p['control']}|{p['medianHV']['1.5']:.8g}|{p['medianIGDplus']:.8g}|{p['medianCgapPP']:.8g}|")
    text+=['','不能只看中位数：以下保留全部逐来源A0增量和域外供给。','',
        '|实例|seed|臂|域外/生产|域外准入次数|域外接受次数|最佳域外单候选HV增量%|最终HV相对A0增量%|',
        '|---|---|---|---:|---:|---:|---:|---:|']
    for s in supply:
        outside=s['outsideResource']+s['outsideOrder']
        text.append(f"|{s['instance']}|{s['seed']}|{s['arm']}|{outside}/4095|{s['outsideAdmissions']}|{s['outsideAccepted']}|{s['bestSingleOutsideHVPct']:.8g}|{s['finalAboveA0HVPct']:.8g}|")
    text+=['','每实例三个来源的容量达标数均为0。HV敏感性、IGD、C分子/分母和完整目标极值向量详见analysis/report.json及pairs.csv。',
        'NOVEL/LEGAL唯一非零来源为100_2_3_1、16110037：HV微增但IGD+与C方向相反。未据中位数平局掩盖该差异。',
        '','## 计费与核验','',
        f"- 科学评价73728成功/0失败；工程3590尝试/3589成功/1次预设失败；总尝试{totals['attempted']}、成功{totals['successful']}。",
        f"- 完整时间轴QA {totals['fullQA']}；输入/池恢复QA {totals['importQA']}；额外完整解码总数{totals['additionalQADecodes']}。",
        f"- 科学JVM过程总时长{totals['scienceProcessSeconds']:.6f}秒；搜索累计{totals['scienceSearchSecondsIncludesQA']:.6f}秒，包含只读观察和物理QA，不是同时间对比。",
        '- 六个原GOM512FE与旧ROLE逐位桥接、19工程、18科学全部独立验收；24570对新生成步骤共享随机骨架核对。',
        '- 全部候选FA不变，原ROLE接受、原池准入截断及末次原共享选择逐条复核；输入、实际类和依赖身份可追溯。',
        '- 所有新候选、重复、资源补集缺失回退及最终父代回退均计费；没有隐藏候选筛选或免费解码。',
        '- 旧支持域泛用夹具的相等键顺序更正单列；六个实际旧来源均无跨工件相等键，旧穷举结果不受影响。',
        '','## 解释范围','',
        'LEGAL已经几乎总能生成域外结构，NOVEL只进一步排除初始已见元组。两者都未形成跨来源实质质量，因此不能用“更多新组合”代替搜索价值。',
        '结论只针对当前FA、成熟入口、固定两工件骨架及4096FE，不是同FA所有合法日程的上界；也不是四子群或原共享无效的证据。',
        '不继续调整新颖性比例、局搜长度、cap或seed。不自动回到TYPED或家族刷新；任何下一假设须提供不同的、能区分有价值结构的证据。',
        '主线、全局QGS、家族及原共享保持原样；本轮未启动完整算法/经典矩阵或TIME、没有恢复Goal。']
    (root/'RESULT.md').write_text('\n'.join(text)+'\n',encoding='utf-8')


def main(root):
    linux();report=read(root/'analysis/report.json');assert report['decision']=='STOP_FIXED_TWO_JOB_DOMAIN_PRODUCER'
    reports=[read(root/(x+'-independent-audit.json')) for x in ('engineering','science')]
    assert all(r['passed'] for r in reports) and read(root/'generator-extended-audit.json')['passed']
    totals={k:sum(r['totals'][k] for r in reports) for k in ('attempted','successful','failed','fullQA','importQA')}
    totals['additionalQADecodes']=totals['fullQA']+totals['importQA']
    totals['scienceProcessSeconds']=sum(read(p)['seconds'] for p in (root/'science').glob('*/*/*/process.json'))
    totals['scienceSearchSecondsIncludesQA']=sum(read(p)['searchSeconds'] for p in (root/'science').glob('*/*/*/receipt.json'))
    assert (totals['attempted'],totals['successful'],totals['failed'])==(77318,77317,1)
    assert totals['additionalQADecodes']==82279
    supply=tables(root,report);aggregate={}
    for arm in ARMS:
        rows=[s for s in supply if s['arm']==arm]
        counts={k:sum(r[k] for r in rows) for k in ('inside','outsideResource','outsideOrder','outsideAccepted','outsideAdmissions','physicalNoop')}
        counts['outsideFraction']=(counts['outsideResource']+counts['outsideOrder'])/(6*4095);aggregate[arm]=counts
    write(root/'delivery-acceptance.json',dict(passed=True,engineeringPassed=True,mechanismCapacityPassed=False,
        totals=totals,supply=aggregate,decision=report['decision'],independentHVChecks=sum(c['independentHVChecks'] for c in report['instances']),
        platform=platform.platform(),python=sys.version,mainlineChanged=False,goalResumed=False))
    summarize(root,report,totals,supply)
    manifest={str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    write(root/'delivery-manifest.json',manifest);archive=root.parent/(root.name+'-delivery.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for name in [*manifest,'delivery-manifest.json']:z.write(root/name,name)
    write(root.parent/(root.name+'-delivery.json'),dict(bytes=archive.stat().st_size,sha256=sha(archive),files=len(manifest)))
    print('DOMAIN_DELIVERY',totals,aggregate,archive.stat().st_size,sha(archive),len(manifest),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);main(p.parse_args().root)
