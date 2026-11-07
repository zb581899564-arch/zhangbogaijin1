"""Read-only envelopes before finite-pool truncation, preserving the frozen shared search."""
from pathlib import Path
import shutil

from paired_survival_bench import FROZEN,class_hashes
from qgs_epoch_build import BASIS
from pool_phase_build import canonical_source,cooperation_source
from run_long_budget_bridge import ROOT,execute,write_once
from run_paired_qgs_guidance import replace


def phase_source():
    body=(ROOT/'src/algorithms/diagnostics/PoolPhaseAudit.java').read_text(encoding='utf-8')
    body=replace(body,'public final class PoolPhaseAudit {',
        'public final class PoolPhaseAudit {\n    private static final boolean ENABLED=Boolean.getBoolean("research.poolRetention.trace");')
    for signature in ('public static void groups(List<PermutationSolution<Integer>> center) {',
        'public static void globalEnd(SwarmSupport support,List<PermutationSolution<Integer>> center) {',
        'public static void localEnd(SwarmSupport support,Direction role) {',
        'public static void centerEntry(SwarmSupport support,Direction role) {'):
        body=replace(body,signature,signature+'\n        if(!ENABLED)return;')
    return replace(body,'    public static Map<String,Object> finish() {',
        '    public static Map<String,Object> finish() {\n        if(!ENABLED)return Collections.singletonMap("enabled",false);')


def build(root):
    src,classes=root/'source',root/'classes';src.mkdir();classes.mkdir()
    cp=(BASIS/'classpath.txt').read_text(encoding='utf-8-sig').strip()
    cooperation=replace(cooperation_source(),'return PoolPhaseAudit.pool(pools, contexts, energyScale, wageScale);',
        'return PoolRetentionTrace.pool(pools, contexts, energyScale, wageScale);')
    factory=(FROZEN/'source/src/algorithms/cooperation/FactoryPool.java').read_text(encoding='utf-8')
    factory=replace(factory,'        for (FactoryRecord r : records) if (r.same(candidate) || r.dominates(candidate))',
        '        PoolRetentionTrace.observe(this, candidate);\n        for (FactoryRecord r : records) if (r.same(candidate) || r.dominates(candidate))')
    for name,body in (('CanonicalHmopso',canonical_source()),('CooperationSupport',cooperation),
                      ('FactoryPool',factory),('PoolPhaseAudit',phase_source())):
        (src/f'{name}.java').write_text(body,encoding='utf-8')
    entry=(BASIS/'source/PddrIsolationRun.java').read_text(encoding='utf-8')
    entry=replace(entry,'        Observations obs = new Observations(audit, limit, checkpoints);',
        '        org.uma.jmetal.util.research.cooperation.PoolPhaseAudit.configure(context::result);\n'
        '        Observations obs = new Observations(audit, limit, checkpoints);')
    entry=replace(entry,'            if (digest != null) digest.update(paid, s);',
        '            org.uma.jmetal.util.research.cooperation.PoolPhaseAudit.paid(paid);\n'
        '            if (digest != null) digest.update(paid, s);')
    entry=replace(entry,'        obs.write(out);','        obs.write(out);\n'
        '        append(out.resolve("pool-phases.jsonl"), org.uma.jmetal.util.research.cooperation.PoolPhaseAudit.finish());\n'
        '        append(out.resolve("pool-retention.jsonl"), org.uma.jmetal.util.research.cooperation.PoolRetentionTrace.diagnostics());\n'
        '        append(out.resolve("pool-class-origins.jsonl"), ClassResolutionProbe.capture(\n'
        '            "org.uma.jmetal.util.research.cooperation.FactoryPool",\n'
        '            "org.uma.jmetal.util.research.cooperation.PoolRetentionTrace"));')
    (src/'PddrIsolationRun.java').write_text(entry,encoding='utf-8')
    for name in ('PoolRetentionTrace','PoolAssemblyCheckRun','ClassResolutionProbe'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',src)
    for name in ('pool_retention_build.py','pool_retention_analysis.py','run_pool_retention_audit.py'):
        shutil.copy2(Path(__file__).with_name(name),src)
    execute(['javac','-encoding','UTF-8','--release','8','-cp',cp,'-d',str(classes),*map(str,src.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{cp}'
    (root/'classpath.txt').write_text(cp,encoding='utf-8');return cp
