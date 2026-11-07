"""Exactly repeat all1056legal four-corner encodings with beta0, no target resampling or new optimizer."""
from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes
from run_paired_qgs_guidance import replace
from schedule_beta0_analysis import analyze

DYNAMIC = ROOT / 'runs/schedule-factor-probe-20261105-124946-994085'
STEMS = ('20_8_5_1', '100_2_3_1')


def build(root):
    source, classes = root / 'source', root / 'classes';source.mkdir();classes.mkdir()
    text = (DYNAMIC / 'source/ScheduleFactorProbe.java').read_text('utf-8').replace('ScheduleFactorProbe', 'ScheduleFactorBeta0Probe')
    text = replace(text, 'DynamicParameters params = DynamicInputs.fatigue(in, Paths.get(args[2]));',
        'DynamicParameters originalParameters = DynamicInputs.fatigue(in, Paths.get(args[2]));\n'
        '        DynamicParameters params = FactorBeta0Parameters.make(in, originalParameters);\n'
        '        NeutralProbeSupport.append(out.resolve("parameter-contract.jsonl"), FactorBeta0Parameters.contract(in, originalParameters, params));')
    (source / 'ScheduleFactorBeta0Probe.java').write_text(text, encoding='utf-8')
    shutil.copy2(DYNAMIC / 'source/NeutralProbeSupport.java', source)
    shutil.copy2(ROOT / 'src/algorithms/diagnostics/schedule_factors/FactorBeta0Parameters.java', source)
    for name in ('run_schedule_factor_beta0.py', 'schedule_beta0_analysis.py'):shutil.copy2(Path(__file__).with_name(name), source)
    base = (DYNAMIC / 'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java', '-version'], root / 'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes), *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{base}';(root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'source-hashes.json', {p.name: digest(p) for p in source.glob('*')});write_once(root / 'class-hashes.json', class_hashes(classes))
    execute(['java', '-cp', cp, 'research.dynamic.ClassResolutionProbe', 'research.dynamic.ScheduleFactorBeta0Probe',
        'research.dynamic.FactorBeta0Parameters', 'org.uma.jmetal.util.research.DynamicEvaluation',
        'org.uma.jmetal.util.research.model.DynamicDecoder', 'org.uma.jmetal.util.research.model.DynamicValidator'], root / 'loaded-identity.json')
    return cp


def parameters(infile, contract):
    expected = {}
    for line in infile.read_text('utf-8').splitlines():
        if not line.strip() or line.startswith('#') or line.startswith('SOURCE'):continue
        parts = line.replace(',', ' ').split()
        if len(parts) != 7:continue
        try: f, k, w = map(int, parts[:3]);values = list(map(float, parts[3:]))
        except ValueError:continue
        expected[f, k, w] = values
    actual = {(r['factory'], r['stage'], r['worker']): r for r in contract['workers']}
    assert actual.keys() == expected.keys() and contract['onlyBetaChanged']
    for key, r in actual.items():
        alpha, mu, beta, h0 = expected[key]
        assert [r['alpha'], r['mu'], r['originalBeta'], r['h0']] == [alpha, mu, beta, h0]
        assert r['counterfactualBeta'] == 0


