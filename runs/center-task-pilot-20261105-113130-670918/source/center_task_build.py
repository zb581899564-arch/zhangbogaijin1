"""Shadow only actual frozen sources; keep every task mechanism outside production code."""
from pathlib import Path
from urllib.parse import unquote, urlparse
import shutil

from run_long_budget_bridge import ROOT, read, write_once, execute
from run_paired_qgs_guidance import replace
from paired_survival_bench import class_hashes
from research.semantic_repair.evidence import digest

ENTRY = ROOT / 'runs/natural-local-audit-20261105-073204-330248'
PREFIX = 'org.uma.jmetal.util.research.search.'
NAMES = ('CanonicalHmopso', 'SearchState', 'GlobalGroupPolicy', 'SurvivorSelection',
         'LocalPddrKernel', 'LocalSearch', 'QgsLocalLedger')


def originals(root, base):
    folder = root / 'original-source'; folder.mkdir()
    execute(['java', '-cp', base, 'research.dynamic.ClassResolutionProbe', *(PREFIX + n for n in NAMES)],
            root / 'original-identity.json')
    identities = read(root / 'original-identity.json'); selected = {}
    for name in NAMES:
        decoded = unquote(urlparse(identities[PREFIX + name]['codeSource']).path)
        if decoded.startswith('/') and len(decoded) > 2 and decoded[2] == ':': decoded = decoded[1:]
        code = Path(decoded)
        source = code.parent / 'source' / f'{name}.java'
        if not source.is_file() and code.name == 'cp-0':
            source = code.parent.parent / 'source/src/java/search' / f'{name}.java'
        assert source.is_file() and source.is_relative_to(ROOT / 'runs'), f'No frozen source for {name}'
        shutil.copy2(source, folder / source.name); selected[name] = source
    write_once(root / 'original-source-map.json', {k: str(p) for k, p in selected.items()})
    local = selected['LocalSearch'].read_text(encoding='utf-8')
    assert local.count('LocalPddrKernel.better') >= 3 and 'direction.better(' not in local
    return selected


def canonical_source(text):
    text = replace(text, '            Map<Direction, List<Particle>> groups = decompose(population);',
                   '            Map<Direction, List<Particle>> groups = decompose(population);\n            CenterTaskLifecycle.begin(groups);')
    text = replace(text, '            List<Particle> globalSnapshots = config.mergeGlobalLocal ? snapshots(globallyUpdated) : null;',
                   '            CenterTaskLifecycle.beforeLocal(updated);\n'
                   '            List<Particle> globalSnapshots = config.mergeGlobalLocal ? snapshots(globallyUpdated) : null;')
    text = replace(text, '        for (int step = 0; step < config.qIterations; step++) {',
                   '        for (int step = 0; step < config.qIterations; step++) {\n'
                   '            CenterTaskLifecycle.beforeBatch(current, direction, step);')
    text = replace(text, '            PermutationSolution<Integer> personal = particle.personalBest(preference);',
                   '            PermutationSolution<Integer> personal = CenterTaskDecisions.personal(particle, preference);')
    text = replace(text, '            if (audit != null) audit.generated(child, particle.current, composed);',
                   '            CenterTaskLifecycle.inherit(particle.current, child, direction);\n'
                   '            if (audit != null) audit.generated(child, particle.current, composed);')
    text = replace(text, 'double reward = GroupReward.compute(current, next, preference);',
                   'double reward = CenterTaskDecisions.reward(current, next, preference);')
    text = replace(text, '                    offspring.add(local.improve(particle, preference, reference));',
                   '                    CenterTaskLifecycle.localStart(particle, direction);\n'
                   '                    try { offspring.add(CenterTaskLifecycle.localResult(\n'
                   '                            local.improve(particle, preference, reference), particle, direction)); }\n'
                   '                    finally { CenterTaskLifecycle.localEnd(); }')
    return text


