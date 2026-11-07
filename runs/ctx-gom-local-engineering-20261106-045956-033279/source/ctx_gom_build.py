"""Compile new modules separately from three isolated source overrides; frozen core remains selectable."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, write_once, execute
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes
from frozen_classpath_identity import resolve_class

BASE = ROOT/'runs/qpa-capability-pilot-20261106-025546-344483'
CONTRACT = ROOT/'research/gomea_reference_audit/CTX_GOM_LOCAL_ENGINEERING_V1.json'
ORIGINALS = {
    'CanonicalHmopso': ROOT/'runs/group-survival-gate-20261104-234602-311536/source/CanonicalHmopso.java',
    'LocalSearch': ROOT/'runs/pddr-equivalence-20261104-081553-961399/source/LocalSearch.java',
    'DeepLocalVisits': ROOT/'runs/dynamic-deep-local-20261103-184901-271850/source/DeepLocalVisits.java',
}


def once(value, old, new):
    if value.count(old) != 1:
        raise ValueError('Frozen patch anchor not unique: '+old[:80])
    return value.replace(old, new)


def build(root):
    base = (BASE/'classpath.txt').read_text('utf-8-sig').strip(); plan = read(CONTRACT)
    for name, expected in plan['criticalOriginalClasses'].items():
        assert resolve_class(base, name) == expected
    source, kernel, overrides, patches = [root/name for name in ('source', 'kernel-classes', 'override-classes', 'overrides')]
    for path in (source, kernel, overrides, patches):
        path.mkdir()
    for folder in ('src/algorithms/context_gom', 'src/algorithms/diagnostics/context_gom'):
        for path in (ROOT/folder).glob('*.java'):
            shutil.copy2(path, source)
    for name in ('ctx_gom_build.py', 'ctx_gom_replay.py', 'ctx_gom_model_checks.py', 'ctx_gom_engineering_cases.py',
                 'run_ctx_gom_engineering.py', 'pa_population_model_checks.py', 'pa_population_state_checks.py',
                 'pa_model_audit_analysis.py', 'qpa_state_checks.py', 'frozen_classpath_identity.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    execute(['java', '-version'], root/'jdk-version.log')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(kernel),
             *map(str, source.glob('*.java'))], root/'compile-kernel.log')
    legacy = str(kernel)+';'+base
    canonical = ORIGINALS['CanonicalHmopso'].read_text('utf-8-sig')
    canonical = once(canonical, '    private final int chapter;',
        '    private final int chapter;\n    private final Instance gomInstance;')
    canonical = once(canonical, '        this.chapter = chapter; this.config = Objects.requireNonNull(config, "config").resolved(chapter);',
        '        this.gomInstance = instance;\n        this.chapter = chapter; this.config = Objects.requireNonNull(config, "config").resolved(chapter);')
    canonical = once(canonical, '            List<PermutationSolution<Integer>> reference = solutions(globallyUpdated);',
        '            List<PermutationSolution<Integer>> reference = solutions(globallyUpdated);\n'
        '            if (GomRunScope.enabled()) GomRunScope.begin(reference, gomInstance);')
    local = ORIGINALS['LocalSearch'].read_text('utf-8-sig')
    local = once(local, '        return improveIntra(improveInter(particle, direction, reference), direction, reference);',
        '        if (GomRunScope.enabled()) {\n'
        '            if (chapter != 4) throw new IllegalStateException("Context GOM is chapter4 only");\n'
        '            return GomLocalProgram.improve(particle, direction, state);\n'
        '        }\n        return improveIntra(improveInter(particle, direction, reference), direction, reference);')
    local = once(local, '    Particle improve(Particle particle, Direction direction, List<PermutationSolution<Integer>> reference) {',
        '    void beginGomPopulation(List<PermutationSolution<Integer>> population) { GomRunScope.begin(population, instance); }\n'
        '    Particle improve(Particle particle, Direction direction, List<PermutationSolution<Integer>> reference) {')
    deep = ORIGINALS['DeepLocalVisits'].read_text('utf-8-sig')
    deep = once(deep, '        Map<Direction, List<PermutationSolution<Integer>>> slots = localRoles(population);',
        '        if (GomRunScope.enabled()) local.beginGomPopulation(population);\n'
        '        Map<Direction, List<PermutationSolution<Integer>>> slots = localRoles(population);')
    for name, value in (('CanonicalHmopso', canonical), ('LocalSearch', local), ('DeepLocalVisits', deep)):
        (patches/(name+'.java')).write_text(value, encoding='utf-8')
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', legacy, '-d', str(overrides),
             *map(str, patches.glob('*.java'))], root/'compile-overrides.log')
    modified = str(overrides)+';'+legacy
    (root/'legacy-classpath.txt').write_text(legacy, encoding='utf-8'); (root/'classpath.txt').write_text(modified, encoding='utf-8')
    write_once(root/'source-hashes.json', {str(p.relative_to(root)): digest(p) for directory in (source, patches) for p in directory.iterdir()})
    write_once(root/'class-hashes.json', {'kernel': class_hashes(kernel), 'overrides': class_hashes(overrides)})
    write_once(root/'original-source-identities.json', {name: {'path': str(path), 'sha256': digest(path)} for name, path in ORIGINALS.items()})
    write_once(root/'dependency-identities.json', [{'position': i, 'path': raw, 'jarSHA256': digest(Path(raw)) if Path(raw).is_file() else None}
               for i, raw in enumerate(base.split(';'))])
    return legacy, modified
