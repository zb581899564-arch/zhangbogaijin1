"""Capture whole-generation retention while reproducing the frozen full paid search sequence."""
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
import shutil

from paired_survival_bench import class_hashes,run_cell,FROZEN
from qgs_epoch_build import BASIS
from run_acceptance_plateau_audit import SOURCE,OBS,STEMS,SEED
from run_long_budget_bridge import ROOT,read,rows,write_once,execute,controller_lock
from run_paired_qgs_guidance import replace
from final_survival_analysis import analyze

PREFIX='org.uma.jmetal.util.research.search.'
IDENTITIES=tuple(PREFIX+n for n in ('SurvivorSelection','CanonicalHmopso','GlobalGroupPolicy','Particle','LocalSearch'))


def original_identity(root,cp):
    work=root/'original-class-identity';work.mkdir();classes=work/'classes';classes.mkdir()
    source=ROOT/'src/algorithms/diagnostics/ClassResolutionProbe.java';shutil.copy2(source,work)
    execute(['javac','-encoding','UTF-8','--release','8','-cp',cp,'-d',str(classes),str(work/source.name)],work/'compile.log')
    cmd=['java','-cp',f'{classes};{cp}','research.dynamic.ClassResolutionProbe',*IDENTITIES]
    execute(cmd,work/'origins.json');identity=read(work/'origins.json')
    resolved=unquote(identity[PREFIX+'SurvivorSelection']['codeSource'])
    assert resolved.rstrip('/').endswith(FROZEN.as_posix()+'/binary/cp-0'),resolved
    javap=Path(identity['javaHome'])/'bin/javap.exe'
    execute([str(javap),'-cp',cp,'-c','-p',PREFIX+'SurvivorSelection'],work/'survivor-bytecode.txt')
    write_once(work/'verified.json',{'status':'PASS','zeroSearchFE':True,'originalSurvivorSource':str(FROZEN/'source/src/java/search/SurvivorSelection.java'),
        'loadedClass':identity[PREFIX+'SurvivorSelection'],'scope':'Actual JVM resolution without search. Frozen source selected from original cp0, not current mutable production source.'})
    return identity


