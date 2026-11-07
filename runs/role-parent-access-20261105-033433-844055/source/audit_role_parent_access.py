"""Describe source access under actual mutually exclusive grouping, without proposing offspring."""
from datetime import datetime
from pathlib import Path
import shutil
import numpy as np

from run_long_budget_bridge import ROOT,read,rows,write_once,execute
from run_acceptance_plateau_audit import SOURCE,STEMS,SEED
from final_survival_analysis import geometry

SURVIVAL=ROOT/'runs/final-survival-audit-20261105-031556-115852'
ROLES=(('MAKESPAN',0),('ENERGY',1),('WORKER_COST',2))


def grouping(points):
    groups={r:[] for r,_ in ROLES};groups['CENTER']=[]
    for category in range(5):
        ids=[i for i,p in enumerate(points) if p['category']==category];size=11 if category==0 else 1
        for role,k in ROLES:
            ids.sort(key=lambda i:points[i]['objectives'][k]);groups[role].extend(ids[:size]);ids=ids[size:]
        score,_,_=geometry([points[i]['objectives'] for i in ids])
        groups['CENTER'].extend(ids[i] for i in sorted(range(len(ids)),key=lambda j:score[j]))
    return groups


def analyze_population(points,groups):
    rows=[]
    for role,k in ROLES:
        for cat in range(5):
            compatible=[i for i,p in enumerate(points) if p['category']==cat]
            own=[i for i in groups[role] if points[i]['category']==cat]
            broad=sorted(compatible,key=lambda i:points[i]['objectives'][k])[:len(own)]
            best_all=min(points[i]['objectives'][k] for i in compatible)
            best_own=min(points[i]['objectives'][k] for i in own)
            mean_all=float(np.mean([points[i]['objectives'][k] for i in broad]))
            mean_own=float(np.mean([points[i]['objectives'][k] for i in own]))
            outside=[i for i in broad if i not in own]
            rows.append({'role':role,'category':cat,'roleCount':len(own),'availableCount':len(compatible),
                'bestOwn':best_own,'bestAllCompatible':best_all,'meanOwn':mean_own,'meanTopCompatible':mean_all,
                'meanScalarGapPct':100*(mean_own/mean_all-1) if mean_all>0 else None,
                'bestScalarGapPct':100*(best_own/best_all-1) if best_all>0 else None,
                'topCompatibleOutsideRole':outside,'ownIndices':own})
    return rows


def main():
    root=ROOT/'runs'/datetime.now().strftime('role-parent-access-%Y%m%d-%H%M%S-%f');root.mkdir()
    write_once(root/'protocol.json',{'source':str(SURVIVAL),'instances':STEMS,'seed':SEED,
        'scope':'Post-hoc source-access description, not a new algorithm gate, offspring improvement or novel four-role claim.',
        'snapshots':'All paid100 initial points and actual first complete-generation100 survivors from the readonly final-survival audit. No best-generation or outcome resampling.',
        'question':'Does mutually exclusive M then E then W ownership prevent a role accessing the best current compatible parent? Preserve family category, count and original frozen grouping.',
        'validation':'Python grouping must equal actual frozen CooperationSupport/FamilyContexts grouping on objective/category snapshots. Existing source genomes/objectives already paid; zero evaluator and decoder calls.',
        'limits':'Whole paid parents carry no new discovery value. Lower scalar objective or availability alone does not prove improved offspring or continuation, nor a reason to discard complementary exclusive groups. Any later probe needs paired teachers/construction noise and ordinary elite/random controls.',
        'literature':['https://arxiv.org/abs/1805.01221','https://pmc.ncbi.nlm.nih.gov/articles/PMC5305220/']})
    src=root/'source';src.mkdir();classes=root/'classes';classes.mkdir()
    java=ROOT/'src/algorithms/diagnostics/RoleGroupingCheckRun.java';shutil.copy2(java,src)
    shutil.copy2(Path(__file__),src)
    cp=(SURVIVAL/'classpath.txt').read_text(encoding='utf-8-sig').strip()
    execute(['javac','-encoding','UTF-8','--release','8','-cp',cp,'-d',str(classes),str(src/java.name)],root/'compile.log');cp=f'{classes};{cp}'
    output=[]
    for stem in STEMS:
        folder=root/stem;folder.mkdir();inp=SOURCE/stem/'inputs'
        initial=[{**p,'category':(p['fe']-1)//5+1 if p['fe']<=20 else 0} for p in rows(SOURCE/stem/str(SEED)/'SHARE_FULL/initial-population.jsonl')]
        event=rows(SURVIVAL/stem/str(SEED)/'ON/final-survival.jsonl')[0]['events'][0]
        final=[event['points'][i] for i in event['selected']]
        for label,points in (('INITIAL',initial),('AFTER_FIRST_GENERATION',final)):
            path=folder/(label+'.tsv');path.write_text('\n'.join(str(p['category'])+'\t'+','.join(map(str,p['objectives'])) for p in points)+'\n',encoding='utf-8')
            execute(['java','-cp',cp,'org.uma.jmetal.util.research.search.RoleGroupingCheckRun',str(inp/(stem+'.txt')),
                str(inp/'RECONSTRUCTED-setup.txt'),str(path)],folder/(label+'-actual-grouping.json'))
            expected=read(folder/(label+'-actual-grouping.json'));groups=grouping(points);assert groups==expected
            output.append({'stem':stem,'snapshot':label,'actualGroupingMatches':True,'groups':groups,'access':analyze_population(points,groups)})
    write_once(root/'analysis.json',{'snapshots':output,'searchFE':0,'decoderCalls':0,'candidateEfficacyEstablished':False})
    write_once(root/'status.json',{'status':'COMPLETE','searchFE':0,'decoderCalls':0,'actualGroupingChecks':4})
    print('ROLE_ACCESS_ROOT',root,flush=True)
    for item in output:print(item['stem'],item['snapshot'],[{k:v for k,v in r.items() if k in ('role','bestScalarGapPct','meanScalarGapPct','topCompatibleOutsideRole')} for r in item['access'] if r['category']==0],flush=True)


if __name__=='__main__':main()
