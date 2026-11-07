package org.uma.jmetal.algorithm.multiobjective.spea2;

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

/**
 * @author Juan J. Durillo
 */
public class SPEA2Builder<S extends Solution<?>> implements AlgorithmBuilder<SPEA2<S>> {
  /**
   * SPEA2Builder class
   */
  protected final Problem<S> problem;
  protected int maxIterations;
  protected int populationSize;
  protected CrossoverOperator<S> crossoverOperator;
  protected MutationOperator<S> mutationOperator;
  protected SelectionOperator<List<S>, S> selectionOperator;
  protected SolutionListEvaluator<S> evaluator;
  protected int k ;
  private double crossoverRate;
  private double mutationRate;

  private double CrossoverRates4worker;
  private double CrossoverRates4machine;
  private double mutationRate4worker;
  private double mutationRate4machine;
  /**
   * SPEA2Builder constructor
   */
  public SPEA2Builder(Problem<S> problem, CrossoverOperator<S> crossoverOperator,
      MutationOperator<S> mutationOperator) {
    this.problem = problem;
    maxIterations = 1000;
    populationSize = 100;
    this.crossoverOperator = crossoverOperator ;
    this.mutationOperator = mutationOperator ;
    selectionOperator = new BinaryTournamentSelection<S>();
    evaluator = new SequentialSolutionListEvaluator<S>();
    k = 1 ;
  }

  public SPEA2Builder<S> setMaxIterations(int maxIterations) {
    if (maxIterations < 0) {
      throw new JMetalException("maxIterations is negative: " + maxIterations);
    }
    this.maxIterations = maxIterations;

    return this;
  }

  public SPEA2Builder<S> setPopulationSize(int populationSize) {
    if (populationSize < 0) {
      throw new JMetalException("Population size is negative: " + populationSize);
    }

    this.populationSize = populationSize;

    return this;
  }

  public SPEA2Builder<S> setSelectionOperator(SelectionOperator<List<S>, S> selectionOperator) {
    if (selectionOperator == null) {
      throw new JMetalException("selectionOperator is null");
    }
    this.selectionOperator = selectionOperator;

    return this;
  }

  public SPEA2Builder<S> setSolutionListEvaluator(SolutionListEvaluator<S> evaluator) {
    if (evaluator == null) {
      throw new JMetalException("evaluator is null");
    }
    this.evaluator = evaluator;

    return this;
  }

  public SPEA2Builder<S> setK(int k) {
    this.k = k ;

    return this;
  }

  public SPEA2<S> build() {
    SPEA2<S> algorithm = null ;
    algorithm = new SPEA2<S>(problem, maxIterations, populationSize, crossoverOperator,
          mutationOperator, selectionOperator, evaluator, k,crossoverRate,mutationRate,CrossoverRates4worker,CrossoverRates4machine,mutationRate4worker,mutationRate4machine);
    
    return algorithm ;
  }

  public SPEA2Builder setCrossoverRate(double Cross_c) {
    this.crossoverRate = Cross_c;
    return this ;
  }
  public SPEA2Builder setMutationRate(double Mutation_m) {
    this.mutationRate = Mutation_m;
    return this ;
  }

  public SPEA2Builder setCrossoverRates4worker(double CrossoverRates4worker) {
    this.CrossoverRates4worker = CrossoverRates4worker;
    return this ;
  }

  public SPEA2Builder setCrossoverRates4machine(double CrossoverRates4machine) {
    this.CrossoverRates4machine = CrossoverRates4machine;

    return this ;
  }


  public SPEA2Builder setMutationRate4worker(double mutationRate4worker) {
    this.mutationRate4worker = mutationRate4worker;
    return this ;
  }

  public SPEA2Builder setMutationRate4machine(double mutationRate4machine) {
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
