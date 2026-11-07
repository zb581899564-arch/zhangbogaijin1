"""Pre-register a fixed-entry, same-FA mechanism probe, not a full optimizer trial."""
import argparse
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from common import SOURCE,CLOSURE,STEMS,SEEDS,ARMS,PRODUCTION,linux,read,write,sha


def main(root):
    linux();root.mkdir(parents=True,exist_ok=False)
    from structure import validate_membership,membership,enumerate_factory
    fixtures=validate_membership()
    tied={j:[(.5,0,0)] for j in range(3)}
    assert list(enumerate_factory([0,1,2],tied)[0])==[((2,0,0),(1,0,0),(0,0,0))]
    assert membership(((0,0,0),(1,0,0),(2,0,0)),tied)[0]=='OUTSIDE_KEY_ORDER'
    assert read(SOURCE/'delivery-acceptance.json')['passed'] and read(CLOSURE/'delivery-acceptance.json')['passed']
    identities=[]
    for stem in STEMS:
        for seed in SEEDS:
            folder=SOURCE/'inputs-v2'/stem/str(seed)/'0'
            before=SOURCE/'science'/stem/str(seed)/'0/ROLE/before.json';rows=read(before)
            tied=defaultdict(set)
            for point in rows:
                for job,key in enumerate(point['keys']):tied[key].add(job)
            ties=sum(len(j)>1 for j in tied.values());assert ties==0
            identities.append(dict(instance=stem,seed=seed,family=rows[0]['family'],crossJobInitialKeyTies=ties,
                sourceBeforeSHA256=sha(before),inputs={p.name:sha(p) for p in folder.iterdir() if p.is_file()}))
    plan=dict(name='FIXED_FA_DOMAIN_PRODUCTION_V1',instances=STEMS,seeds=SEEDS,arms=ARMS,
        source=str(SOURCE),sourceAcceptanceSHA256=sha(SOURCE/'delivery-acceptance.json'),contexts=identities,
        sampledRequest='q0 of every six previously fixed sources; no quality-based resampling',
        anchor='Common mature P100 view; production confined to same five fixed-family slots M1/C2/E1/W1',
        unchanged=['FA','initial mature vectors and objectives','dynamic decoder and inputs','original role acceptance',
            'A0','FactoryPool rules and capacity','actual q0 cap/eta and final original composition'],
        primary='Does explicit outside-support production have material conditional value, and does novelty targeting beat ordinary legal generation?',
        mechanisms=dict(GOM='Original learned factory-block FOS and live-donor paired copying',
            LEGAL='Two jobs in same factory, jointly redraw whole legal resource tuples and independent priorities',
            NOVEL='Same jobs, ranks, keys and costs as LEGAL; first tuple selected from complement of initial five donor tuples, or declared ordinary fallback if empty'),
        sampling='Uniform eligible factory, uniform first job, uniform other job; two tuple ranks and two priority draws; no objective filtering, retries, or hidden prefix decoding',
        RNG='Original source seed xor0x37a9185b for GOM bookkeeping; new joint generator uses that seed xor0x4f2a91; matched LEGAL/NOVEL random stream',
        distinctionTyped='No fieldwise inheritance from observed donor M/W/key marginals; whole legal tuples and fresh keys, two jobs jointly; old TYPED stop preserved',
        distinctionRenewal='Never changes FA, family membership, history by reset, or pool initialization; no ELITE/RANDOM renewal',
        qualityScope='Conditional production probe on reused development sources; not complete four-group competition, independent validation or novelty proof',
        productionFE=PRODUCTION,assemblyFE=1,perArmFE=PRODUCTION+1,scienceRuns=18,scienceFE=18*(PRODUCTION+1),
        engineering='Six GOM511+assembly bridges versus frozen ROLE; LEGAL/NOVEL production63+assembly on both instances; first-instance prefix1/2/63 and quiet64 for both; one NOVEL failure2',
        engineeringAttemptFE=3590,expectedEngineeringFailures=1,
        sequential=True,fullPaidTimelineQA=True,timeComparison=False,
        metricRule='One per-instance ND reference union nine science endpoint fronts (three arms x three sources); no reference feedback; mainHV1.5, sensitivity1.25/2, IGD+,IGD,weak bidirectional C',
        endpoints=['ND(A0+every paid evaluation), primary','paid candidates alone','working five','terminal original shared assembly','best single paid outside-domain candidate versus A0'],
        capacityGate='At least two of three sources in an instance have an actually outside-domain paid candidate adding>=0.1% A0 HV at1.5; report all references',
        targetedMechanismGate='Beyond capacity, NOVEL versus LEGAL needs per-instance median HV>=1% or symmetric IGD+ improvement>=5%, improvement in at least2/3 sources; other instance must not have median HV<-1%, IGD+<-5%, or Cgap<-10pp. Indicator conflicts preclude automatic advance.',
        ordinaryOutcome='If LEGAL has capacity but NOVEL lacks independent value, retain only the domain-expansion question, do not claim novelty targeting or promote ordinary control as a final algorithm',
        noSignal='Stop this fixed two-job joint producer when neither expanded arm has material capacity; do not claim the full same-FA space is exhausted, tune ratios, or add seeds to chase a win',
        hiddenCosts='Import QA and complete timeline QA separately counted; every proposed child, duplicate, unavailable-complement fallback and terminal parent fallback is charged',
        mainlineChanged=False,goalResumed=False)
    write(root/'protocol.json',plan)
    write(root/'tie-order-erratum.json',dict(previousRun=str(CLOSURE),
        issue='Previous generic structural membership fixture used ascending job-id for equal keys; actual typed decoder uses descending job-id',
        actualCrossJobKeyTies=[c['crossJobInitialKeyTies'] for c in identities],
        priorFiniteEnumerationAffected=False,reason='All six actual initial source domains have no cross-job key ties; old frozen artifacts retained',
        currentFix='Correct generic helper to (key,-job) and explicitly verify ties in Linux fixtures',
        fixtureCases=fixtures,explicitAllEqualReverseJobFixture=True,newFE=0,newDecodes=0))
    print('DOMAIN_PROTOCOL_FROZEN',plan['scienceFE'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);main(p.parse_args().root)