def build(root):
    cp=(BASIS/'classpath.txt').read_text(encoding='utf-8-sig').strip();original_identity(root,cp)
    src,classes=root/'source',root/'classes';src.mkdir();classes.mkdir()
    body=(FROZEN/'source/src/java/search/SurvivorSelection.java').read_text(encoding='utf-8')
    body=replace(body,'        return new Result(survivors, indices, fitness, categories, quotas);',
        '        FinalSurvivalTrace.selected(candidates, count, fitness, categories, quotas, indices);\n'
        '        return new Result(survivors, indices, fitness, categories, quotas);')
    (src/'SurvivorSelection.java').write_text(body,encoding='utf-8')
    entry=(BASIS/'source/PddrIsolationRun.java').read_text(encoding='utf-8')
    entry=replace(entry,'        Observations obs = new Observations(audit, limit, checkpoints);',
        '        org.uma.jmetal.util.research.search.FinalSurvivalTrace.configure(context::result);\n'
        '        Observations obs = new Observations(audit, limit, checkpoints);')
    entry=replace(entry,'            if (digest != null) digest.update(paid, s);',
        '            org.uma.jmetal.util.research.search.FinalSurvivalTrace.paid(paid);\n'
        '            if (digest != null) digest.update(paid, s);')
    entry=replace(entry,'        obs.write(out);','        obs.write(out);\n'
        '        append(out.resolve("final-survival.jsonl"), org.uma.jmetal.util.research.search.FinalSurvivalTrace.finish());\n'
        '        append(out.resolve("survival-class-origins.jsonl"), ClassResolutionProbe.capture(\n'
        '            "org.uma.jmetal.util.research.search.SurvivorSelection",\n'
        '            "org.uma.jmetal.util.research.search.FinalSurvivalTrace"));')
    (src/'PddrIsolationRun.java').write_text(entry,encoding='utf-8')
    for name in ('ClassResolutionProbe','FinalSurvivalTrace'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',src)
    for name in ('run_final_survival_audit.py','final_survival_analysis.py'):
        shutil.copy2(Path(__file__).with_name(name),src)
    execute(['javac','-encoding','UTF-8','--release','8','-cp',cp,'-d',str(classes),*map(str,src.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{cp}'
    (root/'classpath.txt').write_text(cp,encoding='utf-8');return cp


def replay(root,cp,stem,enabled):
    arm='ON' if enabled else 'OFF'
    out=run_cell(root,cp,{'stem':stem,'seed':SEED,'arm':arm},{'research.finalSurvival.trace':str(enabled).lower(),
        'research.personal.mode':'OLDEST','research.memory.audit':'true','research.group.mode':'FULL_ROLE',
        'research.reward.mode':'GROUP','research.batch.mode':'ROLE_CROWD'})
    original=SOURCE/stem/str(SEED)/'SHARE_FULL'
    for name in ('solutions.jsonl','initial-population.jsonl','local-ledger.csv'):
        assert (out/name).read_bytes()==(original/name).read_bytes(),name
    assert [r['front'] for r in rows(out/'anytime.jsonl')]==[r['front'] for r in rows(original/'anytime.jsonl')]
    receipt=rows(out/'run-receipt.jsonl')[0]
    assert receipt['paidSHA256']==rows(OBS/stem/str(SEED)/'SHARE_FULL_OFF/run-receipt.jsonl')[0]['paidSHA256']
    assert receipt['search']==rows(original/'run-receipt.jsonl')[0]['search']
    identity=rows(out/'survival-class-origins.jsonl')[0]
    assert unquote(identity[PREFIX+'SurvivorSelection']['codeSource']).rstrip('/').endswith((root/'classes').as_posix())
    trace=rows(out/'final-survival.jsonl')[0]
    assert trace['enabled']==enabled and len(trace['events'])==(1 if enabled else 0)
    write_once(out/'observation-equivalence.json',{'status':'PASS','full500kPaidSequenceSHAIdentical':True,
        'frontsGenesLedgerInitialsAndCountersIdentical':True,'actualLoadedObserverIdentityVerified':True})


def main():
    root=ROOT/'runs'/datetime.now().strftime('final-survival-audit-%Y%m%d-%H%M%S-%f');root.mkdir()
    print('FINAL_SURVIVAL_AUDIT_ROOT',root,flush=True);done=[]
    try:
        with controller_lock(ROOT/'research/night_research','dispatch.lock'):
            specs=read(BASIS/'protocol.json')['instances']
            write_once(root/'protocol.json',{'instances':specs,'seed':SEED,'arms':['OFF','ON'],'successfulReplayFEPlanned':2000000,
                'question':'Does first complete-generation global100 union local100 retention lose unique ND objective coverage that a same-quota feasible subset could retain? This differs from the already-tested QGS groupwise global survival.',
                'engineering':'Resolve original SurvivorSelection in a no-search JVM, capture actual class URL/bytes SHA and JDK. Shadow only frozen source with one post-selection observation. OFF and ON each must reproduce full500k paid-sequence digest, all fronts, final genes, initials, physical ledger including restarts, and search counts. Failed observations retained and not interpreted.',
                'snapshots':'Every completed whole-generation selection, not outcome-selected. Expect exactly one at this500k ledger. All200 already-paid genomes/objectives, fitness, exact indices/categories/quotas, and contemporaneous external archive. No RNG use or change in search decisions.',
                'offlineControls':'Reconstruct actual PDDR+stable order exactly. Same quotas for PDDR_LOCAL_FIRST, PDDR_UNIQUE, RANK_CROWD_UNIQUE. These are feasible same-pool retention witnesses, not optimal-subset or new search methods. No effect on search/result archive.',
                'gate':'Both instances must lose >=2 unique globally ND objective vectors and at least one pre-fixed same-quota witness must increase internally retained HV >=0.5% over actual. A pass only authorizes a fresh retention hypothesis/protocol; no selector implemented in this audit. Duplicate-only explanation is reported separately, not a novel mechanism.',
                'metric':'Same frozen normalization/reference1.5. Pool/retained HV differs from the official external all-paid archive, which already contains every evaluated pool point. Never count reselection as new official HV.',
                'cost':'Four500k replays =2000000FE, all successful evaluation attempts including duplicates/incremental reuse. Return full-decoder QA separately. Offline analysis zero searchFE; observer/digest costs preclude timing superiority.',
                'scope':'Existing development seed only, original oldest/serial/stale/FULL_ROLE/group reward/families/sharing/local ledger preserved. No failed makespan tie, CENTER reward, memory or guide mechanism reintroduced. Default mainline untouched.'})
            for stem in STEMS:
                shutil.copytree(SOURCE/stem/'inputs',root/stem/'inputs');folder=root/stem/str(SEED);folder.mkdir()
                shutil.copy2(SOURCE/stem/str(SEED)/'ledger.csv',folder/'ledger.csv')
            cp=build(root)
            for stem in STEMS:
                for enabled in (False,True):replay(root,cp,stem,enabled);done.append([stem,enabled])
            result=analyze(root,specs,SEED)
    except BaseException as exc:
        write_once(root/'status.json',{'status':'INCOMPLETE_RETAINED','completed':done,'error':str(exc)});raise
    write_once(root/'status.json',{'status':'COMPLETE','successfulReplayFE':2000000,'failedEvaluationFE':0,
        'fullSequenceEquivalence':True,'worthNewRetentionProtocol':result['worthNewRetentionProtocol'],
        'returnFullDecoderQA':sum(read(p)['offlineValidationDecodes'] for p in root.glob('*/*/*/summary.json'))})
    print('FINAL_SURVIVAL_AUDIT_COMPLETE',[(r['stem'],r['events'][0]['lostUniqueGlobalND'],
        {a:v['relativeGainPct'] for a,v in r['events'][0]['alternatives'].items()},r['supported']) for r in result['instances']],flush=True)


if __name__=='__main__':main()
