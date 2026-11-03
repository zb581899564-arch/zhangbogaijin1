"""Accept H1/H2 mechanisms and complete checkpoint genomes before overnight performance."""
from datetime import datetime
from pathlib import Path
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dynamic_build import build_dynamic
from research.semantic_repair.evidence import read, write_once, digest
from research.semantic_repair.diagnostics import validate_trace
from verify_semantic_repair import validate_pool_scores
from research.night_research.protocol import make_protocol
from research.night_research.observations import attach_observation
from research.night_research.checkpoint_evidence import validate_checkpoint_evidence
from research.night_research.execution import run_one
from research.night_research.clock import Deadline

INPUT_SOURCE = ROOT / 'runs/cooperation-roles-20261102-231315-641007'
FROZEN = ROOT / 'runs/demand-feedback-20261102-234716-144779'


def configs():
    paths = [ROOT / 'research/night_research' / name for name in ['h1_context_v1.json', 'h2_packet_v1.json']]
    protocols = [make_protocol(read(path)) for path in paths]
    unique = {}
    for protocol in protocols:
        for spec in protocol['variants'].values():
            key = (spec['mode'], spec['profile'], spec['setting'])
            if key in unique and unique[key] != spec:
                raise ValueError('A shared engineering mode has inconsistent contracts')
            unique[key] = spec
    return protocols, list(unique.values())


def invoke(build, folder, stem, spec, frozen=False):
    folder.mkdir(parents=True)
    cp = ((FROZEN if frozen else build) / 'classpath.txt').read_text(encoding='utf-8-sig').strip()
    inputs = INPUT_SOURCE / 'inputs' / stem
    cmd = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'research.dynamic.DynamicRun',
        str(inputs / (stem + '.txt')), str(inputs / 'RECONSTRUCTED-setup.txt'), str(inputs / 'fatigue-input.txt'), str(folder),
        spec['mode'], '20000', '4242421', 'Infinity', '1.0', 'true', 'false', '0', 'true', 'SCREEN', str(spec['setting']),
        spec['profile'], 'true', 'false', 'false', 'false', 'false', 'SNAPSHOT_GENOMES']
    write_once(folder / 'command.json', cmd)
    started = time.monotonic()
    with (folder / 'run.log').open('x', encoding='utf-8') as log:
        result = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    if result.returncode:
        raise RuntimeError((folder / 'run.log').read_text(encoding='utf-8', errors='replace')[-4000:])
    summary = read(folder / 'summary.json')
    assert summary['status'] == 'passed' and summary['successful'] == summary['attempted'] == 20000
    assert summary['archiveSize'] == summary['offlineValidationDecodes']
    trace = [json.loads(line) for line in (folder / 'semantic-trace.jsonl').read_text(encoding='utf-8').splitlines()]
    validate_trace(trace, summary['semanticAudit'], summary)
    if spec['profile'] == 'SO':
        validate_pool_scores(trace)
    if not frozen:
        # JSON null is the exact representation of the registered infinite time budget.
        infinite = dict(summary, timeLimitSeconds=float('inf'))
        point_rows = [json.loads(line) for line in (folder / 'anytime.jsonl').read_text(encoding='utf-8').splitlines()]
        instance = {'stem': stem}
        validate_checkpoint_evidence(folder, point_rows, infinite, instance)
        attach_observation({'summary': infinite, 'folder': str(folder)}, spec)
        if spec.get('observation') == {'schema': 'context-renewal-v1'}:
            assert summary['cooperation']['contextRenewal']['eventsCompleted'] > 0
        if spec.get('observation') == {'schema': 'factory-transfer-v1'}:
            assert summary['cooperation']['factoryTransfer']['paidTransfers'] > 0
    return summary, time.monotonic() - started


