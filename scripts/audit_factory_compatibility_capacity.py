"""Pre-quality, zero-decoder compatibility audit; not an online pool or selection mechanism."""
from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once
from research.semantic_repair.evidence import digest
from paid_teacher_design import SOURCE, SPECS, STEMS, SEEDS, key
from factory_cover_capacity import analyze_points, fixtures


def context_entries(initial, snapshot):
    known = {}
    scopes = ((1, initial), (2, snapshot['parents']), (4, snapshot['pooledPersonalHistories']),
              (8, snapshot['allPaidArchiveGenomes']))
    for membership, points in scopes:
        for point in points:
            assert point['earliestKnownPaidFE'] <= snapshot['preBatchFE']
            identity = key(point)
            record = known.setdefault(identity, {'point': {k: point[k] for k in ('JS', 'FA', 'MA', 'WA', 'objectives')},
                'firstPaidFE': point['earliestKnownPaidFE'], 'firstRoles': [], 'sourceMembership': 0})
            role = point.get('firstOriginRole', 'INITIALIZATION' if membership == 1 else 'UNKNOWN')
            if role not in record['firstRoles']: record['firstRoles'].append(role)
            record['sourceMembership'] |= membership
    return sorted(known.values(), key=lambda p: (p['firstPaidFE'], key(p['point'])))


def main():
    root = ROOT / 'runs' / datetime.now().strftime('factory-compatibility-capacity-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('FACTORY_COMPATIBILITY_ROOT', root, flush=True)
    write_once(root / 'protocol.json', {'source': str(SOURCE), 'instances': STEMS, 'sourceSeeds': SEEDS,
        'scope': 'Necessary encoded compatibility capacity only; zero new search FE and decoder calls. '
                 'All six original first-generation CENTER windows. First-role absence retained as UNKNOWN.',
        'hypotheses': {'localContext': 'A factory record needs its own factory/job set/physical input, '
                       'not the complete sourceFApartition. Does pooling identical local job sets across '
                       'different fullFAcontexts supply additional distinct ordered job/MA/WA blocks?',
                       'novelAssignment': 'Can complete paid factory job sets from different observed '
                       'assignments form a disjoint full cover whose wholeFAassignment has never appeared?'},
        'source': str(SOURCE), 'inputs': 'All100initial+100current+allacceptedpersonalhistory+actualpaidNDgenomes. '
                    'FullFAcanonicalized by job identity; local order/MA/WA retained. No objective filtering '
                    'or genotype reconstruction from objective absence. Protected/free points all retained '
                    'for an explicit compatibility upper bound, not silently injected into original pools.',
        'computation': 'LocalContext exact set difference for every observedFA. NovelAssignment deterministic '
                       'bitmask exact cover ordered by factory pool size then mask; last factory complement '
                       'lookup. Max250000candidate nodes and256novel witnesses per context. Hitting a cap '
                       'does not prove absence/exhaustiveness. Source indices and paid FE retained.',
        'necessaryGates': 'Each hypothesis separately: each instance>=4of6windows covering both source seeds. '
                          'LocalContext window needs>=20%observed assignments enriched by at least one '
                          'distinct compatible block from another completeFAcontext. NovelAssignment '
                          'window needs>=16different novel complete assignments found within fixed node budget. '
                          'Pass permits only bounded full-decoder/objective-potential QA, not online composition '
                          'or another selector. No quality, same-time, role credit or novelty claim.',
        'failure': 'Stop the failing compatibility hypothesis; no changing node caps, windows, seeds, '
                   'compatibility definitions or gates to rescue it. Old fixed-family pool/teacher failures unchanged.',
        'limits': 'First CENTER windows do not contain newly generated E/W supply. Complete family-free '
                  'upper bound changes supply/context scope, not proof of existing-rule omission. No search, '
                  'resource policy, model, old evidence or default mainline change; no download/transfer.'})
    for name in ('audit_factory_compatibility_capacity.py', 'factory_cover_capacity.py'):
        shutil.copy2(Path(__file__).with_name(name), root / name)
    write_once(root / 'arithmetic-acceptance.json', fixtures())
    specs = {s['stem']: s for s in read(SPECS / 'protocol.json')['instances']}; results = []; input_paths = []
    try:
        for stem in STEMS:
            cases = []
            for seed in SEEDS:
                source = SOURCE / stem / str(seed) / 'capture'
                assert read(source / 'observation-equivalence.json')['status'] == 'PASS'
                paths = [source / name for name in ('mating-initial-points.jsonl', 'mating-source-pools.jsonl')]
                input_paths.extend(paths); initial = rows(paths[0])
                for snap in rows(paths[1]):
                    assert snap['role'] == 'CENTER' and snap['generation'] == 1
                    entries = context_entries(initial, snap); case_id = f'{seed}-step{snap["step"]}'
                    target = root / stem / case_id; target.mkdir(parents=True)
                    write_once(target / 'source-genomes.json', entries)
                    result = analyze_points(entries, int(stem.split('_')[2]), int(stem.split('_')[0]))
                    result.update({'seed': seed, 'step': snap['step'], 'paidFE': snap['preBatchFE'],
                        'localContextCapacity': result['enrichedAssignmentFraction'] >= .2,
                        'novelAssignmentCapacity': len(result['novelCoverWitnesses']) >= 16})
                    write_once(target / 'analysis.json', result); cases.append(result)
                    print('FACTORY_COMPATIBILITY_CASE', stem, case_id, 'assignments', result['observedAssignments'],
                          'enrichedFraction', result['enrichedAssignmentFraction'], 'novelFound',
                          len(result['novelCoverWitnesses']), 'nodes', result['nodesExamined'], flush=True)
            gates = {name: sum(c[name] for c in cases) >= 4 and all(any(c[name] and c['seed'] == seed
                     for c in cases) for seed in SEEDS) for name in ('localContextCapacity', 'novelAssignmentCapacity')}
            summary = {'stem': stem, 'windows': len(cases), 'gates': gates,
                       'passedWindows': {name: sum(c[name] for c in cases) for name in gates}}
            write_once(root / stem / 'summary.json', summary); results.append(summary)
        write_once(root / 'input-hashes.json', {str(p): digest(p) for p in sorted(set(input_paths))})
        decisions = {name: all(r['gates'][name] for r in results) for name in results[0]['gates']}
        write_once(root / 'analysis.json', {'instances': results, 'worthObjectivePotentialQA': decisions,
                                           'searchFE': 0, 'decoderCalls': 0, 'algorithmImplemented': False})
    except BaseException as error:
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error),
                                         'searchFE': 0, 'decoderCalls': 0}); raise
    write_once(root / 'status.json', {'status': 'COMPLETE', 'searchFE': 0, 'decoderCalls': 0,
                                     'worthObjectivePotentialQA': decisions, 'goalAchieved': False})
    print('FACTORY_COMPATIBILITY_COMPLETE', decisions, flush=True)


if __name__ == '__main__': main()
