"""Zero new evaluations: compare actual paid archive with complete current and initial populations."""
from datetime import datetime
from pathlib import Path
import shutil

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once, hypervolume
from fa_admission_volume import volume
from research.composition_oracle.volume import UncoveredVolume

SOURCE = ROOT / 'runs/mating-pool-probe-20261105-062648-478040'
STEMS = ('20_8_5_1', '100_2_3_1')
SEEDS = (11730007, 11730037)


def analyze(root, spec):
    stem = spec['stem']; normal = spec['normalization']
    lower, scale = np.asarray(normal['lower']), np.asarray(normal['scale'])
    cases, errors = [], []
    for seed in SEEDS:
        folder = SOURCE / stem / str(seed) / 'capture'
        initial = rows(folder / 'mating-initial-points.jsonl')
        snapshots = rows(folder / 'mating-source-pools.jsonl')
        receipt, = rows(folder / 'run-receipt.jsonl')
        assert receipt['successful'] == 5100 and receipt['failed'] == 0 and len(initial) == 100
        assert len(snapshots) == 3
        for snap in snapshots:
            assert snap['generation'] == 1 and snap['role'] == 'CENTER'
            current = snap['parents']; assert len(current) == 100
            assert all(p['earliestKnownPaidFE'] <= snap['preBatchFE'] for p in current)
            points = lambda values: (np.asarray(values, dtype=float).reshape(-1, 3) - lower) / scale
            background = points(snap['preBatchArchive'])
            init = points([p['objectives'] for p in initial])
            working = points([p['objectives'] for p in current])
            combined = np.vstack([init, working])
            references = {}
            for ref in (1.25, 1.5, 2.):
                score = UncoveredVolume(combined, (ref,) * 3)
                paid_hv = volume(background, (ref,) * 3)
                union_hv = score.background_hv
                assert paid_hv + 1e-11 >= union_hv
                gains = score.gains(background)
                if ref == 1.5:
                    error = abs(paid_hv - hypervolume(background, (ref,) * 3)); errors.append(error)
                    assert error < 1e-11
                references[str(ref)] = {
                    'initialHV': volume(init, (ref,) * 3), 'currentHV': volume(working, (ref,) * 3),
                    'initialCurrentUnionHV': union_hv, 'allPaidHV': paid_hv,
                    'unavailableUnionFractionPct': 100 * max(0., paid_hv - union_hv) / paid_hv,
                    'bestSingleExtraGain': float(max(gains, default=0.)),
                    'bestSingleExtraGainPctOfPaidHV': 100 * float(max(gains, default=0.)) / paid_hv,
                    'material': bool(max(gains, default=0.) >= .001 * paid_hv)}
            cases.append({'seed': seed, 'generation': 1, 'role': 'CENTER', 'step': snap['step'],
                          'paidFE': snap['preBatchFE'], 'paidArchivePoints': len(background),
                          'fullCurrentParents': len(current), 'fullInitialParents': len(initial),
                          'references': references})
    material = [case for case in cases if case['references']['1.5']['material']]
    by_seed = {str(seed): sum(case['seed'] == seed for case in material) for seed in SEEDS}
    gate = len(material) >= 2 and all(value >= 1 for value in by_seed.values())
    result = {'stem': stem, 'snapshots': 6, 'materialExtraSupplySnapshots': len(material),
              'materialBySeed': by_seed, 'worthCapturingPaidArchiveGenomes': gate,
              'maxIndependentHVError': max(errors), 'cases': cases,
              'scope': 'Numeric availability only. No genotype or parent-history membership is inferred '
                       'from objective absence. These are first-generation CENTER windows, with mostly '
                       'MAKESPAN/earlier CENTER new supply, not all four roles or evidence of useful offspring.'}
    write_once(root / f'{stem}.json', result)
    return result


def main():
    root = ROOT / 'runs' / datetime.now().strftime('paid-archive-supply-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('PAID_ARCHIVE_SUPPLY_ROOT', root, flush=True)
    for name in ('audit_paid_archive_supply.py', 'fa_admission_volume.py'):
        shutil.copy2(Path(__file__).with_name(name), root)
    write_once(root / 'protocol.json', {
        'source': str(SOURCE), 'instances': STEMS, 'sourceSeeds': SEEDS, 'steps': [0, 24, 49],
        'searchFE': 0, 'decoderCalls': 0,
        'question': 'Does all-paid ND supply exceed the complete100current+100initial objective pool, '
                    'a different source from prior accepted-personal-history and live-current donor tests?',
        'primary': 'Largest single paid-archive point HV addition to union(current,initial), '
                   'divided by all-paid archive HV; frozen source normalization/ref1.5,1.25/2sensitivity.',
        'gate': 'Each instance>=2of6snapshots with largest single gain>=0.1%ofpaidHV, covering both '
                'source seeds. Pass permits only an observer-only capture of actual genotype/provenance, '
                'not a teacher selector or complete algorithm. Failure stops this concrete extra-supply '
                'hypothesis without changing windows/thresholds. No future checkpoints in backgrounds.',
        'limits': 'These snapshots contain full100physical groups, unlike the previously filtered80free '
                  'parent dataset. They do not include all personal history genomes. Numeric absence '
                  'does not prove unique genotype or causal continuation. First-generationCENTER source '
                  'does not establish independent supply by all four roles. No new evaluation, download or transfer.'})
    specs = {s['stem']: s for s in read(SOURCE / 'protocol.json')['instances']}
    results = [analyze(root, specs[stem]) for stem in STEMS]
    worth = all(result['worthCapturingPaidArchiveGenomes'] for result in results)
    write_once(root / 'analysis.json', {'instances': results, 'worthCapturingPaidArchiveGenomes': worth})
    write_once(root / 'status.json', {'status': 'COMPLETE', 'searchFE': 0, 'decoderCalls': 0,
                                     'worthCapturingPaidArchiveGenomes': worth})
    print('PAID_ARCHIVE_SUPPLY_COMPLETE', 'worthCapturingPaidArchiveGenomes', worth, flush=True)


if __name__ == '__main__': main()
