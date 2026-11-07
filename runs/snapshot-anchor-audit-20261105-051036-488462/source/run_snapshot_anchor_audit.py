"""Contract and whole-paid-trace engineering acceptance before any snapshot cost claim."""
from datetime import datetime
import shutil
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from run_frozen_cost_profile import verify_trace
from snapshot_anchor_build import build

SOURCE = ROOT/'runs/makespan-tie-screen-20261105-025223-471920'
STEMS = ('20_8_5_1','100_2_3_1')
METHODS = ('STRICT_FULL','NSGA_STRICT')
MODES = ('SERIAL','ANCHOR')
SEED = 10950003


def override(cmd, key, value):
    prefix=f'-D{key}='
    cmd=[s for s in cmd if not s.startswith(prefix)]
    cmd.insert(cmd.index('-cp'),prefix+value)
    return cmd


def fixtures(root,cp):
    results=[]
    for stem in STEMS:
        inp=root/stem/'inputs'
        for mode in MODES:
            out=root/stem/f'contract-{mode}.json'
            cmd=['java','-Xms32m','-Xmx2g',f'-Dresearch.snapshot.mode={mode}','-Dresearch.snapshot.audit=true',
                 '-cp',cp,'org.uma.jmetal.util.research.runtime.SnapshotContractChecks',str(inp/f'{stem}.txt'),
                 str(inp/'RECONSTRUCTED-setup.txt'),str(inp/'fatigue-input.txt'),str(out)]
            write_once(root/stem/f'contract-{mode}-command.json',cmd)
            execute(cmd,root/stem/f'contract-{mode}.log')
            result=read(out);assert result['status']=='PASS' and result['searchFE']==0
            results.append({'stem':stem,**result})
    write_once(root/'contract-results.json',results)
    return results


def run_case(root,cp,stem,method,mode):
    original=SOURCE/stem/str(SEED)/method
    out=root/stem/method/mode;out.mkdir(parents=True)
    cmd=read(original/'command.json');entry=cmd.index('research.dynamic.PddrIsolationRun')
    cmd[cmd.index('-cp')+1]=cp
    for index,name in ((1,f'{stem}.txt'),(2,'RECONSTRUCTED-setup.txt'),(3,'fatigue-input.txt')):
        cmd[entry+index]=str(root/stem/'inputs'/name)
    cmd[entry+4]=str(out);cmd[entry+7]=str(root/stem/'ledger.csv')
    cmd=override(cmd,'research.snapshot.mode',mode)
    cmd=override(cmd,'research.snapshot.audit','true')
    cmd=override(cmd,'research.memory.audit','true')
    write_once(out/'command.json',cmd)
    print('SNAPSHOT_ENGINEERING',stem,method,mode,flush=True)
    execute(cmd,out/'run.log',timeout=240)
    receipt=verify_trace(out,original)
    assert isinstance(receipt['paidSHA256'],str) and len(receipt['paidSHA256'])==64
    metrics,=rows(out/'copy-metrics.jsonl');assert metrics['enabled'] and metrics['mode']==mode
    if mode=='ANCHOR':
        serial=out.parent/'SERIAL'
        baseline,=rows(serial/'run-receipt.jsonl')
        assert receipt['paidSHA256']==baseline['paidSHA256']
        for name in ('initial-population.jsonl','solutions.jsonl','local-ledger.csv','archive-admissions.csv'):
            assert (out/name).read_bytes()==(serial/name).read_bytes(),name
        serial_metrics,=rows(serial/'copy-metrics.jsonl')
        assert metrics['searchCopyAttempts']==serial_metrics['searchCopyAttempts']
        write_once(out/'whole-trace-equivalence.json',{'status':'PASS','paidSHA256':receipt['paidSHA256'],
            'successfulFE':500000,'sameAdmissions':True,'sameAcceptedSearchCounts':True,'sameFEFronts':True,
            'sameFinalGenomes':True,'sameLedger':True,'sameSearchCopyCalls':True,
            'scope':'ANCHOR vs new SERIAL whole paid genome/objective digest; SERIAL vs original frozen run is separately observable-output equality.'})
    return {'stem':stem,'method':method,'mode':mode,'receipt':receipt,'metrics':metrics,
            'qa':read(out/'summary.json')['offlineValidationDecodes']}


