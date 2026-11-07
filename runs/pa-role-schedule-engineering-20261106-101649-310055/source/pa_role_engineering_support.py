"""Build only a two-hook population override; accepted role planner and all other kernels stay frozen."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,rows,write_once,execute
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes
from frozen_classpath_identity import resolve_class,verify_capture
from run_snapshot_anchor_audit import override
from ctx_gom_build import once
from pa_role_replay import replay


def build(root,plan):
    semantic=Path(plan['semanticsRoot']);assert read(semantic/'independent-final-audit.json')['passed']
    assert digest(semantic/'independent-final-audit.json')==plan['semanticsAuditSHA256']
    source,classes,kernel=[root/name for name in ('source','classes','kernel-classes')]
    for p in (source,classes,kernel):p.mkdir()
    for path in (semantic/'classes').rglob('PaRoleSchedule*.class'):
        target=kernel/path.relative_to(semantic/'classes');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    old=ROOT/'runs/qpa-capability-pilot-20261106-025546-344483/source/PaPopulation.java';text=old.read_text('utf-8')
    anchor='            evaluation.checkpoint(); generation++; phase = "REENCODING";'
    text=once(text,anchor,anchor+'\n            PaRoleSchedule.before(generation, population);')
    anchor='''            List<int[]> subsets = learn(); phase = "MIXING";
            for (int i = 0; i < population.size(); i++) {'''
    text=once(text,anchor,anchor.replace('for (int i = 0; i < population.size(); i++)','for (int i : PaRoleSchedule.order(generation))'))
    (source/'PaPopulation.java').write_text(text,encoding='utf-8')
    shutil.copy2(ROOT/'src/algorithms/diagnostics/pa_roles/PaRoleEngineeringRun.java',source)
    for name in ('pa_role_engineering_support.py','pa_role_replay.py','run_pa_role_schedule_engineering.py','pa_role_semantics_data.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    base=(Path(plan['sourceBase'])/'classpath.txt').read_text('utf-8-sig').strip();cp=str(kernel)+';'+base
    execute(['java','-version'],root/'jdk-version.log')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',cp,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    cp=str(classes)+';'+cp;(root/'classpath.txt').write_text(cp,encoding='utf-8')
    write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()});write_once(root/'class-hashes.json',dict(wrapper=class_hashes(classes),planner=class_hashes(kernel)))
    write_once(root/'original-population-source.json',dict(path=str(old),sha256=digest(old)))
    inherited={}
    for suffix in ('PaPaidEvaluation','PaIndividual','PaDependencyModel','PaMixingMove','FactoryKeyReencoder','LinkageHierarchy'):
        name='org.uma.jmetal.util.research.modelglobal.'+suffix;actual=resolve_class(cp,name);assert actual==resolve_class(base,name);inherited[name]=actual
    write_once(root/'inherited-identities.json',inherited);return cp


def receipts(root):
    new=[rows(p)[0] for p in root.glob('*/*/receipt.jsonl')]
    reused=[rows(Path(read(p)['source'])/'receipt.jsonl')[0] for p in root.glob('*/*/reuse.json')]
    data=new+reused
    return dict(runs=len(data),attemptedFE=sum(r['attemptedFE'] for r in data),successfulFE=sum(r['successfulFE'] for r in data),
        failedFE=sum(r['failedFE'] for r in data),extraPaidTimelineQA=sum(r['paidFullTimelineQA'] for r in data),extraViewTimelineQA=sum(r['reencodingFullTimelineQA'] for r in data),
        newAttemptedFE=sum(r['attemptedFE'] for r in new),reusedAttemptedFE=sum(r['attemptedFE'] for r in reused))


def run_one(root,cp,plan,spec,mode,label,limit):
    assert receipts(root)['attemptedFE']+limit<=plan['maximumActualAttemptedFE']
    source=Path(plan['sourceEngineering'])/spec['stem']/'main';cmd=read(source/'command.json');at=cmd.index('research.dynamic.PaPopulationRun')
    cmd[at]='research.dynamic.PaRoleEngineeringRun';cmd[cmd.index('-cp')+1]=cp
    inputs=root/spec['stem']/'inputs'
    for offset,name in enumerate((spec['stem']+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt','sources.tsv'),1):cmd[at+offset]=str(inputs/name)
    folder=root/spec['stem']/label;folder.mkdir();cmd[at+5]=str(folder);cmd[at+7]=str(limit)
    for key,value in {'research.paRole.mode':mode,'research.paRole.seed':str(plan['privateSeed']),'research.paRole.fullTrace':'true'}.items():cmd=override(cmd,key,value)
    at=cmd.index('research.dynamic.PaRoleEngineeringRun')
    amendment=read(root/'protocol.json').get('engineeringAmendment')
    if amendment and spec['stem']=='20_8_5_1' and label==mode=='NATIVE':
        previous=Path(amendment['previousFailure'])/spec['stem']/label
        old_cmd=read(previous/'command.json');old_at=old_cmd.index('research.dynamic.PaRoleEngineeringRun')
        assert old_cmd[old_at+6:]==cmd[at+6:]
        old_prefix=old_cmd[:old_at];new_prefix=cmd[:at]
        old_cp=old_prefix[old_prefix.index('-cp')+1]
        old_prefix[old_prefix.index('-cp')+1]=new_prefix[new_prefix.index('-cp')+1]='<classpath>'
        assert old_prefix==new_prefix
        for i in range(1,5):assert digest(Path(old_cmd[old_at+i]))==digest(Path(cmd[at+i]))
        capture,=rows(previous/'loaded-identity.jsonl');verify_capture(capture,old_cp);capture.update(read(previous/'role-identity.json'))
        for name,value in capture.items():
            if isinstance(value,dict) and 'sha256' in value:assert resolve_class(cp,name)['sha256']==value['sha256']
        result=read(previous/'role-independent-replay.json');assert result['passed']
        write_once(folder/'reuse.json',dict(source=str(previous),classBytesInputsNumericOptionsRevalidated=True,newSearchFE=0))
        print('PA_ROLE_ENGINEERING_REUSE_VALIDATED',spec['stem'],label,flush=True)
        receipt,=rows(previous/'receipt.jsonl');return previous,receipt,result
    write_once(folder/'command.json',cmd);print('PA_ROLE_ENGINEERING_RUN',spec['stem'],label,limit,flush=True)
    execute(cmd,folder/'run.log',timeout=900)
    receipt,=rows(folder/'receipt.jsonl');assert receipt['successfulFE']==receipt['attemptedFE']==receipt['decoder']['dynamic.evaluations']==limit
    loaded,=rows(folder/'loaded-identity.jsonl');verify_capture(loaded,cp);verify_capture(read(folder/'role-identity.json'),cp)
    result=replay(folder,mode,plan['privateSeed']);print('PA_ROLE_ENGINEERING_TRACE_PASS',spec['stem'],label,result['completePrograms'],flush=True)
    return folder,receipt,result
