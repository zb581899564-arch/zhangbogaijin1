"""Build isolated capability entries, preserving frozen strong controls and adding a separately named plain NSGA."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,rows,write_once,execute
from run_paired_qgs_guidance import replace
from run_snapshot_anchor_audit import override
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes

ENGINE=ROOT/'runs/pa-population-engineering-20261105-164116-698339'
SOURCE=ROOT/'runs/linkage-mixing-probe-20261105-142116-487815'
TEMPLATES=ROOT/'runs/makespan-tie-screen-20261105-025223-471920'
ARMS=('PA_JOINT','PA_RELABEL','NSGA2_PLAIN','NSGA2_DEEP','FULL_SHARED_DEEP','LI_RECON_DEEP')


def build(root):
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    for folder in ('src/algorithms/model_global/encoding','src/algorithms/model_global/linkage',
                   'src/algorithms/model_global/population','src/algorithms/diagnostics/pa_capability'):
        for path in (ROOT/folder).glob('*.java'):shutil.copy2(path,source)
    original=ROOT/'runs/dynamic-deep-local-20261103-184901-271850/source/ClassicAlgorithm.java'
    text=original.read_text('utf-8').replace('ClassicAlgorithm','PlainNsgaAlgorithm')
    block='''            if (deep.due(globalOffspring)) {
                List<PermutationSolution<Integer>> local = deep.improve(population);
                next = selection.environmental(ClassicTools.union(population, local), ClassicConfig.POPULATION);
                population = next.population; scores = next.scores;
            }'''
    text=replace(text,block,'            // Plain control: no deep local-search call; common initialization is retained.')
    text=replace(text,'public String configuration() { return config.describe(); }',
                 'public String configuration() { return config.describe() + ";deepLocal=DISABLED;commonInitializationOnly"; }')
    (source/'PlainNsgaAlgorithm.java').write_text(text,encoding='utf-8')
    base=(ENGINE/'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java','-version'],root/'jdk-version.log')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    cp=f'{classes};{base}';(root/'classpath.txt').write_text(cp,encoding='utf-8')
    write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()})
    write_once(root/'class-hashes.json',class_hashes(classes))
    write_once(root/'plain-control-adaptation.json',{'source':str(original),'sourceSHA256':digest(original),
        'changes':['Separate class name','Remove only the deep.due/improve/environmental-local block','Explicit configuration label'],
        'kept':'Original initialization, tournament, OX/resource variation and200to100selection',
        'strongClassicClassOverridden':False})
    return cp


def command(root,cp,stem,arm,label,limit,seed,seconds=float('inf'),audit=False,source_tsv=None):
    template='STRICT_FULL' if arm=='FULL_SHARED_DEEP' else 'LI_STRICT' if arm=='LI_RECON_DEEP' else 'NSGA_STRICT'
    old=read(TEMPLATES/stem/'10950003'/template/'command.json');entry=old.index('research.dynamic.PddrIsolationRun')
    prefix=old[:entry];prefix[prefix.index('-cp')+1]=cp
    settings={'research.snapshot.mode':'ANCHOR','research.snapshot.audit':'false','research.memory.audit':'false',
              'research.makespan.tie':'STRICT','research.pa.traceIdentity':'false','research.pa.auditPaid':str(audit).lower()}
    if source_tsv:settings['research.pa.sourceTSV']=str(source_tsv)
    for key,value in settings.items():prefix=override(prefix,key,value)
    inp=root/stem/'inputs';out=root/stem/label
    return prefix+['research.dynamic.PaCapabilityRun',str(inp/f'{stem}.txt'),str(inp/'RECONSTRUCTED-setup.txt'),
        str(inp/'fatigue-input.txt'),str(out),arm,str(limit),str(seed),'Infinity' if seconds==float('inf') else str(seconds)]


def run_case(root,cp,stem,arm,label,limit,seed,seconds=float('inf'),audit=False,source_tsv=None):
    out=root/stem/label;out.mkdir(parents=True)
    cmd=command(root,cp,stem,arm,label,limit,seed,seconds,audit,source_tsv);write_once(out/'command.json',cmd)
    print('PA_CAPABILITY_RUN',stem,label,arm,limit,seconds,flush=True);execute(cmd,out/'run.log',timeout=300)
    receipt,=rows(out/'run-receipt.jsonl');assert receipt['error'] is None and receipt['constructorsIncludedInClock']
    assert receipt['attempted']==receipt['successful']+receipt['failed']
    assert receipt['failed']==receipt['timeInterruptedAttempts'] and receipt['failed']<=1
    if seconds==float('inf'):assert receipt['stopReason']=='FE_LIMIT' and receipt['successful']==limit and receipt['failed']==0
    else:assert receipt['stopReason']=='TIME_LIMIT' and receipt['searchSeconds']>=seconds and receipt['successful']<limit
    search=receipt['search'];assert sum(search.get(s+'.evaluations',0) for s in ('initialization','global','inter','intra'))==receipt['successful']
    validation=read(out/'checkpoint-validation.json');assert validation['status']=='passed' and validation['allReachedPointsCovered']
    for point in rows(out/'checkpoint-solutions.jsonl'):
        assert point['bornFE']<=point['checkpointFE'] and point['bornSeconds']<=point['checkpointElapsedSeconds']
        if point['checkpointKind']=='TIME':assert point['bornSeconds']<=point['checkpoint']
    if arm=='NSGA2_PLAIN':assert search.get('inter.evaluations',0)+search.get('intra.evaluations',0)==0
    return out,receipt


def initial_key(out):
    return [{key:p[key] for key in ('JS','FA','MA','WA','objectives')} for p in rows(out/'initial-population.jsonl')]


def fees(receipts):
    return {'successfulFE':sum(r['successful'] for _,r in receipts),'attemptedFE':sum(r['attempted'] for _,r in receipts),
            'failedAttempts':sum(r['failed'] for _,r in receipts),'timeInterruptedAttempts':sum(r['timeInterruptedAttempts'] for _,r in receipts),
            'offlineFullDecoderQA':sum(read(out/'checkpoint-validation.json')['uniqueOfflineDecodes'] for out,_ in receipts)}
