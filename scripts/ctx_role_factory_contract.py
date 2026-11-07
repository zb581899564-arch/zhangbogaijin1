"""Pure paid-state responsibility assignment and exact factory-jobset compatibility bookkeeping."""
from collections import Counter,defaultdict

ROLES=['MAKESPAN','CENTER','ENERGY','WORKER_COST']
BOUNDARY={'MAKESPAN','ENERGY','WORKER_COST'}


def duty(slot):
    return 'MAKESPAN' if slot<15 else 'CENTER' if slot<70 else 'ENERGY' if slot<85 else 'WORKER_COST'


def regroup(points):
    result=[None]*100
    for family in (-1,0,1,2,3):
        ids=[i for i,p in enumerate(points) if p['family']==family];assert len(ids)==(80 if family==-1 else 5)
        for role,obj in (('MAKESPAN',0),('ENERGY',1),('WORKER_COST',2)):
            ids=sorted(ids,key=lambda i:points[i]['objectives'][obj]);number=11 if family==-1 else 1
            for i in ids[:number]:result[i]=role
            ids=ids[number:]
        for i in ids:result[i]='CENTER'
    assert Counter(result)==Counter(MAKESPAN=15,CENTER=55,ENERGY=15,WORKER_COST=15)
    return result


def switch_summary(points,previous_duties,assigned):
    old=Counter(previous_duties);new=Counter(assigned);minimum=sum(abs(old[r]-new[r]) for r in ROLES)//2
    count=sum(a!=b for a,b in zip(previous_duties,assigned))
    return dict(changed=count,minimumRequiredByCountRebalance=minimum,excessBeyondCountRebalance=count-minimum,
        freeChanged=sum(a!=b for p,a,b in zip(points,previous_duties,assigned) if p['family']==-1),
        inheritedDutyCounts=dict(old),centerToBoundary=sum(a=='CENTER' and b!='CENTER' for a,b in zip(previous_duties,assigned)),
        boundaryToCenter=sum(a!='CENTER' and b=='CENTER' for a,b in zip(previous_duties,assigned)),
        uniqueUpdateChainRoots=len({p['lineage'] for p in points}))


def factory_parts(point):
    jobs=point['JS'];assignment=[None]*len(jobs)
    for j,f in zip(jobs,point['FA']):assignment[j]=f
    full=tuple(assignment);factories=range(max(assignment)+1);parts=[]
    for factory in factories:
        chain=tuple((j,m,w) for j,f,m,w in zip(jobs,point['FA'],point['MA'],point['WA']) if f==factory)
        assert chain;parts.append((factory,frozenset(j for j,_,_ in chain),chain))
    return full,parts


class FactoryLibrary:
    def __init__(self):
        self.by_jobs=defaultdict(lambda:defaultdict(set));self.by_assignment=defaultdict(set)
        self.patterns=set();self.requests=[]
    def add(self,point,role):
        assignment,parts=factory_parts(point);self.patterns.add(assignment)
        for f,jobs,chain in parts:
            self.by_jobs[f,jobs][chain].add(role);self.by_assignment[assignment,f].add(chain)
    def query(self,point,cycle,fe):
        assignment,parts=factory_parts(point);counts=[]
        for f,jobs,chain in parts:
            broad=self.by_jobs[f,jobs];whole=self.by_assignment[assignment,f];assert chain in broad and chain in whole
            extra=set(broad)-whole
            observed_boundary_only=sum(bool(broad[c]) and broad[c]<=BOUNDARY for c in extra)
            counts.append(dict(factory=f,jobCount=len(jobs),currentWholeFAAlternatives=len(whole-{chain}),
                jobsetAlternatives=len(set(broad)-{chain}),additionalChains=len(extra),observedBoundaryOnlyAdditionalChains=observed_boundary_only))
        self.requests.append(dict(cycle=cycle,fe=fe,family=point['family'],factories=counts,
            strictAddedSupply=any(c['additionalChains']>0 for c in counts),
            atLeastTwoVariableFactories=sum(c['jobsetAlternatives']>0 for c in counts)>=2,
            boundaryOnlyAddedSupply=any(c['observedBoundaryOnlyAdditionalChains']>0 for c in counts)))
    def summary(self):
        n=len(self.requests)
        return dict(requests=n,strictAddedRequests=sum(r['strictAddedSupply'] for r in self.requests),
            multiFactoryRequests=sum(r['atLeastTwoVariableFactories'] for r in self.requests),
            bothAddedAndMultiFactory=sum(r['strictAddedSupply'] and r['atLeastTwoVariableFactories'] for r in self.requests),
            boundaryOnlyAddedRequests=sum(r['boundaryOnlyAddedSupply'] for r in self.requests),
            freeReceiverRequests=sum(r['family']==-1 for r in self.requests),
            knownWholeFAPatterns=len(self.patterns),knownFactoryJobsetKeys=len(self.by_jobs),
            knownDistinctFactoryChains=sum(len(v) for v in self.by_jobs.values()))