def build(root):
    base = (ENTRY / 'classpath.txt').read_text(encoding='utf-8-sig').strip()
    old = originals(root, base)
    source, classes = root / 'source', root / 'classes'; source.mkdir(); classes.mkdir()
    texts = {'CanonicalHmopso': canonical_source(old['CanonicalHmopso'].read_text('utf-8'))}
    texts['SearchState'] = replace(old['SearchState'].read_text('utf-8'), '        problem.evaluate(candidate);',
                                  '        problem.evaluate(candidate);\n        CenterTaskState.paid(candidate);')
    texts['GlobalGroupPolicy'] = replace(old['GlobalGroupPolicy'].read_text('utf-8'),
        '    static List<Particle> select(List<Particle> parents,List<Particle> children,Direction role) {',
        '    static List<Particle> select(List<Particle> parents,List<Particle> children,Direction role) {\n'
        '        if (CenterTaskState.enabled() && role == Direction.CENTER)\n'
        '            return CenterTaskDecisions.global(parents, children, role);')
    selection = replace(old['SurvivorSelection'].read_text('utf-8'),
        '        Objects.requireNonNull(candidates, "candidates");',
        '        if (CenterTaskState.enabled()) return CenterTaskRetention.select(candidates, count, support, checkpoint);\n'
        '        Objects.requireNonNull(candidates, "candidates");')
    texts['SurvivorSelection'] = replace(selection, '        private Result(List<Particle> survivors,',
                                        '        Result(List<Particle> survivors,')
    texts['LocalPddrKernel'] = replace(old['LocalPddrKernel'].read_text('utf-8'),
        '        if (direction == Direction.MAKESPAN)',
        '        if (direction == Direction.CENTER && CenterTaskState.scalar())\n'
        '            return CenterTaskDecisions.localBetter(candidate, incumbent);\n'
        '        if (direction == Direction.MAKESPAN)')
    entry = (ENTRY / 'source/NaturalLocalRun.java').read_text('utf-8').replace('NaturalLocalRun', 'CenterTaskRun')
    entry = replace(entry, 'NaturalRunEvidence.checkpoints(limit)', 'taskCheckpoints(limit)')
    entry = replace(entry, 'QgsLocalLedger.allowDeadlinePrefix(()->context.clock().elapsedSeconds()>=seconds);',
        'QgsLocalLedger.allowDeadlinePrefix(()->context.clock().elapsedSeconds()>=seconds || context.budget().remaining()==0);')
    entry = replace(entry, '        if(failure!=null) {',
        '        lines(out.resolve("center-tasks.json"),Collections.singletonList(CenterTaskState.diagnostics()));\n'
        '        lines(out.resolve("center-task-audit.jsonl"),CenterTaskAudit.records());\n'
        '        if(failure!=null) {')
    entry = replace(entry, '"searchConfiguration",search.configuration,"stopReason",context.stopReason(),',
        '"searchConfiguration",search.configuration,"centerTaskMode",System.getProperty("research.centerTasks.mode","OFF"),"stopReason",context.stopReason(),')
    entry = replace(entry, '    private static Map<String,Object> genome(PermutationSolution<?> s) {',
        '    private static long[] taskCheckpoints(long limit) {\n'
        '        java.util.SortedSet<Long> values=new java.util.TreeSet<>();\n'
        '        for(long fe:new long[]{1,2,100,5100,6700,11700,13300,13301}) if(fe<=limit) values.add(fe);\n'
        '        values.add(limit);long[] result=new long[values.size()];int i=0;for(long fe:values)result[i++]=fe;return result;\n'
        '    }\n\n    private static Map<String,Object> genome(PermutationSolution<?> s) {')
    texts['CenterTaskRun'] = entry
    for name, body in texts.items(): (source / f'{name}.java').write_text(body, encoding='utf-8')
    for path in (ROOT / 'src/algorithms/diagnostics/center_tasks').glob('*.java'): shutil.copy2(path, source)
    for name in ('center_task_build.py', 'center_task_design.py', 'center_task_execution.py', 'center_task_checks.py',
                 'center_task_analysis.py', 'run_center_task_pilot.py'):
        shutil.copy2(Path(__file__).with_name(name), source)
    execute(['javac', '-encoding', 'UTF-8', '--release', '8', '-cp', base, '-d', str(classes),
             *map(str, source.glob('*.java'))], root / 'compile.log')
    cp = f'{classes};{base}'; (root / 'classpath.txt').write_text(cp, encoding='utf-8')
    write_once(root / 'class-hashes.json', class_hashes(classes))
    write_once(root / 'source-hashes.json', {str(p.relative_to(source)): digest(p) for p in source.glob('*') if p.is_file()})
    execute(['java', '-cp', cp, 'research.dynamic.ClassResolutionProbe', *(PREFIX + n for n in NAMES),
             PREFIX + 'CenterTaskState'], root / 'loaded-identity.json')
    return cp
