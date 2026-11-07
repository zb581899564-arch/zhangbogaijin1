"""Zero-search capacity check for persistent CENTER tasks, not a new pbest scoring experiment."""
from datetime import datetime
from pathlib import Path
import shutil

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once

SOURCE = ROOT / 'runs/paid-archive-capture-20261105-101720-096912'
SPECS = ROOT / 'runs/mating-pool-probe-20261105-062648-478040'
STEMS = ('20_8_5_1', '100_2_3_1')
SEEDS = (11730007, 11730037)


def task_weights():
    weights = np.asarray([(a, b, 12 - a - b) for a in range(1, 11) for b in range(1, 12 - a)], dtype=float) / 12
    assert weights.shape == (55, 3) and np.all(weights > 0) and np.allclose(weights.sum(axis=1), 1)
    return weights


def analyze(root, spec):
    stem = spec['stem']; scale = np.asarray(spec['normalization']['scale']); weights = task_weights()
    cases = []
    for seed in SEEDS:
        source = SOURCE / stem / str(seed) / 'capture'
        assert read(source / 'observation-equivalence.json')['status'] == 'PASS'
        for snapshot in rows(source / 'mating-source-pools.jsonl'):
            archive = np.unique(np.asarray(snapshot['preBatchArchive']), axis=0)
            assert np.isfinite(archive).all()
            ideal = archive.min(axis=0)
            shifted = (archive - ideal) / scale
            scores = np.max(shifted[:, None, :] * weights[None, :, :], axis=2)
            winner = np.argmin(scores, axis=0)
            best = np.min(scores, axis=0)
            equal_index = int(np.argmin(np.max(shifted, axis=1)))
            equal_scores = scores[equal_index]
            assert np.all(best > 1e-12), 'One-point ideal degeneracy is inconclusive, do not change scale'
            loss = 100 * (equal_scores / best - 1)
            distinct = len(set(winner.tolist()))
            divergent = int(sum(loss >= 1.))
            center = np.asarray([p['objectives'] for p in snapshot['parents'] if p['role'] == 'CENTER'])
            assert center.shape == (55, 3)
            center_scores = np.max(((center - ideal) / scale)[:, None, :] * weights[None, :, :], axis=2)
            zero_scores = np.max((archive / scale)[:, None, :] * weights[None, :, :], axis=2)
            cases.append({'seed': seed, 'step': snapshot['step'], 'paidFE': snapshot['preBatchFE'],
                'paidArchiveObjectives': len(archive), 'knownIdeal': ideal.tolist(),
                'distinctOnlineIdealTaskOptima': distinct, 'directionsWithAtLeast1PctLossFromEqualTask': divergent,
                'medianEqualTaskRegretPct': float(np.median(loss)),
                'medianBestCurrentCenterRegretPct': float(np.median(100 * (center_scores.min(axis=0) / best - 1))),
                'distinctZeroIdealOptimaDescriptiveOnly': len(set(np.argmin(zero_scores, axis=0).tolist())),
                'capacitySupported': bool(distinct >= 8 and divergent >= 20),
                'winnerObjectiveIndexes': winner.tolist(), 'archiveObjectives': archive.tolist()})
    supported = [case for case in cases if case['capacitySupported']]
    per_seed = {str(seed): sum(case['seed'] == seed for case in supported) for seed in SEEDS}
    result = {'stem': stem, 'snapshots': len(cases), 'capacitySupportedSnapshots': len(supported),
              'supportedBySeed': per_seed, 'worthPersistentTaskProtocol': len(supported) >= 4 and all(per_seed.values()),
              'cases': cases,
              'scope': 'Objective-space task capacity only. Not a causal retention deficit or evidence '
                       'persistent tasks will improve search, final HV, runtime, four-role cooperation or novelty.'}
    write_once(root / f'{stem}.json', result)
    return result


def main():
    root = ROOT / 'runs' / datetime.now().strftime('center-task-capacity-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('CENTER_TASK_CAPACITY_ROOT', root, flush=True)
    shutil.copy2(Path(__file__), root)
    write_once(root / 'protocol.json', {
        'source': str(SOURCE), 'sourceSeeds': SEEDS, 'searchFE': 0, 'decoderCalls': 0,
        'question': 'Can the existing paid front support multiple distinct persistent compromise '
                    'tasks, before considering changes to task-owned acceptance, personal memory and retention?',
        'directions': 'All55strictly positive integer triples summing12, divided12. Same lattice as '
                      'old direction-history study; no resolution/weight scan.',
        'scalarization': 'Tchebycheff max_i w_i*(f_i-z_i)/fixedScale_i. z_i=min of actual paid archive '
                         'at the exact request, never future values. Zero-ideal winner counts descriptive '
                         'only, cannot rescue a failed primary gate.',
        'sampling': 'All original first-generationCENTER step0/24/49windows from both source seeds '
                    'and both development instances, no omission or replacement.',
        'gate': 'Both instances:>=4of6windows support>=8distinct objective-vector task optima and '
                '>=20of55directions with >=1%scalar loss if forced to use the best equal-weight '
                'archive point, covering both seeds. Pass permits a separately designed persistent-task '
                'protocol only; failure stops this55-direction task route without ideal/scale/weight/window tuning.',
        'distinction': 'PriorDIR_CHEBY changed only personal-guide selection under unchanged PDDR/retention. '
                       'CENTER_HV changed Q reward. This new hypothesis would bind target identity across '
                       'generation, local search, personal progress and retention, not choose another teacher '
                       'or reopen failed tie/working-pool rules. No such architecture is implemented here.',
        'requiredControlsIfContinued': 'Original CENTER, one equal scalar task, nonpersistent direction '
                                     'assignment with the same direction marginals, and ordinary MOEA/D/MPSO-D '
                                     'with common representation/decoder/local budget, plus strongNSGA and '
                                     'four-role/share ablations. No novelty claim from generic decomposition.',
        'literature': ['https://doi.org/10.1109/TEVC.2007.892759',
                       'https://www.sciencedirect.com/science/article/pii/S0020025515005101',
                       'https://ieeexplore.ieee.org/document/7946155/'],
        'limits': 'No search, policy, default/mainline, role/Q/shared change, download or external transfer. '
                  'Static capacity is neither performance nor independent confirmation.'})
    specs = {spec['stem']: spec for spec in read(SPECS / 'protocol.json')['instances']}
    results = [analyze(root, specs[stem]) for stem in STEMS]
    worth = all(result['worthPersistentTaskProtocol'] for result in results)
    write_once(root / 'analysis.json', {'instances': results, 'worthPersistentTaskProtocol': worth})
    write_once(root / 'status.json', {'status': 'COMPLETE', 'searchFE': 0, 'decoderCalls': 0,
                                     'worthPersistentTaskProtocol': worth})
    print('CENTER_TASK_CAPACITY_COMPLETE', 'worthPersistentTaskProtocol', worth, flush=True)


if __name__ == '__main__': main()
