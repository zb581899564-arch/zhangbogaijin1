"""Read-only bounded-history reuse potential with paid trace equivalence, not an implemented cache."""
from datetime import datetime
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from paired_survival_bench import class_hashes
from natural_local_support import run_case,command,verify
from run_paired_qgs_guidance import replace
from run_snapshot_anchor_audit import override

ENTRY=ROOT/'runs/natural-local-audit-20261105-073204-330248'
SOURCE=ROOT/'runs/natural-regime-bench-20261105-073626-086353'
FROZEN=ROOT/'runs/night-research-H1-20261103-010138-848045'
SEED=12390003;LIMIT=100000


def build(root):
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    evaluator=(FROZEN/'source/src/java/integration/DynamicEvaluation.java').read_text('utf-8')
    evaluator=replace(evaluator,'        double[] objectives = schedule.objectives();',
        '        FactoryCachePotential.observe(instance,parameters,js,fa,ma,wa,\n'
        '            incremental && previous instanceof DynamicSchedule?(DynamicSchedule)previous:null,schedule,prefix!=null);\n'
        '        double[] objectives = schedule.objectives();')
    (source/'DynamicEvaluation.java').write_text(evaluator,encoding='utf-8')
    body=(ENTRY/'source/NaturalLocalRun.java').read_text('utf-8').replace('NaturalLocalRun','FactoryCachePotentialRun')
    body=replace(body,'        NaturalRunEvidence.identity(out);',
        '        NaturalRunEvidence.identity(out);\n'
        '        lines(out.resolve("factory-cache-identity.json"),Collections.singletonList(ClassResolutionProbe.capture('\
        '"org.uma.jmetal.util.research.model.FactoryCachePotential")));')
    body=replace(body,'        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));',
        '        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));\n'
        '        lines(out.resolve("factory-cache-potential.json"),Collections.singletonList(FactoryCachePotential.diagnostics()));')
    (source/'FactoryCachePotentialRun.java').write_text(body,encoding='utf-8')
    shutil.copy2(ROOT/'src/algorithms/diagnostics/FactoryCachePotential.java',source)
    shutil.copy2(Path(__file__),source)
    base=(ENTRY/'classpath.txt').read_text('utf-8')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{base}';(root/'classpath.txt').write_text(cp,encoding='utf-8');return cp


def compare(old,current):
    a,b=(rows(path/'run-receipt.jsonl')[0] for path in (old,current))
    assert a['paidSHA256']==b['paidSHA256'] and a['search']==b['search']
    operations=lambda r:{k:v for k,v in r['decoder'].items() if not k.endswith('Nanos')}
    assert operations(a)==operations(b)
    for name in ('initial-population.jsonl','local-ledger.csv'):assert (old/name).read_bytes()==(current/name).read_bytes()
    def fronts(path):return [(r['checkpoint'],r['front']) for r in rows(path/'anytime.jsonl') if r['checkpointKind']=='FE']
    def genes(path):return [{k:r[k] for k in ('checkpoint','JS','FA','MA','WA','objectives','bornFE')} for r in rows(path/'checkpoint-solutions.jsonl') if r['checkpointKind']=='FE']
    assert fronts(old)==fronts(current) and genes(old)==genes(current)
    potential=rows(current/'factory-cache-potential.json')[0]
    assert potential['evaluations']==LIMIT and potential['originalRecomputedOperations']==b['decoder']['dynamic.recomputedOperations']
    assert potential['timelineDigestsVerified']==potential['additionalHitsBeyondParent'] and potential['entries']<=8192
    write_once(current/'observer-equivalence.json',{'status':'PASS','successfulFEPerArm':LIMIT,'fullPaidSHAEqual':True,
        'allReachedFEFrontsGenomesInitialsLedgerAndCountersEqual':True,'allAdditionalHitsTimelineDigestEqual':True})
    return potential


