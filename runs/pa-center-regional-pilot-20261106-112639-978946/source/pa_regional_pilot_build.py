"""Reuse accepted policy bytes and build explicit, separately named ordinary MOEA/D adapters."""
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT,read,write_once,execute
from research.semantic_repair.evidence import digest
from paired_survival_bench import class_hashes
from frozen_classpath_identity import resolve_class
from ctx_gom_build import once


def moead_adapters(source,plan):
    deep,original=[Path(plan[k]) for k in ('moeadDeepSource','moeadOriginalSource')]
    a,b=deep.read_text('utf-8'),original.read_text('utf-8')
    start,end='    private void runMoead()','    private List<Integer> matingPool('
    assert a[a.index(start):a.index(end)]==b[b.index(start):b.index(end)]
    a=a.replace('ClassicAlgorithm','OrdinaryMoeadAlgorithm')
    a=once(a,'if (!"NSGA2_4V".equals(config.mode)) throw new IllegalStateException("Deep NSGA-II control only");',
        'if (!"MOEAD_4V".equals(config.mode)) throw new IllegalStateException("Ordinary MOEA/D entry only");')
    b=b.replace('ClassicAlgorithm','MoeadReferenceAlgorithm')
    b=once(b,'        started = true;','        started = true;\n        if (!"MOEAD_4V".equals(config.mode)) throw new IllegalStateException("Reference MOEA/D only");')
    old='''        for (int i = 0; i < ClassicConfig.POPULATION; i++) {
            checkpoint.run(); population.add(evaluate(problem.createSolution(), "initialization"));
        }'''
    new='''        org.uma.jmetal.util.research.search.PaInitialBridge initial = new org.uma.jmetal.util.research.search.PaInitialBridge(instance);
        for (int i = 0; i < ClassicConfig.POPULATION; i++) {
            checkpoint.run(); PermutationSolution<Integer> point = problem.createSolution(); initial.prepare(point, i);
            population.add(evaluate(point, "initialization"));
        }'''
    b=once(b,old,new)
    (source/'OrdinaryMoeadAlgorithm.java').write_text(a,encoding='utf-8');(source/'MoeadReferenceAlgorithm.java').write_text(b,encoding='utf-8')
    return dict(deepSource=str(deep),deepSourceSHA256=digest(deep),originalSource=str(original),originalSourceSHA256=digest(original),
        moeadLoopExactAcrossSources=True,ordinaryChanges=['Separate class name','Guard MOEAD only; canonical initial helper already present'],
        referenceChanges=['Separate class name','Guard MOEAD only','Canonical100 initialization through independent PaInitialBridge'],
        existingClassicAlgorithmOverridden=False,localSearchInvoked=False)


def build(root,plan):
    engine=Path(plan['engineeringRoot']);assert read(engine/'independent-final-audit.json')['passed']
    assert digest(engine/'independent-final-audit.json')==plan['engineeringAuditSHA256']
    hashes=read(engine/'class-hashes.json');assert class_hashes(engine/'classes')==hashes['policy'] and class_hashes(engine/'math-classes')==hashes['math']
    kernel=root/'kernel-classes';shutil.copytree(engine/'classes',kernel);shutil.copytree(engine/'math-classes',kernel,dirs_exist_ok=True)
    shutil.copytree(engine/'source',root/'accepted-kernel-source')
    source,classes=root/'source',root/'classes';source.mkdir();classes.mkdir()
    for name in ('PaRegionalCapabilityRun.java','PlainMoeadSearch.java','PlainMoeadRun.java'):
        shutil.copy2(ROOT/'src/algorithms/diagnostics/pa_regional'/name,source)
    for name in ('pa_regional_pilot_build.py','pa_regional_pilot_support.py','run_pa_center_regional_pilot.py','pa_regional_pilot_analysis.py'):
        shutil.copy2(Path(__file__).with_name(name),source)
    adaptation=moead_adapters(source,plan);write_once(root/'moead-source-adaptation.json',adaptation)
    base=(Path(plan['base'])/'classpath.txt').read_text('utf-8-sig').strip();cp=str(kernel)+';'+base
    execute(['java','-version'],root/'jdk-version.log')
    execute(['javac','-encoding','UTF-8','--release','8','-cp',cp,'-d',str(classes),*map(str,source.glob('*.java'))],root/'compile.log')
    cp=str(classes)+';'+cp;(root/'classpath.txt').write_text(cp,encoding='utf-8')
    write_once(root/'source-hashes.json',{p.name:digest(p) for p in source.iterdir()})
    write_once(root/'class-hashes.json',dict(wrapper=class_hashes(classes),kernel=class_hashes(kernel)))
    inherited={}
    for suffix in ('classic.ClassicAlgorithm','classic.ClassicConfig','classic.MoeadDecomposition','classic.ClassicVariation',
        'search.DeepLocalVisits','search.CanonicalHmopso','model.DynamicDecoder','modelglobal.PaPaidEvaluation','search.PaInitialBridge'):
        name='org.uma.jmetal.util.research.'+suffix;value=resolve_class(cp,name);assert value==resolve_class(base,name);inherited[name]=value
    write_once(root/'inherited-identities.json',inherited);return cp,base
