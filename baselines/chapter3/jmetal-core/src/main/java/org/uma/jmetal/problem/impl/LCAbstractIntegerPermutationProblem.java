package org.uma.jmetal.problem.impl;

import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;
import org.uma.jmetal.solution.impl.LCDefaultIntegerPermutationSolution;

@SuppressWarnings("serial")
public abstract class LCAbstractIntegerPermutationProblem
    extends AbstractGenericProblem<PermutationSolution<Integer>> implements
    PermutationProblem<PermutationSolution<Integer>> {

  private int numberOfFactories = 3 ; //TODO 为什么设定为3？
  /* Getters */
  @Override
  public int getNumberOfFactories() {
    return numberOfFactories ;
  }
  /* Setters */
  protected void setNumberOfFactories(int numberOfFactories) {
    this.numberOfFactories = numberOfFactories;
  }
  @Override
  public PermutationSolution<Integer> createSolution() {
    return new LCDefaultIntegerPermutationSolution(this) ;
  }
}
