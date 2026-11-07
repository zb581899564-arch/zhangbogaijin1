"""Frozen FA-dependency model and matched full mixing programs, not a faithful pGOMEA port."""
from collections import Counter
import math
import shutil
import time

import numpy as np

from run_long_budget_bridge import ROOT, read, write_once
from gap_structure_sources import NAT, by_job
from prefix_state_design import SOURCE, BASE, STEMS, SEEDS, ROLES, source_pool, evenly

METHODS = ('FA_LINKAGE', 'RELABEL_TREE', 'SINGLE_JOB', 'CLASSIC_KERNEL')
NOISE_SEED = 13450003


def protocol():
    return {'source': str(SOURCE), 'base': str(BASE), 'instances': read(NAT / 'protocol.json')['instances'],
        'sourceSeeds': SEEDS, 'noiseSeed': NOISE_SEED, 'methods': METHODS,
        'question': 'Does a fixed learned FA linkage tree improve a complete sequential mixing program '
                    'over a matched random-label tree, single-job mixing and the native classic kernel?',
        'scope': 'Four real post-global source roles,2source seeds,2developmentinstances. '
                 '8stable equally spaced free receivers per role, uniform same-role free donors. '
                 'Same donor sequence and step order/noise for ALL4methods, with no outcome resampling. '
                 'This is equal-role mechanism sampling, not the15/55/15/15 full algorithm or a new seed generalization.',
        'model': 'Train once per source on ALL80free FA-by-job vectors, no objective filtering. '
                 'Empirical mutual information using natural logs; average-linkage clustering of job singletons, '
                 'maximal mean cross-cluster MI, deterministic lexicographic merge ties. All2N-1subsets '
                 'including singletons and root. RELABEL_TREE applies a fixed independent random permutation '
                 'of job labels, preserving every subset size and tree hierarchy. Do not scan alternative metrics.',
        'representation': 'By-job complete(factory,machine,worker) tuples and within-factory relative rank '
                          'keys(rank+0.5)/factoryJobCount. Copy selected donor job tuples AND rank keys; '
                          'others use current recipient. Sort within resulting factory by rank key then jobid; '
                          'canonical inter-factory concatenation. Recompute keys at each step. Missing factory '
                          'means paid unchanged-parent fallback, no shortening/repair/resampling. '
                          'No random rescaling, forced improvement or permutation-pGOMEA replication claim.',
        'program': 'Start at paid original receiver. For2N-1steps, sample one original same-role donor; '
                   'FA_LINKAGE or RELABEL uses same random subset-index order; SINGLE_JOB cycles a fixed '
                   'job permutation; CLASSIC calls actual setting0ClassicKernelBridge.child. '
                   'Every resulting candidate evaluated, duplicates/fallbacks charged. Accept only by original '
                   'role preference, CENTER common LINEAR PDDR and strict scalar boundary objectives. '
                   'No exit-HV, neutral-acceptance change, Q, learner reward, new teacher or local search.',
        'engineering': 'Actual loaded common decoder/validator/classic/PDDR and new class identities/SHA/JDK. '
                       'Source100genomes replay exactly, repair0, all paid candidates independent full timeline QA. '
                       'Pure-genome tests: empty/all subset physical endpoints, alternate neutral interleavings '
                       'produce same physical mixing child, input parents unmodified, explicit empty-factory '
                       'fallback. Full paid genome digest, systematic every257th child genes, all objectives '
                       'and decisions saved. Source factories/stages from actual Instance, no filename guessing.',
        'budget': '4source contexts*100replay=400FE. Each source32receivers*4methods*(2N-1)children. '
                  '20job9984childFE +100job50944childFE =61328total successful FE, same fullQA count. '
                  'No source-search rerun. Common replay charged once, explicitly shared across methods. '
                  'No evaluation hidden in MI/training, ranking or metric computation.',
        'score': 'Full-program HV of ALL its paid candidates added to original paid archive at5100, '
                 'one2N-1FE program is the unit. Unlike single-candidate probes, union here is explicitly '
                 'paid at the full program cost. End-state single-point gain separate. Same original '
                 'normalization/ref1.5; sensitivities1.25/2.0. Outputs never enter source donor pool or scorer.',
        'cost': 'Model-building wall time and all program construction/acceptance/paid-evaluation/fullQA '
                'times separate; source input and evidence I/O additionally included in total runtime. '
                'Random-label matched-shape control depends on learned tree too; do not pretend its shape '
                'is free. No same-time claim or hypothetical amortized performance.',
        'gate': 'BOTHinstances: meanFA_LINKAGEprogramGain>0 and >=1.10*RELABEL, >=SINGLE_JOB '
                'and>=CLASSIC; at least16of64receivers positive, paired wins overRELABEL>losses; '
                'each source seed meanFA_LINKAGE>=RELABEL. Ref1.25/2 mean differences vsRELABEL '
                'andCLASSIC nonnegative. Only permits an evolving-population protocol with matched '
                'strong classical/fullQGS/shared/Li controls, never promotion or innovation proof.',
        'stop': 'If gate fails, stop this fixed FA-MI/rank-key donation program. No changing dependency '
                'metric, rank encoding, acceptance/tie rule, donor group, tree size, root inclusion, '
                'source window, seed or gate to rescue. Failure does not refute all GOMEA/model-based algorithms.',
        'protected': 'No production/mainline, original material, frozen source, four-role/QGS/shared rules '
                     'changed. Protected20 used only as paid reference, not as mixed receivers/donors. '
                     'No download, upload, remote job or paper novelty claim.'}


