"""Read-only hooks in the actually loaded frozen global implementation, never production sources."""
from pathlib import Path
from urllib.parse import unquote, urlparse
import shutil
from run_long_budget_bridge import ROOT, read, write_once, execute
from paired_survival_bench import class_hashes
from run_paired_qgs_guidance import replace

ENTRY=ROOT/'runs/snapshot-anchor-audit-20261105-051047-172151'
PREFIX='org.uma.jmetal.util.research.search.'


def original_sources(root,cp):
    folder=root/'original-identity';folder.mkdir();classes=folder/'classes';classes.mkdir()
    java=ROOT/'src/algorithms/diagnostics/ClassResolutionProbe.java';shutil.copy2(java,folder)
    execute(['javac','-encoding','UTF-8','--release','8','-cp',cp,'-d',str(classes),str(folder/java.name)],folder/'compile.log')
    execute(['java','-cp',f'{classes};{cp}','research.dynamic.ClassResolutionProbe',PREFIX+'CanonicalHmopso',PREFIX+'GlobalGroupPolicy'],folder/'identity.json')
    identities=read(folder/'identity.json');sources={}
    for name in ('CanonicalHmopso','GlobalGroupPolicy'):
        parsed=unquote(urlparse(identities[PREFIX+name]['codeSource']).path)
        if parsed.startswith('/') and len(parsed)>2 and parsed[2]==':':parsed=parsed[1:]
        code=Path(parsed);source=code.parent/'source'/f'{name}.java'
        assert source.is_file() and source.is_relative_to(ROOT/'runs'),f'Unknown frozen source for {name}: {source}'
        sources[name]=source
    write_once(folder/'selected-sources.json',{k:str(v) for k,v in sources.items()})
    return sources


def build(root,oldcp):
    originals=original_sources(root,oldcp)
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    canonical=originals['CanonicalHmopso'].read_text('utf-8')
    canonical=replace(canonical,'            Map<Direction, List<Particle>> updated = new EnumMap<>(Direction.class);',
        '            GlobalWorkingAudit.generationStarted(groups);\n            Map<Direction, List<Particle>> updated = new EnumMap<>(Direction.class);')
    canonical=replace(canonical,'            List<Particle> next = global(current, direction, leader);',
        '            GlobalWorkingAudit.beforeBatch(direction, step, current);\n            List<Particle> next = global(current, direction, leader);')
    group=originals['GlobalGroupPolicy'].read_text('utf-8')
    group=replace(group,'        return out;\n    }\n    public static Map<String,Object> diagnostics()',
        '        GlobalWorkingAudit.selected(parents, children, out, role);\n        return out;\n    }\n    public static Map<String,Object> diagnostics()')
    entry=(ENTRY/'source/PddrIsolationRun.java').read_text('utf-8')
    entry=replace(entry,'            if (digest != null) digest.update(paid, s);',
        '            if (digest != null) digest.update(paid, s);\n            org.uma.jmetal.util.research.search.GlobalWorkingAudit.paid(s, paid, archive);')
    entry=replace(entry,'        obs.write(out);',
        '        obs.write(out);\n        org.uma.jmetal.util.research.search.GlobalWorkingAudit.finish(out);')
    for name,body in (('CanonicalHmopso',canonical),('GlobalGroupPolicy',group),('PddrIsolationRun',entry)):
        (source/f'{name}.java').write_text(body,encoding='utf-8')
    for name in ('GlobalWorkingAudit','WorkingPoolSelection','ClassResolutionProbe','PoolAssemblyCheckRun'):
        shutil.copy2(ROOT/f'src/algorithms/diagnostics/{name}.java',source)
    for name in ('global_working_build.py','global_working_analysis.py','run_global_working_audit.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    execute(['javac','-encoding','UTF-8','--release','8','-cp',oldcp,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    write_once(root/'class-hashes.json',class_hashes(classes));cp=f'{classes};{oldcp}'
    (root/'classpath.txt').write_text(cp,encoding='utf-8');return cp
