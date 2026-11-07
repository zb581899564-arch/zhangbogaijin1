"""Only observe real VNS programs in a frozen shadow LocalSearch and isolated evidence entry."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, write_once, execute
from run_paired_qgs_guidance import replace
from candidate_redundancy_build import ENTRY, PREFIX, NAMES, original_sources
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest

KEY_SOURCE = ROOT / 'runs/candidate-redundancy-20261105-120604-024210/source/CandidatePhysicalKey.java'


def local_source(text):
    old = '''            PermutationSolution<Integer> shaken = evaluateNeighborhood(incumbent, factory, operator, direction, remaining);
            PermutationSolution<Integer> improved = descent(shaken, factory, direction, reference, remaining);
            if (LocalPddrKernel.better(direction, improved, incumbent, reference)) {
                incumbent = improved; operator = 0; state.count("intra.accepted");
            } else operator++;'''
    new = '''            LocalProgramTrace.begin(incumbent, factory, operator, direction, state.ledgerGroup(direction), reference);
            boolean completeProgram = false;
            try {
                PermutationSolution<Integer> shaken = evaluateNeighborhood(incumbent, factory, operator, direction, remaining);
                LocalProgramTrace.shaken(shaken);
                PermutationSolution<Integer> improved = descent(shaken, factory, direction, reference, remaining);
                boolean accepted = LocalPddrKernel.better(direction, improved, incumbent, reference);
                LocalProgramTrace.finished(improved, accepted);
                if (accepted) {
                    incumbent = improved; operator = 0; state.count("intra.accepted");
                } else operator++;
                completeProgram = true;
            } finally { LocalProgramTrace.end(completeProgram); }'''
    return replace(text, old, new)


def build(root):
    base = (ENTRY / 'classpath.txt').read_text('utf-8-sig').strip(); originals = original_sources(root, base)
    source, classes = root / 'source', root / 'classes';source.mkdir();classes.mkdir()
    local = local_source(originals['LocalSearch'].read_text('utf-8'))
    entry = (ENTRY / 'source/NaturalLocalRun.java').read_text('utf-8').replace('NaturalLocalRun', 'LocalProgramRun')
    entry = replace(entry, '            lastPaid.observed(archive,fe);',
                    '            lastPaid.observed(archive,fe);\n            LocalProgramTrace.paid(value,fe,changed);')
    entry = replace(entry, '        NaturalRunEvidence.identity(out);',
                    '        NaturalRunEvidence.identity(out);\n        LocalProgramTrace.configure(in.factories());')
    entry = replace(entry, '        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));',
                    '        lines(out.resolve("run-receipt.jsonl"),Collections.singletonList(receipt));\n        LocalProgramTrace.write(out);')
    (source / 'LocalSearch.java').write_text(local, encoding='utf-8')
    (source / 'LocalProgramRun.java').write_text(entry, encoding='utf-8')
    shutil.copy2(KEY_SOURCE, source)
    for path in (ROOT / 'src/algorithms/diagnostics/local_program').glob('*.java'):shutil.copy2(path, source)
    for name in ('local_program_build.py', 'local_program_analysis.py', 'local_program_stream.py', 'run_local_program_audit.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    execute(['java', '-version'], root / 'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes),
             *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{base}';(root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'class-hashes.json', class_hashes(classes))
    write_once(root / 'source-hashes.json', {str(p.relative_to(source)): digest(p) for p in source.glob('*') if p.is_file()})
    execute(['java', '-cp', cp, 'research.dynamic.ClassResolutionProbe', *(PREFIX + n for n in NAMES),
             PREFIX + 'LocalProgramTrace'], root / 'loaded-identity.json')
    return cp
