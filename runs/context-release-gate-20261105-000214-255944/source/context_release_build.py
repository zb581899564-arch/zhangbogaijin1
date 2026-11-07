"""Build an isolated shadow of frozen cooperation classes; never modify the default sources."""
from pathlib import Path
import shutil

from paired_survival_bench import FROZEN, class_hashes
from run_long_budget_bridge import ROOT, execute, write_once
from run_paired_qgs_guidance import replace

BASIS = ROOT / "runs/batch-survival-study-20261104-222516-378030"


def family_source():
    body = (FROZEN / "source/src/algorithms/cooperation/FamilyContexts.java").read_text(encoding="utf-8")
    old = "int family = family(s); if (family < 0) return;"
    assert body.count(old) == 2
    body = body.replace(old, "ContextRelease.normalize(s); " + old)
    body = replace(body, "        for (int f = -1; f < 4; f++) {",
                   "        for (PermutationSolution<Integer> s : pop) ContextRelease.normalize(s);\n"
                   "        int protectedCount = ContextRelease.protectedCount();\n"
                   "        for (int f = -1; f < 4; f++) {")
    body = replace(body, '            if (ids.size() != (f < 0 ? 80 : 5)) throw new IllegalStateException("Family population lost");',
                   '            int expected = f < 0 ? 100 - 5 * protectedCount : ContextRelease.released(f) ? 0 : 5;\n'
                   '            if (ids.size() != expected) throw new IllegalStateException("Family population lost");\n'
                   '            if (ids.isEmpty()) continue;')
    return replace(body, "int count = f < 0 ? 11 : 1;", "int count = f < 0 ? 15 - protectedCount : 1;")


def cooperation_source():
    body = (FROZEN / "source/src/algorithms/cooperation/CooperationSupport.java").read_text(encoding="utf-8")
    body = replace(body, "        int family = FamilyContexts.family(s);",
                   "        int family = ContextRelease.poolFamily(s, contexts, false);")
    body = replace(body, "        int family = FamilyContexts.family(parent);",
                   "        if (!ContextRelease.compositionEnabled()) return null;\n"
                   "        int family = ContextRelease.poolFamily(parent, contexts, true);")
    body = replace(body, "return new int[] {80, 5, 5, 5, 5};", "return ContextRelease.quotas();")
    body = replace(body, "return FamilyContexts.family(solution) + 1;", "return ContextRelease.category(solution);")
    method = """
    /** Read-only optimistic bound of the retained finite pool; no new evaluations. */
    public double[][] retainedPoolLowerBounds() {
        double[][] out = new double[4][];
        for (int family = 0; family < 4; family++) {
            java.util.List<java.util.List<double[]>> components = new java.util.ArrayList<>();
            for (FactoryPool pool : pools[family]) {
                java.util.List<double[]> objectives = new java.util.ArrayList<>();
                for (FactoryRecord record : pool.records()) objectives.add(record.objectives.clone());
                components.add(objectives);
            }
            out[family] = ContextRelease.lowerBound(components);
        }
        return out;
    }
"""
    return replace(body, "    public Map<String, Object> diagnostics() {", method + "    public Map<String, Object> diagnostics() {")


def build(root):
    src, classes = root / "source", root / "classes"; src.mkdir(); classes.mkdir()
    cp = (BASIS / "classpath.txt").read_text(encoding="utf-8-sig").strip()
    body = (BASIS / "source/CanonicalHmopso.java").read_text(encoding="utf-8")
    body = replace(body, "            List<Particle> globallyUpdated = flatten(updated);",
                   "            List<Particle> globallyUpdated = flatten(updated);\n"
                   "            org.uma.jmetal.util.research.cooperation.ContextRelease.afterGlobal(support, solutions(globallyUpdated));")
    (src / "CanonicalHmopso.java").write_text(body, encoding="utf-8")
    (src / "FamilyContexts.java").write_text(family_source(), encoding="utf-8")
    (src / "CooperationSupport.java").write_text(cooperation_source(), encoding="utf-8")
    entry = (BASIS / "source/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry = replace(entry, "        Observations obs = new Observations(audit, limit, checkpoints);",
                    "        org.uma.jmetal.util.research.cooperation.ContextRelease.configure(context::result, context.budget()::successful, seed);\n"
                    "        Observations obs = new Observations(audit, limit, checkpoints);")
    entry = replace(entry, "        obs.write(out);", "        obs.write(out);\n"
                    "        append(out.resolve(\"release.jsonl\"), org.uma.jmetal.util.research.cooperation.ContextRelease.diagnostics());\n"
                    "        if (search.cooperation != null) append(out.resolve(\"cooperation.jsonl\"), search.cooperation.diagnostics());")
    (src / "PddrIsolationRun.java").write_text(entry, encoding="utf-8")
    for name in ("ContextRelease", "ContextReleaseChecks"):
        shutil.copy2(ROOT / f"src/algorithms/diagnostics/{name}.java", src)
    for name in ("context_release_build.py", "run_context_release_gate.py", "paired_survival_bench.py"):
        shutil.copy2(Path(__file__).with_name(name), src)
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", cp, "-d", str(classes),
             *map(str, src.glob("*.java"))], root / "compile.log")
    write_once(root / "class-hashes.json", class_hashes(classes))
    cp = f"{classes};{cp}"; (root / "classpath.txt").write_text(cp, encoding="utf-8")
    return cp
