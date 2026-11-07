"""Prospective same-parent, same-native-kernel extra-archive teacher test, locally only."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

from datetime import datetime

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from research.semantic_repair.evidence import digest
from paid_teacher_design import SOURCE, STEMS, PROBE_SEED, prepare, protocol
from paid_teacher_build import build
from paid_teacher_analysis import analyze


def main():
    assert read(SOURCE / 'status.json')['worthTeacherValueProbe']
    root = ROOT / 'runs' / datetime.now().strftime('paid-archive-teacher-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('PAID_ARCHIVE_TEACHER_ROOT', root, flush=True)
    completed = []
    try:
        with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
            design = protocol(); write_once(root / 'protocol.json', design)
            plans = {stem: prepare(root, stem) for stem in STEMS}
            write_once(root / 'planned-fees.json', plans)
            cp = build(root)
            write_once(root / 'input-hashes.json', {str(p.relative_to(root)): digest(p)
                       for stem in STEMS for p in (root / stem / 'inputs').glob('*') if p.is_file()})
            specs = {s['stem']: s for s in design['instances']}
            for stem in STEMS:
                folder = root / stem; inputs = folder / 'inputs'
                command = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'research.dynamic.PaidArchiveTeacherProbe',
                           str(inputs / f'{stem}.txt'), str(inputs / 'RECONSTRUCTED-setup.txt'),
                           str(inputs / 'fatigue-input.txt'), str(folder / 'guides.tsv'),
                           str(folder / 'recipients.tsv'), str(folder / 'probe'), str(PROBE_SEED)]
                write_once(folder / 'command.json', command); print('PAID_TEACHER_START', stem, flush=True)
                execute(command, folder / 'run.log', timeout=300)
                receipt, = rows(folder / 'probe/receipt.jsonl')
                assert receipt['successfulFE'] == receipt['attemptedFE'] == receipt['fullDecoderQA'] == plans[stem]
                assert receipt['failedFE'] == 0
                result = analyze(root, specs[stem]); completed.append(result)
                print('PAID_TEACHER_ANALYZED', stem, 'eligible', result['worthNativeClosedLoopDesign'], flush=True)
            worth = all(result['worthNativeClosedLoopDesign'] for result in completed)
            write_once(root / 'analysis.json', {'instances': completed, 'worthNativeClosedLoopDesign': worth})
    except BaseException as error:
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': str(error),
                                         'completedInstances': [r['stem'] for r in completed]})
        raise
    write_once(root / 'status.json', {'status': 'COMPLETE', 'successfulFE': sum(plans.values()),
        'failedFE': 0, 'offspringFE': 7680, 'commonPaidSourceReconstructionFE': sum(plans.values()) - 7680,
        'fullDecoderQA': sum(plans.values()), 'worthNativeClosedLoopDesign': worth})
    print('PAID_ARCHIVE_TEACHER_COMPLETE', 'worthNativeClosedLoopDesign', worth, flush=True)


if __name__ == '__main__': main()
