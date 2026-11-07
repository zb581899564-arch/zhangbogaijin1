package org.uma.jmetal.algorithm.multiobjective.mymohea;

import org.uma.jmetal.algorithm.multiobjective.mypso.MOPSODivSubBuilder;
import org.uma.jmetal.algorithm.multiobjective.nsgaii.NSGAIIBuilder;
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
public class MOHEABuilder<S extends Solution<?>> implements AlgorithmBuilder<MOHEA<S>>{


    protected final Problem<S> problem;
    protected int maxIterations;
    protected int populationSize;
    protected CrossoverOperator<S> crossoverOperator;
    protected MutationOperator<S> mutationOperator;
    protected SelectionOperator<List<S>, S> selectionOperator;
    protected SolutionListEvaluator<S> evaluator;
    protected int archiveSize;
    protected int VEGASize;
    private double crossoverRate;
    private double mutationRate;


    private double CrossoverRates4worker;
    private double CrossoverRates4machine;
    private double mutationRate4worker;
    private double mutationRate4machine;

    /**
     * MOHEABuilder constructor
     */
    public MOHEABuilder(Problem<S> problem, CrossoverOperator<S> crossoverOperator,
                        MutationOperator<S> mutationOperator, int archiveSize, int VEGASize) {
        this.problem = problem;
        maxIterations = 3000;
        populationSize = 100;
        this.crossoverOperator = crossoverOperator ;
        this.mutationOperator = mutationOperator ;
        selectionOperator = new BinaryTournamentSelection<S>();
        evaluator = new SequentialSolutionListEvaluator<S>();
        this.archiveSize = archiveSize ;
        this.VEGASize = VEGASize;
    }

    public MOHEABuilder<S> setMaxIterations(int maxIterations) {
        if (maxIterations < 0) {
            throw new JMetalException("maxIterations is negative: " + maxIterations);
        }
        this.maxIterations = maxIterations;

        return this;
    }

    public MOHEABuilder<S> setPopulationSize(int populationSize) {
        if (populationSize < 0) {
            throw new JMetalException("Population size is negative: " + populationSize);
        }

        this.populationSize = populationSize;

        return this;
    }

    public MOHEABuilder<S> setSelectionOperator(SelectionOperator<List<S>, S> selectionOperator) {
        if (selectionOperator == null) {
            throw new JMetalException("selectionOperator is null");
        }
        this.selectionOperator = selectionOperator;

        return this;
    }

    public MOHEABuilder<S> setSolutionListEvaluator(SolutionListEvaluator<S> evaluator) {
        if (evaluator == null) {
            throw new JMetalException("evaluator is null");
        }
        this.evaluator = evaluator;

        return this;
    }

    public MOHEABuilder<S> setArchiveSize(int archiveSize) {
        this.archiveSize = archiveSize ;

        return this;
    }

    public MOHEABuilder<S> setVEGASize(int VEGASize) {
        this.VEGASize = VEGASize;

        return this;
    }

    public MOHEA<S> build() {
        MOHEA<S> algorithm = null ;
        algorithm = new MOHEA<S>(problem, maxIterations, populationSize, crossoverOperator,
                mutationOperator, selectionOperator, evaluator, archiveSize, VEGASize,crossoverRate, mutationRate,CrossoverRates4worker,CrossoverRates4machine,mutationRate4worker,mutationRate4machine);

        return algorithm ;
    }

    public MOHEABuilder setCrossoverRate(double Cross_c) {
        this.crossoverRate = Cross_c;
        return this ;
    }
    public MOHEABuilder setMutationRate(double Mutation_m) {
        this.mutationRate = Mutation_m;
        return this ;
    }

    public MOHEABuilder setCrossoverRates4worker(double CrossoverRates4worker) {
        this.CrossoverRates4worker = CrossoverRates4worker;
        return this ;
    }

    public MOHEABuilder setCrossoverRates4machine(double CrossoverRates4machine) {
        this.CrossoverRates4machine = CrossoverRates4machine;

        return this ;
    }


    public MOHEABuilder setMutationRate4worker(double mutationRate4worker) {
        this.mutationRate4worker = mutationRate4worker;
        return this ;
    }

    public MOHEABuilder setMutationRate4machine(double mutationRate4machine) {
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
