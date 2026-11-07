"""Engineering then32prospective same-FE/true-time runs, no mainline replacement."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

from datetime import datetime
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock
from research.semantic_repair.evidence import digest
from conditional_exchange_design import AUDIT, SOURCE, SEEDS, ARMS, FE_LIMIT, TIME_FE_CAP, protocol
from conditional_exchange_build import build
from conditional_exchange_execution import engineering, run, paired_acceptance
from conditional_exchange_analysis import analyze


def fees(root):
    receipts = [rows(p)[0] for p in root.glob('*/*/run-receipt.jsonl')]
    return {'runsWithReceipts': len(receipts), 'successfulFE': sum(r['successful'] for r in receipts),
            'attemptedFE': sum(r['attempted'] for r in receipts), 'failedFE': sum(r['failed'] for r in receipts),
            'timeInterruptedAttempts': sum(r['timeInterruptedAttempts'] for r in receipts),
            'checkpointFullDecoderQA': sum(read(p)['uniqueOfflineDecodes'] for p in root.glob('*/*/checkpoint-validation.json'))}


def main():
    assert read(AUDIT / 'status.json')['allObserversEquivalent']
    root = ROOT / 'runs' / datetime.now().strftime('conditional-exchange-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('CONDITIONAL_EXCHANGE_ROOT', root, flush=True)
    try:
        with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
            plan = protocol();write_once(root / 'protocol.json', plan)
            specs = {s['stem']: s for s in plan['instances']}
            for stem in specs: shutil.copytree(SOURCE / stem / 'inputs', root / stem / 'inputs')
            write_once(root / 'input-hashes.json', {str(p.relative_to(root)): digest(p)
                       for stem in specs for p in (root / stem / 'inputs').glob('*') if p.is_file()})
            cp = build(root);engineering(root, cp, specs)
            for case in plan['order']:
                stem, seed, arm, budget = (case[k] for k in ('stem', 'seed', 'arm', 'budget'))
                method, enabled = arm.split('_'); enabled = enabled == 'ON'
                seconds = float('inf') if budget == 'FE' else specs[stem]['time_seconds']
                limit = FE_LIMIT if budget == 'FE' else TIME_FE_CAP
                run(root, cp, specs[stem], f'{budget}-{seed}-{arm}', method, enabled, seed,
                    limit=limit, seconds=seconds)
            paired_acceptance(root, specs, SEEDS, ARMS);result = analyze(root, specs)
    except BaseException as error:
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), **fees(root)});raise
    actual = fees(root); assert actual['attemptedFE'] == actual['successfulFE'] + actual['timeInterruptedAttempts']
    write_once(root / 'status.json', {'status': 'COMPLETE', **actual, 'unexpectedEvaluationFailures': 0,
        'engineeringAccepted': True, 'worthFullComparisonDesign': result['worthFullComparisonDesign'],
        'defaultMainlineChanged': False, 'goalAchieved': False})
    print('CONDITIONAL_EXCHANGE_COMPLETE', result['decision'], actual, flush=True)


if __name__ == '__main__': main()
