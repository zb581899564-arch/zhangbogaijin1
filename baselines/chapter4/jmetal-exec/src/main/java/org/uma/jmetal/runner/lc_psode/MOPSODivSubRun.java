package org.uma.jmetal.runner.lc_psode;

import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.algorithm.multiobjective.mypso.MOPSODivSubBuilder;
import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.problem.multiobjective.dfsp.*;

import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.AbstractAlgorithmRunner;
import org.uma.jmetal.util.AlgorithmRunner;

import java.util.List;

/**
 * Class for configuring and running the MOPSODivideSubgroup algorithm
 *
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 */

public class MOPSODivSubRun extends AbstractAlgorithmRunner {
    private static String algorithmName = new String("MOPSODS-DE");

    public static void mainexe(PermutationProblem<PermutationSolution<Integer>> problem,
                               int numberOfJobs, int numberOfStages, int numberOffactories, int problemId,
                               //int upSize, int centralSize, int downSize,
                               int swarmSize,
                               double rangeOfR1R2,
                               double crossoverRate,double mutationRate,
                               double pmxCrossover,double V1mutationProbability,
                               double DERate,
                               double DEcrossoverRates,double DEmutationRate,
                               double crossoverRates4worker,double crossoverRates4machine,double mutationRates4worker,double mutationRates4machine,
                               int maxIterations,
                               String outputSolutionFolderName, String indexFileName,
                               int runIndex,boolean Nonparametric) throws Exception {
        //public static void mainexe(int problemflag, int numberOfJobs, int numberOfMachines, int snumber, int upSize, int centralSize, int downSize, double Probability, int SwarmSize, int MaxIterations) throws Exception {
        if (Nonparametric == false) {
        double avgtime = 0;
        UtilDominationRelationship utilDominationRelationship = new UtilDominationRelationship();

        //PermutationProblem<PermutationSolution<Integer>> problem;
        Algorithm<List<PermutationSolution<Integer>>> algorithm;

        for (int i = 0; i < runIndex; i++) {
            algorithm = new MOPSODivSubBuilder(problem, swarmSize,numberOffactories,pmxCrossover)
                    .setRand_k(rangeOfR1R2)
                    .setCrossoverRate(crossoverRate)
                    .setMutationRate(mutationRate)
                    .setMaxIterations(maxIterations)
                    .setSwarmSize(swarmSize)
                    .setCrossoverRates4worker(crossoverRates4worker)
                    .setCrossoverRates4machine(crossoverRates4machine)
                    .setMutationRate4worker(mutationRates4worker)
                    .setMutationRate4machine(mutationRates4machine)
                    .build();
            AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm)
                    .execute();

            List<PermutationSolution<Integer>> population = (algorithm).getResult();
            //A.shuchu(population, "算法1", problemflag, numberOfJobs, numberOfMachines, snumber);//输出精英解到问题文件

            utilDominationRelationship.outputSolution2FileNonparametricnew(crossoverRate, mutationRate, rangeOfR1R2, pmxCrossover, V1mutationProbability,
                    swarmSize, DERate, DEcrossoverRates, DEmutationRate, population, algorithmName, numberOfJobs, numberOfStages, numberOffactories, problemId, outputSolutionFolderName,crossoverRates4worker,crossoverRates4machine, mutationRates4worker,mutationRates4machine,0);
            long computingTime = algorithmRunner.getComputingTime();
            avgtime = avgtime + computingTime;
            StringBuilder sbFileName = new StringBuilder();
            sbFileName.append(numberOfJobs).append("_");
            sbFileName.append(numberOfStages).append("_");
            sbFileName.append(numberOffactories).append("_");
            sbFileName.append(problemId).append("-");
            sbFileName.append(algorithmName).append("_");
            sbFileName.append(rangeOfR1R2).append("_");
            sbFileName.append(pmxCrossover).append("_");   //v1
            sbFileName.append(V1mutationProbability).append("_");    //v1
            sbFileName.append(swarmSize).append("_");
            sbFileName.append(crossoverRate).append("_");
            sbFileName.append(mutationRate).append("_");
            sbFileName.append(DERate).append("_");
            sbFileName.append(DEcrossoverRates).append("_");
            sbFileName.append(DEmutationRate);
            sbFileName.append("第").append(i).append("次运行结束");

            System.out.println(sbFileName.toString());
            //System.out.println(problemflag+"_"+numberOfJobs+"_"+numberOfMachines+"_"+snumber+"_算法1第" + i + "次结束");
        }
        avgtime = avgtime / runIndex;
        utilDominationRelationship.outputCPUTime(avgtime, algorithmName, numberOfJobs, numberOfStages, numberOffactories,problemId, outputSolutionFolderName);
    }


        if (Nonparametric == true) {
            double avgtime = 0;
            UtilDominationRelationship utilDominationRelationship = new UtilDominationRelationship();
            Algorithm<List<PermutationSolution<Integer>>> algorithm;
            for (int i = 0; i < runIndex; i++) {
                algorithm = new MOPSODivSubBuilder(problem, swarmSize,numberOffactories,pmxCrossover)
                        .setRand_k(rangeOfR1R2)
                        .setCrossoverRate(crossoverRate)
                        .setMutationRate(mutationRate)
                        .setMaxIterations(maxIterations)
                        .setSwarmSize(swarmSize)
                        .setCrossoverRates4worker(crossoverRates4worker)
                        .setCrossoverRates4machine(crossoverRates4machine)
                        .setMutationRate4worker(mutationRates4worker)
                        .setMutationRate4machine(mutationRates4machine)
                        .build();
                AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm)
                        .execute();

                List<PermutationSolution<Integer>> population = (algorithm).getResult();

                utilDominationRelationship.outputSolution2FileNonparametricnew(crossoverRate, mutationRate, rangeOfR1R2, pmxCrossover, V1mutationProbability,
                        swarmSize, DERate, DEcrossoverRates, DEmutationRate, population, algorithmName, numberOfJobs, numberOfStages, numberOffactories, problemId, outputSolutionFolderName,crossoverRates4worker,crossoverRates4machine, mutationRates4worker,mutationRates4machine,0);
                long computingTime = algorithmRunner.getComputingTime();
                avgtime = avgtime + computingTime;
                StringBuilder sbFileName = new StringBuilder();
                sbFileName.append(numberOfJobs).append("_");
                sbFileName.append(numberOfStages).append("_");
                sbFileName.append(numberOffactories).append("_");
                sbFileName.append(problemId).append("-");
                sbFileName.append(algorithmName);
                sbFileName.append("第").append(i).append("次运行结束");

                System.out.println(sbFileName.toString());
                //System.out.println(problemflag+"_"+numberOfJobs+"_"+numberOfMachines+"_"+snumber+"_算法1第" + i + "次结束");
            }
            avgtime = avgtime / runIndex;
            utilDominationRelationship.outputCPUTime(avgtime, algorithmName, numberOfJobs, numberOfStages, numberOffactories, problemId, outputSolutionFolderName);
        }


    }
}
