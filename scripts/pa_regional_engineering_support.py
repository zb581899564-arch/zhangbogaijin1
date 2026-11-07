"""Exact source inputs, charged full runs and independent regional trace verification."""
from pathlib import Path

from run_long_budget_bridge import read,rows,write_once,execute
from run_snapshot_anchor_audit import override
from frozen_classpath_identity import verify_capture
from research.semantic_repair.evidence import digest
from pa_regional_replay import replay


def totals(root):
    records=[rows(p)[0] for p in root.glob('*/*/receipt.jsonl')]
    return dict(runs=len(records),attemptedFE=sum(r['attemptedFE'] for r in records),successfulFE=sum(r['successfulFE'] for r in records),
        failedFE=sum(r['failedFE'] for r in records),extraPaidTimelineQA=sum(r['paidFullTimelineQA'] for r in records),
        extraViewTimelineQA=sum(r['reencodingFullTimelineQA'] for r in records))


def source_command(spec):
    cmd=read(Path(spec['source'])/'command.json')
    at=next(i for i,value in enumerate(cmd) if value in ('research.dynamic.PaRoleEngineeringRun','research.dynamic.PaPopulationRun'))
    return cmd,at


def run_one(root,cp,plan,spec,mode,label,limit,scale):
    assert totals(root)['attemptedFE']+limit<=plan['maximumActualAttemptedFE']
    cmd,at=source_command(spec);cmd[at]='research.dynamic.PaRegionalEngineeringRun';cmd[cmd.index('-cp')+1]=cp
    inputs=root/spec['instance']/'inputs'
    for offset,name in enumerate((spec['instance']+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt','sources.tsv'),1):cmd[at+offset]=str(inputs/name)
    folder=root/spec['instance']/label;folder.mkdir();cmd[at+5]=str(folder);cmd[at+7]=str(limit)
    for key,value in {'research.paRegional.mode':mode,'research.paRegional.scale':','.join(map(str,scale))}.items():cmd=override(cmd,key,value)
    write_once(folder/'command.json',cmd);print('PA_REGIONAL_ENGINEERING_RUN',spec['instance'],label,limit,flush=True)
    execute(cmd,folder/'run.log',timeout=900);receipt,=rows(folder/'receipt.jsonl')
    assert receipt['status']=='COMPLETE' and receipt['successfulFE']==receipt['attemptedFE']==receipt['decoder']['dynamic.evaluations']==limit and receipt['failedFE']==0
    capture,=rows(folder/'loaded-identity.jsonl');verify_capture(capture,cp);verify_capture(read(folder/'regional-policy.json')['identity'],cp)
    proof=replay(folder,mode,scale,spec['cutoffs']);print('PA_REGIONAL_ENGINEERING_TRACE_PASS',spec['instance'],label,proof['completedPrograms'],flush=True)
    return folder,receipt,proof
