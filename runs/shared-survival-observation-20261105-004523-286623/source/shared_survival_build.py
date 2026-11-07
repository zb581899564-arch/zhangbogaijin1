"""Shadow frozen sources with observation-only hooks and an unconditional paid-sequence digest."""
from pathlib import Path
import shutil

from paired_survival_bench import class_hashes
from run_long_budget_bridge import ROOT,execute,write_once
from run_paired_qgs_guidance import replace

BASIS=ROOT/"runs/group-survival-gate-20261104-234602-311536"


def canonical_source():
    body=(BASIS/"source/CanonicalHmopso.java").read_text(encoding="utf-8")
    body=replace(body,"            if (support != null) support.beginGeneration();",
                 "            if (support != null) support.beginGeneration();\n            SharedSurvivalTrace.generationStarted();")
    body=replace(body,'            state.evaluate(child, "global", direction);',
                 '            SharedSurvivalTrace.generated(child, particle.current, composed);\n            state.evaluate(child, "global", direction);')
    body=replace(body,"                    offspring.add(local.improve(particle, preference, reference));",
                 "                    SharedSurvivalTrace.localEntry(particle, direction);\n                    offspring.add(local.improve(particle, preference, reference));")
    return replace(body,"            if (mechanism != null) mechanism.end(offspring, population, support);",
                   "            if (mechanism != null) mechanism.end(offspring, population, support);\n"
                   "            SharedSurvivalTrace.generationEnd(solutions(population));")


def selection_source():
    body=(BASIS/"source/GlobalGroupPolicy.java").read_text(encoding="utf-8")
    body=replace(body,'        if (MODE.equals("PAIR")) return GlobalBatchPolicy.select(parents,children,role);',
                 '        if (MODE.equals("PAIR")) {\n'
                 '            List<Particle> out = GlobalBatchPolicy.select(parents,children,role);\n'
                 '            SharedSurvivalTrace.selected(parents,children,out,role); return out;\n        }')
    return replace(body,'        return out;\n    }\n    public static Map<String,Object> diagnostics()',
                   '        SharedSurvivalTrace.selected(parents,children,out,role);\n'
                   '        return out;\n    }\n    public static Map<String,Object> diagnostics()')


def entry_source():
    body=(BASIS/"source/PddrIsolationRun.java").read_text(encoding="utf-8")
    body=replace(body,'        Observations obs = new Observations(audit, limit, checkpoints);',
                 '        org.uma.jmetal.util.research.search.SharedSurvivalTrace.initialize(limit);\n'
                 '        Observations obs = new Observations(audit, limit, checkpoints);')
    body=replace(body,'digest = audit ? new PddrPaidDigest() : null;','digest = new PddrPaidDigest();')
    body=replace(body,'"paidSHA256", audit ? obs.digest.finish() : null);','"paidSHA256", obs.digest.finish());')
    body=replace(body,'            if (digest != null) digest.update(paid, s);',
                 '            org.uma.jmetal.util.research.search.SharedSurvivalTrace.paid(s, paid, changed);\n'
                 '            if (digest != null) digest.update(paid, s);')
    return replace(body,'        obs.write(out);','        obs.write(out);\n'
                   '        append(out.resolve("loaded-classes.jsonl"), org.uma.jmetal.util.research.search.RuntimeClassIdentity.capture());\n'
                   '        append(out.resolve("shared-survival.jsonl"), org.uma.jmetal.util.research.search.SharedSurvivalTrace.finish(out, context.result()));')


def build(root):
    src,classes=root/"source",root/"classes";src.mkdir();classes.mkdir()
    cp=(BASIS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
    for name,body in (("CanonicalHmopso",canonical_source()),("GlobalGroupPolicy",selection_source()),("PddrIsolationRun",entry_source())):
        (src/f"{name}.java").write_text(body,encoding="utf-8")
    state=(ROOT/"runs/batch-survival-study-20261104-222516-378030/source/SearchState.java").read_text(encoding="utf-8")
    state=replace(state,"        problem.evaluate(candidate);","        SharedSurvivalTrace.before(candidate, stage);\n        problem.evaluate(candidate);")
    (src/"SearchState.java").write_text(state,encoding="utf-8")
    for name in ("SharedAncestry","SharedSurvivalTrace","SharedSurvivalChecks","RuntimeClassIdentity"):
        shutil.copy2(ROOT/f"src/algorithms/diagnostics/{name}.java",src)
    for name in ("shared_survival_build.py","run_shared_survival_observation.py","analyze_shared_survival_observation.py","paired_survival_bench.py"):
        shutil.copy2(Path(__file__).with_name(name),src)
    execute(["javac","-encoding","UTF-8","--release","8","-cp",cp,"-d",str(classes),*map(str,src.glob("*.java"))],root/"compile.log")
    execute(["java","-version"],root/"jdk-version.log")
    write_once(root/"class-hashes.json",class_hashes(classes));cp=f"{classes};{cp}"
    (root/"classpath.txt").write_text(cp,encoding="utf-8");return cp
