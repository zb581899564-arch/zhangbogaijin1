package org.uma.jmetal.runner.lc_psode;

import org.uma.jmetal.algorithm.multiobjective.mymoead.AbstractMOEADS;
import org.uma.jmetal.algorithm.multiobjective.mymoead.MOEADBuilderS;
import org.uma.jmetal.operator.MutationOperator;
import org.uma.jmetal.operator.impl.crossover.DifferentialEvolutionCrossoverS;
import org.uma.jmetal.operator.impl.mutation.PermutationSwapMutation;
import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.AbstractAlgorithmRunner;
import org.uma.jmetal.util.AlgorithmRunner;

import java.util.List;

public class MOEADRun extends AbstractAlgorithmRunner {
    private static String algorithmName = new String("MOEA-LS");
    public static void mainexe(PermutationProblem<PermutationSolution<Integer>> problem,
                               int numberOfJobs, int numberOfStages, int numberOffactories, int problemId,
                               //int upSize, int centralSize, int downSize,
                               int swarmSize,
                               double rangeOfR1R2,
                               double crossoverRate, double mutationRate,
                               double pmxCrossover, double V1mutationProbability,
                               double DERate, double DEcrossoverRates, double DEmutationRate,
                               int maxIterations,
                               String outputSolutionFolderName, String indexFileName,
                               int runIndex, boolean Nonparametric,double crossoverRates4worker,double crossoverRates4machine,double mutationRates4worker,double mutationRates4machine
                               ) throws Exception {
    //public static void mainexe(PermutationProblem<PermutationSolution<Integer>> problem, int numberOfJobs, int numberOfMachines, int snumber, int upSize, int centralSize, int downSize, double Probability, int SwarmSize, int MaxIterations,String datafile, String indexfile) throws JMetalException, IOException {
        if (Nonparametric == false) {
            double avgtime = 0;
            UtilDominationRelationship utilDominationRelationship = new UtilDominationRelationship();

            // PermutationProblem<PermutationSolution<Integer>> problem;
            AbstractMOEADS algorithm;
            DifferentialEvolutionCrossoverS crossover;
            MutationOperator<PermutationSolution<Integer>> mutation;
            //problem = new MNIFSP(problemflag, numberOfJobs, numberOfMachines, snumber);
            //problem = new DFSP3(numberOfJobs, numberOfMachines, snumber);

            double cr = 1.0;
            double f = 0.5;
            crossover = new DifferentialEvolutionCrossoverS(pmxCrossover); //TODO check crossover 为什么使用这个差分的交叉？？？
            //double mutationProbability = 1.0 / problem.getNumberOfVariables();
            double mutationProbability = V1mutationProbability;
            //double mutationProbability = 0.3;
            mutation = new PermutationSwapMutation<Integer>(mutationProbability);

            String referenceParetoFront = "";

            //referenceParetoFront = "jmetal-problem/src/test/resources/pareto_fronts/"+problem.getName()+"/"+numberOfJobs+"_"+numberOfMachines+"_"+snumber+"_pareto.txt" ;
            //indexfile += "indexs.txt";

            for (int i = 0; i < runIndex; i++) {

                algorithm = new MOEADBuilderS(problem, numberOffactories, crossover, MOEADBuilderS.Variant.MOEADS) //TODO check MOEADS
                        .setMutation(mutation)
                        .setMaxIterations(maxIterations)
                        .setPopulationSize(swarmSize)
                        .setResultPopulationSize(swarmSize)
                        .setNeighborhoodSelectionProbability(0.9) //TODO Check
                        .setMaximumNumberOfReplacedSolutions(2)//TODO Check
                        .setNeighborSize(5)//TODO Check
                        .setCrossoverRate(crossoverRate)
                        .setMutationRate(mutationRate)
                        .setFunctionType(AbstractMOEADS.FunctionType.TCHE)//TODO Check
                        .setCrossoverRates4worker(crossoverRates4worker)
                        .setCrossoverRates4machine(crossoverRates4machine)
                        .setMutationRate4worker(mutationRates4worker)
                        .setMutationRate4machine(mutationRates4machine)
                        .build();

                AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm)
                        .execute();

                List<PermutationSolution<Integer>> population = algorithm.getResult();
                population = utilDominationRelationship.nondominatecaozuo(population);
                //utilDominationRelationship.shuchu(population, "MOEAD", numberOfJobs, numberOfMachines, snumber,datafile);//输出精英解到问题文件

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
                sbFileName.append("第").append(i).append("次运行结束");

                System.out.println(sbFileName.toString());
                //System.out.println(numberOfJobs+"_"+numberOfMachines+"_"+snumber+"_算法MOEAD第" + i + "次结束");
            }
            avgtime = avgtime / runIndex;
            utilDominationRelationship.outputCPUTime(avgtime, algorithmName, numberOfJobs, numberOfStages, numberOffactories, problemId, outputSolutionFolderName);
        }

        if (Nonparametric == true) {
            double avgtime = 0;
            UtilDominationRelationship utilDominationRelationship = new UtilDominationRelationship();
            AbstractMOEADS algorithm;
            DifferentialEvolutionCrossoverS crossover;
            MutationOperator<PermutationSolution<Integer>> mutation;

            double cr = 1.0;
            double f = 0.5;
            crossover = new DifferentialEvolutionCrossoverS(pmxCrossover);
            double mutationProbability = V1mutationProbability;
            mutation = new PermutationSwapMutation<Integer>(mutationProbability);

            for (int i = 0; i < runIndex; i++) {

                algorithm = new MOEADBuilderS(problem, numberOffactories,crossover, MOEADBuilderS.Variant.MOEADS) //TODO check MOEADS
                        .setMutation(mutation)
                        .setMaxIterations(maxIterations)
                        .setPopulationSize(swarmSize)
                        .setResultPopulationSize(swarmSize)
                        .setNeighborhoodSelectionProbability(0.9) //TODO Check
                        .setMaximumNumberOfReplacedSolutions(2)//TODO Check
                        .setNeighborSize(5)//TODO Check
                        .setCrossoverRate(crossoverRate)
                        .setMutationRate(mutationRate)
                        .setFunctionType(AbstractMOEADS.FunctionType.TCHE)//TODO Check
                        .setCrossoverRates4worker(crossoverRates4worker)
                        .setCrossoverRates4machine(crossoverRates4machine)
                        .setMutationRate4worker(mutationRates4worker)
                        .setMutationRate4machine(mutationRates4machine)
                        .build();


                AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm)
                        .execute();

                List<PermutationSolution<Integer>> population = algorithm.getResult();
                population = utilDominationRelationship.nondominatecaozuo(population);

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
            }
            avgtime = avgtime / runIndex;
            utilDominationRelationship.outputCPUTime(avgtime, algorithmName, numberOfJobs, numberOfStages, numberOffactories, problemId, outputSolutionFolderName);
        }


    }
}
