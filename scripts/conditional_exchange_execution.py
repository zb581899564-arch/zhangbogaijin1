"""Fair actual-FE/true-deadline calls and boundary acceptance for the new conditional sampler."""
from run_long_budget_bridge import ROOT, read, rows, write_once, execute
from natural_local_support import command, verify
from run_snapshot_anchor_audit import override
from center_task_checks import off_equivalence
from conditional_exchange_design import BASELINE, FE_LIMIT, TIME_FE_CAP


def run(root, cp, spec, label, method, enabled, seed, limit=FE_LIMIT, seconds=float('inf'), audit=False):
    stem = spec['stem']; out = root / stem / label;out.mkdir(parents=True)
    cmd = command(root, cp, stem, label, 'STRICT_FULL' if method == 'FULL' else 'NSGA_STRICT',
                  'record', seed, limit=limit, seconds=seconds, audit=audit)
    cmd[cmd.index('research.dynamic.NaturalLocalRun')] = 'research.dynamic.ConditionalExchangeRun'
    cmd = override(cmd, 'research.conditionalExchange.enabled', str(enabled).lower())
    write_once(out / 'command.json', cmd)
    print('CONDITIONAL_EXCHANGE_RUN', stem, label, 'T', seconds, 'FEcap', limit, flush=True)
    execute(cmd, out / 'run.log', timeout=300)
    receipt = verify(out, seconds, limit, 'record', require_time=seconds != float('inf'))
    evidence, = rows(out / 'conditional-exchange.json')
    assert evidence['enabled'] == enabled and evidence['preGeneratedCandidateRejections'] == evidence['historyLookups'] == 0
    if enabled:
        assert evidence['requests'] == evidence['appliedNonidentity'] + evidence['emptySupportOriginalPaidFallback']
        expected = sum(receipt['search'].get(f'intra.neighborhood{i}.proposals', 0) for i in (5, 8))
        assert evidence['requests'] == expected
    else: assert evidence['requests'] == evidence['appliedNonidentity'] == evidence['emptySupportOriginalPaidFallback'] == 0
    write_once(out / 'sampler-acceptance.json', {'status': 'PASS', **evidence,
        'countersIncludeOriginalUnpaidProposalTail': True, 'guardedActualFE': receipt['successful']})
    return out, receipt


def engineering(root, cp, specs):
    execute(['java', '-Xms32m', '-Xmx2g', '-cp', cp,
             'org.uma.jmetal.util.research.search.ConditionalExchangeChecks'], root / 'zero-decoder-fixtures.log')
    for spec in specs.values():
        for method in ('FULL', 'NSGA'):
            out, _ = run(root, cp, spec, f'engineering-{method}-OFF', method, False, 12390003, audit=True)
            off_equivalence(BASELINE / spec['stem'] / f'{method}-OFF', out)
        for cutoff in (1, 2, 5100, 10000):
            run(root, cp, spec, f'engineering-ON-{cutoff}', 'FULL', True, 12390003, limit=cutoff, audit=True)
    write_once(root / 'engineering-acceptance.json', {'status': 'PASS', 'successfulFE': 430206,
        'failedFE': 0, 'baselinePaidSequencesEquivalent': 4, 'ONcutoffs': [1, 2, 5100, 10000],
        'conditionalSupportExactlyEnumerated': True, 'emptySupportNotSkipped': True})


def paired_acceptance(root, specs, seeds, arms):
    for stem in specs:
        for seed in seeds:
            initials = []
            for arm in arms:
                folders = [root / stem / f'{budget}-{seed}-{arm}' for budget in ('FE', 'TIME')]
                for folder in folders:
                    data = rows(folder / 'initial-population.jsonl'); assert len(data) == 100; initials.append(data)
                fronts = [{r['checkpoint']: r['front'] for r in rows(folder / 'anytime.jsonl')
                           if r['checkpointKind'] == 'FE' and r['reached']} for folder in folders]
                for fe in fronts[0].keys() & fronts[1].keys(): assert fronts[0][fe] == fronts[1][fe]
            assert all(points == initials[0] for points in initials)
    write_once(root / 'paired-input-acceptance.json', {'status': 'PASS',
        'allInitial100VectorsAndObjectivesEqualPerInstanceSeed': True, 'commonFEFrontsEqualAcrossFEAndTIME': True})
