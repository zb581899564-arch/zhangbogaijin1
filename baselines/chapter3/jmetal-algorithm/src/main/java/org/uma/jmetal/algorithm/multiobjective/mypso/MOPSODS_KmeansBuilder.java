package org.uma.jmetal.algorithm.multiobjective.mypso;

import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.AlgorithmBuilder;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
import org.uma.jmetal.util.evaluator.impl.SequentialSolutionListEvaluator;

/** Class implementing the MOPSODivideSubgroup algorithm */

public class MOPSODS_KmeansBuilder implements AlgorithmBuilder<MOPSODS_Kmeans> {

    protected final Problem<PermutationSolution<Integer>> problem;
    protected SolutionListEvaluator<PermutationSolution<Integer>> evaluator;

    private int swarmSize;
    private int maxIterations;
    private int upSize ;
    private int centralSize;
    private int downSize;
    private double Qnums;
    private double DERate;
    private double rand_k;
    private double crossoverRate;
    private double mutationRate;
    private double DEcrossoverRates;
    private double DEmutationRate;
    private double Krate;
    private int factories;
    /**
     *
     * @param problem
     * @param upSize
     * @param centralSize
     * @param downSize
     * @param Probability
     */
/*    public MOPSODivSubDEBuilder(Problem<PermutationSolution<Integer>> problem, int upSize, int centralSize, int downSize, double Probability) {
        this.problem = problem ;
        evaluator = new SequentialSolutionListEvaluator<PermutationSolution<Integer>>();
        this.upSize = upSize;
        this.centralSize = centralSize;
        this.downSize = downSize;
        this.DERate = Probability;
    }*/

    /**
     * Changed by zhangwq 20211008
     * @param problem
     * @param swarmSize
     * @param Qnums
     */
    public MOPSODS_KmeansBuilder(Problem<PermutationSolution<Integer>> problem, int swarmSize, int numberOffactories,double Qnums) {
        this.problem = problem ;
        evaluator = new SequentialSolutionListEvaluator<PermutationSolution<Integer>>();

        //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,

        this.upSize = swarmSize / 3;
        this.centralSize = swarmSize- (swarmSize / 3) * 2;
        this.downSize = swarmSize / 3;
        this.DEcrossoverRates=DEcrossoverRates;
        this.DEmutationRate=DEmutationRate;
        this.Qnums = Qnums;
        this.factories = numberOffactories;
        this.DERate = DERate;
        this.Krate = Krate;
    }

    public MOPSODS_KmeansBuilder setSwarmSize(int swarmSize) {
        this.swarmSize = swarmSize ;

        return this ;
    }

    public MOPSODS_KmeansBuilder setMaxIterations(int maxIterations) {
        this.maxIterations = maxIterations ;

        return this ;
    }

    /* Getters */
    public int getSwarmSize() {
        return swarmSize;
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
    public int getMaxIterations() {
        return maxIterations;
    }

    public MOPSODS_KmeansBuilder setRand_k(double rand_k) {
        this.rand_k = rand_k;
        return this ;
    }
    public MOPSODS_KmeansBuilder setCrossoverRate(double Cross_c) {
        this.crossoverRate = Cross_c;
        return this ;
    }
    public MOPSODS_KmeansBuilder setMutationRate(double Mutation_m) {
        this.mutationRate = Mutation_m;
        return this ;
    }


    public MOPSODS_Kmeans build() {
        return new MOPSODS_Kmeans(factories,crossoverRate, mutationRate, rand_k,problem, evaluator, swarmSize, maxIterations, upSize, centralSize, downSize,Qnums) ;
    }
}
