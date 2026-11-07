"""Zero-FE preflight of reproduction allocation; cannot infer unobserved parents' offspring values."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
from datetime import datetime
from pathlib import Path
import shutil
import numpy as np
from run_long_budget_bridge import ROOT, read, write_once, execute
from paired_survival_bench import class_hashes

SOURCE=ROOT/'runs/mating-pool-probe-20261105-062648-478040'
KERNEL=ROOT/'runs/snapshot-anchor-audit-20261105-051047-172151'


def analyze(root,spec):
    stem=spec['stem'];scores=read(root/stem/'scores.json')['contexts'];source=read(SOURCE/stem/'analysis.json');contexts=[]
    indices=[i*46//7 for i in range(8)];methods=('WITHIN','SHARED','RANDOM_SHARED','INITIAL_SHARED')
    for score in scores:
        own=sorted([c for c in source['cells'] if c['context']==score['context']],key=lambda c:c['recipient'])
        assert [c['recipient'] for c in own]==list(range(8))
        probabilities=np.asarray(score['probabilities']);assert np.all(probabilities>0) and abs(sum(probabilities)-1)<1e-12
        mass=float(np.sum(probabilities[indices]));weights=probabilities[indices]/mass;assert abs(np.sum(weights)-1)<1e-12
        estimates={}
        for method in methods:
            gains=np.asarray([c['methods'][method]['meanSingleAddedHV'] for c in own])
            estimates[method]={'uniformObserved8':float(np.mean(gains)),'conditionalTournamentObserved8':float(weights@gains)}
        contexts.append({'context':score['context'],'seed':own[0]['seed'],'step':own[0]['step'],'selectedIndices':indices,
            'selectedRanks':[score['rank'][i] for i in indices],'full47TournamentMassOnObserved8':mass,
            'conditionalWeights':weights.tolist(),'effectiveObservedParents':float(1/np.sum(weights**2)),'estimates':estimates})
    grouped=[]
    for seed in sorted({c['seed'] for c in contexts}):
        own=[c for c in contexts if c['seed']==seed]
        grouped.append({'seed':seed,'uniform':float(np.mean([c['estimates']['WITHIN']['uniformObserved8'] for c in own])),
                        'weighted':float(np.mean([c['estimates']['WITHIN']['conditionalTournamentObserved8'] for c in own]))})
    uniform=float(np.mean([c['estimates']['WITHIN']['uniformObserved8'] for c in contexts]))
    weighted=float(np.mean([c['estimates']['WITHIN']['conditionalTournamentObserved8'] for c in contexts]))
    effect=100*(weighted/uniform-1) if uniform>1e-12 else None
    positive=sum(c['estimates']['WITHIN']['conditionalTournamentObserved8']>c['estimates']['WITHIN']['uniformObserved8']+1e-12 for c in contexts)
    minimum_ess=min(c['effectiveObservedParents'] for c in contexts)
    supported=effect is not None and effect>=10 and positive>=4 and minimum_ess>=3 and all(g['weighted']>g['uniform'] for g in grouped)
    report={'stem':stem,'contexts':contexts,'primaryDonorRule':'WITHIN','uniformObserved8':uniform,'conditionalTournamentObserved8':weighted,
        'effectPct':effect,'positiveContexts':positive,'totalContexts':len(contexts),'minimumEffectiveObservedParents':minimum_ess,
        'sourceSeedMeans':grouped,'worthNewPaidParentSelectionProbe':bool(supported),
        'limits':'Exact full47 tournament weights, conditioned on8already-observed recipients. Gains use16old paired proposal samples each. '
                 'Other39recipient values are unobserved; this is not expected full47 algorithm gain or independent confirmation. '
                 'OnlyWITHIN is primary; other donor rules descriptive. No source/parent subset retuning or production changes.'}
    write_once(root/f'{stem}-analysis.json',report);return report


def main():
    root=ROOT/'runs'/datetime.now().strftime('parent-selection-audit-%Y%m%d-%H%M%S-%f');root.mkdir();print('PARENT_SELECTION_ROOT',root,flush=True)
    specs=read(SOURCE/'protocol.json')['instances'];completed=[]
    write_once(root/'protocol.json',{'source':str(SOURCE),'instances':specs,'primaryDonorRule':'WITHIN','newSearchFE':0,'additionalDecodes':0,
        'question':'Does fixed-slot first-parent reproduction spend offspring evaluations on less promising recipients than crowded tournament would, '
                   'holding the already-paid second-parent rule and actual classic offspring samples fixed?',
        'calculation':'ActualNsgaSelection.score on current47freeCENTER; enumerate all47^2crowded tournaments including half-credit ties and '
                      'verify closed-form probabilities. Condition winners on existing8equally-spaced recipients, then weight their16paid child gains.',
        'gate':'Eachinstance primaryWITHIN weighted mean gain>=10%overobserved8uniform,>=4/6contexts positive, bothsource seeds positive, '
               'eachcontext conditional effective sample size>=3. Only permits newpaid all47parent-selection probe, not algorithm promotion.',
        'limits':'39parents offspring unknown. Conditional8weights cannot establish full47expected gain, same-time, nativeQGS improvement or novelty. '
                 'No post-hoc promotion of another donor rule, no newparent/window/seed selection on failure.',
        'preserved':'No newevaluator calls or source/default/Q/role/family/sharing changes; no filetransfers.'})
    try:
        source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
        for name in ('ParentSelectionScores','ClassResolutionProbe'):shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
        shutil.copy2(__file__,source/Path(__file__).name);base=(KERNEL/'classpath.txt').read_text('utf-8')
        execute(['javac','-encoding','UTF-8','--release','8','-cp',base,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
        write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{base}';(root/'classpath.txt').write_text(cp,encoding='utf-8')
        for spec in specs:
            stem=spec['stem'];out=root/stem;out.mkdir();inp=SOURCE/stem/'inputs'
            cmd=['java','-Xms32m','-Xmx2g','-cp',cp,'org.uma.jmetal.util.research.classic.ParentSelectionScores',
                 str(inp/f'{stem}.txt'),str(inp/'RECONSTRUCTED-setup.txt'),str(SOURCE/stem/'donors.tsv'),str(out/'scores.json')]
            write_once(out/'command.json',cmd);execute(cmd,out/'run.log');score=read(out/'scores.json')
            assert score['status']=='PASS' and score['searchFE']==score['decodes']==0;completed.append(analyze(root,spec))
    except BaseException as error:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','newSearchFE':0,'additionalDecodes':0,'error':repr(error)});raise
    result={'instances':[{k:v for k,v in r.items() if k!='contexts'} for r in completed],
            'worthNewPaidParentSelectionProbe':all(r['worthNewPaidParentSelectionProbe'] for r in completed)}
    write_once(root/'analysis.json',result);write_once(root/'status.json',{'status':'COMPLETE','newSearchFE':0,'additionalDecodes':0,
        'contexts':12,'worthNewPaidParentSelectionProbe':result['worthNewPaidParentSelectionProbe']})
    print('PARENT_SELECTION_COMPLETE',result,flush=True)


if __name__=='__main__':main()
