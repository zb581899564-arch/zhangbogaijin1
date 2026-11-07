"""Capture real QGS action2 cohorts and reuse actual kernels with paired per-parent construction noise."""
from pathlib import Path
import shutil

from paired_survival_bench import class_hashes
from pool_phase_build import OBS
from run_long_budget_bridge import ROOT,execute,write_once
from run_paired_qgs_guidance import replace


def build(root,operator_block=16,extra_sources=()):
    src,classes=root/"source",root/"classes";src.mkdir();classes.mkdir()
    cp=(OBS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
    body=(OBS/"source/CanonicalHmopso.java").read_text(encoding="utf-8")
    body=replace(body,"            SharedSurvivalTrace.generationStarted();",
                 "            SharedSurvivalTrace.generationStarted();\n            TeacherCohortCapture.generationStarted();")
    body=replace(body,"            List<Particle> next = global(current, direction, leader);",
                 "            TeacherCohortCapture.begin(direction, step, action, current, state.archive());\n            List<Particle> next = global(current, direction, leader);")
    body=replace(body,"            SharedSurvivalTrace.generated(child, particle.current, composed);",
                 "            TeacherCohortCapture.proposal(particle.current, personal, leader, composed);\n            SharedSurvivalTrace.generated(child, particle.current, composed);")
    (src/"CanonicalHmopso.java").write_text(body,encoding="utf-8")
    entry=(OBS/"source/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry=replace(entry,"        Observations obs = new Observations(audit, limit, checkpoints);",
                  "        org.uma.jmetal.util.research.search.TeacherCohortCapture.configure(context::result);\n        Observations obs = new Observations(audit, limit, checkpoints);")
    entry=replace(entry,"            if (digest != null) digest.update(paid, s);",
                  "            org.uma.jmetal.util.research.search.TeacherCohortCapture.paid(paid);\n            if (digest != null) digest.update(paid, s);")
    entry=replace(entry,"        obs.write(out);","        obs.write(out);\n        append(out.resolve(\"teacher-cohorts.jsonl\"), org.uma.jmetal.util.research.search.TeacherCohortCapture.finish());")
    (src/"PddrIsolationRun.java").write_text(entry,encoding="utf-8")
    probe=(ROOT/"src/java/dynamicentries/KernelProbeRun.java").read_text(encoding="utf-8")
    probe=replace(probe,"long seed = baseSeed + caseIndex * 100L + rep;",f"long seed = mixed(baseSeed + (caseIndex / {operator_block}) * 1009L + rep);")
    probe=replace(probe,"    private static final class Probe implements Algorithm<Object> {","""    private static long mixed(long value) {
        value = (value ^ (value >>> 30)) * 0xbf58476d1ce4e5b9L;
        value = (value ^ (value >>> 27)) * 0x94d049bb133111ebL;
        return value ^ (value >>> 31);
    }
    private static final class Probe implements Algorithm<Object> {""")
    (src/"KernelProbeRun.java").write_text(probe,encoding="utf-8")
    shutil.copy2(ROOT/"src/algorithms/diagnostics/TeacherCohortCapture.java",src)
    for name in ("teacher_cohort_build.py","run_teacher_coupling_probe.py","teacher_coupling_analysis.py",*extra_sources):
        shutil.copy2(Path(__file__).with_name(name),src)
    execute(["javac","-encoding","UTF-8","--release","8","-cp",cp,"-d",str(classes),*map(str,src.glob("*.java"))],root/"compile.log")
    write_once(root/"class-hashes.json",class_hashes(classes));cp=f"{classes};{cp}"
    (root/"classpath.txt").write_text(cp,encoding="utf-8");return cp
