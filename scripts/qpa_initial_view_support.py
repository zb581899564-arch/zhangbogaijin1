"""Isolated two-hook build, fixed commands, initial physics and paid-suffix bridge."""
from pathlib import Path
import shutil
import struct

from run_long_budget_bridge import ROOT, read, rows, write_once, execute
from run_snapshot_anchor_audit import override
from paired_survival_bench import class_hashes
from frozen_classpath_identity import resolve_class, verify_capture
from research.semantic_repair.evidence import digest
from ctx_gom_capability_support import checked
from qpa_geometry_audit_inputs import JavaRandom, physical


def build(root, plan):
    geometry = read(Path(plan['sourceGeometry'])/'protocol.json')['contract']
    frozen = Path(geometry['sourceEngineering'])/'source/QpaPaidEvaluation.java'
    sources = [frozen, ROOT/'src/algorithms/model_global/population/PaPaidEvaluation.java']
    directory, classes = root/'source', root/'classes'
    directory.mkdir(); classes.mkdir()
    changes = []
    for path in sources:
        text = path.read_text('utf-8')
        initial = 'initializer.prepare(point, index);'
        assert text.count(initial) == 1
        text = text.replace(initial, initial+' NeutralInitialView.apply(instance, point, index);')
        budget = 'run' if path.name.startswith('Qpa') else 'context'
        paid = f'checks.paid(point, {budget}.budget().successful());'
        assert text.count(paid) == 1
        text = text.replace(paid, paid+f' NeutralInitialView.paid(point, {budget}.budget().successful());')
        (directory/path.name).write_text(text, encoding='utf-8')
        changes.append(dict(source=str(path), sha256=digest(path), hooks=['initialTransform', 'readOnlyPaidDigest']))
    for path in (ROOT/'src/algorithms/diagnostics/qpa_initial_view').glob('*.java'):
        shutil.copy2(path, directory)
    for name in ('qpa_initial_view_support.py', 'qpa_initial_view_analysis.py', 'run_qpa_initial_neutral_causal.py'):
        shutil.copy2(Path(__file__).with_name(name), directory)
    base = (Path(plan['sourceQpa'])/'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java', '-version'], root/'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes),
             *map(str, directory.glob('*.java'))], root/'compile.log')
    cp = str(classes)+';'+base
    (root/'classpath.txt').write_text(cp, encoding='utf-8')
    inherited = {}
    for suffix in ('QpaPopulation', 'PaPopulation', 'QpaLinkageModel', 'PaDependencyModel', 'DirectJointMove', 'PaMixingMove'):
        name = 'org.uma.jmetal.util.research.modelglobal.'+suffix
        actual, old = resolve_class(cp, name), resolve_class(base, name)
        assert actual == old
        inherited[name] = actual
    write_once(root/'build-changes.json', changes)
    write_once(root/'inherited-identities.json', inherited)
    write_once(root/'source-hashes.json', {p.name: digest(p) for p in directory.iterdir()})
    write_once(root/'class-hashes.json', class_hashes(classes))
    return cp


def source_folder(plan, stem, seed, arm):
    return Path(plan['sourcePilot'])/stem/str(seed)/('FE100K-'+('SYNC' if arm.startswith('Q_') else 'PA_JOINT'))


def run_one(root, cp, plan, stem, seed, arm):
    template = source_folder(plan, stem, seed, arm)
    command = read(template/'command.json')
    at = command.index('research.dynamic.QpaFeedbackCapabilityRun')
    command[at] = 'research.dynamic.QpaInitialViewRun'
    command[command.index('-cp')+1] = cp
    inputs = root/stem/'inputs'
    for offset, name in enumerate((stem+'.txt', 'RECONSTRUCTED-setup.txt', 'fatigue-input.txt'), 1):
        command[at+offset] = str(inputs/name)
    out = root/stem/str(seed)/('FE100K-'+arm)
    out.mkdir(parents=True)
    command[at+4] = str(out)
    mode = arm.split('_')[1]
    for key, value in {'research.initialView.mode': mode, 'research.initialView.seed': str(plan['privateInterleavingSeed'])}.items():
        command = override(command, key, value)
    write_once(out/'command.json', command)
    print('INITIAL_NEUTRAL_CAUSAL_RUN', stem, seed, arm, flush=True)
    execute(command, out/'run.log', timeout=900)
    receipt = checked(out, cp, plan['fixedFE'], float('inf'))
    assert receipt['attempted'] == receipt['successful'] == receipt['decoder']['dynamic.evaluations'] == plan['fixedFE']
    helper = read(out/'initial-view-identity.json')
    assert helper['error'] is None and helper['suffixPaidRows'] == plan['fixedFE']-100
    assert helper['intervention'] == dict(mode=mode, transforms=100, paid=plan['fixedFE'],
                                         privateSeed=plan['privateInterleavingSeed'], mainRNGCalls=0)
    write_once(out/'initial-view-identity-verified.json', verify_capture(helper['identity'], cp))
    check_initial(out, template, mode, plan['privateInterleavingSeed'])
    return out, receipt


def check_initial(out, source, mode, seed):
    current, original = rows(out/'initial-population.jsonl'), rows(source/'initial-population.jsonl')
    assert len(current) == len(original) == 100
    rng = JavaRandom(seed)
    for a, b in zip(current, original):
        factories = max(b['FA'])+1
        assert physical(a, factories) == physical(b, factories)
        assert struct.pack('>ddd', *a['objectives']) == struct.pack('>ddd', *b['objectives'])
        if mode == 'ORIGINAL':
            order = b['JS']
        elif mode == 'CONCAT':
            order = [job for chain in physical(b, factories) for job, _, _ in chain]
        else:
            labels = b['FA'].copy()
            for p in range(len(labels)-1, 0, -1):
                q = rng.integer(p+1)
                labels[p], labels[q] = labels[q], labels[p]
            chains = physical(b, factories)
            ranks = [0]*factories; order = []
            for f in labels:
                order.append(chains[f][ranks[f]][0]); ranks[f] += 1
        assert a['JS'] == order


def fe_fronts(folder):
    return {int(p['checkpoint']): sorted(map(tuple, p['front'])) for p in rows(folder/'anytime.jsonl')
            if p['checkpointKind'] == 'FE' and p['reached']}


def original_bridge(root, plan, stem, seed, arm):
    folder = root/stem/str(seed)/('FE100K-'+arm)
    native = source_folder(plan, stem, seed, arm)
    actual, = rows(folder/'run-receipt.jsonl'); old, = rows(native/'run-receipt.jsonl')
    assert actual['paidSHA256'] == old['paidSHA256'] and fe_fronts(folder) == fe_fronts(native)
    return dict(instance=stem, seed=seed, arm=arm, nativeWholePaidSHAAndFEFrontsEqual=True)


def pa_bridge(root, plan, stem, seed):
    folders = [root/stem/str(seed)/('FE100K-P_'+mode) for mode in ('ORIGINAL', 'CONCAT', 'RANDOM')]
    helpers = [read(folder/'initial-view-identity.json') for folder in folders]
    assert len({h['suffixPaidSHA256'] for h in helpers}) == 1
    assert fe_fronts(folders[0]) == fe_fronts(folders[1]) == fe_fronts(folders[2])
    return dict(instance=stem, seed=seed, paPaidSuffixFrom101AndAllFEFrontsEqual=True)
