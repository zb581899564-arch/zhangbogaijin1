"""Reconstruct a feasible dual bound with downward Decimal rounding, independent of solver status."""
from decimal import Decimal,localcontext,ROUND_FLOOR


def certificate(problem,budgets,marginals):
    with localcontext() as ctx:
        ctx.prec=60;ctx.rounding=ROUND_FLOOR
        prices=[max(Decimal(0),-Decimal.from_float(float(v))) for v in marginals]
        total=sum(prices,Decimal(0))
        if total>1:prices=[p/total for p in prices]
        assert sum(prices,Decimal(0))<=1 and min(prices)>=0
        weights=[p/Decimal.from_float(float(b)) for p,b in zip(prices,budgets)]
        lambdas=[]
        for start,end in problem.groups:
            costs=[]
            for col in range(start,end):
                value=Decimal(0)
                for row,coefficient in problem.column_entries[col]:
                    if weights[row]:value+=Decimal.from_float(coefficient)*weights[row]
                costs.append(value)
            lambdas.append(min(costs))
        lower=sum(lambdas,Decimal(0))
        return {'lowerDecimal':str(lower),'lower':float(lower),'priceMass':str(sum(prices,Decimal(0))),
            'prices':[{'row':i,'kind':problem.row_kinds[i],'label':problem.row_labels[i],'value':str(p)} for i,p in enumerate(prices) if p],
            'excludesTarget':lower>Decimal('1.000001')}
