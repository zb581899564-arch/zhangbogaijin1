package org.uma.jmetal.util.research.search;

import java.util.*;

/** A permutation-invariant CENTER group reward for set-based survival; original reward remains a control. */
public final class GroupReward {
    private static final String MODE = System.getProperty("research.reward.mode", "INDIVIDUAL");
    private GroupReward() { }
    static double compute(List<Particle> before, List<Particle> after, Direction role) {
        if (before.size() != after.size()) throw new IllegalArgumentException("Group size changed");
        if (MODE.equals("INDIVIDUAL") || role != Direction.CENTER) {
            double reward = 0;
            for (int i = 0; i < before.size(); i++) reward += role.reward(before.get(i).current,after.get(i).current);
            return reward / before.size();
        }
        if (!MODE.equals("GROUP")) throw new IllegalArgumentException("Unknown reward mode");
        double reward = 0;
        for (int k = 0; k < 3; k++) {
            double a = 0, b = 0;
            for (Particle p : before) a += p.current.getObjective(k);
            for (Particle p : after) b += p.current.getObjective(k);
            a /= before.size(); b /= after.size();
            reward += (a - b) / (a == 0 ? 1 : Math.abs(a));
        }
        return reward;
    }
    public static String mode() { return MODE; }
}
