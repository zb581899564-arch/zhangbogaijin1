"""Frozen trace equivalence plus a bounded causal donor rollback; no mainline or selector changes."""
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, rows, read, write_once, execute, controller_lock
from run_qpa_complete_engineering import protected
from pa_capability_support import command, initial_key
from run_snapshot_anchor_audit import override
from frozen_classpath_identity import verify_capture
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest
from pa_neutral_replay import reconstruct, select, write_pairs
from pa_neutral_pair_analysis import analyze

PRIOR = ROOT/'runs/qpa-capability-pilot-20261106-025546-344483'


def protocol():
    return {'version': 'PA_NEUTRAL_DONOR_CAUSAL_DIAGNOSTIC-v1', 'registered': '2026-11-06', 'frozenProgramSource': str(PRIOR),
        'instances': read(PRIOR/'protocol.json')['instances'], 'traceSeed': 14670003, 'traceFE': {'20_8_5_1': 7900, '100_2_3_1': 39900},
        'traceRuns': 'Strict and equal perinstance, allpaidfullQA and independent transitions; digest/finalfront/initial100 mustmatch prior ENGINE-STRICT/EQUAL',
        'traceActualFE': 95600, 'maximumPairFE': 96, 'maximumActualSearchFE': 95696,
        'motivation': 'Current complete-program equal control improved both instances; zeroFEstrict traces contain physically changed exact-own-target ties. This does not reopen failed COST_LEX/FACTORY_LEX or promote the former control',
        'hypothesis': 'An accepted physically changed scalar-neutral specialist state can provide useful incremental material through an actual same-generation CENTER donor read',
        'scope': 'One-step causal mechanism under frozen PA, not explanation of all500k differences, not original shared mainline, no full performance, selector or published novelty claim',
        'eligibility': 'All CENTER reads of a current-generation specialist state whose latest accepted raw change was exact-own-scalar tie and physical change. Exact raw duplicates may preserve provenance. Clear provenance at reencoding; no cross-generation coordinate counterfactual. Same receiver/mask, rollback donor to its immediately preceding paid working state. Require physical child difference only, never filter on receiver acceptance/objective/archive gain',
        'sampling': {'seed': 14750019, 'perGeneration': 12, 'generations': [1, 2], 'rule': 'Private seeded uniform without replacement from all eligible chronological reads; maximum24perinstance, all eligibility records retained; no replacement by quality'},
        'minimum': 'At least8selectedpairs in BOTHinstances before any pair evaluations; otherwise stop as insufficient without extra seeds/horizon',
        'pairBilling': 'Both actual and rollback evaluated anew once viaRunContext; actual matches source objective bits; both fullQA; missingfactory uses same unchanged receiver fallback and remains paid; no search feedback or extra repair',
        'indicators': 'Perrequest prior allpaid archive A0; compareND(A0+actual) vsND(A0+rollback). HV1.5/1.25/2 on prior norm; IGD+referenceNDunionofboth resultingfronts; exactweakdeduplicatedbidirectionalC includingequal. Rawobjectiveandcoveragecounts retained',
        'clueGate': 'BOTHinstances: >=8pairs; >=3pairs HVdifference>1e-10%ofpriorHV with IGD+nonworse/Cdelta>=-1e-10; >=1pair HVdifference>=0.1%ofpriorHV; positiveHVcount>=negativecount+2; sumHVdifference>1e-10; medianIGD+worsening<=1e-10; medianCdelta>=-1e-10; sumHVdirectionnonnegative atrefs1.25/2. Tolerance numericalonly',
        'interpretation': 'Passing permits a separate complete neutral-relay mechanism protocol only. Failing stops this latest-neutral direct-relay hypothesis, no neutral tolerance/mask/role/seed rescanning. All old stops stay unchanged',
        'defaultMainlineChanged': False, 'goalAchieved': False}


