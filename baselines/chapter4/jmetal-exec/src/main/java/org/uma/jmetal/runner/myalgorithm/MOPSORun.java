//package org.uma.jmetal.runner.myalgorithm;
//
//import org.uma.jmetal.algorithm.Algorithm;
//import org.uma.jmetal.algorithm.multiobjective.mypso.MOPSOBuilder;
//import org.uma.jmetal.problem.PermutationProblem;
//import org.uma.jmetal.problem.multiobjective.dfsp.*;
//import org.uma.jmetal.runner.lc_psode.UtilDominationRelationship;
//import org.uma.jmetal.solution.PermutationSolution;
//import org.uma.jmetal.util.AbstractAlgorithmRunner;
//import org.uma.jmetal.util.AlgorithmRunner;
//
//import java.util.List;
//
///**
// * Class for configuring and running the OMOPSO algorithm
// *
// * @author Antonio J. Nebro <antonio@lcc.uma.es>
// */
//
//public class MOPSORun extends AbstractAlgorithmRunner {
//    /**
//     * @param args Command line arguments.
//     * @throws org.uma.jmetal.util.JMetalException
//     * @throws java.io.IOException
//     * @throws SecurityException
//     * Invoking command:
//    java org.uma.jmetal.runner.multiobjective.OMOPSORunner problemName [referenceFront]
//     */
//    public static void main(String[] args) throws Exception {
//
//        for (int i = 0; i < 30; i++) {
//            PermutationProblem<PermutationSolution<Integer>> problem;
//            Algorithm<List<PermutationSolution<Integer>>> algorithm;
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
//            //problem  = new TestFSP();
//            // problem  = new FSP();
//            problem = new DFSP3();
//
//            algorithm = new MOPSOBuilder(problem)
//                    .setMaxIterations(20000)
//                    .setSwarmSize(40)
//                    .setw(0.8)
//                    .build();
//
//            AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm)
//                    .execute();
//
//            List<PermutationSolution<Integer>> population = (algorithm).getResult();
//
//            UtilDominationRelationship A = new UtilDominationRelationship();
//            //A.shuchu(population, "算法2");//输出精英解到问题文件
///*
//            long computingTime = algorithmRunner.getComputingTime();
//
//            JMetalLogger.logger.info("Total execution time: " + computingTime + "ms");
//
//            printFinalSolutionSet(population);
//        if (!referenceParetoFront.equals("")) {
//            printQualityIndicatorstest(population, referenceParetoFront, "MOPSO");
//        }
//
// */
//        System.out.println("第"+i+"次结束");
//        }
//    }
//}
