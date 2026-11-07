"""Compile uniquely named isolated types; original common classes are never shadowed."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, write_once, execute
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest
from explicit_resource_design import KERNEL


def build(root):
    source, classes = root / 'source', root / 'classes'
    source.mkdir(); classes.mkdir()
    for path in (ROOT / 'src/algorithms/diagnostics/explicit_resources').glob('*.java'):
        shutil.copy2(path, source)
    for name in ('NeutralProbeSupport', 'ClassResolutionProbe'):
        shutil.copy2(ROOT / f'src/algorithms/diagnostics/{name}.java', source)
    for name in ('explicit_resource_design.py', 'explicit_resource_build.py', 'explicit_resource_analysis.py',
                 'run_explicit_resource_witness.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    shutil.copytree(ROOT / 'research/composition_oracle', source / 'composition_oracle',
                    ignore=shutil.ignore_patterns('__pycache__'))
    cp = (KERNEL / 'classpath.txt').read_text(encoding='utf-8-sig').strip()
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', cp, '-d', str(classes),
             *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{cp}'
    (root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'class-hashes.json', class_hashes(classes))
    write_once(root / 'source-hashes.json', {str(p.relative_to(source)): digest(p)
                                           for p in source.rglob('*') if p.is_file()})
    execute(['java', '-cp', cp, 'research.dynamic.ClassResolutionProbe',
             *('org.uma.jmetal.util.research.model.' + name for name in
               ('DynamicDecoder', 'DynamicValidator', 'DynamicStageState', 'DynamicPhysics',
                'StageResourcePlan', 'ExplicitSchedule', 'ExplicitResourceDecoder', 'ExplicitResourceValidator')),
             'org.uma.jmetal.util.research.runtime.BudgetedProblem'], root / 'loaded-identity.json')
    return cp
