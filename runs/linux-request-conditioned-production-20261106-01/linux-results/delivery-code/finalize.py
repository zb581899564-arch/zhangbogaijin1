"""Reconcile actual costs and seal the completed conditional evidence on Linux."""
import argparse
import importlib.util
from pathlib import Path
import shutil
import sys
from common import ANCHOR, SOURCE, linux, read, sha, write


def costs(root):
    records=[]
    for kind,pattern in [('source','sources/*/*/run-receipt.jsonl'),
                         ('engineering','engineering/*/*/*/*/receipt.json'),
                         ('science','science/*/*/*/*/receipt.json')]:
        for path in sorted(root.glob(pattern)):
            value=read(path);row=dict(kind=kind,path=str(path.relative_to(root)),
                **{k:value[k] for k in ('attempted','successful','failed','searchSeconds')},
                processSeconds=read(path.parent/'process.json')['seconds'])
            imports=value.get('importQA',{})
            row.update(importRestorationDecodes=imports.get('sourcePointFullDecodes',0),
                retainedRecordQADecodes=imports.get('retainedRecordFullDecodes',0),
                importQASeconds=imports.get('sourcePointQASeconds',0)+imports.get('retainedRecordQASeconds',0),
                paidTimelineChecks=value['physicsQA']['fullTimelineChecks'],
                paidTimelineQASeconds=value['physicsQA']['engineeringOnlySeconds'],
                preparationSeconds=value.get('prepareSeconds',0),
                detailedEvidenceSeconds=value.get('paidEvidenceSeconds',0)+value.get('stepEvidenceSeconds',0))
            checkpoint=path.parent/'checkpoint-validation.json'
            qa=read(checkpoint) if checkpoint.exists() else {}
            row.update(checkpointQADecodes=qa.get('uniqueOfflineDecodes',0),
                       checkpointQASeconds=qa.get('offlineValidationSeconds',0))
            records.append(row)
    totals={}
    keys=[k for k,v in records[0].items() if isinstance(v,(int,float))]
    for kind in ('source','engineering','science'):
        subset=[r for r in records if r['kind']==kind]
        totals[kind]=dict(runs=len(subset),**{key:sum(r[key] for r in subset) for key in keys})
    assert [totals[k]['attempted'] for k in ('source','engineering','science')]==[1618320,7176,36864]
    assert sum(v['failed'] for v in totals.values())==2
    result=dict(runs=records,totals=totals,
        allNewAttempts=sum(v['attempted'] for v in totals.values()),
        allNewSuccessful=sum(v['successful'] for v in totals.values()),
        failedAttempts=2,expectedInjectedFailures=2,
        importAndQADecodes=sum(v['importRestorationDecodes']+v['retainedRecordQADecodes']+
                              v['paidTimelineChecks']+v['checkpointQADecodes'] for v in totals.values()),
        offlineSeconds={name:read(root/name).get('seconds',0) for name in
            ('request-audit.json','request-audit-v2.json','engineering-independent-audit.json','science-independent-audit.json')},
        metricSeconds=read(root/'report/analysis.json')['seconds'],
        interpretation='Science/search/prepare/QA/process timings are overlapping categories, not additive wall-clock speedups. Source request-observation time is not separately isolated; no TIME_LIMIT claim')
    write(root/'actual-fees.json',result)
    return result


def identities(root):
    out=root/'dependency-identity';out.mkdir(exist_ok=False)
    for stem in ('20_8_5_1','100_2_3_1'):
        folder=out/'inputs'/stem;folder.mkdir(parents=True)
        for name in (stem+'.txt','RECONSTRUCTED-setup.txt','fatigue-input.txt'):
            shutil.copyfile(ANCHOR/'payload/inputs'/stem/name,folder/name)
    for name in ('protocol.json','delivery-acceptance.json'):
        shutil.copyfile(SOURCE/name,out/('source-'+name))
    metrics={str(p):sha(p) for p in (ANCHOR/'payload/research/pilot_evaluation').glob('*.py')}
    metrics.update({str(SOURCE/'analysis-code'/name):sha(SOURCE/'analysis-code'/name)
                    for name in ('analysis_metrics.py','audit_metrics.py','analysis_common.py')})
    write(out/'identities.json',dict(inputFiles={str(p.relative_to(out)):sha(p) for p in (out/'inputs').rglob('*') if p.is_file()},
        acceptedMetricModules=metrics,sourceAcceptanceSHA256=sha(SOURCE/'delivery-acceptance.json'),
        classDependencyManifest='../capture-build-01/dependencies.json',
        runtimeQualification='Runtime JDK and inherited classpath files remain in previously frozen Linux anchor; identity manifests included, no duplicate runtime binaries'))


def main(root,archive):
    linux()
    required=['engineering-acceptance.json','engineering-independent-audit.json',
              'science-complete.json','science-independent-audit.json','request-audit-v2.json']
    for name in required:assert read(root/name)['passed']
    analysis=read(root/'report/analysis.json');assert analysis['independentHVChecks']==216
    assert (root/'decision.json').is_file() and (root/'report/RESULTS.md').is_file()
    result=costs(root);identities(root)
    write(root/'delivery-acceptance.json',dict(passed=True,requiredReceipts=required,
        scientificRuns=72,scienceFE=36864,scienceFailures=0,allNewAttemptedFE=result['allNewAttempts'],
        allNewSuccessfulFE=result['allNewSuccessful'],expectedInjectedFailures=2,
        independentlyRecomputedHV=216,statisticsPending=False,
        initialSamplingAmendedBeforeAnyProbe=True,defaultMainlineChanged=False,
        newInstanceOrSeed=False,goalResumed=False,fullAlgorithmOrTimeClaim=False,
        newSearchFEAtDelivery=0,newDecodesAtDelivery=0))
    path=ANCHOR/'finalize_delivery.py'
    spec=importlib.util.spec_from_file_location('accepted_packaging',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    module.package(root,archive)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--archive',type=Path,required=True)
    args=parser.parse_args();main(args.root,args.archive)
