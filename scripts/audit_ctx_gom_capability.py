"""Zero-search independent-axis HV, scalar IGD+, exact covered counts and source/fee audit."""
from pathlib import Path
import sys

import numpy as np

from run_long_budget_bridge import ROOT, read, rows, write_once, nondominated
from qpa_capability_analysis import endpoint
from research.expansion_audit.metrics import grid_hv
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from paired_survival_bench import class_hashes


def direct_igd(front,reference):
    return float(np.mean([np.min(np.linalg.norm(np.maximum(front-p,0.),axis=1)) for p in reference]))


def direct_c(first,second):
    a,b = np.unique(first,axis=0),np.unique(second,axis=0)
    covered = sum(any(all(x<=y for x,y in zip(p,q)) for p in a) for q in b)
    return covered,len(b)


def phase_audit(root,plan,result):
    checks = []
    for spec,item in zip(plan['instances'],result['instances']):
        stem,norm = spec['stem'],spec['normalization']; phase = result['phase']
        limit = spec['time_seconds'] if phase=='TIME' else plan['fixedFE']
        fronts = {(seed,arm):np.asarray(endpoint(root/stem/str(seed)/(phase+'-'+arm),phase,limit)['front'],float)
                  for seed in plan['seeds'] for arm in plan['arms']}
        normal = {k:(p-norm['lower'])/norm['scale'] for k,p in fronts.items()}
        reference = nondominated(np.vstack(list(normal.values())))
        assert len(reference) == item['referenceSize']
        errors = []
        for record in item['observations']:
            key = record['seed'],record['arm']; front = normal[key]
            for r in (1.25,1.5,2.):
                error = abs(grid_hv(front,r)-record['HV'][str(r)])
                assert error < 2e-10; errors.append(error)
            error = abs(direct_igd(front,reference)-record['IGDplus']); assert error < 2e-12
        for comparison in item['comparisons']:
            for pair in comparison['pairs']:
                a,b = fronts[pair['seed'],comparison['A']],fronts[pair['seed'],comparison['B']]
                ab,nb = direct_c(a,b); ba,na = direct_c(b,a); c = pair['coverage']
                assert (ab,nb,ba,na) == (c['coveredB'],c['totalB'],c['coveredA'],c['totalA'])
                assert c['C_A_B'] == ab/nb and c['C_B_A'] == ba/na
        competitive = all(p['registeredAssessment']['pass_'] for p in item['comparisons'] if p['B'] not in plan['mechanismControls'])
        mechanism = all(p['registeredAssessment']['pass_'] for p in item['comparisons'] if p['B'] in plan['mechanismControls'])
        assert competitive == item['competitivePass'] and mechanism == item['independentRoleAndSharingPass']
        checks.append(dict(instance=stem,fronts=len(fronts),referenceSize=len(reference),maximumIndependentHVError=max(errors),
            allScalarIGDAndCoveredCountsAgree=True,competitivePass=competitive,independentRoleAndSharingPass=mechanism))
    assert result['competitivePass'] == all(c['competitivePass'] for c in checks)
    return dict(phase=result['phase'],checks=checks)


def audit(root):
    plan = read(root/'protocol.json'); result = read(root/'analysis.json')
    for name,sha in read(root/'source-hashes.json').items(): assert digest(root/name) == sha
    classes = read(root/'class-hashes.json')
    assert class_hashes(root/'kernel-classes') == classes['kernel'] and class_hashes(root/'override-classes') == classes['overrides']
    for spec in plan['instances']:
        stem = spec['stem']
        for name,sha in read(root/stem/'input-hashes.json').items(): assert digest(root/stem/'inputs'/name) == sha
    assert protected() == read(root/'protected-before.json')
    fees = dict(attempted=0,successful=0,failed=0,receipts=0)
    for path in root.rglob('run-receipt.jsonl'):
        receipt, = rows(path); fees['receipts'] += 1
        for key in ('attempted','successful','failed'): fees[key] += receipt[key]
        assert receipt['attempted'] == receipt['successful']+receipt['failed'] and receipt['error'] is None
        assert receipt['successful'] <= receipt['decoder']['dynamic.evaluations'] <= receipt['attempted']
        assert read(path.parent/'checkpoint-validation.json')['status'] == 'passed'
        assert (path.parent/'identity-verified.json').exists()
    assert fees['attempted'] == result['attemptedFE'] and fees['successful'] == result['successfulFE'] and fees['failed'] == result['failedFE']
    science = [p for p in root.glob('*/*/FE500K-*/run-receipt.jsonl')]; assert len(science) == 40
    assert sum(rows(p)[0]['successful'] for p in science) == plan['plannedFixedScienceFE']
    phases = [phase_audit(root,plan,r) for r in result['phases']]
    write_once(root/'independent-final-audit.json',dict(passed=True,phases=phases,fees=fees,
        originalSourcesAndInputsRetained=True,defaultProtectedSourcesUnchanged=True,newSearchFE=0,newDecoderCalls=0,goalAchieved=False))
    print('CTX_CAPABILITY_FINAL_AUDIT_PASSED',fees)


if __name__=='__main__': audit(Path(sys.argv[1]).resolve())
