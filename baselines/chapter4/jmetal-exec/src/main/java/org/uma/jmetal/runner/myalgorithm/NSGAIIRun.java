package org.uma.jmetal.runner.myalgorithm;

import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.algorithm.multiobjective.nsgaii.NSGAIIBuilder;
import org.uma.jmetal.operator.CrossoverOperator;
import org.uma.jmetal.operator.MutationOperator;
import org.uma.jmetal.operator.SelectionOperator;
import org.uma.jmetal.operator.impl.crossover.PMXCrossover;
import org.uma.jmetal.operator.impl.mutation.PermutationSwapMutation;
import org.uma.jmetal.operator.impl.selection.BinaryTournamentSelection;
import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.problem.multiobjective.dfsp.*;
import org.uma.jmetal.runner.lc_psode.UtilDominationRelationship;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.*;
import org.uma.jmetal.util.comparator.RankingAndCrowdingDistanceComparator;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.List;


/**
 * Class to configure and run the NSGA-II algorithm
 *
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 */

public class NSGAIIRun extends AbstractAlgorithmRunner{
    /**
     * @param args Command line arguments.
     * @throws JMetalException
     * @throws FileNotFoundException Invoking command:
     *                               java org.uma.jmetal.runner.multiobjective.NSGAIIRunner problemName [referenceFront]
     */
    public static void main(String[] args) throws JMetalException, IOException {

        for (int i = 0; i < 30; i++) {
            PermutationProblem<PermutationSolution<Integer>> problem;
            Algorithm<List<PermutationSolution<Integer>>> algorithm;
            CrossoverOperator<PermutationSolution<Integer>> crossover;
            MutationOperator<PermutationSolution<Integer>> mutation;
            SelectionOperator<List<PermutationSolution<Integer>>, PermutationSolution<Integer>> selection;

            String referenceParetoFront = "";

            String problemName;
            if (args.length == 1) {
                problemName = args[0];
            } else if (args.length == 2) {
                problemName = args[0];
                referenceParetoFront = args[1];
            } else {
                problemName = "org.uma.jmetal.problem.multiobjective.dfsp.DFSP9";
                referenceParetoFront = "jmetal-problem/src/test/resources/pareto_fronts/DFSP/DFSP9.pf";
            }

            //    problem = new TestFSP();
            //    problem = new FSP();
             problem = new DFSP2();

            crossover = new PMXCrossover(0.9);

            double mutationProbability = 1.0 / problem.getNumberOfVariables();
            mutation = new PermutationSwapMutation<Integer>(mutationProbability);

            selection = new BinaryTournamentSelection<PermutationSolution<Integer>>(new RankingAndCrowdingDistanceComparator<PermutationSolution<Integer>>());

            int populationSize = 40;
            algorithm = new NSGAIIBuilder<PermutationSolution<Integer>>(problem, crossover, mutation, populationSize)
                    .setSelectionOperator(selection)
                    .setMaxEvaluations(20000)  //最大代
                    .build();

            AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm)
                    .execute();

            List<PermutationSolution<Integer>> population = algorithm.getResult();

            UtilDominationRelationship A = new UtilDominationRelationship();
            population = A.nondominatecaozuo(population);
           // A.shuchu(population,"算法4");//输出精英解到问题文件
/*
            long computingTime = algorithmRunner.getComputingTime();

            JMetalLogger.logger.info("Total execution time: " + computingTime + "ms");

            printFinalSolutionSet(population);

        if (!referenceParetoFront.equals("")) {
            printQualityIndicatorstest(population, referenceParetoFront, "NSGAII");
        }

 */
        System.out.println("第"+i+"次结束");
        }
    }
}