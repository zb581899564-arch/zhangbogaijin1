package org.uma.jmetal.algorithm.multiobjective.mypso;

import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.AlgorithmBuilder;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
import org.uma.jmetal.util.evaluator.impl.SequentialSolutionListEvaluator;

/** Class implementing the MOPSODivideSubgroup algorithm */

public class MOPSODivSubDEBuilder implements AlgorithmBuilder<MOPSODivSubDE> {

    protected final Problem<PermutationSolution<Integer>> problem;
    protected SolutionListEvaluator<PermutationSolution<Integer>> evaluator;

    private int swarmSize;
    private int maxIterations;
    private int upSize ;
    private int upNewSize;
    private int centralSize;
    private int downSize;
    private int factories;

    private double DERate;
    private double rand_k;
    private double crossoverRate;
    private double mutationRate;
    private double DEcrossoverRates;
    private double DEmutationRate;
    private double Qnums;
    private double CrossoverRates4worker;
    private double CrossoverRates4machine;
    private double mutationRate4worker;
    private double mutationRate4machine;
    private int localsearch;

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
     * @param DERate
     */

    /**
     *
     * @param problem
     * @param swarmSize
     * @param numberOffactories
     * @param DERate
     * @param DEcrossoverRates
     * @param DEmutationRate
     * @param Qnums
     */
    public MOPSODivSubDEBuilder(Problem<PermutationSolution<Integer>> problem, int swarmSize, int numberOffactories,double DERate,double DEcrossoverRates,double DEmutationRate,double Qnums) {
        this.problem = problem ;
        evaluator = new SequentialSolutionListEvaluator<PermutationSolution<Integer>>();

        //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,


        //新版分成四个种群 均分
//        this.upSize = swarmSize / 4;//20
//        this.upNewSize = swarmSize - (swarmSize / 4) * 3;//20
//        this.centralSize = swarmSize- (swarmSize / 4) * 3;//40
//        this.downSize = swarmSize -upSize-upNewSize-centralSize;//20


        //中心种群40，其余20
//        this.upSize = swarmSize / 5;//20
//        this.upNewSize = swarmSize - (swarmSize / 5) * 4;//20
//        this.centralSize = swarmSize- (swarmSize / 5) * 3;//40
//        this.downSize = swarmSize -upSize-upNewSize-centralSize;//20


        //中心种群55，其余15
        this.upSize      = 15;
        this.upNewSize   = 15;
        this.centralSize = 55;
        this.downSize    = 15;

        //中心种群70，其余10
//        this.upSize      = swarmSize/10;
//        this.upNewSize   = swarmSize/10;
//        this.downSize    = swarmSize/10;
//        this.centralSize = swarmSize-upSize-upNewSize-downSize;

        //中心种群46，其余18
//        this.upSize      = 18;
//        this.upNewSize   = 18;
//        this.downSize    = 18;
//        this.centralSize = swarmSize-upSize-upNewSize-downSize;

//        System.out.println(this.upSize);
//        System.out.println(this.upNewSize);
//        System.out.println(this.centralSize);
//        System.out.println(this.downSize);
//
//        try {
//            Thread.sleep(9999999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }

        //老版分成三个种群
//        this.upSize = swarmSize / 3;
//        this.centralSize = swarmSize - (swarmSize / 3) * 2;
//        this.downSize = swarmSize/  3;

        this.DEcrossoverRates=DEcrossoverRates;
        this.DEmutationRate=DEmutationRate;
        this.DERate = DERate;
        this.Qnums = Qnums;
        this.factories = numberOffactories;
    }

    public MOPSODivSubDEBuilder setSwarmSize(int swarmSize) {
        this.swarmSize = swarmSize ;

        return this ;
    }

    public MOPSODivSubDEBuilder setLocalSearch(int localsearch) {
        this.localsearch = localsearch ;
        return this ;
    }

    public MOPSODivSubDEBuilder setMaxIterations(int maxIterations) {
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

    public double getCrossoverRates4worker() {
        return CrossoverRates4worker;
    }

    public MOPSODivSubDEBuilder setRand_k(double rand_k) {
        this.rand_k = rand_k;
        return this ;
    }
    public MOPSODivSubDEBuilder setCrossoverRate(double Cross_c) {
        this.crossoverRate = Cross_c;
        return this ;
    }
    public MOPSODivSubDEBuilder setMutationRate(double Mutation_m) {
        this.mutationRate = Mutation_m;
        return this ;
    }
    public MOPSODivSubDEBuilder setFactories(int factories) {
        this.factories = factories;
        return this ;
    }


    public MOPSODivSubDEBuilder setCrossoverRates4worker(double CrossoverRates4worker) {
        this.CrossoverRates4worker = CrossoverRates4worker;
        return this ;
    }

    public MOPSODivSubDEBuilder setCrossoverRates4machine(double CrossoverRates4machine) {
        this.CrossoverRates4machine = CrossoverRates4machine;

        return this ;
    }


    public MOPSODivSubDEBuilder setMutationRate4worker(double mutationRate4worker) {
        this.mutationRate4worker = mutationRate4worker;
        return this ;
    }

    public MOPSODivSubDEBuilder setMutationRate4machine(double mutationRate4machine) {
        this.mutationRate4machine = mutationRate4machine;
        return this ;
    }


//新版三目标
    public MOPSODivSubDE build() {
        return new MOPSODivSubDE(factories,crossoverRate, mutationRate, rand_k,problem, evaluator, swarmSize, maxIterations, upSize, centralSize, downSize, upNewSize,DERate,DEcrossoverRates,DEmutationRate,Qnums,
                CrossoverRates4worker,CrossoverRates4machine,mutationRate4worker,mutationRate4machine,localsearch) ;
    }


    //老版双目标
//    public MOPSODivSubDE build() {
//        return new MOPSODivSubDE(factories,crossoverRate, mutationRate, rand_k,problem, evaluator, swarmSize, maxIterations, upSize, centralSize, downSize,DERate,DEcrossoverRates,DEmutationRate,Qnums) ;
//    }
}
