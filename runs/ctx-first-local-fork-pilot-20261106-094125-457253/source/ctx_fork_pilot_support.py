"""Reuse accepted fork class bytes, guarded light dispatch and complete native bridges."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes
from frozen_classpath_identity import verify_capture, resolve_class
from run_snapshot_anchor_audit import override
from ctx_gom_capability_support import checked, counts
from qpa_capability_analysis import endpoint
from pa_capability_support import initial_key


def build(root, plan):
    engine = Path(plan['engineeringRoot'])
    assert read(engine/'independent-final-audit.json')['passed']
    assert digest(engine/'independent-final-audit.json') == plan['engineeringAuditSHA256']
    assert class_hashes(engine/'classes') == read(engine/'class-hashes.json')
    shutil.copytree(engine/'classes',root/'kernel-classes'); shutil.copytree(engine/'source',root/'kernel-source')
    source, classes = root/'source', root/'classes'; source.mkdir(); classes.mkdir()
    shutil.copy2(ROOT/'src/algorithms/diagnostics/ctx_fork/GomForkCapabilityRun.java',source)
    for name in ('ctx_fork_pilot_support.py','ctx_fork_pilot_analysis.py','run_ctx_first_local_fork_pilot.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    base = (Path(plan['source'])/'classpath.txt').read_text('utf-8-sig').strip()
    cp = str(root/'kernel-classes')+';'+base
    execute(['java','-version'],root/'jdk-version.log')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',cp,'-d',str(classes),str(source/'GomForkCapabilityRun.java')],root/'compile.log')
    cp = str(classes)+';'+cp; (root/'classpath.txt').write_text(cp,encoding='utf-8')
    write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()})
    write_once(root/'kernel-source-hashes.json',{p.name:digest(p) for p in (root/'kernel-source').iterdir()})
    write_once(root/'class-hashes.json',dict(wrapper=class_hashes(classes),kernel=class_hashes(root/'kernel-classes')))
    for name in ('org.uma.jmetal.util.research.classic.ClassicAlgorithm','org.uma.jmetal.util.research.search.DeepLocalVisits',
                 'org.uma.jmetal.util.research.modelglobal.PaPopulation','org.uma.jmetal.util.research.model.DynamicDecoder'):
        assert resolve_class(cp,name) == resolve_class(base,name)
    return cp,base


def run_one(root,cp,plan,spec,arm,mode,seed,label,limit,old=False):
    assert counts(root)['attemptedFE']+limit <= plan['maximumTotalAttemptedFE']
    template=Path(plan['source'])/spec['stem']/'14910003'/('FE500K-'+arm)
    command=read(template/'command.json');at=command.index('research.dynamic.GomCapabilityRun')
    if not old:command[at]='research.dynamic.GomForkCapabilityRun'
    command[command.index('-cp')+1]=cp;inputs=root/spec['stem']/'inputs'
    for offset,name in enumerate((spec['stem']+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt'),1):command[at+offset]=str(inputs/name)
    out=root/spec['stem']/label;out.mkdir(parents=True);command[at+4]=str(out);command[at+6]=str(limit);command[at+7]=str(seed)
    for key,value in {'research.ctxFork.localInput':mode,'research.pa.auditPaid':'true'}.items():command=override(command,key,value)
    write_once(out/'command.json',command);print('CTX_FORK_PILOT_RUN',spec['stem'],label,limit,flush=True)
    execute(command,out/'run.log',timeout=900);receipt=checked(out,cp,limit,float('inf'))
    assert receipt['successful']==receipt['attempted']==receipt['decoder']['dynamic.evaluations']==limit and receipt['paidSHA256']
    if not old:
        helper=read(out/'fork-input.json');verify_capture(helper['identity'],cp);fork=helper['fork']
        if arm in ('SHARE_CTX_GOM','UNIFORM_CTX_GOM','SYNC_CTX_GOM'):
            assert fork['mode']==mode and fork['snapshotChecks']==(100 if mode=='PRE_FIRST' else 0)
            assert [p['source'] for p in fork['entries']]==(['PRE','POST'] if mode=='PRE_FIRST' else ['POST','POST'])
            assert receipt['search']['contextGom']['completePasses']==2 and receipt['search']['contextGom']['completePrograms']==200
        else:assert fork['cyclesStarted']==fork['snapshotChecks']==0
    return out,receipt


def bridge(root,cp,base,plan):
    engine=Path(plan['engineeringRoot']);checks=[]
    for spec in plan['instances']:
        stem=spec['stem']
        for arm in ('SHARE_CTX_GOM','UNIFORM_CTX_GOM'):
            for mode in ('POST','PRE_FIRST'):
                native=engine/stem/(arm+'-'+mode);old,=rows(native/'receipt.jsonl')
                out,new=run_one(root,cp,plan,spec,arm,mode,14810003,'BRIDGE-'+arm+'-'+mode,spec['fixedFE'])
                assert new['paidSHA256']==old['paidSHA256'] and initial_key(out)==initial_key(native)
                assert sorted(map(tuple,endpoint(out,'FE',spec['fixedFE'])['front']))==sorted(tuple(p['objectives']) for p in old['lastValidFront'])
                checks.append(dict(instance=stem,arm=arm,mode=mode,heavyLightWholePaidTraceAndFrontEqual=True))
        for arm in ('FULL_SHARED_DEEP','LI_RECON_DEEP'):
            a,ra=run_one(root,base,plan,spec,arm,'POST',14810003,'BRIDGE-OLD-'+arm,5102,old=True)
            b,rb=run_one(root,cp,plan,spec,arm,'POST',14810003,'BRIDGE-NEW-'+arm,5102)
            assert ra['paidSHA256']==rb['paidSHA256'] and initial_key(a)==initial_key(b)
            assert endpoint(a,'FE',5102)['front']==endpoint(b,'FE',5102)['front']
            checks.append(dict(instance=stem,arm=arm,originalControlWholePaidTraceAndFrontEqual=True))
    actual=counts(root);assert actual['attemptedFE']==actual['successfulFE']==plan['plannedBridgeFE']
    write_once(root/'bridge-acceptance.json',dict(passed=True,checks=checks,**actual))