def build(root):
    assert read(PRIOR/'post-audit.json')['passed']
    assert class_hashes(PRIOR/'classes') == read(PRIOR/'class-hashes.json')
    source, classes = root/'source', root/'classes'; source.mkdir(); classes.mkdir()
    for path in (ROOT/'src/algorithms/diagnostics/pa_neutral').glob('*.java'):
        shutil.copy2(path, source)
    for name in ('run_pa_neutral_relay_probe.py', 'pa_neutral_replay.py', 'pa_neutral_pair_analysis.py', 'pa_population_replay.py',
                 'pa_population_state_checks.py', 'pa_population_model_checks.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    base = (PRIOR/'classpath.txt').read_text('utf-8-sig').strip()
    execute(['java', '-version'], root/'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes), *map(str, source.glob('*.java'))], root/'compile.log')
    cp = str(classes)+';'+base; (root/'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root/'source-hashes.json', {p.name: digest(p) for p in source.iterdir()})
    write_once(root/'class-hashes.json', class_hashes(classes)); return cp


def fees(root):
    result = dict(successfulFE=0, attemptedFE=0, failedFE=0, paidFullTimelineQA=0, neutralFullTimelineQA=0, runs=0)
    for path in root.glob('*/*/receipt.jsonl'):
        receipt, = rows(path); result['runs'] += 1
        for key in result:
            if key != 'runs':
                result[key] += receipt.get(key, 0)
    return result


def trace(root, cp, spec, arm, plan):
    stem = spec['stem']; out = root/stem/arm; out.mkdir(); limit = plan['traceFE'][stem]
    label = 'PA_EQUAL' if arm == 'EQUAL' else 'PA_JOINT'
    cmd = command(root, cp, stem, 'PA_JOINT', arm, limit, plan['traceSeed'], audit=True)
    cmd = override(cmd, 'research.pa.traceIdentity', 'true')
    entry = cmd.index('research.dynamic.PaCapabilityRun'); cmd[entry] = 'research.dynamic.PaNeutralTraceRun'; cmd[entry+5] = label
    write_once(out/'command.json', cmd); print('PA_NEUTRAL_TRACE', stem, arm, limit, flush=True); execute(cmd, out/'run.log', timeout=600)
    capture, = rows(out/'loaded-identity.jsonl'); write_once(out/'identity-verified.json', verify_capture(capture, cp))
    check, catalog, receipt = reconstruct(out)
    previous = PRIOR/stem/('ENGINE-'+arm); old, = rows(previous/'run-receipt.jsonl')
    assert receipt['paidSHA256'] == old['paidSHA256']
    point, = [p for p in rows(previous/'anytime.jsonl') if p['checkpointKind'] == 'FE' and p['checkpoint'] == limit and p['reached']]
    assert {tuple(v) for v in point['front']} == {tuple(v['objectives']) for v in receipt['lastValidFront']}
    assert check.initial == initial_key(previous)
    write_once(out/'independent-replay.json', {'passed': True, 'paidSHA256': receipt['paidSHA256'], 'frozenDigestFrontAndInitialsEqual': True,
               'bridgeCounts': dict(check.bridges), 'eligibleReads': len(check.cases), 'newQAFromPython': 0})
    return check, catalog


def probe(root, cp, stem, cases, catalog):
    inp, out = root/stem/'inputs', root/stem/'PAIRS'; out.mkdir()
    write_once(root/stem/'selected-cases.json', cases); write_pairs(root/stem/'pairs.tsv', cases, catalog['tuples'])
    cmd = ['java', '-Xms32m', '-Xmx2g', '-Dresearch.snapshot.mode=ANCHOR', '-cp', cp, 'research.dynamic.PaNeutralPairRun',
           str(inp/(stem+'.txt')), str(inp/'RECONSTRUCTED-setup.txt'), str(inp/'fatigue-input.txt'), str(root/stem/'pairs.tsv'), str(out), '14750023']
    write_once(out/'command.json', cmd); print('PA_NEUTRAL_PAIRS', stem, len(cases), flush=True); execute(cmd, out/'run.log', timeout=180)
    receipt, = rows(out/'receipt.jsonl'); assert receipt['status'] == 'COMPLETE' and receipt['failedFE'] == 0
    assert receipt['successfulFE'] == receipt['attemptedFE'] == receipt['paidFullTimelineQA'] == receipt['decoder']['dynamic.evaluations'] == 2*len(cases)
    capture, = rows(out/'loaded-identity.jsonl'); write_once(out/'identity-verified.json', verify_capture(capture, cp))


def main():
    with controller_lock(ROOT/'research/night_research', 'dispatch.lock'):
        root = ROOT/'runs'/datetime.now().strftime('pa-neutral-relay-probe-%Y%m%d-%H%M%S-%f'); root.mkdir()
        plan = protocol(); before = protected(); write_once(root/'protocol.json', plan); write_once(root/'protected-before.json', before)
        print('PA_NEUTRAL_RELAY_ROOT', root, flush=True)
        try:
            cp = build(root); selected = {}; catalogs = {}; traces = []
            for spec in plan['instances']:
                stem = spec['stem']; shutil.copytree(PRIOR/stem/'inputs', root/stem/'inputs')
                write_once(root/stem/'input-hashes.json', {p.name: digest(p) for p in (root/stem/'inputs').iterdir() if p.is_file()})
                trace(root, cp, spec, 'STRICT', plan); eq, catalog = trace(root, cp, spec, 'EQUAL', plan)
                selected[stem], eligibility = select(eq, plan['sampling']['seed'], plan['sampling']['perGeneration'])
                write_once(root/stem/'all-eligible-reads.json', eligibility)
                write_once(root/stem/'selection.json', {'selectedPaidFE': [c['paidFE'] for c in selected[stem]],
                    'eligibleCount': len(eligibility), 'bridgeCounts': dict(eq.bridges), 'receiverOutcomeUsedForSelection': False})
                catalogs[stem] = catalog; traces.append({'stem': stem, 'eligible': len(eligibility), 'selected': len(selected[stem])})
            assert fees(root)['successfulFE'] == plan['traceActualFE']
            results = []
            if all(len(v) >= 8 for v in selected.values()):
                for spec in plan['instances']:
                    stem = spec['stem']; probe(root, cp, stem, selected[stem], catalogs[stem])
                    results.append({'stem': stem, **analyze(root/stem, selected[stem], spec['normalization'])})
            passed = len(results) == 2 and all(r['mechanismCluePass'] for r in results)
            decision = 'SEPARATE_COMPLETE_NEUTRAL_RELAY_PROTOCOL_PERMITTED' if passed else 'STOP_LATEST_NEUTRAL_RELAY_HYPOTHESIS'
            actual = fees(root)
            assert actual['attemptedFE'] == actual['successfulFE'] <= plan['maximumActualSearchFE'] and actual['failedFE'] == 0
            assert actual['neutralFullTimelineQA'] == 800 and actual['paidFullTimelineQA'] == actual['successfulFE']
            assert protected() == before and class_hashes(root/'classes') == read(root/'class-hashes.json')
            for name, sha in read(root/'source-hashes.json').items():
                assert digest(root/'source'/name) == sha
            write_once(root/'analysis.json', {'traces': traces, 'instances': results, 'decision': decision, **actual,
                'fullAlgorithmPerformanceProved': False, 'oldStopsUnchanged': True, 'defaultMainlineChanged': False, 'goalAchieved': False})
        except BaseException as error:
            write_once(root/'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), **fees(root), 'goalAchieved': False}); raise
        write_once(root/'status.json', {'status': 'COMPLETE', 'decision': decision, **actual, 'goalAchieved': False})
        print('PA_NEUTRAL_RELAY_COMPLETE', decision, actual, flush=True)


if __name__ == '__main__':
    main()
