package org.uma.jmetal.util.research.search;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.cooperation.FrozenCenterSupport;
import org.uma.jmetal.util.research.model.DynamicParameters;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.RunContext;

/** Execute only the 55 CENTER local visits; no QGS, pool choice or environment selection. */
public final class CenterCrossSearch implements Algorithm<Object> {
    private static final long serialVersionUID = 1L;
    private final RunContext<PermutationSolution<Integer>> context;
    private final CenterEntryTrace.Entry entries, reference;
    private final LocalSearch local;
    private final SearchState state;

    public CenterCrossSearch(RunContext<PermutationSolution<Integer>> context, Instance instance, DynamicParameters fatigue,
            Path out, Path particles, Path reference, Path alternate, Path bank) {
        this.context = context;
        entries = CenterEntryTrace.load(particles);
        this.reference = CenterEntryTrace.load(reference);
        CenterEntryTrace.Entry alternateEntry = CenterEntryTrace.load(alternate);
        if (entries.paid != this.reference.paid || entries.paid != alternateEntry.paid
                || entries.particles.size() != 55 || this.reference.reference.size() != 100
                || alternateEntry.reference.size() != 100)
            throw new IllegalArgumentException("Not matching paid CENTRAL snapshots");
        List<PermutationSolution<Integer>> initial = new ArrayList<>();
        for (Particle p : entries.particles) initial.add(p.current);
        validate(initial, instance, fatigue);
        validate(this.reference.reference, instance, fatigue);
        validate(alternateEntry.reference, instance, fatigue);
        state = new SearchState(context.problem(), instance, new FrozenCenterSupport(instance, initial));
        state.observationGroup(Direction.CENTER);
        local = new LocalSearch(instance, 4, new SearchConfig().resolved(4), state);
        CenterEntryTrace.prepare(out, bank, alternateEntry.reference);
    }

    @Override public void run() {
        for (Particle entry : entries.particles) {
            context.problem().checkpoint();
            CenterEntryTrace.retained(local.improve(entry, Direction.CENTER, reference.reference));
        }
        CenterEntryTrace.finish();
        context.problem().checkpoint();
        throw new IllegalStateException("CENTER stage returned before spending its budget");
    }
    private static void validate(List<PermutationSolution<Integer>> values, Instance instance, DynamicParameters fatigue) {
        for (PermutationSolution<Integer> value : values) {
            DynamicSchedule s = (DynamicSchedule) value.getAttribute(DynamicEvaluation.KEY);
            s.validateContext(instance, fatigue);
            if (!Arrays.equals(s.objectives(), value.getObjectives()))
                throw new IllegalStateException("Entry objectives differ from its evaluated schedule");
        }
    }
    public Map<String, Long> diagnostics() { return state.diagnostics(); }
    @Override public Object getResult() { return null; }
    @Override public String getName() { return "CENTER_ENTRY_CROSS_REPLAY"; }
    @Override public String getDescription() { return getName(); }
}
