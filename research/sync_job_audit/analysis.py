from datetime import datetime
import numpy as np
from research.dynamic_benchmark.metrics import nondominated
from research.expansion_screen._metrics import compare, igd_guard_metrics
from research.semantic_repair.analysis import _records, csv_write
from research.semantic_repair.evidence import read, write_once
from research.semantic_repair.metrics import _uncertainty
from research.semantic_repair.trials import load_trial
from .protocol import PAIRS, jobs, trial_folder
from .feedback import validate_feedback, feedback_records


def validate_variant(run):
    summary = run['summary']; label = run['variant']; search = summary['search']
    if label != 'NSGA':
        if search.get('globalKernel') != 'JOB_ALIGNED' or search.get('alignedKernelProposals', 0) < 1:
            raise ValueError('Non-classic control did not use the same JOB_ALIGNED kernel')
    elif 'alignedKernelProposals' in search:
        raise ValueError('NSGA acquired the new kernel')
    if 'joint' in summary or summary.get('mechanismCapture') or summary.get('retainInitialParents'):
        raise ValueError('An unregistered search mechanism entered the run')
    cooperative = label in ('SYNC_JOB', 'SHARE_JOB')
    if cooperative:
        if summary.get('cooperation', {}).get('sharing') is not (label == 'SHARE_JOB'):
            raise ValueError('SYNC/SHARE switch differs from the protocol')
        if label == 'SYNC_JOB' and (summary['cooperation'].get('assembliesProposed', 0) or summary['cooperation'].get('poolRecords', 0)):
            raise ValueError('Disabled sharing still composed or populated factory pools')
    elif 'cooperation' in summary:
        raise ValueError('Free control acquired FA families')


def load_run(root, job, instance, spec):
    folder = trial_folder(root, job)
    run = load_trial(folder, instance, job['seed'], job['variant'], spec)
    validate_variant(run)
    run['feedbackTrace'] = validate_feedback(folder, run['summary'], job['variant'])
    return run


def analyze(root, deadline=None):
    protocol = read(root / 'protocol.json'); instances = {r['stem']: r for r in protocol['instances']}
    runs = []
    for job in jobs(protocol):
        if deadline: deadline.require()
        runs.append(load_run(root, job, instances[job['instance']], protocol['variants'][job['variant']]))
    if len(runs) != 120: raise ValueError('All120 contemporaneous runs required')
    references = {stem: nondominated(np.concatenate([r['final'] for r in runs if r['instance'] == stem])) for stem in instances}
    records, costs = _records(runs, references, deadline)
    index = {(r['instance'], r['seed'], r['variant']): r for r in records}
    effects = {}
    for candidate, control in PAIRS:
        args = (index, candidate, control, list(instances), protocol['algorithm_seeds'])
        time = {str(point): compare(*args, str(point)) for point in (1.25, 1.5, 2.)}
        effects[candidate + '__vs__' + control] = {'T': time, 'uncertainty': _uncertainty(time['1.5']),
            'FE15000': {'allInstances': compare(*args, field='hv_fe15000'),
                        'completePairsOnly': compare(*args, field='hv_fe15000', available_only=True)},
            'halfTime': compare(*args, field='hv_half'), 'IGDplus': igd_guard_metrics(*args)}
    totals, steps = [], []
    for run in runs:
        total, detail = feedback_records(run); totals.append(total); steps.extend(detail)
    audit = {'status': 'COMPLETE', 'runs': len(runs), 'genuineFailures': 0,
        'successfulFE': sum(r['summary']['successful'] for r in runs), 'attemptedFE': sum(r['summary']['attempted'] for r in runs),
        'timeInterruptedAttempts': sum(r['summary']['timeInterruptedAttempts'] for r in runs),
        'fixedFEReached': sum(r['fe'] is not None for r in runs),
        'returnedSolutionsReplayed': sum(r['summary']['offlineValidationDecodes'] for r in runs),
        'maxOvershootSeconds': max(r['summary']['deadlineOvershootSeconds'] for r in runs),
        'processWallSeconds': sum(r['execution']['processWallSeconds'] for r in runs),
        'controllerValidationSeconds': sum(r['execution']['controllerValidationSeconds'] for r in runs),
        'observerExtraFE': 0, 'formalStep6Started': False}
    output = root / 'analysis' / datetime.now().strftime('analysis-%Y%m%d-%H%M%S-%f'); output.mkdir(parents=True)
    for name, value in [('effects', effects), ('records', records), ('audit', audit)]: write_once(output / (name + '.json'), value)
    for stem, values in references.items(): write_once(output / (stem + '-reference.json'), values.tolist())
    for name, values in [('run-metrics', costs), ('feedback-run-metrics', totals), ('feedback-steps', steps)]: csv_write(output / (name + '.csv'), values)
    lines = ['# SYNC_JOB归因与反馈时序：120次', '',
             '|比较|同T平均HV变化%|同FE15000平均变化%|同T实质胜/负|', '|---|---:|---:|---:|']
    for label, item in effects.items():
        t = item['T']['1.5']; f = item['FE15000']['allInstances']['mean_effect_percent']
        lines.append(f"|{label}|{t['mean_effect_percent']:.4f}|{f if f is not None else '删失'}|{t['practical_wins']}/{t['practical_losses']}|")
    lines += ['', 'SYNC/SO衡量原家族组织整体影响；SHARE/SYNC衡量开启原共享模块后的整体增量。',
        '反馈仅观察，不刷新档案、不增加评价或随机抽取；出生时间为保存快照的付费发生时点。',
        '部分代仅用于截止前时序样本，不当作完整代；NSGA内部QGS时序不适用。',
        '档案接纳事件可能暂时非支配；截止未出现不能解释为永久丢失，年龄不能解释为性能因果。',
        '同T/FE与敏感性和IGD+见effects.json；只用本轮同期结果，不拼接旧T数据。', '']
    (output / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
    return output
