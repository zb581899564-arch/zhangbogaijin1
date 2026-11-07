"""One guarded JVM and independent trace acceptance; no performance selection."""
from run_long_budget_bridge import rows, read, write_once, execute
from pa_capability_support import command, initial_key
from run_snapshot_anchor_audit import override
from frozen_classpath_identity import verify_capture
from ctx_gom_replay import replay

MODES = {'SHARE_CTX_GOM': 'SHARE_JOB_ALIGNED', 'SYNC_CTX_GOM': 'SYNC_JOB_ALIGNED',
         'UNIFORM_CTX_GOM': 'SHARE_JOB_ALIGNED_UNIFORM', 'NSGA_CTX_GOM': 'NSGA2_4V'}


def fees(root):
    result = dict(successfulFE=0, attemptedFE=0, failedFE=0, timeInterruptedAttempts=0,
                  paidFullTimelineQA=0, viewFullTimelineQA=0, checkpointOfflineQA=0, receiptCount=0)
    for path in root.glob('*/*/receipt.jsonl'):
        record, = rows(path); result['receiptCount'] += 1
        for target, key in (('successfulFE','successful'), ('attemptedFE','attempted'), ('failedFE','failed'),
                            ('timeInterruptedAttempts','timeInterruptedAttempts'), ('paidFullTimelineQA','paidFullTimelineQA'),
                            ('viewFullTimelineQA','viewFullTimelineQA')):
            result[target] += record[key]
        validation = path.parent/'checkpoint-validation.json'
        if validation.exists():
            result['checkpointOfflineQA'] += read(validation)['uniqueOfflineDecodes']
    return result


def run_one(root, cp, stem, variant, label, limit, seed, enabled=True, seconds=float('inf'), synthetic='NONE', prefixes=()):
    protocol = read(root/'protocol.json')
    total_before = protocol['previousRetainedAttemptedFE'] + fees(root)['attemptedFE']
    assert total_before + limit <= protocol['prospectiveContract']['maximumActualAttemptedFE'], 'Combined engineering attempt cap would be exceeded'
    out = root/stem/label; out.mkdir(parents=True)
    control = 'NSGA2_DEEP' if variant == 'NSGA_CTX_GOM' else 'FULL_SHARED_DEEP'
    cmd = command(root,cp,stem,control,label,limit,seed,seconds,audit=True)
    entry = cmd.index('research.dynamic.PaCapabilityRun'); cmd[entry] = 'research.dynamic.GomEngineeringRun'
    cmd[entry+5] = MODES[variant]; cmd.append(synthetic)
    for key, value in {'research.ctxGom.enabled': str(enabled).lower(),
                       'research.ctxGom.prefixFE': ','.join(map(str,prefixes))}.items():
        cmd = override(cmd,key,value)
    write_once(out/'command.json',cmd)
    print('CTX_GOM_RUN',stem,label,limit,seconds,synthetic,flush=True)
    execute(cmd,out/'run.log',timeout=900)
    receipt, = rows(out/'receipt.jsonl')
    capture, = rows(out/'loaded-identity.jsonl')
    write_once(out/'identity-verified.json',verify_capture(capture,cp))
    result = replay(out); write_once(out/'independent-replay.json',result)
    assert receipt['enabled'] == enabled
    search = receipt['search']
    assert sum(search.get(k+'.evaluations',0) for k in ('initialization','global','inter','intra','jointLocal')) == receipt['successful']
    if synthetic != 'NONE' or seconds != float('inf'):
        assert receipt['stopReason'] == 'TIME_LIMIT' and receipt['successful'] < limit
        if synthetic != 'NONE':
            assert receipt['failed'] == 0
        else:
            assert receipt['searchSecondsIncludingEngineeringQA'] >= seconds
    else:
        assert receipt['stopReason'] == 'FE_LIMIT' and receipt['successful'] == limit and receipt['failed'] == 0
    if enabled:
        assert search.get('inter.evaluations',0) == search.get('intra.evaluations',0) == 0
    validation = read(out/'checkpoint-validation.json')
    assert validation['status'] == 'passed' and validation['allReachedPointsCovered']
    for point in rows(out/'checkpoint-solutions.jsonl'):
        assert point['bornFE'] <= point['checkpointFE'] and point['bornSeconds'] <= point['checkpointElapsedSeconds']
        if point['checkpointKind'] == 'TIME':
            assert point['bornSeconds'] <= point['checkpoint']
    print('CTX_GOM_REPLAY_PASSED',stem,label,receipt['successful'],result['localProposalsValidated'],flush=True)
    return out,receipt,result


def parity(root, legacy, modified, stem, seed):
    result = []
    for variant in ('SHARE_CTX_GOM','NSGA_CTX_GOM'):
        old, old_r, _ = run_one(root,legacy,stem,variant,'OFF-OLD-'+variant,5102,seed,enabled=False)
        new, new_r, _ = run_one(root,modified,stem,variant,'OFF-NEW-'+variant,5102,seed,enabled=False)
        assert old_r['paidSHA256'] == new_r['paidSHA256']
        assert initial_key(old) == initial_key(new)
        assert old_r['lastValidFront'] == new_r['lastValidFront']
        assert old_r['internalArchive'] == new_r['internalArchive']
        assert old_r['search'] == new_r['search']
        assert old_r['gom']['localEvaluations'] == new_r['gom']['localEvaluations'] == 0
        result.append(dict(variant=variant, successfulFE=5102, exactPaidSHA256=old_r['paidSHA256'],
                           initialAndFinalFrontEqual=True, originalSearchDiagnosticsEqual=True))
    return result
