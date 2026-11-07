package org.uma.jmetal.algorithm.myimpl;


import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.Problem;

import java.util.List;

/**
 * Abstract class representing an evolutionary algorithm 只适应于MOHEA
 *
 * @param <S> Solution
 * @param <R> Result
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 */
@SuppressWarnings("serial")
public abstract class AbstractEvolutionaryAlgorithmS<S, R> implements Algorithm<R> {
    protected List<S> population;
    protected Problem<S> problem;

    public List<S> getPopulation() {
        return population;
    }

    public void setPopulation(List<S> population) {
        this.population = population;
    }

    public void setProblem(Problem<S> problem) {
        this.problem = problem;
    }

    public Problem<S> getProblem() {
        return problem;
    }

    protected abstract void initProgress();

    protected abstract void updateProgress();

    protected abstract boolean isStoppingConditionReached();

    protected abstract List<S> createInitialPopulation();

    protected abstract List<S> evaluatePopulation(List<S> population);

    protected abstract List<S> selection(List<S> population,int index);

    protected abstract List<S> reproduction(List<S> population);

    protected abstract List<S> Create_VEGA_Population1(List<S> population);

    protected abstract List<S> merge(List<S> Population1);

    protected abstract List<S> replacement(List<S> population, List<S> offspringPopulation);

    @Override
    public abstract R getResult();

    @Override
    public void run() {
        List<S> offspringPopulation;
        List<S> matingPopulation;
        List<S> VEGA_Population;

        population = createInitialPopulation();
        population = evaluatePopulation(population);

        initProgress();
        int index = 0;
        while (!isStoppingConditionReached()) {

            VEGA_Population = Create_VEGA_Population1(population);
            matingPopulation = merge(VEGA_Population);
            offspringPopulation = reproduction(matingPopulation);
            offspringPopulation = evaluatePopulation(offspringPopulation);
            population = replacement(population, offspringPopulation);
            matingPopulation = merge(population);
            matingPopulation = selection(matingPopulation,index);
//            population = merge(population);
//            selection(matingPopulation);
            index++;
            updateProgress();

        }
        //System.out.println();
    }
}
