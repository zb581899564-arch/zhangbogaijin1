"""Post-hoc geometry and actual opportunity coverage; never changes the frozen pilot decision."""
from collections import defaultdict
from datetime import datetime
import shutil

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once, hypervolume, igd_plus, nondominated
from natural_local_support import ledger_rows
from research.semantic_repair.evidence import digest

SOURCE = ROOT / 'runs/program-exit-pilot-20261105-134233-231280'


def endpoint(folder, norm):
    point, = [p for p in rows(folder / 'anytime.jsonl')
              if p['checkpointKind'] == 'FE' and p['checkpoint'] == 100000]
    assert point['reached']
    genomes = [p for p in rows(folder / 'checkpoint-solutions.jsonl')
               if p['checkpointKind'] == 'FE' and p['checkpoint'] == 100000]
    assert {tuple(g['objectives']) for g in genomes} == {tuple(p) for p in point['front']}
    assert all(g['bornFE'] <= 100000 for g in genomes)
    return (np.asarray(point['front']) - norm['lower']) / norm['scale'], genomes


def pair_geometry(first, second):
    h_a, h_b = (hypervolume(p, (1.5,) * 3) for p in (first, second))
    together = hypervolume(nondominated(np.vstack([first, second])), (1.5,) * 3)
    def strict_coverage(front, other):
        return sum(bool(np.any(np.all(other <= point, axis=1) & np.any(other < point, axis=1))) for point in front)
    return {'firstPoints': len(first), 'secondPoints': len(second),
        'firstStrictlyDominatedBySecond': strict_coverage(first, second),
        'secondStrictlyDominatedByFirst': strict_coverage(second, first),
        'missingSecondVolumePctOfFirstHV': 100 * max(0., together - h_a) / h_a,
        'missingFirstVolumePctOfSecondHV': 100 * max(0., together - h_b) / h_b,
        'firstApproximationToSecondReferenceIGDplus': float(igd_plus(first, second)),
        'secondApproximationToFirstReferenceIGDplus': float(igd_plus(second, first)),
        'firstVsSecondObjectiveMinimaPct': (100 * (first.min(axis=0) / second.min(axis=0) - 1)).tolist()}


def actual_search_scope(folder, genomes):
    receipt, = rows(folder / 'run-receipt.jsonl');search = receipt['search']
    visits = defaultdict(set);slots = defaultdict(int);paid = defaultdict(int)
    for row in ledger_rows(folder / 'local-ledger.csv'):
        group = str(row['group']);visits[group].add(row['visit']);slots[group] += 1;paid[group] += row['paid']
    result = {'globalFE': search['global.evaluations'], 'interFE': search.get('inter.evaluations', 0),
        'intraFE': search.get('intra.evaluations', 0),
        'byPhysicalGroup': {g: {'startedParticleVisits': len(visits[g]), 'ledgerSlots': slots[g], 'paidFE': paid[g]} for g in visits}}
    # First-generation FULL ordering has a verifiable FE boundary, not an inferred generation label.
    if 'FULL_' in folder.name:
        assert search['global.evaluations'] == 5000 and search['initialization.evaluations'] == 100
        assert all(search.get(f'{phase}.g{g}.evaluations', 0) == 0 for phase in ('inter', 'intra') for g in (3, 4))
        boundary = 5100 + search.get('inter.g1.evaluations', 0) + search.get('intra.g1.evaluations', 0)
        births = defaultdict(int)
        for genome in genomes:
            fe = genome['bornFE'];phase = 'initial' if fe <= 100 else 'firstGlobal' if fe <= 5100 else 'Mlocal' if fe <= boundary else 'Clocal'
            births[phase] += 1
        result.update({'firstMlocalEndFE': boundary, 'frontPointBirthPhases': dict(births),
            'laterBoundaryLocalSearchNotReached': True})
    return result


def analyze_instance(root, spec, seeds, arms):
    stem = spec['stem'];fronts = {};scopes = {}
    for seed in seeds:
        for arm in arms:
            folder = SOURCE / stem / f'FE-{seed}-{arm}';front, genomes = endpoint(folder, spec['normalization'])
            fronts[seed, arm] = front;scopes[f'{seed}:{arm}'] = actual_search_scope(folder, genomes)
    comparisons = []
    for seed in seeds:
        for first, second in (('FULL_ON', 'FULL_OFF'), ('FULL_ON', 'NSGA_ON'), ('FULL_ON', 'NSGA_OFF')):
            comparisons.append({'seed': seed, 'first': first, 'second': second,
                                **pair_geometry(fronts[seed, first], fronts[seed, second])})
    reference = nondominated(np.vstack(list(fronts.values())))
    origins = defaultdict(list)
    for point in reference:
        labels = tuple(f'{seed}:{arm}' for (seed, arm), values in fronts.items() if np.any(np.all(values == point, axis=1)))
        assert labels;origins[labels].append(point)
    partition = [{'origins': list(labels), 'referencePoints': len(values), 'referenceWeight': len(values) / len(reference),
        'meanIGDplusByOnArmAndSeed': {f'{seed}:{arm}': float(igd_plus(fronts[seed, arm], np.asarray(values)))
                                   for seed in seeds for arm in ('FULL_ON', 'NSGA_ON')}}
        for labels, values in origins.items()]
    assert sum(p['referencePoints'] for p in partition) == len(reference)
    result = {'stem': stem, 'comparisons': comparisons, 'actualSearchScope': scopes,
        'registeredEmpiricalReferenceSize': len(reference), 'empiricalReferenceOriginPartition': partition,
        'noAlternativeReferenceOrGateSubstitution': True, 'pilotStopUnchanged': True}
    write_once(root / f'{stem}.json', result)
    for c in comparisons:
        if c['second'] == 'NSGA_ON':
            print('EXIT_FRONTIER_GEOMETRY', stem, c, flush=True)
    print('EXIT_SEARCH_SCOPE', stem, {k: v for k, v in scopes.items() if 'FULL_ON' in k}, flush=True)
    return result


def main():
    assert read(SOURCE / 'status.json')['status'] == 'COMPLETE'
    root = ROOT / 'runs' / datetime.now().strftime('program-exit-frontiers-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('PROGRAM_EXIT_FRONTIERS_ROOT', root, flush=True)
    plan = read(SOURCE / 'protocol.json');shutil.copy2(__file__, root)
    write_once(root / 'protocol.json', {'source': str(SOURCE), 'additionalSearchFE': 0, 'decoderCalls': 0,
        'scope': 'Post-hoc description of ALL16registeredFE endpoints: paired bidirectional volume, '
                 'strict dominance, objective minima; actual local visits/FE and paid birth phases; '
                 'exact disjoint origin partition of the unchanged registered empiricalIGD reference. '
                 'No new gate, reweighting, alternative acceptance, excluded seed or policy promotion.'})
    inputs = [p for spec in plan['instances'] for p in (SOURCE / spec['stem']).glob('FE-*/*')
              if p.name in ('anytime.jsonl', 'checkpoint-solutions.jsonl', 'local-ledger.csv', 'run-receipt.jsonl')]
    write_once(root / 'input-hashes.json', {str(p.relative_to(SOURCE)): digest(p) for p in inputs})
    try:
        for spec in plan['instances']: analyze_instance(root, spec, plan['seeds'], plan['arms'])
    except BaseException as error:
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error),
            'additionalSearchFE': 0, 'decoderCalls': 0});raise
    write_once(root / 'status.json', {'status': 'COMPLETE', 'additionalSearchFE': 0, 'decoderCalls': 0,
        'pilotStopUnchanged': True, 'goalAchieved': False})


if __name__ == '__main__': main()
