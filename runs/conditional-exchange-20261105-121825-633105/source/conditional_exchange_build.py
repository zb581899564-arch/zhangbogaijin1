"""Single shadow neighborhood change plus evidence export; original production/default untouched."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, write_once, execute
from run_paired_qgs_guidance import replace
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest
from candidate_redundancy_build import ENTRY, NAMES, PREFIX, original_sources


def build(root):
    base = (ENTRY / 'classpath.txt').read_text('utf-8-sig').strip(); original = original_sources(root, base)
    source, classes = root / 'source', root / 'classes'; source.mkdir(); classes.mkdir()
    intra = original['IntraNeighborhoods'].read_text('utf-8')
    for operator, vector in ((5, 'ParticleOperators.machines(child)'), (8, 'child.getVariablesworker()')):
        intra = replace(intra, f'else if (operator == {operator}) permute({vector}, positions, 2);',
            f'else if (operator == {operator}) {{\n'
            f'            if (!ConditionalResourceExchange.apply({vector}, positions)) permute({vector}, positions, 2);\n        }}')
    entry = (ENTRY / 'source/NaturalLocalRun.java').read_text('utf-8').replace('NaturalLocalRun', 'ConditionalExchangeRun')
    entry = replace(entry, '        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));',
        '        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));\n'
        '        lines(out.resolve("conditional-exchange.json"),Collections.singletonList(ConditionalResourceExchange.diagnostics()));')
    (source / 'IntraNeighborhoods.java').write_text(intra, encoding='utf-8')
    (source / 'ConditionalExchangeRun.java').write_text(entry, encoding='utf-8')
    for path in (ROOT / 'src/algorithms/diagnostics/conditional_exchange').glob('*.java'): shutil.copy2(path, source)
    for name in ('conditional_exchange_build.py', 'conditional_exchange_design.py', 'conditional_exchange_execution.py',
                 'conditional_exchange_analysis.py', 'run_conditional_exchange_pilot.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    execute(['java', '-version'], root / 'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes),
             *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{base}';(root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'class-hashes.json', class_hashes(classes))
    write_once(root / 'source-hashes.json', {str(p.relative_to(source)): digest(p) for p in source.glob('*') if p.is_file()})
    execute(['java', '-cp', cp, 'research.dynamic.ClassResolutionProbe', *(PREFIX + n for n in NAMES),
             PREFIX + 'ConditionalResourceExchange'], root / 'loaded-identity.json')
    return cp
