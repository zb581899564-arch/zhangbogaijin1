"""Frozen light classpaths, guarded single-JVM dispatch and source/control identity checks."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,rows,write_once,execute
from run_snapshot_anchor_audit import override
from ctx_gom_capability_support import checked
from frozen_classpath_identity import resolve_class,verify_capture
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest

MODES=('ALL','OWN','SYNC')
PHYSICS=[f'org.uma.jmetal.util.research.model.{n}' for n in
         ('DynamicDecoder','DynamicPhysics','DynamicParameters','DynamicSchedule','DynamicValidator','Instance')]


def build(root,plan):
    engine=Path(plan['engineeringRoot']);qpa=Path(plan['sourceQpa']);ctx=Path(plan['sourceCtx'])
    assert read(engine/'independent-final-audit.json')['passed']
    assert digest(engine/'independent-final-audit.json')==plan['engineeringAuditSHA256']
    assert class_hashes(engine/'classes')==read(engine/'class-hashes.json')
    assert class_hashes(qpa/'classes')==read(qpa/'class-hashes.json')
    ctx_hashes=read(ctx/'class-hashes.json')
    assert class_hashes(ctx/'kernel-classes')==ctx_hashes['kernel']
    assert class_hashes(ctx/'override-classes')==ctx_hashes['overrides']
    for name,sha in read(engine/'source-hashes.json').items():assert digest(engine/'source'/name)==sha
    shutil.copytree(engine/'classes',root/'kernel-classes');shutil.copytree(engine/'source',root/'kernel-source')
    source=root/'source';classes=root/'classes';source.mkdir();classes.mkdir()
    shutil.copy2(ROOT/'src/algorithms/diagnostics/qpa_feedback/QpaFeedbackCapabilityRun.java',source)
    for name in ('qpa_feedback_pilot_support.py','qpa_feedback_pilot_analysis.py','run_qpa_completed_donor_pilot.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    oldq=(qpa/'classpath.txt').read_text('utf-8-sig').strip();ctxcp=(ctx/'classpath.txt').read_text('utf-8-sig').strip()
    kernel=str(root/'kernel-classes')+';'+oldq
    execute(['java','-version'],root/'jdk-version.log')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',kernel,'-d',str(classes),str(source/'QpaFeedbackCapabilityRun.java')],root/'compile.log')
    qpacp=str(classes)+';'+kernel
    for name,cp in (('classpath.txt',qpacp),('ctx-classpath.txt',ctxcp)):(root/name).write_text(cp,encoding='utf-8')
    identities={}
    for name in PHYSICS:
        q,c=resolve_class(qpacp,name),resolve_class(ctxcp,name);assert q['sha256']==c['sha256'];identities[name]=dict(qpa=q,ctx=c)
    # Every ordinary control uses its original classes. The declared QPA override is the sole exception.
    sample=qpa/plan['instances'][0]['stem']/'14730003/FE500K-QPA_DIRECT/loaded-identity.jsonl'
    capture,=rows(sample)
    for name,record in capture.items():
        if not isinstance(record,dict) or 'sha256' not in record or name.endswith('.QpaPopulation'):continue
        expected=resolve_class(qpacp,name);assert expected['sha256']==record['sha256'];identities[name]=expected
    write_once(root/'inherited-class-identities.json',identities)
    write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()})
    write_once(root/'class-hashes.json',dict(wrapper=class_hashes(classes),kernel=class_hashes(root/'kernel-classes')))
    write_once(root/'kernel-source-hashes.json',{p.name:digest(p) for p in (root/'kernel-source').iterdir()})
    return dict(qpa=qpacp,ctx=ctxcp)


def prepare_inputs(root,plan):
    source=Path(plan['sourceEngineering']);ctx=Path(plan['sourceCtx'])
    for spec in plan['instances']:
        stem=spec['stem'];shutil.copytree(source/stem/'inputs',root/stem/'inputs')
        names=(stem+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt')
        for name in names:assert digest(root/stem/'inputs'/name)==digest(ctx/stem/'inputs'/name)
        write_once(root/stem/'input-hashes.json',{p.name:digest(p) for p in (root/stem/'inputs').iterdir()})


def run_one(root,paths,plan,stem,arm,label,seed,limit,bridge=False):
    context=arm=='NSGA_CTX_GOM';source=Path(plan['sourceCtx'] if context else plan['sourceQpa'])
    real=arm if arm not in MODES else 'QPA_DIRECT';mode=arm if arm in MODES else 'SYNC'
    folder=source/stem/('ENGINE-LIGHT' if bridge else f"{14910003 if context else 14730003}/FE500K-{real}")
    cmd=read(folder/'command.json');entry='research.dynamic.GomCapabilityRun' if context else 'research.dynamic.QpaCapabilityRun';index=cmd.index(entry)
    cp=paths['ctx' if context else 'qpa'];cmd[cmd.index('-cp')+1]=cp
    if not context:cmd[index]='research.dynamic.QpaFeedbackCapabilityRun'
    for offset,name in enumerate((stem+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt'),1):cmd[index+offset]=str(root/stem/'inputs'/name)
    out=root/stem/label;out.mkdir(parents=True);cmd[index+4]=str(out);cmd[index+5]=real;cmd[index+6]=str(limit);cmd[index+7]=str(seed);cmd[index+8]='Infinity'
    for key,value in {'research.qpa.completedDonors':mode,'research.pa.auditPaid':'true','research.pa.traceIdentity':'false'}.items():cmd=override(cmd,key,value)
    write_once(out/'command.json',cmd);print('QPA_FEEDBACK_PILOT_RUN',stem,label,limit,flush=True)
    execute(cmd,out/'run.log',timeout=900);receipt=checked(out,cp,limit,float('inf'))
    assert receipt['decoder']['dynamic.evaluations']==receipt['successful']==receipt['attempted']==limit and receipt['failed']==0
    assert receipt['paidSHA256'] is not None
    if not context:
        helper,=rows(out/'completed-donor-identity.jsonl');assert helper['reads']['mode']==mode
        write_once(out/'completed-donor-identity-verified.json',verify_capture(helper['identity'],cp))
        reads=helper['reads']
        if arm not in MODES:assert reads['maskReads']==0
        elif arm=='ALL':assert reads['crossRoleFreshMaskReads']>0
        elif arm=='OWN':assert reads['freshMaskReads']>0 and reads['crossRoleFreshMaskReads']==0
        else:assert reads['freshMaskReads']==0
    return out,receipt
