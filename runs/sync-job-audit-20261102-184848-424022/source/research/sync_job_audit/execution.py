from pathlib import Path
import subprocess
import time
from research.semantic_repair.evidence import read, write_once
from research.semantic_repair.execution import command as base_command
from .protocol import ROOT, trial_folder
from .analysis import load_run


class Deadline:
    def __init__(self, root):
        clock = read(root / 'clock.json')
        self.limit = clock['wallCapSeconds']
        if self.limit != 2700: raise ValueError('Original45-minute cap changed')
        self.offset = max(0., time.time() - clock['startedEpoch']); self.start = time.monotonic()
    def elapsed(self): return self.offset + time.monotonic() - self.start
    def remaining(self): return max(0., self.limit - self.elapsed())
    def require(self, margin=0):
        if self.remaining() <= margin: raise TimeoutError('Original campaign clock exhausted; evidence preserved')


def command(root, folder, job, spec):
    return base_command(root, folder, job, spec) + ['false', 'false', 'true']


def run_one(root, job, instance, spec, deadline):
    folder = trial_folder(root, job); cmd = command(root, folder, job, spec)
    if folder.exists():
        required = ['summary.json', 'solutions.jsonl', 'anytime.jsonl', 'semantic-trace.jsonl', 'feedback-trace.jsonl', 'execution.json', 'command.json']
        if not all((folder / name).exists() for name in required):
            raise RuntimeError('Incomplete owner preserved; no automatic rerun: ' + str(folder))
        if read(folder / 'command.json') != cmd: raise ValueError('Frozen job command differs')
        return load_run(root, job, instance, spec), False
    deadline.require(job['seconds'] + 5); folder.mkdir(parents=True); write_once(folder / 'command.json', cmd)
    start = time.monotonic()
    with (folder / 'run.log').open('x', encoding='utf-8') as stream:
        result = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                timeout=min(deadline.remaining(), max(60., job['seconds'] * 3 + 30)))
    process_wall = time.monotonic() - start
    if result.returncode: raise RuntimeError('Owned JVM failed; partial evidence preserved: ' + str(folder))
    start = time.monotonic(); run = load_run(root, job, instance, spec)
    receipt = {'processWallSeconds': process_wall, 'controllerValidationSeconds': time.monotonic() - start}
    write_once(folder / 'execution.json', receipt); run['execution'] = receipt; deadline.require()
    return run, True
