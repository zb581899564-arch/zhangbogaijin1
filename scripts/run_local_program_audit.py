"""400k read-only original-kernel replays: complete local programs, not another sampler variant."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

from datetime import datetime
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock, hypervolume
from natural_local_support import command, verify
from center_task_checks import off_equivalence
from local_program_build import build
from local_program_analysis import analyze
from research.semantic_repair.evidence import digest
from fa_admission_volume import checks

BASELINE = ROOT / 'runs/factory-cache-potential-20261105-082934-494793'
SEED, LIMIT = 12390003, 100000


def protocol(specs):
    return {'baseline': str(BASELINE), 'instances': specs, 'seed': SEED, 'plannedNewSuccessfulFE': 400000,
        'historicalBaselineFEReusedNotNew': 400000,
        'hypothesis': 'Some physically identity shakes with zero immediate archive gain may still '
                      'have material subsequent descent discovery/retained-endpoint value. Observe '
                      'whole native programs before treating one-candidate change rate as an optimization target.',
        'unit': 'Every original outer VNS iteration: entry, one original shake, original descent, '
                'original outer comparison once. Record all full/partial/zero-paid tails, paidFE and '
                'physical group/factory/operator/reference. No overlapping programs. Whole-kernel '
                'OFF original sampling only, not stopped conditional exchange or empty-neighborhood skipping.',
        'evidence': 'Stream all paid objective rows and archive-changed flags. Offline replay original '
                    'unbounded ND archive exactly, independently recompute every admission and savedFE '
                    'front. Compute sequential HV before/shake/after, and improved endpoint singleHV '
                    'against entry archive. Full programs vs aborted tails separate. Reference and '
                    'every257thprogram starting1 fullgenomes saved, no quality/RNG sampling; physical '
                    'paid birth checked, not mislabeled as exact raw-vector first birth.',
        'gate': 'Eachof4instance/methodcells: >=5completedidentity-shake programs with downstream '
                'HVgain>1e-10, identity downstream gain>=5%ofallcompletedprogramHVgain, >=1identity '
                'program accepted with endpoint singleHVgain>1e-10. All necessary only to allow '
                'a separate matched-parent program probe; not a newlearning/reward rule or performance pass.',
        'engineering': 'Resolve actual class/source SHA/JDK and freeze observer source. Every100k '
                       'matches existing baseline full paidSHA, initials, ledger, FEfronts/genes/birthFE, '
                       'search and nontime decoder counts. Callback rows1..100k contiguous; program '
                       'paidFE sum equals allintra successFE. Original comparison called once, no RNG '
                       'or objective change. Numeric sweep fixtures against independentHV. Partial '
                       'programs cleaned in finally. Any failure stops interpretation and retains prefix.',
        'limits': 'One oldseed,100kprefix, M/C local only as reached; not all four local roles, causality, '
                  'fatigue-specificity or complete algorithm value. Identity/nonidentity programs '
                  'have different states/operators/costs; do not compare rawmeans as treatment effect. '
                  'Failed sampler/empty/critic/teacher experiments remain stopped; no new Q table, '
                  'selector, online graph or mainline change. All attempts paid, QA separate. No transfers.'}


def actual_fees(root):
    values = [rows(p)[0] for p in root.glob('*/*/run-receipt.jsonl')]
    return {'successfulFE': sum(v['successful'] for v in values), 'attemptedFE': sum(v['attempted'] for v in values),
            'failedFE': sum(v['failed'] for v in values), 'runsWithReceipts': len(values),
            'checkpointFullDecoderQA': sum(read(p)['uniqueOfflineDecodes'] for p in root.glob('*/*/checkpoint-validation.json'))}


def main():
    root = ROOT / 'runs' / datetime.now().strftime('local-program-audit-%Y%m%d-%H%M%S-%f')
    root.mkdir();print('LOCAL_PROGRAM_AUDIT_ROOT', root, flush=True);results = []
    try:
        with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
            specs = read(BASELINE / 'protocol.json')['instances'];write_once(root / 'protocol.json', protocol(specs))
            for spec in specs:shutil.copytree(BASELINE / spec['stem'] / 'inputs', root / spec['stem'] / 'inputs')
            write_once(root / 'input-hashes.json', {str(p.relative_to(root)): digest(p)
                       for spec in specs for p in (root / spec['stem'] / 'inputs').glob('*') if p.is_file()})
            write_once(root / 'numeric-HV-acceptance.json', checks(hypervolume));cp = build(root)
            for spec in specs:
                for method, template in (('FULL', 'STRICT_FULL'), ('NSGA', 'NSGA_STRICT')):
                    stem = spec['stem'];out = root / stem / method;out.mkdir(parents=True)
                    cmd = command(root, cp, stem, method, template, 'record', SEED, limit=LIMIT, audit=True)
                    cmd[cmd.index('research.dynamic.NaturalLocalRun')] = 'research.dynamic.LocalProgramRun'
                    write_once(out / 'command.json', cmd);print('LOCAL_PROGRAM_RUN', stem, method, flush=True)
                    execute(cmd, out / 'run.log', timeout=300);verify(out, float('inf'), LIMIT, 'record')
                    off_equivalence(BASELINE / stem / f'{method}-OFF', out)
                    results.append(analyze(out, spec, method, LIMIT))
            eligible = all(r['summary']['eligibleForPairedProgramProbe'] for r in results)
            write_once(root / 'analysis.json', {'cells': results, 'worthPairedProgramProbe': eligible,
                'causalInterpretationEstablished': False, 'newAlgorithmImplemented': False, 'goalAchieved': False})
    except BaseException as error:
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), **actual_fees(root)});raise
    fees = actual_fees(root);assert fees['successfulFE'] == fees['attemptedFE'] == 400000 and fees['failedFE'] == 0
    write_once(root / 'status.json', {'status': 'COMPLETE', **fees,
        'allObserverRunsEquivalent': True, 'worthPairedProgramProbe': eligible, 'goalAchieved': False})
    print('LOCAL_PROGRAM_AUDIT_COMPLETE', 'worthPairedProgramProbe', eligible, fees, flush=True)


if __name__ == '__main__':main()
