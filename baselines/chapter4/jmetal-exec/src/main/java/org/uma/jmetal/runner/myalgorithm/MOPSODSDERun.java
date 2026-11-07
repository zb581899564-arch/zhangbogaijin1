//package org.uma.jmetal.runner.myalgorithm;
//
//import org.uma.jmetal.algorithm.Algorithm;
//import org.uma.jmetal.algorithm.multiobjective.mypso.MOPSODivSubDEBuilder;
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
// * Class for configuring and running the MOPSODivideSubgroup algorithm
// *
// * @author Antonio J. Nebro <antonio@lcc.uma.es>
// */
//
//
//public class MOPSODSDERun extends AbstractAlgorithmRunner {
//
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
//            for (int i = 0; i < 30; i++) {
//        PermutationProblem<PermutationSolution<Integer>> problem;
//        Algorithm<List<PermutationSolution<Integer>>> algorithm;
//
//        String referenceParetoFront = "";
//
//        String problemName;
//        if (args.length == 1) {
//            problemName = args[0];
//        } else if (args.length == 2) {
//            problemName = args[0];
//            referenceParetoFront = args[1];
//        } else {
//            problemName = "org.uma.jmetal.problem.multiobjective.dfsp.DFSP9";
//            referenceParetoFront = "jmetal-problem/src/test/resources/pareto_fronts/DFSP/DFSP9.pf";
//        }
//
//        //   problem  = new TestFSP();
//        //   problem  = new FSP();
//             problem = new DFSP2();
//
//        int upSize = 15;
//        int centralSize = 10;
//        int downSize = 15;
//        double Probability = 0.4;
//
//        algorithm = new MOPSODivSubDEBuilder(problem, upSize, centralSize, downSize, Probability)
//                .setMaxIterations(20000)
//                .setSwarmSize(40)
//                .build();
//
//        AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm)
//                .execute();
//
//        List<PermutationSolution<Integer>> population = (algorithm).getResult();
//
//        UtilDominationRelationship A = new UtilDominationRelationship();
//       // A.shuchu(population,"主算法");//输出精英解到问题文件
//
///*
//        long computingTime = algorithmRunner.getComputingTime();
//
//        JMetalLogger.logger.info("Total execution time: " + computingTime + "ms");
//
//        printFinalSolutionSet(population);
//        if (!referenceParetoFront.equals("")) {
//            printQualityIndicatorstest(population, referenceParetoFront, "MOPSODSDE");
//        }
//
// */
//
//
//        System.out.println("第"+i+"次结束");
//            }
//    }
//}
