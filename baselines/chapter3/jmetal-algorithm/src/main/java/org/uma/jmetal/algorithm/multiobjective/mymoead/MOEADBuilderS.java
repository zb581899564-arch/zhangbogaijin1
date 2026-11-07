package org.uma.jmetal.algorithm.multiobjective.mymoead;

import org.uma.jmetal.algorithm.multiobjective.nsgaii.NSGAIIBuilder;
import org.uma.jmetal.operator.CrossoverOperator;
import org.uma.jmetal.operator.MutationOperator;
import org.uma.jmetal.operator.impl.mutation.PermutationSwapMutation;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.AlgorithmBuilder;

/**
 * Builder class for algorithm MOEA/D and variants
 *
 * @author Antonio J. Nebro
 * @version 1.0
 */
public class MOEADBuilderS<S extends Solution<?>> implements AlgorithmBuilder<AbstractMOEADS<S>> {

    public enum Variant {MOEADS} ;

    protected Problem<S> problem ;

    /** T in Zhang & Li paper */
    protected int neighborSize;
    /** Delta in Zhang & Li paper */
    protected double neighborhoodSelectionProbability;
    /** nr in Zhang & Li paper */
    protected int maximumNumberOfReplacedSolutions;

    protected MOEADS.FunctionType functionType;

    protected CrossoverOperator<S> crossover;
    protected MutationOperator<S> mutation;
    protected String dataDirectory;

    protected int populationSize;
    protected int resultPopulationSize ;

    protected int maxIterations;
    private int factories;
    protected int numberOfThreads ;
    private double crossoverRate;
    private double mutationRate;

    private double CrossoverRates4worker;
    private double CrossoverRates4machine;
    private double mutationRate4worker;
    private double mutationRate4machine;

    protected Variant moeadVariant ;

    /** Constructor */
    public MOEADBuilderS(Problem<S> problem, int numberOffactories, CrossoverOperator<S> crossover, Variant variant) {
        this.problem = problem ;
//        populationSize = 100 ;
//        resultPopulationSize = 100 ;
//        maxIterations = 3000 ;
        this.crossover = crossover ;

        //crossover =new PMXCrossover(0.9);

        mutation = new PermutationSwapMutation(0.3);

        functionType = MOEADS.FunctionType.TCHE ;
        //neighborhoodSelectionProbability = 0.1 ;
        //maximumNumberOfReplacedSolutions = 2 ;
        dataDirectory = "" ;
        //neighborSize = 20 ;
        numberOfThreads = 1 ;
        moeadVariant = variant ;

        this.factories = numberOffactories;
    }

    /* Getters/Setters */
    public int getNeighborSize() {
        return neighborSize;
    }

    public int getMaxEvaluations() {
        return maxIterations;
    }

    public int getPopulationSize() {
        return populationSize;
    }

    public int getResultPopulationSize() {
        return resultPopulationSize;
    }

    public String getDataDirectory() {
        return dataDirectory;
    }

    public MutationOperator<S> getMutation() {
        return mutation;
    }

    public CrossoverOperator<S> getCrossover() {
        return crossover;
    }

    public MOEADS.FunctionType getFunctionType() {
        return functionType;
    }

    public int getMaximumNumberOfReplacedSolutions() {
        return maximumNumberOfReplacedSolutions;
    }

    public double getNeighborhoodSelectionProbability() {
        return neighborhoodSelectionProbability;
    }

    public int getNumberOfThreads() {
        return numberOfThreads ;
    }

    public MOEADBuilderS<S> setPopulationSize(int populationSize) {
        this.populationSize = populationSize;

        return this;
    }

    public MOEADBuilderS<S> setResultPopulationSize(int resultPopulationSize) {
        this.resultPopulationSize = resultPopulationSize;

        return this;
    }

    public MOEADBuilderS<S> setMaxIterations(int maxIterations) {
        this.maxIterations = maxIterations;

        return this;
    }

    public MOEADBuilderS<S> setNeighborSize(int neighborSize) {
        this.neighborSize = neighborSize ;

        return this ;
    }

    public MOEADBuilderS setCrossoverRate(double Cross_c) {
        this.crossoverRate = Cross_c;
        return this ;
    }
    public MOEADBuilderS setMutationRate(double Mutation_m) {
        this.mutationRate = Mutation_m;
        return this ;
    }
    public double getCrossoverRate() {
        return crossoverRate;
    }
    public double getMutationRate() {
        return mutationRate;
    }
    public MOEADBuilderS<S> setNeighborhoodSelectionProbability(double neighborhoodSelectionProbability) {
        this.neighborhoodSelectionProbability = neighborhoodSelectionProbability ;

        return this ;
    }

    public MOEADBuilderS<S> setFunctionType(MOEADS.FunctionType functionType) {
        this.functionType = functionType ;

        return this ;
    }

    public MOEADBuilderS<S> setMaximumNumberOfReplacedSolutions(int maximumNumberOfReplacedSolutions) {
        this.maximumNumberOfReplacedSolutions = maximumNumberOfReplacedSolutions ;

        return this ;
    }

    public MOEADBuilderS<S> setCrossover(CrossoverOperator<S> crossover) {
        this.crossover = crossover ;

        return this ;
    }

    public MOEADBuilderS<S> setMutation(MutationOperator<S> mutation) {
        this.mutation = mutation ;

        return this ;
    }

    public MOEADBuilderS<S> setDataDirectory(String dataDirectory) {
        this.dataDirectory = dataDirectory ;

        return this ;
    }

    public MOEADBuilderS<S> setNumberOfThreads(int numberOfThreads) {
        this.numberOfThreads = numberOfThreads ;

        return this ;
    }


    public MOEADBuilderS<S> setCrossoverRates4worker(double CrossoverRates4worker) {
        this.CrossoverRates4worker = CrossoverRates4worker;
        return this ;
    }

    public MOEADBuilderS<S> setCrossoverRates4machine(double CrossoverRates4machine) {
        this.CrossoverRates4machine = CrossoverRates4machine;

        return this ;
    }


    public MOEADBuilderS<S> setMutationRate4worker(double mutationRate4worker) {
        this.mutationRate4worker = mutationRate4worker;
        return this ;
    }

    public MOEADBuilderS<S> setMutationRate4machine(double mutationRate4machine) {
        this.mutationRate4machine = mutationRate4machine;
        return this ;
    }


    public AbstractMOEADS<S> build() {
        MOEADS<S> algorithm = null ;
        if (moeadVariant.equals(MOEADBuilderS.Variant.MOEADS)) {
            algorithm = new MOEADS<>(factories,problem, populationSize, resultPopulationSize, maxIterations, mutation,
                    crossover, functionType, dataDirectory, neighborhoodSelectionProbability,
                    maximumNumberOfReplacedSolutions, neighborSize,crossoverRate, mutationRate, CrossoverRates4worker,CrossoverRates4machine,mutationRate4worker,mutationRate4machine);
        }
        return algorithm ;
    }
}
