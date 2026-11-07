"""Freeze complete natural-trajectory read-only FA accounting; no mechanism or budget change."""
from datetime import datetime
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from factory_assignment_audit_build import ENTRY,build
from factory_assignment_audit_analysis import analyze
from natural_local_support import run_case,command,verify

SOURCE=ROOT/'runs/natural-regime-bench-20261105-073626-086353'
SEED=12390003


def compare(old,current,original):
    a,b=(rows(p/'run-receipt.jsonl')[0] for p in (old,current))
    assert a['paidSHA256']==b['paidSHA256'] and a['search']==b['search']
    operations=lambda r:{k:v for k,v in r['decoder'].items() if not k.endswith('Nanos')}
    assert operations(a)==operations(b)
    for name in ('initial-population.jsonl','local-ledger.csv'):assert (old/name).read_bytes()==(current/name).read_bytes()==(original/name).read_bytes()
    def fronts(p):return [(r['checkpoint'],r['front']) for r in rows(p/'anytime.jsonl') if r['checkpointKind']=='FE']
    def genes(p):return [{k:r[k] for k in ('checkpoint','JS','FA','MA','WA','objectives','bornFE')} for r in rows(p/'checkpoint-solutions.jsonl') if r['checkpointKind']=='FE']
    assert fronts(old)==fronts(current)==fronts(original) and genes(old)==genes(current)==genes(original)
    prior=rows(original/'run-receipt.jsonl')[0];assert b['search']==prior['search'] and operations(b)==operations(prior)
    info=rows(current/'fa-audit.jsonl')[0]
    assert info['status']=='PASS' and info['successfulFE']==500000 and info['unknownParentHints']==info['protectedActualFAChanges']==0
    write_once(current/'observer-equivalence.json',{'status':'PASS','fullPaidSHAEqualOriginalEntryOFF':True,
        'frozenOriginalFrontsGenesInitialsLedgerSearchAndDecodeOperationsEqual':True,'successfulFEPerArm':500000,
        'parentHintsAllEarlierPaid':True,'protectedActualFAUnchanged':True})


def main():
    root=ROOT/'runs'/datetime.now().strftime('factory-assignment-audit-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('FACTORY_ASSIGNMENT_AUDIT_ROOT',root,flush=True);completed=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(SOURCE/'protocol.json')['instances']
            write_once(root/'protocol.json',{'instances':specs,'seed':SEED,'successfulFEPerRun':500000,'plannedSuccessfulFE':4000000,
                'question':'How much actual physical job-to-factory change is attempted/evaluated, suppressed by family restoration, accepted locally, and associated with sequential external archive gains?',
                'design':'2existingdevelopmentinstances * FULL/NSGA * originalOFF/read-onlyON, eachnaturalrecord500k. SequentialsingleJVM. '
                         'Everychild retains originalsearch rules; no newselector, acceptance, generator, cache, sharedpool or budgets.',
                'measurement':'Compare FA byjob identity, not position. Capture rawintention beforefamilyrestore then actual afterrestore/commonrepair. '
                              'Parenthint DynamicSchedule comes from copied first/current parent in auditedfrozenkernels; weak paididentity map must prove earlierpaidFE. '
                              'Every noninitial parent must be known; protected actualFA changes0, intra physicalFA changes0. '
                              'Recordstage/role/freeprotected/changedjobs/newFA perpaidcandidate and everyarchiveadmission; observe realinteracceptance afterunchangeddecision.',
                'engineering':'6zeroDecoderencodingfixtures. ON/OFF fullpaidSHA, allcommonFEfronts/genomes/birthFE, initials, ledger andsearch/decodeoperationcounts identical. '
                              'Also match originalfrozen500k artifacts; exclude nondeterministicNanos andactualtimefronts. Allcounts close tosuccessful500k.',
                'metrics':'Primarycommon frozenHVref1.5. Reconstructexternalarchive fromalladmissionevents, exactlymatch everyFEfront. '
                          'Sequential peradmissionHV credit bystage/role/protection/FAclass, totals telescope. '
                          'Dedicatednumeric3Dsweep verified with67fixturefronts*3refs and up16systematicactualfronts perrun againstexistingindependentHV. '
                          'RawFA changes canceledbyrestoration are counted, never asactualfactorymoves. Initializationexcluded fromsearchFEshares andgainshares.',
                'descriptivePrediction':'On20_8, FAchangingcandidates<=5%postinitialFE but>=30%postinitialHVincrements, '
                                        'and FAHVshare exceeds100_2 by>=10percentagepoints, inBOTHFULL/NSGA. '
                                        'This physicallymotivated contrast is developmental, not independentconfirmation or a trigger toalterbudget. '
                                        'Ifsupported, onlydesigna separate fixedparent pairedcontinuation question; otherwise no broad reallocationhypothesis.',
                'limits':'Existingseed used because exactfrozenreference available. Admissioncredit follows actualorder, not causal or orderfree. '
                         'FAchangingmovesmayalsochangeJS/resources. No isolatedFAeffect, beta0control, same-time quality or novelty claim. '
                         'No seed/window/threshold/role retuning torescue a missedprediction.',
                'preserved':'Production/defaultmainline, originalmaterials, frozenrecords, physics/Q/family/sharing unchanged. No externaldownload/transfer.'})
            cp=build(root);execute(['java','-cp',cp,'org.uma.jmetal.util.research.search.FactoryAssignmentChecks'],root/'encoding-checks.log')
            for spec in specs:
                stem=spec['stem'];shutil.copytree(SOURCE/stem/'inputs',root/stem/'inputs')
                for method,template,original in (('FULL','STRICT_FULL','FULL_NAT'),('NSGA','NSGA_STRICT','NSGA_NAT')):
                    baseline,receipt=run_case(root,(ENTRY/'classpath.txt').read_text('utf-8'),stem,method+'-OFF',template,'record',SEED,audit=True)
                    completed.append((baseline,receipt));out=root/stem/(method+'-ON');out.mkdir()
                    cmd=command(root,cp,stem,method+'-ON',template,'record',SEED,audit=True)
                    cmd[cmd.index('research.dynamic.NaturalLocalRun')]='research.dynamic.FactoryAssignmentRun'
                    write_once(out/'command.json',cmd);print('FACTORY_ASSIGNMENT_OBSERVER',stem,method,flush=True)
                    execute(cmd,out/'run.log',timeout=600);receipt=verify(out,float('inf'),500000,'record');completed.append((out,receipt))
                    compare(baseline,out,SOURCE/stem/('FE-'+original))
            result=analyze(root,specs)
    except BaseException as error:
        actual=[rows(p)[0] for p in root.rglob('run-receipt.jsonl')]
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','successfulFE':sum(r['successful'] for r in actual),
            'attemptedFE':sum(r['attempted'] for r in actual),'error':repr(error)});raise
    write_once(root/'status.json',{'status':'COMPLETE','runs':len(completed),'successfulFE':sum(r['successful'] for _,r in completed),
        'attemptedFE':sum(r['attempted'] for _,r in completed),'unexpectedEvaluationFailures':0,
        'checkpointFullDecoderQA':sum(read(p/'checkpoint-validation.json')['uniqueOfflineDecodes'] for p,_ in completed),
        'supportsAllocationContinuationQuestion':result['supportsAllocationContinuationQuestion']})
    print('FACTORY_ASSIGNMENT_AUDIT_COMPLETE',[(r['stem'],r['method'],r['actualFAChangedFE'],r['FAChangedShareOfPostInitialHVIncrementPct']) for r in result['cases']],flush=True)


if __name__=='__main__':main()
