"""Implement the predeclared common-fixedFA explanatory experiment, without a new complete algorithm."""
from datetime import datetime
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from fixed_fa_build import SOURCE,build
from fixed_fa_inputs import select_contexts
from fixed_fa_execution import METHODS,run,engineering
from fixed_fa_analysis import analyze

SEEDS=(12790003,12790033)


def main():
    root=ROOT/'runs'/datetime.now().strftime('fixedfa-conditional-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('FIXED_FA_CONDITIONAL_ROOT',root,flush=True);completed=[];guard=None
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(SOURCE/'protocol.json')['instances'];contexts={}
            for spec in specs:
                stem=spec['stem'];shutil.copytree(SOURCE/stem/'inputs',root/stem/'inputs');contexts[stem]=select_contexts(root,spec)
            order=[]
            for i,spec in enumerate(specs):
                stem=spec['stem']
                for j,context in enumerate(contexts[stem]):
                    for k,seed in enumerate(SEEDS):
                        methods=list(METHODS);offset=(i+j+k)%len(methods)
                        order.extend({'stem':stem,'contextId':context['contextId'],'seed':seed,'method':m} for m in methods[offset:]+methods[:offset])
            write_once(root/'protocol.json',{'instances':specs,'contexts':contexts,'seeds':SEEDS,'methods':METHODS,'order':order,
                'plannedMechanismSuccessfulFE':len(order)*5100,'plannedOffEngineeringSuccessfulFE':40800,
                'guardFixtureSuccessfulFE':2,'guardFixtureExpectedFailedFE':1,
                'designSource':'docs/共同固定FA条件交叉验证设计-2026-11-05.md; written before new outcomes',
                'question':'Do original four objective duties have conditional JS/MA/WA search value when ALL methods receive exactly the same fixed physical factory assignment?',
                'sourceFASelection':'Natural source seed12390003 atFE5100 FULL/NSGA fronts: C/E/W extrema and frozen normalizedsum minimum; '
                                    'ties bylexfourvectors. ExactFA-byjob dedup, all origin/direction labels retained; no replacement. No original JS/resource warmstart.',
                'adaptation':'Common createSolution overwrites FA-byjob BEFORE family initialization, repairs initialresources only. '
                             'Both actualfrozen JOB_ALIGNED andclassic factorymutation bodies masked, triggerdraws retained. '
                             'Factorycrossover between sameFA-byjob parents preservesassignment; no evaluation projection. Everypaidattempt checks exactFA and aborts drift. '
                             'Original4physicalgroups/Q/sharing/familylabels kept inFULL/UNIFORM, while allfourfamilyassignments nowequalthe target. '
                             'NSGA has originalmating/survival andnofamilysharing. Cannot claim differentFA supply fromidenticalfamilytags.',
                'budget':'Eachrun5100success=100initial+5000global, no paidLS. Sequential singleJVM; all construction/guard/repair/archive costs inside search. '
                         'Complete paid genotype evidence and fullcheckpointQA separate. Guardfixture deliberatethirdattempt failure retained separately.',
                'engineering':'OriginalOFF andmaskOFF pairs each5100, 2instances*2methods; fullpaidSHA/FEfronts/genomes/birthFE/initials/ledger/searchanddecodeoperations exact. '
                              'Guard rejects a different feasibleFA beforedecode atattempt3 after2real successes; lastvalidfront retained and2fullQA. '
                              'Every performancepair sameinitial100genomes/objectives, every attempt fixedFA, no projection and mutationmask actuallytriggered.',
                'metrics':'Common oldnormalization, HV1.5 and1.25/2, percontext/seed NDunionof3arms forIGD+. '
                          'UniqueFA*seed paired medians within eachinstance; duplicate source/direction labels notnewreplicates. ActualFEsearchSeconds not a trueTIMEcomparison.',
                'gate':'Bothinstances: medianFULLvsNSGA HV1.5>=+0.5%, >=60%pairsnonnegative; vsUNIFORM median>=+1%; eachFAorigin medianvsNSGA>=-1%; '
                       'median symmetricIGD+worsening<=5%; mediansearchcostratio<=1.25; refs1.25/2 medianvsNSGA nonnegative. '
                       'Allnecessary; noninformativeHV/failed/missingcases not replaced. Pass only supports further architecture design, no fullalgorithm promotion. '
                       'Failure stopsfixedFAconditionaladvantage hypothesis; no morebudget/templates/seeds/maskvariants torescue.',
                'limits':'Additional sharedfixedFA constraint diagnoses one searchsubproblem; full objective unchanged. No originalFA-budget flag reversal, '
                         'fixedfamilyrefresh, common100parentpool, newsharingselector, beta0specificity, same-time superiority or ESWA claim.',
                'preserved':'No production/defaultmainline, rawmaterial orfrozenrecords modified; no downloads/transfers/publicpush.'})
            cp=build(root)
            execute(['java','-cp',cp,'org.uma.jmetal.util.research.search.FactoryAssignmentChecks'],root/'encoding-checks.log')
            engineering_runs,guard=engineering(root,cp,specs,contexts);completed.extend(engineering_runs)
            for cell in order:
                stem,context_id,seed,method=(cell[k] for k in ('stem','contextId','seed','method'))
                folder=f'{context_id}/{seed}/{method}';target=root/stem/'contexts'/(context_id+'.txt')
                out,receipt=run(root,cp,stem,folder,method,seed,target);completed.append((out,receipt))
                others=[p/'initial-population.jsonl' for p in out.parent.iterdir() if p.is_dir() and (p/'initial-population.jsonl').exists()]
                assert all(p.read_bytes()==others[0].read_bytes() for p in others)
            result=analyze(root,specs,contexts,SEEDS)
    except BaseException as error:
        actual=[rows(p)[0] for p in root.rglob('run-receipt.jsonl')]
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','successfulFEInRunReceipts':sum(r['successful'] for r in actual),
            'attemptedFEInRunReceipts':sum(r['attempted'] for r in actual),'guardFixture':guard,'error':repr(error)});raise
    write_once(root/'status.json',{'status':'COMPLETE','validRuns':len(completed),'mechanismRuns':len(order),
        'uniqueContexts':sum(len(v) for v in contexts.values()),'successfulFE':sum(r['successful'] for _,r in completed)+guard['successfulFE'],
        'attemptedFE':sum(r['attempted'] for _,r in completed)+guard['attemptedFE'],
        'expectedGuardFailures':1,'unexpectedEvaluationFailures':0,
        'checkpointAndGuardFullDecoderQA':sum(read(p/'checkpoint-validation.json')['uniqueOfflineDecodes'] for p,_ in completed)+guard['offlineFullDecoderQA'],
        'supportsConditionalArchitecture':result['supportsConditionalArchitecture']})
    print('FIXED_FA_CONDITIONAL_COMPLETE',[(r['stem'],r['medianFullVsNsgaHVPct'],r['supported']) for r in result['instances']],flush=True)


if __name__=='__main__':main()
