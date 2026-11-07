"""Frozen context-aware complete local integration acceptance. At most650000 attempts, no performance."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from datetime import datetime
import shutil

from run_long_budget_bridge import ROOT, read, write_once, controller_lock
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from pa_capability_support import initial_key
from ctx_gom_build import BASE, CONTRACT, build
from ctx_gom_engineering_cases import MODES, fees, run_one, parity


def main_cases(root, cp, stem, plan):
    n = stem.split('_')[0]; seed = plan['seed']; bounds = plan['mainBounds'][n]
    results = {}; initial = None
    for variant in MODES:
        limit = bounds['matchedNSGA'] if variant == 'NSGA_CTX_GOM' else bounds['sharedOrSyncOrUniform']
        out, receipt, result = run_one(root,cp,stem,variant,variant,limit,seed,prefixes=plan['sharedCutoffs'][n])
        assert result['completePasses'] == 2 and result['completePrograms'] == 200
        assert receipt['gom']['passesStarted'] == 2 and receipt['gom']['stage'] == 'GLOBAL_OR_INITIAL'
        local_per_pass = 100*(2*int(n)-1) if variant == 'NSGA_CTX_GOM' else 80*(2*int(n)-1)+20*(2*int(n)-int(stem.split('_')[1]))
        assert result['localProposalsValidated'] == 2*local_per_pass
        assert receipt['search']['global.evaluations'] == 10001
        assert receipt['search']['initialization.evaluations'] == 100
        generation_key = 'generations' if variant == 'NSGA_CTX_GOM' else 'generations.completed'
        assert receipt['search'][generation_key] >= 2
        assert result['physicalRoleLocalFE'].keys() == {1,2,3,4} or set(map(int,result['physicalRoleLocalFE'])) == {1,2,3,4}
        if initial is None:
            initial = initial_key(out)
        else:
            assert initial == initial_key(out)
        results[variant] = dict(receipt=receipt, independent=result)
    return results


def cutoff_cases(root, cp, stem, plan, main):
    cuts = plan['sharedCutoffs'][stem.split('_')[0]]; prefixes = main['receipt']['paidPrefixes']; result = []
    for limit in cuts:
        out, receipt, check = run_one(root,cp,stem,'SHARE_CTX_GOM','cut'+str(limit),limit,plan['seed'])
        assert receipt['paidSHA256'] == prefixes[str(limit)]
        result.append(dict(limit=limit, paidPrefixIdentical=True, independent=check))
    return result


def clock_cases(root, cp, plan):
    results = []
    for test in plan['syntheticClockTests']:
        stem = test['instance']; limit = plan['mainBounds'][stem.split('_')[0]]['sharedOrSyncOrUniform']
        _, receipt, check = run_one(root,cp,stem,'SHARE_CTX_GOM','synthetic-'+test['phase'],limit,plan['seed'],synthetic=test['phase'])
        assert receipt['successful'] == test['expectedSuccessfulFE']
        assert receipt['gom']['stage'] == ('LEARNING' if test['phase'] == 'MODEL_ROW' else 'LOCAL')
        results.append(dict(instance=stem, synthetic=True, phase=test['phase'], successfulFE=receipt['successful'], independent=check))
    for stem in plan['instances']:
        _, receipt, check = run_one(root,cp,stem,'SHARE_CTX_GOM','real-clock',50000,plan['seed'],seconds=.2)
        results.append(dict(instance=stem, synthetic=False, successfulFE=receipt['successful'],
                            attemptedFE=receipt['attempted'], stopReason=receipt['stopReason'], independent=check))
    return results


def engineering(root, legacy, cp, plan):
    # All four OFF pairs must pass before any ON numerical trial.
    parities = {stem: parity(root,legacy,cp,stem,plan['seed']) for stem in plan['instances']}
    results = []
    for stem in plan['instances']:
        mains = main_cases(root,cp,stem,plan)
        cuts = cutoff_cases(root,cp,stem,plan,mains['SHARE_CTX_GOM'])
        item = dict(instance=stem, offParity=parities[stem], mains=mains, cutoffs=cuts)
        results.append(item); write_once(root/stem/'acceptance.json',item)
    clocks = clock_cases(root,cp,plan)
    actual = fees(root)
    fixed = sum(v['successful'] for item in results for v in [m['receipt'] for m in item['mains'].values()])
    fixed += sum(x['limit'] for item in results for x in item['cutoffs'])+8*5102
    assert fixed == plan['plannedFixedFESuccessful']
    assert actual['receiptCount'] == 40 and actual['attemptedFE'] <= plan['maximumActualAttemptedFE']
    assert actual['successfulFE'] == actual['paidFullTimelineQA']
    return results,clocks,actual


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        root = ROOT/'runs'/datetime.now().strftime('ctx-gom-local-engineering-%Y%m%d-%H%M%S-%f'); root.mkdir()
        print('CTX_GOM_ENGINEERING_ROOT',root,flush=True)
        plan = read(CONTRACT); before = protected()
        write_once(root/'protocol.json',dict(prospectiveContract=plan, contractSHA256=digest(CONTRACT), protectedBefore=before,
            observerCost='Every paid/view timeline QA, archive and evidence included; engineering timings not performance',
            metricsForFuture='HV, IGD+ and bidirectional C jointly; no single-metric pass', externalTransfers=False, goalAchieved=False))
        try:
            for stem in plan['instances']:
                shutil.copytree(BASE/stem/'inputs',root/stem/'inputs')
                write_once(root/stem/'input-hashes.json',{p.name:digest(p) for p in (root/stem/'inputs').iterdir() if p.is_file()})
            legacy, cp = build(root)
            results,clocks,actual = engineering(root,legacy,cp,plan)
            assert protected() == before
            write_once(root/'analysis.json',dict(engineeringPass=True, instances=results, clockChecks=clocks, **actual,
                protectedAfter=protected(), defaultMainlineChanged=False, sameBudgetPerformanceProved=False, goalAchieved=False))
        except BaseException as error:
            write_once(root/'status.json',dict(status='INCOMPLETE_RETAINED', error=repr(error), **fees(root), goalAchieved=False))
            raise
        write_once(root/'status.json',dict(status='COMPLETE', engineeringPass=True, **actual, goalAchieved=False))
        print('CTX_GOM_ENGINEERING_PASSED',root,actual,flush=True)


if __name__ == '__main__':
    main()
