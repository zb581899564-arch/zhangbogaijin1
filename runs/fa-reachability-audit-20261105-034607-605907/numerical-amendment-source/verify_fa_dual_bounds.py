"""Reverify stored dual prices using an upper enclosure of their total mass; no LP reruns."""
from decimal import Decimal
from pathlib import Path

import numpy as np

from run_long_budget_bridge import ROOT,read,rows,write_once
from research.reachability.dual_bound import certificate_with_prices
from research.reachability.relaxation import FixedFARelaxation,ROUNDING_BUDGET_INFLATION

RUN=ROOT/'runs/fa-reachability-audit-20261105-034607-605907'


def main():
    models={};verified=[]
    for record in rows(RUN/'lp-solves.jsonl'):
        stem=record['stem'];key=(stem,tuple(record['assignment']))
        if key not in models:models[key]=FixedFARelaxation(read(RUN/stem/'physical-coefficients.json'),record['assignment'])
        model=models[key];prices=[Decimal(0)]*len(model.row_kinds)
        for p in record['dual']['prices']:prices[p['row']]=Decimal(p['value'])
        budgets=np.asarray(record['target'])[np.asarray(model.row_kinds)]*ROUNDING_BUDGET_INFLATION
        bound=certificate_with_prices(model,budgets,prices)
        assert bound['excludesTarget']==record['dual']['excludesTarget']
        assert abs(bound['lower']-record['dual']['lower'])<1e-12
        assert Decimal(bound['priceMassUpper'])<=1
        verified.append({'id':record['id'],'stem':stem,**bound})
    write_once(RUN/'dual-reverification.json',{'status':'PASS','bounds':verified,'newLPSolves':0,'searchFE':0,'decoderCalls':0,
        'amendment':'Original lower-rounded price-mass sum was not a rigorous upper enclosure. Reverify all stored prices with100-digit upward mass summation and downward normalization before60-digit lower-bound reconstruction. Raw execution retained; no classification changed.',
        'source':str(Path(__file__))})
    print('FA_DUAL_REVERIFICATION_PASS',len(verified),'newLPSolves=0 decoderCalls=0')


if __name__=='__main__':main()
