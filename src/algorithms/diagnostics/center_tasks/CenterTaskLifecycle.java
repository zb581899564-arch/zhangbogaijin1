package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Random;
import org.uma.jmetal.solution.PermutationSolution;

/** Rebind tasks only at registered phase boundaries; the physics and search RNG are untouched. */
final class CenterTaskLifecycle {
    private CenterTaskLifecycle() { }

    static void begin(Map<Direction,List<Particle>> groups) {
        if (!CenterTaskState.enabled()) return;
        CenterTaskState.epoch++; CenterTaskState.count("epochsStarted");
        if (groups.get(Direction.CENTER).size() != 55) throw new AssertionError("Expected55CENTERslots");
        for (Direction role : Direction.values()) {
            List<Particle> group = groups.get(role);
            for (int slot = 0; slot < group.size(); slot++) {
                int weight = role == Direction.CENTER ? slot : -1;
                group.get(slot).current.setAttribute(CenterTaskState.KEY,
                        new CenterTaskState.Owner(CenterTaskState.epoch, role, slot, weight));
            }
        }
        CenterTaskState.event("EPOCH_START", groups.get(Direction.CENTER));
    }

    static void beforeBatch(List<Particle> group, Direction role, int step) {
        if (!CenterTaskState.enabled() || role != Direction.CENTER) return;
        reassign(group, step);
        if (step == 0 || step == 49) CenterTaskState.event("GLOBAL_STEP_" + step, group);
    }

    static void beforeLocal(Map<Direction,List<Particle>> groups) {
        if (!CenterTaskState.enabled()) return;
        reassign(groups.get(Direction.CENTER), 50);
        CenterTaskState.event("LOCAL_ENTRY", groups.get(Direction.CENTER));
    }

    private static void reassign(List<Particle> group, int phase) {
        List<Integer> permutation = new ArrayList<>(); for (int i = 0; i < 55; i++) permutation.add(i);
        long seed = Long.getLong("research.centerTasks.seed", 0L) + CenterTaskState.epoch * 104729L + phase;
        // All enabled controls pay the same separate permutation work; it never advances SeededRandom.
        Collections.shuffle(permutation, new Random(seed)); CenterTaskState.count("separateTaskPermutationCalls");
        boolean[] seen = new boolean[55];
        for (Particle particle : group) {
            CenterTaskState.Owner old = CenterTaskState.owner(particle.current);
            if (old.role != Direction.CENTER || old.epoch != CenterTaskState.epoch || seen[old.slot])
                throw new AssertionError("CENTER slots lost before phase");
            seen[old.slot] = true;
            int weight = CenterTaskState.MODE == CenterTaskState.Mode.PERMUTE ? permutation.get(old.slot) : old.slot;
            particle.current.setAttribute(CenterTaskState.KEY,
                    new CenterTaskState.Owner(old.epoch, old.role, old.slot, weight));
        }
    }

    static void inherit(PermutationSolution<Integer> parent, PermutationSolution<Integer> child, Direction role) {
        if (!CenterTaskState.enabled()) return;
        CenterTaskState.Owner owner = CenterTaskState.owner(parent);
        if (owner.role != role) throw new AssertionError("Wrong physical group at inheritance");
        child.setAttribute(CenterTaskState.KEY, owner); CenterTaskState.count("globalChildrenTagged");
    }

    static void localStart(Particle particle, Direction role) {
        if (!CenterTaskState.enabled()) return;
        if (CenterTaskState.activeLocal != null) throw new AssertionError("Nested local task");
        CenterTaskState.activeLocal = CenterTaskState.owner(particle.current);
        if (CenterTaskState.activeLocal.role != role) throw new AssertionError("Wrong local physical role");
        CenterTaskState.count("localEntries");
    }

    static Particle localResult(Particle result, Particle parent, Direction role) {
        if (!CenterTaskState.enabled()) return result;
        result.current.setAttribute(CenterTaskState.KEY, CenterTaskState.owner(parent.current));
        return result;
    }

    static void localEnd() {
        if (!CenterTaskState.enabled()) return;
        if (CenterTaskState.activeLocal == null) throw new AssertionError("Missing local task to close");
        CenterTaskState.activeLocal = null; CenterTaskState.count("localExits");
    }
}
