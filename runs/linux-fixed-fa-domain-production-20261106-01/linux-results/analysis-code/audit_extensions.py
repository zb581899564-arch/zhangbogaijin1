"""Additional zero-decode counter, paired private-RNG and failed-pending checks."""
import argparse
from pathlib import Path
import sys
from common import SOURCE,MATURE,STEMS,SEEDS,linux,read,write,lines
from audit_generation import domain_check,joint


def main(root):
    linux();sys.path.insert(1,str(SOURCE/'audit-analysis-code'));sys.path.insert(2,str(MATURE/'analysis-code'))
    from audit_genome import JavaRandom
    matched=0;generators=0
    for folder in sorted((root/'science').glob('*/*/*')):
        if not folder.is_dir():continue
        r=read(folder/'receipt.json');steps=lines(folder/'steps.jsonl');g=r['generator']
        assert g['proposalsGenerated']==(0 if r['arm']=='GOM' else len(steps))
        if r['arm']!='GOM':
            unavailable=sum(p['generation']['noveltyUnavailable'] for p in steps)
            assert g['noveltyUnavailable']==unavailable and g['noEligibleFactory']==0
            assert g['novelFirstJobGenerated']==(len(steps)-unavailable if r['arm']=='NOVEL' else 0)
        assert r['paidLogRows']==r['successful'] and r['acceptanceMode']=='ROLE';generators+=1
    for stem in STEMS:
        for seed in SEEDS:
            base=root/'science'/stem/str(seed)
            aa,bb=[lines(base/a/'steps.jsonl') for a in ('LEGAL','NOVEL')]
            for a,b in zip(aa,bb):
                for k in ('factory','jobs','rank1','rank2','key1','key2','resource2'):
                    assert a['generation'][k]==b['generation'][k],k
                matched+=1
    folder=root/'engineering'/STEMS[0]/str(SEEDS[0])/'NOVEL_FAIL_2'
    r=read(folder/'receipt.json');before=read(folder/'before.json');domain=domain_check(read(folder/'domain.json'),before,STEMS[0],r['seed'])
    rng=JavaRandom(r['seed']^0x4f2a91);first=lines(folder/'steps.jsonl')[0]
    joint(before[0],'NOVEL',rng,domain)
    resources,keys,metadata=joint(before[1],'NOVEL',rng,domain)
    assert r['pending']['generation']==metadata and r['pending']['resources']==resources and r['pending']['keys']==keys
    assert r['generator']['proposalsGenerated']==2 and (r['attempted'],r['successful'],r['failed'])==(2,1,1)
    write(root/'generator-extended-audit.json',dict(passed=True,scienceGeneratorReceipts=generators,
        matchedLegalNovelProductionPairs=matched,failedPendingCandidateVerified=True,newFE=0,newDecodes=0))
    print('DOMAIN_EXTENSION_PASS',matched,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);main(p.parse_args().root)
