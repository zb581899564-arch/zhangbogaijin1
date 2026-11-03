from datetime import datetime
from pathlib import Path
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dynamic_build import build_dynamic
from verify_semantic_repair import validate_pool_scores
from research.semantic_repair.evidence import read,write_once,digest
from research.semantic_repair.diagnostics import validate_trace
from research.center_last.protocol import PREVIOUS,VARIANTS
from research.center_last.observations import validate_observations


def real_entry(build,folder,stem,label,*,frozen=False,seconds='Infinity',fe=20000):
    folder.mkdir(parents=True)
    old=ROOT/'runs/sync-job-audit-20261102-184848-424022'
    cp=((old if frozen else build)/'classpath.txt').read_text(encoding='utf-8').strip()
    inputs=PREVIOUS/'inputs'/stem;spec=VARIANTS[label]
    cmd=['java','-Xms32m','-Xmx2g','-cp',cp,'research.dynamic.DynamicRun',
         str(inputs/(stem+'.txt')),str(inputs/'RECONSTRUCTED-setup.txt'),str(inputs/'fatigue-input.txt'),str(folder),
         spec['mode'],str(fe),'4242421',str(seconds),'1.0','true','false','0','true','SCREEN','0',spec['profile'],'true','false','false','true']
    write_once(folder/'command.json',cmd)
    with (folder/'run.log').open('x',encoding='utf-8') as log:
        result=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    if result.returncode:raise RuntimeError((folder/'run.log').read_text(encoding='utf-8',errors='replace')[-3000:])
    summary=read(folder/'summary.json');assert summary['status']=='passed' and summary['failed']==summary['timeInterruptedAttempts']
    assert summary['archiveSize']==summary['offlineValidationDecodes']
    if seconds=='Infinity':assert summary['successful']==summary['attempted']==fe
    trace=[json.loads(x) for x in (folder/'semantic-trace.jsonl').read_text().splitlines()]
    validate_trace(trace,summary['semanticAudit'],summary);validate_pool_scores(trace)
    if not frozen:validate_observations(folder,summary,label,require_complete=summary['stopReason']=='FE_LIMIT')
    return summary


def verify():
    out=ROOT/'runs'/datetime.now().strftime('center-last-engineering-%Y%m%d-%H%M%S-%f');out.mkdir()
    cp=build_dynamic(out,skip_maven=True);(out/'classpath.txt').write_text(cp,encoding='utf-8')
    for name in ['org.uma.jmetal.util.research.cooperation.CompositionTimingChecks','org.uma.jmetal.util.research.search.FeedbackAuditChecks']:
        path=out/(name.rsplit('.',1)[-1]+'.log')
        with path.open('x',encoding='utf-8') as log:result=subprocess.run(['java','-Xmx768m','-cp',cp,name],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=60)
        if result.returncode:raise RuntimeError(path.read_text(encoding='utf-8',errors='replace'))
        print(name,'PASS',flush=True)
    checks=[]
    for stem in ['20_2_3_1','200_8_5_1']:
        for label in VARIANTS:
            folder=out/'integration'/stem/label;summary=real_entry(out,folder,stem,label)
            old_control=label in ['SYNC_ORIGINAL','SHARE_ORIGINAL','NSGA']
            if old_control:
                reference=out/'frozen-control'/stem/label;real_entry(out,reference,stem,label,frozen=True)
                assert (folder/'solutions.jsonl').read_bytes()==(reference/'solutions.jsonl').read_bytes()
            checks.append({'instance':stem,'variant':label,'FE':summary['successful'],'frozenControlByteExact':old_control})
            print('CENTER_LAST_FE_PASS',stem,label,flush=True)
    for label in VARIANTS:real_entry(out,out/'interruptions'/label,'20_2_3_1',label,seconds=.3,fe=9223372036854775807)
    write_once(out/'source-manifest.json',{str(p.relative_to(ROOT)):digest(p) for folder in ['src/java','src/algorithms'] for p in (ROOT/folder).rglob('*.java')})
    write_once(out/'acceptance.json',{'status':'passed','realEntryChecks':checks,'metadataDoesNotAffectPoolChoice':True,
        'originalControlsMatchFrozen':True,'centerOffsetsVerified':True,'fullGenerationOpportunitiesVerified':True,
        'PDDRAndFamilyQuotasReplayed':True,'paidFragmentProvenanceVerified':True,'timeInterruptions':list(VARIANTS),'qualitySelectedParameters':False})
    print('CENTER_LAST_ENGINEERING_ACCEPTED',out,flush=True)


if __name__=='__main__':verify()
