package org.uma.jmetal.algorithm.multiobjective.mypso.util;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class Experience {
    public double[][] state;
    public int action;
    public double reward;
    public double[][] nextState;
    public boolean done;

    public Experience(double[][] state, int action, double reward, double[][] nextState, boolean done) {
        this.state = state;
        this.action = action;
        this.reward = reward;
        this.nextState = nextState;
        this.done = done;
    }
}

