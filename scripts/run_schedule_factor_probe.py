"""Fully charged legal order/bundle counterfactuals from actual common-model classic dominators."""
from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from candidate_redundancy_build import ENTRY
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest
from schedule_factor_design import SOURCE, STEMS, protocol, prepare
from schedule_factor_analysis import analyze


def build(root):
    source, classes = root / 'source', root / 'classes';source.mkdir();classes.mkdir()
    for p in (ROOT / 'src/algorithms/diagnostics/schedule_factors').glob('*.java'):shutil.copy2(p, source)
    shutil.copy2(ROOT / 'src/algorithms/diagnostics/NeutralProbeSupport.java', source)
    for name in ('schedule_factor_design.py', 'schedule_factor_analysis.py', 'run_schedule_factor_probe.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    base = (ENTRY / 'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java', '-version'], root / 'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes), *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{base}';(root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'class-hashes.json', class_hashes(classes));write_once(root / 'source-hashes.json', {p.name: digest(p) for p in source.glob('*')})
    execute(['java', '-cp', cp, 'research.dynamic.ClassResolutionProbe', 'org.uma.jmetal.util.research.DynamicEvaluation',
        'org.uma.jmetal.util.research.model.DynamicDecoder', 'org.uma.jmetal.util.research.model.DynamicValidator',
        'research.dynamic.ScheduleFactorProbe'], root / 'loaded-identity.json')
    return cp


def run_locked():
    assert read(SOURCE / 'status.json')['status'] == 'COMPLETE'
    root = ROOT / 'runs' / datetime.now().strftime('schedule-factor-probe-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('SCHEDULE_FACTOR_PROBE_ROOT', root, flush=True);results = []
    try:
        plan = protocol();write_once(root / 'protocol.json', plan)
        expected = {stem: prepare(root, stem) for stem in STEMS};write_once(root / 'planned-fees.json', expected)
        assert 0 < sum(expected.values()) <= 1536
        write_once(root / 'input-hashes.json', {str(p.relative_to(root)): digest(p)
            for stem in STEMS for p in (root / stem).rglob('*') if p.is_file()})
        cp = build(root);specs = {s['stem']: s for s in plan['instances']}
        for stem in STEMS:
            folder = root / stem;inp = folder / 'inputs'
            cmd = ['java', '-Xms32m', '-Xmx2g', '-cp', cp, 'research.dynamic.ScheduleFactorProbe',
                str(inp / f'{stem}.txt'), str(inp / 'RECONSTRUCTED-setup.txt'), str(inp / 'fatigue-input.txt'),
                str(folder / 'cases.tsv'), str(folder / 'probe')]
            write_once(folder / 'command.json', cmd);execute(cmd, folder / 'run.log', timeout=300)
            receipt, = rows(folder / 'probe/receipt.jsonl')
            assert receipt['successfulFE'] == receipt['attemptedFE'] == receipt['fullDecoderQA'] == expected[stem] and receipt['failedFE'] == 0
            results.append(analyze(root, specs[stem]))
        write_once(root / 'analysis.json', {'instances': results, 'newAlgorithmImplemented': False,
            'learnedPolicyOrTeacherImplemented': False, 'goalAchieved': False})
    except BaseException as error:
        actual = [rows(p)[0] for p in root.glob('*/probe/receipt.jsonl')]
        write_once(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error),
            'successfulFE': sum(r['successfulFE'] for r in actual), 'failedFE': sum(r['failedFE'] for r in actual)});raise
    write_once(root / 'status.json', {'status': 'COMPLETE', 'successfulFE': sum(expected.values()),
        'attemptedFE': sum(expected.values()), 'failedFE': 0, 'fullDecoderQA': sum(expected.values()), 'goalAchieved': False})
    print('SCHEDULE_FACTOR_PROBE_COMPLETE', expected, flush=True)


def main():
    with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
        run_locked()


if __name__ == '__main__':main()
