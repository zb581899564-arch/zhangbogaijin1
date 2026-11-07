"""Two existing instances, six initial-view arms; bridge runs count in the 2.4M real-FE cap."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, write_once, controller_lock
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes
from run_qpa_complete_engineering import protected
from ctx_gom_capability_support import counts
from qpa_initial_view_support import build, run_one, original_bridge, pa_bridge
from qpa_initial_view_analysis import analyze

CONTRACT = ROOT/'research/gomea_reference_audit/QPA_INITIAL_NEUTRAL_CAUSAL_V1.json'


def main():
    with controller_lock(ROOT/'research/night_research', 'dispatch.lock'):
        plan = read(CONTRACT)
        for key in ('Geometry', 'Pilot'):
            audit = Path(plan['source'+key])/'independent-final-audit.json'
            assert read(audit)['passed'] and digest(audit) == plan['source'+key+'AuditSHA256']
        root = ROOT/'runs'/datetime.now().strftime('qpa-initial-neutral-causal-%Y%m%d-%H%M%S-%f')
        root.mkdir(); print('QPA_INITIAL_NEUTRAL_CAUSAL_ROOT', root, flush=True)
        before = protected()
        write_once(root/'protocol.json', dict(contract=plan, contractSHA256=digest(CONTRACT), protectedBefore=before))
        completed = set(); bridges = []
        try:
            cp = build(root, plan)
            for spec in plan['instances']:
                stem = spec['stem']
                shutil.copytree(Path(plan['sourcePilot'])/stem/'inputs', root/stem/'inputs')
                write_once(root/stem/'input-hashes.json', {p.name: digest(p) for p in (root/stem/'inputs').iterdir()})
            seed = plan['seeds'][0]
            for spec in plan['instances']:
                stem = spec['stem']
                for arm in ('Q_ORIGINAL', 'P_ORIGINAL', 'P_CONCAT', 'P_RANDOM'):
                    run_one(root, cp, plan, stem, seed, arm); completed.add((stem, seed, arm))
                    if arm.endswith('ORIGINAL'):
                        bridges.append(original_bridge(root, plan, stem, seed, arm))
                bridges.append(pa_bridge(root, plan, stem, seed))
            write_once(root/'bridge-acceptance.json', dict(passed=True, checks=bridges, actualFE=800000, allRunsReusedAsScience=True))
            for index, spec in enumerate(plan['instances']):
                stem = spec['stem']
                for seed_index, seed in enumerate(plan['seeds']):
                    shift = (index+seed_index) % len(plan['arms'])
                    order = plan['arms'][shift:]+plan['arms'][:shift]
                    for arm in order:
                        if (stem, seed, arm) not in completed:
                            run_one(root, cp, plan, stem, seed, arm); completed.add((stem, seed, arm))
                    if seed != plan['seeds'][0]:
                        for arm in ('Q_ORIGINAL', 'P_ORIGINAL'):
                            bridges.append(original_bridge(root, plan, stem, seed, arm))
                        bridges.append(pa_bridge(root, plan, stem, seed))
            assert len(completed) == 24 and protected() == before
            assert class_hashes(root/'classes') == read(root/'class-hashes.json')
            costs = counts(root)
            assert costs['successfulFE'] == costs['attemptedFE'] == plan['plannedScientificFE']
            assert costs['failedFE'] == costs['timeInterruptedAttempts'] == 0
            write_once(root/'all-invariance-checks.json', dict(passed=True, checks=bridges))
            result = analyze(root, plan, costs)
        except BaseException as error:
            write_once(root/'status.json', dict(status='INCOMPLETE_RETAINED', error=repr(error), **counts(root), goalAchieved=False))
            raise
        write_once(root/'status.json', dict(status='COMPLETE', decision=result['decision'], **costs, goalAchieved=False))
        print('INITIAL_NEUTRAL_CAUSAL_COMPLETE', result['decision'], costs, flush=True)
        for item in result['instances']:
            for row in item['comparisons']:
                print(item['instance'], row['B'], row['medianHVEffectPct']['1.5'], row['medianIGDplusSymmetricWorseningPct'], row['medianC_A_B'], row['medianC_B_A'], row['registeredAssessment'], flush=True)


if __name__ == '__main__':
    main()
