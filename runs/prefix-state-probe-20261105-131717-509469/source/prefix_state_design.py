"""Fixed-source, fully paid prefix-state intervention; no online teacher or selector."""
from collections import Counter
import shutil

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once
from gap_structure_sources import NAT, by_job

SOURCE = ROOT / 'runs/global-working-audit-20261105-055724-963327'
BASE = ROOT / 'runs/schedule-factor-probe-20261105-124946-994085'
STEMS = ('20_8_5_1', '100_2_3_1')
SEEDS = (11730007, 11730037)
ROLES = ('MAKESPAN', 'CENTER', 'ENERGY', 'WORKER_COST')
METHODS = ('PARENT', 'TEACHER', 'PREFIX', 'ORDER_CONTROL', 'CONTEXT_CONTROL')


def protocol():
    return {
        'source': str(SOURCE), 'base': str(BASE), 'instances': read(NAT / 'protocol.json')['instances'],
        'seeds': SEEDS, 'methods': METHODS, 'plannedFE': 10240,
        'question': 'Does copying a real factory first-stage prefix through its first worker reuse '
                    'preserve teacher state and produce useful new schedules beyond matched order/context controls?',
        'sourceWindow': 'Reuse existing first-generation WORKER_COST step49 actualIndices at paidFE5100. '
                        'All four roles have completed their global updates. First100 parent points use frozen '
                        'Direction.values order15M,55C,15E,15W; additional15 children belong to W. '
                        'category0 only: free80; do not change or invent protected-family labels.',
        'sampling': 'Each source:8 equally spaced CENTER receiver indices and8 equally spaced teacher indices '
                    'in EACH of four roles, stable actual selection order. All512pairs per instance across2seeds. '
                    'Factory=(receiverRank+teacherRank)%factoryCount. Same receiver/factory and teacher draw count '
                    'for all roles. No gain-based selection, replacement, deduplication or missing-sample repair.',
        'unit': 'Shortest teacher first-stage factory chain ending at first repeated worker. Copy all its '
                'jobs with complete(factory,machine,worker) tuples. Other jobs retain receiver tuples. '
                'PREFIX puts ordered block first; ORDER_CONTROL puts same jobs/tuples first in receiver '
                'relative order; CONTEXT_CONTROL puts ordered teacher block last. All other within-factory '
                'receiver chains retained. Neutral cross-factory interleaving canonicalized in all3children.',
        'fallback': 'No repeated worker or any emptied receiver factory: all3children equal original receiver, '
                    'fully paid. Never shorten block, repair, resample, or omit pair. Source parent/teacher '
                    'always paid. Identity/repeated physical candidates counted and reported.',
        'engineering': 'Same frozen decoder/FAM policy, repair0. Every candidate paid through RunContext and '
                       'independent full timeline QA. Dynamic PARENT/TEACHER objectives must exactly replay '
                       'paid sources. For every eligible PREFIX, compare ALL teacher first-stage prefix '
                       'operation identifiers and10numeric fields bit-exact, with identical leading job order. '
                       'No claim later stages or whole factory remain identical. Preserve receipts on failure.',
        'beta0': 'Evaluate exactly same genes with only beta0, retaining alpha/mu/h0 and decoder policy; '
                 'independently check parameter contract. Parent-singleton HV scoring identical in both models. '
                 'Dynamic source selection remains a limitation; no beta0 optimization or unbiased landscape claim.',
        'primaryScore': 'DYNAMIC single-child HV gain against common original paid archive at5100, ref1.5 '
                        'and original scales. Do not add enumeration outputs to background. PARENT/TEACHER '
                        'must have zero new volume. Parent-relative gains secondary in BOTH models. '
                        'No union of all teacher draws advertised as one candidate gain.',
        'prefixGate': 'BOTH instances: >=25% eligible pairs with both seeds represented; >=25% of16preselected '
                      'receivers have PREFIX singlechild gain>=0.1% of common paid archiveHV; mean PREFIX gain '
                      '>0 and >=1.05*max(meanORDER,meanCONTEXT); paired PREFIX-vs-max(ORDER,CONTEXT) wins>losses. '
                      'Direction of mean difference must remain positive at reference1.25and2.0. '
                      'Only permits a separate small continuation study, never full algorithm promotion.',
        'roleGate': 'Separate necessary condition for a four-role supply claim: for same8draw budgets, '
                    'mean PREFIX gain averaged equally over M/E/W >=1.05*CENTER and positive, '
                    'receiver-paired mean M/E/W wins>CENTER losses in BOTH instances. '
                    'Report all roles, not maximum among3 as equal cost. Real-source association, not causal '
                    'proof of responsibility specialization without matched UNIFORM source control.',
        'stop': 'Failing prefixGate stops this first-worker-reuse prefix rule. No block-length, factory, '
                'source window, role subset, seed, threshold, context or ordering scan to rescue it. '
                'If prefix passes but role fails, do not claim distinctive four-group collaboration.',
        'limits': 'Offline finite-sample mechanism probe; no same-time/complete-algorithm claim, new sharing '
                  'selector, Q, budget allocation, production change or external transfer. Observation, '
                  'construction, paid evaluation and full-QA times separate where possible.'}


