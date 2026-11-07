"""Build only shadow classes for the isolated reverse-ledger experiment."""
import difflib
from hashlib import sha256
from pathlib import Path
import shutil

from run_dynamic_deep_roles import ANCHOR, FROZEN, ROOT
from run_long_budget_bridge import execute, write_once
from run_paired_qgs_guidance import replace


ROLE_SOURCE = ROOT / "runs/dynamic-deep-roles-20261103-212007-121034/source"
FROZEN_SOURCE = FROZEN / "source/src"
DEEP_SOURCE = ANCHOR / "source"
AUDIT = "org.uma.jmetal.util.research.search.ReverseAudit"
POOL = "org.uma.jmetal.util.research.cooperation.ReversePoolSnapshots"


def entry(source):
    source = replace(source, '&& !mode.equals("SHARE_JOB_ALIGNED_UNIFORM")))',
                     '&& !mode.equals("SHARE_JOB_ALIGNED_UNIFORM") && !mode.equals("NSGA2_4V")))')
    source = replace(source, "        AnytimeRecorder recorder =", f"""        ReverseClassOrigins.write(out);
        {AUDIT} evidence = {AUDIT}.run();
        AnytimeRecorder recorder =""")
    source = replace(source, "                if (changed)\n", """
                evidence.paid((PermutationSolution<?>) s, paid, changed, archive);
                if (changed)
""".lstrip("\n"))
    source = replace(source, "        try { context.run(search.algorithm); }", f"""        try {{ context.run(search.algorithm); }}
        catch (RuntimeException | Error e) {{
            append(out.resolve("failures.jsonl"), {AUDIT}.row(
                    "reason", e.toString(), "attempted", context.budget().attempted(),
                    "successful", context.budget().successful(), "failed", context.budget().failed(),
                    "lastValidFront", evidence.archive(), "log", "run.log"));
            throw e;
        }}""")
    source = replace(source, '        if (!"plain".equals(options.get(0)))',
                     f'''        evidence.finish(out);
        {POOL}.finish(out);
        append(out.resolve("search-end.jsonl"), {AUDIT}.row(
                "attempted", context.budget().attempted(), "successful", context.budget().successful(),
                "failed", context.budget().failed(), "stopReason", context.stopReason(), "lastValidFront", evidence.archive()));
        if (!"plain".equals(options.get(0)))''')
    return replace(source, '        receipt.put("cooperation", search.cooperation.diagnostics());',
                   '        if (search.cooperation != null) receipt.put("cooperation", search.cooperation.diagnostics());')


def swarm(source):
    source = replace(source, "            if (support != null) support.beginGeneration();",
                     "            ReverseAudit.run().begin();\n            if (support != null) support.beginGeneration();")
    source = replace(source, "            for (Direction direction : globalUpdateOrder()) {",
                     f"""            for (Direction direction : globalUpdateOrder()) {{
                if (direction == Direction.CENTER && support != null)
                    {POOL}.enter(ReverseAudit.run().generation());""")
    source = replace(source, "            List<PermutationSolution<Integer>> reference = solutions(globallyUpdated);",
                     """            List<PermutationSolution<Integer>> reference = solutions(globallyUpdated);
            ReverseAudit.run().phase("global-end", updated.get(Direction.CENTER), reference);""")
    a = """                for (Direction direction : Direction.values()) for (Particle particle : updated.get(direction)) {
                    state.observationGroup(direction);
                    Direction preference = preference(direction);
                    state.count("local.g" + direction.id() + ".preference." + preference.name());
                    guarded.checkpoint();
                    offspring.add(local.improve(particle, preference, reference));
                }"""
    b = """                for (Direction direction : Direction.values()) {
                    if (direction == Direction.CENTER)
                        ReverseAudit.run().phase("center-entry", updated.get(Direction.CENTER), reference);
                    for (Particle particle : updated.get(direction)) {
                        state.observationGroup(direction);
                        Direction preference = preference(direction);
                        state.count("local.g" + direction.id() + ".preference." + preference.name());
                        guarded.checkpoint();
                        offspring.add(local.improve(particle, preference, reference));
                    }
                    if (direction == Direction.MAKESPAN)
                        ReverseAudit.run().phase("makespan-local-end", updated.get(Direction.CENTER), reference);
                }"""
    source = replace(source, a, b)
    return replace(source, "                population = selected.survivors();",
                   """                ReverseAudit.run().selection(candidates, selected, globalSnapshots.size());
                population = selected.survivors();""")


