package org.uma.jmetal.solution;

import java.io.Serializable;
import java.util.List;
import java.util.Map;

/**
 * Interface representing a Solution
 *
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 * @param <T> Type (Double, Integer, etc.)
 */
public interface Solution<T> extends Serializable {
  void setObjective(int index, double value) ;

  double getObjective(int index) ;

  double[] getObjectives() ;

  T getVariableValue(int index) ;
  List<T> getVariables() ;    //工件向量
  void setVariableValue(int index, T value) ;  //给工件向量赋值
  String getVariableValueString(int index) ;     //  可能得到的是工件序列值



  int getNumberOfVariables() ;
  int getNumberOfObjectives() ;

  Solution<T> copy() ;

  void setAttribute(Object id, Object value) ;
  Object getAttribute(Object id) ;
  
  public Map<Object, Object> getAttributes();



}
