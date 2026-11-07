"""Isolated, locally executed prerequisite test. No complete optimizer is modified."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest
from action_feedback_design import KERNEL, SOURCE, STEMS, prepare, protocol
from action_feedback_analysis import analyze


def build(root):
    source, classes = root / 'source', root / 'classes'
    source.mkdir(); classes.mkdir()
    for name in ('ActionStateFeatures', 'ActionFeedbackProbe', 'NeutralProbeSupport', 'ClassResolutionProbe'):
        shutil.copy2(ROOT / f'src/algorithms/diagnostics/{name}.java', source)
    for name in ('run_action_feedback_probe.py', 'action_feedback_design.py',
                 'action_feedback_models.py', 'action_feedback_analysis.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    shutil.copytree(ROOT / 'research/composition_oracle', source / 'composition_oracle',
                    ignore=shutil.ignore_patterns('__pycache__'))
    base = (KERNEL / 'classpath.txt').read_text(encoding='utf-8-sig').strip()
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base,
             '-d', str(classes), *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{base}'
    (root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'class-hashes.json', class_hashes(classes))
    write_once(root / 'source-hashes.json', {str(path.relative_to(source)): digest(path)
                                           for path in source.rglob('*') if path.is_file()})
    execute(['java', '-cp', cp, 'research.dynamic.ClassResolutionProbe',
             'org.uma.jmetal.util.research.search.IntraNeighborhoods',
             'org.uma.jmetal.util.research.search.ParticleOperators',
             'org.uma.jmetal.util.research.SchedulingEncoding',
             'org.uma.jmetal.util.research.DynamicEvaluation',
             'org.uma.jmetal.util.research.model.DynamicDecoder',
             'org.uma.jmetal.util.research.runtime.RunContext'], root / 'loaded-identity.json')
    return cp


def run_instance(root, cp, spec):
    stem = spec['stem']; folder = root / stem; inputs = folder / 'inputs'
    command = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'research.dynamic.ActionFeedbackProbe',
               str(inputs / f'{stem}.txt'), str(inputs / 'RECONSTRUCTED-setup.txt'),
               str(inputs / 'fatigue-input.txt'), str(folder / 'cases.tsv'), str(folder / 'probe'),
               ','.join(map(str, spec['normalization']['scale']))]
    write_once(folder / 'command.json', command)
    print('ACTION_FEEDBACK_START', stem, flush=True)
    execute(command, folder / 'run.log')
    receipt = rows(folder / 'probe/receipt.jsonl')[0]
    assert receipt['status'] == 'COMPLETE'
    assert receipt['successfulFE'] == receipt['attemptedFE'] == receipt['fullDecoderQA'] == 7104
    assert receipt['failedFE'] == 0
    result = analyze(root, spec)
    print('ACTION_FEEDBACK_ANALYZED', stem, 'eligible', result['worthNativeClosedLoopDesign'], flush=True)
    return result


def main():
    root = ROOT / 'runs' / datetime.now().strftime('action-feedback-probe-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('ACTION_FEEDBACK_ROOT', root, flush=True)
    completed = []
    try:
        with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
            design = protocol(); write_once(root / 'protocol.json', design)
            cp = build(root)
            for stem in STEMS: prepare(root, stem)
            write_once(root / 'input-hashes.json', {str(path.relative_to(root)): digest(path)
                       for stem in STEMS for path in (root / stem / 'inputs').glob('*') if path.is_file()})
            specs = {spec['stem']: spec for spec in design['instances']}
            for stem in STEMS: completed.append(run_instance(root, cp, specs[stem]))
            worth = all(result['worthNativeClosedLoopDesign'] for result in completed)
            write_once(root / 'analysis.json', {'instances': completed, 'worthNativeClosedLoopDesign': worth})
    except BaseException as error:
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': str(error),
                                         'completedInstances': [result['stem'] for result in completed]})
        raise
    write_once(root / 'status.json', {'status': 'COMPLETE', 'successfulFE': 14208, 'failedFE': 0,
                                     'fullDecoderQA': 14208, 'worthNativeClosedLoopDesign': worth})
    print('ACTION_FEEDBACK_COMPLETE', 'worthNativeClosedLoopDesign', worth, flush=True)


if __name__ == '__main__': main()
