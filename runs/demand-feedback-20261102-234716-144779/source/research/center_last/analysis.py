from datetime import datetime
import numpy as np
from research.dynamic_benchmark.metrics import nondominated
from research.expansion_screen._metrics import compare, igd_guard_metrics, mean
from research.semantic_repair.analysis import _records, csv_write
from research.semantic_repair.evidence import read, write_once
from research.semantic_repair.metrics import _uncertainty
from research.semantic_repair.trials import load_trial
from .protocol import PAIRS, jobs, trial_folder
from .observations import validate_observations, composition_metrics


def load_run(root, job, instance, spec):
    folder = trial_folder(root, job)
    run = load_trial(folder, instance, job['seed'], job['variant'], spec)
    run['feedbackTrace'], run['compositionTrace'] = validate_observations(folder, run['summary'], job['variant'])
    return run


def interaction(index, protocol, field):
    rows = []
    for instance in protocol['instances']:
        pairs = []
        for seed in protocol['algorithm_seeds']:
            values = {label: (index[instance['stem'], seed, label]['hv']['1.5'] if field == 'T' else index[instance['stem'], seed, label]['hv_fe15000'])
                      for label in ['SYNC_ORIGINAL', 'SYNC_LAST', 'SHARE_ORIGINAL', 'SHARE_LAST']}
            raw = values['SHARE_LAST'] - values['SYNC_LAST'] - values['SHARE_ORIGINAL'] + values['SYNC_ORIGINAL'] if all(v is not None for v in values.values()) else None
            pairs.append({'seed': seed, 'values': values, 'rawInteractionHV': raw})
        available = all(p['rawInteractionHV'] is not None for p in pairs)
        denominator = mean(p['values']['SYNC_ORIGINAL'] for p in pairs) if available else None
        effect = 100 * mean(p['rawInteractionHV'] for p in pairs) / denominator if available and denominator > 1e-12 else None
        rows.append({'instance': instance['stem'], 'interactionPercentOfSYNCOriginal': effect, 'pairs': pairs})
    resolved = all(r['interactionPercentOfSYNCOriginal'] is not None for r in rows)
    return {'field': field, 'instances': rows, 'meanInteractionPercent': mean(r['interactionPercentOfSYNCOriginal'] for r in rows) if resolved else None,
            'positiveInstances': sum(r['interactionPercentOfSYNCOriginal'] > 0 for r in rows) if resolved else None}


def analyze(root, deadline=None):
    protocol = read(root / 'protocol.json'); instances = {r['stem']: r for r in protocol['instances']}; runs = []
    for job in jobs(protocol):
        if deadline: deadline.require()
        runs.append(load_run(root, job, instances[job['instance']], protocol['variants'][job['variant']]))
    if len(runs) != 150: raise ValueError('All150 contemporaneous cells required')
    references = {stem: nondominated(np.concatenate([r['final'] for r in runs if r['instance'] == stem])) for stem in instances}
    records, costs = _records(runs, references, deadline); index = {(r['instance'],r['seed'],r['variant']):r for r in records}; effects = {}
    for candidate, control in PAIRS:
        args = (index,candidate,control,list(instances),protocol['algorithm_seeds'])
        t = {str(point): compare(*args,str(point)) for point in (1.25,1.5,2.)}
        effects[candidate+'__vs__'+control] = {'T': t,'uncertainty':_uncertainty(t['1.5']),
            'FE15000':{'allInstances':compare(*args,field='hv_fe15000'),'completePairsOnly':compare(*args,field='hv_fe15000',available_only=True)},
            'halfTime':compare(*args,field='hv_half'),'IGDplus':igd_guard_metrics(*args)}
    interactions = {field: interaction(index,protocol,field) for field in ['T','FE15000']}
    primary = effects['SHARE_LAST__vs__SHARE_ORIGINAL']; t = primary['T']['1.5']; fe = primary['FE15000']['allInstances']['mean_effect_percent']
    signal = {'meanTAtLeast1Percent': t['mean_effect_percent'] >= 1., 'atLeast3PracticalInstanceWins': t['practical_wins'] >= 3,
              'meanFEPositive': fe is not None and fe > 0, 'meanInteractionPositive': interactions['T']['meanInteractionPercent'] is not None and interactions['T']['meanInteractionPercent'] > 0}
    signal['supportedDescriptiveSignal'] = all(signal.values()); signal['scope'] = 'Predeclared hypothesis signal only; no formal scale-up or publication verdict'
    totals, generations, samples = [],[],[]
    for run in runs:
        a,b,c = composition_metrics(run)
        if a is not None: totals.append(a); generations.extend(b); samples.extend(c)
    audit = {'status':'COMPLETE','runs':len(runs),'genuineFailures':0,'successfulFE':sum(r['summary']['successful'] for r in runs),
        'attemptedFE':sum(r['summary']['attempted'] for r in runs),'timeInterruptedAttempts':sum(r['summary']['timeInterruptedAttempts'] for r in runs),
        'fixedFEReached':sum(r['fe'] is not None for r in runs),'returnedSolutionsReplayed':sum(r['summary']['offlineValidationDecodes'] for r in runs),
        'processWallSeconds':sum(r['execution']['processWallSeconds'] for r in runs),'controllerValidationSeconds':sum(r['execution']['controllerValidationSeconds'] for r in runs),
        'maxOvershootSeconds':max(r['summary']['deadlineOvershootSeconds'] for r in runs),'observerExtraFE':0,'formalStep6Started':False}
    output=root/'analysis'/datetime.now().strftime('analysis-%Y%m%d-%H%M%S-%f');output.mkdir(parents=True)
    for name,value in [('effects',effects),('interaction',interactions),('signal',signal),('audit',audit),('records',records)]:write_once(output/(name+'.json'),value)
    for stem,front in references.items():write_once(output/(stem+'-reference.json'),front.tolist())
    for name,rows in [('run-metrics',costs),('composition-run-metrics',totals),('composition-generation-metrics',generations)]:csv_write(output/(name+'.csv'),rows)
    write_once(output/'composition-paid-samples.json',samples)
    lines=['# 中央群最后：单一顺序150次','','|比较|同T平均HV变化%|同FE15000平均变化%|同T实质胜/负|','|---|---:|---:|---:|']
    for label,item in effects.items():
        a=item['T']['1.5'];f=item['FE15000']['allInstances']['mean_effect_percent'];lines.append(f"|{label}|{a['mean_effect_percent']:.4f}|{f if f is not None else '删失'}|{a['practical_wins']}/{a['practical_losses']}|")
    lines += ['', '中心移后与共享的交互：'+str(interactions['T']['meanInteractionPercent'])+'%（SYNC_ORIGINAL归一化）。',
              '预定描述性信号：'+str(signal['supportedDescriptiveSignal'])+'。只解释本次时序假设，不作论文/正式扩量判定。',
              '片段来源表示真实付费池记录；完整代与部分代分开，机会数/实际组合次数不混同。',
              '新鲜不代表质量好；交互也可能包含可行率、调用次数及随机流/预算截断变化，不能单独断言纯信息时效因果。','']
    (output/'report.md').write_text('\n'.join(lines),encoding='utf-8');return output
