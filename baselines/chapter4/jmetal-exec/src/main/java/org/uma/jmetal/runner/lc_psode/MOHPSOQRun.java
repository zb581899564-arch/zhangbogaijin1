package org.uma.jmetal.runner.lc_psode;

import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.algorithm.multiobjective.mypso.MOHPSOQBuilder;
import org.uma.jmetal.algorithm.multiobjective.mypso.MOPSODivSubDEBuilder;
import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.AbstractAlgorithmRunner;
import org.uma.jmetal.util.AlgorithmRunner;

import java.util.List;

/**
 * Class for configuring and running the MOPSODivideSubgroup algorithm
 *
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 */


public class MOHPSOQRun extends AbstractAlgorithmRunner {

    private static String algorithmName = new String("MOHPSO-Q");

    public static void mainexe(PermutationProblem<PermutationSolution<Integer>> problem,
                               int numberOfJobs,int numberOfStages, int numberOffactories, int problemId,
                               //int upSize, int centralSize, int downSize,
                               int swarmSize,
                               double rangeOfR1R2,
                               double crossoverRate,double mutationRate,
                               double pmxCrossover,double V1mutationProbability,
                               double DERate,
                               double DEcrossoverRates,double DEmutationRate,
                               int maxIterations,
                               String outputSolutionFolderName, String indexFileName,
                               int runIndex,boolean Nonparametric,double crossoverRates4worker,double crossoverRates4machine,
                               double mutationRate4worker,double mutationRate4machine,int localsearch) throws Exception {
        //public static void mainexe(PermutationProblem<PermutationSolution<Integer>> problem,
        // int numberOfJobs, int numberOfMachines, int snumber,
        // int upSize, int centralSize, int downSize,
        // double Probability, int SwarmSize, int MaxIterations,String datafile, String indexfile) throws Exception {
        if (Nonparametric == false) {
            double avgtime = 0;
            UtilDominationRelationship utilDominationRelationship = new UtilDominationRelationship();     //  对算法结果筛选非支配解，并输出到文件

            //PermutationProblem<PermutationSolution<Integer>> problem;
            Algorithm<List<PermutationSolution<Integer>>> algorithm;

            String referenceParetoFront = "";

            referenceParetoFront = "jmetal-problem/src/test/resources/pareto_fronts/" + problem.getName() + "/" + numberOfJobs + "_" + numberOfStages+ "_" + numberOffactories  + "_" + problemId + "_pareto.txt";
            indexFileName += "indexs.txt";

            //problem = new DFSP3(problemflag, numberOfJobs, numberOfMachines, snumber);
            //problem = new DFSP3(numberOfJobs, numberOfMachines, snumber);

            for (int i = 0; i < runIndex; i++) {
                //algorithm = new MOPSODSDEBuilder(problem, upSize, centralSize, downSize, DERate)
                algorithm = new MOHPSOQBuilder(problem, swarmSize, numberOffactories,DERate, DEcrossoverRates, DEmutationRate,pmxCrossover)
                        .setMaxIterations(maxIterations)
                        .setSwarmSize(swarmSize)
                        .setRand_k(rangeOfR1R2)
                        .setCrossoverRate(crossoverRate)
                        .setMutationRate(mutationRate)
                        .setCrossoverRates4worker(crossoverRates4worker)
                        .setCrossoverRates4machine(crossoverRates4machine)
                        .setMutationRate4worker(mutationRate4worker)
                        .setMutationRate4machine(mutationRate4machine)
                        .setLocalSearch(localsearch)
                        .build();     //大概就是到构造函数处

                AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm)
                        .execute();    //              运行算法主体


                List<PermutationSolution<Integer>> population = (algorithm).getResult();

                //A.shuchu(population, "主算法", problemflag, numberOfJobs, numberOfMachines, snumber);//输出精英解到问题文件


                // A.shuchu(population, "主算法", numberOfJobs, numberOfMachines, snumber, datafile);//输出精英解到问题文件
//                utilDominationRelationship.outputSolution2File(crossoverRate, mutationRate, rangeOfR1R2, pmxCrossover, V1mutationProbability, swarmSize, DERate, DEcrossoverRates, DEmutationRate, population, algorithmName, numberOfJobs, numberOfStages, numberOffactories, problemId, outputSolutionFolderName);
//                utilDominationRelationship.outputSolution2FileNonparametric(crossoverRate, mutationRate, rangeOfR1R2, pmxCrossover, V1mutationProbability, swarmSize, DERate, DEcrossoverRates, DEmutationRate, population, algorithmName, numberOfJobs, numberOfStages, numberOffactories, problemId, outputSolutionFolderName);
                utilDominationRelationship.outputSolution2FileNonparametricnew(crossoverRate, mutationRate, rangeOfR1R2, pmxCrossover, V1mutationProbability, swarmSize, DERate, DEcrossoverRates, DEmutationRate, population, algorithmName, numberOfJobs, numberOfStages, numberOffactories, problemId, outputSolutionFolderName,
                        crossoverRates4worker,crossoverRates4machine,mutationRate4worker,mutationRate4machine,localsearch);


                long computingTime = algorithmRunner.getComputingTime();    //
                avgtime = avgtime + computingTime;

                //sbFileName.append(jobs).append("_").append(machines).append("_").append(snumber).append("-");
                //sbFileName.append(algorithmname).append("_").append(rand_k).append("_").append(swarmsize).append("_").append(DERate).append("_").append(crossoverRate).append("_").append(mutationRate).append(".txt");


                //StringBuffer sb = new StringBuffer();
                //sb.append(numberOfJobs).append("_").append(numberOfMachines).append("_").append(snumber).append("-");
                //sb.append("主算法").append("_").append(rand).append("_").append(SwarmSize).append("_").append(DERate).append("_").append(crossoverRate).append("_").append(mutationRate).append("-");

                StringBuilder sbFileName = new StringBuilder();
                sbFileName.append(numberOfJobs).append("_");
                sbFileName.append(numberOfStages).append("_");
                sbFileName.append(numberOffactories).append("_");
                sbFileName.append(problemId).append("_");
                sbFileName.append(algorithmName).append("_");
                sbFileName.append(rangeOfR1R2).append("_");
                sbFileName.append(pmxCrossover).append("_");   //v1
                sbFileName.append(V1mutationProbability).append("_");    //v1
                sbFileName.append(swarmSize).append("_");
                sbFileName.append(crossoverRate).append("_");
                sbFileName.append(mutationRate).append("_");
                sbFileName.append(DERate).append("_");
                sbFileName.append(DEcrossoverRates).append("_");
                sbFileName.append(DEmutationRate).append("_");
                sbFileName.append(crossoverRates4worker).append("_");
                sbFileName.append(crossoverRates4machine).append("_");
                sbFileName.append(mutationRate4worker).append("_");
                sbFileName.append(mutationRate4machine).append("_");
                sbFileName.append(localsearch);
                sbFileName.append("第").append(i).append("次运行结束");

                System.out.println(sbFileName.toString());
                //System.out.println(rand+"_"+SwarmSize+"_"+Probability+"_"+Cross+"_"+Mutation+"_"+numberOfJobs+"_"+numberOfMachines+"_"+snumber+"_主算法第" + i + "次结束");
                //System.out.println(SwarmSize+"_"+Probability+"_"+numberOfJobs+"_"+numberOfMachines+"_"+snumber+"_主算法第" + i + "次结束");
            }
            avgtime = avgtime / runIndex;
            utilDominationRelationship.outputCPUTime(avgtime, algorithmName, numberOfJobs, numberOfStages, numberOffactories, problemId, outputSolutionFolderName);
        }


