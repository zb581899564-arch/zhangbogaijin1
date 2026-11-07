//package org.uma.jmetal.runner.myalgorithm;
//
//import org.uma.jmetal.algorithm.multiobjective.mymoead.AbstractMOEADS;
//import org.uma.jmetal.algorithm.multiobjective.mymoead.MOEADBuilderS;
//import org.uma.jmetal.operator.MutationOperator;
//import org.uma.jmetal.operator.impl.crossover.DifferentialEvolutionCrossoverS;
//import org.uma.jmetal.operator.impl.mutation.PermutationSwapMutation;
//import org.uma.jmetal.problem.PermutationProblem;
//import org.uma.jmetal.problem.multiobjective.dfsp.*;
//import org.uma.jmetal.runner.lc_psode.UtilDominationRelationship;
//import org.uma.jmetal.solution.PermutationSolution;
//import org.uma.jmetal.util.AbstractAlgorithmRunner;
//import org.uma.jmetal.util.AlgorithmRunner;
//import org.uma.jmetal.util.JMetalException;
//
//import java.io.IOException;
//import java.util.List;
//
//public class MOEADRun extends AbstractAlgorithmRunner {
//
//    public static void main(String[] args) throws JMetalException, IOException {
//
//        for (int i = 0; i < 30; i++) {
//
//            PermutationProblem<PermutationSolution<Integer>> problem;
//            AbstractMOEADS algorithm;
//            DifferentialEvolutionCrossoverS crossover;
//            MutationOperator<PermutationSolution<Integer>> mutation;
//
//            String referenceParetoFront = "";
//
//            String problemName;
//            if (args.length == 1) {
//                problemName = args[0];
//            } else if (args.length == 2) {
//                problemName = args[0];
//                referenceParetoFront = args[1];
//            } else {
//                problemName = "org.uma.jmetal.problem.multiobjective.dfsp.DFSP9";
//                referenceParetoFront = "jmetal-problem/src/test/resources/pareto_fronts/DFSP/DFSP9.pf";
//            }
//
//            //    problem = new TestFSP();
//            //    problem = new FSP();
//            problem = new DFSP2();
//
//            double cr = 1.0;
//            double f = 0.5;
//            crossover = new DifferentialEvolutionCrossoverS(0.9);
//
//            double mutationProbability = 1.0 / problem.getNumberOfVariables();
//            mutation = new PermutationSwapMutation<Integer>(mutationProbability);
//
//            algorithm = new MOEADBuilderS(problem, crossover, MOEADBuilderS.Variant.MOEADS)
//                    //    .setCrossover(crossover)
//                    .setMutation(mutation)
//                    .setMaxIterations(30000)
//                    .setPopulationSize(40)
//                    .setResultPopulationSize(40)
//                    .setNeighborhoodSelectionProbability(0.9)
//                    .setMaximumNumberOfReplacedSolutions(2)
//                    .setNeighborSize(5)
//                    .setFunctionType(AbstractMOEADS.FunctionType.TCHE)
//                    .build();
//
//
//            AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm)
//                    .execute();
//
//            List<PermutationSolution<Integer>> population = algorithm.getResult();
//
//            UtilDominationRelationship A = new UtilDominationRelationship();
//            population = A.nondominatecaozuo(population);
//            //A.shuchu(population, "算法6");//输出精英解到问题文件
//
///*
//            long computingTime = algorithmRunner.getComputingTime();
//
//            JMetalLogger.logger.info("Total execution time: " + computingTime + "ms");
//
//            printFinalSolutionSet(population);
//            if (!referenceParetoFront.equals("")) {
//                printQualityIndicatorstest(population, referenceParetoFront, "MOEAD");
//            }
//
// */
//            System.out.println("第"+i+"次结束");
//        }
//    }
//
//}
