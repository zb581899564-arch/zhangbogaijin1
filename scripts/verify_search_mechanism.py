"""Targeted acceptance: observers preserve trajectories, variants stay legal, probes replay."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from research.search_mechanism.protocol import PREVIOUS, VARIANTS
from research.semantic_repair.evidence import read, write_once
from research.semantic_repair.diagnostics import validate_trace
from verify_semantic_repair import validate_pool_scores


def execute(build, folder, stem, label, *, frozen=False, seconds='Infinity', fe=20000):
    folder.mkdir(parents=True)
    inputs = PREVIOUS / 'inputs' / stem
    cp = ((PREVIOUS if frozen else build) / 'classpath.txt').read_text(encoding='utf-8').strip()
    spec = VARIANTS[label]
    cmd = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'research.dynamic.DynamicRun',
           str(inputs / (stem + '.txt')), str(inputs / 'RECONSTRUCTED-setup.txt'),
           str(inputs / 'fatigue-input.txt'), str(folder), spec['mode'], str(fe), '4242421',
           str(seconds), '1.0', 'true', 'false', '0', 'true', 'SCREEN', '0', spec['profile'], 'true']
    if not frozen:
        cmd += ['true', str(spec['parents']).lower()]
    write_once(folder / 'command.json', cmd)
    with (folder / 'run.log').open('x', encoding='utf-8') as log:
        completed = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    if completed.returncode:
        raise RuntimeError((folder / 'run.log').read_text(encoding='utf-8', errors='replace')[-3000:])
    summary = read(folder / 'summary.json')
    assert summary['status'] == 'passed' and summary['failed'] == summary['timeInterruptedAttempts']
    assert summary['offlineValidationDecodes'] == summary['archiveSize']
    trace = [json.loads(line) for line in (folder / 'semantic-trace.jsonl').read_text().splitlines()]
    validate_trace(trace, summary['semanticAudit'], summary)
    validate_pool_scores(trace)
    if not frozen:
        evidence = [json.loads(line) for line in (folder / 'mechanism-trace.jsonl').read_text().splitlines()]
        generations = [row for row in evidence if row['type'] == 'generation' and row['complete']]
        if seconds == 'Infinity':
            assert summary['successful'] == fe and len(generations) > 0
        if spec['parents']:
            assert all(len(row['candidates']) == 300 for row in trace[1:])
        assert len([row for row in evidence if row['type'] == 'kernel-case']) <= 24
    return summary


def verify(build):
    build = Path(build).resolve()
    from dynamic_build import build_dynamic
    cp = build_dynamic(build, skip_maven=True)
    (build / 'classpath.txt').write_text(cp, encoding='utf-8')
    for name in ['org.uma.jmetal.util.research.mechanism.KernelContractChecks',
                 'org.uma.jmetal.util.research.search.SelectionSemanticsChecks']:
        log = build / (name.rsplit('.', 1)[-1] + '.log')
        with log.open('x', encoding='utf-8') as stream:
            result = subprocess.run(['java', '-Xmx768m', '-cp', cp, name], cwd=ROOT,
                                    stdout=stream, stderr=subprocess.STDOUT, timeout=60)
        if result.returncode:
            raise RuntimeError(log.read_text(encoding='utf-8', errors='replace'))
        print(name, 'PASS', flush=True)
    checks = []
    for stem in ['20_2_3_1', '200_8_5_1']:
        for label in ['SO', 'SHARE', 'NSGA']:
            new = build / 'trajectory' / stem / label
            old = build / 'frozen-control' / stem / label
            summary = execute(build, new, stem, label)
            execute(build, old, stem, label, frozen=True)
            assert (new / 'solutions.jsonl').read_bytes() == (old / 'solutions.jsonl').read_bytes()
            checks.append({'instance': stem, 'variant': label, 'fixedFE': summary['successful'], 'frozenArchiveByteExact': True})
            print('TRAJECTORY_BYTE_EXACT', stem, label, flush=True)
    for label in ['SO_PARENT', 'SHARE_PARENT']:
        summary = execute(build, build / 'parent-variant' / label, '20_2_3_1', label)
        checks.append({'variant': label, 'parentPool': 300, 'fixedFE': summary['successful']})
    for label in VARIANTS:
        execute(build, build / 'time-interruption' / label, '20_2_3_1', label,
                seconds=.3, fe=9223372036854775807)
    write_once(build / 'acceptance.json', {'status': 'passed', 'trajectoryChecks': checks,
               'timeInterruptions': list(VARIANTS), 'newPaidSearchModes': 'diagnostic only; no quality selection',
               'kernelContractChecksFE': 0, 'allCapturedPDDRReplayed': True})
    print('SEARCH_MECHANISM_ENGINEERING_PASS', build, flush=True)


if __name__ == '__main__':
    verify(sys.argv[1])
