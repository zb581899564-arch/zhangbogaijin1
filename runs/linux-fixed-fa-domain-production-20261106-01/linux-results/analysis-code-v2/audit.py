"""Isolated independent evidence gate before and after the finite science batch."""
import argparse
from functools import lru_cache
from pathlib import Path
import hashlib
import sys
import time
from urllib.parse import unquote,urlparse
import zipfile
from common import SOURCE,MATURE,ANCHOR,STEMS,SEEDS,ARMS,linux,read,write,sha,lines


@lru_cache(None)
def resolve(cp,name):
    relative=name.replace('.','/')+'.class'
    for entry in cp.split(':'):
        path=Path(entry)
        if path.is_dir() and (path/relative).is_file():return sha(path/relative),str((path/relative).resolve())
        if path.is_file() and zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z:
                if relative in z.namelist():return hashlib.sha256(z.read(relative)).hexdigest(),str(path.resolve())+'!/'+relative
    raise AssertionError(name)


def verify_identity(root):
    cp=(root/'build-01/classpath.txt').read_text().strip();identity=read(root/'build-01/identity.json')
    for entry,expected in identity['dependencies'].items():
        path=Path(entry)
        actual={str(p.relative_to(path)):sha(p) for p in sorted(path.rglob('*')) if p.is_file()} if path.is_dir() else sha(path)
        assert actual==expected,'Frozen dependency changed: '+entry
    actual={str(p.relative_to(root/'build-01/classes')):sha(p) for p in (root/'build-01/classes').rglob('*.class')}
    assert actual==identity['classes'];return cp


def main(root,category):
    linux();start=time.perf_counter();cp=verify_identity(root)
    sys.path.insert(1,str(SOURCE/'audit-analysis-code'));sys.path.insert(2,str(MATURE/'analysis-code'))
    sys.path.insert(3,str(ANCHOR/'payload'))
    from audit_inputs import load_context
    from audit_genome import JavaRandom,physical,verify_encoding,verify_mix
    from audit_replay import ParetoLedger,update_paid_digest
    from audit_trajectory import replay
    helpers=dict(JavaRandom=JavaRandom,physical=physical,verify_encoding=verify_encoding,
        verify_mix=verify_mix,ParetoLedger=ParetoLedger,update_paid_digest=update_paid_digest)
    contexts={};reports=[];totals=dict(attempted=0,successful=0,failed=0,fullQA=0,importQA=0)
    folders=sorted((root/category).glob('*/*/*/receipt.json'))
    assert len(folders)==(19 if category=='engineering' else 18),len(folders)
    for file in folders:
        folder=file.parent;stem,seed,label=folder.relative_to(root/category).parts;receipt=read(file)
        key=stem,seed
        if key not in contexts:
            contexts[key]=load_context(SOURCE,'inputs-v2',stem,seed,'0');contexts[key]['stem']=stem
        context=contexts[key]
        assert receipt['sourceSeed']==int(seed) and receipt['requestIndex']==0 and receipt['seed']==int(seed)^0x37a9185b
        assert read(folder/'before.json')==read(SOURCE/'science'/stem/seed/'0/ROLE/before.json')
        for name,item in receipt['loaded'].items():
            if not isinstance(item,dict):continue
            digest,location=resolve(cp,name);assert item['sha256']==digest,name
            actual=unquote(item['resource']).removeprefix('jar:').removeprefix('file:')
            assert actual==location,(name,actual,location)
        assert receipt['actualRequest']==receipt['effectiveRequest']==context['actual']
        imported=receipt['importQA'];assert imported['sourcePointFullDecodes']==102
        assert imported['retainedRecordFullDecodes']==sum(map(len,context['pools']))
        assert imported['importedCandidatesOfferedToArchive']==imported['qaCombinationsOfferedToArchive']==0
        assert receipt['physicsQA']['fullTimelineChecks']==receipt['successful']
        if receipt['observer']:result=replay(folder,context,receipt,helpers)
        else:
            assert not lines(folder/'paid.jsonl') and not lines(folder/'steps.jsonl')
            reference=folder.parent/receipt['arm'];other=read(reference/'receipt.json')
            assert receipt['paidSHA256']==other['paidSHA256'];result=dict(quietEquivalentTo=str(reference))
        reports.append(dict(instance=stem,seed=int(seed),label=label,**result))
        for name in ('attempted','successful','failed'):totals[name]+=receipt[name]
        totals['fullQA']+=receipt['physicsQA']['fullTimelineChecks']
        totals['importQA']+=imported['sourcePointFullDecodes']+imported['retainedRecordFullDecodes']
        print('DOMAIN_AUDIT_DONE',category,stem,seed,label,flush=True)
    expected=(3590,3589,1) if category=='engineering' else (73728,73728,0)
    assert tuple(totals[k] for k in ('attempted','successful','failed'))==expected
    write(root/(category+'-independent-audit.json'),dict(passed=True,runs=reports,totals=totals,seconds=time.perf_counter()-start,
        physics='Java full timeline verification on every paid success; Python independently reconstructs generation, acceptance and archives',
        identitySHA256=sha(root/'build-01/identity.json')))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--category',choices=['engineering','science'],required=True);a=p.parse_args();main(a.root,a.category)
