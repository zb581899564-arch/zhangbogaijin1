"""Independent indicators and accounting for the fixed initial-coordinate causal test."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from pathlib import Path
import shutil
import sys

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once
from run_qpa_complete_engineering import protected
from paired_survival_bench import class_hashes
from frozen_classpath_identity import verify_capture, resolve_class
from research.semantic_repair.evidence import digest
from ctx_gom_capability_support import checked, counts
from qpa_capability_analysis import endpoint
from qpa_initial_view_support import check_initial, source_folder, original_bridge, pa_bridge
from audit_qpa_completed_donor_pilot import scalar_metrics, criterion, flags
from audit_pa_qpa_complement_capacity import independent_nd, coverage


def check_command(folder, source, plan, arm):
    command, old = read(folder/'command.json'), read(source/'command.json')
    vm, settings = flags(command); oldvm, oldsettings = flags(old)
    assert vm == oldvm
    assert settings == dict(oldsettings, **{'research.initialView.mode': arm.split('_')[1],
                                           'research.initialView.seed': str(plan['privateInterleavingSeed'])})
    at = command.index('research.dynamic.QpaInitialViewRun')
    previous = old.index('research.dynamic.QpaFeedbackCapabilityRun')
    assert command[at+5:] == old[previous+5:]
    assert Path(command[at+4]) == folder
    stem = folder.parents[1].name
    for offset, name in enumerate((stem+'.txt', 'RECONSTRUCTED-setup.txt', 'fatigue-input.txt'), 1):
        assert Path(command[at+offset]) == folder.parents[1]/'inputs'/name
    return command[command.index('-cp')+1]


def instance_audit(root, item, plan):
    stem, norm = item['instance'], item['normalization']
    fronts, values, scalar_checks = {}, {}, []
    for observation in item['observations']:
        seed, arm = observation['seed'], observation['arm']
        folder = root/stem/str(seed)/('FE100K-'+arm)
        source = source_folder(plan, stem, seed, arm)
        cp = check_command(folder, source, plan, arm)
        receipt = checked(folder, cp, plan['fixedFE'], float('inf'))
        assert receipt['seed'] == seed and receipt['arm'] == ('QPA_DIRECT' if arm.startswith('Q_') else 'PA_JOINT')
        assert receipt['successful'] == receipt['attempted'] == receipt['decoder']['dynamic.evaluations'] == plan['fixedFE']
        assert receipt['paidSHA256'] and observation['successfulFE'] == receipt['successful']
        assert observation['searchSeconds'] == receipt['searchSeconds']
        helper = read(folder/'initial-view-identity.json')
        verify_capture(helper['identity'], cp)
        assert helper['error'] is None and helper['suffixPaidRows'] == plan['fixedFE']-100
        assert helper['intervention'] == dict(mode=arm.split('_')[1], transforms=100, paid=plan['fixedFE'],
                                             privateSeed=plan['privateInterleavingSeed'], mainRNGCalls=0)
        check_initial(folder, source, arm.split('_')[1], plan['privateInterleavingSeed'])
        actual = independent_nd(endpoint(folder, 'FE100K', plan['fixedFE'])['front'])
        assert np.array_equal(actual, np.array(observation['metrics']['front']))
        fronts[seed, arm], values[seed, arm] = actual, observation['metrics']
    assert set(fronts) == {(s, a) for s in plan['seeds'] for a in plan['arms']}
    for seed in plan['seeds']:
        for arm in ('Q_ORIGINAL', 'P_ORIGINAL'):
            original_bridge(root, plan, stem, seed, arm)
        pa_bridge(root, plan, stem, seed)
    reference = independent_nd(np.vstack([(f-norm['lower'])/norm['scale'] for f in fronts.values()]))
    assert np.array_equal(reference, np.array(item['reference']))
    for key, front in fronts.items():
        hv, igd = scalar_metrics(front, reference, norm)
        error = max(abs(hv[r]-values[key]['HV'][r]) for r in hv)
        igd_error = abs(igd-values[key]['IGDplus'])
        assert error < 2e-11 and igd_error < 2e-12
        scalar_checks.append(dict(seed=key[0], arm=key[1], maximumHVError=error, IGDplusError=igd_error))
    for row in item['comparisons']:
        assert row['A'] == plan['primary'] and row['kind'] == plan['criterionByControl'][row['B']]
        effects = {r: [] for r in ('1.25', '1.5', '2.0')}; igds, deltas = [], []
        for pair in row['pairs']:
            seed = pair['seed']; a, b = fronts[seed, row['A']], fronts[seed, row['B']]
            cov = pair['coverage']
            assert cov['coveredB'] == coverage(a, b) and cov['coveredA'] == coverage(b, a)
            assert cov['totalA'] == len(a) and cov['totalB'] == len(b)
            assert cov['C_A_B'] == cov['coveredB']/len(b) and cov['C_B_A'] == cov['coveredA']/len(a)
            assert cov['sharedObjectiveVectors'] == len(set(map(tuple, a)) & set(map(tuple, b)))
            av, bv = values[seed, row['A']], values[seed, row['B']]
            for r in effects:
                value = 100*(av['HV'][r]/bv['HV'][r]-1)
                assert value == pair['HVEffectPct'][r]; effects[r].append(value)
            den = av['IGDplus']+bv['IGDplus']
            igd = 200*(av['IGDplus']-bv['IGDplus'])/den if den else 0.
            delta = cov['C_A_B']-cov['C_B_A']
            assert igd == pair['IGDplusSymmetricWorseningPct'] and delta == pair['Cdelta']
            igds.append(igd); deltas.append(delta)
        assert row['medianHVEffectPct'] == {r: float(np.median(v)) for r, v in effects.items()}
        assert row['medianIGDplusSymmetricWorseningPct'] == float(np.median(igds))
        assert row['medianCdelta'] == float(np.median(deltas))
        checks = criterion(row, plan['criteria'][row['kind']])
        assert row['registeredAssessment'] == dict(checks=checks, pass_=all(checks.values()))
    assert item['pass_'] == all(r['registeredAssessment']['pass_'] for r in item['comparisons'])
    return dict(instance=stem, metrics=scalar_checks, pass_=item['pass_'], allNativeAndPAInvarianceChecksPassed=True)


def audit(root):
    protocol = read(root/'protocol.json'); plan = protocol['contract']
    assert read(root/'status.json')['status'] == 'COMPLETE' and read(root/'bridge-acceptance.json')['passed']
    assert digest(ROOT/'research/gomea_reference_audit/QPA_INITIAL_NEUTRAL_CAUSAL_V1.json') == protocol['contractSHA256']
    assert protected() == protocol['protectedBefore']
    assert class_hashes(root/'classes') == read(root/'class-hashes.json')
    for name, sha in read(root/'source-hashes.json').items():
        assert digest(root/'source'/name) == sha
    for change in read(root/'build-changes.json'):
        assert digest(Path(change['source'])) == change['sha256']
    for name, expected in read(root/'inherited-identities.json').items():
        assert resolve_class((root/'classpath.txt').read_text().strip(), name) == expected
    for spec in plan['instances']:
        for name, sha in read(root/spec['stem']/'input-hashes.json').items():
            assert digest(root/spec['stem']/'inputs'/name) == sha
            assert digest(Path(plan['sourcePilot'])/spec['stem']/'inputs'/name) == sha
    result = read(root/'analysis.json')
    instances = [instance_audit(root, item, plan) for item in result['instances']]
    costs = counts(root)
    assert costs['runs'] == 24 and costs['attemptedFE'] == costs['successfulFE'] == plan['plannedScientificFE']
    assert costs['failedFE'] == costs['timeInterruptedAttempts'] == 0
    assert result['pass_'] == all(i['pass_'] for i in instances)
    for key, value in costs.items():
        assert result[key] == value
    record = dict(passed=True, instances=instances, **costs, nativeWholeTraceAndPAViewInvariance=True,
        independentlyVerifiedHVIGDplusBidirectionalCoverageAndCriteria=True,
        initialPhysicalAndObjectiveBitsEqual=True, newSearchFE=0, newDecoderCalls=0, goalAchieved=False)
    write_once(root/'independent-final-audit.json', record)
    folder = root/'independent-audit-source'; folder.mkdir()
    shutil.copy2(Path(__file__), folder)
    print('QPA_INITIAL_NEUTRAL_CAUSAL_INDEPENDENT_AUDIT_PASS', costs, flush=True)


if __name__ == '__main__':
    audit(Path(sys.argv[1]).resolve())
