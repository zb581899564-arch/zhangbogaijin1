"""Read-only shadow hooks in actual loaded frozen sources; never touch production modules."""
from pathlib import Path
from urllib.parse import urlparse, unquote
import shutil

from run_long_budget_bridge import ROOT, read, write_once, execute
from run_paired_qgs_guidance import replace
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest

ENTRY = ROOT / 'runs/natural-local-audit-20261105-073204-330248'
PREFIX = 'org.uma.jmetal.util.research.search.'
NAMES = ('SearchState', 'LocalSearch', 'IntraNeighborhoods', 'LocalPddrKernel', 'QgsLocalLedger')


def original_sources(root, base):
    execute(['java', '-cp', base, 'research.dynamic.ClassResolutionProbe', *(PREFIX + n for n in NAMES)],
            root / 'original-identity.json')
    result = {}; identity = read(root / 'original-identity.json'); target = root / 'original-source'; target.mkdir()
    for name in NAMES:
        decoded = unquote(urlparse(identity[PREFIX + name]['codeSource']).path)
        if decoded.startswith('/') and len(decoded) > 2 and decoded[2] == ':': decoded = decoded[1:]
        code = Path(decoded); path = code.parent / 'source' / f'{name}.java'
        if not path.is_file() and code.name == 'cp-0': path = code.parent.parent / 'source/src/java/search' / f'{name}.java'
        assert path.is_file() and path.is_relative_to(ROOT / 'runs'), name
        shutil.copy2(path, target / path.name); result[name] = path
    write_once(root / 'original-source-map.json', {name: str(p) for name, p in result.items()})
    return result


def build(root):
    base = (ENTRY / 'classpath.txt').read_text('utf-8-sig').strip(); original = original_sources(root, base)
    source, classes = root / 'source', root / 'classes'; source.mkdir(); classes.mkdir()
    state = replace(original['SearchState'].read_text('utf-8'), '        problem.evaluate(candidate);',
        '        CandidateRedundancy.enter(candidate, stage, direction);\n'
        '        try { problem.evaluate(candidate); } finally { CandidateRedundancy.exit(); }')
    intra = replace(original['IntraNeighborhoods'].read_text('utf-8'), '        SchedulingEncoding.repair(child, instance);',
        '        SchedulingEncoding.repair(child, instance);\n'
        '        CandidateRedundancy.intra(parent, child, instance, factory, operator);')
    entry = (ENTRY / 'source/NaturalLocalRun.java').read_text('utf-8').replace('NaturalLocalRun', 'CandidateRedundancyRun')
    entry = replace(entry, '            lastPaid.observed(archive,fe);',
                    '            CandidateRedundancy.paid(value,fe,changed);\n            lastPaid.observed(archive,fe);')
    entry = replace(entry, '        NaturalRunEvidence.identity(out);',
                    '        NaturalRunEvidence.identity(out);\n        CandidateRedundancy.configure(in,params);')
    entry = replace(entry, '        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));',
        '        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));\n'
        '        lines(out.resolve("candidate-redundancy.json"),Collections.singletonList(CandidateRedundancy.diagnostics()));')
    for name, text in (('SearchState', state), ('IntraNeighborhoods', intra), ('CandidateRedundancyRun', entry)):
        (source / f'{name}.java').write_text(text, encoding='utf-8')
    for path in (ROOT / 'src/algorithms/diagnostics/candidate_redundancy').glob('*.java'): shutil.copy2(path, source)
    for name in ('candidate_redundancy_build.py', 'candidate_redundancy_analysis.py', 'run_candidate_redundancy_audit.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    execute(['java', '-version'], root / 'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes),
             *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{base}';(root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'class-hashes.json', class_hashes(classes))
    write_once(root / 'source-hashes.json', {str(p.relative_to(source)): digest(p) for p in source.glob('*') if p.is_file()})
    execute(['java', '-cp', cp, 'research.dynamic.ClassResolutionProbe', *(PREFIX + n for n in NAMES),
             PREFIX + 'CandidateRedundancy'], root / 'loaded-identity.json')
    return cp
