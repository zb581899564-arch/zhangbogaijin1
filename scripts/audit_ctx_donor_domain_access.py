"""Independent membership arrays, three indicators, source identity and fixed stop-rule audit."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from collections import Counter
from pathlib import Path
import json
import shutil
import sys

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once
from run_qpa_complete_engineering import protected
from frozen_classpath_identity import resolve_class
from research.semantic_repair.evidence import digest
from audit_pa_qpa_complement_capacity import independent_nd, coverage
from audit_qpa_completed_donor_pilot import scalar_metrics


def array(points):
    n = len(points[0]['JS'])
    result = np.empty((len(points), n, 3), dtype=np.int64)
    for index, point in enumerate(points):
        assert sorted(point['JS']) == list(range(n))
        result[index, point['JS'], :] = np.array([point[k] for k in ('FA', 'MA', 'WA')]).T
    return result


def support(targets, carriers):
    found = np.zeros(targets.shape[:2], dtype=bool)
    for j in range(targets.shape[1]):
        found[:, j] = np.all(targets[:, j, None, :] == carriers[None, :, j, :], axis=2).any(axis=1)
    return found


def saved_front(folder):
    return [p for p in rows(folder/'checkpoint-solutions.jsonl') if p['checkpointKind'] == 'FE' and p['checkpoint'] == 500000]


def check_metric(value, expected, reference, norm):
    front = independent_nd(expected)
    assert np.array_equal(front, np.array(value['front']))
    hv, igd = scalar_metrics(front, reference, norm)
    assert max(abs(hv[r]-value['HV'][r]) for r in hv) < 2e-11
    assert abs(igd-value['IGDplus']) < 2e-12


def case_audit(case, source):
    stem, seed, norm = case['instance'], case['seed'], case['normalization']
    base = source/stem/str(seed)
    target = saved_front(base/'FE500K-PA_JOINT')
    initial = rows(base/'FE500K-PA_JOINT/initial-population.jsonl')
    shared = saved_front(base/'FE500K-SHARE_CTX_GOM')
    matrix, carrier = array(target), array(initial)
    present, full = support(matrix, carrier[20:]), support(matrix, carrier)
    assert full.all() and case['fullInitialDomainCoversAllRecordedTargets']
    misses = [np.flatnonzero(~p).tolist() for p in present]
    assert misses == case['missingJobsByTarget']
    okay = present.all(axis=1)
    assert int((~okay).sum()) == case['targetRecordedSchedulesNeedingInitialFixedOnlyTuples']
    fraction = float((~okay).mean()); assert fraction == case['targetFraction']
    for column, start in (('initialAllTupleCounts', 0), ('initialFreeTupleCounts', 20)):
        assert case[column] == [len(np.unique(carrier[start:, j, :], axis=0)) for j in range(carrier.shape[1])]
    reference_groups = []
    for other_seed in (14910003, 14910037):
        for arm in ('PA_JOINT', 'SHARE_CTX_GOM'):
            values = np.array([p['objectives'] for p in saved_front(source/stem/str(other_seed)/('FE500K-'+arm))])
            reference_groups.append((values-norm['lower'])/norm['scale'])
    reference = independent_nd(np.vstack(reference_groups))
    assert np.array_equal(reference, np.array(case['reference']))
    target_values = np.array([p['objectives'] for p in target]); shared_values = np.array([p['objectives'] for p in shared])
    check_metric(case['pa'], target_values, reference, norm)
    check_metric(case['empiricalFullUnion'], np.vstack((shared_values, target_values)), reference, norm)
    check_metric(case['empiricalFreeSupportedUnion'], np.vstack((shared_values, target_values[okay])), reference, norm)
    a, b = case['empiricalFullUnion'], case['empiricalFreeSupportedUnion']
    cov = case['fullVsReducedCoverage']
    assert cov['coveredB'] == coverage(np.array(a['front']), np.array(b['front']))
    assert cov['coveredA'] == coverage(np.array(b['front']), np.array(a['front']))
    assert cov['totalA'] == len(a['front']) and cov['totalB'] == len(b['front'])
    assert cov['C_A_B'] == cov['coveredB']/cov['totalB'] and cov['C_B_A'] == cov['coveredA']/cov['totalA']
    lost = {r: 100*(a['HV'][r]-b['HV'][r])/case['pa']['HV'][r] for r in a['HV']}
    assert lost == case['lostHVRelativeToPAHVPercent']
    assert case['preconditionPass'] == (fraction >= .2 and lost['1.5'] >= .1 and min(lost['1.25'], lost['2.0']) > 0.)
    return dict(instance=stem, seed=seed, recordedTargetCount=len(target), preconditionPass=case['preconditionPass'])


def pipeline_audit(item, plan):
    source = Path(plan['source'])/'100_2_3_1/14910003'
    targets = array(saved_front(source/'FE500K-PA_JOINT'))
    initial = array(rows(source/'FE500K-PA_JOINT/initial-population.jsonl'))
    path = Path(plan['pipeline'])/'100_2_3_1'/(item['arm']+'-OBSERVED')/'pipeline.jsonl'
    count = good = 0; ever = [set() for _ in range(targets.shape[1])]
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            event = json.loads(line)
            if event['kind'] != 'population':
                continue
            points = event['points']
            if event['phase'] == 'INITIAL':
                assert np.array_equal(array(points), initial)
                assert [p['family'] for p in points] == [i//5 if i < 20 else -1 for i in range(100)]
            if event['phase'] != 'POST_GLOBAL':
                continue
            families = np.array([p['family'] for p in points])
            assert Counter(families) == Counter({-1: 80, 0: 5, 1: 5, 2: 5, 3: 5})
            carrier = array(points)
            all_ok = support(targets, carrier).all(axis=1)
            free_ok = support(targets, carrier[families == -1]).all(axis=1)
            blocked = np.flatnonzero(all_ok & ~free_ok).tolist()
            expected = item['observations'][count]
            assert expected['cycle'] == event['cycle'] and expected['fe'] == event['fe']
            assert expected['blockedTargetIndices'] == blocked and expected['blockedByDomain'] == len(blocked)
            assert expected['all100Supported'] == int(all_ok.sum()) and expected['free80Supported'] == int(free_ok.sum())
            assert expected['blockedFraction'] == len(blocked)/len(targets)
            good += len(blocked)/len(targets) >= .1; count += 1
            for j in range(targets.shape[1]):
                ever[j].update(map(tuple, carrier[families == -1, j, :]))
    ever_count = sum(all(tuple(row[j]) in ever[j] for j in range(len(ever))) for row in targets)
    assert item['everFreeAlleleSupportedTargets'] == ever_count
    assert item['materiallyBlockedPasses'] == good and item['passes'] == count == 20
    assert item['preconditionPass'] == (good/count >= .2)
    return dict(arm=item['arm'], passes=count, preconditionPass=item['preconditionPass'])


def audit(root):
    protocol = read(root/'protocol.json'); plan = protocol['contract']; result = read(root/'analysis.json')
    assert read(root/'status.json')['status'] == 'COMPLETE'
    assert digest(ROOT/'research/gomea_reference_audit/CTX_DONOR_DOMAIN_ACCESS_V1.json') == protocol['contractSHA256']
    assert protected() == protocol['protectedBefore']
    for path, sha in read(root/'source-identities.json').items():
        assert digest(Path(path)) == sha
    for name, sha in read(root/'source-hashes.json').items():
        assert digest(root/'source'/name) == sha
    cp = (Path(plan['source'])/'classpath.txt').read_text('utf-8-sig').strip()
    for name, expected in read(root/'class-identities.json').items():
        assert resolve_class(cp, name) == expected
    cases = [case_audit(case, Path(plan['source'])) for case in result['cases']]
    pipelines = [pipeline_audit(item, plan) for item in result['pipelines']]
    assert result['initialAccessPreconditionPass'] == all(c['preconditionPass'] for c in cases)
    assert result['observedAccessPreconditionPass'] == all(p['preconditionPass'] for p in pipelines)
    assert result['decision'] == ('STRUCTURAL_CANDIDATE_ONLY_SEPARATE_SAME_ENTRY_CONTRACT_REQUIRED'
        if result['initialAccessPreconditionPass'] and result['observedAccessPreconditionPass'] else 'STOP_INITIAL_FIXED_ALLELE_ACCESS_EXPLANATION')
    for key in ('newSearchFE', 'newObjectiveQueries', 'newDecoderCalls', 'newProposalConstructions'):
        assert result[key] == 0
    record = dict(passed=True, cases=cases, pipelines=pipelines, independentMembershipHVIGDplusAndCoverage=True,
        sameFrozenSourceClassAndInputIdentity=True, newSearchFE=0, newDecoderCalls=0, goalAchieved=False)
    write_once(root/'independent-final-audit.json', record)
    shutil.copy2(Path(__file__), root/'source'/Path(__file__).name)
    print('CTX_DONOR_DOMAIN_ACCESS_INDEPENDENT_AUDIT_PASS', flush=True)


if __name__ == '__main__':
    audit(Path(sys.argv[1]).resolve())
