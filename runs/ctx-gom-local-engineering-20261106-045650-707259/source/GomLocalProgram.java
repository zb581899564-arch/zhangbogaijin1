package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Complete source-style joint program, called explicitly instead of the old local phase. */
public final class GomLocalProgram {
    private GomLocalProgram() { }
    public static Particle improve(Particle particle, Direction preference, SearchState evaluator) {
        GomRunScope scope = GomRunScope.require(); scope.guard("PROGRAM_START"); GomWorkspace w = scope.workspace;
        if (w == null || !scope.stage.equals("LOCAL")) throw new AssertionError("Unprepared local pass");
        int slot = w.claim(particle.current); w.slot = slot; w.step = w.subset = w.donorSlot = -1; int family = w.families.get(slot);
        List<int[]> masks = w.masks.get(family); List<Integer> order = new ArrayList<>();
        for (int i = 0; i < masks.size(); i++) order.add(i); Collections.shuffle(order, SeededRandom.current());
        List<Integer> donors = new ArrayList<>(w.domains.get(family)); donors.remove(Integer.valueOf(slot));
        scope.evidence.record(GomRecords.row("kind", "program", "pass", scope.passes, "slot", slot, "family", family,
            "preference", preference.name(), "physicalGroup", evaluator.ledgerGroup(preference), "order", order,
            "inputFee", scope.registry.fee(particle.current), "receiverRaw", GomRecords.raw(particle.current)));
        for (int step = 0; step < order.size(); step++) {
            scope.guard("LOCAL_PROPOSAL"); w.step = step; w.subset = order.get(step); w.donorSlot = donors.get(SeededRandom.current().nextInt(donors.size()));
            GomRecords.State parent = w.values.get(slot), donor = w.values.get(w.donorSlot);
            PaMixingMove move = PaMixingMove.apply(w.catalog, parent.genes, donor.genes, masks.get(w.subset));
            PermutationSolution<Integer> child = GomRecords.copy(parent.point, move.genome);
            if (SchedulingEncoding.repair(child, w.instance) != 0) throw new AssertionError("GOM proposal required repair");
            w.pending = GomRecords.row("kind", "proposal", "pass", scope.passes, "slot", slot, "step", step, "subset", w.subset,
                "donorSlot", w.donorSlot, "parentId", parent.id, "donorId", donor.id, "fallback", move.fallback);
            scope.evidence.record(w.pending);
            evaluator.evaluate(child, "jointLocal", preference); GomRecords.sameView(child, move.genome);
            if (scope.lastPaid != child) throw new AssertionError("Missing paid archive notification");
            double[] a = child.getObjectives(), b = parent.objectives;
            boolean keep = preference == Direction.CENTER ? PaInternalArchive.weaklyDominates(a,b) || !scope.lastFlags.dominated
                : a[preference.objective()] < b[preference.objective()];
            GomRecords.State state = new GomRecords.State(++scope.states, scope.run.budget().successful(), move.genome, child); scope.localFees++;
            if (keep) w.values.set(slot, state);
            Map<String,Object> event = state.record(false); event.putAll(GomRecords.row("kind", "step", "pass", scope.passes, "slot", slot,
                "step", step, "subset", w.subset, "donorSlot", w.donorSlot, "parentId", parent.id, "donorId", donor.id,
                "accepted", keep, "fallback", move.fallback)); scope.evidence.record(event); w.pending = null;
        }
        w.programs++; scope.completedPrograms++; scope.evidence.record(GomRecords.row("kind", "programEnd", "pass", scope.passes,
            "slot", slot, "result", w.values.get(slot).record(false)));
        if (w.programs == 100) {
            scope.completedPasses++; scope.stage = "GLOBAL_OR_INITIAL";
            scope.evidence.record(GomRecords.row("kind", "passEnd", "pass", scope.passes, "workspace", w.receipt()));
        }
        return particle.descend(w.values.get(slot).point);
    }
}
