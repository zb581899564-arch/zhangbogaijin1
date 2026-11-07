"""Execute the prospective52043FE joint-population lifecycle engineering contract, no performance gate."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes
from pa_population_replay import analyze

SOURCE = ROOT / 'runs/linkage-mixing-probe-20261105-142116-487815'
BASE = ROOT / 'runs/schedule-factor-probe-20261105-124946-994085'
MODEL = ROOT / 'runs/pa-model-audit-20261105-160326-565953'
PROTOCOL = ROOT / 'research/gomea_reference_audit/PA_MO_ENGINEERING_V1.json'
ORDER = [('20_8_5_1', 'cut1', 1), ('20_8_5_1', 'cut2', 2), ('20_8_5_1', 'cut101', 101),
         ('20_8_5_1', 'cut139', 139), ('20_8_5_1', 'main', 7900), ('20_8_5_1', 'cut4000', 4000),
         ('100_2_3_1', 'main', 39900)]


def build(root):
    source, classes = root / 'source', root / 'classes'; source.mkdir(); classes.mkdir()
    for folder in ('src/algorithms/model_global/encoding', 'src/algorithms/model_global/linkage',
                   'src/algorithms/model_global/population', 'src/algorithms/diagnostics/pa_population'):
        for path in (ROOT / folder).glob('*.java'):
            shutil.copy2(path, source)
    for path in (BASE / 'source/NeutralProbeSupport.java', ROOT / 'src/java/dynamicentries/ProbeData.java',
                 ROOT / 'src/algorithms/diagnostics/PddrPaidDigest.java'):
        shutil.copy2(path, source)
    for name in ('run_pa_population_engineering.py', 'pa_population_replay.py', 'pa_population_state_checks.py',
                 'pa_population_model_checks.py', 'pa_model_audit_analysis.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    base = (BASE / 'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java', '-version'], root / 'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes), *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{base}'; (root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'source-hashes.json', {p.name: digest(p) for p in source.iterdir()})
    write_once(root / 'class-hashes.json', class_hashes(classes)); return cp


def fees(root):
    receipts = [r for p in root.glob('*/*/audit/receipt.jsonl') for r in rows(p)]
    return {k: sum(r[k] for r in receipts) for k in ('successfulFE','attemptedFE','failedFE','paidFullTimelineQA',
        'reencodingFullTimelineQA','fullDecoderQA','accepted','fallbacks','completeRawDuplicates',
        'currentGenerationDonorReads','changedCurrentGenerationDonorReads')}


def run_one(root, cp, plan, stem, name, limit):
    folder = root / stem / name; folder.mkdir(parents=True); inputs = SOURCE / stem / 'inputs'
    source = SOURCE / stem / str(plan['engineeringRuns']['sourceSeed']) / 'sources.tsv'
    files = [inputs / f'{stem}.txt', inputs / 'RECONSTRUCTED-setup.txt', inputs / 'fatigue-input.txt', source]
    write_once(folder / 'input-hashes.json', {str(p): digest(p) for p in files})
    command = ['java', '-Xms32m', '-Xmx2g', '-Dresearch.snapshot.mode=ANCHOR', '-cp', cp, 'research.dynamic.PaPopulationRun',
               *map(str, files), str(folder / 'audit'), str(plan['engineeringRuns']['algorithmSeed']), str(limit)]
    write_once(folder / 'command.json', command); print('PA_POPULATION_RUN', stem, name, limit, flush=True)
    execute(command, folder / 'run.log', timeout=300)
    result = analyze(folder / 'audit'); assert result['successfulFE'] == limit
    if name == 'main':
        assert result['generations'] == 2 and result['programs'] == 200 and len(result['modelChecks']) == 2
        assert result['changedCurrentGenerationDonorReads'] > 0
    result.update(stem=stem, name=name); return result


def main():
    with controller_lock(ROOT / 'research/night_research', 'dispatch.lock'):
        assert read(MODEL / 'status.json')['status'] == 'COMPLETE'
        plan = read(PROTOCOL); assert sum(r[2] for r in ORDER) == plan['engineeringRuns']['expectedTotalSuccessfulFE'] == 52043
        root = ROOT / 'runs' / datetime.now().strftime('pa-population-engineering-%Y%m%d-%H%M%S-%f'); root.mkdir()
        print('PA_POPULATION_ENGINEERING_ROOT', root, flush=True); results = []
        write_once(root / 'protocol.json', {'prospectiveContract':plan, 'contractSHA256':digest(PROTOCOL), 'order':ORDER,
            'purpose':'Complete lifecycle engineering only, no performance or novelty comparison',
            'observerCost':'Every paid timeline QA and evidence I/O enabled, no same-time conclusion',
            'externalTransfers':False,'defaultMainlineChanged':False,'goalAchieved':False})
        try:
            cp = build(root)
            for stem, name, limit in ORDER: results.append(run_one(root, cp, plan, stem, name, limit))
            main20, = [r for r in results if r['stem'] == '20_8_5_1' and r['name'] == 'main']
            for result in results:
                if result['name'].startswith('cut'):
                    assert result['paidSHA256'] == main20['prefixPaidSHA256'][str(result['successfulFE'])]
            actual = fees(root)
            assert actual['successfulFE'] == actual['attemptedFE'] == actual['paidFullTimelineQA'] == 52043 and actual['failedFE'] == 0
            assert actual['reencodingFullTimelineQA'] == 700 and actual['fullDecoderQA'] == 52743
            write_once(root / 'analysis.json', {'runs':results, **actual,'engineeringPass':True,'allCutoffsMatchMainPaidPrefix':True,
                'newCompleteOrdinaryAdaptedLifecycleImplemented':True,'sameBudgetPerformanceProved':False,'goalAchieved':False})
        except BaseException as error:
            write_once(root / 'status.json', {'status':'INCOMPLETE_RETAINED','error':repr(error),**fees(root)}); raise
        write_once(root / 'status.json', {'status':'COMPLETE',**actual,'engineeringPass':True,'goalAchieved':False})
        print('PA_POPULATION_ENGINEERING_COMPLETE',actual,flush=True)


if __name__ == '__main__':
    main()
