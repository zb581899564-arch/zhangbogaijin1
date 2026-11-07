"""Frozen source adaptation and one guarded heavy trace for the first-local ancestry fork."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute
from research.semantic_repair.evidence import digest
from frozen_classpath_identity import resolve_class, verify_capture
from paired_survival_bench import class_hashes
from run_snapshot_anchor_audit import override
from ctx_gom_build import once
from ctx_gom_replay import replay


def build(root, plan):
    source, classes = root/'source', root/'classes'; source.mkdir(); classes.mkdir()
    old = Path(plan['source'])/'overrides/CanonicalHmopso.java'
    text = old.read_text('utf-8-sig')
    anchor = '            Map<Direction, List<Particle>> groups = decompose(population);'
    text = once(text, anchor, anchor+'\n            Map<Direction,List<Particle>> forkLocalGroups = GomForkInputs.capture(groups);')
    anchor = '            if (GomRunScope.enabled()) GomRunScope.begin(reference, gomInstance);'
    text = once(text, anchor,
        '            Map<Direction,List<Particle>> localGroups = forkLocalGroups == null ? updated : forkLocalGroups;\n'
        '            GomForkInputs.selected(localGroups, updated);\n'
        '            if (GomRunScope.enabled()) GomRunScope.begin(solutions(flatten(localGroups)), gomInstance);')
    anchor = '''                for (Direction direction : Direction.values()) for (Particle particle : updated.get(direction)) {
                    state.observationGroup(direction);
                    Direction preference = preference(direction);'''
    text = once(text, anchor, anchor.replace('updated.get(direction)', 'localGroups.get(direction)'))
    (source/'CanonicalHmopso.java').write_text(text, encoding='utf-8')
    for path in (ROOT/'src/algorithms/diagnostics/ctx_fork').glob('*.java'):
        shutil.copy2(path, source)
    for name in ('ctx_fork_engineering_support.py', 'run_ctx_first_local_fork_engineering.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    base = (Path(plan['source'])/'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java', '-version'], root/'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes),
             *map(str, source.glob('*.java'))], root/'compile.log')
    cp = str(classes)+';'+base; (root/'classpath.txt').write_text(cp, encoding='utf-8')
    identities = {}
    for suffix in ('GomLocalProgram', 'GomWorkspace', 'GomDomainModels', 'GomRunScope', 'Particle', 'SurvivorSelection'):
        name = 'org.uma.jmetal.util.research.search.'+suffix
        identities[name] = resolve_class(cp, name)
        assert identities[name] == resolve_class(base, name)
    write_once(root/'inherited-identities.json', identities)
    write_once(root/'source-hashes.json', {p.name: digest(p) for p in source.iterdir()})
    write_once(root/'class-hashes.json', class_hashes(classes))
    write_once(root/'original-canonical-source.json', dict(path=str(old), sha256=digest(old)))
    return cp


def native_folder(plan, stem, arm):
    folder = Path(plan['sourceEngineering'])/stem/arm
    return Path(read(folder/'reuse.json')['source']) if (folder/'reuse.json').exists() else folder


def run_one(root, cp, plan, spec, arm, mode, label, limit):
    native = native_folder(plan, spec['stem'], arm)
    command = read(native/'command.json')
    at = command.index('research.dynamic.GomEngineeringRun')
    command[at] = 'research.dynamic.GomForkEngineeringRun'
    command[command.index('-cp')+1] = cp
    inputs = root/spec['stem']/'inputs'
    for offset, name in enumerate((spec['stem']+'.txt', 'RECONSTRUCTED-setup.txt', 'fatigue-input.txt'), 1):
        command[at+offset] = str(inputs/name)
    out = root/spec['stem']/label; out.mkdir()
    command[at+4] = str(out); command[at+6] = str(limit)
    assert int(command[at+7]) == plan['engineeringSeed']
    for key, value in {'research.ctxFork.localInput': mode,
                       'research.ctxGom.prefixFE': ','.join(map(str, sorted(set(spec['cutoffs']+[5100,spec['masterFE']]))))}.items():
        command = override(command, key, value)
    write_once(out/'command.json', command)
    print('CTX_FORK_ENGINEERING_RUN', spec['stem'], label, limit, flush=True)
    execute(command, out/'run.log', timeout=900)
    receipt, = rows(out/'receipt.jsonl')
    assert receipt['status'] == 'COMPLETE' and receipt['error'] is None
    assert receipt['successful'] == receipt['attempted'] == receipt['decoder']['dynamic.evaluations'] == limit
    assert receipt['failed'] == receipt['timeInterruptedAttempts'] == 0 and receipt['stopReason'] == 'FE_LIMIT'
    assert sum(receipt['search'].get(k+'.evaluations',0) for k in ('initialization','global','inter','intra','jointLocal')) == limit
    capture, = rows(out/'loaded-identity.jsonl'); verify_capture(capture, cp)
    helper = read(out/'fork-input.json'); verify_capture(helper['identity'], cp)
    independent = replay(out); write_once(out/'independent-replay.json', independent)
    assert independent['passed'] and read(out/'checkpoint-validation.json')['allReachedPointsCovered']
    print('CTX_FORK_TRACE_ACCEPTED', spec['stem'], label, independent['localProposalsValidated'], flush=True)
    return out, receipt, helper['fork']
