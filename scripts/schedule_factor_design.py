"""Legal joint bundles plus order, without splitting factory-local resource ids from their factory."""
import shutil
import numpy as np

from run_long_budget_bridge import ROOT, read, write_once
from gap_structure_sources import NAT, by_job

SOURCE = ROOT / 'runs/gap-schedule-structure-20261105-124609-883191'
STEMS = ('20_8_5_1', '100_2_3_1')
METHODS = ('PARENT', 'ORDER_ONLY', 'BUNDLE_ONLY', 'TARGET')


def hybrid(order_source, bundle_source):
    bundles = by_job(bundle_source);sequence = order_source['JS']
    return {'JS': list(sequence), **{name: [int(bundles[job, column]) for job in sequence]
            for column, name in enumerate(('FA', 'MA', 'WA'))}}


def protocol():
    return {'source': str(SOURCE), 'instances': read(NAT / 'protocol.json')['instances'], 'methods': METHODS,
        'question': 'In actual observed enhanced-NSGA dominators, how much single-point gap recovery '
                    'survives order only versus complete job(factory,machine,worker) bundles only?',
        'scope': 'Schedule-level explanatory counterfactual, not algorithm treatment, new teacher or proof '
                 'FAcauses gap. Explicitly separate from failed identity-shake materiality, conditional '
                 'exchange, v7smallsyntheticbarriers and one-stepactioncritic. No learning or policy implementation.',
        'sampling': 'All12prior strata, each32 equally spaced FULLfront indices in stable objective order '
                    'before checking observed strictdominator. Missing matches retained, no replacement. '
                    'Target fixed by previous minimumFA/minimumbundle/objectivedistance rule; no new outcome selection.',
        'factors': 'WholeJSorder and perjob(FA,MA,WA)bundle. Fourlegal corners PARENT,ORDER_ONLY, '
                   'BUNDLE_ONLY,TARGET. Resource ids travel with their originalfactory; do not graft '
                   'FAalone or remap/clamp resources. All factories remain nonempty because source '
                   'bundle assignments valid. Commonrepair must edit0 or stop. No activewaiting/modelchange.',
        'budget': 'Exactly4charged guarded evaluations per matched pair, including repeated knownsource '
                  'parent/target, each also independentfulltimelineQA. <=1536newFE; exactperinstance '
                  'fee plan frozen after deterministic input preparation before any evaluation. No dedupfreecalls.',
        'score': 'SinglecandidateHV addition against complete sourceFULLfront at its registered endpoint, '
                 'ref1.5andoriginalscales. TARGET is privileged known solution, not an online available '
                 'teacher or oneFEalgorithm success. Report sums then sum-ratios to TARGET, perpair '
                 'fractions and signed twofactorfinite-difference; never unionallhybridsasonecandidate.',
        'interpretation': 'No performance pass/selector authorization. Report missing/zero-target-gain '
                          'and all strata separately. LargechangedFA distance alone is not evidence '
                          'that a large mutation is needed; bothoptimizers may have different ancestors. '
                          'Do not tune factors, target match, samples, scales or thresholds after outcomes.',
        'engineering': 'Frozen modelclasspath actualDynamicEvaluation/Decoder/Validator class identity '
                       'and SHA/JDK; sourceendpoint objectives bitexact; every fullschedule timeline '
                       'QA matches paid decoder. Repair0, duplicate attempts charged, lastvalidfront '
                       'and usedFE retained onfailure. Defaultmainline/fourroles/Q/sharing unchanged; no transfer.'}


def prepare(root, stem):
    folder = root / stem;folder.mkdir();shutil.copytree(NAT / stem / 'inputs', folder / 'inputs')
    lines = [];selected = []
    for path in sorted((SOURCE / stem).glob('*.json')):
        data = read(path);indices = np.linspace(0, len(data['parentGenomes']) - 1, 32, dtype=int)
        assert len(set(indices)) == 32
        for index in indices:
            selected_match = data['matches'][int(index)]['match'];case = f'c{len(selected)}'
            row = {'case': case, 'source': str(path), 'stem': stem, 'seed': data['seed'], 'stratum': data['stratum'],
                   'parentIndex': int(index), 'targetIndex': None if selected_match is None else selected_match['targetIndex']}
            selected.append(row)
            if selected_match is None:continue
            parent = data['parentGenomes'][int(index)];target = data['targetGenomes'][selected_match['targetIndex']]
            variants = {'PARENT': hybrid(parent, parent), 'ORDER_ONLY': hybrid(target, parent),
                        'BUNDLE_ONLY': hybrid(parent, target), 'TARGET': hybrid(target, target)}
            assert all(variants['PARENT'][k] == parent[k] and variants['TARGET'][k] == target[k] for k in ('JS', 'FA', 'MA', 'WA'))
            for method in METHODS:
                point = variants[method];expected = parent['objectives'] if method == 'PARENT' else target['objectives'] if method == 'TARGET' else None
                lines.append('\t'.join([case, method, '-' if expected is None else ','.join(map(str, expected)),
                    *(','.join(map(str, point[k])) for k in ('JS', 'FA', 'MA', 'WA'))]))
    write_once(folder / 'selected-pairs.json', selected)
    (folder / 'cases.tsv').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return len(lines)
