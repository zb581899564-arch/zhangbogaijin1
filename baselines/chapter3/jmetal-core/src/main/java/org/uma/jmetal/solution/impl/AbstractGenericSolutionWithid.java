package org.uma.jmetal.solution.impl;

import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;


import javax.crypto.spec.DHGenParameterSpec;
import java.util.*;

/**
 * Abstract class representing a generic solution
 *
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 */
@SuppressWarnings("serial")
public abstract class AbstractGenericSolutionWithid<T, P extends Problem<?>> implements PermutationSolution<T> {
    private double[] objectives;

    private double[] objectives1;
    private List<T> variables;
    private List<T> variablesid;

    private List<T> variablesworker;

    private List<T> variablesmachine;
    protected P problem ;
    protected Map<Object, Object> attributes ;
    /**
     * @deprecated Call {@link JMetalRandom#getInstance()} if you need one.
     */
    @Deprecated
    protected final JMetalRandom randomGenerator ;

    /**
     * Constructor
     */
    protected AbstractGenericSolutionWithid(P problem) {
        this.problem = problem ;
        attributes = new HashMap<>() ;
        randomGenerator = JMetalRandom.getInstance() ;

        objectives = new double[problem.getNumberOfObjectives()] ;
        objectives1 = new double[problem.getNumberOfObjectives()] ;
        variables = new ArrayList<>(problem.getNumberOfVariables()) ;    // 向量大小这么多个空间的列表   存工件
        //variablesDouble = new ArrayList<>(problem.getNumberOfVariables()) ;
        variablesid = new ArrayList<>(problem.getNumberOfVariables()) ;                            // 存工厂
        variablesworker = new ArrayList<>(problem.getNumberOfVariables()) ;                            // 存工人
        variablesmachine = new ArrayList<>();     //存机器

        for (int i = 0; i < problem.getNumberOfVariables(); i++) {
            variables.add(i, null) ;
            variablesid.add(i, null) ;
//            variablesworker.add(i,null);
        }

        //todo
        for (int i = 0; i < problem.getNumberOfVariables(); i++) {  //乘的是阶段数
            variablesmachine.add(i, null) ;
        }

        int workerLength = ((org.uma.jmetal.util.research.InstanceFileProvider) problem)
                .getWorkerVectorLength();
        for (int i = 0; i < workerLength; i++) {
            variablesworker.add(null);
        }

        attributes.put("worker",variablesworker);
        attributes.put("machine",variablesmachine);

    }



    @Override
    public double[] getObjectives() { return objectives ; }

    @Override
    public List<T> getVariables() {
        return variables ;
    }  //工件

    @Override
    public List<T> getVariablesid() {  //工厂
        return variablesid ;
    }
    @Override
    public List<T> getVariablesworker(){  //工人
        return variablesworker;
    }

    public List<T> getVariablesmachine(){  //机器
        return variablesmachine;
    }

    @Override
    public void setAttribute(Object id, Object value) {
        if ("machine".equals(id)) {
            variablesmachine = new ArrayList<>((List<T>) value);
            value = variablesmachine;
        } else if ("worker".equals(id)) {
            variablesworker = new ArrayList<>((List<T>) value);
            value = variablesworker;
        }
        attributes.put(id, value) ;
    }

    @Override
    public Object getAttribute(Object id) { return attributes.get(id) ; }

    @Override
    public void setObjective(int index, double value) {
        objectives[index] = value ;
    }


    @Override
    public double getObjective(int index) {
        return objectives[index];
    }


    @Override
    public T getVariableValue(int index) {
        return variables.get(index);
    }    //工件
    @Override
    public T getVariableValueworker(int index) {
        return variablesworker.get(index);
    }    //工人

    @Override
    public T getVariableValueid(int index) {

        return variablesid.get(index);
    }  //工厂

    public T getVariableValuemachine(int index) {

        return variablesmachine.get(index);
    }  //机器


