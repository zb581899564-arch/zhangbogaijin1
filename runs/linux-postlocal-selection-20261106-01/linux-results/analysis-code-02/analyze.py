"""Linux-only all-registered-endpoint metrics after the complete scientific batch."""
import argparse
import csv
import json
from pathlib import Path
import platform
import sys
import time
import numpy as np
from prepare import read, write

ENDPOINTS = ['finalArchive', 'workingPopulation', 'archive2B', 'working2B']


def raw_front(population):
    return [row['raw']['objectives'] for row in population]


def compare(observations, plan, endpoint):
    from analysis_metrics import pair, distribution
    from audit_metrics import verify_pair
    values = {(row['seed'], row['arm']): row[endpoint] for row in observations}
    output = []
    for a, b in plan['comparisons']:
        pairs = [pair(seed, values[seed, a], values[seed, b]) for seed in plan['seeds']]
        for record in pairs:
            verify_pair(record, values[record['seed'], a], values[record['seed'], b])
        output.append(dict(candidate=a, control=b, endpoint=endpoint, pairs=pairs,
            HVEffectPct={radius: distribution([p['HVEffectPct'][radius] for p in pairs])
                         for radius in ['1.25', '1.5', '2.0']},
            IGDplusSymmetricImprovementPct=distribution([p['IGDplusSymmetricImprovementPct'] for p in pairs]),
            IGDImprovement=distribution([p['IGDImprovement'] for p in pairs]),
            Cdelta=distribution([p['Cdelta'] for p in pairs]),
            C_A_B=distribution([p['coverage']['C_A_B'] for p in pairs]),
            C_B_A=distribution([p['coverage']['C_B_A'] for p in pairs])))
    return output


def selection_diagnostic(root, stem, seed):
    selections = {arm: read(root / 'science' / stem / str(seed) / arm / 'selected.json')
                  for arm in ['RAW_ROLE', 'POST_ROLE', 'POST_PARETO']}
    identities = {arm: {(r['origin'], r['sourceIndex']) for r in rows} for arm, rows in selections.items()}
    return dict(seed=seed, retainedOrigins={arm: {kind: sum(r['origin'] == kind for r in rows)
                for kind in ['P', 'C']} for arm, rows in selections.items()},
                selectedRootOverlap={a + '/' + b: len(identities[a] & identities[b])
                                     for a, b in [('POST_ROLE', 'RAW_ROLE'), ('POST_ROLE', 'POST_PARETO')]},
                qualification='Root identity changes only; different budgets at selection and evolved states prevent a causal quality claim')


def instance(root, spec, plan):
    from analysis_metrics import frozen_scale, metrics, reference_from
    from audit_metrics import endpoint_metrics, verify_metrics_record, independent_nd
    stem = spec['stem']; scale = frozen_scale(spec)
    folders = {(seed, arm): root / 'science' / stem / str(seed) / arm
               for seed in plan['seeds'] for arm in plan['arms']}
    fronts = {key: read(folder / 'front.json') for key, folder in folders.items()}
    reference, source_ids = reference_from(fronts)
    independent_reference = independent_nd(np.vstack(list(fronts.values())))
    assert set(map(tuple, reference)) == set(map(tuple, independent_reference))
    observations, checks = [], []
    for (seed, arm), folder in folders.items():
        receipt, passes = read(folder / 'receipt.json'), read(folder / 'passes.json')
        assert receipt['successful'] == 3 * plan['passFE'][stem] and len(passes) == 3
        assert all(p['complete'] for p in passes)
        middle = passes[1]['afterPopulation'] if arm == 'RAW_ROLE' else read(folder / 'selected.json')
        raw = dict(finalArchive=fronts[seed, arm], workingPopulation=raw_front(read(folder / 'after.json')),
                   archive2B=passes[1]['publicArchive'], working2B=raw_front(middle))
        row = dict(seed=seed, arm=arm, successfulFE=receipt['successful'], searchSeconds=receipt['searchSeconds'],
                   prepareSeconds=receipt['prepareSeconds'], processSeconds=read(folder / 'process.json')['seconds'])
        for endpoint, points in raw.items():
            row[endpoint] = metrics(points, reference, scale)
            norm = {'lower': np.asarray(spec['normalization']['lower']), 'scale': np.asarray(spec['normalization']['scale'])}
            expected, errors = endpoint_metrics(independent_nd(points), independent_reference, norm)
            verify_metrics_record(row[endpoint], expected)
            checks.append(dict(seed=seed, arm=arm, endpoint=endpoint, absoluteHVErrors=errors))
        background = read(root / 'inputs' / stem / str(seed) / 'background.json')
        initial = metrics(background, reference, scale)
        row['HVAboveA0'] = {r: row['finalArchive']['HV'][r] - initial['HV'][r] for r in initial['HV']}
        assert min(row['HVAboveA0'].values()) >= -1e-11
        observations.append(row)
    comparisons = [c for endpoint in ENDPOINTS for c in compare(observations, plan, endpoint)]
    return dict(instance=stem, normalization=spec['normalization'], reference=reference.tolist(),
                referenceSourceIds=source_ids, observations=observations, comparisons=comparisons,
                selectionDiagnostics=[selection_diagnostic(root, stem, seed) for seed in plan['seeds']],
                independentHVChecks=checks)


