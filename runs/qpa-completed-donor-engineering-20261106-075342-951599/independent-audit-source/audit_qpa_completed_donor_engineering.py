"""Terminal, artifact and accounting audit of the accepted donor-feedback engineering matrix."""
from pathlib import Path
import sys

from run_long_budget_bridge import read,rows,write_once
from run_qpa_complete_engineering import protected,fees
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes
from frozen_classpath_identity import verify_capture
from qpa_feedback_engineering import trajectory


def audit(root):
    protocol=read(root/'protocol.json');plan=protocol['contract'];source=Path(plan['source']);cp=(root/'classpath.txt').read_text('utf-8-sig').strip()
    assert read(root/'status.json')['engineeringPass'] and protected()==protocol['protectedBefore']
    assert digest(Path('src/algorithms/model_global/qpa/QpaPopulation.java'))==protocol['originalQpaPopulationSHA256']
    assert class_hashes(root/'classes')==read(root/'class-hashes.json')
    for name,sha in read(root/'source-hashes.json').items():assert digest(root/'source'/name)==sha
    old=(source/'source/QpaPopulation.java').read_text('utf-8-sig');new=(root/'source/QpaPopulation.java').read_text('utf-8-sig')
    expression='QpaIndividual donor = QpaCompletedDonors.choose(parents, offspring, donorSlot, working.role);'
    assert new.count(expression)==1 and new.replace(expression,'QpaIndividual donor = parents.get(donorSlot);')==old
    totals=fees(root);assert totals['successfulFE']==totals['attemptedFE']==totals['paidFullTimelineQA']==plan['plannedActualSearchFE']
    assert totals['failedFE']==0 and totals['receiptCount']==12
    results=[]
    for spec in plan['instances']:
        stem=spec['stem'];base=root/stem;sync=trajectory(base/'SYNC');native=trajectory(source/stem/'main');assert sync==native
        initial=rows(base/'SYNC/initial-population.jsonl')
        for name,sha in read(base/'input-hashes.json').items():assert digest(base/'inputs'/name)==sha==digest(source/stem/'inputs'/name)
        for folder in sorted(p for p in base.iterdir() if p.is_dir() and (p/'receipt.jsonl').exists()):
            receipt,=rows(folder/'receipt.jsonl');assert receipt['attemptedFE']==receipt['successfulFE']==receipt['paidFullTimelineQA']==receipt['decoder']['dynamic.evaluations']
            assert receipt['failedFE']==0 and rows(folder/'initial-population.jsonl')==initial[:min(100,receipt['successfulFE'])]
            capture,=rows(folder/'loaded-identity.jsonl');verify_capture(capture,cp)
            helper,=rows(folder/'completed-donor-identity.jsonl');verify_capture(helper['identity'],cp)
            mode=helper['reads']['mode'];trace=trajectory(folder)
            if mode!='SYNC':
                proof=read(folder/'independent-replay.json');assert proof['passed'] and proof['paidSHA256']==receipt['paidSHA256']
                if trace['firstFreshFE'] is not None:assert trace['raw'][:trace['firstFreshFE']-1]==sync['raw'][:trace['firstFreshFE']-1]
                if folder.name in ('OWN','ALL'):
                    assert trace['drawSHA256']==sync['drawSHA256'] and trace['activeSubsets']==sync['activeSubsets']
                    assert receipt['completedGenerations']==1 and receipt['successfulFE']==spec['firstGenerationFE']
                else:
                    limit=receipt['successfulFE'];main=read(base/'ALL/independent-replay.json')
                    assert receipt['paidSHA256']==main['prefixSHA256'][str(limit)]
                    if limit!=101:assert receipt['phase']==(1 if limit==spec['cuts'][1] else 2)
            if mode in ('SYNC','OWN'):assert helper['reads']['crossRoleFreshMaskReads']==0
            results.append(dict(run=str(folder.relative_to(root)),mode=mode,successfulFE=receipt['successfulFE'],
                freshMaskReads=helper['reads']['freshMaskReads'],crossRoleFreshMaskReads=helper['reads']['crossRoleFreshMaskReads'],
                nativePrefixAndDonorClosureChecked=True,loadedClassesChecked=True))
    assert len(results)==12
    write_once(root/'independent-final-audit.json',dict(passed=True,onlyOneDonorFetchExpressionChanged=True,runs=results,**totals,
        firstGenerationRngSchedulesAndPreFreshPrefixesEqual=True,loadedClassesInputsProtectedMainlineEqual=True,
        newSearchFE=0,newDecoderCalls=0,performanceProved=False,goalAchieved=False))
    print('QPA_DONOR_ENGINEERING_FINAL_AUDIT_PASS',totals,flush=True)


if __name__=='__main__':audit(Path(sys.argv[1]).resolve())
