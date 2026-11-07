"""Compile observer-only frozen shadows and a diagnostic bridge to the actual classic kernel."""
from pathlib import Path
import shutil
from run_long_budget_bridge import ROOT, write_once, execute
from global_working_build import original_sources, ENTRY
from paired_survival_bench import class_hashes
from run_paired_qgs_guidance import replace


def build(root):
    oldcp=(ENTRY/'classpath.txt').read_text('utf-8')
    originals=original_sources(root,oldcp)
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    canonical=originals['CanonicalHmopso'].read_text('utf-8')
    canonical=replace(canonical,'            Map<Direction, List<Particle>> updated = new EnumMap<>(Direction.class);',
        '            MatingSourceAudit.generationStarted(groups);\n            Map<Direction, List<Particle>> updated = new EnumMap<>(Direction.class);')
    canonical=replace(canonical,'            List<Particle> next = global(current, direction, leader);',
        '            MatingSourceAudit.beforeBatch(direction, step, current);\n            List<Particle> next = global(current, direction, leader);')
    group=originals['GlobalGroupPolicy'].read_text('utf-8')
    group=replace(group,'        return out;\n    }\n    public static Map<String,Object> diagnostics()',
        '        MatingSourceAudit.selected(out, role);\n        return out;\n    }\n    public static Map<String,Object> diagnostics()')
    entry=(ENTRY/'source/PddrIsolationRun.java').read_text('utf-8')
    entry=replace(entry,'            if (digest != null) digest.update(paid, s);',
        '            if (digest != null) digest.update(paid, s);\n            org.uma.jmetal.util.research.search.MatingSourceAudit.paid(s, paid, archive);')
    entry=replace(entry,'        obs.write(out);',
        '        obs.write(out);\n        org.uma.jmetal.util.research.search.MatingSourceAudit.finish(out);')
    for name,body in (('CanonicalHmopso',canonical),('GlobalGroupPolicy',group),('PddrIsolationRun',entry)):
        (source/f'{name}.java').write_text(body,encoding='utf-8')
    for name in ('PaidObjectiveMirror','MatingSourceAudit','ClassicMatingBridge','MatingPoolProbe','NeutralProbeSupport','ClassResolutionProbe'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
    for name in ('mating_probe_build.py','mating_pool_analysis.py','run_mating_pool_probe.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    shutil.copytree(ROOT/'research/composition_oracle',source/'composition_oracle',ignore=shutil.ignore_patterns('__pycache__'))
    execute(['javac','-encoding','UTF-8','--release','8','-cp',oldcp,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{oldcp}'
    (root/'classpath.txt').write_text(cp,encoding='utf-8')
    execute(['java','-cp',cp,'research.dynamic.ClassResolutionProbe',
        'org.uma.jmetal.util.research.classic.NsgaSelection','org.uma.jmetal.util.research.classic.ClassicVariation',
        'org.uma.jmetal.util.research.classic.ClassicKernelBridge','org.uma.jmetal.util.research.DynamicEvaluation',
        'org.uma.jmetal.util.research.search.CanonicalHmopso','org.uma.jmetal.util.research.search.GlobalGroupPolicy'],root/'loaded-identity.json')
    return cp
