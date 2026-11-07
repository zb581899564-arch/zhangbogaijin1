"""Export frozen complete-method evidence and verify actual delegates; zero new search FE."""
import csv
from pathlib import Path
import sys

from run_long_budget_bridge import ROOT, read, rows, write_once
from frozen_classpath_identity import verify_capture
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected


def post_audit(root):
    status = read(root/'status.json'); assert status['status'] == 'COMPLETE'
    cp = (root/'classpath.txt').read_text('utf-8-sig').strip(); checked = []
    for path in root.rglob('run-receipt.jsonl'):
        receipt, = rows(path)
        assert receipt['attempted'] == receipt['successful'] + receipt['failed']
        if receipt['stopReason'] == 'FE_LIMIT':
            assert receipt['successful'] == receipt['feLimit'] and receipt['failed'] == 0
            assert receipt['decoder']['dynamic.evaluations'] == receipt['successful']
        expected = cp
        if path.parent.name == 'ENGINE-FROZEN-PA':
            from pa_specialist_bridge_build import INTERFACE
            expected = (INTERFACE/'classpath.txt').read_text('utf-8-sig').strip()
        capture, = rows(path.parent/'loaded-identity.jsonl'); verified = verify_capture(capture, expected)
        validation = read(path.parent/'checkpoint-validation.json')
        assert validation['status'] == 'passed' and validation['allReachedPointsCovered']
        checked.append({'run': str(path.parent.relative_to(root)), 'successful': receipt['successful'],
                        'actualDecoderDelegates': receipt['decoder']['dynamic.evaluations'], 'classCount': len(verified)})
    assert class_hashes(root/'classes') == read(root/'class-hashes.json')
    for name, sha in read(root/'source-hashes.json').items():
        assert digest(root/'source'/name) == sha
    assert protected() == read(root/'protected-before.json')
    result = {'passed': True, 'runs': checked, 'totalActualDecoderDelegates': sum(r['actualDecoderDelegates'] for r in checked),
              'sourceAndClassIdentitiesUnchanged': True, 'defaultMainlineChanged': False, 'newSearchFE': 0, 'decoderQACalls': 0}
    write_once(root/'post-audit.json', result); return result


def report(root):
    analysis = read(root/'analysis.json'); audit = post_audit(root)
    lines = ['# 完整直接联合普通基座：500k三指标结果', '', '2026-11-06。完整工程、轻观察等价与真实评价对账均通过；这里评估普通完整程序的能力，不能替代原四子群/QGS/共享的独立收益或最终创新结论。', '',
             f"状态：`{analysis['decision']}`。正式同时间阶段{'已执行' if analysis['sameTimeExecuted'] else '按事前停止分支未启动'}，不从同FE结果推断同时间优势。", '',
             'QPA_DIRECT 保留15/55/15/15接受职责，但没有接入原QGS及条件共享。PA_EQUAL只放开旧PA边界等值接受，CENTER与其他搜索语义不变。原共享版与Li均为既有深局搜增强/规范重建，并非原作者发表数值的复现。', '',
             '## 预算与验收', '',
             f"本能力批次实际 {analysis['attemptedFE']:,} 次尝试、{analysis['successfulFE']:,} 次成功、{analysis['failedFE']} 次失败/中断；额外离线完整解码QA {analysis['extraFullDecoderQA']:,} 次。其中轻观察/旧PA开关工程236,600FE，24条正式同FE轨迹各500,000，合计12,000,000FE。实际底层评价调用按每条receipt核对，不能将离线QA算成搜索或以缓存免费补候选。", '',
             '先前完整内核工程另187,210FE/0失败、187,039额外完整QA，不混入本批比较。两批累计费用应分别列明。观察从共同付费入口采集；QA在搜索计时外运行，不反馈档案或RNG。', '',
             '## 预先登记的联合判断', '',
             '两个实例均须相对全部五个对照满足：主HV中位提升至少1%，参考点1.25/2方向不反；IGD+对称恶化中位不大于0；C差中位不小于0。逐seed分别不低于HV−1%、IGD+恶化5%、C差−0.02的底线。存在指标冲突就不按多数票晋升，不降低门槛、换seed或挑更好的控制。', '',
             'HV越大越好；IGD+越小越好。IGD+效应为200*(IA−IB)/(IA+IB)，正数表示恶化。双向C均为精确去重后的弱支配覆盖率，相等计覆盖；C(A,B)高、C(B,A)低较有利，两个方向不互补。共同经验参考由本阶段全部六方法、两seed终点的非支配并集构造；归一化沿用已登记常量，不按新结果重定边界。', '',
             '## 配对汇总', '', 'A固定为QPA_DIRECT。表中效应及C为两个seed的中位数，仅是开发诊断，不作显著性或留出确认。', '',
             '|阶段 / 实例|对照B|HV1.5效应%|IGD+对称恶化%|C(A,B)%|C(B,A)%|预定推进条件|',
             '|---|---|---:|---:|---:|---:|---|']
    observations, pairs = [], []
    for phase in analysis['phases']:
        for instance in phase['instances']:
            for value in instance['observations']:
                observations.append({'phase': phase['phase'], 'instance': instance['stem'], **value})
            for comparison in instance['comparisons']:
                lines.append(f"|{phase['phase']} / {instance['stem']}|{comparison['B']}|{comparison['medianHVEffectPct']['1.5']:+.3f}|{comparison['medianIGDplusSymmetricWorseningPct']:+.3f}|{100*comparison['medianC_A_B']:.3f}|{100*comparison['medianC_B_A']:.3f}|{'满足' if comparison['jointPass'] else '未满足'}|")
                for pair in comparison['pairs']:
                    pairs.append({'phase': phase['phase'], 'instance': instance['stem'], 'A': comparison['A'], 'B': comparison['B'], **pair})
    lines += ['', '逐seed原始HV/IGD+、三目标极值、FE和时间见 `observations.json`；双向覆盖计数、分母与参考点敏感性见 `paired-effects.json`；PA_EQUAL对旧PA的诊断另保留在各阶段analysis中。完整前沿、源码、实际加载class、命令和检查点QA均在本运行目录。', '',
              '## 停止与后续边界', '',
              '若不满足联合条件，停止此固定直接联合版本的资格比较，不把控制臂中较好者追认为新主候选，也不改掩码、FI、角色比例、代数或seed补救。若满足，也只能另立原四职责/共享独立增量协议；普通搜索能力不是新贡献。旧PA及其他机制的停止结论保持，默认主线未替换，完整研究目标未实现。', '',
              f"零FE后审计完成{len(audit['runs'])}条运行；冻结source/class与实际加载来源一致。"]
    write_once(root/'observations.json', observations); write_once(root/'paired-effects.json', pairs)
    (root/'report.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    with (root/'observations.csv').open('x', encoding='utf-8-sig', newline='') as stream:
        fields = ['phase','instance','seed','arm','frontSize','HV1.25','HV1.5','HV2.0','IGDplus','successfulFE','searchSeconds']
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader()
        for value in observations:
            row = {k: value[k] for k in fields if k in value}
            row.update({'HV'+r: v for r, v in value['HV'].items()}); writer.writerow(row)
    return analysis


if __name__ == '__main__':
    folder = Path(sys.argv[1]); result = report(folder)
    print('QPA_REPORT_COMPLETE', result['decision'], folder, flush=True)
