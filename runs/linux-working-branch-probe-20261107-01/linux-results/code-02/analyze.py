"""Offline common-reference evaluation; no search or endpoint-selection feedback."""
from collections import Counter
import numpy as np
from audit_inputs import weak
from indicators import fixtures, independent_module, measured, pair
from common import *


def front_tables(root, paid, ends, archives, reference, independent):
    fronts, values, table, extrema = {}, {}, [], []
    for context, base in archives.items():
        for arm in ARMS:
            subsets = {'ALL_PAID': [r['objectives'] for r in paid if r['context'] == context and r['arm'] == arm],
                       'COMMIT_ENDPOINTS': [r['objectives'] for r in ends if r['context'] == context and r['arm'] == arm and r['wouldCommit']]}
            for kind, subset in subsets.items():
                key = kind, context, arm; front = nd(base+subset); fronts[key] = front
                values[key] = measured(front, reference, independent)
                table.append(dict(kind=kind, context=context, arm=arm, searchFE=128, **values[key]))
                extrema.append(dict(kind=kind, context=context, arm=arm,
                    vectors={name: front[int(np.argmin(front[:, k]))].tolist() for k, name in enumerate(('Cmax', 'TEC', 'TWC'))}))
        base_values = measured(base, reference, independent)
        table.append(dict(kind='A0', context=context, arm='A0', searchFE=0, **base_values))
    csv_write(root/'analysis/metrics.csv', table)
    write(root/'analysis/extreme-vectors.json', extrema)
    write(root/'analysis/fronts.json', [dict(kind=k[0], context=k[1], arm=k[2], front=v.tolist()) for k, v in fronts.items()])
    return fronts, values


def programs(root, paid, ends, archives):
    records = []
    for end in ends:
        subset = [r for r in paid if (r['case'], r['arm'], r['branch']) == (end['case'], end['arm'], end['branch'])]
        base = archives[end['context']]
        fresh = lambda r: not any(weak(a, r['objectives']) for a in base)
        records.append({**{k: end[k] for k in ('case', 'context', 'role', 'arm', 'branch', 'seedTag', 'programFE',
            'seedNumber', 'lastAcceptedNumber', 'lastGeneratedNumber', 'wouldCommit', 'freshToA0', 'fromSuccessor')},
            'acceptedSuccessors': sum(r['accepted'] is True for r in subset),
            'freshPaidPoints': sum(fresh(r) for r in subset),
            'freshAcceptedPoints': sum(fresh(r) and r['accepted'] is True for r in subset),
            'fallbacks': sum(r['fallback'] for r in subset),
            'terminalCmax': end['objectives'][0], 'terminalTEC': end['objectives'][1], 'terminalTWC': end['objectives'][2]})
    csv_write(root/'analysis/programs.csv', records)
    qualified = [r for r in records if r['arm'] == 'BRANCH' and r['branch'] == 1 and
                 r['wouldCommit'] and r['freshToA0'] and r['fromSuccessor']]
    q = dict(qualifiedCount=len(qualified), caseDenominator=12,
             contexts=sorted({r['context'] for r in qualified}), roles=sorted({r['role'] for r in qualified}), qualified=qualified)
    q['passed'] = q['qualifiedCount'] >= 4 and len(q['contexts']) >= 2 and len(q['roles']) >= 2
    return q, records


def decide(pairs, q):
    primary = [r for r in pairs if r['kind'] == 'ALL_PAID' and r['control'] == 'CURRENT']
    secondary = [r for r in pairs if r['kind'] == 'ALL_PAID' and r['control'] != 'CURRENT']
    quality = (sum(r['signal'] for r in primary) >= 2 and not any(r['majorReverse'] for r in primary+secondary)
               and not any(r['signal'] and r['HVreferenceFlip'] for r in primary))
    return dict(qualityGate=quality, primarySignalContexts=[r['context'] for r in primary if r['signal']],
                majorReversals=[r for r in primary+secondary if r['majorReverse']],
                QendpointGate=q, decision='RETAIN_CONDITIONAL_BRANCH' if quality and q['passed'] else 'STOP_FIXED_BRANCH',
                noBudgetOrSeedExtension=True, noProductionChanges=True, noSameTimeOrWholeAlgorithmClaim=True,
                correlatedContextsSameSeed=True)


def main(root):
    assert read(root/'independent-audit.json')['passed']
    start = time.monotonic(); out = root/'analysis'; out.mkdir()
    fixtures(); independent, independent_path = independent_module(); independent.check_metrics()
    paid, ends = rows(root/'science/evaluations.jsonl'), rows(root/'science/endpoints.jsonl')
    archives = read(root/'prepared/archives.json')
    reference = nd([a for base in archives.values() for a in base]+[r['objectives'] for r in paid])
    write(out/'empirical-reference.json', dict(scale=SCALE, reference=reference.tolist(),
          rule='ND(union of three A0 and all 1536 paid objectives); offline only; no search feedback'))
    fronts, values = front_tables(root, paid, ends, archives, reference, independent)
    paired = [pair(kind, context, control, fronts, values) for kind in ('ALL_PAID', 'COMMIT_ENDPOINTS')
              for context in archives for control in ('CURRENT', 'ONE', 'RESTART')]
    csv_write(out/'paired.csv', paired)
    q, program_rows = programs(root, paid, ends, archives); decision = decide(paired, q)
    write(out/'decision.json', decision)
    cost = {p: read(root/p/'process.json') for p in ('build-02/compile', 'logic-fixture', 'mix-fixture', 'qa', 'science')}
    write(out/'cost.json', dict(phases=cost, actualFE=1536, actualQA=36,
        fullDecoderNanos=read(root/'science/receipt.json')['decoder']['dynamic.decodeNanos'],
        offlineAnalysisSeconds=time.monotonic()-start, completeSearchIncludesValidationAndIO=True,
        independentAuditWallSeconds=None, auditTimingNote='Standalone audit wall time was not captured; no time comparison.',
        sameTimeClaim=False))
    write(out/'metric-audit.json', dict(passed=True, frontSets=27, independentHVChecks=81,
        independentIGDplusChecks=27, independentIGDChecks=27, mathAndCDirectionFixtures=True,
        independentCoverageCountChecks=36,
        independentCode=str(independent_path), independentCodeSHA256=sha(independent_path), newDecoderCalls=0))
    print(json.dumps(dict(decision=decision['decision'], qualityGate=decision['qualityGate'],
        QendpointCount=q['qualifiedCount'], QendpointContexts=q['contexts'], QendpointRoles=q['roles'],
        primary=[r for r in paired if r['kind'] == 'ALL_PAID' and r['control'] == 'CURRENT']), indent=2), flush=True)


if __name__ == '__main__':
    linux(); main(Path(sys.argv[1]))
