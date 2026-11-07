"""Engineering -> fixed-FE pilot -> conditional true-time pilot; stop exactly at registered failure."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

from datetime import datetime
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, controller_lock
from research.semantic_repair.evidence import digest
from program_exit_design import AUDIT, SOURCE, FE_LIMIT, TIME_FE_CAP, protocol
from program_exit_build import build
from program_exit_execution import engineering, run, pairing
from program_exit_analysis import analyze_budget


def fees(root):
    receipts = [rows(p)[0] for p in root.glob('*/*/run-receipt.jsonl')]
    return {'runsWithReceipts': len(receipts), 'successfulFE': sum(r['successful'] for r in receipts),
        'attemptedFE': sum(r['attempted'] for r in receipts), 'failedFE': sum(r['failed'] for r in receipts),
        'timeInterruptedAttempts': sum(r['timeInterruptedAttempts'] for r in receipts),
        'checkpointFullDecoderQA': sum(read(p)['uniqueOfflineDecodes'] for p in root.glob('*/*/checkpoint-validation.json'))}


def science_budget(root, cp, specs, plan, budget):
    for case in plan['order' + budget]:
        spec = specs[case['stem']];method, flag = case['arm'].split('_')
        run(root, cp, spec, f'{budget}-{case["seed"]}-{case["arm"]}', method, flag == 'ON', case['seed'],
            limit=FE_LIMIT if budget == 'FE' else TIME_FE_CAP,
            seconds=float('inf') if budget == 'FE' else spec['time_seconds'])
    pairing(root, specs, budget)
    return analyze_budget(root, specs, budget)


def main():
    with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
        assert read(AUDIT / 'status.json')['worthMatchedIndicatorContinuation']
        root = ROOT / 'runs' / datetime.now().strftime('program-exit-pilot-%Y%m%d-%H%M%S-%f');root.mkdir()
        print('PROGRAM_EXIT_PILOT_ROOT', root, flush=True)
        try:
            plan = protocol();write_once(root / 'protocol.json', plan);specs = {s['stem']: s for s in plan['instances']}
            for stem in specs: shutil.copytree(SOURCE / stem / 'inputs', root / stem / 'inputs')
            write_once(root / 'input-hashes.json', {str(p.relative_to(root)): digest(p)
                for stem in specs for p in (root / stem / 'inputs').glob('*') if p.is_file()})
            cp = build(root);engineering(root, cp, specs)
            first = science_budget(root, cp, specs, plan, 'FE');second = None
            if first['pass']: second = science_budget(root, cp, specs, plan, 'TIME')
            passed = first['pass'] and second is not None and second['pass']
            result = {'sameFEStagePassed': first['pass'], 'timeStageStarted': second is not None,
                'sameTimeStagePassed': None if second is None else second['pass'],
                'worthFull500kRoleShareLiProtocol': passed, 'goalAchieved': False,
                'decision': 'DESIGN_FULL_500K_ROLE_SHARE_LI_COMPARISON' if passed else 'STOP_EXACT_CENTER_OUTER_HV_RULE',
                'noMainlineChange': True}
            write_once(root / 'analysis.json', result)
        except BaseException as error:
            write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), **fees(root)});raise
        actual = fees(root)
        assert actual['attemptedFE'] == actual['successfulFE'] + actual['timeInterruptedAttempts']
        write_once(root / 'status.json', {'status': 'COMPLETE', **actual, 'unexpectedEvaluationFailures': 0,
            'engineeringAccepted': True, **result})
        print('PROGRAM_EXIT_PILOT_COMPLETE', result, actual, flush=True)


if __name__ == '__main__': main()
