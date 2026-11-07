package org.uma.jmetal.algorithm.multiobjective.mypso;

import org.uma.jmetal.algorithm.multiobjective.nsgaii.NSGAIIBuilder;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.AlgorithmBuilder;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
import org.uma.jmetal.util.evaluator.impl.SequentialSolutionListEvaluator;

/** Class implementing the MOPSODivideSubgroup algorithm */

public class MOPSODivSubBuilder implements AlgorithmBuilder<MOPSODivSub> {
    protected final Problem<PermutationSolution<Integer>> problem;
    protected SolutionListEvaluator<PermutationSolution<Integer>> evaluator;

    private int swarmSize = 100 ;
    private int maxIterations = 2500 ;
    private int upSize ;
    private int centralSize;
    private int downSize;
    private int upNewSize;
    private double rand_k;
    private double crossoverRate;
    private double mutationRate;
    private int factories;
    private double Qnums;

    private double CrossoverRates4worker;
    private double CrossoverRates4machine;
    private double mutationRate4worker;
    private double mutationRate4machine;

/*    public MOPSODivSubBuilder(Problem<PermutationSolution<Integer>> problem, int upSize, int centralSize, int downSize) {
        this.problem = problem ;
        evaluator = new SequentialSolutionListEvaluator<PermutationSolution<Integer>>();
        this.upSize = upSize;
        this.centralSize = centralSize;
        this.downSize = downSize;
    }*/
    public MOPSODivSubBuilder(Problem<PermutationSolution<Integer>> problem, int swarmSize, int numberOffactories,double Qnums) {
        this.problem = problem ;
        evaluator = new SequentialSolutionListEvaluator<PermutationSolution<Integer>>();
//        this.upSize = swarmSize / 3;
//        this.centralSize = swarmSize- (swarmSize / 3) * 2;
//        this.downSize = swarmSize / 3;

        this.upSize = swarmSize / 4;//20
        this.upNewSize = swarmSize - (swarmSize / 4) * 3;//20
        this.centralSize = swarmSize- (swarmSize / 4) * 3;//40
        this.downSize = swarmSize -upSize-upNewSize-centralSize;//20

//        System.out.println(this.upSize);
//        System.out.println(this.upNewSize);
//        System.out.println(this.centralSize);
//        System.out.println(this.downSize);

        this.factories = numberOffactories;
        this.Qnums = Qnums;
    }

    public MOPSODivSubBuilder setSwarmSize(int swarmSize) {
        this.swarmSize = swarmSize ;

        return this ;
    }

    public MOPSODivSubBuilder setMaxIterations(int maxIterations) {
        this.maxIterations = maxIterations ;

        return this ;
    }

    public MOPSODivSubBuilder setRand_k(double rand_k) {
        this.rand_k = rand_k;
        return this ;
    }

    public MOPSODivSubBuilder setCrossoverRate(double Cross_c) {
        this.crossoverRate = Cross_c;
        return this ;
    }
    public MOPSODivSubBuilder setMutationRate(double Mutation_m) {
        this.mutationRate = Mutation_m;
        return this ;
    }



    public MOPSODivSubBuilder setCrossoverRates4worker(double CrossoverRates4worker) {
        this.CrossoverRates4worker = CrossoverRates4worker;
        return this ;
    }

    public MOPSODivSubBuilder setCrossoverRates4machine(double CrossoverRates4machine) {
        this.CrossoverRates4machine = CrossoverRates4machine;

        return this ;
    }


    public MOPSODivSubBuilder setMutationRate4worker(double mutationRate4worker) {
        this.mutationRate4worker = mutationRate4worker;
        return this ;
    }

    public MOPSODivSubBuilder setMutationRate4machine(double mutationRate4machine) {
        this.mutationRate4machine = mutationRate4machine;
        return this ;
    }

    public double getCrossoverRate() {
        return crossoverRate;
    }
    public double getMutationRate() {
        return mutationRate;
    }
    /* Getters */
    public int getSwarmSize() {
        return swarmSize;
    }

    public int getMaxIterations() {
        return maxIterations;
    }
    public double getRand_k() {
        return rand_k;
    }
    public MOPSODivSub build() {
//        return new MOPSODivSub(factories,crossoverRate, mutationRate,rand_k,problem, evaluator, swarmSize, maxIterations, upSize, centralSize, downSize,Qnums) ;
        return new MOPSODivSub(factories,crossoverRate, mutationRate, rand_k,problem, evaluator, swarmSize, maxIterations, upSize, centralSize, downSize, upNewSize,Qnums,CrossoverRates4worker,CrossoverRates4machine,mutationRate4worker,mutationRate4machine) ;

    }
}