    @Override
    public void setVariableValue(int index, T value) { variables.set(index, value); }    //工件
    @Override
    public void setVariableValueworker(int index, T value) { variablesworker.set(index, value); }    //工人

    @Override
    public void setVariableValueid(int index, T value) { variablesid.set(index, value); }    //工厂


    public void setVariableValuemachine(int index, T value) { variablesmachine.set(index, value); }    //机器


    @Override
    public int getNumberOfVariables() {
        return variables.size();
    }

    @Override
    public int getNumberOfVariablesid() {
        return variablesid.size();
    }
    public int getNumberOfVariablesworker() {
        return variablesworker.size();
    }

    public int getNumberOfVariablesmachine() {
        return variablesmachine.size();
    }

    @Override
    public int getNumberOfObjectives() {
        return objectives.length;
    }

    protected void initializeObjectiveValues() {
        for (int i = 0; i < problem.getNumberOfObjectives(); i++) {
            objectives[i] = 0.0 ;
        }
    }
    public T getVariableValueDouble(int index) {
        return variables.get(index);
    }
    public void setVariableValueDouble(int index, T value) { variables.set(index, value); }
    @Override
    public String toString() {
        String result = "Variables: " ;
        for (T var : variables) {
            result += "" + var + " " ;
        }

        result += "Variablesid: " ;
        for (T varid : variablesid) {
            result += "" + varid + " " ;
        }

        result += "Variablesworker: " ;
        for (T varid : variablesworker) {
            result += "" + varid + " " ;
        }

        result += "Objectives: " ;
        for (Double obj : objectives) {
            result += "" + obj + " " ;
        }
        result += "\t" ;
        result += "AlgorithmAttributes: " + attributes + "\n" ;

        return result ;
    }

    private boolean equalsIgnoringAttributes(Object o) {
        if (this == o)
            return true;
        if (o == null || getClass() != o.getClass())
            return false;

        AbstractGenericSolutionWithid<?, ?> that = (AbstractGenericSolutionWithid<?, ?>) o;

        if (!Arrays.equals(objectives, that.objectives))
            return false;

        if (!variables.equals(that.variables))
            return false;

        if (!variablesid.equals(that.variablesid))
            return false;

        return true;
    }

    @Override public boolean equals(Object o) {

        if (!this.equalsIgnoringAttributes(o)) {
            return false;
        }

        AbstractGenericSolutionWithid<?, ?> that = (AbstractGenericSolutionWithid<?, ?>) o;
        // avoid recursive infinite comparisons when solution as attribute

        // examples when problems would arise with a simple comparison attributes.equals(that.attributes):
        // if A contains itself as Attribute
        // If A contains B as attribute, B contains A as attribute
        //
        // the following implementation takes care of this by considering solutions as attributes as a special case

        if (attributes.size() != that.attributes.size()) {
            return false;
        }

        for (Object key : attributes.keySet()) {
            Object value      = attributes.get(key);
            Object valueThat  = that.attributes.get(key);

            if (value != valueThat) { // it only makes sense comparing when having different references

                if (value == null) {
                    return false;
                } else if (valueThat == null) {
                    return false;
                } else { // both not null

                    boolean areAttributeValuesEqual;
                    if (value instanceof AbstractGenericSolutionWithid) {
                        areAttributeValuesEqual = ((AbstractGenericSolutionWithid<?, ?>) value).equalsIgnoringAttributes(valueThat);
                    } else {
                        areAttributeValuesEqual = !value.equals(valueThat);
                    }
                    if (!areAttributeValuesEqual) {
                        return false;
                    } // if equal the next attributeValue will be checked
                }
            }
        }

        return true;
    }

    @Override public int hashCode() {
        int result = Arrays.hashCode(objectives);
        result = 31 * result + variables.hashCode();
        result = 31 * result + variablesid.hashCode();
        result = 31 * result + attributes.hashCode();
        return result;
    }
}
