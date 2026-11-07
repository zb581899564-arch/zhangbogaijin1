package org.uma.jmetal.util.research.search;

import java.util.Random;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Two-state tabular Q learning; a separate instance is required for each agent. */
public final class QTable {
    private final double[][] values;
    private final double alpha, gamma;
    public QTable(int actions, double alpha, double gamma) {
        if (actions < 1 || !(alpha > 0 && alpha <= 1) || !(gamma >= 0 && gamma <= 1)) {
            throw new IllegalArgumentException("Invalid Q-table dimensions or learning parameters");
        }
        values = new double[2][actions]; this.alpha = alpha; this.gamma = gamma;
    }
    public int choose(int state, double exploration) {
        Random random = SeededRandom.current();
        if (random.nextDouble() < exploration) return random.nextInt(values[state].length);
        double best = maximum(state); int ties = 0, chosen = 0;
        for (int a = 0; a < values[state].length; a++) if (values[state][a] == best) {
            if (random.nextInt(++ties) == 0) chosen = a;
        }
        return chosen;
    }
    public void update(int state, int action, double reward, int nextState) {
        if (!Double.isFinite(reward)) throw new IllegalArgumentException("Non-finite Q reward");
        double previous = values[state][action];
        values[state][action] = previous + alpha * (reward + gamma * maximum(nextState) - previous);
    }
    public double value(int state, int action) { return values[state][action]; }
    public double[][] snapshot() { return new double[][] {values[0].clone(), values[1].clone()}; }
    private double maximum(int state) {
        double best = values[state][0];
        for (double value : values[state]) best = Math.max(best, value);
        return best;
    }
}
