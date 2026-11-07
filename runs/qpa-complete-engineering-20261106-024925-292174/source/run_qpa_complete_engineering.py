"""Frozen complete ordinary direct-joint lifecycle acceptance, at most190010searchFE."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from pa_specialist_bridge_build import INTERFACE
from pa_capability_support import run_case, initial_key
from frozen_classpath_identity import verify_capture
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes
from qpa_engineering_replay import replay

PROTOCOL = ROOT/'research/gomea_reference_audit/QPA_FIXED100_ENGINEERING_V1.json'
INPUTS = ROOT/'runs/pa-role-acceptance-probe-20261106-011839-887122'
PROTECTED = ('src/java/search/CanonicalHmopso.java', 'src/algorithms/model_global/population/PaPopulation.java',
             'src/algorithms/model_global/population/PaPaidEvaluation.java')


def protected():
    return {name: digest(ROOT/name) for name in PROTECTED}


def build(root):
    source, classes = root/'source', root/'classes'; source.mkdir(); classes.mkdir()
    for folder in ('src/algorithms/model_global/direct', 'src/algorithms/model_global/qpa',
                   'src/algorithms/diagnostics/qpa_engineering'):
        for path in (ROOT/folder).glob('*.java'):
            shutil.copy2(path, source/path.name)
    for name in ('run_qpa_complete_engineering.py', 'qpa_engineering_replay.py', 'qpa_state_checks.py',
                 'qgomea_reference_math.py', 'pa_population_state_checks.py', 'frozen_classpath_identity.py'):
        shutil.copy2(Path(__file__).with_name(name), source/name)
    base = (INTERFACE/'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java', '-version'], root/'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes),
             *map(str, source.glob('*.java'))], root/'compile.log')
    cp = str(classes) + os.pathsep + base
    (root/'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root/'source-hashes.json', {p.name: digest(p) for p in source.iterdir()})
    write_once(root/'class-hashes.json', class_hashes(classes))
    write_once(root/'dependencies.json', [{'position': i, 'path': raw, 'jarSHA256': digest(Path(raw)) if Path(raw).is_file() else None}
               for i, raw in enumerate(cp.split(os.pathsep))])
    return cp, base


def fees(root):
    result = dict(successfulFE=0, attemptedFE=0, failedFE=0, paidFullTimelineQA=0, oldPAOfflineQA=0, receiptCount=0)
    for path in root.glob('*/*/receipt.jsonl'):
        record, = rows(path); result['receiptCount'] += 1
        for key in ('successfulFE', 'attemptedFE', 'failedFE', 'paidFullTimelineQA'):
            result[key] += record[key]
    for path in root.glob('*/PARITY-OLD-PA/run-receipt.jsonl'):
        record, = rows(path); result['receiptCount'] += 1
        for target, key in (('successfulFE', 'successful'), ('attemptedFE', 'attempted'), ('failedFE', 'failed')):
            result[target] += record[key]
        check = path.parent/'checkpoint-validation.json'
        if check.exists():
            result['oldPAOfflineQA'] += read(check)['uniqueOfflineDecodes']
    return result


def run_one(root, cp, stem, name, seed, limit, generations):
    out = root/stem/name; out.mkdir(parents=True); inputs = root/stem/'inputs'
    command = ['java', '-Xms32m', '-Xmx2g', '-Dresearch.snapshot.mode=ANCHOR', '-Dresearch.pa.traceIdentity=true',
               '-cp', cp, 'research.dynamic.QpaPopulationRun', str(inputs/(stem+'.txt')),
               str(inputs/'RECONSTRUCTED-setup.txt'), str(inputs/'fatigue-input.txt'), str(out), str(seed), str(limit), str(generations)]
    write_once(out/'command.json', command); print('QPA_ENGINEERING_RUN', stem, name, limit, flush=True)
    execute(command, out/'run.log', timeout=600)
    capture, = rows(out/'loaded-identity.jsonl'); checked = verify_capture(capture, cp)
    write_once(out/'identity-verified.json', checked)
    result = replay(out); write_once(out/'independent-replay.json', result)
    if generations > 0:
        assert result['completeGenerations'] == 2 and result['completePrograms'] == 200 and len(result['modelChecks']) == 2
    else:
        assert result['paidReconstructed'] == limit
    print('QPA_INDEPENDENT_REPLAY_PASSED', stem, name, result['paidReconstructed'], flush=True)
    return out, result


def engineering(root, cp, base, plan):
    results = []
    for stem in plan['engineering']['instances']:
        shutil.copytree(INPUTS/stem/'inputs', root/stem/'inputs')
        write_once(root/stem/'input-hashes.json', {p.name: digest(p) for p in (root/stem/'inputs').iterdir() if p.is_file()})
        seed = plan['engineering']['seed']; bound = plan['engineering']['maximumMainFE'][stem]
        main_out, main_result = run_one(root, cp, stem, 'main', seed, bound, 2)
        actual = main_result['paidReconstructed']; assert actual <= bound
        cuts = [1, 2, 100, 101, 102, actual - 1]; initial_out = None
        for cutoff in cuts:
            out, result = run_one(root, cp, stem, 'cut'+str(cutoff), seed, cutoff, -1)
            assert result['paidSHA256'] == main_result['prefixSHA256'][str(cutoff)]
            if cutoff == 100:
                initial_out = out
        old_out, old = run_case(root, base, stem, 'PA_JOINT', 'PARITY-OLD-PA', 100, seed, audit=True)
        capture, = rows(old_out/'loaded-identity.jsonl')
        write_once(old_out/'identity-verified.json', verify_capture(capture, base))
        assert initial_key(old_out) == initial_key(initial_out) == initial_key(main_out)
        assert old['paidSHA256'] == main_result['prefixSHA256']['100']
        result = dict(stem=stem, main=main_result, cutoffs=cuts, initial100EqualToOldPA=True,
                      cutoffPaidDigestsMatchMainPrefixes=True)
        results.append(result); write_once(root/stem/'acceptance.json', result)
    return results


def main():
    with controller_lock(ROOT/'research/night_research', 'dispatch.lock'):
        root = ROOT/'runs'/datetime.now().strftime('qpa-complete-engineering-%Y%m%d-%H%M%S-%f'); root.mkdir()
        print('QPA_COMPLETE_ENGINEERING_ROOT', root, flush=True)
        plan = read(PROTOCOL); before = protected()
        write_once(root/'protocol.json', {'prospectiveContract': plan, 'contractSHA256': digest(PROTOCOL),
            'observerCost': 'Every paid full QA and evidence included; engineering timings are not performance',
            'protectedBefore': before, 'externalTransfers': False, 'goalAchieved': False})
        try:
            cp, base = build(root); results = engineering(root, cp, base, plan); actual = fees(root)
            assert actual['successfulFE'] == actual['attemptedFE'] <= plan['engineering']['maximumActualSearchFE']
            assert actual['failedFE'] == 0 and actual['receiptCount'] == 16
            assert actual['paidFullTimelineQA'] == actual['successfulFE'] - 200
            assert protected() == before
            write_once(root/'analysis.json', {'engineeringPass': True, 'instances': results, **actual,
                'protectedAfter': protected(), 'defaultMainlineChanged': False, 'sameBudgetPerformanceProved': False,
                'goalAchieved': False})
        except BaseException as error:
            write_once(root/'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), **fees(root), 'goalAchieved': False})
            raise
        write_once(root/'status.json', {'status': 'COMPLETE', 'engineeringPass': True, **actual, 'goalAchieved': False})
        print('QPA_COMPLETE_ENGINEERING_PASSED', root, actual, flush=True)


if __name__ == '__main__':
    main()
