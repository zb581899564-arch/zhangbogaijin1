"""Prospective complete direct-joint qualification; protect defaults and do not tune stopped variants."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock
from run_qpa_complete_engineering import protected
from qpa_capability_support import ENGINE, build, engineering, run_case
from qpa_capability_analysis import analyze
from pa_capability_support import initial_key
from research.semantic_repair.evidence import digest

ARMS = ['QPA_DIRECT', 'PA_JOINT', 'PA_EQUAL', 'NSGA2_DEEP', 'FULL_SHARED_DEEP', 'LI_RECON_DEEP']


def protocol():
    previous = read(ROOT/'runs/pa-base-qualification-20261105-180835-751659/protocol.json')
    return {'version': 'QPA_COMPLETE_ORDINARY_CAPABILITY-v1', 'registered': '2026-11-06',
            'engineeringAccepted': str(ENGINE), 'instances': previous['instances'], 'seeds': [14730003, 14730037],
            'arms': ARMS, 'primary': 'QPA_DIRECT only; do not select the better control as a replacement primary',
            'initialization': 'Same100 fresh canonical fourvectors/objectives in every arm, paired per seed; all attempts charged',
            'core': 'Accepted QPA canonical fixed100 noFI snapshot unchanged; synchronous parent donors, filtered FOS, both joint phases charged',
            'notSourceExact': 'Canonical average linkage, fixed100 and joint FMW extend the native permutation preset; no QGS/shared mechanism in ordinary QPA',
            'equalityControl': 'PA_EQUAL changes only boundary strict< to non-worse<=; CENTER/model/representation/donors/reencoding untouched. Both PA arms use same isolated switch class; off must match frozenPA',
            'engineeringFE': 236600, 'engineering': 'QPA light allpaidSHA/finalfront equals both full two-gen native runs; oldPA switch-off exact frozen two-gen paidSHA/finalfront; allinitials identical; equal2gens legal',
            'fixedFE': 500000, 'plannedFixedScienceFE': 12000000, 'plannedEngineeringPlusFixedFE': 12236600,
            'timeSafetyFE': 5000000, 'phases': ['FE500K all24 runs', 'TIME all24 runs only if fixedFE joint gate passes bothinstances vsall5controls'],
            'sameTime': 'Prior registered4s/5s per instance; new isolated sequential JVMs, same heap and common observer/archives, no cross-resource timing comparison',
            'indicators': 'HV1.5 plus1.25/2 sensitivity, IGD+same NDunion of all6arms/all2seeds at that phase endpoint, exactdeduplicated bidirectional weakC includingequal. Preserve rawvalues/covered counts, no voting',
            'gate': 'For BOTHinstances vsEACHof5controls: medianHV1.5>=1%, medianHV1.25/2>=0; medianIGD+symmetricworsening<=0; median(CAB-CBA)>=0. EveryseedHV>=-1%,IGD+worsening<=5%,Cdelta>=-0.02. No majority vote or posthoc relaxation',
            'interpretation': 'Passing qualifies an ordinary search base only. Differences fromPA_EQUAL still combine directrepresentation, positionalmodel, donor lifecycle and two-phase program; not proof of a single cause or four-role/shared innovation',
            'order': 'Rotate six-arm order by(instanceIndex+seedIndex); finishall prescribed fixed runs before deciding. No selective seeds/timepoints/arms',
            'scope': 'Two reused development instances/two fresh seeds, exploratory capability; no large matrix, no heldout claim',
            'failure': 'Engineering/evaluation failure stops and preserves spentFE/log/lastfront. Negative or metric-conflicting primary ends this fixedQPA qualification; do not retune masks/roles/phase ratio/FI or extendhorizon to chase it',
            'oldNegativeEvidence': 'All old PA/typed/donor/role/shadow stops remain; current qualification cannot restore them',
            'defaultMainlineChanged': False, 'externalTransfers': False, 'goalAchieved': False}


def counts(root):
    receipts = [p for p in root.rglob('run-receipt.jsonl')]; records = [rows(p)[0] for p in receipts]
    qa = sum(read(p.parent/'checkpoint-validation.json')['uniqueOfflineDecodes'] for p in receipts
             if (p.parent/'checkpoint-validation.json').exists())
    return {'runs': len(records), 'attemptedFE': sum(r['attempted'] for r in records),
            'successfulFE': sum(r['successful'] for r in records), 'failedFE': sum(r['failed'] for r in records),
            'timeInterruptedAttempts': sum(r['timeInterruptedAttempts'] for r in records), 'extraFullDecoderQA': qa}


def phase(root, cp, plan, kind):
    for i, spec in enumerate(plan['instances']):
        stem = spec['stem']
        for k, seed in enumerate(plan['seeds']):
            shift = (i+k) % len(ARMS); order = ARMS[shift:]+ARMS[:shift]; expected = None
            for arm in order:
                limit = plan['fixedFE'] if kind == 'FE500K' else plan['timeSafetyFE']
                seconds = float('inf') if kind == 'FE500K' else spec['time_seconds']
                out, _ = run_case(root, cp, stem, arm, f'{seed}/{kind}-{arm}', limit, seed, seconds)
                initial = initial_key(out); assert len(initial) == 100
                if expected is None:
                    expected = initial
                else:
                    assert initial == expected
                if kind == 'TIME':
                    assert initial == initial_key(root/stem/str(seed)/('FE500K-'+arm))
    result = analyze(root, plan, kind); print('QPA_CAPABILITY_GATE', kind, result['pass'], flush=True)
    return result


def main():
    with controller_lock(ROOT/'research/night_research', 'dispatch.lock'):
        assert read(ENGINE/'status.json')['engineeringPass']
        root = ROOT/'runs'/datetime.now().strftime('qpa-capability-pilot-%Y%m%d-%H%M%S-%f'); root.mkdir()
        print('QPA_CAPABILITY_ROOT', root, flush=True); plan = protocol(); before = protected()
        write_once(root/'protocol.json', plan); write_once(root/'protected-before.json', before)
        try:
            cp = build(root)
            for spec in plan['instances']:
                stem = spec['stem']; shutil.copytree(ENGINE/stem/'inputs', root/stem/'inputs')
                write_once(root/stem/'input-hashes.json', {p.name: digest(p) for p in (root/stem/'inputs').iterdir() if p.is_file()})
            engineering(root, cp, plan)
            assert counts(root)['successfulFE'] == plan['engineeringFE']
            results = [phase(root, cp, plan, 'FE500K')]
            assert counts(root)['successfulFE'] == plan['plannedEngineeringPlusFixedFE'] and counts(root)['failedFE'] == 0
            if results[0]['pass']:
                results.append(phase(root, cp, plan, 'TIME'))
            passed = len(results) == 2 and all(r['pass'] for r in results)
            decision = 'ORDINARY_QPA_CAPABILITY_ONLY_SEPARATE_MECHANISM_PROTOCOL_REQUIRED' if passed else 'STOP_FIXED_DIRECT_QPA_QUALIFICATION'
            assert protected() == before
            for name, sha in read(root/'source-hashes.json').items():
                assert digest(root/'source'/name) == sha
            write_once(root/'analysis.json', {'phases': results, 'decision': decision, **counts(root), 'defaultMainlineChanged': False,
                'oldQualificationsUnchanged': True, 'sameTimeExecuted': len(results) == 2, 'finalAlgorithmProved': False, 'goalAchieved': False})
        except BaseException as error:
            write_once(root/'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), **counts(root), 'goalAchieved': False})
            raise
        write_once(root/'status.json', {'status': 'COMPLETE', 'decision': decision, **counts(root), 'goalAchieved': False})
        print('QPA_CAPABILITY_COMPLETE', decision, counts(root), flush=True)


if __name__ == '__main__':
    main()
