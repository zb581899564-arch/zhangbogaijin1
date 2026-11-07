"""Build read-only observers over exact frozen sources; original classes remain the control."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
from common import *

TRACE = 'org.uma.jmetal.util.research.search.TrajectoryTrace'


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Patch anchor not unique: ' + old[:90])
    return text.replace(old, new, 1)


def insert(text, anchor, extra):
    return once(text, anchor, anchor + '\n' + extra)


def patch_entry(text):
    text=insert(text,'PaLightEvidence evidence=new PaLightEvidence(limit,seconds); GomCapabilitySearch search=new GomCapabilitySearch(arm,run,in,fatigue,decoder);',
                '        TrajectoryTrace trajectory=new TrajectoryTrace(run,out,arm);')
    text=insert(text,'search.observed((PermutationSolution<Integer>)value,fe); evidence.completedSolution(value,fe,t,changed,archive);',
                '                trajectory.paid((PermutationSolution<Integer>)value,fe,changed);')
    text=insert(text,'finally { SnapshotCopyMetrics.searchEnded(); decoder.clearPrepared(); }',
                '        PaLightEvidence.writeRows(out.resolve("trajectory-receipt.jsonl"),Collections.singletonList(trajectory.finish()));')
    return text


def patch_swarm(text):
    for anchor, extra in [
        ('        if (audit != null) audit.feedbackInitialized();','        TrajectoryTrace.population("INITIAL",solutions(population));'),
        ('            renewContexts(population);','            TrajectoryTrace.population("PRE_GLOBAL",solutions(population));'),
        ('            List<Particle> globallyUpdated = flatten(updated);','            TrajectoryTrace.population("POST_GLOBAL",solutions(globallyUpdated));'),
        ('            if (chapter == 3) offspring.addAll(population);','            TrajectoryTrace.population("POST_LOCAL",solutions(offspring));'),
        ('                population = selected.survivors();','                TrajectoryTrace.population("SURVIVORS",solutions(population));')]:
        text=insert(text,anchor,extra)
    text=once(text,'            state.evaluate(child, "global", direction);',
        '            TrajectoryTrace.proposal(composed?"SHARED":"QGS",preference,-1,-1,particle.current,personal,leader);\n'
        '            state.evaluate(child, "global", direction);')
    return once(text,'        return GlobalGroupPolicy.select(group, result, preference);',
        '        List<Particle> selected=GlobalGroupPolicy.select(group,result,preference);\n'
        '        TrajectoryTrace.population("QGS_BATCH_SELECTED",solutions(selected));\n        return selected;')


def patch_local(text):
    text=once(text,'            evaluator.evaluate(child, "jointLocal", preference);',
        '            TrajectoryTrace.proposal("GOM_LOCAL",preference,slot,family,parent.point,donor.point,null);\n'
        '            evaluator.evaluate(child, "jointLocal", preference);')
    text=insert(text,'            if (keep) w.values.set(slot, state);','            TrajectoryTrace.accepted(keep);')
    return once(text,'        w.programs++; scope.completedPrograms++;',
        '        TrajectoryTrace.program(w.values.get(slot).point,slot,preference);\n        w.programs++; scope.completedPrograms++;')


def patch_classic(text):
    text=once(text,'            if (mechanism != null) mechanism.begin(population);',
        '            '+TRACE+'.population("PRE_GLOBAL",population);\n            if (mechanism != null) mechanism.begin(population);')
    text=insert(text,'\n            population = next.population; scores = next.scores;',
        '            '+TRACE+'.population("POST_GLOBAL",population);')
    text=insert(text,'                List<PermutationSolution<Integer>> local = deep.improve(population);',
        '                '+TRACE+'.population("POST_LOCAL",local);')
    text=insert(text,'                population = next.population; scores = next.scores;',
        '                '+TRACE+'.population("SURVIVORS",population);')
    return once(text,'        child = evaluate(child, "global");',
        '        '+TRACE+'.proposal("NSGA_VARIATION",null,-1,-1,a,b,null);\n        child = evaluate(child, "global");')


def patch_pa(text):
    text=insert(text,'            List<int[]> subsets = learn(); phase = "MIXING";',
        '            PaTrajectoryBridge.population("PA_MODEL",population());')
    text=once(text,'                    PaIndividual child = evaluation.candidate(move.genome, parent);',
        '                    PaTrajectoryBridge.proposal(generation,i,parent,donor);\n'
        '                    PaIndividual child = evaluation.candidate(move.genome, parent);')
    text=insert(text,'                    if (accepted) population.set(i, child);',
        '                    '+TRACE+'.accepted(accepted);')
    text=insert(text,'                completedPrograms++; observer.programEnd(generation, i, population.get(i));',
        '                PaTrajectoryBridge.program(i,population.get(i));')
    return insert(text,'            completedGenerations++; phase = "GENERATION_COMPLETE"; observer.generationEnd(generation, population());',
        '            PaTrajectoryBridge.population("SURVIVORS",population());')


def main(root):
    linux()
    update=root/'update-01'; output=root/'build-01'; output.mkdir()
    source=output/'source';source.mkdir()
    originals={'GomCapabilityRun':ANCHOR/'anchor/source/GomCapabilityRun.java',
        'CanonicalHmopso':ANCHOR/'anchor/overrides/CanonicalHmopso.java',
        'GomLocalProgram':ANCHOR/'anchor/source/GomLocalProgram.java',
        'ClassicAlgorithm':root/'payload/extra-source/ClassicAlgorithm.java',
        'PaPopulation':update/'frozen/PaPopulation.java'}
    transforms=dict(zip(originals,[patch_entry,patch_swarm,patch_local,patch_classic,patch_pa]))
    identities=[]
    for name,path in originals.items():
        target=source/(name+'.java');target.write_text(transforms[name](path.read_text('utf-8-sig')),encoding='utf-8')
        identities.append(dict(name=name,source=str(path),originalSHA256=sha(path),overrideSHA256=sha(target)))
    for p in (update/'java').glob('*.java'):shutil.copy2(p,source/p.name)
    cp=os.pathsep.join(str(ANCHOR/p['relative']) for p in read(ANCHOR/'classpath-providers.json'))
    (output/'base-classpath.txt').write_text(cp,encoding='utf-8')
    classes=output/'classes';classes.mkdir()
    command=[str(BASE/'runtime/jdk17/bin/javac'),'-encoding','UTF-8','--release','8','-cp',cp,'-d',str(classes),*map(str,source.glob('*.java'))]
    result=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (output/'compile.log').write_text(result.stdout,encoding='utf-8')
    write(output/'source-identity.json',identities)
    if result.returncode:raise RuntimeError(result.stdout)
    # Baseline gets only the observing entry and trace utility; search classes resolve frozen originals.
    baseline=output/'baseline-entry';baseline.mkdir()
    for p in classes.rglob('*.class'):
        if p.stem.startswith('GomCapabilityRun') or p.stem.startswith('TrajectoryTrace'):
            target=baseline/p.relative_to(classes);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    write(output/'class-identity.json',{p.relative_to(output).as_posix():sha(p) for p in output.rglob('*.class')})
    (output/'classpath.txt').write_text(str(classes)+os.pathsep+cp,encoding='utf-8')
    (output/'baseline-classpath.txt').write_text(str(baseline)+os.pathsep+cp,encoding='utf-8')
    print('BUILD_DONE',len(identities))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);main(p.parse_args().root.resolve())
