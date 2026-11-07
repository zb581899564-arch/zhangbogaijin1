"""Resolve actual immutable decoder policy before considering any representation extension."""
from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, write_once, execute

KERNEL = ROOT / 'runs/action-feedback-probe-20261105-094303-818797'
CLASSES = (
    'org.uma.jmetal.util.research.model.DynamicDecoder',
    'org.uma.jmetal.util.research.model.DynamicValidator',
    'org.uma.jmetal.util.research.model.DynamicStageState',
    'org.uma.jmetal.util.research.model.DynamicPhysics',
    'org.uma.jmetal.util.research.model.DynamicSchedule',
)


def main():
    root = ROOT / 'runs' / datetime.now().strftime('decoder-control-contract-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('DECODER_CONTROL_ROOT', root, flush=True)
    shutil.copy2(Path(__file__), root / Path(__file__).name)
    write_once(root / 'protocol.json', {
        'kind': 'Zero-FE actual-class/source contract audit, not an outcome or performance experiment',
        'classpathSource': str(KERNEL), 'classes': CLASSES, 'searchFE': 0, 'decoderCalls': 0,
        'question': 'Does the loaded common decoder expose later-stage resource decisions? '
                    'Does its validator enforce the same binding policy, separately from physical feasibility?',
        'scope': 'Record identity/JDK/bytecode. No policy relaxation, new representation, '
                 'candidate evaluation, mainline change, download or external transfer.'})
    cp = (KERNEL / 'classpath.txt').read_text(encoding='utf-8-sig').strip()
    (root / 'classpath.txt').write_text(cp, encoding='utf-8')
    execute(['java', '-cp', cp, 'research.dynamic.ClassResolutionProbe', *CLASSES],
            root / 'class-identity.json')
    identity = read(root / 'class-identity.json')
    javap = Path(identity['javaHome']) / 'bin/javap.exe'
    assert javap.is_file(), 'Use the actual JDK tools; do not alter PATH or install dependencies'
    for name in CLASSES:
        execute([str(javap), '-p', '-c', '-classpath', cp, name], root / f'{name.rsplit(".", 1)[-1]}.javap.txt')
    decoder = (root / 'DynamicDecoder.javap.txt').read_text(encoding='utf-8')
    validator = (root / 'DynamicValidator.javap.txt').read_text(encoding='utf-8')
    assert decoder.count('DynamicStageState.firstAvailable:') == 2
    assert validator.count('Method earliest:') == 2
    assert 'DynamicStageState.preview:' in decoder and 'Method auditOperation:' in validator
    write_once(root / 'status.json', {
        'status': 'IDENTITY_AND_POLICY_RECORDED', 'searchFE': 0, 'decoderCalls': 0,
        'laterStageMachineAndWorkerSelections': 'Two independent firstAvailable calls in decodeFactory',
        'validator': 'Also enforces earliest machine/worker. It is not only a broad physical feasibility audit.',
        'unproven': 'Physical-resource representation extension, new policy correctness, '
                    'existence of useful unrepresentable schedules, objective improvement and algorithm performance.'})
    print('DECODER_CONTROL_COMPLETE zeroFE zeroDecoderCalls', flush=True)


if __name__ == '__main__': main()
