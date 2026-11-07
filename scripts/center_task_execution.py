"""Sequential local JVM execution and prospective engineering acceptance."""
from time import perf_counter

from run_long_budget_bridge import read, write_once, execute
from run_snapshot_anchor_audit import override
from natural_local_support import command, verify
from center_task_build import ENTRY
from center_task_design import STEMS, LIMIT, CUTOFFS, ledger
from center_task_checks import verify_cutoff, verify_tasks, off_equivalence


def run(root, cp, spec, label, arm, seed, ledger_path, limit=LIMIT, original=False, scalar_audit=False):
    stem = spec['stem']; out = root / stem / label; out.mkdir(parents=True)
    cmd = command(root, cp, stem, label, 'NSGA_STRICT' if arm == 'NSGA' else 'STRICT_FULL',
                  'replay', seed, limit=limit, ledger=ledger_path, audit=True)
    mode = 'OFF' if arm == 'NSGA' else arm
    for key, value in (('research.centerTasks.mode', mode), ('research.centerTasks.seed', str(seed)),
                       ('research.centerTasks.scale', ','.join(map(str, spec['normalization']['scale']))),
                       ('research.centerTasks.audit', str(scalar_audit).lower())):
        cmd = override(cmd, key, value)
    if not original: cmd[cmd.index('research.dynamic.NaturalLocalRun')] = 'research.dynamic.CenterTaskRun'
    write_once(out / 'command.json', cmd)
    print('CENTER_TASK_RUN', stem, label, arm, limit, flush=True)
    start = perf_counter()
    try: execute(cmd, out / 'run.log', timeout=300)
    finally: write_once(out / 'process.json', {'wallSecondsIncludingStartupIOAndOfflineQA': perf_counter() - start})
    receipt = (verify(out, float('inf'), limit, 'replay', ledger_path) if limit == LIMIT
               else verify_cutoff(out, limit, ledger_path))
    if not original: verify_tasks(out, arm, limit, spec['normalization']['scale'], scalar_audit)
    return out, receipt


def engineering(root, cp, specs):
    base = (ENTRY / 'classpath.txt').read_text('utf-8-sig').strip()
    for stem in STEMS:
        path = root / stem / 'engineering-ledger.csv'; ledger(path, stem, 12390003)
        original, _ = run(root, base, specs[stem], 'engineering-original', 'OFF', 12390003, path, original=True)
        shadow, _ = run(root, cp, specs[stem], 'engineering-off', 'OFF', 12390003, path)
        off_equivalence(original, shadow)
    inputs = root / STEMS[0] / 'inputs'
    execute(['java', '-Xms32m', '-Xmx2g', '-Dresearch.centerTasks.mode=FIXED',
             '-Dresearch.centerTasks.scale=1,1,1', '-cp', cp,
             'org.uma.jmetal.util.research.search.CenterTaskChecks', str(inputs),
             str(inputs / 'RECONSTRUCTED-setup.txt')], root / 'zero-decoder-fixtures.log')
    for limit in CUTOFFS:
        run(root, cp, specs[STEMS[0]], f'engineering-cutoff-{limit}', 'FIXED', 12390003,
            root / STEMS[0] / 'engineering-ledger.csv', limit=limit, scalar_audit=True)
    write_once(root / 'engineering-acceptance.json', {'status': 'PASS',
        'successfulFE': 4 * LIMIT + sum(CUTOFFS), 'failedFE': 0,
        'originalOffEquivalentInstances': list(STEMS), 'scalarAndSlotZeroDecoderFixtures': True,
        'cutoffs': list(CUTOFFS), 'decisionEvidence': 'Independently recomputed for all FIXED cutoff runs'})
