"""Zero-search-FE capacity audit of existing paid factory envelopes, beyond nine fixed policies."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

from datetime import datetime
from itertools import product
from pathlib import Path
import json
import math
import shutil
import time
import numpy as np
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock, hypervolume
from pool_phase_analysis import construct, check_assemblies
from research.composition_oracle.frontier import close, decode, objective_powers
from research.composition_oracle.frontier import engineering_checks as check_frontier
from research.composition_oracle.volume import UncoveredVolume, engineering_checks as check_volume

SOURCE = ROOT / 'runs/pool-retention-audit-20261105-032405-385212'
STEMS = ('20_8_5_1', '100_2_3_1')
SEED = 9940003
PHASE = 'G2_CENTER_ENTRY'


def validate_family(family, phase_fe):
    for key in ('factories', 'fullFactories'):
        for f, records in enumerate(family[key]):
            expected = {j for j, factory in enumerate(family['factoryByJob']) if factory == f}
            assert records
            for r in records:
                assert len(r['jobs']) == len(set(r['jobs'])) and set(r['jobs']) == expected
                assert len(r['machines']) == len(r['workers']) == len(r['jobs'])
                assert 0 < r['paidFE'] <= phase_fe


def assembly(factories, state, powers):
    genes = {key: [] for key in ('JS', 'FA', 'MA', 'WA')}
    for f, index in enumerate(state[3]):
        r = factories[f][index]
        genes['JS'].extend(r['jobs']); genes['FA'].extend([f]*len(r['jobs']))
        genes['MA'].extend(r['machines']); genes['WA'].extend(r['workers'])
    assert sorted(genes['JS']) == list(range(len(genes['JS'])))
    return {**genes, 'objectives': decode(state[:3], powers)}


def nine_candidates(phase, receiver, full):
    families = [{**f, 'factories': f['fullFactories'] if full else f['factories']} for f in phase['pool']['families']]
    pool = {**phase['pool'], 'families': families}
    return [c for cap, eta in product((.9, 1., 1.1), (0., 1., 4.))
            if (c := construct(pool, receiver, cap, eta)) is not None]


def analyze_instance(root, spec, cp):
    stem, norm = spec['stem'], spec['normalization']
    folder = root / stem; folder.mkdir()
    shutil.copytree(SOURCE/stem/'inputs', folder/'inputs')
    input_path = SOURCE/stem/str(SEED)/'ON/pool-phases.jsonl'
    shutil.copy2(input_path, folder/'source-pool-phases.jsonl')
    data, = rows(input_path)
    phase = next(s for s in data['snapshots'] if s['phase'] == PHASE)
    normalized = lambda p: (np.asarray(p)-norm['lower'])/norm['scale']
    background = normalized(phase['knownArchive'])
    scorers = {ref: UncoveredVolume(background, (ref,)*3) for ref in (1.25, 1.5, 2.)}
    for ref, scorer in scorers.items():
        assert abs(scorer.background_hv-hypervolume(background, (ref,)*3)) < 1e-11
    summaries, witnesses = [], {}
    for family in phase['pool']['families']:
        validate_family(family, phase['paidFE'])
        all_records = [r for key in ('factories','fullFactories') for factory in family[key] for r in factory]
        powers = objective_powers(all_records)
        receiver = next(r for r in data['laterReceivers'] if r['family'] == family['family'])
        per_mode = {}
        for mode, key in (('FINITE','factories'), ('FULL','fullFactories')):
            start = time.monotonic()
            frontier, stages = close(family[key], powers)
            dp_seconds = time.monotonic()-start
            objectives = np.asarray([decode(p[:3], powers) for p in frontier])
            points = normalized(objectives)
            scored = {}
            winners = set()
            for ref, scorer in scorers.items():
                gains = scorer.gains(points); best = int(np.argmax(gains)); winners.add(best)
                scored[str(ref)] = {'bestSingleGainPct': 100*float(gains[best])/scorer.background_hv,
                    'bestIndex': best, 'newPoints': int(np.sum(gains > 1e-10))}
            candidates = nine_candidates(phase, receiver, mode == 'FULL')
            gains_nine = scorers[1.5].gains(normalized([c['objectives'] for c in candidates])) if candidates else []
            best_nine = 100*float(max(gains_nine, default=0.))/scorers[1.5].background_hv
            # The exact closure must weakly dominate every feasible nine-policy candidate.
            for candidate in candidates:
                assert np.any(np.all(objectives <= np.asarray(candidate['objectives'])+1e-8, axis=1))
            sample = sorted({0, len(frontier)-1, *(int(i) for i in np.linspace(0,len(frontier)-1,8)),
                             *(int(np.argmin(objectives[:,k])) for k in range(3)), *winners})
            max_hv_error = 0.
            for index in sample:
                candidate = assembly(family[key], frontier[index], powers)
                # Independent existing HV implementation, before trusting material winners.
                expected = hypervolume(np.vstack([background, points[index]]), (1.5,)*3) - scorers[1.5].background_hv
                observed = scorers[1.5].gains([points[index]])[0]
                max_hv_error = max(max_hv_error, abs(expected-observed))
                assert abs(expected-observed) < 1e-11
                genome_key = tuple(tuple(candidate[k]) for k in ('JS','FA','MA','WA'))
                witnesses[genome_key] = candidate
            output = folder/f'family-{family["family"]}-{mode}-frontier.json'
            write_once(output, {'integerPowers': powers, 'states': [list(p[:3])+[list(p[3])] for p in frontier],
                                'stages': stages, 'sourceRecordsKey': key})
            per_mode[mode] = {'cartesianCombinations': math.prod(map(len,family[key])), 'frontierCount': len(frontier),
                'dpSeconds': dp_seconds, 'scoreSecondsIncludingChecks': time.monotonic()-start-dp_seconds,
                'referenceResults': scored, 'bestNineGainPct': best_nine, 'objectiveExtremes': objectives.min(axis=0).tolist(),
                'independentHVCheckMaxError': max_hv_error, 'qaWitnessIndices': sample}
            print('POOL_CLOSURE', stem, family['family'], mode, len(frontier), scored['1.5']['bestSingleGainPct'], flush=True)
        full = per_mode['FULL']['referenceResults']['1.5']['bestSingleGainPct']
        finite = per_mode['FINITE']['referenceResults']['1.5']['bestSingleGainPct']
        assert full + 1e-8 >= finite
        summaries.append({'family': family['family'], 'modes': per_mode,
            'finiteMaterialNinePolicyOmission': finite >= .1 and per_mode['FINITE']['bestNineGainPct'] < finite/2,
            'fullMaterialNinePolicyOmission': full >= .1 and per_mode['FULL']['bestNineGainPct'] < full/2})
    qa = check_assemblies(root, cp, stem, list(witnesses.values()))
    result = {'stem': stem, 'phase': PHASE, 'paidSourceFE': phase['paidFE'], 'families': summaries,
        'finiteMaterialFamilies': sum(s['finiteMaterialNinePolicyOmission'] for s in summaries),
        'fullMaterialFamilies': sum(s['fullMaterialNinePolicyOmission'] for s in summaries),
        'offlineFullDecoderQA': qa['passedOfflineDecodes'], 'maxAbsoluteObjectiveError': qa['maxAbsoluteObjectiveError']}
    result['worthPairedSupplyDiagnostic'] = result['fullMaterialFamilies'] >= 2
    write_once(folder/'analysis.json', result)
    return result


def main():
    root = ROOT/'runs'/datetime.now().strftime('pool-closure-oracle-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('POOL_CLOSURE_ROOT', root, flush=True)
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            protocol = read(SOURCE/'protocol.json')
            write_once(root/'protocol.json', {'instances': protocol['instances'], 'source': str(SOURCE), 'seed': SEED,
                'phase': PHASE, 'searchFE': 0,
                'question': 'Do nine fixed cap/eta policies cover material single-candidate capacity of the same paid factory records?',
                'scope': 'All4 families, only pre-fixed G2_CENTER_ENTRY common paid archive. Finite8 and complete offered '
                         'paid nondominated objective envelopes separately. No new records, parent windows, cap/eta scans or selector.',
                'exactClosure': 'Convert every stored double to common power-of-two integers. Exhaustive Pareto dynamic '
                                'programming under max(C),sum(E),sum(W), with exact integer dominance and a record-index witness per state.',
                'metrics': 'Maximum SINGLE-candidate HV increment over the common archive; secondary references1.25/2.0. '
                          'No aggregate free injection of the whole oracle front, no claim of uniform selection performance.',
                'qa': 'Exhaustive small Cartesian fixtures vsDP; independent existing HV comparison on deterministic '
                      'front samples and every best witness, full decoding all distinct samples. Objective aggregation '
                      'roundoff reported separately; full QA tolerance inherits existing1e-9 relative contract.',
                'gate': 'Both instances >=2/4 FULL families have best single gain>=0.1% of archiveHV and nine-policy '
                        'best gains <half that. Finite reported separately. A pass only permits a new matched '
                        'SPECIAL/UNIFORM supply diagnostic, never authorizes an online selector or repairs old gates.',
                'interpretation': 'This can correct the scope of prior nine-policy negatives, not turn them into positives. '
                                  'Only SPECIAL source data available, so no independent four-role supply or novelty claim.',
                'limits': 'Offline capacity oracle may be expensive and exploit already-paid objective labels. Not an '
                          'implementable free selector, online FE result, same-time superiority, or a new algorithm.'})
            source_dir=root/'source';source_dir.mkdir()
            shutil.copy2(Path(__file__),source_dir)
            shutil.copytree(ROOT/'research/composition_oracle',source_dir/'composition_oracle',ignore=shutil.ignore_patterns('__pycache__'))
            write_once(root/'engineering.json', {'frontierFixtures':check_frontier(),'volumeFixtures':check_volume(hypervolume)})
            cp=(SOURCE/'classpath.txt').read_text(encoding='utf-8-sig').strip()
            (root/'classpath.txt').write_text(cp,encoding='utf-8')
            execute(['java','-cp',cp,'research.dynamic.ClassResolutionProbe',
                     'org.uma.jmetal.util.research.model.DynamicDecoder','research.dynamic.PoolAssemblyCheckRun'],root/'qa-class-identity.json')
            results=[analyze_instance(root,s,cp) for s in protocol['instances'] if s['stem'] in STEMS]
            result={'instances':results,'searchFE':0,'offlineFullDecoderQA':sum(r['offlineFullDecoderQA'] for r in results),
                    'worthPairedSupplyDiagnostic':all(r['worthPairedSupplyDiagnostic'] for r in results)}
            write_once(root/'analysis.json',result)
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','error':str(exc),'searchFE':0});raise
    write_once(root/'status.json',{'status':'COMPLETE','searchFE':0,'offlineFullDecoderQA':result['offlineFullDecoderQA'],
                                 'worthPairedSupplyDiagnostic':result['worthPairedSupplyDiagnostic']})
    print('POOL_CLOSURE_COMPLETE', {r['stem']:{'finite':r['finiteMaterialFamilies'],'full':r['fullMaterialFamilies']}
                                    for r in results},flush=True)


if __name__=='__main__':
    main()
