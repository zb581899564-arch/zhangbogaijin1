"""Isolated light-entry build and exact engineering/parity checks for the frozen QPA core."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute
from pa_capability_support import command, initial_key
from pa_specialist_bridge_build import INTERFACE, replace_once
from frozen_classpath_identity import verify_capture
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes

ENGINE = ROOT/'runs/qpa-complete-engineering-20261106-024925-292174'


def build(root):
    assert read(ENGINE/'status.json')['engineeringPass']
    assert class_hashes(ENGINE/'classes') == read(ENGINE/'class-hashes.json')
    for name, sha in read(ENGINE/'source-hashes.json').items():
        assert digest(ENGINE/'source'/name) == sha
    source, classes = root/'source', root/'classes'; source.mkdir(); classes.mkdir()
    shutil.copy2(ROOT/'src/algorithms/diagnostics/qpa_engineering/QpaCapabilityRun.java', source)
    population = (INTERFACE/'source/PaPopulation.java').read_text('utf-8-sig')
    old = ': a[parent.role.objective()] < b[parent.role.objective()];'
    new = ': (a[parent.role.objective()] < b[parent.role.objective()]\n'
    new += '                    || Boolean.getBoolean("research.pa.boundaryNonWorse") && a[parent.role.objective()] == b[parent.role.objective()]);'
    population = replace_once(population, old, new)
    (source/'PaPopulation.java').write_text(population, encoding='utf-8')
    for name in ('qpa_capability_support.py', 'qpa_capability_analysis.py', 'run_qpa_capability_pilot.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    base = (ENGINE/'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java', '-version'], root/'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes),
             *map(str, source.glob('*.java'))], root/'compile.log')
    cp = str(classes)+';'+base; (root/'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root/'source-hashes.json', {p.name: digest(p) for p in source.iterdir()})
    write_once(root/'class-hashes.json', class_hashes(classes))
    write_once(root/'pa-equality-adaptation.json', {'source': str(INTERFACE/'source/PaPopulation.java'),
        'sourceSHA256': digest(INTERFACE/'source/PaPopulation.java'), 'onlyChange': 'Boundary accepts equality when explicit property true',
        'unchanged': 'CENTER, all genes/model/FOS/reencoding/donor lifecycle/RNG/budget/default source files'})
    return cp


def run_case(root, cp, stem, arm, label, limit, seed, seconds=float('inf'), audit=False):
    out = root/stem/label; out.mkdir(parents=True)
    template_arm = 'PA_JOINT' if arm in ('QPA_DIRECT', 'PA_EQUAL') else arm
    cmd = command(root, cp, stem, template_arm, label, limit, seed, seconds, audit)
    entry = cmd.index('research.dynamic.PaCapabilityRun'); cmd[entry] = 'research.dynamic.QpaCapabilityRun'; cmd[entry+5] = arm
    write_once(out/'command.json', cmd); print('QPA_CAPABILITY_RUN', stem, label, limit, seconds, flush=True)
    execute(cmd, out/'run.log', timeout=600)
    receipt, = rows(out/'run-receipt.jsonl')
    assert receipt['error'] is None and receipt['constructorsIncludedInClock']
    assert receipt['attempted'] == receipt['successful'] + receipt['failed']
    assert receipt['failed'] == receipt['timeInterruptedAttempts'] <= 1
    if seconds == float('inf'):
        assert receipt['stopReason'] == 'FE_LIMIT' and receipt['successful'] == limit and receipt['failed'] == 0
    else:
        assert receipt['stopReason'] == 'TIME_LIMIT' and receipt['searchSeconds'] >= seconds and receipt['successful'] < limit
    assert sum(receipt['search'].get(s+'.evaluations', 0) for s in ('initialization', 'global', 'inter', 'intra')) == receipt['successful']
    assert read(out/'checkpoint-validation.json')['status'] == 'passed'
    for value in rows(out/'checkpoint-solutions.jsonl'):
        assert value['bornFE'] <= value['checkpointFE'] and value['bornSeconds'] <= value['checkpointElapsedSeconds']
        if value['checkpointKind'] == 'TIME':
            assert value['bornSeconds'] <= value['checkpoint']
    capture, = rows(out/'loaded-identity.jsonl'); write_once(out/'identity-verified.json', verify_capture(capture, cp))
    return out, receipt


def front(folder, endpoint):
    point, = [p for p in rows(folder/'anytime.jsonl') if p['checkpointKind'] == 'FE' and p['checkpoint'] == endpoint and p['reached']]
    return {tuple(row) for row in point['front']}


def engineering(root, cp, plan):
    from pa_capability_support import run_case as old_case
    base = (INTERFACE/'classpath.txt').read_text('utf-8-sig').strip(); results = []
    for spec in plan['instances']:
        stem = spec['stem']; native, = rows(ENGINE/stem/'main/receipt.jsonl'); limit = native['successfulFE']
        light, qpa = run_case(root, cp, stem, 'QPA_DIRECT', 'ENGINE-LIGHT', limit, 14670003, audit=True)
        assert qpa['paidSHA256'] == native['paidSHA256'] and qpa['search']['completeGenerations'] == 2
        assert front(light, limit) == {tuple(p['objectives']) for p in native['lastValidFront']}
        old_limit = 7900 if stem.startswith('20_') else 39900
        frozen, old = old_case(root, base, stem, 'PA_JOINT', 'ENGINE-FROZEN-PA', old_limit, 14670003, audit=True)
        capture, = rows(frozen/'loaded-identity.jsonl'); write_once(frozen/'identity-verified.json', verify_capture(capture, base))
        strict, off = run_case(root, cp, stem, 'PA_JOINT', 'ENGINE-STRICT', old_limit, 14670003, audit=True)
        equal, on = run_case(root, cp, stem, 'PA_EQUAL', 'ENGINE-EQUAL', old_limit, 14670003, audit=True)
        assert old['paidSHA256'] == off['paidSHA256'] and front(strict, old_limit) == front(frozen, old_limit)
        assert initial_key(light) == initial_key(frozen) == initial_key(strict) == initial_key(equal)
        assert off['search']['completeGenerations'] == on['search']['completeGenerations'] == 2
        assert on['boundaryNonWorse'] and not off['boundaryNonWorse']
        results.append(dict(stem=stem, qpaFullPaidDigestAndFrontEqual=True, strictPAPaidDigestAndFrontEqual=True,
                            all100InitialsEqual=True, equalityControlEngineeringOnly=True))
    write_once(root/'engineering.json', {'passed': True, 'instances': results, 'actualSuccessfulFE': 236600})
