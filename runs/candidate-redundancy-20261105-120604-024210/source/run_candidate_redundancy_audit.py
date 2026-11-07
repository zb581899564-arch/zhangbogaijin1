"""400k charged read-only replays against existing complete100k natural baselines, locally only."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

from datetime import datetime
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from natural_local_support import command, verify
from candidate_redundancy_build import ENTRY, build
from candidate_redundancy_analysis import acceptance, cell, finish
from research.semantic_repair.evidence import digest

BASELINE = ROOT / 'runs/factory-cache-potential-20261105-082934-494793'
SEED, LIMIT = 12390003, 100000


def protocol(specs):
    return {'baseline': str(BASELINE), 'entry': str(ENTRY), 'instances': specs, 'seed': SEED,
        'FELimitPerRun': LIMIT, 'plannedNewSuccessfulFE': 400000, 'historicalBaselineFEReusedNotNew': 400000,
        'question': 'How many complete physical candidates repeat, and how many intra candidates come '
                    'from an operator whose entire current support is provably the parent?',
        'identity': 'Canonical ordered(job,firstStageMA,WA) within each real factory, with factory separators; '
                    'fixed physical model/input context. Full integer equality after hash, full100k '
                    'history without eviction. Every duplicate objectives and all operation fields '
                    'timeline SHA must equal earliest paid representative. No approximate objective-based identity.',
        'observations': 'Original Intra.propose still copies/repairs/generates; immutable parent key and '
                        'exact empty-support certificate saved after proposal. All original guarded '
                        'evaluations, RNG, VNS, acceptance, PDDR/Q/families/sharing execute unchanged. '
                        'Count all stages, physical roles, operators and factory occupancies. NSGA '
                        'ordinary global without SearchState hook labeledCLASSIC. Every997thpaid sample, no RNG.',
        'certificate': 'JS permutation empty if fewerthan2jobs; machine/worker exchange empty if '
                       'current local vector homogeneous. Original load/capacity reallocation '
                       'empty if noeligible move or deterministic source==target. Certificate '
                       'must imply actual full canonical parent identity for every paid proposal.',
        'engineering': 'Resolve actual frozen classes/sources/JDK and hashes. Zero-decoder known key '
                       '/neutral interleave/resource change/empty-support fixtures. Each observer '
                       '100k must equal its original baseline full paidSHA, initial population, '
                       'every commonFE front/genome/bornFE, physical local ledger, search counts '
                       'and non-time decoder counts. Failed engineering stops interpretation. '
                       'Every paid observation contiguous, history accounting and stage fees independent.',
        'gate': 'Everyone of4instance/methodcells certified-empty neighborhood paidFE>=5%ofall100kFE. '
                'This only permits a separate common-core operator precheck protocol for both methods. '
                'History duplicates alone do not justify filtering/caching, or withoutreplacement '
                'sampling. Do not change caps/seed/window/operator after outcomes.',
        'scope': '100kprefix of originalnatural VNS only; not whole500k, allroles completed, actual '
                 'savedcost, fullalgorithm same-time performance or paper novelty. Observer and '
                 'digest costs belong to this audit; no shadow lookup affects decoder or search. '
                 'All duplicate/cache-hit evaluations remain charged. No production/default changes, '
                 'downloads, transfers, remote jobs or public push.'}


def run(root, cp, spec, label, template):
    stem = spec['stem']; out = root / stem / label; out.mkdir(parents=True)
    cmd = command(root, cp, stem, label, template, 'record', SEED, limit=LIMIT, audit=True)
    cmd[cmd.index('research.dynamic.NaturalLocalRun')] = 'research.dynamic.CandidateRedundancyRun'
    write_once(out / 'command.json', cmd); print('CANDIDATE_REDUNDANCY_RUN', stem, label, flush=True)
    execute(cmd, out / 'run.log', timeout=300)
    verify(out, float('inf'), LIMIT, 'record')
    return out


def totals(root):
    receipts = [rows(p)[0] for p in root.glob('*/*/run-receipt.jsonl')]
    return {'successfulFE': sum(r['successful'] for r in receipts), 'attemptedFE': sum(r['attempted'] for r in receipts),
            'failedFE': sum(r['failed'] for r in receipts), 'runsWithReceipts': len(receipts),
            'checkpointFullDecoderQA': sum(read(p)['uniqueOfflineDecodes'] for p in root.glob('*/*/checkpoint-validation.json'))}


def main():
    assert read(BASELINE / 'status.json')['status'] == 'COMPLETE'
    root = ROOT / 'runs' / datetime.now().strftime('candidate-redundancy-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('CANDIDATE_REDUNDANCY_ROOT', root, flush=True); cells = []
    try:
        with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
            specs = read(BASELINE / 'protocol.json')['instances']; write_once(root / 'protocol.json', protocol(specs))
            for spec in specs: shutil.copytree(BASELINE / spec['stem'] / 'inputs', root / spec['stem'] / 'inputs')
            write_once(root / 'input-hashes.json', {str(p.relative_to(root)): digest(p)
                       for spec in specs for p in (root / spec['stem'] / 'inputs').glob('*') if p.is_file()})
            cp = build(root); inputs = root / '20_8_5_1/inputs'
            execute(['java', '-Xms32m', '-Xmx2g', '-cp', cp,
                'org.uma.jmetal.util.research.search.CandidateRedundancyChecks', str(inputs),
                str(inputs / 'RECONSTRUCTED-setup.txt')], root / 'zero-decoder-fixtures.log')
            for spec in specs:
                for label, template in (('FULL', 'STRICT_FULL'), ('NSGA', 'NSGA_STRICT')):
                    out = run(root, cp, spec, label, template)
                    evidence = acceptance(BASELINE / spec['stem'] / f'{label}-OFF', out, LIMIT)
                    summary = cell(spec['stem'], label, evidence); cells.append(summary)
                    print('CANDIDATE_REDUNDANCY_ACCEPTED', summary['stem'], label, 'duplicate',
                          summary['wholeHistoryDuplicateFraction'], 'empty', summary['certifiedEmptyFractionOfAllFE'], flush=True)
            result = finish(root, cells)
    except BaseException as error:
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), **totals(root)}); raise
    fees = totals(root); assert fees['successfulFE'] == fees['attemptedFE'] == 400000 and fees['failedFE'] == 0
    write_once(root / 'status.json', {'status': 'COMPLETE', **fees, 'allObserversEquivalent': True,
        'worthEmptyNeighborhoodEngineering': result['worthEmptyNeighborhoodEngineering'],
        'newSearchKernelImplemented': False, 'goalAchieved': False})
    print('CANDIDATE_REDUNDANCY_COMPLETE', result['decision'], fees, flush=True)


if __name__ == '__main__': main()
