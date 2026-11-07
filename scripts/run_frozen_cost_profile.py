"""Use the existing local JDK sampler without changing any search implementation."""
from datetime import datetime
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from paired_survival_bench import class_hashes
from frozen_cost_profile_analysis import analyze

SOURCE = ROOT/'runs/makespan-tie-screen-20261105-025223-471920'
STEMS = ('20_8_5_1', '100_2_3_1')
METHODS = ('STRICT_FULL', 'NSGA_STRICT')
SEED = 10950003


def identity_tool(root, original_cp):
    source, classes = root/'source', root/'identity-classes'
    source.mkdir(); classes.mkdir()
    shutil.copy2(ROOT/'src/algorithms/diagnostics/ClassResolutionProbe.java', source)
    for name in ('run_frozen_cost_profile.py', 'frozen_cost_profile_analysis.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', original_cp, '-d', str(classes),
             str(source/'ClassResolutionProbe.java')], root/'identity-compile.log')
    write_once(root/'identity-class-hashes.json', class_hashes(classes))
    return str(classes)+';'+original_cp


def verify_trace(out, original):
    receipt, = rows(out/'run-receipt.jsonl')
    old, = rows(original/'run-receipt.jsonl')
    assert receipt['successful'] == receipt['attempted'] == receipt['decoder']['dynamic.evaluations'] == 500000
    assert receipt['failed'] == 0 and receipt['stopReason'] == 'FE_LIMIT'
    assert receipt['search'] == old['search']
    for key in ('dynamic.reusedOperations','dynamic.recomputedOperations','dynamic.preparedChildren'):
        assert receipt['decoder'][key] == old['decoder'][key]
    for name in ('initial-population.jsonl','local-ledger.csv','solutions.jsonl'):
        assert (out/name).read_bytes() == (original/name).read_bytes(), name
    assert [r['front'] for r in rows(out/'anytime.jsonl')] == [r['front'] for r in rows(original/'anytime.jsonl')]
    assert read(out/'summary.json')['offlineValidationDecodes'] == len(rows(out/'solutions.jsonl'))
    write_once(out/'observation-acceptance.json', {
        'status':'PASS','successfulFE':500000,'failedFE':0,'sameInitials':True,'samePhysicalLedger':True,
        'sameFEFronts':True,'sameFinalGenomes':True,'sameSearchCounts':True,'sameDecoderOperationCounts':True,
        'scope':'Observable checkpoints and output equality only; these original performance traces have no whole-paid-sequence hash. '
                'No source or search class was changed. Profiling timing is not performance evidence.'})
    return receipt


def run_case(root, case, helper_cp, jfr_tool):
    stem, method = case['stem'], case['method']
    original = SOURCE/stem/str(SEED)/method
    out = root/stem/method; out.mkdir(parents=True)
    cmd = read(original/'command.json')
    entry = cmd.index('research.dynamic.PddrIsolationRun')
    assert cmd[entry+4] == str(original)
    cmd[entry+4] = str(out)
    cmd[cmd.index('-cp')+1] = helper_cp
    jfr_path = out/'profile.jfr'
    cmd[1:1] = [f'-XX:StartFlightRecording=settings=profile,dumponexit=true,maxsize=32m,filename={jfr_path}',
                '-XX:FlightRecorderOptions=stackdepth=128']
    write_once(out/'command.json', cmd)
    print('FROZEN_COST_PROFILE', stem, method, flush=True)
    execute(cmd, out/'run.log', timeout=180)
    receipt = verify_trace(out, original)
    assert jfr_path.is_file() and jfr_path.stat().st_size > 0
    execute([str(jfr_tool),'print','--json','--stack-depth','128','--events',
             'jdk.ExecutionSample,jdk.ObjectAllocationSample',str(jfr_path)], out/'jfr-events.json')
    return receipt


def main():
    root = ROOT/'runs'/datetime.now().strftime('frozen-cost-profile-%Y%m%d-%H%M%S-%f')
    root.mkdir(); print('FROZEN_COST_ROOT', root, flush=True)
    cases = [{'stem':stem,'method':method} for stem in STEMS for method in METHODS]
    completed = []
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            write_once(root/'protocol.json', {
                'source':str(SOURCE),'instances':STEMS,'seed':SEED,'methods':METHODS,'cases':cases,
                'plannedFE':2000000,'perRunFE':500000,'sourceOfAllInputAndOptions':'Exact frozen command.json, unchanged source paths and classpath.',
                'question':'Where do the frozen four-role and matched NSGA-II actually spend CPU and allocation effort?',
                'observation':'Local existing JDK Flight Recorder, settings=profile, stackdepth128, max32MB, one JVM at a time. '
                              'Helper-only classpath prefix exports identities; it contains no scheduling class.',
                'acceptance':'500000 successful,0failed, old initialization/physical ledger/final genomes/allFE fronts/search counts/decoder operation counts identical. '
                             'No whole-paid-sequence hash in frozen performance run; do not claim one.',
                'limits':'Sampling is descriptive, can perturb time and omit inlined frames. No quality winner, same-time advantage, new algorithm, '
                         'parameter scan or automatic optimization. Only a demonstrated hot path may motivate a separate exact-equivalence engineering protocol.',
                'preserved':'Default production mainline, four duties, Q, family, sharing and every frozen result; no installs, transfers or public push.'})
            first = read(SOURCE/STEMS[0]/str(SEED)/METHODS[0]/'command.json')
            original_cp = first[first.index('-cp')+1]
            helper_cp = identity_tool(root,original_cp)
            execute(['java','-cp',helper_cp,'research.dynamic.ClassResolutionProbe',
                     'org.uma.jmetal.util.research.model.DynamicDecoder',
                     'org.uma.jmetal.util.research.DynamicEvaluation',
                     'org.uma.jmetal.util.research.runtime.ThreeObjectiveArchive',
                     'org.uma.jmetal.util.research.search.Particle',
                     'org.uma.jmetal.util.research.search.LocalPddrKernel'],root/'runtime-class-identity.json')
            jfr_tool = Path(read(root/'runtime-class-identity.json')['javaHome'])/'bin/jfr.exe'
            assert jfr_tool.is_file(), 'Existing local JDK JFR tool missing; no installation attempted'
            for case in cases:
                completed.append(run_case(root,case,helper_cp,jfr_tool))
            result = analyze(root,cases)
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completedRuns':len(completed),'error':str(exc)});raise
    write_once(root/'status.json',{'status':'COMPLETE','successfulFE':sum(r['successful'] for r in completed),
        'failedFE':0,'offlineReturnFullDecoderQA':sum(read(root/c['stem']/c['method']/'summary.json')['offlineValidationDecodes'] for c in cases),
        'searchSamples':{c['stem']+'/'+c['method']:c['searchCpuSamples'] for c in result['cases']}})
    print('FROZEN_COST_COMPLETE',read(root/'status.json'),flush=True)


if __name__=='__main__':
    main()
