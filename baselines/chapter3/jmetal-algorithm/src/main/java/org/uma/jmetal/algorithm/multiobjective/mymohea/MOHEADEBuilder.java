package org.uma.jmetal.algorithm.multiobjective.mymohea;

import org.uma.jmetal.operator.CrossoverOperator;
import org.uma.jmetal.operator.MutationOperator;
import org.uma.jmetal.operator.SelectionOperator;
import org.uma.jmetal.operator.impl.selection.BinaryTournamentSelection;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.AlgorithmBuilder;
import org.uma.jmetal.util.JMetalException;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
import org.uma.jmetal.util.evaluator.impl.SequentialSolutionListEvaluator;

import java.util.List;


/** Builder class */
public class MOHEADEBuilder<S extends Solution<?>> implements AlgorithmBuilder<MOHEADE<S>> {


    protected final Problem<S> problem;
    protected int maxIterations;
    protected int populationSize;
    protected CrossoverOperator<S> crossoverOperator;
    protected MutationOperator<S> mutationOperator;
    protected SelectionOperator<List<S>, S> selectionOperator;
    protected SolutionListEvaluator<S> evaluator;
    protected int archiveSize;
    protected int VEGASize;
    protected double DERate;
    private double crossoverRate;
    private double mutationRate;

    private double CrossoverRates4worker;
    private double CrossoverRates4machine;
    private double mutationRate4worker;
    private double mutationRate4machine;

    /**
     * MOHEABuilder constructor
     */
    public MOHEADEBuilder(Problem<S> problem, CrossoverOperator<S> crossoverOperator,
                        MutationOperator<S> mutationOperator, int archiveSize, int VEGASize) {
        this.problem = problem;
        maxIterations = 4000;
        populationSize = 200;
        this.crossoverOperator = crossoverOperator ;
        this.mutationOperator = mutationOperator ;
        selectionOperator = new BinaryTournamentSelection<S>();
        evaluator = new SequentialSolutionListEvaluator<S>();
        this.archiveSize = archiveSize ;
        this.VEGASize = VEGASize;



    }

    public MOHEADEBuilder<S> setMaxIterations(int maxIterations) {
        if (maxIterations < 0) {
            throw new JMetalException("maxIterations is negative: " + maxIterations);
        }
        this.maxIterations = maxIterations;

        return this;
    }

    public MOHEADEBuilder<S> setPopulationSize(int populationSize) {
        if (populationSize < 0) {
            throw new JMetalException("Population size is negative: " + populationSize);
        }

        this.populationSize = populationSize;

        return this;
    }

    public MOHEADEBuilder<S> setSelectionOperator(SelectionOperator<List<S>, S> selectionOperator) {
        if (selectionOperator == null) {
            throw new JMetalException("selectionOperator is null");
        }
        this.selectionOperator = selectionOperator;

        return this;
    }

    public MOHEADEBuilder<S> setSolutionListEvaluator(SolutionListEvaluator<S> evaluator) {
        if (evaluator == null) {
            throw new JMetalException("evaluator is null");
        }
        this.evaluator = evaluator;

        return this;
    }

    public MOHEADEBuilder<S> setnumberofarchive(int numberofarchive) {
        this.archiveSize = numberofarchive ;

        return this;
    }

    public MOHEADEBuilder<S> setVEGASize(int VEGASize) {
        this.VEGASize = VEGASize;

        return this;
    }
    public MOHEADEBuilder setCrossoverRate(double Cross_c) {
        this.crossoverRate = Cross_c;
        return this ;
    }
    public MOHEADEBuilder setMutationRate(double Mutation_m) {
        this.mutationRate = Mutation_m;
        return this ;
    }
    public double getCrossoverRate() {
        return crossoverRate;
    }
    public double getMutationRate() {
        return mutationRate;
    }
    public MOHEADEBuilder<S> setDERate(double Probability) {
        this.DERate = Probability ;

        return this;
    }

    public MOHEADEBuilder setCrossoverRates4worker(double CrossoverRates4worker) {
        this.CrossoverRates4worker = CrossoverRates4worker;
        return this ;
    }

    public MOHEADEBuilder setCrossoverRates4machine(double CrossoverRates4machine) {
        this.CrossoverRates4machine = CrossoverRates4machine;

        return this ;
    }


    public MOHEADEBuilder setMutationRate4worker(double mutationRate4worker) {
        this.mutationRate4worker = mutationRate4worker;
        return this ;
    }

    public MOHEADEBuilder setMutationRate4machine(double mutationRate4machine) {
        this.mutationRate4machine = mutationRate4machine;
        return this ;
    }



    public MOHEADE<S> build() {
        MOHEADE<S> algorithm = null ;
        algorithm = new MOHEADE<S>(problem, maxIterations, populationSize, crossoverOperator,
                mutationOperator, selectionOperator, evaluator, archiveSize, VEGASize, DERate,crossoverRate, mutationRate,CrossoverRates4worker,CrossoverRates4machine,mutationRate4worker,mutationRate4machine);

        return algorithm ;
    }

    /* Getters */
    public Problem<S> getProblem() {
        return problem;
    }

    public int getMaxIterations() {
        return maxIterations;
    }

    public int getPopulationSize() {
        return populationSize;
    }

    public CrossoverOperator<S> getCrossoverOperator() {
        return crossoverOperator;
    }

    public MutationOperator<S> getMutationOperator() {
        return mutationOperator;
    }

    public SelectionOperator<List<S>, S> getSelectionOperator() {
        return selectionOperator;
    }

    public SolutionListEvaluator<S> getSolutionListEvaluator() {
        return evaluator;
    }
}
