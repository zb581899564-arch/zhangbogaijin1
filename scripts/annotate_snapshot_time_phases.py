"""Post-hoc fixed-checkpoint interpretation only; never retune the preceding failed gate."""
from pathlib import Path
import sys
import numpy as np
from run_long_budget_bridge import read, rows, write_once, hypervolume


def annotate(root):
    protocol=read(root/'protocol.json');results=[]
    for spec in protocol['instances']:
        stem,norm=spec['stem'],spec['normalization'];seconds=protocol['timeSeconds'][stem]
        indexed={}
        for seed in protocol['seeds']:
            for label in protocol['methods']:
                folder=root/stem/f'{seed}-{label}'
                points=rows(folder/'anytime.jsonl');receipt,=rows(folder/'run-receipt.jsonl')
                values={}
                for fe in (100,5100,50000,100000):
                    point=next(p for p in points if p['checkpointKind']=='FE' and p['checkpoint']==fe)
                    if not point['reached']:values[str(fe)]=None;continue
                    front=(np.asarray(point['front']).reshape(-1,3)-norm['lower'])/norm['scale']
                    values[str(fe)]=float(hypervolume(front,(1.5,)*3))
                end=next(p for p in points if p['checkpointKind']=='TIME' and p['checkpoint']==seconds)
                front=(np.asarray(end['front']).reshape(-1,3)-norm['lower'])/norm['scale']
                values['T']=float(hypervolume(front,(1.5,)*3))
                indexed[(seed,label)]={'HV':values,'search':receipt['search']}
        gap={}
        for checkpoint in ('100','5100','50000','100000','T'):
            effects=[100*(indexed[(s,'FULL_ANCHOR')]['HV'][checkpoint]/indexed[(s,'NSGA_ANCHOR')]['HV'][checkpoint]-1)
                     for s in protocol['seeds'] if indexed[(s,'FULL_ANCHOR')]['HV'][checkpoint] is not None
                     and indexed[(s,'NSGA_ANCHOR')]['HV'][checkpoint] is not None]
            gap[checkpoint]={'pairedPct':effects,'medianPct':float(np.median(effects)) if effects else None}
        late={label:[100*(indexed[(s,label)]['HV']['T']/indexed[(s,label)]['HV']['100000']-1)
                     for s in protocol['seeds']] for label in ('FULL_SERIAL','FULL_ANCHOR','NSGA_ANCHOR')}
        roles={label:[{k:v for k,v in indexed[(s,label)]['search'].items()
                        if '.preference.' in k and k.startswith('local.') or k=='generations.completed'}
                      for s in protocol['seeds']] for label in ('FULL_ANCHOR','NSGA_ANCHOR')}
        results.append({'stem':stem,'fullVsNsgaAtFixedCheckpoints':gap,
                        'gainFrom100000FEToDeadlinePct':late,'observedLocalVisitCounts':roles})
    result={'instances':results,'searchFE':0,'status':'DESCRIPTIVE_AFTER_PRIMARY_OUTCOMES',
        'scope':'Fixed FE100/5100/50000/100000 and actual T, chosen for phase interpretation; no new threshold, '
                'causal mediation claim, censored-point replacement, or rescue of the failed primary experiment.'}
    write_once(root/'phase-annotation.json',result)
    for r in results:print(r['stem'],r['fullVsNsgaAtFixedCheckpoints'],r['gainFrom100000FEToDeadlinePct'],flush=True)


if __name__=='__main__':
    annotate(Path(sys.argv[1]))
