"""Read-only phase hooks around the frozen source and unchanged factory selection policies."""
from pathlib import Path
import shutil

from paired_survival_bench import FROZEN,class_hashes
from run_long_budget_bridge import ROOT,execute,write_once
from run_paired_qgs_guidance import replace

OBS=ROOT/"runs/shared-survival-observation-20261105-004523-286623"


def canonical_source():
    body=(OBS/"source/CanonicalHmopso.java").read_text(encoding="utf-8")
    hook="org.uma.jmetal.util.research.cooperation.PoolPhaseAudit"
    body=replace(body,"            Map<Direction, List<Particle>> groups = decompose(population);",
                 f"            Map<Direction, List<Particle>> groups = decompose(population);\n            {hook}.groups(solutions(groups.get(Direction.CENTER)));")
    body=replace(body,"            List<Particle> globallyUpdated = flatten(updated);",
                 f"            List<Particle> globallyUpdated = flatten(updated);\n            {hook}.globalEnd(support, solutions(updated.get(Direction.CENTER)));")
    old="""                for (Direction direction : Direction.values()) for (Particle particle : updated.get(direction)) {
                    state.observationGroup(direction);
                    Direction preference = preference(direction);"""
    body=replace(body,old,"""                for (Direction direction : Direction.values()) {
                    for (Particle particle : updated.get(direction)) {
                    state.observationGroup(direction);
                    Direction preference = preference(direction);""")
    body=replace(body,"""                    offspring.add(local.improve(particle, preference, reference));
                }
            }""",f"""                    offspring.add(local.improve(particle, preference, reference));
                    }}
                    {hook}.localEnd(support, direction);
                }}
            }}""")
    return replace(body,"    private List<Particle> qgs(List<Particle> group, Direction direction) {",
                   f"    private List<Particle> qgs(List<Particle> group, Direction direction) {{\n        {hook}.centerEntry(support, direction);")


def cooperation_source():
    body=(FROZEN/"source/src/algorithms/cooperation/CooperationSupport.java").read_text(encoding="utf-8")
    body=replace(body,"if (timing == null && nightSuccessful == null) return new FactoryRecord(schedule, factory);",
                 "if (timing == null && nightSuccessful == null) return new FactoryRecord(schedule, factory, PoolPhaseAudit.paidFE(), generation, stage, direction == null ? \"INITIALIZATION\" : direction.name());")
    return replace(body,"    public Map<String, Object> diagnostics() {",
                   "    public Map<String, Object> phasePoolSnapshot() { return PoolPhaseAudit.pool(pools, contexts, energyScale, wageScale); }\n"
                   "    public Map<String, Object> diagnostics() {")


def build(root):
    src,classes=root/"source",root/"classes";src.mkdir();classes.mkdir()
    cp=(OBS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
    for name,body in (("CanonicalHmopso",canonical_source()),("CooperationSupport",cooperation_source())):
        (src/f"{name}.java").write_text(body,encoding="utf-8")
    entry=(OBS/"source/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry=replace(entry,"        Observations obs = new Observations(audit, limit, checkpoints);",
                  "        org.uma.jmetal.util.research.cooperation.PoolPhaseAudit.configure(context::result);\n        Observations obs = new Observations(audit, limit, checkpoints);")
    entry=replace(entry,"            if (digest != null) digest.update(paid, s);",
                  "            org.uma.jmetal.util.research.cooperation.PoolPhaseAudit.paid(paid);\n            if (digest != null) digest.update(paid, s);")
    entry=replace(entry,"        obs.write(out);","        obs.write(out);\n        append(out.resolve(\"pool-phases.jsonl\"), org.uma.jmetal.util.research.cooperation.PoolPhaseAudit.finish());")
    (src/"PddrIsolationRun.java").write_text(entry,encoding="utf-8")
    for name in ("PoolPhaseAudit","PoolAssemblyCheckRun"):
        shutil.copy2(ROOT/f"src/algorithms/diagnostics/{name}.java",src)
    for name in ("pool_phase_build.py","run_pool_phase_audit.py","pool_phase_analysis.py","paired_survival_bench.py"):
        shutil.copy2(Path(__file__).with_name(name),src)
    execute(["javac","-encoding","UTF-8","--release","8","-cp",cp,"-d",str(classes),*map(str,src.glob("*.java"))],root/"compile.log")
    write_once(root/"class-hashes.json",class_hashes(classes));cp=f"{classes};{cp}"
    (root/"classpath.txt").write_text(cp,encoding="utf-8");return cp
