"""Common guarded dispatch, light/full and frozen-control identity checks."""
from pathlib import Path

from run_long_budget_bridge import ROOT, read, rows, write_once, execute
from ctx_gom_build import BASE
from pa_capability_support import command, initial_key
from run_snapshot_anchor_audit import override
from frozen_classpath_identity import verify_capture
from qpa_capability_analysis import endpoint

ENGINE = ROOT/'runs/ctx-gom-local-engineering-20261106-050127-857497'
CONTEXT = ['SHARE_CTX_GOM','SYNC_CTX_GOM','UNIFORM_CTX_GOM','NSGA_CTX_GOM']
CONTROLS = ['FULL_SHARED_DEEP','LI_RECON_DEEP','NSGA2_PLAIN','NSGA2_DEEP','PA_JOINT','PA_EQUAL']
ARMS = CONTEXT+CONTROLS


def counts(root):
    paths = list(root.rglob('run-receipt.jsonl')); records = [rows(path)[0] for path in paths]
    return dict(runs=len(records),successfulFE=sum(r['successful'] for r in records),
        attemptedFE=sum(r['attempted'] for r in records),failedFE=sum(r['failed'] for r in records),
        timeInterruptedAttempts=sum(r['timeInterruptedAttempts'] for r in records),
        extraCheckpointQA=sum(read(p.parent/'checkpoint-validation.json')['uniqueOfflineDecodes'] for p in paths
                              if (p.parent/'checkpoint-validation.json').exists()))


def checked(folder,cp,limit,seconds):
    receipt, = rows(folder/'run-receipt.jsonl')
    assert receipt['error'] is None and receipt['constructorsIncludedInClock']
    assert receipt['attempted'] == receipt['successful']+receipt['failed']
    assert receipt['failed'] == receipt['timeInterruptedAttempts'] <= 1
    assert sum(receipt['search'].get(k+'.evaluations',0) for k in ('initialization','global','inter','intra','jointLocal')) == receipt['successful']
    if seconds == float('inf'):
        assert receipt['stopReason'] == 'FE_LIMIT' and receipt['successful'] == limit and receipt['failed'] == 0
    else:
        assert receipt['stopReason'] == 'TIME_LIMIT' and receipt['successful'] < limit and receipt['searchSeconds'] >= seconds
    validation = read(folder/'checkpoint-validation.json')
    assert validation['status'] == 'passed' and validation['allReachedPointsCovered']
    for point in rows(folder/'checkpoint-solutions.jsonl'):
        assert point['bornFE'] <= point['checkpointFE'] and point['bornSeconds'] <= point['checkpointElapsedSeconds']
        if point['checkpointKind'] == 'TIME':
            assert point['bornSeconds'] <= point['checkpoint']
    capture, = rows(folder/'loaded-identity.jsonl'); result = verify_capture(capture,cp)
    if not (folder/'identity-verified.json').exists():
        write_once(folder/'identity-verified.json',result)
    return receipt


def run_case(root,cp,stem,arm,label,limit,seed,seconds=float('inf'),audit=False,old=False):
    template = 'FULL_SHARED_DEEP' if arm in CONTEXT[:3] else 'NSGA2_DEEP' if arm == 'NSGA_CTX_GOM' else 'PA_JOINT' if arm == 'PA_EQUAL' else arm
    cmd = command(root,cp,stem,template,label,limit,seed,seconds,audit)
    entry = cmd.index('research.dynamic.PaCapabilityRun')
    if not old:
        cmd[entry] = 'research.dynamic.GomCapabilityRun'
    elif arm == 'PA_EQUAL':
        cmd[entry] = 'research.dynamic.QpaCapabilityRun'
    cmd[entry+5] = arm
    for key,value in {'research.pa.traceIdentity':'false','research.ctxGom.enabled':'false'}.items():
        cmd = override(cmd,key,value)
    out = root/stem/label
    if out.exists():
        assert read(out/'command.json') == cmd, 'Cannot reuse a different command'
        print('CTX_CAPABILITY_RECHECK',stem,label,flush=True)
    else:
        out.mkdir(parents=True); write_once(out/'command.json',cmd)
        print('CTX_CAPABILITY_RUN',stem,label,limit,seconds,flush=True)
        execute(cmd,out/'run.log',timeout=900)
    return out,checked(out,cp,limit,seconds)


def heavy_folder(stem,arm):
    folder = ENGINE/stem/arm
    return Path(read(folder/'reuse.json')['source']) if (folder/'reuse.json').exists() else folder


def engineering(root,cp,plan):
    base = (BASE/'classpath.txt').read_text('utf-8-sig').strip(); evidence = []
    for spec in plan['instances']:
        stem = spec['stem']; initial = None
        for arm in CONTEXT:
            source = heavy_folder(stem,arm); heavy, = rows(source/'receipt.jsonl'); limit = heavy['successful']
            out, light = run_case(root,cp,stem,arm,'ENGINE-LIGHT-'+arm,limit,plan['engineeringSeed'],audit=True)
            assert light['paidSHA256'] == heavy['paidSHA256']
            assert {tuple(v) for v in endpoint(out,'FE500K',limit)['front']} == {tuple(p['objectives']) for p in heavy['lastValidFront']}
            assert light['search']['contextGom']['completePasses'] == 2 and light['search']['contextGom']['completePrograms'] == 200
            assert light['search']['contextGom']['validatedViews'] == 0 and light['search']['contextGom']['preparedViews'] == 200
            current = initial_key(out)
            if initial is None: initial = current
            assert initial == current == initial_key(source)
            evidence.append(dict(instance=stem,arm=arm,completeTwoPassPaidSHAAndFrontEqual=True))
        for arm in CONTROLS:
            old, old_r = run_case(root,base,stem,arm,'ENGINE-FROZEN-'+arm,5102,plan['engineeringSeed'],audit=True,old=True)
            new, new_r = run_case(root,cp,stem,arm,'ENGINE-CONTROL-'+arm,5102,plan['engineeringSeed'],audit=True)
            assert old_r['paidSHA256'] == new_r['paidSHA256']
            assert endpoint(old,'FE500K',5102)['front'] == endpoint(new,'FE500K',5102)['front']
            assert initial == initial_key(old) == initial_key(new)
            evidence.append(dict(instance=stem,arm=arm,frozenControlPaidSHAAndFrontEqual=True))
        for arm in ('SHARE_CTX_GOM','NSGA_CTX_GOM'):
            _, receipt = run_case(root,cp,stem,arm,'ENGINE-CLOCK-'+arm,5000,plan['engineeringSeed'],seconds=.2)
            evidence.append(dict(instance=stem,arm=arm,realTimeStop=True,successfulFE=receipt['successful']))
    actual = counts(root)
    assert actual['attemptedFE'] <= plan['maximumLightEngineeringAttempts'] and actual['successfulFE'] >= plan['fixedLightEngineeringFE']
    write_once(root/'light-engineering.json',dict(passed=True,checks=evidence,**actual,sameTimePerformanceClaim=False))
    return actual