def local(source):
    source = replace(source, "                int factory = SeededRandom.current().nextInt(instance.factories());",
                     "                state.checkLocalSlot();\n                int factory = SeededRandom.current().nextInt(instance.factories());")
    assert source.count("direction.better(") == 3
    return source.replace("direction.better(", "ReverseAudit.run().better(direction, ")


def state(source):
    return replace(source, "    int ledgerGroup(Direction preference) {",
                   """    void checkLocalSlot() {
        ((org.uma.jmetal.util.research.runtime.BudgetedProblem<?>) problem).checkpoint();
    }
    int ledgerGroup(Direction preference) {""")


def direction(source):
    return replace(source, "        return score[score.length - 1] < score[score.length - 2];",
                   """        ReverseAudit.run().pddr(candidate, score[score.length - 1], score[score.length - 2]);
        return score[score.length - 1] < score[score.length - 2];""")


def particle(source):
    return replace(source, "        return ParetoTools.copy(history.get(ParetoTools.order(history, direction).get(0)));",
                   """        PermutationSolution<Integer> best = history.get(ParetoTools.order(history, direction).get(0));
        ReverseAudit.run().pbest(direction, best, history.size());
        return ParetoTools.copy(best);""")


def cooperation(source):
    source = replace(source, "        if (timing == null && nightSuccessful == null) return new FactoryRecord(schedule, factory);",
                     f"""        if (timing == null && nightSuccessful == null)
            return new FactoryRecord(schedule, factory, {AUDIT}.run().fe(), generation, stage,
                    direction == null ? "INITIALIZATION" : direction.name());""")
    return replace(source, "        if (evidence == null) return;",
                   """        ReversePoolSnapshots.capture(pools[family], parent,
                (DynamicSchedule) parent.getAttribute(DynamicEvaluation.KEY),
                family, cycle, cap, eta, energyScale, wageScale, outcome);
        if (evidence == null) return;""")


def build(root):
    source, classes = root / "source", root / "classes"
    source.mkdir()
    classes.mkdir()
    base = (ROLE_SOURCE.parent / "classpath.txt").read_text(encoding="utf-8-sig").strip()
    paths = [Path(p) for p in base.split(";")]
    assert all(p.exists() for p in paths)
    write_once(root / "dependencies.json", [
        {"path": str(p), "kind": "jar" if p.is_file() else "classes",
         "sha256": sha256(p.read_bytes()).hexdigest() if p.is_file() else None} for p in paths])
    patches = (
        (ROLE_SOURCE / "LongBudgetRun.java", entry),
        (DEEP_SOURCE / "CanonicalHmopso.java", swarm),
        (ROLE_SOURCE / "LocalSearch.java", local),
        (ROLE_SOURCE / "SearchState.java", state),
        (FROZEN_SOURCE / "java/search/Direction.java", direction),
        (FROZEN_SOURCE / "java/search/Particle.java", particle),
        (FROZEN_SOURCE / "algorithms/cooperation/CooperationSupport.java", cooperation),
    )
    files = []
    for original, patch in patches:
        before = original.read_text(encoding="utf-8")
        after = patch(before)
        target = source / original.name
        target.write_text(after, encoding="utf-8")
        (source / (target.stem + ".diff")).write_text("".join(difflib.unified_diff(
            before.splitlines(True), after.splitlines(True), fromfile=str(original), tofile=target.name)), encoding="utf-8")
        files.append(str(target))
    for name in ("ReverseAudit", "ReversePoolSnapshots", "ReverseClassOrigins", "ReverseLedgerChecks"):
        files.append(shutil.copy2(ROOT / f"src/algorithms/diagnostics/{name}.java", source / f"{name}.java"))
    for name in ("run_dynamic_reverse_ledger_audit.py", "reverse_ledger_build.py", "reverse_ledger_analysis.py"):
        shutil.copy2(ROOT / "scripts" / name, source / name)
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", base,
             "-d", str(classes), *files], root / "compile.log")
    cp = f"{classes};{base}"
    (root / "classpath.txt").write_text(cp, encoding="utf-8")
    return cp
