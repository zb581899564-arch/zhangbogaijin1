package org.uma.jmetal.algorithm.multiobjective.mypso;

import org.uma.jmetal.algorithm.multiobjective.nsgaii.NSGAIIBuilder;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.AlgorithmBuilder;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
import org.uma.jmetal.util.evaluator.impl.SequentialSolutionListEvaluator;


/** Class implementing the OMOPSO algorithm */
public class MOPSOBuilder implements AlgorithmBuilder<MOPSO> {
    protected final Problem<PermutationSolution<Integer>> problem;
    protected SolutionListEvaluator<PermutationSolution<Integer>> evaluator;

    private int swarmSize ;
    private int archiveSize ;
    private int maxIterations ;
/*    private double w ;*/
    private double rand_k;
    private double crossoverRate;
    private double mutationRate;


    private double CrossoverRates4worker;
    private double CrossoverRates4machine;
    private double mutationRate4worker;
    private double mutationRate4machine;


    public MOPSOBuilder(Problem<PermutationSolution<Integer>> problem) {
        this.problem = problem ;
        evaluator = new SequentialSolutionListEvaluator<PermutationSolution<Integer>>();

    }

    public MOPSOBuilder setSwarmSize(int swarmSize) {
        this.swarmSize = swarmSize ;

        return this ;
    }

/*    public MOPSOBuilder setw(double w) {
        this.w = w ;
        return this ;
    }*/

    public MOPSOBuilder setArchiveSize(int archiveSize) {
        this.archiveSize = archiveSize ;

        return this ;
    }

    public MOPSOBuilder setMaxIterations(int maxIterations) {
        this.maxIterations = maxIterations ;

        return this ;
    }

    public MOPSOBuilder setRand_k(double rand_k) {
        this.rand_k = rand_k;
        return this ;
    }
    public MOPSOBuilder setCrossoverRate(double Cross_c) {
        this.crossoverRate = Cross_c;
        return this ;
    }
    public MOPSOBuilder setMutationRate(double Mutation_m) {
        this.mutationRate = Mutation_m;
        return this ;
    }

    public MOPSOBuilder setCrossoverRates4worker(double CrossoverRates4worker) {
        this.CrossoverRates4worker = CrossoverRates4worker;
        return this ;
    }

    public MOPSOBuilder setCrossoverRates4machine(double CrossoverRates4machine) {
        this.CrossoverRates4machine = CrossoverRates4machine;

        return this ;
    }


    public MOPSOBuilder setMutationRate4worker(double mutationRate4worker) {
        this.mutationRate4worker = mutationRate4worker;
        return this ;
    }

    public MOPSOBuilder setMutationRate4machine(double mutationRate4machine) {
        this.mutationRate4machine = mutationRate4machine;
        return this ;
    }




    public double getRand_k() {
        return rand_k;
    }
    public double getCrossoverRate() {
        return crossoverRate;
    }
    public double getMutationRate() {
        return mutationRate;
    }
    /* Getters */
    public int getArchiveSize() {
        return archiveSize;
    }

/*    public double getw() {
        return w;
    }*/

    public int getSwarmSize() {
        return swarmSize;
    }

    public int getMaxIterations() {
        return maxIterations;
    }

    public MOPSO build() {
        return new MOPSO(crossoverRate, mutationRate, rand_k,problem, evaluator, swarmSize, maxIterations, archiveSize ,CrossoverRates4worker,CrossoverRates4machine,mutationRate4worker,mutationRate4machine) ;
    }
}
