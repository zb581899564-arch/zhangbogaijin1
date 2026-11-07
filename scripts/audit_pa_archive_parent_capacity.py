"""Independent source chronology, scalar dominance and sparse maximum-matching checks."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'

from collections import Counter
from pathlib import Path
import json
import shutil
import sys
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching

from run_long_budget_bridge import ROOT,read,rows,write_once
from run_qpa_complete_engineering import protected
from research.semantic_repair.evidence import digest


def dominates(a,b):return all(x<=y for x,y in zip(a,b)) and any(x<y for x,y in zip(a,b))


def check_snapshot(snapshot,catalog):
    live=[catalog[str(fe)] for fe in snapshot['populationFE']];archive=[catalog[str(fe)] for fe in snapshot['archiveFE']]
    assert len(live)==len(set(snapshot['populationFE']))==100
    assert len(archive)==len(set(snapshot['archiveFE']))==len({p['physicalHash'] for p in archive})
    assert all(p['paidFE']<=snapshot['asOfPaidFE'] for p in live+archive)
    matrix=np.zeros((len(snapshot['parentSlots']),len(archive)),dtype=np.int8)
    ordinary=matrix.copy();live_hash={p['physicalHash'] for p in live}
    for at,(slot,row) in enumerate(zip(snapshot['parentSlots'],snapshot['assessment']['rows'])):
        p=live[slot];ld=[v['paidFE'] for v in live if dominates(v['objectives'],p['objectives'])]
        ad=[v['paidFE'] for v in archive if dominates(v['objectives'],p['objectives'])];exclusive=not ld and bool(ad)
        assert row['slot']==slot and row['parentFE']==p['paidFE'] and row['liveDominatorFE']==ld and row['archiveDominatorFE']==ad
        assert row['archiveOnly']==exclusive and row['archiveOnlyWitnessFE']==(ad if exclusive else [])
        assert row['extraPhysicalDominatorFE']==[v['paidFE'] for v in archive if v['paidFE'] in ad and v['physicalHash'] not in live_hash]
        if exclusive:
            for col,v in enumerate(archive):
                if v['paidFE'] in ad:matrix[at,col]=1;ordinary[at,col]=not v['strictSpecialistProduced']
    sizes=[]
    for edges,key,size_key in ((matrix,'matchingAll','maximumMatches'),(ordinary,'matchingWithoutSpecialists','maximumMatchesWithoutSpecialists')):
        maximum=maximum_bipartite_matching(csr_matrix(edges),perm_type='column');size=int(np.sum(maximum>=0));sizes.append(size)
        pairs=snapshot['assessment'][key]
        assert len(pairs)==size==snapshot['assessment'][size_key]
        assert len({p['slot'] for p in pairs})==len({catalog[str(p['donorFE'])]['physicalHash'] for p in pairs})==size
        for pair in pairs:assert edges[snapshot['parentSlots'].index(pair['slot']),snapshot['archiveFE'].index(pair['donorFE'])]
    assert snapshot['assessment']['extraSpecialistMatches']==sizes[0]-sizes[1]


def source_chronology(spec,case):
    catalog=case['catalog'];snapshots=iter(case['snapshots']);live=[];archive={};paid=0;count=0;seen_catalog=set()
    def capture(kind,generation):
        nonlocal count
        snap=next(snapshots);assert snap['kind']==kind and snap['generation']==generation and snap['asOfPaidFE']==paid
        assert snap['populationFE']==live and snap['archiveFE']==list(archive.values());count+=1
        check_snapshot(snap,catalog)
    with (Path(spec['source'])/'events.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            event=json.loads(line);kind=event['kind']
            if kind=='model':capture('MODEL',event['generation'])
            if kind=='step' and event['step']==0 and event['role']=='CENTER':capture('PROGRAM',event['generation'])
            if kind not in ('initial','step'):continue
            paid+=1;assert paid==event['paidFE'];key=str(paid)
            if key in catalog:
                p=catalog[key];producer='INITIAL' if paid<=100 else event['role']
                assert p['paidFE']==paid and p['objectives']==event['objectives'] and p['producer']==producer
                assert p['strictSpecialistProduced']==(spec['mode']!='NO_SPECIALIST' and producer not in ('INITIAL','CENTER'))
                assert len(p['physicalHash'])==64;seen_catalog.add(key)
            if event['archiveFresh']:
                objective=tuple(event['objectives']);archive={obj:fe for obj,fe in archive.items() if not dominates(objective,obj)}
                assert objective not in archive;archive[objective]=paid
            assert len(archive)==event['archiveSizeAfter']
            if kind=='initial':assert event['slot']==len(live);live.append(paid)
            elif event['accepted']:live[event['slot']]=paid
    assert next(snapshots,None) is None and count==112 and len(seen_catalog)==len(catalog)
    receipt,=rows(Path(spec['source'])/'receipt.jsonl')
    assert paid==case['paidRowsReplayed']==receipt['successfulFE'] and case['sourcePaidSHA256']==receipt['paidSHA256']
    assert set(archive)=={tuple(p['objectives']) for p in receipt['lastValidFront']}


def check_summary(case,plan):
    catalog=case['catalog'];programs=[s for s in case['snapshots'] if s['kind']=='PROGRAM']
    assert [(s['generation'],s['parentSlots']) for s in programs]==[(g,[slot]) for g in (1,2) for slot in range(15,70)]
    jobs=int(case['instance'].split('_')[0]);program=2*jobs-1
    for s in case['snapshots']:
        expected=100+(s['generation']-1)*100*program
        if s['kind']=='PROGRAM':expected+=s['parentSlots'][0]*program
        assert s['asOfPaidFE']==expected
    opportunities=[s for s in programs if s['assessment']['rows'][0]['archiveOnly']]
    witnesses={catalog[str(fe)]['physicalHash'] for s in opportunities for fe in s['assessment']['rows'][0]['archiveOnlyWitnessFE']}
    generations=sorted({s['generation'] for s in opportunities});fraction=len(opportunities)/110
    model,=[s for s in case['snapshots'] if s['kind']=='MODEL' and s['generation']==2];m=model['assessment'];t=plan['generalThresholds']
    expected=dict(centerPrograms=110,archiveDominatingPrograms=sum(bool(s['assessment']['rows'][0]['archiveDominatorFE']) for s in programs),
        liveDominatingPrograms=sum(bool(s['assessment']['rows'][0]['liveDominatorFE']) for s in programs),archiveOnlyPrograms=len(opportunities),
        archiveOnlyProgramFraction=fraction,distinctPhysicalWitnesses=len(witnesses),opportunityGenerations=generations,
        generation2MaximumMatches=m['maximumMatches'],generation2MatchesWithoutSpecialists=m['maximumMatchesWithoutSpecialists'],generation2ExtraSpecialistMatches=m['extraSpecialistMatches'])
    checks=dict(programFraction=fraction>=t['archiveOnlyProgramFraction'],distinctWitnesses=len(witnesses)>=t['distinctPhysicalWitnesses'],
        generation2Matching=m['maximumMatches']>=t['generation2InjectiveMatches'],bothGenerations=generations==t['opportunityGenerations'])
    expected.update(generalChecks=checks,generalPass=all(checks.values()),specialistSupplyPass=m['extraSpecialistMatches']>=plan['specialistThresholds']['generation2ExtraMatchesBeyondNonSpecialists'])
    assert case['summary']==expected


def audit(root):
    protocol=read(root/'protocol.json');plan=protocol['contract'];result=read(root/'analysis.json')
    assert read(root/'status.json')['status']=='COMPLETE' and protected()==protocol['protectedBefore']
    assert digest(ROOT/'research/gomea_reference_audit/PA_ARCHIVE_PARENT_CAPACITY_V1.json')==protocol['contractSHA256']
    for name,sha in read(root/'source-hashes.json').items():assert digest(root/'source'/name)==sha
    for key,sha in (('sourceEngineering','sourceEngineeringAuditSHA256'),('precedingScience','precedingScienceAuditSHA256')):
        assert digest(Path(plan[key])/'independent-final-audit.json')==plan[sha]
    checked=[]
    for spec,item in zip(plan['cases'],result['cases']):
        for name,sha in spec['sourceHashes'].items():assert digest(Path(spec['source'])/name)==sha
        case=read(root/item['evidence']);assert case['instance']==spec['instance'] and case['mode']==spec['mode'] and case['primary']==spec['primary']
        source_chronology(spec,case);check_summary(case,plan)
        assert item['summary']==case['summary'] and case['knownMixedGenomesRebuilt']==case['paidRowsReplayed']-100 and case['neutralViewsVerified']==200
        checked.append(dict(instance=spec['instance'],mode=spec['mode'],chronologyDominanceAndIndependentMaximumMatchingPassed=True))
    general=all(c['summary']['generalPass'] for c in result['cases'] if c['primary']);special=all(c['summary']['specialistSupplyPass'] for c in result['cases'] if c['primary'])
    assert result['generalCapacityPass']==general and result['specialistCapacityPass']==special
    expected='STOP_FIXED_ARCHIVE_PARENT_CAPACITY' if not general else 'GENERAL_AND_SPECIAL_CAPACITY_ONLY' if special else 'ORDINARY_ARCHIVE_CAPACITY_ONLY_NO_SPECIAL_SUPPLY'
    assert result['decision']==expected and result['existingPaidRowsReplayed']==143400 and result['knownMixedGenomesRebuilt']==142800 and result['centerPrograms']==660
    assert result['newSearchFE']==result['newObjectiveQueries']==result['newDecoderCalls']==0
    write_once(root/'independent-final-audit.json',dict(passed=True,cases=checked,sourceSnapshotsIndependentlyChecked=672,
        independentDominanceChronologyProvenanceAndMatchingVerified=True,newSearchFE=0,newObjectiveQueries=0,newDecoderCalls=0,performanceProved=False,goalAchieved=False))
    folder=root/'independent-audit-source';folder.mkdir();shutil.copy2(Path(__file__),folder)
    print('ARCHIVE_PARENT_CAPACITY_FINAL_AUDIT_PASS',672,'snapshots,0newFE/queries/decoder',flush=True)


if __name__=='__main__':audit(Path(sys.argv[1]).resolve())
