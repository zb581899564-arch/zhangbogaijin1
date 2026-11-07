package org.uma.jmetal.problem;

import org.uma.jmetal.solution.PermutationSolution;

/**
 * Interface representing permutation problems
 *
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 */
public interface PermutationProblem<S extends PermutationSolution<?>> extends Problem<S> {
  public int getPermutationLength() ;   //向量长度
//  public int getfactories() ;
  int getNumberOfFactories() ;    //工厂数量
  

}
