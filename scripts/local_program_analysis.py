"""Whole-program attribution. Observational differences never imply counterfactual action value."""
from collections import defaultdict

from run_long_budget_bridge import rows, write_once
from local_program_stream import PaidArchiveStream


def summarize(programs):
    done = [p for p in programs if p['completed']]
    identity = [p for p in done if p['identityShake']]
    gain = sum(p['totalHVgain'] for p in done)
    hidden = sum(p['descentHVgain'] for p in identity)
    positive = sum(p['descentHVgain'] > 1e-10 for p in identity)
    retained = sum(p['accepted'] and p['endpointSingleHVgain'] > 1e-10 for p in identity)
    return {'completePrograms': len(done), 'identityShakePrograms': len(identity),
        'completedProgramFE': sum(p['programFE'] for p in done),
        'identityProgramFE': sum(p['programFE'] for p in identity),
        'allProgramHVgain': gain, 'identityDescentHVgain': hidden,
        'identityDescentShareOfProgramHVgain': hidden / gain if gain > 1e-12 else None,
        'identityPositiveDescentPrograms': positive, 'identityAcceptedWithNewEndpointPrograms': retained,
        'allShakeHVgain': sum(p['shakeHVgain'] for p in done),
        'allDescentHVgain': sum(p['descentHVgain'] for p in done),
        'eligibleForPairedProgramProbe': gain > 1e-12 and hidden >= .05 * gain and positive >= 5 and retained >= 1}


def analyze(out, spec, method, limit):
    programs = rows(out / 'local-programs.jsonl');receipt, = rows(out / 'local-program-receipt.json')
    expected_ids = list(range(1, len(programs) + 1));assert [p['episode'] for p in programs] == expected_ids
    stream = PaidArchiveStream(out, spec['normalization']);analyzed = []
    for p in programs:
        before = stream.advance(p['startFE']);entry_front = stream.front.copy()
        if p['shakeFE'] is None:
            assert p['endFE'] == p['startFE'] and not p['completed'];after_shake = before
        else:
            assert p['shakeFE'] == p['startFE'] + 1
            after_shake = stream.advance(p['shakeFE'], p['episode'], 'SHAKE')
        after = stream.advance(p['endFE'], p['episode'], 'DESCENT')
        if p['identityShake']:
            assert p['entry'] == p['shaken'] and abs(after_shake - before) < 1e-11
        assert after + 1e-11 >= after_shake >= before - 1e-11
        analyzed.append({**p, 'programFE': p['endFE'] - p['startFE'],
            'descentFE': 0 if p['shakeFE'] is None else p['endFE'] - p['shakeFE'],
            'entryArchiveHV': before, 'shakeHVgain': max(0., after_shake - before),
            'descentHVgain': max(0., after - after_shake), 'totalHVgain': max(0., after - before),
            'endpointSingleHVgain': stream.endpoint_gain(entry_front, before, p['improved']) if p['completed'] else None})
    independent = stream.finish(limit)
    assert independent['intraRows'] == receipt['programSuccessfulFE'] == sum(p['programFE'] for p in analyzed)
    assert receipt['programsStarted'] == len(programs) == receipt['programsCompleted'] + receipt['programsPartial']
    assert receipt['activeProgramCleared'] and receipt['programsPartial'] <= 1
    raw, = rows(out / 'run-receipt.jsonl');assert independent['intraRows'] == raw['search']['intra.evaluations']
    groups = defaultdict(list)
    for p in analyzed:
        groups[f'role:{p["preference"]}'].append(p);groups[f'operator:{p["operator"]}'].append(p)
    result = {'stem': spec['stem'], 'method': method, 'summary': summarize(analyzed),
              'strata': {k: summarize(values) for k, values in groups.items()},
              'independentArchiveAndFEAcceptance': independent,
              'scope': 'Observed original trajectories, no matched-parent counterfactual, action selection or timing comparison.'}
    write_once(out / 'program-value-rows.json', analyzed);write_once(out / 'program-value-analysis.json', result)
    print('LOCAL_PROGRAM_ANALYZED', spec['stem'], method, result['summary'], flush=True)
    return result
