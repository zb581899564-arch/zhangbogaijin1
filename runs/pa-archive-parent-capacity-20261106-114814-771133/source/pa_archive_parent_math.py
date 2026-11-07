"""Strict all-objective parent opportunities and injective known-state capacity."""
import numpy as np


def matching(edges):
    """Deterministic augmenting paths; rows are parent slots, columns archival states."""
    owner={}
    def augment(row,seen):
        for col in edges[row]:
            if col in seen:continue
            seen.add(col)
            if col not in owner or augment(owner[col],seen):owner[col]=row;return True
        return False
    for row in range(len(edges)):augment(row,set())
    return sorted((row,col) for col,row in owner.items())


def analyze_snapshot(snapshot,catalog):
    live=[catalog[str(fe)] for fe in snapshot['populationFE']];archive=[catalog[str(fe)] for fe in snapshot['archiveFE']]
    assert len(live)==len(set(snapshot['populationFE']))==100
    assert len({p['physicalHash'] for p in archive})==len(archive)
    assert all(p['paidFE']<=snapshot['asOfPaidFE'] for p in live+archive)
    lp=np.asarray([p['objectives'] for p in live]);ap=np.asarray([p['objectives'] for p in archive]);live_physical={p['physicalHash'] for p in live}
    rows=[];all_edges=[];ordinary_edges=[]
    for slot in snapshot['parentSlots']:
        parent=live[slot];obj=np.asarray(parent['objectives'])
        li=np.flatnonzero(np.all(lp<=obj,axis=1)&np.any(lp<obj,axis=1))
        ai=np.flatnonzero(np.all(ap<=obj,axis=1)&np.any(ap<obj,axis=1))
        exclusive=len(li)==0 and len(ai)>0;eligible=ai.tolist() if exclusive else []
        if exclusive:assert all(archive[i]['physicalHash'] not in live_physical for i in eligible)
        all_edges.append(eligible);ordinary_edges.append([i for i in eligible if not archive[i]['strictSpecialistProduced']])
        rows.append(dict(slot=slot,parentFE=parent['paidFE'],liveDominatorFE=[live[i]['paidFE'] for i in li],
            archiveDominatorFE=[archive[i]['paidFE'] for i in ai],archiveOnly=exclusive,
            archiveOnlyWitnessFE=[archive[i]['paidFE'] for i in eligible],
            extraPhysicalDominatorFE=[archive[i]['paidFE'] for i in ai if archive[i]['physicalHash'] not in live_physical]))
    pack=lambda result:[dict(slot=snapshot['parentSlots'][row],donorFE=archive[col]['paidFE']) for row,col in result]
    full,ordinary=matching(all_edges),matching(ordinary_edges);assert len(full)>=len(ordinary)
    return dict(rows=rows,matchingAll=pack(full),matchingWithoutSpecialists=pack(ordinary),
        maximumMatches=len(full),maximumMatchesWithoutSpecialists=len(ordinary),extraSpecialistMatches=len(full)-len(ordinary))


def summarize(snapshots,catalog,plan):
    programs=[s for s in snapshots if s['kind']=='PROGRAM'];assert len(programs)==110
    opportunities=[s for s in programs if s['assessment']['rows'][0]['archiveOnly']]
    witnesses={catalog[str(fe)]['physicalHash'] for s in opportunities for fe in s['assessment']['rows'][0]['archiveOnlyWitnessFE']}
    generations=sorted({s['generation'] for s in opportunities});fraction=len(opportunities)/len(programs)
    model,=[s for s in snapshots if s['kind']=='MODEL' and s['generation']==2];m=model['assessment'];t=plan['generalThresholds']
    checks=dict(programFraction=fraction>=t['archiveOnlyProgramFraction'],distinctWitnesses=len(witnesses)>=t['distinctPhysicalWitnesses'],
        generation2Matching=m['maximumMatches']>=t['generation2InjectiveMatches'],bothGenerations=generations==t['opportunityGenerations'])
    return dict(centerPrograms=len(programs),archiveDominatingPrograms=sum(bool(s['assessment']['rows'][0]['archiveDominatorFE']) for s in programs),
        liveDominatingPrograms=sum(bool(s['assessment']['rows'][0]['liveDominatorFE']) for s in programs),archiveOnlyPrograms=len(opportunities),
        archiveOnlyProgramFraction=fraction,distinctPhysicalWitnesses=len(witnesses),opportunityGenerations=generations,
        generation2MaximumMatches=m['maximumMatches'],generation2MatchesWithoutSpecialists=m['maximumMatchesWithoutSpecialists'],
        generation2ExtraSpecialistMatches=m['extraSpecialistMatches'],generalChecks=checks,generalPass=all(checks.values()),
        specialistSupplyPass=m['extraSpecialistMatches']>=plan['specialistThresholds']['generation2ExtraMatchesBeyondNonSpecialists'])
