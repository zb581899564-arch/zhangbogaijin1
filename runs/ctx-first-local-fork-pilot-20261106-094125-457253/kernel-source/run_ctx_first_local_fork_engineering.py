"""At most500k attemptedFE; native-equivalent POST, PRE-first two-cycle traces and cutoff prefixes."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock
from research.semantic_repair.evidence import digest
from run_qpa_complete_engineering import protected
from paired_survival_bench import class_hashes
from ctx_gom_engineering_cases import fees
from ctx_fork_engineering_support import build, run_one, native_folder

CONTRACT = ROOT/'research/gomea_reference_audit/CTX_FIRST_LOCAL_FORK_ENGINEERING_V1.json'
ARMS = ('SHARE_CTX_GOM', 'UNIFORM_CTX_GOM')


def validate_fork(fork, mode, entries):
    assert fork['mode'] == mode and len(fork['entries']) == entries
    assert fork['snapshotChecks'] == (100 if mode == 'PRE_FIRST' and fork['cyclesStarted'] else 0)
    for event in fork['entries']:
        assert event['source'] == ('PRE' if mode == 'PRE_FIRST' and event['cycle'] == 1 else 'POST')
        expected = event['before'] if event['source'] == 'PRE' else event['global']
        for a, b in zip(event['local'], expected):
            assert all(a[k] == b[k] for k in ('JS','FA','MA','WA','objectives','family','direction','lineage','branch'))


def masters(root, cp, plan):
    records, acceptance = {}, []
    for spec in plan['cases']:
        stem = spec['stem']
        for arm in ARMS:
            native, = rows(native_folder(plan, stem, arm)/'receipt.jsonl')
            for mode in ('POST', 'PRE_FIRST'):
                folder, receipt, fork = run_one(root, cp, plan, spec, arm, mode, arm+'-'+mode, spec['masterFE'])
                validate_fork(fork, mode, 2)
                assert receipt['gom']['completePasses'] == 2 and receipt['gom']['completePrograms'] == 200
                assert receipt['search']['global.evaluations'] == 10001
                assert receipt['search']['jointLocal.evaluations'] == 2*spec['passFees']
                assert receipt['paidFullTimelineQA'] == receipt['successful']
                records[stem, arm, mode] = receipt
                if mode == 'POST':
                    assert receipt['paidSHA256'] == native['paidSHA256']
                    assert {tuple(p['objectives']) for p in receipt['lastValidFront']} == {tuple(p['objectives']) for p in native['lastValidFront']}
                else:
                    post = records[stem, arm, 'POST']
                    assert receipt['paidPrefixes']['5100'] == post['paidPrefixes']['5100']
                acceptance.append(dict(instance=stem, arm=arm, mode=mode, exactNativePOSTOrCommon5100Prefix=True,
                                       twoCompletePasses=True, allModelsProposalsAcceptsTimelineQAValidated=True))
    return records, acceptance


def cutoffs(root, cp, plan, records):
    cases = []
    for spec in plan['cases']:
        master = records[spec['stem'], 'SHARE_CTX_GOM', 'PRE_FIRST']
        for limit in spec['cutoffs']:
            folder, receipt, fork = run_one(root, cp, plan, spec, 'SHARE_CTX_GOM', 'PRE_FIRST', 'cut'+str(limit), limit)
            assert receipt['paidSHA256'] == master['paidPrefixes'][str(limit)]
            expected = 0 if limit < 5100 else 1 if limit <= spec['firstLocalEnd'] else 2
            validate_fork(fork, 'PRE_FIRST', expected)
            cases.append(dict(instance=spec['stem'], successfulFE=limit, exactMasterPrefix=True, pendingAndPartialRetained=True))
    return cases


def main():
    with controller_lock(ROOT/'research/night_research','dispatch.lock'):
        plan = read(CONTRACT); before = protected()
        assert read(Path(plan['source'])/'independent-final-audit.json')['passed']
        assert digest(Path(plan['source'])/'independent-final-audit.json') == plan['sourceAuditSHA256']
        root = ROOT/'runs'/datetime.now().strftime('ctx-first-local-fork-engineering-%Y%m%d-%H%M%S-%f')
        root.mkdir(); print('CTX_FIRST_LOCAL_FORK_ENGINEERING_ROOT', root, flush=True)
        write_once(root/'protocol.json', dict(contract=plan, contractSHA256=digest(CONTRACT), protectedBefore=before))
        try:
            cp = build(root,plan)
            for spec in plan['cases']:
                stem = spec['stem']; shutil.copytree(Path(plan['source'])/stem/'inputs',root/stem/'inputs')
                write_once(root/stem/'input-hashes.json',{p.name:digest(p) for p in (root/stem/'inputs').iterdir()})
            records, acceptance = masters(root,cp,plan)
            cut = cutoffs(root,cp,plan,records); actual = fees(root)
            assert actual['attemptedFE'] == actual['successfulFE'] == plan['plannedFixedAttemptedFE'] <= plan['maximumActualAttemptedFE']
            assert actual['failedFE'] == actual['timeInterruptedAttempts'] == 0
            assert protected() == before and class_hashes(root/'classes') == read(root/'class-hashes.json')
            write_once(root/'acceptance.json',dict(passed=True, masters=acceptance, cutoffs=cut, **actual,
                engineeringOnly=True, performanceProved=False, defaultMainlineChanged=False, goalAchieved=False))
        except BaseException as error:
            write_once(root/'status.json',dict(status='INCOMPLETE_RETAINED',error=repr(error),**fees(root),goalAchieved=False));raise
        write_once(root/'status.json',dict(status='COMPLETE',engineeringPass=True,**actual,goalAchieved=False))
        print('CTX_FIRST_LOCAL_FORK_ENGINEERING_PASS',actual,flush=True)


if __name__ == '__main__':
    main()