def main():
    root=ROOT/'runs'/datetime.now().strftime('factory-cache-potential-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('FACTORY_CACHE_POTENTIAL_ROOT',root,flush=True);completed=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(SOURCE/'protocol.json')['instances']
            write_once(root/'protocol.json',{'instances':specs,'seed':SEED,'FELimit':LIMIT,'plannedSuccessfulFE':800000,
                'sampling':'Same2developmentinstances, FULL/NSGA, actual100kFE originalnaturalrecord stopping. ON/OFF pairs, oneJVM atatime.',
                'question':'Beyond the already-reused parent factory/prefix, how many recomputed operations belong to factory sequences paid earlier in this run?',
                'observer':'FrozenDynamicEvaluation unchanged except postdecode callback. Key=ordered(job,firststageMA,WA,factory) chain, fullint equality, fixedcontext. '
                           '8192entryLRU history, no capacity scan. Every originaldecode executes; only read-only counts/digests stored. '
                           'Potential saved work excludes existingparent reuse; independently reconstruct currentincrementaloperation count. '
                           'All extra hit factory fulltimeline SHA256 must match previously paid result. Preparedprefix unsupported and aborts; originalconfig preparedCount0.',
                'engineering':'ON vs originalacceptedentry baseline OFF fullpaidSHA, FEfront/genomes/bornFE, initials, ledger, search anddecoderoperationcounts must equal; '
                              'exclude nondeterministicNanos andtimecheckpointfronts only. Both actual100k successes/zero failures, fullcheckpointQA separate.',
                'gate':'Each of4instance/methodcells potentialSavedRecomputedOperations>=30%oforiginalrecomputedOperations. '
                       'Allnecessary to justify a separate engineering cache implementation. No changinghistorycapacity/FEwindow/seed afterfailure. '
                       'Pass is not measuredspeedup, searchquality or scientificgoal completion.',
                'limits':'Prefix100k only, not whole500kregime. SHAverifiedphysicalidentity, not savedwallclock. '
                         'Observercost belongs to audit, no performance comparison. Keyintegers/timelineopcounts not actualtotalmemory. '
                         'Would count everyfuturecandidateFE evenforcachehits; not a candidate rejection or newselector.',
                'preserved':'No production/defaultsearch, physicalmodel, roles/Q/FA/sharingrule changes. No downloads/transfers.'})
            cp=build(root);results=[]
            for i,spec in enumerate(specs):
                stem=spec['stem'];shutil.copytree(SOURCE/stem/'inputs',root/stem/'inputs')
                for label,template in (('FULL','STRICT_FULL'),('NSGA','NSGA_STRICT')):
                    baseline,receipt=run_case(root,(ENTRY/'classpath.txt').read_text('utf-8'),stem,label+'-OFF',template,'record',SEED,limit=LIMIT,audit=True)
                    completed.append((baseline,receipt));out=root/stem/(label+'-ON');out.mkdir()
                    cmd=command(root,cp,stem,label+'-ON',template,'record',SEED,limit=LIMIT,audit=True)
                    cmd[cmd.index('research.dynamic.NaturalLocalRun')]='research.dynamic.FactoryCachePotentialRun'
                    cmd=override(cmd,'research.factoryCache.observe','true');write_once(out/'command.json',cmd)
                    print('FACTORY_CACHE_OBSERVER',stem,label,flush=True);execute(cmd,out/'run.log',timeout=300)
                    receipt=verify(out,float('inf'),LIMIT,'record');completed.append((out,receipt))
                    info=compare(baseline,out);results.append({'stem':stem,'method':label,'potential':info,'gate':info['potentialSavedFraction']>=.3})
            result={'cells':results,'worthCacheEngineering':all(r['gate'] for r in results),'newCacheImplemented':False}
            write_once(root/'analysis.json',result)
    except BaseException as error:
        actual=[rows(p)[0] for p in root.rglob('run-receipt.jsonl')]
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','successfulFE':sum(r['successful'] for r in actual),
            'attemptedFE':sum(r['attempted'] for r in actual),'error':repr(error)});raise
    write_once(root/'status.json',{'status':'COMPLETE','runs':len(completed),'successfulFE':sum(r['successful'] for _,r in completed),
        'attemptedFE':sum(r['attempted'] for _,r in completed),'unexpectedEvaluationFailures':0,
        'checkpointFullDecoderQA':sum(read(p/'checkpoint-validation.json')['uniqueOfflineDecodes'] for p,_ in completed),
        'worthCacheEngineering':result['worthCacheEngineering']})
    print('FACTORY_CACHE_POTENTIAL_COMPLETE',[(r['stem'],r['method'],r['potential']['potentialSavedFraction']) for r in results],result['worthCacheEngineering'],flush=True)


if __name__=='__main__':main()
