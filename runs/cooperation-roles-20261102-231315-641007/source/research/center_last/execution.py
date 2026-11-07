import subprocess
import time
from research.semantic_repair.evidence import read, write_once
from research.sync_job_audit.execution import Deadline, command
from .protocol import ROOT, trial_folder
from .analysis import load_run


def run_one(root, job, instance, spec, deadline):
    folder = trial_folder(root, job); cmd = command(root, folder, job, spec)
    if folder.exists():
        required = ['summary.json','solutions.jsonl','anytime.jsonl','semantic-trace.jsonl','feedback-trace.jsonl','execution.json','command.json']
        if job['variant'] != 'NSGA': required.append('composition-trace.jsonl')
        if not all((folder / name).exists() for name in required): raise RuntimeError('Incomplete owner preserved: '+str(folder))
        if read(folder/'command.json') != cmd: raise ValueError('Frozen job differs')
        return load_run(root,job,instance,spec),False
    deadline.require(job['seconds']+5);folder.mkdir(parents=True);write_once(folder/'command.json',cmd)
    start=time.monotonic()
    with (folder/'run.log').open('x',encoding='utf-8') as log:
        result=subprocess.run(cmd,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=min(deadline.remaining(),max(60.,job['seconds']*3+30)))
    process_wall=time.monotonic()-start
    if result.returncode:raise RuntimeError('Owned JVM failed; evidence preserved: '+str(folder))
    start=time.monotonic();run=load_run(root,job,instance,spec)
    receipt={'processWallSeconds':process_wall,'controllerValidationSeconds':time.monotonic()-start}
    write_once(folder/'execution.json',receipt);run['execution']=receipt;deadline.require();return run,True
