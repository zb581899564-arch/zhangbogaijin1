"""Exact finite resource-key support and physical-order membership, without objectives."""
import itertools
import math


def physical(point,factory):
    return tuple((j,m,w) for j,f,m,w in zip(point['JS'],point['FA'],point['MA'],point['WA']) if f==factory)


def support(points):
    fixed=dict(zip(points[0]['JS'],points[0]['FA']))
    options={j:[] for j in sorted(fixed)}
    for point in points:
        assert dict(zip(point['JS'],point['FA']))==fixed
        by_job={j:(m,w) for j,m,w in zip(point['JS'],point['MA'],point['WA'])}
        for job in options:
            options[job].append((point['keys'][job],*by_job[job]))
    return fixed,options


def membership(chain,options):
    """Greedy earliest compatible key is exact for a strictly ordered job chain."""
    choices=[]
    for job,machine,worker in chain:
        allowed=sorted((key,job,i) for i,(key,m,w) in enumerate(options[job]) if (m,w)==(machine,worker))
        if not allowed:return 'OUTSIDE_RESOURCE',None
        choices.append(allowed)
    previous=(-math.inf,-1);selected=[]
    for allowed in choices:
        next_choice=next((a for a in allowed if a[:2]>previous),None)
        if next_choice is None:return 'OUTSIDE_KEY_ORDER',None
        previous=next_choice[:2];selected.append(next_choice[2])
    return 'INSIDE',selected


def enumerate_factory(jobs,options):
    """Enumerate every inherited per-job pair, deduplicate only physical factory chains."""
    states={};assignments=0
    for choices in itertools.product(*(range(len(options[j])) for j in jobs)):
        keyed=[(options[j][i][0],j,*options[j][i][1:]) for j,i in zip(jobs,choices)]
        chain=tuple((j,m,w) for _,j,m,w in sorted(keyed));assignments+=1
        if chain not in states:states[chain]=choices
    assert assignments==math.prod(len(options[j]) for j in jobs)
    return states,assignments


def validate_membership():
    """Brute-force three-job physical universes, including ties and missing alleles."""
    cases=[{0:[(.1,0,0),(.8,1,0)],1:[(.2,0,0),(.7,1,0)],2:[(.3,0,0),(.6,1,0)]},
           {0:[(.5,0,0),(.5,1,0)],1:[(.5,0,0),(.6,1,0)],2:[(.4,0,0),(.5,1,0)]}]
    checked=0
    for options in cases:
        actual,_=enumerate_factory(list(options),options)
        for order in itertools.permutations(options):
            for allocations in itertools.product(range(3),repeat=3):
                chain=tuple((j,m,0) for j,m in zip(order,allocations))
                assert (membership(chain,options)[0]=='INSIDE')==(chain in actual)
                checked+=1
    return checked
