from datetime import datetime
from pathlib import Path
import shutil
import sys
import time
from research.semantic_repair.evidence import read,write_once,status,digest,_freeze_classpath
from research.semantic_repair.execution import controller_lock
from research.sync_job_audit.execution import Deadline
from .protocol import ROOT,PREVIOUS,make_protocol,jobs
from .execution import run_one
from .analysis import analyze


def prepare(engineering):
    engineering=Path(engineering).resolve();acceptance=read(engineering/'acceptance.json')
    if acceptance['status']!='passed':raise ValueError('Engineering acceptance required')
    for name,expected in read(engineering/'source-manifest.json').items():
        if digest(ROOT/name)!=expected:raise ValueError('Accepted Java source changed: '+name)
    root=ROOT/'runs'/datetime.now().strftime('center-last-%Y%m%d-%H%M%S-%f');root.mkdir()
    write_once(root/'clock.json',{'startedEpoch':time.time(),'wallCapSeconds':2700})
    protocol=make_protocol(read(PREVIOUS/'protocol.json'));write_once(root/'protocol.json',protocol);write_once(root/'run-order.json',jobs(protocol))
    write_once(root/'engineering-acceptance.json',acceptance)
    for row in protocol['instances']:shutil.copytree(PREVIOUS/'inputs'/row['stem'],root/'inputs'/row['stem'])
    _freeze_classpath(engineering,root);manifest={}
    folders=['src/java','src/algorithms','research/center_last','research/sync_job_audit','research/semantic_repair','research/dynamic_benchmark','research/expansion_screen']
    for folder in folders:
        for source in (ROOT/folder).rglob('*'):
            if source.suffix not in ('.java','.py'):continue
            relative=source.relative_to(ROOT);target=root/'source'/relative;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target);manifest[str(relative)]=digest(target)
    write_once(root/'source-manifest.json',manifest)
    paths=[p for folder in ['inputs','binary','source'] for p in (root/folder).rglob('*') if p.is_file()]
    paths += [root/name for name in ['clock.json','protocol.json','run-order.json','classpath.txt']]
    write_once(root/'frozen-artifacts.json',{str(p.relative_to(root)):digest(p) for p in paths});return root


def campaign(engineering=None,resume=None):
    root=Path(resume).resolve() if resume else prepare(engineering)
    if (root/'final-status.json').exists():raise RuntimeError('Completed campaign cannot restart')
    for name,expected in read(root/'frozen-artifacts.json').items():
        if digest(root/name)!=expected:raise ValueError('Frozen artifact changed: '+name)
    for name,expected in read(root/'source-manifest.json').items():
        if name.endswith('.py') and digest(ROOT/name)!=expected:raise ValueError('Use frozen Python source: '+name)
    deadline=Deadline(root);deadline.require();protocol=read(root/'protocol.json');instances={r['stem']:r for r in protocol['instances']}
    print('CENTER_LAST_ROOT',root,flush=True)
    with controller_lock(root):
        try:
            for number,job in enumerate(jobs(protocol),1):
                _,dispatched=run_one(root,job,instances[job['instance']],protocol['variants'][job['variant']],deadline)
                status(root,{'status':'RUNNING','completed':number,'expected':150,'wallSeconds':deadline.elapsed(),'last':job})
                print('CENTER_LAST',number,'/150',job['instance'],job['variant'],'new' if dispatched else 'preserved',flush=True)
            output=analyze(root,deadline);deadline.require()
            result={'status':'CENTER_LAST_COMPLETE','completed':150,'analysis':str(output.relative_to(root)),'wallSeconds':deadline.elapsed(),'formalStep6Started':False,'automaticFurtherExperiments':False}
            write_once(root/'final-status.json',result);status(root,result);print('CENTER_LAST_COMPLETE',output,flush=True)
        except BaseException as error:
            status(root,{'status':'STOPPED_EVIDENCE_PRESERVED','error':str(error),'wallSeconds':deadline.elapsed()});raise
    return root


if __name__=='__main__':
    campaign(resume=sys.argv[2]) if sys.argv[1]=='--resume' else campaign(engineering=sys.argv[1])