def run_locked():
    assert read(DYNAMIC / 'status.json')['status'] == 'COMPLETE'
    root = ROOT / 'runs' / datetime.now().strftime('schedule-factor-beta0-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('SCHEDULE_FACTOR_BETA0_ROOT', root, flush=True);results = []
    try:
        write_once(root / 'protocol.json', {'dynamicSource': str(DYNAMIC), 'instances': STEMS,
            'question': 'Is observed order/bundle dependence retained with beta0 at exactly the same264pairs?',
            'budget': '1056newguarded beta0evaluations+1056independentfulltimelineQA. Prior1056dynamic '
                      'evaluations reused, not charged as new. No source search, new target, extra pair or new policy.',
            'invariant': 'Only beta zeroed, allalpha/mu/h0 retained and independently checked against input; '
                         'sameFIFO/FAM dynamics and sourcelegal fourvectors. Commonrepair0. Model parameter '
                         'context explicit; no cache crossing models. Exactsame264matchedpairs+120missing.',
            'scoring': 'Recompute BOTHmodels with eachpairPARENT singleton background and same original '
                       'normalization/HVref1.5. Parent-relative gain differs from previousFULLarchive score '
                       'and never replaces it. Record lostbeta0dominance and zerojointgain, no replacement. '
                       'Jointdependence bothsinglefactorgains<0.1targetgain only when targetgain>1e-10. '
                       'Amplification=beta0bestsinglefactorrecovery-dynamicrecovery for comparable positivepairs.',
            'limits': 'Targets selected by dynamic optimizer. Paired beta intervention describes these '
                      'fixed schedules, not whole landscape, beta0algorithm performance, independent '
                      'fatigue-specific innovation or useful offspring. No success gate or algorithm '
                      'promotion. Preserve all mismatches, failures, missingpairs; defaultline unchanged.'})
        expected = read(DYNAMIC / 'planned-fees.json');specs = {s['stem']: s for s in read(DYNAMIC / 'protocol.json')['instances']}
        for stem in STEMS:
            folder = root / stem;folder.mkdir();shutil.copytree(DYNAMIC / stem / 'inputs', folder / 'inputs')
            shutil.copy2(DYNAMIC / stem / 'selected-pairs.json', folder)
            lines = []
            for raw in (DYNAMIC / stem / 'cases.tsv').read_text('utf-8').splitlines():
                parts = raw.split('\t');parts[2] = '-';lines.append('\t'.join(parts))
            (folder / 'cases.tsv').write_text('\n'.join(lines) + '\n', encoding='utf-8')
            assert len(lines) == expected[stem]
        write_once(root / 'planned-fees.json', expected);write_once(root / 'input-hashes.json',
            {str(p.relative_to(root)): digest(p) for stem in STEMS for p in (root / stem).rglob('*') if p.is_file()})
        cp = build(root)
        for stem in STEMS:
            folder = root / stem;inp = folder / 'inputs'
            cmd = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'research.dynamic.ScheduleFactorBeta0Probe',
                str(inp / f'{stem}.txt'), str(inp / 'RECONSTRUCTED-setup.txt'), str(inp / 'fatigue-input.txt'),
                str(folder / 'cases.tsv'), str(folder / 'probe')]
            write_once(folder / 'command.json', cmd);execute(cmd, folder / 'run.log', timeout=300)
            contract, = rows(folder / 'probe/parameter-contract.jsonl');parameters(inp / 'fatigue-input.txt', contract)
            receipt, = rows(folder / 'probe/receipt.jsonl')
            assert receipt['successfulFE'] == receipt['attemptedFE'] == receipt['fullDecoderQA'] == expected[stem] and receipt['failedFE'] == 0
            results.append(analyze(root, DYNAMIC, specs[stem]))
        write_once(root / 'analysis.json', {'instances': results, 'fatigueSpecificAlgorithmEstablished': False, 'goalAchieved': False})
    except BaseException as error:
        receipts = [rows(p)[0] for p in root.glob('*/probe/receipt.jsonl')]
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error),
            'successfulFE': sum(r['successfulFE'] for r in receipts), 'failedFE': sum(r['failedFE'] for r in receipts)});raise
    write_once(root / 'status.json', {'status': 'COMPLETE', 'successfulFE': 1056, 'attemptedFE': 1056,
        'failedFE': 0, 'fullDecoderQA': 1056, 'onlyBetaChanged': True, 'goalAchieved': False})
    print('SCHEDULE_FACTOR_BETA0_COMPLETE', flush=True)


def main():
    with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):run_locked()


if __name__ == '__main__':main()
