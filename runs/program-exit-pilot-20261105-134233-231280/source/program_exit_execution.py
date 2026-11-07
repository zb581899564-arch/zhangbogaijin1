"""Targeted numeric/trajectory acceptance, then strict FE or real deadline runs."""
import numpy as np

from run_long_budget_bridge import read, rows, write_once, execute, hypervolume
from natural_local_support import command, verify
from run_snapshot_anchor_audit import override
from center_task_checks import off_equivalence
from run_program_acceptance_audit import pddr
from program_exit_design import AUDIT, BASELINE, ARMS, SEEDS, FE_LIMIT


def run(root, cp, spec, label, method, enabled, seed, limit=FE_LIMIT, seconds=float('inf'), audit=False):
    out = root / spec['stem'] / label;out.mkdir(parents=True)
    cmd = command(root, cp, spec['stem'], label, 'STRICT_FULL' if method == 'FULL' else 'NSGA_STRICT',
                  'record', seed, limit=limit, seconds=seconds, audit=audit)
    cmd[cmd.index('research.dynamic.NaturalLocalRun')] = 'research.dynamic.ProgramExitRun'
    for key, value in (('research.programExit.enabled', str(enabled).lower()), ('research.programExit.audit', str(audit).lower()),
                       ('research.programExit.scale', ','.join(map(str, spec['normalization']['scale']))),
                       ('research.programExit.lower', ','.join(map(str, spec['normalization']['lower'])))):
        cmd = override(cmd, key, value)
    write_once(out / 'command.json', cmd);print('PROGRAM_EXIT_RUN', spec['stem'], label, 'FEcap', limit, 'T', seconds, flush=True)
    execute(cmd, out / 'run.log', timeout=300)
    receipt = verify(out, seconds, limit, 'record', require_time=seconds != float('inf'))
    evidence, = rows(out / 'program-exit-policy.jsonl')
    assert evidence['enabled'] == enabled and evidence['audit'] == audit and evidence['innerPddrUnchanged']
    assert evidence['objectiveEvaluationsInMetric'] == 0 and evidence['scale'] == spec['normalization']['scale']
    if not enabled: assert evidence['centerOuterDecisions'] == evidence['referenceBuilds'] == 0
    if audit and enabled: verify_decisions(out, spec['normalization'], evidence)
    return out, receipt


def verify_decisions(out, norm, evidence):
    references = {r['reference']: np.asarray(r['points']) for r in rows(out / 'program-exit-references.jsonl')}
    records = rows(out / 'program-exit-comparisons.jsonl');cache = {};worst = 0.
    for record in records:
        raw = references[record['reference']];scores = []
        for name in ('candidate', 'incumbent'):
            point = np.asarray(record[name]);key = record['reference'], tuple(point)
            if key not in cache:
                values = (np.vstack([raw, point]) - norm['lower']) / norm['scale']
                cache[key] = float(hypervolume(values, (1.5,) * 3))
            scores.append(cache[key]);error = abs(scores[-1] - record[name + 'ReferenceHV']);worst = max(worst, error)
            assert error < 1e-11
        assert (scores[0] > scores[1] + 1e-10) == record['accepted'], 'Independent exit decision differs'
        c, i = pddr(np.asarray(record['candidate']), np.asarray(record['incumbent']), raw)
        assert (c < i) == record['originalPddrWouldAccept']
    assert len(records) == evidence['centerOuterDecisions']
    write_once(out / 'exit-decision-acceptance.json', {'status': 'PASS', 'decisions': len(records),
        'referenceCount': len(references), 'maxIndependentHVError': worst, 'extraSearchFE': 0, 'extraDecoderCalls': 0})


