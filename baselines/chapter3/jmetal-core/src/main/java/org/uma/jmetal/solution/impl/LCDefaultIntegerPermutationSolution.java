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
public class LCDefaultIntegerPermutationSolution                     //编码
    extends AbstractGenericSolutionWithid<Integer, PermutationProblem<?>>
    implements PermutationSolution<Integer> {

  protected int problemflag ;



  /** Constructor */
  public LCDefaultIntegerPermutationSolution(PermutationProblem<?> problem) {
    super(problem);

    List<Integer> randomSequence = new ArrayList<>(problem.getPermutationLength());

    for (int j = 0; j < problem.getPermutationLength(); j++) {
      Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
      int r;
      r = random.nextInt() * j;
      randomSequence.add(r);

    }
    org.uma.jmetal.util.research.runtime.SeededRandom.shuffle(randomSequence);   //  打乱的序列

    for (int i = 0; i < getNumberOfVariables(); i++) {
      setVariableValueDouble(i, randomSequence.get(i)); ;      //工件向量序列
    }


    List<Integer> randomSequence1 = new ArrayList<>(problem.getPermutationLength());
    for (int j = 0; j < problem.getPermutationLength(); j++) {
      randomSequence1.add(j % problem.getNumberOfFactories());       //用于工厂序列
    }   //之前

    org.uma.jmetal.util.research.runtime.SeededRandom.shuffle(randomSequence1);          //  打乱的序列
    for (int i = 0; i < getNumberOfVariablesid(); i++) {
      setVariableValueid(i, randomSequence1.get(i)) ;         //工厂向量序列
    }
  }

  /** Copy Constructor */
  public LCDefaultIntegerPermutationSolution(LCDefaultIntegerPermutationSolution solution) {
    super(solution.problem) ;
    for (int i = 0; i < problem.getNumberOfObjectives(); i++) {
      setObjective(i, solution.getObjective(i)) ;
    }

    for (int i = 0; i < problem.getNumberOfVariables(); i++) {
      setVariableValue(i, solution.getVariableValueDouble(i));          //工件向量
    }

    for (int i = 0; i < problem.getNumberOfVariables(); i++) {
      setVariableValueid(i, solution.getVariableValueid(i));        //工厂向量
    }

    attributes = new HashMap<Object, Object>(solution.attributes) ;
  }


  @Override public String getVariableValueString(int index) {
    return getVariableValueDouble(index).toString();
  }

  @Override
  public LCDefaultIntegerPermutationSolution copy() {
    return new LCDefaultIntegerPermutationSolution(this);
  }
  
	@Override
	public Map<Object, Object> getAttributes() {
		return attributes;
	}

}
