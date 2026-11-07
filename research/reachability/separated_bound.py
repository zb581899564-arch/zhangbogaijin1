"""Independent objective, job-chain and uniform resource-price bounds without an LP solve."""
from decimal import Decimal
import numpy as np

from .dual_bound import certificate_with_prices
from .relaxation import ROUNDING_BUDGET_INFLATION


def separated_bound(problem,target):
    rows=len(problem.row_labels);bases=[];resource={}
    for i,label in enumerate(problem.row_labels):
        if '/machine' in label or '/worker' in label:
            key=label.rsplit('/',1)[0]+('/M' if '/machine' in label else '/W')
            resource.setdefault(key,[]).append(i)
        else:
            price=np.zeros(rows);price[i]=1.;bases.append(price)
    for group in resource.values():
        price=np.zeros(rows);price[group]=1/len(group);bases.append(price)
    prices=np.asarray(bases);budgets=np.asarray(target)[np.asarray(problem.row_kinds)]*ROUNDING_BUDGET_INFLATION
    costs=np.asarray(problem.matrix.T@(prices/budgets).T)
    starts=np.asarray([s for s,_ in problem.groups])
    values=np.minimum.reduceat(costs,starts,axis=0).sum(axis=0)+(prices/budgets)@np.asarray(problem.row_constants)
    best=prices[int(np.argmax(values))]
    bound=certificate_with_prices(problem,budgets,[Decimal.from_float(float(p)) for p in best])
    return {'basisCount':len(bases),'dual':bound}
