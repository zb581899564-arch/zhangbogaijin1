"""Shadow only the original outer VNS call; preserve original inner descent source byte-for-byte."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, write_once, execute
from run_paired_qgs_guidance import replace
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest
from candidate_redundancy_build import ENTRY, NAMES, PREFIX, original_sources


def build(root):
    base = (ENTRY / 'classpath.txt').read_text('utf-8-sig').strip();original = original_sources(root, base)
    source, classes = root / 'source', root / 'classes';source.mkdir();classes.mkdir()
    old = original['LocalSearch'].read_text('utf-8')
    needle = 'if (LocalPddrKernel.better(direction, improved, incumbent, reference)) {'
    local = replace(old, needle, 'if (ProgramExitPolicy.better(direction, improved, incumbent, reference)) {')
    assert local.replace('ProgramExitPolicy.better(direction, improved, incumbent, reference)',
                         'LocalPddrKernel.better(direction, improved, incumbent, reference)') == old
    entry = (ENTRY / 'source/NaturalLocalRun.java').read_text('utf-8').replace('NaturalLocalRun', 'ProgramExitRun')
    entry = replace(entry, '        DynamicEvaluation decoder=new DynamicEvaluation(source,in,params,true);',
        '        ProgramExitPolicy.initialize();\n        DynamicEvaluation decoder=new DynamicEvaluation(source,in,params,true);')
    entry = replace(entry, '        NaturalRunEvidence.identity(out);',
        '        NaturalRunEvidence.identity(out);\n'
        '        lines(out.resolve("program-exit-loaded-identity.jsonl"),Collections.singletonList(ClassResolutionProbe.capture(\n'
        '            "org.uma.jmetal.util.research.search.LocalSearch", "org.uma.jmetal.util.research.search.ProgramExitPolicy",\n'
        '            "org.uma.jmetal.util.research.search.ProgramExitHv3D", "org.uma.jmetal.util.research.search.LocalPddrKernel")));')
    entry = replace(entry, '        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));',
        '        ProgramExitPolicy.write(out);\n        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));')
    (source / 'LocalSearch.java').write_text(local, encoding='utf-8');(source / 'ProgramExitRun.java').write_text(entry, encoding='utf-8')
    for path in (ROOT / 'src/algorithms/diagnostics/program_exit').glob('*.java'):shutil.copy2(path, source)
    for name in ('program_exit_design.py', 'program_exit_build.py', 'program_exit_execution.py',
                 'program_exit_analysis.py', 'run_program_exit_pilot.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    execute(['java', '-version'], root / 'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes), *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{base}';(root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'class-hashes.json', class_hashes(classes));write_once(root / 'source-hashes.json', {p.name: digest(p) for p in source.glob('*')})
    write_once(root / 'scope-acceptance.json', {'status': 'PASS', 'outerCallChanges': 1,
        'reversingOnlyOuterCallReproducesOriginalSource': True, 'innerAndInterCallSitesUnchanged': True})
    execute(['java', '-cp', cp, 'research.dynamic.ClassResolutionProbe', *(PREFIX + n for n in NAMES),
        PREFIX + 'ProgramExitPolicy', PREFIX + 'ProgramExitHv3D'], root / 'loaded-identity.json')
    return cp