        if (Nonparametric == true) {

            double avgtime = 0;
            UtilDominationRelationship utilDominationRelationship = new UtilDominationRelationship();     //  对算法结果筛选非支配解，并输出到文件

            Algorithm<List<PermutationSolution<Integer>>> algorithm;
            String referenceParetoFront = "";
            referenceParetoFront = "jmetal-problem/src/test/resources/pareto_fronts/" + problem.getName() + "/" + numberOfJobs + "_" + numberOfStages+ "_" + numberOffactories + "_"  + problemId + "_pareto.txt";
            indexFileName += "indexs.txt";
            for (int i = 0; i < runIndex; i++) {
                algorithm = new MOHPSOQBuilder(problem, swarmSize, numberOffactories,DERate, DEcrossoverRates, DEmutationRate,pmxCrossover)
                        .setMaxIterations(maxIterations)
                        .setSwarmSize(swarmSize)
                        .setRand_k(rangeOfR1R2)
                        .setCrossoverRate(crossoverRate)
                        .setMutationRate(mutationRate)
                        .setCrossoverRates4worker(crossoverRates4worker)
                        .setCrossoverRates4machine(crossoverRates4machine)
                        .setMutationRate4worker(mutationRate4worker)
                        .setMutationRate4machine(mutationRate4machine)
                        .setLocalSearch(localsearch)
                        .build();     //大概就是到构造函数处

                AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm)
                        .execute();    //              运行算法主体

                List<PermutationSolution<Integer>> population = (algorithm).getResult();
//                System.out.println(population.size());
                utilDominationRelationship.outputSolution2FileNonparametric(crossoverRate, mutationRate, rangeOfR1R2, pmxCrossover, V1mutationProbability, swarmSize, DERate, DEcrossoverRates, DEmutationRate, population, algorithmName, numberOfJobs, numberOfStages, numberOffactories, problemId, outputSolutionFolderName);

                long computingTime = algorithmRunner.getComputingTime();    //
                avgtime = avgtime + computingTime;

                StringBuilder sbFileName = new StringBuilder();
                sbFileName.append(numberOfJobs).append("_");
                sbFileName.append(numberOfStages).append("_");
                sbFileName.append(numberOffactories).append("_");
                sbFileName.append(problemId).append("-");
                sbFileName.append(algorithmName);
/*                sbFileName.append(rangeOfR1R2).append("_");
                sbFileName.append(pmxCrossover).append("_");   //v1
                sbFileName.append(V1mutationProbability).append("_");    //v1
                sbFileName.append(swarmSize).append("_");
                sbFileName.append(crossoverRate).append("_");
                sbFileName.append(mutationRate).append("_");
                sbFileName.append(DERate).append("_");
                sbFileName.append(DEcrossoverRates).append("_");
                sbFileName.append(DEmutationRate);*/
                sbFileName.append("第").append(i).append("次运行结束");

                System.out.println(sbFileName.toString());
                //System.out.println(rand+"_"+SwarmSize+"_"+Probability+"_"+Cross+"_"+Mutation+"_"+numberOfJobs+"_"+numberOfMachines+"_"+snumber+"_主算法第" + i + "次结束");
                //System.out.println(SwarmSize+"_"+Probability+"_"+numberOfJobs+"_"+numberOfMachines+"_"+snumber+"_主算法第" + i + "次结束");
            }
            avgtime = avgtime / runIndex;
            utilDominationRelationship.outputCPUTime(avgtime, algorithmName, numberOfJobs, numberOfStages, numberOffactories, problemId, outputSolutionFolderName);

        }

    }
}
