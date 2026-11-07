"""Frozen five-way closed-loop matrix with original-clock resume and preserved owners."""
from datetime import datetime
from pathlib import Path
import shutil
import sys
import time

from research.semantic_repair.evidence import read, write_once, status, digest, _freeze_classpath
from research.semantic_repair.execution import CampaignDeadline, controller_lock, run_one
from .protocol import ROOT, PREVIOUS, make_protocol, jobs, trial_folder
from .analysis import analyze, validate_variant


def _freeze_sources(root):
    manifest = {}
    folders = ['src/java', 'src/algorithms', 'research/job_aligned_closure',
               'research/semantic_repair', 'research/expansion_screen', 'research/dynamic_benchmark']
    for folder in folders:
        for source in (ROOT / folder).rglob('*'):
            if source.suffix not in ('.java', '.py'):
                continue
            relative = source.relative_to(ROOT); target = root / 'source' / relative
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
            manifest[str(relative)] = digest(target)
    write_once(root / 'source-manifest.json', manifest)


def prepare(engineering):
    engineering = Path(engineering).resolve()
    acceptance = read(engineering / 'acceptance.json')
    if acceptance['status'] != 'passed':
        raise ValueError('Engineering acceptance required')
    for name, expected in read(engineering / 'source-manifest.json').items():
        if digest(ROOT / name) != expected:
            raise ValueError('Accepted source changed: ' + name)
    root = ROOT / 'runs' / datetime.now().strftime('job-aligned-closure-%Y%m%d-%H%M%S-%f')
    root.mkdir()
    write_once(root / 'clock.json', {'startedEpoch': time.time(), 'wallCapSeconds': 5400})
    protocol = make_protocol(read(PREVIOUS / 'protocol.json'))
    write_once(root / 'protocol.json', protocol)
    write_once(root / 'run-order.json', jobs(protocol))
    write_once(root / 'engineering-acceptance.json', acceptance)
    for instance in protocol['instances']:
        shutil.copytree(PREVIOUS / 'inputs' / instance['stem'], root / 'inputs' / instance['stem'])
    _freeze_classpath(engineering, root); _freeze_sources(root)
    paths = [p for folder in ['inputs', 'binary', 'source'] for p in (root / folder).rglob('*') if p.is_file()]
    paths += [root / name for name in ['protocol.json', 'clock.json', 'run-order.json', 'classpath.txt']]
    write_once(root / 'frozen-artifacts.json', {str(p.relative_to(root)): digest(p) for p in paths})
    status(root, {'status': 'PREPARED', 'completed': 0, 'expected': 150})
    return root


def verify_frozen(root):
    for name, expected in read(root / 'frozen-artifacts.json').items():
        if digest(root / name) != expected:
            raise ValueError('Frozen input/binary/controller changed: ' + name)
    for name, expected in read(root / 'source-manifest.json').items():
        if name.endswith('.py') and digest(ROOT / name) != expected:
            raise ValueError('Use original frozen Python sources to resume: ' + name)


def campaign(engineering=None, resume=None):
    root = Path(resume).resolve() if resume else prepare(engineering)
    if (root / 'final-status.json').exists():
        raise RuntimeError('Completed campaign cannot be restarted')
    verify_frozen(root); deadline = CampaignDeadline(root); deadline.require()
    protocol = read(root / 'protocol.json')
    instances = {row['stem']: row for row in protocol['instances']}
    print('JOB_ALIGNED_CLOSURE_ROOT', root, flush=True)
    with controller_lock(root):
        try:
            for number, job in enumerate(jobs(protocol), 1):
                run, dispatched = run_one(root, trial_folder(root, job), job, instances[job['instance']],
                                          protocol['variants'][job['variant']], deadline)
                validate_variant(run)
                status(root, {'status': 'CLOSURE_RUNNING', 'completed': number, 'expected': 150,
                              'wallSeconds': deadline.elapsed(), 'last': job})
                print('CLOSURE', number, '/150', job['instance'], job['variant'],
                      'new' if dispatched else 'preserved', flush=True)
            output = analyze(root, deadline)
            deadline.require()
            result = {'status': 'JOB_ALIGNED_CLOSURE_COMPLETE', 'completed': 150, 'expected': 150,
                      'analysis': str(output.relative_to(root)), 'wallSeconds': deadline.elapsed(),
                      'formalStep6Started': False, 'automaticFurtherExperiments': False}
            write_once(root / 'final-status.json', result); status(root, result)
            print('JOB_ALIGNED_CLOSURE_COMPLETE', output, flush=True)
        except BaseException as error:
            status(root, {'status': 'STOPPED_EVIDENCE_PRESERVED', 'error': str(error),
                          'wallSeconds': deadline.elapsed(), 'automaticRerun': False})
            raise
    return root


if __name__ == '__main__':
    if sys.argv[1] == '--resume':
        campaign(resume=sys.argv[2])
    else:
        campaign(engineering=sys.argv[1])
