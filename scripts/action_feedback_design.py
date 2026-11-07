"""Frozen inputs and decision rules for paid cross-duty action feedback diagnostics."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, write_once

SOURCE = ROOT / 'runs/mating-pool-probe-20261105-062648-478040'
KERNEL = ROOT / 'runs/snapshot-anchor-audit-20261105-051047-172151'
STEMS = ('20_8_5_1', '100_2_3_1')
ROLES = ('MAKESPAN', 'CENTER', 'ENERGY', 'WORKER_COST')
REPLICATES = 4
RIDGE = 1.0


def protocol():
    return {
        'source': str(SOURCE), 'kernel': str(KERNEL), 'replicates': REPLICATES,
        'instances': read(SOURCE / 'protocol.json')['instances'],
        'question': 'Can previously paid multiobjective action outcomes transfer across duties, '
                    'beyond own-duty training, extra sample count, state-free action means and random choice?',
        'sampling': 'All six pre-existing windows per instance, each duty eight equally spaced current free parents. '
                    'Retain duplicates and metadata. Factory=(sourceSeed+step+17*withinRoleIndex)%factoryCount. '
                    'Every original intra action0..8 receives four draws from the same parent/factory. No action modification.',
        'budget': '2*6*4*8*(1+9*4)=14208 successful FE. Parent replay and every duplicate/noop paid. '
                  'All14208 schedules additionally receive full timeline QA, separately counted. No new source search.',
        'featureNames': ['normalizedC', 'normalizedE', 'normalizedW', 'factoryJobShare',
                         'factoryCShare', 'factoryEShare', 'factoryWShare', 'machineLoadCV',
                         'workerLoadCV', 'usedMachineShare', 'usedWorkerShare', 'meanStartFatigue',
                         'maxStartFatigue', 'meanEndFatigue', 'workExposurePerDuration', 'durationOverBase'],
        'features': 'Only already-paid parent state; first11 basic, last5 fatigue. No candidate preview, '
                    'action outcome, source seed, job identity, context position or role identifier is a predictive feature.',
        'fit': {'method': 'One three-output linear ridge per original action; standardized train features, '
                          'unpenalized intercept. Raw signed relative objective reductions; average four draws for each training parent/action.',
                'ridge': RIDGE, 'tuning': 'None. No alternative feature/model/regularization scan.'},
        'policies': {
            'SHARED': 'All training duties, all16 features.',
            'OWN': 'Receiver-duty training parents only, same16 features and fit.',
            'MATCHED_SHARED': 'Exactly as many training parents as OWN; outcome-independent role/context balanced '
                              'ordering, within-role index order0,7,1,6,2,5,3,4. Same16 features.',
            'BASIC_SHARED': 'Same complete shared rows, first11 features only.',
            'ROLE_MEAN': 'Own-duty per-action vector mean, no state features.',
            'POOLED_MEAN': 'All-duty per-action vector mean, no state features.',
            'UNIFORM': 'Expected uniform action and draw, never choose best realized draw.',
            'FIRST': 'Original first intra action0, one proposal only; not a full VNS comparison.',
            'ORACLE': 'Best realized four-draw average action per parent, privileged diagnostic only, never eligible.'},
        'holdout': 'Two leave-one-source-seed-out folds11730007/11730037. No test outcome used for fitting '
                   'or choosing actions. Remove every training parent physically equivalent to any heldout parent, '
                   'even if global inter-factory JS interleaving differs. Missing own training<12 per duty fails coverage, no replacement.',
        'choice': 'Choose maximum predicted relative improvement in the receiver objective; CENTER uses original '
                  'Direction.reward sum of three relative changes. Exact ties choose lower action id. '
                  'This is a one-step reward diagnostic, not a change or faithful simulation of CENTER PDDR acceptance.',
        'scoring': 'Expected positive one-step original-duty reward over four random draws of selected action, '
                   'not max draw or union of four children. Also expected single-candidate HV gain against the '
                   'exact pre-existing paid background, references1.5 and1.25/2. All policies share the same paid pool.',
        'gate': 'Both instances:>=64 informative parents (oracle positive>1e-8 and action reward range>1e-8); '
                'SHARED mean positive reward >=10%over OWN and UNIFORM, >=5%over ROLE_MEAN and POOLED_MEAN; '
                'MATCHED_SHARED >=5%over OWN; SHARED positive against OWN in each heldout fold and nonnegative '
                'in at least3of4 duties. SHARED mean single-candidate HV>=OWN and UNIFORM at all three refs. '
                'Zero control mean is inconclusive, not infinite success. All necessary. '
                'Fatigue information independently supported only if SHARED>=2%over BASIC_SHARED in both instances '
                'with nonnegative HV differences at all refs. Failure stops this fixed model/data-transfer mechanism '
                'without seed/model/feature/regularization/target/window/action retuning.',
        'cost': 'Measure actual feature extraction, ridge fitting and batch predictions; divide complete fold '
                'fit+prediction cost by tested decisions, compare with measured generation+guarded evaluation. '
                'Report separately from IO/QA. Python offline costs do not establish Java closed-loop or same-time advantage. '
                'A quality pass permits only a separately frozen native-cost/closed-loop design.',
        'engineering': 'Actual class sources/hashes/JDK and frozen source copies, common legal parents/objectives, '
                       'each paid incremental result bit-exact full timeline, no parent mutation; '
                       'every action/rep observed, receipts reconcile. Failures retain last valid front and fee log.',
        'novelty': 'Adaptive operator selection and preference-relabelled vector experience are established. '
                   'This probes a practical prerequisite, not a novel ESWA contribution. Generic AOS improvement '
                   'alone does not prove four-duty supply or dynamic-fatigue specificity.',
        'literature': [
            'https://colalab.ai/publications/LiFKZ14.pdf',
            'https://papers.neurips.cc/paper_files/paper/2019/hash/4a46fbfca3f1465a27b210f4bdfe6ab3-Abstract.html',
            'https://www.sciencedirect.com/science/article/pii/S0952197625023000'],
        'limits': 'Early paid source windows are reused development evidence, not new-seed complete algorithms '
                  'or independent confirmation. No on-policy continuation, unseen-action free labels, PDDR '
                  'acceptance conclusion, beta0 specificity, Li superiority, complete sameFE/time or publication claim. '
                  'No production/default, QGS, shared pool or operator change; no downloads/file transfer.'
    }


def prepare(root, stem):
    shutil.copytree(SOURCE / stem / 'inputs', root / stem / 'inputs')
    contexts = read(SOURCE / stem / 'contexts.json')
    write_once(root / stem / 'contexts.json', contexts)
    lines, selected = [], []
    for context in contexts:
        for role in ROLES:
            pool = [parent for parent in context['current'] if parent['role'] == role]
            assert len(pool) == (47 if role == 'CENTER' else 11)
            for local_index in range(8):
                parent = pool[local_index * (len(pool) - 1) // 7]
                assert parent['category'] == 0 and parent['earliestKnownPaidFE'] <= context['preBatchFE']
                ordinal = len(selected)
                factory = (context['seed'] + context['step'] + 17 * local_index) % int(stem.split('_')[2])
                item = {'id': f'p{ordinal}', 'context': context['contextId'], 'sourceSeed': context['seed'],
                        'role': role, 'localIndex': local_index, 'factory': factory, 'parent': parent}
                selected.append(item)
                line = [item['id'], item['context'], str(item['sourceSeed']), role, str(factory), str(ordinal)]
                line += [','.join(map(str, parent[key])) for key in ('objectives', 'JS', 'FA', 'MA', 'WA')]
                lines.append('\t'.join(line))
    assert len(selected) == 192
    write_once(root / stem / 'selected.json', selected)
    (root / stem / 'cases.tsv').write_text('\n'.join(lines) + '\n', encoding='utf-8')

