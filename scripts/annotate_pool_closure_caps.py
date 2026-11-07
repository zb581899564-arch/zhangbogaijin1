"""Declared post-hoc scope annotation; it cannot alter the frozen primary closure gate."""
import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'

from pathlib import Path
import sys
import shutil
import numpy as np
from run_long_budget_bridge import read, rows, write_once
from run_pool_closure_oracle import assembly, nine_candidates
from pool_phase_analysis import check_assemblies
from research.composition_oracle.frontier import decode
from research.composition_oracle.volume import UncoveredVolume


def annotate(root):
    out=root/'posthoc-cap-decomposition';out.mkdir()
    write_once(out/'protocol.json',{
        'status':'DESCRIPTIVE_AFTER_PRIMARY_OUTCOMES', 'searchFE':0,
        'scope':'Same8 original later receivers, all4 families, unchanged primary1.5 reference and commonG2 archive. '
                'Evaluate exact-closure front under each of the already-registered caps. No new cap or policy weights.',
        'question':'Separate lack of any cap-feasible material candidate from omissions within caps. '
                   'No test independence, role supply claim, gate change or online selector authorization.',
        'qa':'Full-decode all distinct per-cap maximum witnesses; separate from original closure QA and searchFE.'})
    shutil.copy2(Path(__file__),out/Path(__file__).name)
    protocol=read(root/'protocol.json');cp=(root/'classpath.txt').read_text('utf-8')
    summaries=[];qa_total=0
    for spec in protocol['instances']:
        stem=spec['stem'];folder=out/stem;folder.mkdir()
        shutil.copytree(root/stem/'inputs',folder/'inputs')
        data,=rows(root/stem/'source-pool-phases.jsonl')
        phase=next(s for s in data['snapshots'] if s['phase']=='G2_CENTER_ENTRY')
        norm=spec['normalization'];normalized=lambda x:(np.asarray(x)-norm['lower'])/norm['scale']
        scorer=UncoveredVolume(normalized(phase['knownArchive']),(1.5,)*3)
        cells=[];witnesses={}
        for family in phase['pool']['families']:
            receivers=[(i,r) for i,r in enumerate(data['laterReceivers']) if r['family']==family['family']]
            assert len(receivers)==2
            for mode,key in (('FINITE','factories'),('FULL','fullFactories')):
                saved=read(root/stem/f'family-{family["family"]}-{mode}-frontier.json')
                states=[(s[0],s[1],s[2],tuple(s[3])) for s in saved['states']];powers=saved['integerPowers']
                objectives=np.asarray([decode(s[:3],powers) for s in states])
                gains=100*scorer.gains(normalized(objectives))/scorer.background_hv
                for receiver_index,receiver in receivers:
                    caps=[]
                    for factor in (.9,1.,1.1):
                        eligible=np.flatnonzero(objectives[:,0]<=factor*receiver['objectives'][0])
                        if len(eligible):
                            best=int(eligible[np.argmax(gains[eligible])]);best_gain=float(gains[best])
                            candidate=assembly(family[key],states[best],powers)
                            genome=tuple(tuple(candidate[k]) for k in ('JS','FA','MA','WA'));witnesses[genome]=candidate
                        else:
                            best=None;best_gain=None
                        caps.append({'factor':factor,'eligibleFrontPoints':len(eligible),'bestIndex':best,'bestSingleGainPct':best_gain})
                    nine=nine_candidates(phase,receiver,mode=='FULL')
                    best_nine=float(max(100*scorer.gains(normalized([c['objectives'] for c in nine]))/scorer.background_hv,default=0)) if nine else 0.
                    cells.append({'family':family['family'],'mode':mode,'receiver':receiver_index,
                        'parentCmax':receiver['objectives'][0],'caps':caps,'unrestrictedBestGainPct':float(np.max(gains)),
                        'bestNineGainPct':best_nine})
        report=check_assemblies(out,cp,stem,list(witnesses.values()));qa_total+=report['passedOfflineDecodes']
        item={'stem':stem,'cells':cells,'offlineFullDecoderQA':report['passedOfflineDecodes'],
              'maxAbsoluteObjectiveError':report['maxAbsoluteObjectiveError']}
        write_once(folder/'analysis.json',item);summaries.append(item)
    result={'instances':summaries,'searchFE':0,'offlineFullDecoderQA':qa_total,
            'primaryGateUnchanged':True,'scope':'Post-hoc explanation of existing caps, no new mechanism or performance gate.'}
    write_once(out/'analysis.json',result)
    print('POOL_CAP_ANNOTATION_COMPLETE',qa_total,flush=True)


if __name__=='__main__':
    annotate(Path(sys.argv[1]))
