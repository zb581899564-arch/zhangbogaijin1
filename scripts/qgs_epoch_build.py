"""Extract the same QGS single update into isolated scheduling agents, with exact serial control."""
from pathlib import Path
import shutil

from paired_survival_bench import class_hashes
from run_long_budget_bridge import ROOT,execute,write_once
from run_paired_qgs_guidance import replace

BASIS=ROOT/"runs/personal-memory-screen-20261105-014020-602252"
GROUP=ROOT/"runs/group-survival-gate-20261104-234602-311536"


def canonical_source():
    body=(GROUP/"source/CanonicalHmopso.java").read_text(encoding="utf-8")
    start=body.index("            Map<Direction, List<Particle>> updated = new EnumMap<>(Direction.class);")
    end=body.index("            List<Particle> globallyUpdated = flatten(updated);",start)
    body=body[:start]+"""            Map<Direction, List<Particle>> updated;
            if (chapter == 4) updated = QgsEpochSchedule.run(groups, globalUpdateOrder(), config, this::qgsStep);
            else {
                updated = new EnumMap<>(Direction.class);
                for (Direction direction : globalUpdateOrder()) {
                    state.observationGroup(direction);
                    updated.put(direction, global(groups.get(direction), direction, randomLeader()));
                }
            }
"""+body[end:]
    start=body.index("    private List<Particle> qgs(List<Particle> group, Direction direction) {")
    end=body.index("    private Direction[] globalUpdateOrder() {",start)
    body=body[:start]+"""    private void qgsStep(QgsEpochSchedule.Agent agent, Direction direction, int step) {
        state.observationGroup(direction);
        Direction preference = preference(direction);
        List<Particle> current = agent.current;
        int action = agent.table.choose(agent.observation, config.exploration);
        PermutationSolution<Integer> leader = chooseLeader(action, direction, current);
        GlobalFlowTrace.selected(leader, direction, step, action);
        if (audit != null) audit.feedbackQgs(direction, step, action, leader);
        if (audit != null) audit.teacherSelected(leader);
        List<Particle> next = global(current, direction, leader);
        if (mechanism != null) mechanism.batch(direction, step, next);
        double reward = GroupReward.compute(current, next, preference);
        int nextState = preference.state(reward, chapter);
        agent.table.update(agent.observation, action, reward, nextState);
        state.count("qgs.g" + direction.id() + ".updates");
        state.count("qgs.g" + direction.id() + ".preference." + preference.name());
        state.count("qgs.g" + direction.id() + ".action" + action);
        previousLeaders.put(direction, ParetoTools.copy(leader));
        agent.current = next; agent.observation = nextState;
        if (QgsEpochSchedule.fresh()) {
            long start = System.nanoTime();
            for (Particle p : next) state.remember(java.util.Collections.singletonList(p.current));
            GlobalFlowTrace.offered(next.size(), System.nanoTime() - start);
        }
    }
"""+body[end:]
    return body


def build(root):
    src,classes=root/"source",root/"classes";src.mkdir();classes.mkdir()
    cp=(BASIS/"classpath.txt").read_text(encoding="utf-8-sig").strip()
    (src/"CanonicalHmopso.java").write_text(canonical_source(),encoding="utf-8")
    state=(ROOT/"runs/batch-survival-study-20261104-222516-378030/source/SearchState.java").read_text(encoding="utf-8")
    state=replace(state,"        problem.evaluate(candidate);","        GlobalFlowTrace.before(candidate, stage, direction);\n        problem.evaluate(candidate);")
    (src/"SearchState.java").write_text(state,encoding="utf-8")
    entry=(BASIS/"source/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry=replace(entry,"        obs.write(out);","        obs.write(out);\n        append(out.resolve(\"global-flow.jsonl\"), org.uma.jmetal.util.research.search.GlobalFlowTrace.diagnostics());")
    (src/"PddrIsolationRun.java").write_text(entry,encoding="utf-8")
    for name in ("QgsEpochSchedule","GlobalFlowTrace","QgsEpochScheduleChecks"):
        shutil.copy2(ROOT/f"src/algorithms/diagnostics/{name}.java",src)
    for name in ("qgs_epoch_build.py","run_qgs_epoch_probe.py","paired_survival_bench.py"):
        shutil.copy2(Path(__file__).with_name(name),src)
    execute(["javac","-encoding","UTF-8","--release","8","-cp",cp,"-d",str(classes),*map(str,src.glob("*.java"))],root/"compile.log")
    write_once(root/"class-hashes.json",class_hashes(classes));cp=f"{classes};{cp}"
    (root/"classpath.txt").write_text(cp,encoding="utf-8");return cp
