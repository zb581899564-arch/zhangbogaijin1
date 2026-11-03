"""Targeted adapter/entrypoint acceptance, with quality-independent fixed settings."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dynamic_build import build_dynamic
from verify_semantic_repair import validate_pool_scores
from research.semantic_repair.evidence import read, write_once, digest
from research.semantic_repair.diagnostics import validate_trace
from research.job_aligned_closure.protocol import VARIANTS, make_protocol, PREVIOUS
from research.job_aligned_closure.analysis import validate_variant


def real_entry(build, folder, stem, label, *, frozen=False, fe=20000, seconds='Infinity'):
    folder.mkdir(parents=True)
    old = ROOT / 'runs/search-mechanism-20261102-163156-017661'
    cp = ((old if frozen else build) / 'classpath.txt').read_text(encoding='utf-8').strip()
    inputs = PREVIOUS / 'inputs' / stem; spec = VARIANTS[label]
    cmd = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'research.dynamic.DynamicRun',
           str(inputs / (stem + '.txt')), str(inputs / 'RECONSTRUCTED-setup.txt'),
           str(inputs / 'fatigue-input.txt'), str(folder), spec['mode'], str(fe), '4242421',
           str(seconds), '1.0', 'true', 'false', '0', 'true', 'SCREEN', '0', spec['profile'], 'true']
    write_once(folder / 'command.json', cmd)
    with (folder / 'run.log').open('x', encoding='utf-8') as stream:
        result = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=120)
    if result.returncode:
        raise RuntimeError((folder / 'run.log').read_text(encoding='utf-8', errors='replace')[-3000:])
    summary = read(folder / 'summary.json')
    assert summary['status'] == 'passed' and summary['failed'] == summary['timeInterruptedAttempts']
    assert summary['archiveSize'] == summary['offlineValidationDecodes']
    if seconds == 'Infinity':
        assert summary['attempted'] == summary['successful'] == fe
    trace = [json.loads(line) for line in (folder / 'semantic-trace.jsonl').read_text().splitlines()]
    validate_trace(trace, summary['semanticAudit'], summary); validate_pool_scores(trace)
    if spec['profile'] == 'SO':
        assert all(len(row['candidates']) == 200 for row in trace[1:])
    validate_variant({'summary': summary, 'variant': label})
    assert 'mechanismCapture' not in summary and 'retainInitialParents' not in summary
    if label.endswith('_JOB'):
        assert summary['search']['alignedKernelProposals'] > 0
        assert summary['search']['qgs.g1.updates'] > 0
    if label.startswith('SHARE') and seconds == 'Infinity':
        assert summary['cooperation']['assembliesValidated'] == summary['cooperation']['assembliesProposed']
        assert summary['cooperation']['assembliesProposed'] > 0
    return summary


def verify():
    out = ROOT / 'runs' / datetime.now().strftime('job-aligned-engineering-%Y%m%d-%H%M%S-%f'); out.mkdir()
    cp = build_dynamic(out, skip_maven=True); (out / 'classpath.txt').write_text(cp, encoding='utf-8')
    for name in ['KernelContractChecks', 'JobAlignedPolicyChecks']:
        with (out / (name + '.log')).open('x', encoding='utf-8') as stream:
            result = subprocess.run(['java', '-Xmx768m', '-cp', cp,
                                     'org.uma.jmetal.util.research.mechanism.' + name],
                                    cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=60)
        if result.returncode:
            raise RuntimeError((out / (name + '.log')).read_text())
        print(name, 'PASS', flush=True)
    checks = []
    for stem in ['20_2_3_1', '200_8_5_1']:
        for label in VARIANTS:
            new = out / 'integration' / stem / label
            summary = real_entry(out, new, stem, label)
            if label in ['SO', 'SHARE', 'NSGA']:
                old = out / 'frozen-control' / stem / label
                real_entry(out, old, stem, label, frozen=True)
                assert (new / 'solutions.jsonl').read_bytes() == (old / 'solutions.jsonl').read_bytes()
            checks.append({'instance': stem, 'variant': label, 'FE': summary['successful'],
                           'frozenControlByteExact': label in ['SO', 'SHARE', 'NSGA']})
            print('REAL_ENTRY_PASS', stem, label, flush=True)
    for label in VARIANTS:
        real_entry(out, out / 'interruptions' / label, '20_2_3_1', label,
                   fe=9223372036854775807, seconds=.3)
    # No quality information is used to choose the five methods or their settings.
    from research.job_aligned_closure.protocol import jobs
    protocol = make_protocol(read(PREVIOUS / 'protocol.json'))
    assert len(jobs(protocol)) == 150 and protocol['planned_search_seconds'] == 1300
    manifest = {str(p.relative_to(ROOT)): digest(p) for folder in ['src/java', 'src/algorithms']
                for p in (ROOT / folder).rglob('*.java')}
    write_once(out / 'source-manifest.json', manifest)
    write_once(out / 'acceptance.json', {'status': 'passed', 'realEntryChecks': checks,
        'fixedFE20000ControlsMatchPreviousFrozen': True, 'kernelAdapterMatchesPreviousProbeExactly': True,
        'PDDRAndFamilyQuotasReplayed': True, 'sameModelAndBudget': True,
        'timeInterruptions': list(VARIANTS), 'qualitySelectedParameters': False})
    print('JOB_ALIGNED_ENGINEERING_ACCEPTED', out, flush=True)


if __name__ == '__main__':
    verify()
