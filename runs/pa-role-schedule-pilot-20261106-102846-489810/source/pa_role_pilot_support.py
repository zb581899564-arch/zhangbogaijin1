"""Accepted role kernel, light trace bridges and fixed-budget ordinary-base dispatch."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,rows,write_once,execute
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes
from frozen_classpath_identity import resolve_class,verify_capture
from run_snapshot_anchor_audit import override
from ctx_gom_capability_support import checked,counts
from pa_capability_support import initial_key
from qpa_capability_analysis import endpoint
from pa_role_semantics_data import expected
from qpa_geometry_audit_inputs import JavaRandom


def actual(folder):
    return Path(read(folder/'reuse.json')['source']) if (folder/'reuse.json').exists() else folder


def supplied_initials(path):
    result=[]
    for line in path.read_text('utf-8').splitlines():
        fields=line.split('\t')
        result.append(dict(objectives=list(map(float,fields[3].split(','))),
            **{name:list(map(int,fields[at].split(','))) for at,name in enumerate(('JS','FA','MA','WA'),4)}))
    return result


def build(root,plan):
    engine=Path(plan['engineeringRoot'])
    assert read(engine/'independent-final-audit.json')['passed']
    assert digest(engine/'independent-final-audit.json')==plan['engineeringAuditSHA256']
    hashes=read(engine/'class-hashes.json')
    assert hashes['wrapper']==class_hashes(engine/'classes') and hashes['planner']==class_hashes(engine/'kernel-classes')
    kernel=root/'kernel-classes';shutil.copytree(engine/'classes',kernel)
    shutil.copytree(engine/'kernel-classes',kernel,dirs_exist_ok=True)
    shutil.copytree(engine/'source',root/'accepted-kernel-source')
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    shutil.copy2(ROOT/'src/algorithms/diagnostics/pa_roles/PaRoleCapabilityRun.java',source)
    for name in ('pa_role_pilot_support.py','pa_role_pilot_analysis.py','run_pa_role_schedule_pilot.py','pa_role_semantics_data.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    base=(Path(plan['base'])/'classpath.txt').read_text('utf-8-sig').strip();cp=str(kernel)+';'+base
    execute(['java','-version'],root/'jdk-version.log')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',cp,'-d',str(classes),str(source/'PaRoleCapabilityRun.java')],root/'compile.log')
    cp=str(classes)+';'+cp;(root/'classpath.txt').write_text(cp,encoding='utf-8')
    write_once(root/'class-hashes.json',dict(wrapper=class_hashes(classes),kernel=class_hashes(kernel)))
    write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()})
    inherited={}
    for suffix in ('PaPaidEvaluation','PaIndividual','PaDependencyModel','PaMixingMove','FactoryKeyReencoder','LinkageHierarchy','QpaPopulation'):
        name='org.uma.jmetal.util.research.modelglobal.'+suffix;value=resolve_class(cp,name)
        assert value==resolve_class(base,name);inherited[name]=value
    for suffix in ('search.CanonicalHmopso','search.GomLocalProgram','classic.ClassicAlgorithm','search.DeepLocalVisits','model.DynamicDecoder'):
        name='org.uma.jmetal.util.research.'+suffix;value=resolve_class(cp,name)
        assert value==resolve_class(base,name);inherited[name]=value
    write_once(root/'inherited-identities.json',inherited);return cp,base


def verify_roles(folder,mode,seed):
    rng=JavaRandom(seed);events=rows(folder/'role-events.jsonl');changed=visited=0
    for number,event in enumerate(events,1):
        assert event['generation']==number and event['mode']==mode
        before,after=event['before'],event['after'];roles,visit=expected(before,mode,rng)
        assert event['visit']==visit and [p['role'] for p in after]==roles
        assert [{k:v for k,v in p.items() if k!='role'} for p in before]==[{k:v for k,v in p.items() if k!='role'} for p in after]
        assert len({p['id'] for p in before})==len(set(visit))==100
        changed+=sum(a['role']!=b['role'] for a,b in zip(before,after));visited+=sum(a!=b for a,b in enumerate(visit))
    return dict(generations=len(events),roleChanges=changed,visitPositionChanges=visited,mappingAndPhysicalIdentityPassed=True)


def run_one(root,cp,plan,spec,arm,seed,label,limit,old=False,source_tsv=None):
    assert counts(root)['attemptedFE']+limit<=plan['maximumTotalAttemptedFE']
    real,mode=plan['armDefinitions'][arm]
    is_qpa=real=='QPA_DIRECT';entry='research.dynamic.QpaCapabilityRun' if is_qpa else 'research.dynamic.GomCapabilityRun'
    source=Path(plan['qpaSource'] if is_qpa else plan['controlSource'])
    source_seed='14730003' if is_qpa else '14910003'
    cmd=read(source/spec['stem']/source_seed/('FE500K-'+real)/'command.json');at=cmd.index(entry)
    cmd[cmd.index('-cp')+1]=cp
    if not old:cmd[at]='research.dynamic.PaRoleCapabilityRun'
    out=root/spec['stem']/label;out.mkdir(parents=True)
    for offset,name in enumerate((spec['stem']+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt'),1):cmd[at+offset]=str(root/spec['stem']/'inputs'/name)
    cmd[at+4]=str(out);cmd[at+6]=str(limit);cmd[at+7]=str(seed)
    options={'research.paRole.mode':mode,'research.paRole.seed':str(plan['privateSeed']),'research.paRole.fullTrace':'false',
        'research.pa.auditPaid':'true','research.pa.traceIdentity':'false','research.ctxFork.localInput':'POST'}
    if source_tsv:options['research.pa.sourceTSV']=str(source_tsv)
    for key,value in options.items():cmd=override(cmd,key,value)
    write_once(out/'command.json',cmd);print('PA_ROLE_PILOT_RUN',spec['stem'],label,limit,flush=True)
    execute(cmd,out/'run.log',timeout=900);receipt=checked(out,cp,limit,float('inf'))
    assert receipt['attempted']==receipt['successful']==receipt['decoder']['dynamic.evaluations']==limit and receipt['paidSHA256']
    if not old:
        verify_capture(read(out/'role-identity.json'),cp)
        mapping=verify_roles(out,mode,plan['privateSeed']);write_once(out/'role-mapping-audit.json',mapping)
        assert bool(mapping['generations'])==(real in ('PA_JOINT','PA_EQUAL') and limit>100)
    return out,receipt


def bridge(root,cp,base,plan):
    engine=Path(plan['engineeringRoot']);checks=[]
    for spec in plan['instances']:
        stem=spec['stem'];sources=engine/stem/'inputs/sources.tsv'
        for mode in plan['modes']:
            original=actual(engine/stem/mode);old,=rows(original/'receipt.jsonl')
            out,new=run_one(root,cp,plan,spec,mode,13630003,'BRIDGE-'+mode,spec['engineeringFE'],source_tsv=sources)
            assert old['paidSHA256']==new['paidSHA256'] and initial_key(out)==supplied_initials(sources)
            assert sorted(map(tuple,endpoint(out,'FE',spec['engineeringFE'])['front']))==sorted(tuple(p['objectives']) for p in old['lastValidFront'])
            checks.append(dict(instance=stem,arm=mode,heavyLightWholePaidTraceInitialAndFrontEqual=True))
        for arm in plan['controls']:
            a,ra=run_one(root,base,plan,spec,arm,13630003,'BRIDGE-OLD-'+arm,5102,old=True)
            b,rb=run_one(root,cp,plan,spec,arm,13630003,'BRIDGE-NEW-'+arm,5102)
            assert ra['paidSHA256']==rb['paidSHA256'] and initial_key(a)==initial_key(b)
            assert endpoint(a,'FE',5102)['front']==endpoint(b,'FE',5102)['front']
            checks.append(dict(instance=stem,arm=arm,oldNewWholePaidTraceInitialAndFrontEqual=True))
    totals=counts(root);assert totals['attemptedFE']==totals['successfulFE']==plan['plannedBridgeFE']
    write_once(root/'bridge-acceptance.json',dict(passed=True,checks=checks,**totals))
