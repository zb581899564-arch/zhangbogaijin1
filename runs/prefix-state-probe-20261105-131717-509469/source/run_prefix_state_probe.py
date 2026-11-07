"""Reuse frozen source pools; isolated, fully charged state-preserving block diagnostics."""
from datetime import datetime
from pathlib import Path
import shutil
import time

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock, hypervolume
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest
from run_paired_qgs_guidance import replace
from run_schedule_factor_beta0 import parameters
from fa_admission_volume import checks
from prefix_state_design import SOURCE, BASE, STEMS, protocol, prepare
from prefix_state_analysis import analyze


def build(root):
    source, classes = root / 'source', root / 'classes';source.mkdir();classes.mkdir()
    text = (BASE / 'source/ScheduleFactorProbe.java').read_text('utf-8').replace('ScheduleFactorProbe', 'PrefixStateProbe')
    text = replace(text, 'DynamicParameters params = DynamicInputs.fatigue(in, Paths.get(args[2]));',
        'DynamicParameters originalParameters = DynamicInputs.fatigue(in, Paths.get(args[2]));\n'
        '        DynamicParameters params = Boolean.parseBoolean(args[5]) ? FactorBeta0Parameters.make(in, originalParameters) : originalParameters;\n'
        '        if (Boolean.parseBoolean(args[5])) NeutralProbeSupport.append(out.resolve("parameter-contract.jsonl"),\n'
        '            FactorBeta0Parameters.contract(in, originalParameters, params));')
    text = replace(text, '        NeutralProbeSupport.append(output.resolve("outcomes.jsonl"),',
        '        PrefixStateChecks.observe(fields, full, output);\n        NeutralProbeSupport.append(output.resolve("outcomes.jsonl"),')
    text = text.replace('PAID_SCHEDULE_FACTOR_COUNTERFACTUAL', 'PAID_PREFIX_STATE_COUNTERFACTUAL')
    (source / 'PrefixStateProbe.java').write_text(text, encoding='utf-8')
    for path in (BASE / 'source/NeutralProbeSupport.java',
                 ROOT / 'src/algorithms/diagnostics/schedule_factors/FactorBeta0Parameters.java',
                 ROOT / 'src/algorithms/diagnostics/prefix_state/PrefixStateChecks.java'):
        shutil.copy2(path, source)
    for name in ('run_prefix_state_probe.py', 'prefix_state_design.py', 'prefix_state_analysis.py', 'run_schedule_factor_beta0.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    base = (BASE / 'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java', '-version'], root / 'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes), *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{base}';(root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'class-hashes.json', class_hashes(classes))
    write_once(root / 'source-hashes.json', {p.name: digest(p) for p in source.glob('*')})
    execute(['java', '-cp', cp, 'research.dynamic.ClassResolutionProbe', 'research.dynamic.PrefixStateProbe',
        'research.dynamic.PrefixStateChecks', 'research.dynamic.FactorBeta0Parameters',
        'org.uma.jmetal.util.research.DynamicEvaluation', 'org.uma.jmetal.util.research.model.DynamicDecoder',
        'org.uma.jmetal.util.research.model.DynamicValidator'], root / 'loaded-identity.json')
    return cp


def evaluate(root, cp, stem, model, expected):
    folder = root / stem;out = folder / model;out.mkdir();inp = folder / 'inputs';cases = folder / 'cases.tsv'
    if model == 'BETA0':
        lines = []
        for line in cases.read_text('utf-8').splitlines():
            fields = line.split('\t');fields[2] = '-';lines.append('\t'.join(fields))
        cases = out / 'cases.tsv';cases.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    command = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'research.dynamic.PrefixStateProbe',
        str(inp / f'{stem}.txt'), str(inp / 'RECONSTRUCTED-setup.txt'), str(inp / 'fatigue-input.txt'),
        str(cases), str(out / 'probe'), str(model == 'BETA0').lower()]
    write_once(out / 'command.json', command);started = time.monotonic()
    execute(command, out / 'run.log', timeout=300)
    write_once(out / 'wall-time.json', {'wholeProbeIncludingFullQASeconds': time.monotonic() - started,
        'notSearchOnlyTime': True, 'noSameTimeClaim': True})
    receipt, = rows(out / 'probe/receipt.jsonl')
    assert receipt['successfulFE'] == receipt['attemptedFE'] == receipt['fullDecoderQA'] == expected and receipt['failedFE'] == 0
    if model == 'BETA0':
        contract, = rows(out / 'probe/parameter-contract.jsonl');parameters(inp / 'fatigue-input.txt', contract)
    print('PREFIX_STATE_PAID', stem, model, expected, flush=True)


def run_locked():
    assert read(SOURCE / 'status.json')['status'] == read(BASE / 'status.json')['status'] == 'COMPLETE'
    root = ROOT / 'runs' / datetime.now().strftime('prefix-state-probe-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('PREFIX_STATE_ROOT', root, flush=True);results = []
    try:
        plan = protocol();write_once(root / 'protocol.json', plan)
        write_once(root / 'numeric-hv-checks.json', checks(hypervolume));started = time.monotonic()
        expected = {stem: prepare(root, stem) for stem in STEMS}
        write_once(root / 'construction-time.json', {'seconds': time.monotonic() - started, 'searchFE': 0})
        assert 2 * sum(expected.values()) == plan['plannedFE']
        write_once(root / 'planned-fees.json', {'perInstancePerModel': expected, 'totalFE': plan['plannedFE']})
        paths = [p for stem in STEMS for p in (root / stem).rglob('*') if p.is_file()]
        write_once(root / 'input-hashes.json', {str(p.relative_to(root)): digest(p) for p in paths})
        cp = build(root);specs = {s['stem']: s for s in plan['instances']}
        for stem in STEMS:
            for model in ('DYNAMIC', 'BETA0'): evaluate(root, cp, stem, model, expected[stem])
            results.append(analyze(root, specs[stem]))
        prefix_pass = all(r['worthIndependentPrefixContinuation'] for r in results)
        role_pass = all(r['roleComparison']['pass'] for r in results)
        write_once(root / 'analysis.json', {'instances': results, 'worthIndependentPrefixContinuation': prefix_pass,
            'fourRoleSupplyNecessaryCondition': role_pass, 'newAlgorithmImplemented': False, 'goalAchieved': False})
    except BaseException as error:
        receipts = [rows(p)[0] for p in root.glob('*/*/probe/receipt.jsonl')]
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error),
            'successfulFE': sum(r['successfulFE'] for r in receipts), 'failedFE': sum(r['failedFE'] for r in receipts),
            'fullDecoderQA': sum(r['fullDecoderQA'] for r in receipts)});raise
    write_once(root / 'status.json', {'status': 'COMPLETE', 'successfulFE': plan['plannedFE'],
        'attemptedFE': plan['plannedFE'], 'failedFE': 0, 'fullDecoderQA': plan['plannedFE'],
        'worthIndependentPrefixContinuation': prefix_pass, 'fourRoleSupplyNecessaryCondition': role_pass, 'goalAchieved': False})
    print('PREFIX_STATE_COMPLETE', prefix_pass, role_pass, flush=True)


def main():
    with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'): run_locked()


if __name__ == '__main__': main()
