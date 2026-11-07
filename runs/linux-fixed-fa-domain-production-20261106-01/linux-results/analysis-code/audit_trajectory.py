"""Rebuild every proposal, role acceptance, original pool and reporting archive."""
from collections import Counter
import hashlib
from common import read,lines
from audit_generation import domain_check,joint,outside


def replay(folder,context,receipt,helpers):
    from audit_inputs import RAW,FACTORY,PROPOSAL,check_raw,check_factory,raw,same
    from audit_moves import initial_rng,check_models,expected_proposal
    from audit_pool import PoolLedger,decision,check_assembly
    before,after,models=[read(folder/n) for n in ('before.json','after.json','models.json')]
    seed=receipt['seed'];rng,orders=initial_rng(context,before,models,seed,helpers);check_models(context,before,models)
    domain=domain_check(read(folder/'domain.json'),before,context['stem'],seed)
    new_rng=helpers['JavaRandom'](seed^0x4f2a91);catalog=domain['catalog']
    for p in before:helpers['verify_encoding'](p,catalog,context['factories'])
    live={r['slot']:r for r in before};slots=list(live);pool=PoolLedger(context)
    initial=pool.snapshot();initial['initialSelection']=pool.select(context['actual'])
    same(read(folder/'initial-pools.json'),initial,'Initial pool changed')
    ledger=helpers['ParetoLedger'](context['background']);digest=hashlib.sha256();counts=Counter();status=Counter()
    per_slot=[0]*5;paid=lines(folder/'paid.jsonl');steps=lines(folder/'steps.jsonl');production=receipt['plannedProductionFE']
    assert len(paid)==receipt['successful'] and len(steps)==min(len(paid),production)
    for fe,p in enumerate(paid,1):
        assert p['fe']==fe;check_raw(p,context);check_factory(p,context['factories'])
        size=len(ledger.points);flags=ledger.offer(p['objectives'])
        expected_flags=dict(dominated=flags['dominated'],equal=flags['equal'],fresh=flags['admitted'],archiveBefore=size,archiveAfter=len(ledger.points))
        for k,v in expected_flags.items():same(p[k],v,'Archive flag '+k)
        helpers['update_paid_digest'](digest,p)
        if str(fe) in receipt['prefixSHA256']:assert receipt['prefixSHA256'][str(fe)]==digest.hexdigest()
        if fe<=production:
            expected=expected_proposal(fe,live,slots,models,rng,orders,context);step=steps[fe-1]
            for k in PROPOSAL:
                if k=='mask':continue
                same(p[k],expected[k],'Proposal '+k);same(step[k],expected[k],'Step '+k)
            assert p['fosMask']==step['fosMask']==expected['mask']
            assert p['donorUsedForProposal']==step['donorUsedForProposal']==(receipt['arm']=='GOM')
            parent,donor=live[expected['slot']],live[expected['donorSlot']]
            if receipt['arm']=='GOM':
                assert step['mask']==expected['mask'];helpers['verify_mix'](parent,donor,step,catalog,context['factories'])
            else:
                resources,keys,meta=joint(parent,receipt['arm'],new_rng,domain)
                same(step['generation'],meta,'Independent joint generator')
                assert step['resources']==resources and step['keys']==keys and step['mask']==meta['jobs']
                assert not step['fallback'];helpers['verify_encoding'](step,catalog,context['factories'])
            assert p['generation']==step['generation'] and p['mask']==step['mask']
            assert raw(step)==raw(p) and step['parentObjectives']==parent['objectives']
            result=decision('ROLE',expected['role'],p,parent,context['actual'],flags['dominated'])
            for k,v in dict(result,**expected_flags).items():same(step[k],v,'Acceptance '+k)
            assert step['candidateId']==100+fe
            counts[result['acceptanceReason']]+=1;counts['proposed.'+expected['role']]+=1
            if result['accepted']:
                counts['accepted.'+expected['role']]+=1
                live[expected['slot']]=dict(step,**{k:p[k] for k in FACTORY},stateId=100+fe,paidFE=fe,
                    family=context['actual']['family'],sourcePaidByFE=parent['sourcePaidByFE'])
            if result['candidateViolation']==0:counts['candidateFeasible']+=1
            per_slot[expected['receiver']]+=1
            status[outside(step,domain)]+=1
        else:
            assembly=read(folder/'assembly.json');assert assembly['fe']==production+1
            # Reuse the original selector verifier after explicitly validating the new terminal FE.
            check_assembly(dict(assembly,fe=512),p,pool.select(context['actual']),context)
        pool.observe(p)
    assert receipt['paidSHA256']==digest.hexdigest() and receipt['acceptance']==dict(counts)
    assert receipt['perReceiverFE']==per_slot and read(folder/'final-pools.json')==pool.snapshot()
    assert sorted(map(tuple,read(folder/'front.json')))==sorted(map(tuple,ledger.points))
    for actual,slot in zip(after,slots):
        for k in RAW+FACTORY+('resources','keys','stateId','paidFE','family','sourcePaidByFE','role'):
            same(actual[k],live[slot][k],'Final working state '+k)
    if len(paid)<=production:assert read(folder/'assembly.json')=={'performed':False}
    if not receipt['failed']:assert receipt['pending'] is None
    return dict(paidRows=len(paid),productionRows=len(steps),membership=dict(status),
        exactRNG=True,allCandidateVectors=True,roleAcceptance=True,originalPool=True,allPaidArchive=True)