def checks(build, cp):
    names = ['org.uma.jmetal.util.research.cooperation.NightCooperationChecks',
        'org.uma.jmetal.util.research.runtime.CheckpointGenomeChecks', 'org.uma.jmetal.util.research.runtime.AnytimeChecks',
        'org.uma.jmetal.util.research.search.SearchChecks']
    for name in names:
        chapters = [3, 4] if name.endswith('SearchChecks') else [None]
        for chapter in chapters:
            label = name.rsplit('.', 1)[-1] + (str(chapter) if chapter else '')
            with (build / (label + '.log')).open('x', encoding='utf-8') as log:
                cmd = ['java', '-Xmx768m', '-cp', cp, name] + ([str(chapter)] if chapter else [])
                if name.endswith('CheckpointGenomeChecks'):
                    cmd.append(str(build / 'checkpoint-unit'))
                result = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=90)
            if result.returncode:
                raise RuntimeError((build / (label + '.log')).read_text(encoding='utf-8', errors='replace'))
            print(label, 'PASS', flush=True)


def smoke(build, cp, protocols, specs):
    # Use the actual night loader against legal short TIME_LIMIT runs; no quality interpretation.
    scratch = build / 'loader-smoke'; scratch.mkdir()
    (scratch / 'classpath.txt').write_text(cp, encoding='utf-8')
    (scratch / 'clock.json').write_text(json.dumps({'startedEpoch': time.time(), 'wallCapSeconds': 3600,
        'absoluteStopEpoch': 1793660400}), encoding='utf-8')
    import shutil
    shutil.copytree(INPUT_SOURCE / 'inputs' / '20_2_3_1', scratch / 'inputs' / '20_2_3_1')
    deadline = Deadline(scratch)
    instance = dict(protocols[0]['instances'][0], time_seconds=.35)
    for spec in specs:
        job = {'phase': 'engineering', 'instance': instance['stem'], 'seed': 4242421,
               'variant': spec['mode'], 'seconds': .35}
        run, _ = run_one(scratch, job, instance, spec, deadline)
        assert run['summary']['status'] == 'passed'
        print('NIGHT_LOADER_SMOKE_PASS', spec['mode'], flush=True)


def verify():
    output = ROOT / 'runs' / datetime.now().strftime('night-engineering-%Y%m%d-%H%M%S-%f')
    output.mkdir(); protocols, specs = configs()
    cp = build_dynamic(output, skip_maven=True)
    (output / 'classpath.txt').write_text(cp, encoding='utf-8')
    checks(output, cp); results = []
    for stem in ['20_2_3_1', '200_8_5_1']:
        for spec in specs:
            target = output / 'integration' / stem / spec['mode']
            summary, wall = invoke(output, target, stem, spec)
            control = not spec.get('observation')
            if control:
                reference = output / 'frozen-control' / stem / spec['mode']
                invoke(output, reference, stem, spec, frozen=True)
                assert (target / 'solutions.jsonl').read_bytes() == (reference / 'solutions.jsonl').read_bytes()
            results.append({'instance': stem, 'mode': spec['mode'], 'setting': spec['setting'],
                'FE': 20000, 'originalControlByteExact': control, 'processAndValidationSeconds': wall,
                'checkpointPoints': summary['checkpointEvidence']['checkpointPoints']})
            print('NIGHT_FE_PASS', stem, spec['mode'], flush=True)
    smoke(output, cp, protocols, specs)
    write_once(output / 'source-manifest.json', {str(path.relative_to(ROOT)): digest(path)
        for name in ['src/java', 'src/algorithms'] for path in (ROOT / name).rglob('*.java')})
    write_once(output / 'acceptance.json', {'status': 'passed', 'realEntryChecks': results,
        'defaultControlsMatchFrozen': True, 'H1ContextRenewalAndHistoryReset': True,
        'H2FactoryTransferAndSameMarginalControls': True, 'checkpointGenomeCoverageAndFullReplay': True,
        'newAndOriginalClassicalSettingIdentities': True, 'timeInterruptionAndNightLoader': True,
        'qualitySelectedParameters': False, 'performanceEvidence': False})
    print('NIGHT_ENGINEERING_ACCEPTED', output, flush=True)


if __name__ == '__main__':
    verify()
