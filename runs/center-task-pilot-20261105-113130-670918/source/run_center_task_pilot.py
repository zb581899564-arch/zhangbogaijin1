"""Local-only, finite prospective pilot of complete generation-owned CENTER tasks."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

from datetime import datetime

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from research.semantic_repair.evidence import digest
from center_task_design import CAPACITY, STEMS, SEEDS, design, prepare_inputs, ledger, run_order
from center_task_build import build
from center_task_execution import engineering, run
from center_task_analysis import analyze


def accounting(root):
    receipts = [rows(p)[0] for p in root.glob('*/*/run-receipt.jsonl')]
    return {'actualRunsWithReceipts': len(receipts),
            'successfulFE': sum(r['successful'] for r in receipts),
            'attemptedFE': sum(r['attempted'] for r in receipts), 'failedFE': sum(r['failed'] for r in receipts),
            'checkpointFullDecoderQA': sum(read(p)['uniqueOfflineDecodes']
                                           for p in root.glob('*/*/checkpoint-validation.json'))}


def freeze(root):
    protocol = design(); order = run_order(); protocol['order'] = order
    write_once(root / 'protocol.json', protocol)
    prepare_inputs(root)
    for stem in STEMS:
        for seed in SEEDS: ledger(root / stem / f'ledger-{seed}.csv', stem, seed)
    write_once(root / 'input-and-ledger-hashes.json', {str(p.relative_to(root)): digest(p)
        for stem in STEMS for p in (root / stem).rglob('*') if p.is_file()})
    execute(['java', '-version'], root / 'jdk-version.log')
    execute(['javac', '-version'], root / 'javac-version.log')
    cp = build(root)
    return {s['stem']: s for s in protocol['instances']}, order, cp


def main():
    assert read(CAPACITY / 'analysis.json')['worthPersistentTaskProtocol']
    root = ROOT / 'runs' / datetime.now().strftime('center-task-pilot-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('CENTER_TASK_PILOT_ROOT', root, flush=True)
    try:
        with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
            specs, order, cp = freeze(root)
            engineering(root, cp, specs)
            for case in order:
                stem, seed, arm = (case[k] for k in ('stem', 'seed', 'arm'))
                run(root, cp, specs[stem], f'{seed}-{arm}', arm, seed, root / stem / f'ledger-{seed}.csv')
            result = analyze(root, specs)
    except BaseException as error:
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), **accounting(root)})
        raise
    fees = accounting(root)
    assert fees['successfulFE'] == fees['attemptedFE'] == 398420 and fees['failedFE'] == 0
    write_once(root / 'status.json', {'status': 'COMPLETE', **fees,
        'engineeringAccepted': True, 'worthFullRegimeDesign': result['worthFullRegimeDesign'],
        'defaultMainlineChanged': False, 'transfersOrDownloads': False, 'goalAchieved': False})
    print('CENTER_TASK_PILOT_COMPLETE', result['decision'], fees, flush=True)


if __name__ == '__main__': main()
