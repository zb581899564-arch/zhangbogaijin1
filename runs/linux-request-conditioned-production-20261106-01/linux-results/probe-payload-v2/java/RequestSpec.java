package org.uma.jmetal.util.research.search;

import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;

/** One source-paid composition request; its immutable parameters never consume FE. */
public final class RequestSpec {
    public final String id;
    public final int family;
    public final double cap, eta, energyScale, wageScale;
    public final PermutationSolution<Integer> parent;

    RequestSpec(String[] fields, PermutationSolution<Integer> point) {
        id = fields[0]; family = Integer.parseInt(fields[1]);
        cap = Double.parseDouble(fields[2]); eta = Double.parseDouble(fields[3]);
        energyScale = Double.parseDouble(fields[4]); wageScale = Double.parseDouble(fields[5]); parent = point;
        if (family < 0 || family > 3 || !(cap > 0) || !(energyScale > 0) || !(wageScale > 0)
                || !Double.isFinite(cap + eta + energyScale + wageScale) || eta < 0)
            throw new IllegalArgumentException("Invalid source request parameters");
    }

    double violation(double[] factoryMakespan) {
        double result = 0;
        for (double value : factoryMakespan) result += Math.max(value - cap, 0) / cap;
        return result;
    }

    double score(double[] objectives) {
        return objectives[1] / energyScale + eta * objectives[2] / wageScale;
    }

    public Map<String,Object> record() {
        return GomRecords.row("requestId", id, "family", family, "cap", cap, "eta", eta,
            "energyScale", energyScale, "wageScale", wageScale);
    }
}