def report(result, out):
    lines = ['# Post-local selection: registered three-arm diagnostic', '',
             'Three reused developmental source seeds; each arm pays3B. No full-algorithm or equal-time claim.', '',
             'Positive HV/IGD+ effect favours candidate. C directions are not complementary.', '',
             '|Instance|Endpoint|Candidate/control|HV % median|IGD+ symmetric % median|C(A,B)% / C(B,A)%|',
             '|---|---|---|---:|---:|---:|']
    records = []
    for case in result['instances']:
        for comp in case['comparisons']:
            lines.append(f"|{case['instance']}|{comp['endpoint']}|{comp['candidate']}/{comp['control']}|"
                         f"{comp['HVEffectPct']['1.5']['median']:.6f}|{comp['IGDplusSymmetricImprovementPct']['median']:.6f}|"
                         f"{100*comp['C_A_B']['median']:.4f} / {100*comp['C_B_A']['median']:.4f}|")
            for p in comp['pairs']:
                records.append(dict(instance=case['instance'], endpoint=comp['endpoint'], candidate=comp['candidate'],
                    control=comp['control'], seed=p['seed'], HVEffectPct=p['HVEffectPct']['1.5'],
                    IGDplusSymmetricImprovementPct=p['IGDplusSymmetricImprovementPct'], **p['coverage']))
    (out / 'report.md').write_text('\n'.join(lines) + '\n')
    with (out / 'paired-comparisons.csv').open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)


def main():
    assert platform.system() == 'Linux'
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ['root', 'anchor', 'donor', 'output']:
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args(); start = time.perf_counter()
    assert read(args.root / 'science-complete.json')['passed']
    assert read(args.root / 'science-independent-audit.json')['passed']
    args.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.anchor / 'payload'))
    sys.path.insert(0, str(args.donor / 'analysis-code'))
    plan, anchor = read(args.root / 'protocol.json'), read(args.anchor / 'protocol.json')
    assert [spec['stem'] for spec in anchor['instances']] == plan['instances']
    result = dict(instances=[instance(args.root, spec, plan) for spec in anchor['instances']],
        scienceFE=plan['scienceFE'], sourceNewFE=0, newSearchFEAtAnalysis=0, newDecoderCallsAtAnalysis=0,
        EAFProduced=False, sameTimeAdvantageProved=False, allInputsAlreadyUsedDevelopmentStates=True,
        sourceCoverage='All six first batches S=0; no direct shared-proposal postlocal claim')
    write(args.output / 'analysis.json', result); report(result, args.output)
    write(args.output / 'acceptance.json', dict(passed=True, seconds=time.perf_counter()-start,
          independentHVChecks=sum(len(c['independentHVChecks'])*3 for c in result['instances']),
          allPairedCAndHVEffectsVerified=True, referenceOfflineOnly=True, newSearchFE=0, newDecoderCalls=0))
    print('POSTLOCAL_ANALYSIS_COMPLETE', args.output, flush=True)


if __name__ == '__main__':
    main()