def main():
    root=ROOT/'runs'/datetime.now().strftime('snapshot-anchor-audit-%Y%m%d-%H%M%S-%f')
    root.mkdir();print('SNAPSHOT_ANCHOR_ROOT',root,flush=True);completed=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            write_once(root/'protocol.json',{
                'source':str(SOURCE),'instances':STEMS,'seed':SEED,'methods':METHODS,'modes':MODES,
                'plannedFE':4000000,'perRunSuccessfulFE':500000,'plannedContractDecoderCalls':4,
                'implementation':'DefaultSERIAL retains frozen serialization. ExplicitANCHOR only replaces exact '
                                 'audited final Instance/DynamicParameters/DynamicSchedule/DynamicStep/SchedulingMetadata '
                                 'with per-copy in-memory handles; all other fields, aliases, cycles and mutable attributes '
                                 'remain Java serialized. No solution.copy shortcut.',
                'contracts':'Four fixtures before any search: actual private-final classes without serialization callbacks; '
                            'defensive getters, unknown mutable nested graph/cycles, vector aliases, mutablePrefix, '
                            'multiple snapshots independent, and failed dominating insertion does not remove old archive.',
                'acceptance':'Both instances and methods must have500000successful/0failed, equal full paidSHA256, '
                             'archive admissions, acceptance counters, FE fronts, final genomes, initial vectors, '
                             'decoder operations, physical ledger and copy counts. SERIAL also reproduces original frozen output.',
                'accounting':'All attempted evaluations guarded, source replays included. Contract decoder calls and '
                             'return full-decoder QA separate. Observation/digest costs enabled; no speed/same-time claim.',
                'nextGate':'Only all engineering acceptance passes permits a separately frozen observer-off cost '
                           'comparison with the SAME implementation for four duties and matched NSGA-II. No algorithm quality promotion.',
                'references':['https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/io/ObjectOutputStream.html',
                              'https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/io/ObjectInputStream.html'],
                'preserved':'Production runtime/model/search unchanged, original materials and every frozen record unchanged; no installs or file transfers.'})
            first=read(SOURCE/STEMS[0]/str(SEED)/METHODS[0]/'command.json');oldcp=first[first.index('-cp')+1]
            for stem in STEMS:
                shutil.copytree(SOURCE/stem/'inputs',root/stem/'inputs')
                shutil.copy2(SOURCE/stem/str(SEED)/'ledger.csv',root/stem/'ledger.csv')
                for method in METHODS:
                    cmd=read(SOURCE/stem/str(SEED)/method/'command.json')
                    assert cmd[cmd.index('-cp')+1]==oldcp
            cp=build(root,SOURCE,oldcp)
            execute(['java','-cp',cp,'research.dynamic.ClassResolutionProbe',
                     'org.uma.jmetal.util.research.runtime.SolutionSnapshots',
                     'org.uma.jmetal.util.research.runtime.AnchoredSnapshotGraph',
                     'org.uma.jmetal.util.research.model.Instance','org.uma.jmetal.util.research.model.DynamicParameters',
                     'org.uma.jmetal.util.research.model.DynamicSchedule','org.uma.jmetal.util.research.model.DynamicStep',
                     'org.uma.jmetal.util.research.SchedulingMetadata'],root/'runtime-class-identity.json')
            contracts=fixtures(root,cp)
            for stem in STEMS:
                for method in METHODS:
                    for mode in MODES:completed.append(run_case(root,cp,stem,method,mode))
            write_once(root/'analysis.json',{'cases':[{k:v for k,v in c.items() if k!='receipt'} for c in completed],
                'wholeTraceEngineeringAccepted':True,'scope':'Observation-on equivalence and serialization-volume diagnostics only.'})
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completedRuns':len(completed),'error':str(exc)});raise
    write_once(root/'status.json',{'status':'COMPLETE','successfulFE':sum(c['receipt']['successful'] for c in completed),
        'failedFE':0,'contractFullDecoderCalls':sum(c['engineeringFullDecoderCalls'] for c in contracts),
        'returnFullDecoderQA':sum(c['qa'] for c in completed),'wholeTraceEngineeringAccepted':True})
    print('SNAPSHOT_ANCHOR_COMPLETE',read(root/'status.json'),flush=True)


if __name__=='__main__':
    main()
