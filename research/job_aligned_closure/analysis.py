"""Complete-matrix, instance-paired HV/IGD+ and true-cost evidence."""
from datetime import datetime
import numpy as np

from research.dynamic_benchmark.metrics import nondominated
from research.expansion_screen._metrics import compare, igd_guard_metrics, mean
from research.semantic_repair.analysis import _records, csv_write
from research.semantic_repair.evidence import read, write_once
from research.semantic_repair.metrics import _uncertainty
from research.semantic_repair.trials import load_trial
from .protocol import PAIRS, jobs, trial_folder


def validate_variant(run):
    summary = run['summary']; label = run['variant']
    aligned = label.endswith('_JOB')
    search = summary['search']
    if aligned:
        if search.get('globalKernel') != 'JOB_ALIGNED' or search.get('alignedKernelProposals', 0) < 1:
            raise ValueError('Aligned label did not use the aligned proposal policy')
        if ';globalKernel=JOB_ALIGNED' not in summary['searchConfiguration']:
            raise ValueError('Kernel identity missing from configuration')
    elif 'alignedKernelProposals' in search or ';globalKernel=' in summary['searchConfiguration']:
        raise ValueError('A control silently used another proposal policy')
    if summary.get('mechanismCapture') or summary.get('retainInitialParents') or 'joint' in summary:
        raise ValueError('An unregistered mechanism entered the closed-loop run')
    if label.startswith('SHARE'):
        if summary.get('cooperation', {}).get('sharing') is not True:
            raise ValueError('Shared method lost its sharing mechanism')
    elif 'cooperation' in summary:
        raise ValueError('A non-sharing control acquired family/compose machinery')


def _interaction(records, protocol):
    index = {(row['instance'], row['seed'], row['variant']): row for row in records}
    results = {}
    for field in ['T', 'FE15000']:
        rows = []
        for instance in protocol['instances']:
            paired = []
            for seed in protocol['algorithm_seeds']:
                values = {label: (index[instance['stem'], seed, label]['hv']['1.5'] if field == 'T'
                                  else index[instance['stem'], seed, label]['hv_fe15000'])
                          for label in ['SO', 'SO_JOB', 'SHARE', 'SHARE_JOB']}
                value = (values['SHARE_JOB'] - values['SHARE'] - values['SO_JOB'] + values['SO']) if all(v is not None for v in values.values()) else None
                paired.append({'seed': seed, 'values': values, 'rawInteractionHV': value})
            available = all(p['rawInteractionHV'] is not None for p in paired)
            baseline = mean(p['values']['SO'] for p in paired) if available else None
            effect = 100 * mean(p['rawInteractionHV'] for p in paired) / baseline if available and baseline > 1e-12 else None
            rows.append({'instance': instance['stem'], 'interactionPercentOfSO': effect, 'paired': paired})
        results[field] = {'instances': rows, 'meanInteractionPercentOfSO': mean(r['interactionPercentOfSO'] for r in rows)
                         if all(r['interactionPercentOfSO'] is not None for r in rows) else None,
                         'scope': 'Kernel x sharing interaction in this closed loop; no isolated genetic causal attribution'}
    return results


def analyze(root, deadline=None):
    root = root.resolve(); protocol = read(root / 'protocol.json')
    instances = {row['stem']: row for row in protocol['instances']}
    runs = []
    for job in jobs(protocol):
        if deadline: deadline.require()
        run = load_trial(trial_folder(root, job), instances[job['instance']], job['seed'], job['variant'], protocol['variants'][job['variant']])
        validate_variant(run); runs.append(run)
    if len(runs) != 150:
        raise ValueError('All150 contemporaneous cells are required')
    references = {stem: nondominated(np.concatenate([run['final'] for run in runs if run['instance'] == stem]))
                  for stem in instances}
    records, costs = _records(runs, references, deadline)
    index = {(row['instance'], row['seed'], row['variant']): row for row in records}
    effects = {}
    seeds = protocol['algorithm_seeds']; stems = list(instances)
    for candidate, control in PAIRS:
        args = (index, candidate, control, stems, seeds)
        full = {str(point): compare(*args, str(point)) for point in (1.25, 1.5, 2.)}
        effects[candidate + '__vs__' + control] = {
            'T': full, 'uncertainty': _uncertainty(full['1.5']),
            'halfTime': compare(*args, field='hv_half'),
            'FE15000': {'allInstances': compare(*args, field='hv_fe15000'),
                        'completePairsOnly': compare(*args, field='hv_fe15000', available_only=True)},
            'IGDplus': igd_guard_metrics(*args)}
    for run, cost in zip(runs, costs):
        search = run['summary']['search']
        cost['globalKernel'] = search.get('globalKernel', 'CLASSIC' if run['variant'] == 'NSGA' else 'PAPER')
        cost['alignedKernelProposals'] = search.get('alignedKernelProposals', 0)
        cost['globalPaidEvaluations'] = run['summary']['semanticAudit'].get('paid.global', 0)
    audit = {'status': 'COMPLETE', 'runs': len(runs), 'genuineFailures': 0,
             'successfulFE': sum(run['summary']['successful'] for run in runs),
             'attemptedFE': sum(run['summary']['attempted'] for run in runs),
             'timeInterruptedAttempts': sum(run['summary']['timeInterruptedAttempts'] for run in runs),
             'fixedFEReached': sum(run['fe'] is not None for run in runs),
             'offlineReturnedSolutionReplays': sum(run['summary']['offlineValidationDecodes'] for run in runs),
             'processWallSeconds': sum(run['execution']['processWallSeconds'] for run in runs),
             'controllerValidationSeconds': sum(run['execution']['controllerValidationSeconds'] for run in runs),
             'maxOvershootSeconds': max(run['summary']['deadlineOvershootSeconds'] for run in runs),
             'offlineAnalysisExtraFE': 0, 'formalStep6Started': False}
    if deadline: audit['campaignWallSecondsBeforeExport'] = deadline.elapsed()
    output = root / 'analysis' / datetime.now().strftime('analysis-%Y%m%d-%H%M%S-%f'); output.mkdir(parents=True)
    for name, value in [('effects', effects), ('interaction', _interaction(records, protocol)), ('records', records), ('audit', audit)]:
        write_once(output / (name + '.json'), value)
    for stem, front in references.items(): write_once(output / (stem + '-reference.json'), front.tolist())
    csv_write(output / 'run-metrics.csv', costs)
    lines = ['# JOB_ALIGNED闭环验证：五版本150次', '',
             '仅替换普通全局生成核；四子群、共享、Q设置、局搜和共同模型固定。', '',
             '|比较|同T平均HV变化%|同FE15000平均HV变化%|同T实质胜/负|', '|---|---:|---:|---:|']
    for label, result in effects.items():
        t = result['T']['1.5']; fe = result['FE15000']['allInstances']['mean_effect_percent']
        lines.append(f"|{label}|{t['mean_effect_percent']:.4f}|{fe if fe is not None else '删失'}|{t['practical_wins']}/{t['practical_losses']}|")
    lines += ['', '六个开发实例各五seed；实例等权，seed不当独立实例。全部方法同期块内随机顺序。',
              'FE未达到保持删失；15000点为成功评价快照，未另启FE运行。',
              '主HV点1.5，敏感性1.25/2.0；IGD+参考为本轮全部五方法×五seed有效T档案的ND并集，离线近似。',
              '全部搜索费用进入T，启动/输入/离线QA与导出由进程墙钟和总campaign另记。',
              '未使用旧270次判灯器，不构成正式第6步或论文资格判定。', '']
    (output / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
    return output
