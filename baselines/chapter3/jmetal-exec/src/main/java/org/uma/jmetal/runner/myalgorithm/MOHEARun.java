package org.uma.jmetal.runner.myalgorithm;

import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.algorithm.multiobjective.mymohea.MOHEABuilder;
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
import org.uma.jmetal.util.AbstractAlgorithmRunner;
import org.uma.jmetal.util.AlgorithmRunner;
import org.uma.jmetal.util.JMetalException;
import org.uma.jmetal.util.comparator.RankingAndCrowdingDistanceComparator;

import java.io.IOException;
import java.util.List;

public class MOHEARun extends AbstractAlgorithmRunner {

    public static void main(String[] args) throws JMetalException, IOException {

        for (int i = 0; i < 30; i++) {
            PermutationProblem<PermutationSolution<Integer>> problem;
            Algorithm<List<PermutationSolution<Integer>>> algorithm;
            CrossoverOperator<PermutationSolution<Integer>> crossover;
            MutationOperator<PermutationSolution<Integer>> mutation;
            SelectionOperator<List<PermutationSolution<Integer>>, PermutationSolution<Integer>> selection;
            int numberofarchive = 50;
            int VEGAsize = 50;

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

            //  problem = new TestFSP();
            //   problem = new FSP();
            problem = new DFSP2();

            crossover = new PMXCrossover(0.9);

            double mutationProbability = 1.0 / problem.getNumberOfVariables();
            mutation = new PermutationSwapMutation<Integer>(mutationProbability);

            selection = new BinaryTournamentSelection<PermutationSolution<Integer>>(new RankingAndCrowdingDistanceComparator<PermutationSolution<Integer>>());

            //  int populationSize = 50 ;

            algorithm = new MOHEABuilder<>(problem, crossover, mutation, numberofarchive, VEGAsize)
                    .setSelectionOperator(selection)
                    .setMaxIterations(20000)
                    .setPopulationSize(40)
                    .setArchiveSize(10)
                    .setVEGASize(15)
                    .build();

            AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm)
                    .execute();

            List<PermutationSolution<Integer>> population = algorithm.getResult();

            UtilDominationRelationship A = new UtilDominationRelationship();
            population = A.nondominatecaozuo(population);
            //A.shuchu(population, "算法3");//输出精英解到问题文件

/*
            long computingTime = algorithmRunner.getComputingTime();

            JMetalLogger.logger.info("Total execution time: " + computingTime + "ms");
            printFinalSolutionSet(population);
            if (!referenceParetoFront.equals("")) {
                printQualityIndicatorstest(population, referenceParetoFront,"MOHEA");
            }

 */
            System.out.println("第"+i+"次结束");
        }
    }
}