def mutual_information(matrix):
    n = matrix.shape[1];result = np.zeros((n, n));count = len(matrix)
    for i in range(n):
        first = Counter(matrix[:, i])
        for j in range(i):
            second = Counter(matrix[:, j]);joint = Counter(zip(matrix[:, i], matrix[:, j]))
            value = sum((frequency / count) * math.log(frequency * count / (first[a] * second[b]))
                        for (a, b), frequency in joint.items())
            assert value >= -1e-12
            result[i, j] = result[j, i] = max(0., value)
    return result


def linkage_tree(dependency):
    clusters = [tuple([i]) for i in range(len(dependency))];subsets = list(clusters)
    while len(clusters) > 1:
        pairs = [(float(dependency[np.ix_(a, b)].mean()), a, b) for i, a in enumerate(clusters) for b in clusters[i + 1:]]
        _, a, b = min(pairs, key=lambda p: (-p[0], p[1], p[2]))
        merged = tuple(sorted(a + b));subsets.append(merged)
        clusters = sorted([c for c in clusters if c != a and c != b] + [merged])
    assert len(subsets) == 2 * len(dependency) - 1 and subsets[-1] == tuple(range(len(dependency)))
    return subsets


def field(point):
    return [','.join(map(str, point[name])) for name in ('JS', 'FA', 'MA', 'WA')]


def prepare(root, stem):
    folder = root / stem;folder.mkdir();shutil.copytree(BASE / stem / 'inputs', folder / 'inputs')
    contexts = [];n = int(stem.split('_')[0])
    for context_index, seed in enumerate(SEEDS):
        snapshot, grouped, source = source_pool(stem, seed);out = folder / str(seed);out.mkdir()
        free = [p for role in ROLES for p in grouped[role]]
        started = time.monotonic();matrix = np.asarray([by_job(p)[:, 0] for p in free]);dependency = mutual_information(matrix)
        subsets = linkage_tree(dependency);model_seconds = time.monotonic() - started
        rng = np.random.default_rng(NOISE_SEED + seed);relabel = rng.permutation(n).tolist()
        random_subsets = [tuple(sorted(relabel[j] for j in subset)) for subset in subsets]
        assert [len(s) for s in subsets] == [len(s) for s in random_subsets]
        write_once(out / 'model.json', {'freeTrainingPoints': 80, 'mutualInformation': dependency.tolist(),
            'subsets': subsets, 'randomRelabel': relabel, 'relabeledSubsets': random_subsets,
            'modelBuildSeconds': model_seconds, 'freeTrainingIndices': [p['index'] for p in free]})
        records = []
        for index in snapshot['actualIndices']:
            role = 'MAKESPAN' if index < 15 else 'CENTER' if index < 70 else 'ENERGY' if index < 85 else 'WORKER_COST'
            point = snapshot['points'][index]
            records.append('\t'.join([str(index), role, str(point['category']), ','.join(map(str, point['objectives'])), *field(point)]))
        (out / 'sources.tsv').write_text('\n'.join(records) + '\n', encoding='utf-8')
        (out / 'subsets.tsv').write_text('\n'.join(','.join(map(str, s)) + '\t' + ','.join(map(str, r))
                                           for s, r in zip(subsets, random_subsets)) + '\n', encoding='utf-8')
        parents = [{'role': role, 'rank': rank, 'sourceIndex': p['index']} for role in ROLES for rank, p in enumerate(evenly(grouped[role]))]
        (out / 'parents.tsv').write_text('\n'.join(f'{p["role"]}\t{p["rank"]}\t{p["sourceIndex"]}' for p in parents) + '\n', encoding='utf-8')
        write_once(out / 'source.json', {'source': str(source), 'paidFE': 5100, 'parents': parents, 'knownArchive': snapshot['knownArchive']})
        contexts.append({'seed': seed, 'modelSeconds': model_seconds, 'expectedSuccessfulFE': 100 + 32 * 4 * (2 * n - 1),
            'noiseSeed': NOISE_SEED + seed + context_index * 100003})
    write_once(folder / 'contexts.json', contexts)
    return contexts
