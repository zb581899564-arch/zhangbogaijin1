package org.uma.jmetal.solution;

import java.util.List;

/**
 * Interface representing permutation based solutions
 *
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 */
public interface PermutationSolution<T> extends Solution<T> {



    T getVariableValueid(int index) ;
    List<T> getVariablesid() ;   //  工厂向量

    void setVariableValueid(int index, T value) ;  //工厂向量赋值
    //String getVariableValueidString(int index) ;

    int getNumberOfVariablesid() ;   //向量位数


    List<T> getVariablesworker();  //工人向量

    int getNumberOfVariablesworker();

    void setVariableValueworker(int index , T value);

    T getVariableValueworker(int index);  //工人向量




/*    //自己加的
    T getVariableValue(int index) ;
    List<T> getVariables() ;   //  工件向量
    void setVariableValue(int index, T value) ;
    //String getVariableValueString(int index) ;

    int getNumberOfVariables() ;   // 向量位数*/

}
