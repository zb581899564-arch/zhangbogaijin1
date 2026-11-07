"""Zero-decoder Java precondition: exact assignments, LP costs, scaling and paid ideals."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import linear_sum_assignment,linprog
from scipy.sparse import eye,kron,vstack

from run_long_budget_bridge import read,write_once,execute


def fixtures(root,plan):
    opportunity=read(Path(plan['opportunityRoot'])/'protocol.json')['contract'];data=[]
    for spec in opportunity['cases']:
        points=[]
        with (Path(spec['source'])/'events.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                row=json.loads(line)
                if row['kind']=='initial':points.append(row['objectives'])
                if len(points)==100:break
        data.append(dict(id=spec['instance'],points=points,scale=spec['scale'],actual=True))
    data.extend([dict(id='ALL_TIED',points=[[1.,1.,1.]]*100,scale=[1.,1.,1.],actual=False),
        dict(id='ANTICHAIN',points=[[float(i),float(99-i),float(i%7)] for i in range(100)],scale=[2.,4.,8.],actual=False)])
    base=data[0];factor=np.array([2.,4.,8.])
    data.append(dict(id='SCALED_FIRST',points=(np.array(base['points'])*factor).tolist(),scale=(np.array(base['scale'])*factor).tolist(),actual=False))
    write_once(root/'math-fixtures.json',data)
    with (root/'math-fixtures.tsv').open('x',encoding='utf-8') as stream:
        for item in data:
            for point in item['points']:stream.write(item['id']+'\t'+','.join(map(str,point))+'\t'+','.join(map(str,item['scale']))+'\n')
    return data


def validate(root,plan,data):
    result=read(root/'math-output.json');old=read(Path(plan['opportunityRoot'])/'analysis.json');checks=[]
    weights=np.array([(a,b,c) for a in range(1,11) for b in range(1,11) for c in range(1,11) if a+b+c==12],float)
    constraints=vstack((kron(eye(55),np.ones((1,55))),kron(np.ones((1,55)),eye(55))),format='csr')
    for fixture,actual in zip(data,result['fixtures']):
        assert fixture['id']==actual['fixture'] and actual['directions']==weights.tolist()
        points=np.array(fixture['points']);scale=np.array(fixture['scale']);ideal=points.min(axis=0)
        assert actual['initialIdeal']==ideal.tolist()
        cost=(weights[None,:,:]*((points[15:70,None,:]-ideal)/scale)).max(axis=2)
        r,c=linear_sum_assignment(cost);assert r.tolist()==list(range(55))
        assert actual['columns']==c.tolist(),('Assignment differs',fixture['id'])
        minimum=float(cost[r,c].sum());assert abs(minimum-actual['assignmentCost'])<2e-12
        lp=linprog(cost.ravel(),A_eq=constraints,b_eq=np.ones(110),bounds=(0,None),method='highs');assert lp.success and abs(lp.fun-minimum)<2e-9
        if fixture['actual']:
            source,=[s for s in old['cases'] if s['instance']==fixture['id']]
            assert [weights[int(col)].tolist() for col in c]==[source['slotDirections']['MATCHED'][str(i)] for i in range(15,70)]
        for axis in range(3):
            ideal[axis]-=scale[axis]
            for k,slot in enumerate((15,40,69)):
                probe=actual['probes'][3*axis+k];w=weights[c[slot-15]]
                assert probe['slot']==slot and probe['ideal']==ideal.tolist() and probe['weight']==w.tolist()
                expected=float(np.max(w*((points[slot]-ideal)/scale)))
                assert abs(expected-probe['score'])<2e-13
        checks.append(dict(fixture=fixture['id'],exactAssignmentAndIdeal=True,LPObjectiveError=abs(lp.fun-minimum)))
    assert result['fixtures'][0]['columns']==result['fixtures'][-1]['columns']
    assert [p['score'] for p in result['fixtures'][0]['probes']]==[p['score'] for p in result['fixtures'][-1]['probes']]
    assert result['invalidScaleRejections']==4 and result['newSearchFE']==result['newDecoderCalls']==0
    write_once(root/'math-acceptance.json',dict(passed=True,checks=checks,scaleInvariant=True,newSearchFE=0,newDecoderCalls=0))


def run(root,cp,plan):
    data=fixtures(root,plan)
    command=['java','-Xms32m','-Xmx2g','-cp',cp,'research.dynamic.PaRegionalMathRun',str(root/'math-fixtures.tsv'),str(root/'math-output.json')]
    write_once(root/'math-command.json',command);execute(command,root/'math-run.log')
    validate(root,plan,data);print('PA_REGIONAL_MATH_PRECONDITION_PASS',len(data),'fixtures,0newFE/decoder',flush=True)
