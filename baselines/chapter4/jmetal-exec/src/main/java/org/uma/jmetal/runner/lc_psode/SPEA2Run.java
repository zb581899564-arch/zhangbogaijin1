package org.uma.jmetal.runner.lc_psode;

import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.algorithm.multiobjective.spea2.SPEA2Builder;
import org.uma.jmetal.operator.CrossoverOperator;
import org.uma.jmetal.operator.MutationOperator;
import org.uma.jmetal.operator.SelectionOperator;
import org.uma.jmetal.operator.impl.crossover.PMXCrossover;
import org.uma.jmetal.operator.impl.mutation.PermutationSwapMutation;
import org.uma.jmetal.operator.impl.selection.BinaryTournamentSelection;
import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.AbstractAlgorithmRunner;
import org.uma.jmetal.util.AlgorithmRunner;
import org.uma.jmetal.util.comparator.RankingAndCrowdingDistanceComparator;

import java.util.List;

public class SPEA2Run extends AbstractAlgorithmRunner {
    private static String algorithmName = new String("SPEA2");

    public static void mainexe(PermutationProblem<PermutationSolution<Integer>> problem,
                               int numberOfJobs, int numberOfStages, int numberOffactories, int problemId,
                               //int upSize, int centralSize, int downSize,
                               int swarmSize,
                               double rangeOfR1R2,
                               double crossoverRate,double mutationRate,
                               double pmxCrossover,double V1mutationProbability,
                               double DERate,double DEcrossoverRates,double DEmutationRate,
                               double crossoverRates4worker,double crossoverRates4machine,double mutationRates4worker,double mutationRates4machine,
                               int maxIterations,
                               String outputSolutionFolderName, String indexFileName,
                               int runIndex,boolean Nonparametric) throws Exception {
    //public static void mainexe(PermutationProblem<PermutationSolution<Integer>> problem, int numberOfJobs, int numberOfMachines, int snumber, int upSize, int centralSize, int downSize, double Probability, int SwarmSize, int MaxIterations,String datafile, String indexfile) throws JMetalException, IOException {
        if (Nonparametric == false) {
            double avgtime = 0;
            UtilDominationRelationship utilDominationRelationship = new UtilDominationRelationship();

            //PermutationProblem<PermutationSolution<Integer>> problem;
            Algorithm<List<PermutationSolution<Integer>>> algorithm;
            CrossoverOperator<PermutationSolution<Integer>> crossover;
            MutationOperator<PermutationSolution<Integer>> mutation;
            SelectionOperator<List<PermutationSolution<Integer>>, PermutationSolution<Integer>> selection;

            //problem = new DFSP3(numberOfJobs, numberOfMachines, snumber);

            crossover = new PMXCrossover(pmxCrossover); //TODO check crossover
            double mutationProbability = V1mutationProbability; //TODO check mutation
            //double mutationProbability = 0.3;
            mutation = new PermutationSwapMutation<Integer>(mutationProbability);
            selection = new BinaryTournamentSelection<PermutationSolution<Integer>>(new RankingAndCrowdingDistanceComparator<PermutationSolution<Integer>>());

            String referenceParetoFront = "";

            //referenceParetoFront = "jmetal-problem/src/test/resources/pareto_fronts/"+problem.getName()+"/"+numberOfJobs+"_"+numberOfMachines+"_"+snumber+"_pareto.txt" ;
            //indexfile += "indexs.txt";

            for (int i = 0; i < runIndex; i++) {
                algorithm = new SPEA2Builder<>(problem, crossover, mutation)
                        .setSelectionOperator(selection)
                        .setMaxIterations(maxIterations)
                        .setPopulationSize(swarmSize)
                        .setCrossoverRate(crossoverRate)
                        .setMutationRate(mutationRate)
                        .setCrossoverRates4worker(crossoverRates4worker)
                        .setCrossoverRates4machine(crossoverRates4machine)
                        .setMutationRate4worker(mutationRates4worker)
                        .setMutationRate4machine(mutationRates4machine)
                        .setK(1)
                        .build();

                AlgorithmRunner algorithmRunner = new AlgorithmRunner.Executor(algorithm)
                        .execute();

                List<PermutationSolution<Integer>> population = algorithm.getResult();
                population = utilDominationRelationship.nondominatecaozuo(population);
                //utilDominationRelationship.shuchu(population, "SPEA2", numberOfJobs, numberOfMachines, snumber, datafile);//输出精英解到问题文件
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
                //System.out.println(numberOfJobs+"_"+numberOfMachines+"_"+snumber+"_算法SPEA2第" + i + "次结束");
            }
            avgtime = avgtime / runIndex;
            utilDominationRelationship.outputCPUTime(avgtime, algorithmName, numberOfJobs, numberOfStages, numberOffactories, problemId, outputSolutionFolderName);
        }


        if (Nonparametric == true) {
            double avgtime = 0;
            UtilDominationRelationship utilDominationRelationship = new UtilDominationRelationship();
            Algorithm<List<PermutationSolution<Integer>>> algorithm;
            CrossoverOperator<PermutationSolution<Integer>> crossover;
            MutationOperator<PermutationSolution<Integer>> mutation;
            SelectionOperator<List<PermutationSolution<Integer>>, PermutationSolution<Integer>> selection;

            crossover = new PMXCrossover(pmxCrossover);
            double mutationProbability = V1mutationProbability;
            mutation = new PermutationSwapMutation<Integer>(mutationProbability);
            selection = new BinaryTournamentSelection<PermutationSolution<Integer>>(new RankingAndCrowdingDistanceComparator<PermutationSolution<Integer>>());

            for (int i = 0; i < runIndex; i++) {
                algorithm = new SPEA2Builder<>(problem, crossover, mutation)
                        .setSelectionOperator(selection)
                        .setMaxIterations(maxIterations)
                        .setPopulationSize(swarmSize)
                        .setCrossoverRate(crossoverRate)
                        .setMutationRate(mutationRate)
                        .setCrossoverRates4worker(crossoverRates4worker)
                        .setCrossoverRates4machine(crossoverRates4machine)
                        .setMutationRate4worker(mutationRates4worker)
                        .setMutationRate4machine(mutationRates4machine)
                        .setK(1)
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
                //System.out.println(numberOfJobs+"_"+numberOfMachines+"_"+snumber+"_算法SPEA2第" + i + "次结束");
            }
            avgtime = avgtime / runIndex;
            utilDominationRelationship.outputCPUTime(avgtime, algorithmName, numberOfJobs, numberOfStages, numberOffactories, problemId, outputSolutionFolderName);
        }


    }
}