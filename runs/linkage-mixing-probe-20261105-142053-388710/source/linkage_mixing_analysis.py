"""Independent program accounting and outcomes against an immutable, previously paid archive."""
from collections import defaultdict

import numpy as np

from run_long_budget_bridge import read, rows, write_once
from fa_admission_volume import volume
from run_program_acceptance_audit import pddr
from linkage_mixing_design import METHODS, SEEDS


def normalized(points, norm):
    return (np.asarray(points) - norm['lower']) / norm['scale']


def verify_context(folder, norm, jobs):
    outcomes = rows(folder / 'probe/outcomes.jsonl');programs = rows(folder / 'probe/programs.jsonl')
    source_data = {}
    for line in (folder / 'sources.tsv').read_text('utf-8').splitlines():
        f = line.split('\t');source_data[int(f[0])] = np.asarray(list(map(float, f[3].split(','))))
    reference = np.asarray(list(source_data.values()));steps = 2 * jobs - 1;groups = defaultdict(list)
    assert [r['paidFE'] for r in outcomes] == list(range(101, 101 + len(outcomes)))
    for r in outcomes:
        groups[r['role'], r['receiverRank'], r['method']].append(r)
        candidate, parent = np.asarray(r['objectives']), np.asarray(r['parentObjectives'])
        if r['role'] == 'CENTER':
            c, i = pddr(candidate, parent, reference);accepted = c < i
        else: accepted = candidate[{'MAKESPAN': 0, 'ENERGY': 1, 'WORKER_COST': 2}[r['role']]] < parent[{'MAKESPAN': 0, 'ENERGY': 1, 'WORKER_COST': 2}[r['role']]]
        assert bool(accepted) == r['accepted'], 'Actual program role acceptance differs'
        if r['fallback']: assert np.array_equal(candidate, parent)
    assert len(programs) == len(groups) == 128
    for p in programs:
        own = groups[p['role'], p['receiverRank'], p['method']]
        assert len(own) == p['successfulChildFE'] == steps and [r['step'] for r in own] == list(range(steps))
        current = source_data[p['sourceIndex']]
        for r in own:
            assert np.array_equal(current, r['parentObjectives'])
            if r['accepted']: current = np.asarray(r['objectives'])
        assert np.array_equal(current, p['finalGenome']['objectives'])
    # Same recipient and same original donor at each corresponding paid step.
    for role in ('MAKESPAN', 'CENTER', 'ENERGY', 'WORKER_COST'):
        for rank in range(8):
            paired = [groups[role, rank, method] for method in METHODS]
            for k in range(steps): assert len({p[k]['donorIndex'] for p in paired}) == 1
            assert [p['subsetSize'] for p in paired[0]] == [p['subsetSize'] for p in paired[1]]
    write_once(folder / 'program-acceptance.json', {'status': 'PASS', 'childRows': len(outcomes), 'completePrograms': len(programs),
        'roleDecisionsIndependentlyRecomputed': len(outcomes), 'sameDonorSequencesAndTreeSizes': True,
        'allCurrentStateChainsAndFinalObjectivesEqual': True, 'additionalSearchFE': 0, 'additionalDecoderCalls': 0})
    return groups, programs


def analyze(root, spec):
    stem = spec['stem'];norm = spec['normalization'];jobs = int(stem.split('_')[0]);scored = []
    for seed in SEEDS:
        folder = root / stem / str(seed);groups, programs = verify_context(folder, norm, jobs)
        background = normalized(read(folder / 'source.json')['knownArchive'], norm)
        for ref in (1.25, 1.5, 2.):
            base = volume(background, (ref,) * 3)
            for p in programs:
                own = groups[p['role'], p['receiverRank'], p['method']]
                points = normalized([r['objectives'] for r in own], norm)
                gain = max(0., volume(np.vstack([background, points]), (ref,) * 3) - base)
                final = normalized(p['finalGenome']['objectives'], norm)
                endpoint_gain = max(0., volume(np.vstack([background, final]), (ref,) * 3) - base)
                scored.append({'seed': seed, 'role': p['role'], 'receiverRank': p['receiverRank'], 'method': p['method'],
                    'reference': ref, 'programHVgain': gain, 'endStateSingleHVgain': endpoint_gain,
                    'emptyFactoryFallbacks': p['emptyFactoryFallbacks'], 'programSecondsIncludingQAAndEvidence': p['wholeProgramIncludingQAEvidenceSeconds']})
    summaries = {}
    for ref in (1.25, 1.5, 2.):
        own = [p for p in scored if p['reference'] == ref]
        lookup = {(p['seed'], p['role'], p['receiverRank'], p['method']): p['programHVgain'] for p in own}
        means = {m: float(np.mean([p['programHVgain'] for p in own if p['method'] == m])) for m in METHODS}
        deltas = [value - lookup[s, role, rank, 'RELABEL_TREE'] for (s, role, rank, method), value in lookup.items() if method == 'FA_LINKAGE']
        summaries[str(ref)] = {'meanProgramHVgain': means, 'pairedWinsVsRelabel': sum(d > 1e-10 for d in deltas),
            'pairedLossesVsRelabel': sum(d < -1e-10 for d in deltas), 'pairedTiesVsRelabel': sum(abs(d) <= 1e-10 for d in deltas),
            'positiveReceivers': sum(p['method'] == 'FA_LINKAGE' and p['programHVgain'] > 1e-10 for p in own),
            'meanBySourceSeedAndMethod': {f'{seed}:{m}': float(np.mean([p['programHVgain'] for p in own if p['method'] == m and p['seed'] == seed])) for seed in SEEDS for m in METHODS},
            'meanByRoleAndMethod': {f'{role}:{m}': float(np.mean([p['programHVgain'] for p in own if p['method'] == m and p['role'] == role]))
                for role in ('MAKESPAN', 'CENTER', 'ENERGY', 'WORKER_COST') for m in METHODS}}
    primary = summaries['1.5'];means = primary['meanProgramHVgain']
    gates = {'meanIndependentBenefit': means['FA_LINKAGE'] > 1e-10 and means['FA_LINKAGE'] >= 1.10 * means['RELABEL_TREE']
                and means['FA_LINKAGE'] >= max(means['SINGLE_JOB'], means['CLASSIC_KERNEL']),
        'receiverCoverage': primary['positiveReceivers'] >= 16,
        'pairedBenefit': primary['pairedWinsVsRelabel'] > primary['pairedLossesVsRelabel'],
        'bothSourceSeeds': all(primary['meanBySourceSeedAndMethod'][f'{seed}:FA_LINKAGE'] >= primary['meanBySourceSeedAndMethod'][f'{seed}:RELABEL_TREE'] for seed in SEEDS),
        'referenceRobustness': all(summaries[str(ref)]['meanProgramHVgain']['FA_LINKAGE'] >=
            max(summaries[str(ref)]['meanProgramHVgain'][m] for m in ('RELABEL_TREE', 'CLASSIC_KERNEL')) for ref in (1.25, 2.))}
    result = {'stem': stem, 'summaries': summaries, 'gates': gates, 'pass': all(gates.values()),
        'scope': 'Paid whole-program offspring supply under fixed source/ref, not complete optimizer or same-time result.'}
    write_once(root / stem / 'analysis.json', {**result, 'programScores': scored})
    print('LINKAGE_MIXING_ANALYSIS', stem, 'primary', {k: v for k, v in primary.items() if not k.startswith('meanBy')}, 'gates', gates, flush=True)
    return result
