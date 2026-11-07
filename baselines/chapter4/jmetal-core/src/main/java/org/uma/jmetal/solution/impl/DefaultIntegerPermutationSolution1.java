package org.uma.jmetal.solution.impl;

import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;

import java.util.*;

/**
 * Defines an implementation of solution composed of a permuation of integers
 *
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 */
@SuppressWarnings("serial")
public class DefaultIntegerPermutationSolution1                     //编码
    extends AbstractGenericSolutionWithid<Integer, PermutationProblem<?>>
    implements PermutationSolution<Integer> {


  protected int problemflag ;

  //protected int[][] timeMatrix_;     // 时间矩阵（问题集中的内容）
  //protected int[] timeArray1;      //一维时间和
//  protected int[][] jobindex = new int[500][500];



  /** Constructor */
  public DefaultIntegerPermutationSolution1(PermutationProblem<?> problem) {
    super(problem);

    List<Integer> randomSequence = new ArrayList<>(problem.getPermutationLength());
/*    List<Integer> jobArr = new ArrayList<>(problem.getPermutationLength());
    List<Integer> facArrtemp = new ArrayList<>(problem.getPermutationLength());
    List<Integer> facArr = new ArrayList<>(problem.getPermutationLength());
    Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
    for (int i = 0; i < indexArr.length; i++) {
      //randomSequence.add(indexArr[0][i]);
      for(int k = 0;k<indexArr[i].length;k++){
         jobArr.add(indexArr[i][k]);
      }
      int mark = (indexArr[i].length) % 3;
      for(int j = 0; j<indexArr[i].length-mark; j=j+3){
        facArrtemp.add(0);
        facArrtemp.add(1);
        facArrtemp.add(2);
      }
      for(int j = indexArr[i].length-mark; j<indexArr[i].length; j++) {
        facArrtemp.add(r.nextInt(3));
      }
      org.uma.jmetal.util.research.runtime.SeededRandom.shuffle(facArrtemp);        //打乱工厂
      for(int k = 0;k<indexArr[i].length;k++){
        facArr.add(facArrtemp.get(i));
      }
      facArrtemp.clear();
  }

    for (int i = 0; i < getNumberOfVariables(); i++) {
      setVariableValue(i, jobArr.get(i)) ;      //工件向量序列
    }

    for (int i = 0; i < getNumberOfVariablesid(); i++) {
      setVariableValueid(i, facArr.get(i)) ;         //工厂向量序列
    }*/
    /////////////////////////////////////////////////////////

    for (int j = 0; j < problem.getPermutationLength(); j++) {
      randomSequence.add(j); // 有序的序列

    }
    org.uma.jmetal.util.research.runtime.SeededRandom.shuffle(randomSequence);   //  打乱的序列    用于工件

    for (int i = 0; i < getNumberOfVariables(); i++) {
      setVariableValue(i, randomSequence.get(i)) ;      //工件向量序列
    }


    List<Integer> randomSequence1 = new ArrayList<>(problem.getPermutationLength());
/*    for (int j = 0; j < problem.getPermutationLength(); j++) {
      randomSequence1.add(j % problem.getNumberOfFactories());       //用于工厂序列
    }   //之前*/

    for (int j = 0; j < problem.getNumberOfFactories(); j++) {
      randomSequence1.add(j);       //用于工厂序列
    }

/*    for (int j = problem.getNumberOfFactories(); j < 2*problem.getNumberOfFactories(); j++) {
      randomSequence1.add(j);       //用于工厂序列
    }*/

    Random rand=org.uma.jmetal.util.research.runtime.SeededRandom.current();
    for (int j = problem.getNumberOfFactories(); j < getNumberOfVariables(); j++) {
      int f=rand.nextInt(problem.getNumberOfFactories());
      randomSequence1.add(f);       //用于工厂序列
    }

    //org.uma.jmetal.util.research.runtime.SeededRandom.shuffle(randomSequence1);          //  打乱的序列
    for (int i = 0; i < getNumberOfVariablesid(); i++) {
      setVariableValueid(i, randomSequence1.get(i)) ;         //工厂向量序列
    }
  }

  /** Copy Constructor */
  public DefaultIntegerPermutationSolution1(DefaultIntegerPermutationSolution1 solution) {


    super(solution.problem) ;
    for (int i = 0; i < problem.getNumberOfObjectives(); i++) {
      setObjective(i, solution.getObjective(i)) ;
    }

    for (int i = 0; i < problem.getNumberOfVariables(); i++) {
      setVariableValue(i, solution.getVariableValue(i));          //工件向量
    }

    for (int i = 0; i < problem.getNumberOfVariables(); i++) {
      setVariableValueid(i, solution.getVariableValueid(i));        //工厂向量
    }

    for (int i = 0 ; i < problem.getNumberOfVariables();i++){        //工人向量
      setVariableValueworker(i, solution.getVariableValueworker(i));

    }



    attributes = new HashMap<Object, Object>(solution.attributes) ;
  }



  @Override public String getVariableValueString(int index) {
    return getVariableValue(index).toString();
  }

  @Override
  public DefaultIntegerPermutationSolution1 copy() {
    return new DefaultIntegerPermutationSolution1(this);
  }
  
	@Override
	public Map<Object, Object> getAttributes() {
		return attributes;
	}



  //增加的部分（没用到，不需要）
  /*
  @Override
  public Integer getVariableValueid(int index) {
    return variablesid.get(index);
  }

  @Override
  public List<Integer> getVariablesid() {
    return variablesid;
  }

  @Override
  public void setVariableValueid(int index, Integer value) {
    variablesid.set(index, value);
  }

  @Override
  public int getNumberOfVariablesid() {
    return variablesid.size();
  }

   */

}
