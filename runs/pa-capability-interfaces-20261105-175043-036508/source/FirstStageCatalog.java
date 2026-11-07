package org.uma.jmetal.util.research.modelglobal;

import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;

/** Legal categorical (factory, machine, worker) tuples; ids have no metric meaning. */
public final class FirstStageCatalog {
    private final Instance instance;
    private final int[] offsets;
    private final int[][] tuples;

    public FirstStageCatalog(Instance value) {
        if (value == null || value.kind() != ModelKind.CHAPTER4_DUAL_RESOURCE)
            throw new IllegalArgumentException("Chapter4 dual-resource instance required");
        instance = value; offsets = new int[value.factories() + 1];
        for (int f = 0; f < value.factories(); f++)
            offsets[f + 1] = Math.addExact(offsets[f], Math.multiplyExact(value.machines(f, 0), value.workers(f, 0)));
        tuples = new int[offsets[value.factories()]][3];
        for (int f = 0; f < value.factories(); f++)
            for (int m = 0; m < value.machines(f, 0); m++)
                for (int w = 0; w < value.workers(f, 0); w++)
                    tuples[id(f, m, w)] = new int[]{f, m, w};
    }

    public int jobs() { return instance.jobs(); }
    public int factories() { return instance.factories(); }
    public int size() { return tuples.length; }

    public int id(int factory, int machine, int worker) {
        range(factory, factories(), "factory");
        range(machine, instance.machines(factory, 0), "machine");
        range(worker, instance.workers(factory, 0), "worker");
        return offsets[factory] + machine * instance.workers(factory, 0) + worker;
    }

    public int[] tuple(int id) {
        range(id, size(), "tuple"); return tuples[id].clone();
    }

    public int factory(int id) { range(id, size(), "tuple"); return tuples[id][0]; }

    static void range(int value, int count, String name) {
        if (value < 0 || value >= count) throw new IllegalArgumentException("Invalid " + name + ": " + value);
    }
}
