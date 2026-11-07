"""Compile only new probe classes and freeze actual common-kernel identities."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, write_once, execute
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest
from paid_teacher_design import SOURCE


def build(root):
    source, classes = root / 'source', root / 'classes'; source.mkdir(); classes.mkdir()
    for path in (ROOT / 'src/algorithms/diagnostics/paid_teacher').glob('*.java'):
        shutil.copy2(path, source)
    for name in ('NeutralProbeSupport', 'ClassResolutionProbe'):
        shutil.copy2(ROOT / f'src/algorithms/diagnostics/{name}.java', source)
    for name in ('paid_teacher_design.py', 'paid_teacher_analysis.py', 'paid_teacher_build.py',
                 'run_paid_archive_teacher_probe.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    shutil.copytree(ROOT / 'research/composition_oracle', source / 'composition_oracle',
                    ignore=shutil.ignore_patterns('__pycache__'))
    base = (SOURCE / 'classpath.txt').read_text(encoding='utf-8-sig').strip()
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes),
             *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{base}'; (root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'class-hashes.json', class_hashes(classes))
    write_once(root / 'source-hashes.json', {str(p.relative_to(source)): digest(p)
                                           for p in source.rglob('*') if p.is_file()})
    execute(['java', '-cp', cp, 'research.dynamic.ClassResolutionProbe',
             'org.uma.jmetal.util.research.mechanism.KernelVariants',
             'org.uma.jmetal.util.research.mechanism.JobAlignedPaperKernel',
             'org.uma.jmetal.util.research.mechanism.JobAlignedResources',
             'org.uma.jmetal.util.research.DynamicEvaluation', 'research.dynamic.ProbeData',
             'org.uma.jmetal.util.research.runtime.RunContext'], root / 'loaded-identity.json')
    return cp