def source_pool(stem, seed):
    path = SOURCE / stem / str(seed) / 'ON/global-working-pools.jsonl'
    snapshot, = [s for s in rows(path) if s['role'] == 'WORKER_COST' and s['step'] == 49]
    assert snapshot['paidFE'] == 5100 and snapshot['parentCount'] == 100 and len(snapshot['points']) == 115
    grouped = {role: [] for role in ROLES}
    for index in snapshot['actualIndices']:
        role = 'MAKESPAN' if index < 15 else 'CENTER' if index < 70 else 'ENERGY' if index < 85 else 'WORKER_COST'
        point = snapshot['points'][index]
        assert point['earliestKnownPaidFE'] <= 5100
        if point['category'] == 0: grouped[role].append({'index': index, 'role': role, **point})
    assert {r: len(v) for r, v in grouped.items()} == {'MAKESPAN': 11, 'CENTER': 47, 'ENERGY': 11, 'WORKER_COST': 11}
    return snapshot, grouped, path


def evenly(values):
    indices = np.linspace(0, len(values) - 1, 8, dtype=int)
    assert len(set(indices)) == 8
    return [values[int(i)] for i in indices]


def prefix_jobs(teacher, factory):
    seen, jobs = set(), []
    for job, f, worker in zip(teacher['JS'], teacher['FA'], teacher['WA']):
        if f != factory: continue
        jobs.append(job)
        if worker in seen: return jobs
        seen.add(worker)
    return []


def splice(receiver, teacher, factory, block, method, factories):
    tuples = by_job(receiver).copy();source = by_job(teacher)
    tuples[block] = source[block]
    if not block: return receiver, 'NO_WORKER_REUSE'
    if set(tuples[:, 0]) != set(range(factories)): return receiver, 'EMPTY_RECEIVER_FACTORY'
    jobs = set(block);ordered = [j for j in receiver['JS'] if j in jobs] if method == 'ORDER_CONTROL' else block
    chains = [[j for j in receiver['JS'] if j not in jobs and tuples[j, 0] == f] for f in range(factories)]
    chains[factory] = chains[factory] + ordered if method == 'CONTEXT_CONTROL' else ordered + chains[factory]
    sequence = [j for chain in chains for j in chain]
    assert sorted(sequence) == list(range(len(sequence)))
    return {'JS': sequence, **{name: [int(tuples[j, col]) for j in sequence]
            for col, name in enumerate(('FA', 'MA', 'WA'))}}, 'ELIGIBLE'


def physical_key(point):
    tuples = by_job(point)
    return tuple((f, tuple((j, int(tuples[j, 1]), int(tuples[j, 2])) for j in point['JS'] if tuples[j, 0] == f))
                 for f in sorted(set(point['FA'])))


def prepare(root, stem):
    folder = root / stem; folder.mkdir(); shutil.copytree(BASE / stem / 'inputs', folder / 'inputs')
    cases, lines, backgrounds = [], [], {}
    factories = int(stem.split('_')[1])
    for seed in SEEDS:
        snapshot, grouped, path = source_pool(stem, seed)
        backgrounds[str(seed)] = snapshot['knownArchive']
        for receiver_rank, receiver in enumerate(evenly(grouped['CENTER'])):
            for role in ROLES:
                for teacher_rank, teacher in enumerate(evenly(grouped[role])):
                    factory = (receiver_rank + teacher_rank) % factories
                    block = prefix_jobs(teacher, factory);case = f'c{len(cases)}'
                    variants = {'PARENT': receiver, 'TEACHER': teacher}
                    flags = set()
                    for method in METHODS[2:]:
                        variants[method], reason = splice(receiver, teacher, factory, block, method, factories)
                        flags.add(reason)
                    assert len(flags) == 1;reason, = flags
                    cases.append({'case': case, 'seed': seed, 'source': str(path), 'paidFE': 5100,
                        'receiverRank': receiver_rank, 'receiverIndex': receiver['index'], 'role': role,
                        'teacherRank': teacher_rank, 'teacherIndex': teacher['index'], 'factory': factory,
                        'block': block, 'reason': reason, 'receiver': receiver, 'teacher': teacher,
                        'prefixPhysicallyEqualsParent': physical_key(variants['PREFIX']) == physical_key(receiver),
                        'orderPhysicallyEqualsPrefix': physical_key(variants['ORDER_CONTROL']) == physical_key(variants['PREFIX']),
                        'contextPhysicallyEqualsPrefix': physical_key(variants['CONTEXT_CONTROL']) == physical_key(variants['PREFIX'])})
                    for method in METHODS:
                        point = variants[method];expected = point['objectives'] if method in METHODS[:2] else None
                        lines.append('\t'.join([case, method, '-' if expected is None else ','.join(map(str, expected)),
                            *(','.join(map(str, point[k])) for k in ('JS', 'FA', 'MA', 'WA')),
                            str(factory), ','.join(map(str, block)) or '-', reason]))
    assert len(cases) == 512 and len(lines) == 2560
    write_once(folder / 'cases.json', cases);write_once(folder / 'backgrounds.json', backgrounds)
    write_once(folder / 'coverage.json', {'pairs': len(cases), 'reasons': dict(Counter(c['reason'] for c in cases)),
        'identicalOrderControls': sum(c['orderPhysicallyEqualsPrefix'] for c in cases),
        'identicalContextControls': sum(c['contextPhysicallyEqualsPrefix'] for c in cases)})
    (folder / 'cases.tsv').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return len(lines)
