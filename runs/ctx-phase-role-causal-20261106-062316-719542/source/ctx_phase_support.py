"""Frozen commands, whole-paid-prefix invariants and counted one-JVM diagnostic dispatch."""
from run_long_budget_bridge import ROOT,read,rows,write_once,execute
from ctx_gom_capability_support import checked
from run_snapshot_anchor_audit import override
from frozen_classpath_identity import verify_capture

PILOT=ROOT/'runs/ctx-gom-capability-20261106-051509-678987'


def counts(root):
    paths=list(root.glob('*/*/run-receipt.jsonl'));rs=[rows(p)[0] for p in paths]
    return dict(runs=len(rs),successfulFE=sum(r['successful'] for r in rs),attemptedFE=sum(r['attempted'] for r in rs),
        failedFE=sum(r['failed'] for r in rs),extraCheckpointQA=sum(read(p.parent/'checkpoint-validation.json')['uniqueOfflineDecodes'] for p in paths if (p.parent/'checkpoint-validation.json').exists()))


def load_events(folder):
    populations={};prefix={};tail=None;selection={};workspace={};programs=[]
    with (folder/'pipeline.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            import json
            e=json.loads(line)
            if e['kind']=='population':populations[e['cycle'],e['phase']]=e
            elif e['kind']=='paidPrefix':prefix[str(e['fe'])]=e['sha256']
            elif e['kind']=='finish':tail=e
            elif e['kind']=='selection':selection[e['cycle']]=e
            elif e['kind']=='workspace':workspace[e['cycle']]=e
            elif e['kind']=='program':programs.append(e)
    assert tail is not None and tail['passes']==10 and tail['fe']==248701
    assert len(selection)==len(workspace)==10 and len(programs)==1000
    return dict(populations=populations,prefix=prefix,tail=tail,selection=selection,workspace=workspace,programs=programs)


def run_one(root,cp,seed,arm,plan):
    stem=plan['instance'];out=root/str(seed)/arm;out.mkdir(parents=True)
    cmd=read(PILOT/stem/str(seed)/'FE500K-SHARE_CTX_GOM/command.json');entry=cmd.index('research.dynamic.GomCapabilityRun')
    cmd[cmd.index('-cp')+1]=cp;cmd[entry]='research.dynamic.GomPhaseRoleRun';cmd[entry+4]=str(out);cmd[entry+6]=str(plan['runLimitFE'])
    for i,name in enumerate((stem+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt'),entry+1):cmd[i]=str(root/'inputs'/name)
    global_level,local_level=plan['arms'].get(arm,plan['arms']['RR'])
    for key,value in {'research.pa.auditPaid':'true','research.ctxPipeline.file':str(out/'pipeline.jsonl'),
                      'research.ctxPhase.global':global_level,'research.ctxPhase.local':local_level}.items():cmd=override(cmd,key,value)
    write_once(out/'command.json',cmd);print('CTX_PHASE_RUN',seed,arm,plan['runLimitFE'],flush=True);execute(cmd,out/'run.log',timeout=900)
    receipt=checked(out,cp,plan['runLimitFE'],float('inf'))
    assert receipt['decoder']['dynamic.evaluations']==plan['runLimitFE']
    assert receipt['search']['global.evaluations']==50001 and receipt['search']['jointLocal.evaluations']==198600
    assert receipt['search']['contextGom']['completePasses']==10
    for file in ('loaded-probe-identity.jsonl','loaded-phase-identity.jsonl'):
        capture,=rows(out/file);write_once(out/(file.replace('.jsonl','-verified.json')),verify_capture(capture,cp))
    events=load_events(out);assert events['tail']['paidSHA256']==receipt['paidSHA256']
    return out,receipt,events


def invariants(records,plan):
    native=records['NATIVE'];rr=records['RR']
    assert native[1]['paidSHA256']==rr[1]['paidSHA256']
    for key in native[1]['search']:
        if key!='cooperation':assert native[1]['search'][key]==rr[1]['search'][key]
    for key in ('dynamic.evaluations','dynamic.reusedOperations','dynamic.recomputedOperations'):assert native[1]['decoder'][key]==rr[1]['decoder'][key]
    front=lambda folder:[(p['checkpoint'],p['front']) for p in rows(folder/'anytime.jsonl') if p['checkpointKind']=='FE']
    assert front(native[0])==front(rr[0])
    baseline=records['NATIVE'][2]['prefix'][str(plan['commonPrefixFE'])]
    assert all(r[2]['prefix'][str(plan['commonPrefixFE'])]==baseline for r in records.values())
    for a,b in (('RR','RC'),('CR','CC')):
        assert records[a][2]['prefix'][str(plan['afterIntervenedGlobalFE'])]==records[b][2]['prefix'][str(plan['afterIntervenedGlobalFE'])]
        assert records[a][2]['populations'][10,'POST_GLOBAL']['points']==records[b][2]['populations'][10,'POST_GLOBAL']['points']
    before=records['NATIVE'][2]['populations'][10,'PRE_GLOBAL']['points']
    assert all(r[2]['populations'][10,'PRE_GLOBAL']['points']==before for r in records.values())
    return dict(nativeRRWholePaidSHAEqual=True,commonPrefixFE=plan['commonPrefixFE'],commonPrefixSHA256=baseline,
        globalRowPrefixAndCohortEqual=True,commonInputFullParticleStateEqual=True)
