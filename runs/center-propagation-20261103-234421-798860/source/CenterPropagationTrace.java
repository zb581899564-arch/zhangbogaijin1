package org.uma.jmetal.util.research.search;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.uma.jmetal.solution.PermutationSolution;

/** Connect paid first-CENTER outcomes to the next generation without changing search inputs. */
public final class CenterPropagationTrace {
    private static final Set<Long> centerEndpoints = new LinkedHashSet<>(), selected = new LinkedHashSet<>();
    private static final List<Map<String, Object>> events = new ArrayList<>();
    private static long[] assembled;
    private static long from, through;
    private CenterPropagationTrace() {}

    static void selection(List<Particle> candidates, SurvivorSelection.Result result, int globalCount) {
        if (ReverseAudit.run().generation() != 1) return;
        if (candidates.size() != 200 || globalCount != 100) throw new IllegalStateException("Unexpected selection scope");
        from = Long.getLong("research.center.from");
        through = Long.getLong("research.center.through");
        for (int i = globalCount + 15; i < globalCount + 70; i++) {
            long born = ReverseAudit.birth(candidates.get(i).current);
            if (from < born && born <= through) centerEndpoints.add(born);
        }
        for (int i : result.indices()) {
            long born = ReverseAudit.birth(candidates.get(i).current);
            if (i >= globalCount + 15 && i < globalCount + 70 && centerEndpoints.contains(born)) selected.add(born);
        }
    }

    public static void composition(long[] sourceFEs) {
        if (ReverseAudit.run().generation() == 2) assembled = sourceFEs;
    }

    static void evaluated(Particle receiver, PermutationSolution<Integer> pbest,
            PermutationSolution<Integer> leader, PermutationSolution<Integer> child, Direction direction, boolean composed) {
        if (ReverseAudit.run().generation() != 2) return;
        if ((assembled != null) != composed) throw new IllegalStateException("Missing assembly evidence");
        long parent = ReverseAudit.birth(receiver.current), p = ReverseAudit.birth(pbest), g = ReverseAudit.birth(leader);
        events.add(ReverseAudit.row("paidFE", ReverseAudit.birth(child), "group", direction.name(), "composed", composed,
                "parentFE", parent, "personalInputFE", composed ? null : p, "leaderInputFE", composed ? null : g,
                "factorySourceFEs", assembled, "admitted", Boolean.TRUE.equals(child.getAttribute("diagnostic.reverse.admitted")),
                "objectives", child.getObjectives().clone()));
        assembled = null;
    }

    public static void finish(Path out) throws IOException {
        ReverseAudit.writeRows(out.resolve("propagation-endpoints.jsonl"), java.util.Collections.singletonList(
                ReverseAudit.row("from", from, "through", through, "centerEndpoints", centerEndpoints,
                        "selectedCenterEndpoints", selected)));
        ReverseAudit.writeRows(out.resolve("propagation-gen2.jsonl"), events);
    }
}
