package org.uma.jmetal.util.research.model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Objectives and auxiliary factory metadata are separate typed values. */
public final class Schedule implements java.io.Serializable {
    private static final long serialVersionUID = 1L;
    private final List<Operation> operations;
    private final double[] makespan, energy, cost, objectives;
    private final String policy;
    Schedule(Instance instance, List<Operation> operations, String policy) {
        this.operations = Collections.unmodifiableList(new ArrayList<Operation>(operations));
        this.policy = policy;
        makespan = new double[instance.factories()];
        energy = new double[instance.factories()]; cost = new double[instance.factories()];
        accumulate(instance);
        objectives = new double[3];
        for (int f = 0; f < makespan.length; f++) {
            objectives[0] = Math.max(objectives[0], makespan[f]);
            objectives[1] += energy[f]; objectives[2] += cost[f];
        }
    }
    private void accumulate(Instance in) {
        for (Operation op : operations) {
            int f = op.factory(); makespan[f] = Math.max(makespan[f], op.end());
            energy[f] += op.duration() * in.power(f, op.stage(), op.machine());
            if (in.kind() == ModelKind.CHAPTER4_DUAL_RESOURCE) {
                cost[f] += op.duration() * in.cost(f, op.stage(), op.worker());
            }
        }
        for (int f = 0; f < in.factories(); f++) for (int k = 0; k < in.stages(); k++) {
            for (int m = 0; m < in.machines(f, k); m++) {
                double first = Double.POSITIVE_INFINITY, last = 0, busy = 0; int worker = -1;
                for (Operation op : operations) if (op.factory() == f && op.stage() == k && op.machine() == m) {
                    first = Math.min(first, op.start()); last = Math.max(last, op.end());
                    busy += op.duration(); worker = op.worker();
                }
                if (worker < 0) continue;
                double span = last - first;
                energy[f] += Math.max(0, span - busy) * in.standby(f, k, m);
                if (in.kind() == ModelKind.CHAPTER3_FIXED_WORKER) cost[f] += span * in.cost(f, k, worker);
            }
        }
    }
    public List<Operation> operations() { return operations; }
    public String decodingPolicy() { return policy; }
    public double[] objectives() { return objectives.clone(); }
    public double[] factoryMakespan() { return makespan.clone(); }
    public double[] factoryEnergy() { return energy.clone(); }
    public double[] factoryCost() { return cost.clone(); }
    public int criticalFactory(int objective, boolean maximum) {
        if (objective < 0 || objective > 2) throw new IllegalArgumentException("Objective must be 0,1,2");
        double[] values = objective == 0 ? makespan : objective == 1 ? energy : cost;
        int best = 0;
        for (int f = 1; f < values.length; f++) if (maximum ? values[f] > values[best] : values[f] < values[best]) best = f;
        return best;
    }
}
