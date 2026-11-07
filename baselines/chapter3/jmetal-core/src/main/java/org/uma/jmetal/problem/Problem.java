package org.uma.jmetal.problem;

import java.io.Serializable;

/**
 * Interface representing a multi-objective optimization problem
 *
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 *
 * @param <S> Encoding
 */
public interface Problem<S> extends Serializable {
  /* Getters */
  int getNumberOfVariables() ;   // return variables.size();   向量有几个空间  工件数

  int getNumberOfObjectives() ;
  int getNumberOfConstraints() ;


  String getName() ;

  /* Methods */
  void evaluate(S solution) ;   // 具体实现在DFSP3里面
  S createSolution() ;        //
  //S createSolution1() ;
}
