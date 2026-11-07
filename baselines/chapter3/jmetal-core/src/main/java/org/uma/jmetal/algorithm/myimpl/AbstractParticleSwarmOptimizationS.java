package org.uma.jmetal.algorithm.myimpl;

import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.algorithm.impl.AbstractParticleSwarmOptimization;

import java.util.List;

/**
 * Abstract class representing a PSO algorithm
 *
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 */
@SuppressWarnings("serial")
public abstract class AbstractParticleSwarmOptimizationS<S, Result>  implements Algorithm<Result> {
    private List<S> swarm;
    public List<S> getSwarm() {
        return swarm;
    }
    public void setSwarm(List<S> swarm) {
        this.swarm = swarm;
    }

    protected abstract void initProgress() ;
    protected abstract void updateProgress() ;

    protected abstract boolean isStoppingConditionReached() ;
    protected abstract List<S> createInitialSwarm() ;
    protected abstract List<S> evaluateSwarm(List<S> swarm) ;
    protected abstract void initializeLeader(List<S> swarm) ;
    protected abstract void initializeParticlesMemory(List<S> swarm) ;
    protected abstract void update(List<S> swarm) ;
    protected abstract void updateLeaders(List<S> swarm) ;
    protected abstract void updateParticlesMemory(List<S> swarm) ;

    public abstract List<S> getResult1() ;

    //  public abstract ArrayList<double[]> getResult2();
    @Override
    public void run() {
        swarm = createInitialSwarm() ;
        swarm = evaluateSwarm(swarm);
        initializeParticlesMemory(swarm) ;
        initializeLeader(swarm) ;
        initProgress();

        while (!isStoppingConditionReached()) {
            update(swarm);
            swarm = evaluateSwarm(swarm) ;
            updateParticlesMemory(swarm) ;
            updateLeaders(swarm) ;
            updateProgress();
        }
    }
}