def numeric_fixtures(root, cp, specs):
    lines = []
    for spec in specs.values():
        for method in ('FULL', 'NSGA'):
            old = BASELINE / spec['stem'] / method
            refs = {r['id']: np.asarray([p['objectives'] for p in r['points']]) for r in rows(old / 'program-references.jsonl')}
            records = read(AUDIT / spec['stem'] / method / 'analysis.json')['programs']
            for record in records[::257]:
                for name in ('entry', 'improved'):
                    values = (np.vstack([refs[record['reference']], record[name]]) - spec['normalization']['lower']) / spec['normalization']['scale']
                    for ref in (1.25, 1.5, 2.):
                        lines.append((ref, values))
    for values in ([[0, 0, 0]], [[.2, .4, .6], [.2, .4, .6]], [[.1, .9, .9], [.9, .1, .9], [.9, .9, .1]],
                   [[2, 0, 0], [1.5, .1, .1]], [[0, 1.5, .2], [1.5, 0, .2], [.5, .5, .5]]):
        for ref in (1.25, 1.5, 2.):lines.append((ref, np.asarray(values)))
    path = root / 'numeric-hv-fixtures.tsv'
    path.write_text('\n'.join('\t'.join([str(ref), repr(float(hypervolume(values, (ref,) * 3))),
        ';'.join(','.join(map(str, point)) for point in values)]) for ref, values in lines) + '\n', encoding='utf-8')
    execute(['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'org.uma.jmetal.util.research.search.ProgramExitMetricChecks', str(path)],
        root / 'numeric-hv-fixtures.log')


def engineering(root, cp, specs):
    numeric_fixtures(root, cp, specs)
    for spec in specs.values():
        for method in ('FULL', 'NSGA'):
            out, _ = run(root, cp, spec, f'engineering-{method}-OFF', method, False, 12390003, audit=True)
            off_equivalence(BASELINE / spec['stem'] / method, out)
            out, _ = run(root, cp, spec, f'engineering-{method}-ON', method, True, 12390003, audit=True)
            assert rows(out / 'program-exit-policy.jsonl')[0]['centerOuterDecisions'] > 0
        for cutoff in (1, 2, 5100, 10000):
            run(root, cp, spec, f'engineering-ON-{cutoff}', 'FULL', True, 12390003, limit=cutoff, audit=True)
    write_once(root / 'engineering-acceptance.json', {'status': 'PASS', 'successfulFE': 830206,
        'failedFE': 0, 'fullOffPaidTrajectoryEqualities': 4, 'independentOnDecisionAudits': 4,
        'cutoffs': [1, 2, 5100, 10000], 'innerDescentAndInterAcceptanceUnchanged': True})


def pairing(root, specs, budget):
    for stem in specs:
        for seed in SEEDS:
            folders = {arm: root / stem / f'{budget}-{seed}-{arm}' for arm in ARMS}
            initials = [rows(p / 'initial-population.jsonl') for p in folders.values()]
            assert all(len(v) == 100 and v == initials[0] for v in initials)
            for method in ('FULL', 'NSGA'):
                checkpoints = []
                for flag in ('OFF', 'ON'):
                    points = rows(folders[f'{method}_{flag}'] / 'anytime.jsonl')
                    checkpoints.append({p['checkpoint']: p['front'] for p in points if p['checkpointKind'] == 'FE' and p['reached']})
                if 5100 in checkpoints[0].keys() & checkpoints[1].keys(): assert checkpoints[0][5100] == checkpoints[1][5100]
            if budget == 'TIME':
                for arm, folder in folders.items():
                    fixed = root / stem / f'FE-{seed}-{arm}'
                    def reached(path): return {p['checkpoint']: p['front'] for p in rows(path / 'anytime.jsonl') if p['checkpointKind'] == 'FE' and p['reached']}
                    first, second = reached(fixed), reached(folder)
                    for fe in first.keys() & second.keys(): assert first[fe] == second[fe]
    write_once(root / f'pairing-{budget}.json', {'status': 'PASS', 'sameInitial100': True,
        'preLocalGlobal5100UnchangedWithinMethod': True, 'commonReachedFEAcrossBudgetsEqual': budget == 'TIME'})
