package org.uma.jmetal.algorithm.multiobjective.mypso;

import org.uma.jmetal.algorithm.impl.AbstractParticleSwarmOptimization;
import org.uma.jmetal.algorithm.multiobjective.mypso.util.Experience;
import org.uma.jmetal.algorithm.multiobjective.mypso.util.ReplayBuffer;
import org.uma.jmetal.algorithm.multiobjective.mypso.util.SO;
import org.uma.jmetal.algorithm.multiobjective.mypso.util.ST;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.problem.multiobjective.dfsp.DHFSP;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;

import java.util.*;
import java.util.stream.Collectors;


/**
 * Class implementing the OMOPSO algorithm
 */

@SuppressWarnings("serial")
public class MOPSODivSubDE extends AbstractParticleSwarmOptimization<PermutationSolution<Integer>, List<PermutationSolution<Integer>>> {
    @Override public void run() {
        throw new UnsupportedOperationException("Historical search implementation is retained for audit; use CanonicalHmopso with RunContext");
    }


    public static List<PermutationSolution<Integer>> GbestsetG1 = new ArrayList<>();
    public static List<PermutationSolution<Integer>> GbestsetG2 = new ArrayList<>();
    public static List<PermutationSolution<Integer>> GbestsetG3 = new ArrayList<>();
    public static List<PermutationSolution<Integer>> GbestsetG4 = new ArrayList<>();

    public static int actionnum = 3;
    public static int indextest;
    private Problem<PermutationSolution<Integer>> problem;
    private final SolutionListEvaluator<PermutationSolution<Integer>> evaluator;

    private int swarmSize;
    private int upSize;
    private int upNewSize;
    private int centralSize;
    private int downSize;

    //    private int archiveSize;
    private int maxIterations;

    private ArrayList<List<PermutationSolution<Integer>>> tempSwarm;
    private List<PermutationSolution<Integer>> globallyOptimalIndividual;

    private List<PermutationSolution<Integer>> groupU1Solution;
    private List<PermutationSolution<Integer>> groupUNewSolution;
    private List<PermutationSolution<Integer>> groupC2Solution;
    private List<PermutationSolution<Integer>> groupD3Solution;

    private ArrayList<List<PermutationSolution<Integer>>> upGroup1Population;
    private ArrayList<List<PermutationSolution<Integer>>> upNewGroup1Population;
    private ArrayList<List<PermutationSolution<Integer>>> centralGroup2Population;
    private ArrayList<List<PermutationSolution<Integer>>> downGroup3Population;

    private List<PermutationSolution<Integer>> upGr1HisOptIndividual;
    private List<PermutationSolution<Integer>> upNewGr1HisOptIndividual;
    private List<PermutationSolution<Integer>> centralGr2HisOptIndividual;
    private List<PermutationSolution<Integer>> downGr3HisOptIndividual;

    private List<PermutationSolution<Integer>> all3GlobalOptIndividuals;

    private double Rand_k;
    private double Cross_c;
    private double Mutation_m;
    private int currentIteration;
    private JMetalRandom randomGenerator;
    private ArrayList<List<Integer>> action;
    private double Qnums;
    private int numberOfFactories;
    private double CrossoverRates4worker;
    private double CrossoverRates4machine;
    private double mutationRate4worker;
    private double mutationRate4machine;
    private int localsearch;
    private double gamma = 0.8, tl = 0.85;//之前是tl=0.85

    private int t = 0;

    /**
     * Constructor
     */
    public MOPSODivSubDE(int factories, double crossoverRate, double mutationRate, double rand_k,
                         Problem<PermutationSolution<Integer>> problem, SolutionListEvaluator<PermutationSolution<Integer>> evaluator,
                         int swarmSize, int maxIterations, int upSize, int centralSize, int downSize, int upNewSize, double DERate, double DEcrossoverRates, double DEmutationRate, double Qnums, double CrossoverRates4worker, double CrossoverRates4machine,
                         double mutationRate4worker, double mutationRate4machine, int localsearch
    ) {
        this.problem = problem;
        this.evaluator = evaluator;

        this.swarmSize = swarmSize;
        this.maxIterations = maxIterations;
        this.numberOfFactories = factories;
        this.upSize = upSize;
        this.upNewSize = upNewSize;
        this.centralSize = centralSize;
        this.downSize = downSize;
        this.Mutation_m = mutationRate;
        this.Cross_c = crossoverRate;
        this.Rand_k = rand_k;
        //     this.archiveSize = archiveSize ;
        this.Qnums = Qnums;
        this.gamma = DEcrossoverRates;
        this.tl = DEmutationRate;
        this.CrossoverRates4worker = CrossoverRates4worker;
        this.CrossoverRates4machine = CrossoverRates4machine;
        this.mutationRate4worker = mutationRate4worker;
        this.mutationRate4machine = mutationRate4machine;
        this.localsearch = localsearch;
        tempSwarm = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);
//        tempSwarm = new ArrayList<List<PermutationSolution<Integer>>>(50);

        globallyOptimalIndividual = new ArrayList<PermutationSolution<Integer>>();

        groupU1Solution = new ArrayList<>(upSize);
        groupUNewSolution = new ArrayList<>(upNewSize);
        groupC2Solution = new ArrayList<>(centralSize);
        groupD3Solution = new ArrayList<>(downSize);

        upGroup1Population = new ArrayList<List<PermutationSolution<Integer>>>(upSize);
        upNewGroup1Population = new ArrayList<List<PermutationSolution<Integer>>>(upNewSize);
        centralGroup2Population = new ArrayList<List<PermutationSolution<Integer>>>(centralSize);
        downGroup3Population = new ArrayList<List<PermutationSolution<Integer>>>(downSize);

        upGr1HisOptIndividual = new ArrayList<PermutationSolution<Integer>>(upSize);
        upNewGr1HisOptIndividual = new ArrayList<PermutationSolution<Integer>>(upNewSize);
        centralGr2HisOptIndividual = new ArrayList<PermutationSolution<Integer>>(centralSize);
        downGr3HisOptIndividual = new ArrayList<PermutationSolution<Integer>>(downSize);
        all3GlobalOptIndividuals = new ArrayList<PermutationSolution<Integer>>(4);

        randomGenerator = JMetalRandom.getInstance();
//        System.out.println("MOPSODivSubDE 构造函数参数：");
//        System.out.println("factories: " + factories);
//        System.out.println("crossoverRate: " + crossoverRate);
//        System.out.println("mutationRate: " + mutationRate);
//        System.out.println("rand_k: " + rand_k);
//        System.out.println("problem: " + problem.getClass().getSimpleName());  // 打印问题类名
//        System.out.println("evaluator: " + evaluator.getClass().getSimpleName());  // 打印评估器类名
//        System.out.println("swarmSize: " + swarmSize);
//        System.out.println("maxIterations: " + maxIterations);
//        System.out.println("upSize: " + upSize);
//        System.out.println("centralSize: " + centralSize);
//        System.out.println("downSize: " + downSize);
//        System.out.println("upNewSize: " + upNewSize);
//        System.out.println("DERate: " + DERate);
//        System.out.println("DEcrossoverRates: " + DEcrossoverRates);
//        System.out.println("DEmutationRate: " + DEmutationRate);
//        System.out.println("Qnums: " + Qnums);
//        System.out.println("CrossoverRates4worker: " + CrossoverRates4worker);
//        System.out.println("CrossoverRates4machine: " + CrossoverRates4machine);
//        System.out.println("mutationRate4worker: " + mutationRate4worker);
//        System.out.println("mutationRate4machine: " + mutationRate4machine);
//        sleep();
    }

    @Override
    protected void initProgress() {
        currentIteration = swarmSize + currentIteration;
        //currentIteration = 1;
        //    crowdingDistance.computeDensityEstimator(leaderArchive.getSolutionList());
    }

    @Override
    protected void updateProgress() {
//        System.out.println(currentIteration);
        currentIteration = currentIteration + swarmSize;
//        currentIteration =  swarmSize;
//        System.out.println(currentIteration);

//        currentIteration = swarmSize;
//        System.out.println(currentIteration);
//        try {
//            Thread.sleep(9999999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
        //currentIteration += 1;
        //   crowdingDistance.computeDensityEstimator(leaderArchive.getSolutionList());
    }

    @Override
    protected boolean isStoppingConditionReached() {
        return currentIteration >= maxIterations;
    }

    @Override
    protected List<PermutationSolution<Integer>> createInitialSwarm() {

        List<PermutationSolution<Integer>> swarm = new ArrayList<>(swarmSize);

        PermutationSolution<Integer> newSolution;

        // for (int i = 0; i < swarmSize/4; i++) {

        // newSolution =  problem.createSolution();
        //Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        //PermutationSolution<Integer> solutionNew  = problem.createSolution();
        //int a, i , j;
/*            PermutationSolution<Integer> solutiontemp = problem.createSolution();
            //List<List<Integer>> t = new ArrayList<>();  //存工厂号下对应的工件序列的下标
            //ArrayList<List<Integer>> N = new ArrayList<>();
            int [][] N= new int[3][newSolution.getNumberOfVariablesid()];

            List<Integer> v = new ArrayList<>();
            //int[] ind = new int[selectFac.size()];     //存工厂号
//对0，1，2工厂的工件顺序排列
            int [][] len=new int[3][1];
            for (int r = 0; r < 3; r++) {
                int h=0;
                for (int y = 0; y < newSolution.getNumberOfVariablesid(); y++) {
                    if (newSolution.getVariableValueid(y) == r) {  //等于工厂号的下标
                        N[r][h]=y;     //等于工厂号的下标
                        h++;
                        //System.out.println(N[r]);
                        // x++;
                    }
                }
                len[r][0]=h;   //工厂的工件个数  0，1，2长度
            }
            int nums = 0;
            int[] flag = new int[3];
            int[] flagBeg = new int[3];
            for (int r = 0; r < 3; r++) {
                for (int y = 0; y < len[r][0]; y++) {
                    int temp1 = newSolution.getVariableValue(N[r][y]);    //工件号
                    solutiontemp.setVariableValue(nums, temp1);
                    //int temp2 =  solution.getVariableValueid(NEW.get(r).get(y));    //工厂号
                    solutiontemp.setVariableValueid(nums, r);
                    //solutionNew.setVariableValueid(nums,solutionNew.getVariableValue(nums));
                    nums++;
                }
                flagBeg[r]=nums-len[r][0];
                flag[r] = nums - 1; //工厂的最后一个下标
            }*/
        //swarm.add(newSolution);
        //}
        Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        for (int k = 0; k < swarmSize; k++) {
            PermutationSolution<Integer> solutionNew = problem.createSolution();

//            for (int i = 0; i < 18; i++) {
//                solutionNew.setVariableValueworker(i,i);   //工人向量
//            }

//            for (int j = 0; j < numberOfFactories; j++) {
//                solutionNew.setVariableValueid(j, j);       //用于工厂序列
//
//                solutionNew.setVariableValueid(j + numberOfFactories, j);
//
//                solutionNew.setVariableValueid(j + 2 * numberOfFactories, j);
//
//            }
////            System.out.println(solutionNew);
////            try {
////                Thread.sleep(99999);
////            } catch (InterruptedException e) {
////                throw new RuntimeException(e);
////            }
//            for (int j = 3 * numberOfFactories; j < solutionNew.getNumberOfVariables(); j++) {
//                int f = A.nextInt(numberOfFactories);
//                solutionNew.setVariableValueid(j, f);       //用于工厂序列
//            }


//            for (int i = 0; i < solutionNew.getNumberOfVariables(); i++) {
//                solutionNew.setVariableValueworker(i,i);
//            }
//            System.out.println(solutionNew);
//sleep();
            swarm.add(solutionNew);

        }
//        System.out.println(swarm);
//        sleep();
//        try {
//            Thread.sleep(99999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
        return swarm;
    }

    @Override
    protected List<PermutationSolution<Integer>> evaluateSwarm(List<PermutationSolution<Integer>> swarm) {
        swarm = evaluator.evaluate(swarm, (Problem<PermutationSolution<Integer>>) problem);

        //currentIteration=currentIteration+swarmSize;
        return swarm;
    }

    @Override
    protected void initializeLeader(List<PermutationSolution<Integer>> swarm) {


        List<Double> aa = new ArrayList<>(swarmSize);
        for (int i = 0; i < swarmSize; i++) {
            double count1 = 0;
            double count2 = 0;
            for (int j = 0; j < swarmSize; j++) {
                if (i != j) {
                    if (swarm.get(i).getObjective(0) <= swarm.get(j).getObjective(0) &&
                            swarm.get(i).getObjective(1) <= swarm.get(j).getObjective(1) &&
                            swarm.get(i).getObjective(2) <= swarm.get(j).getObjective(2)) {
                        count1 = count1 + 1;
                    }
                    if (swarm.get(i).getObjective(0) >= swarm.get(j).getObjective(0) &&
                            swarm.get(i).getObjective(1) >= swarm.get(j).getObjective(1) &&
                            swarm.get(i).getObjective(2) >= swarm.get(j).getObjective(2)) {
                        count2 = count2 + 1;
                    }
                }
            }
            aa.add(count2 + 1 / (count1 + 1));
        }


        // Step 1: Calculate the average value of the list
        double sum = 0;
        for (double num : aa) {
            sum += num;
        }
        double average = sum / aa.size();
        // Step 2 and 3: Find indices of elements that are greater than the average
        List<Integer> indices = new ArrayList<>();
        for (int i = 0; i < aa.size(); i++) {
            if (aa.get(i) > average) {
                indices.add(i); // Add index to the list if element is above average
            }
        }
        for (Integer i : indices) {
            globallyOptimalIndividual.add(tempSwarm.get(i).get(0));
        }


    }

    @Override
    protected void initializeParticlesMemory(List<PermutationSolution<Integer>> swarm) {
        for (int i = 0; i < swarm.size(); i++) {
            ArrayList<PermutationSolution<Integer>> A = new ArrayList<PermutationSolution<Integer>>();
            A.add(swarm.get(i));
            tempSwarm.add(A);
        }
    }

    @Override
    protected void initializeVelocity(List<PermutationSolution<Integer>> swarm) {

    }


    //分群
    protected void updateVelocity(List<PermutationSolution<Integer>> swarm) {

        upGroup1Population.clear();
        upNewGroup1Population.clear();
        centralGroup2Population.clear();
        downGroup3Population.clear();

        groupU1Solution.clear();
        groupUNewSolution.clear();
        groupC2Solution.clear();
        groupD3Solution.clear();

        List<PermutationSolution<Integer>> temp1 = new ArrayList<>(swarmSize);
        List<PermutationSolution<Integer>> temp2 = new ArrayList<>(swarmSize);
        List<PermutationSolution<Integer>> temp3 = new ArrayList<>(swarmSize);
        List<PermutationSolution<Integer>> temp4 = new ArrayList<>(swarmSize);  //新加的，是保存Cost的

        ArrayList<List<PermutationSolution<Integer>>> tempPd1 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);
        ArrayList<List<PermutationSolution<Integer>>> tempPd2 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);
        ArrayList<List<PermutationSolution<Integer>>> tempPd3 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);
        ArrayList<List<PermutationSolution<Integer>>> tempPd4 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);    //新加的，是保存Cost的

        for (int i = 0; i < swarmSize; i++) {
            temp1.add((PermutationSolution<Integer>) swarm.get(i).copy());
            temp2.add((PermutationSolution<Integer>) swarm.get(i).copy());
            temp3.add((PermutationSolution<Integer>) swarm.get(i).copy());
            temp4.add((PermutationSolution<Integer>) swarm.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(tempSwarm.get(i).size());
            for (int j = 0; j < tempSwarm.get(i).size(); j++) {

                A.add((PermutationSolution<Integer>) tempSwarm.get(i).get(j).copy());
            }

            tempPd1.add(A);
            tempPd2.add(A);
            tempPd3.add(A);
            tempPd4.add(A);
        }


        //划分sub1  25
        for (int i = 0; i < upSize; i++) {
            int b = 0;
            for (int j = 1; j < temp1.size(); j++) {
                if ((temp1.get(j).getObjective(0) < temp1.get(b).getObjective(0))) {
                    b = j;
                }
            }
            groupU1Solution.add(temp1.get(b));
            upGroup1Population.add(tempPd1.get(b));

            temp1.remove(b);
            tempPd1.remove(b);

        }


        //划分sub2
        List<Double> aa = new ArrayList<>(swarmSize);
        for (int i = 0; i < swarmSize; i++) {
            double count1 = 0;
            double count2 = 0;
            for (int j = 0; j < swarmSize; j++) {
                if (i != j) {
                    if (temp2.get(i).getObjective(0) <= temp2.get(j).getObjective(0) &&
                            temp2.get(i).getObjective(1) <= temp2.get(j).getObjective(1) &&
                            temp2.get(i).getObjective(2) <= temp2.get(j).getObjective(2)) {
                        count1 = count1 + 1;
                    }
                    if (temp2.get(i).getObjective(0) >= temp2.get(j).getObjective(0) &&
                            temp2.get(i).getObjective(1) >= temp2.get(j).getObjective(1) &&
                            temp2.get(i).getObjective(2) >= temp2.get(j).getObjective(2)) {
                        count2 = count2 + 1;
                    }
                }
            }
            aa.add(count2 + 1 / (count1 + 1));
        }

        for (int i = 0; i < centralSize; i++) {
            int b = 0;
            for (int j = 1; j < aa.size(); j++) {
                if (aa.get(j) < aa.get(b)) {
                    b = j;
                }
            }
            groupC2Solution.add(temp2.get(b));
            centralGroup2Population.add(tempPd2.get(b));

            aa.remove(b);
            tempPd2.remove(b);
            temp2.remove(b);
        }


        //划分sub3
        for (int i = 0; i < downSize; i++) {
            int b = 0;
            for (int j = 1; j < temp3.size(); j++) {
                if ((temp3.get(j).getObjective(1) < temp3.get(b).getObjective(1))) {
                    b = j;
                }
            }
            groupD3Solution.add(temp3.get(b));
            downGroup3Population.add(tempPd3.get(b));

            temp3.remove(b);
            tempPd3.remove(b);
        }


        //划分sub4
        for (int i = 0; i < upNewSize; i++) {
            int b = 0;
            for (int j = 1; j < temp4.size(); j++) {
                if ((temp4.get(j).getObjective(2) < temp4.get(b).getObjective(2))) {
                    b = j;
                }
            }
            groupUNewSolution.add(temp4.get(b));
            upNewGroup1Population.add(tempPd4.get(b));

            temp4.remove(b);
            tempPd4.remove(b);
        }


//        select();

    }

    //二元锦标赛法（选三个，取最好）
    //选择Gbest和Pbest
    private void select() {

        upGr1HisOptIndividual.clear();
        upNewGr1HisOptIndividual.clear();
        centralGr2HisOptIndividual.clear();
        downGr3HisOptIndividual.clear();
        all3GlobalOptIndividuals.clear();

        for (int i = 0; i < upSize; i++) {
            int a1 = randomGenerator.nextInt(0, upGroup1Population.get(i).size() - 1);
            int a2 = randomGenerator.nextInt(0, upGroup1Population.get(i).size() - 1);
            int a3 = randomGenerator.nextInt(0, upGroup1Population.get(i).size() - 1);
            int temp = a1;
            if ((upGroup1Population.get(i).get(a1).getObjective(0) >= upGroup1Population.get(i).get(a2).getObjective(0) &&
                    upGroup1Population.get(i).get(a3).getObjective(0) >= upGroup1Population.get(i).get(a2).getObjective(0))
            ) {
                temp = a2;
            }

            if ((upGroup1Population.get(i).get(a1).getObjective(0) >= upGroup1Population.get(i).get(a3).getObjective(0) &&
                    upGroup1Population.get(i).get(a2).getObjective(0) >= upGroup1Population.get(i).get(a3).getObjective(0))
            ) {
                temp = a3;
            }
//            System.out.println(upGroup1Population.get(i).get(temp));
            upGr1HisOptIndividual.add(upGroup1Population.get(i).get(temp));

        }

        for (int i = 0; i < centralSize; i++) {
            int a1 = randomGenerator.nextInt(0, centralGroup2Population.get(i).size() - 1);
            int a2 = randomGenerator.nextInt(0, centralGroup2Population.get(i).size() - 1);
            int a3 = randomGenerator.nextInt(0, centralGroup2Population.get(i).size() - 1);
            int temp = a1;
            List<Double> bb = new ArrayList<>(centralGroup2Population.get(i).size());

            for (int j = 0; j < centralGroup2Population.get(i).size(); j++) {
                double count1 = 0;
                double count2 = 0;
                for (int k = 0; k < centralGroup2Population.get(i).size(); k++) {
                    if (j != k) {
                        if (centralGroup2Population.get(i).get(j).getObjective(0) <= centralGroup2Population.get(i).get(k).getObjective(0) &&
                                centralGroup2Population.get(i).get(j).getObjective(1) <= centralGroup2Population.get(i).get(k).getObjective(1) &&
                                centralGroup2Population.get(i).get(j).getObjective(2) <= centralGroup2Population.get(i).get(k).getObjective(2)

                        ) {
                            count1 = count1 + 1;
                        }
                        if (centralGroup2Population.get(i).get(j).getObjective(0) >= centralGroup2Population.get(i).get(k).getObjective(0) &&
                                centralGroup2Population.get(i).get(j).getObjective(1) >= centralGroup2Population.get(i).get(k).getObjective(1) &&
                                centralGroup2Population.get(i).get(j).getObjective(2) >= centralGroup2Population.get(i).get(k).getObjective(2)) {
                            count2 = count2 + 1;
                        }
                    }
                }
                bb.add(count2 + 1 / (count1 + 1));
            }

            if (bb.get(a1) >= bb.get(a2) && bb.get(a3) >= bb.get(a2)) {
                temp = a2;
            }
            if (bb.get(a1) >= bb.get(a3) && bb.get(a2) >= bb.get(a3)) {
                temp = a3;
            }
            centralGr2HisOptIndividual.add(centralGroup2Population.get(i).get(temp));

        }

        for (int i = 0; i < downSize; i++) {
            int a1 = randomGenerator.nextInt(0, downGroup3Population.get(i).size() - 1);
            int a2 = randomGenerator.nextInt(0, downGroup3Population.get(i).size() - 1);
            int a3 = randomGenerator.nextInt(0, downGroup3Population.get(i).size() - 1);
            int temp = a1;
            if ((downGroup3Population.get(i).get(a1).getObjective(1) >= downGroup3Population.get(i).get(a2).getObjective(1) &&
                    downGroup3Population.get(i).get(a3).getObjective(1) >= downGroup3Population.get(i).get(a2).getObjective(1))
            ) {
                temp = a2;
            }
            if ((downGroup3Population.get(i).get(a1).getObjective(1) >= downGroup3Population.get(i).get(a3).getObjective(1) &&
                    downGroup3Population.get(i).get(a2).getObjective(1) >= downGroup3Population.get(i).get(a3).getObjective(1))
            ) {
                temp = a3;
            }
            downGr3HisOptIndividual.add(downGroup3Population.get(i).get(temp));
        }


        for (int i = 0; i < upNewSize; i++) {
            int a1 = randomGenerator.nextInt(0, upNewGroup1Population.get(i).size() - 1);
            int a2 = randomGenerator.nextInt(0, upNewGroup1Population.get(i).size() - 1);
            int a3 = randomGenerator.nextInt(0, upNewGroup1Population.get(i).size() - 1);
            int temp = a1;
            if ((upNewGroup1Population.get(i).get(a1).getObjective(2) >= upNewGroup1Population.get(i).get(a2).getObjective(2) &&
                    upNewGroup1Population.get(i).get(a3).getObjective(2) >= upNewGroup1Population.get(i).get(a2).getObjective(2))
            ) {
                temp = a2;
            }
            if ((upNewGroup1Population.get(i).get(a1).getObjective(2) >= upNewGroup1Population.get(i).get(a3).getObjective(2) &&
                    upNewGroup1Population.get(i).get(a2).getObjective(2) >= upNewGroup1Population.get(i).get(a3).getObjective(2))
            ) {
                temp = a3;
            }
            upNewGr1HisOptIndividual.add(upNewGroup1Population.get(i).get(temp));
        }

//        System.out.println(indextest++);
//        判断选择全局最优解Gbest
//        把下面部分放到全局搜索里面
//        int a1 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
//        int a2 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
//        int a3 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
//        int temp = a1;
//        if ((globallyOptimalIndividual.get(a1).getObjective(0) >= globallyOptimalIndividual.get(a2).getObjective(0) &&
//                globallyOptimalIndividual.get(a3).getObjective(0) >= globallyOptimalIndividual.get(a2).getObjective(0))
//        ) {
//            temp = a2;
//        }
//
//        if ((globallyOptimalIndividual.get(a1).getObjective(0) >= globallyOptimalIndividual.get(a3).getObjective(0) &&
//                globallyOptimalIndividual.get(a2).getObjective(0) >= globallyOptimalIndividual.get(a3).getObjective(0))
//        ) {
//            temp = a3;
//        }
//        all3GlobalOptIndividuals.add(globallyOptimalIndividual.get(temp));
//
//
//        a1 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
//        a2 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
//        a3 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
//        temp = a1;
//        List<Double> cc = new ArrayList<>(globallyOptimalIndividual.size());
//        for (int i = 0; i < globallyOptimalIndividual.size(); i++) {
//            double count1 = 0;
//            double count2 = 0;
//            for (int j = 0; j < globallyOptimalIndividual.size(); j++) {
//                if (i != j) {
//                    if (globallyOptimalIndividual.get(i).getObjective(0) <= globallyOptimalIndividual.get(j).getObjective(0) &&
//                            globallyOptimalIndividual.get(i).getObjective(1) <= globallyOptimalIndividual.get(j).getObjective(1) &&
//                            globallyOptimalIndividual.get(i).getObjective(2) <= globallyOptimalIndividual.get(j).getObjective(2)) {
//                        count1 = count1 + 1;
//                    }
//                    if (globallyOptimalIndividual.get(i).getObjective(0) >= globallyOptimalIndividual.get(j).getObjective(0) &&
//                            globallyOptimalIndividual.get(i).getObjective(1) >= globallyOptimalIndividual.get(j).getObjective(1) &&
//                            globallyOptimalIndividual.get(i).getObjective(2) >= globallyOptimalIndividual.get(j).getObjective(2)) {
//                        count2 = count2 + 1;
//                    }
//                }
//            }
//            cc.add(count2 + 1 / (count1 + 1));
//        }
//
//        if (cc.get(a1) >= cc.get(a2) && cc.get(a3) >= cc.get(a2)) {
//            temp = a2;
//        }
//        if (cc.get(a1) >= cc.get(a3) && cc.get(a2) >= cc.get(a3)) {
//            temp = a3;
//        }
//        all3GlobalOptIndividuals.add(globallyOptimalIndividual.get(temp));
//
//        a1 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
//        a2 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
//        a3 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
//        temp = a1;
//        if ((globallyOptimalIndividual.get(a1).getObjective(1) >= globallyOptimalIndividual.get(a2).getObjective(1) &&
//                globallyOptimalIndividual.get(a3).getObjective(1) >= globallyOptimalIndividual.get(a2).getObjective(1))
//        ) {
//            temp = a2;
//        }
//
//        if ((globallyOptimalIndividual.get(a1).getObjective(1) >= globallyOptimalIndividual.get(a3).getObjective(1) &&
//                globallyOptimalIndividual.get(a2).getObjective(1) >= globallyOptimalIndividual.get(a3).getObjective(1))
//        ) {
//            temp = a3;
//        }
//        all3GlobalOptIndividuals.add(globallyOptimalIndividual.get(temp));
//
//
//        a1 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
//        a2 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
//        a3 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
//        temp = a1;
//        if ((globallyOptimalIndividual.get(a1).getObjective(2) >= globallyOptimalIndividual.get(a2).getObjective(2) &&
//                globallyOptimalIndividual.get(a3).getObjective(2) >= globallyOptimalIndividual.get(a2).getObjective(2))
//        ) {
//            temp = a2;
//        }
//
//        if ((globallyOptimalIndividual.get(a1).getObjective(2) >= globallyOptimalIndividual.get(a3).getObjective(2) &&
//                globallyOptimalIndividual.get(a2).getObjective(2) >= globallyOptimalIndividual.get(a3).getObjective(2))
//        ) {
//            temp = a3;
//        }
//        all3GlobalOptIndividuals.add(globallyOptimalIndividual.get(temp));


        /*
        //新的判断全局最优
        double object1 = Integer.MAX_VALUE;
        double object2 = Integer.MAX_VALUE;
        double object3 = Integer.MAX_VALUE;
        int temp1 = 0;
        int temp2 = 0;
        int temp3 = 0;
        for (int i = 0; i < globallyOptimalIndividual.size(); i++) {
            if (globallyOptimalIndividual.get(i).getObjective(0)<object1){
                object1=globallyOptimalIndividual.get(i).getObjective(0);
                temp1 = i;
            }
            if (globallyOptimalIndividual.get(i).getObjective(1)<object2){
                object2=globallyOptimalIndividual.get(i).getObjective(1);
                temp2 = i;
            }
            if (globallyOptimalIndividual.get(i).getObjective(2)<object3){
                object3=globallyOptimalIndividual.get(i).getObjective(2);
                temp3 = i;
            }
        }

        all3GlobalOptIndividuals.add(globallyOptimalIndividual.get(temp1));
        all3GlobalOptIndividuals.add(globallyOptimalIndividual.get(temp2));
        all3GlobalOptIndividuals.add(globallyOptimalIndividual.get(temp3));

        List<Double> aa = new ArrayList<>(swarmSize);
        for (int i = 0; i < globallyOptimalIndividual.size(); i++) {
            double count1 = 0;
            double count2 = 0;
            for (int j = 0; j < globallyOptimalIndividual.size(); j++) {
                if (i != j) {
                    if (globallyOptimalIndividual.get(i).getObjective(0) <= globallyOptimalIndividual.get(j).getObjective(0) &&
                            globallyOptimalIndividual.get(i).getObjective(1) <= globallyOptimalIndividual.get(j).getObjective(1) &&
                            globallyOptimalIndividual.get(i).getObjective(2) <= globallyOptimalIndividual.get(j).getObjective(2)) {
                        count1 = count1 + 1;
                    }
                    if (globallyOptimalIndividual.get(i).getObjective(0) >= globallyOptimalIndividual.get(j).getObjective(0) &&
                            globallyOptimalIndividual.get(i).getObjective(1) >= globallyOptimalIndividual.get(j).getObjective(1) &&
                            globallyOptimalIndividual.get(i).getObjective(2) >= globallyOptimalIndividual.get(j).getObjective(2)) {
                        count2 = count2 + 1;
                    }
                }
            }
            aa.add(count2 + 1 / (count1 + 1));
        }

        int minIndex = 0; // 假设第一个元素是最小的
        for (int i = 1; i < aa.size(); i++) {
            if (aa.get(i) < aa.get(minIndex)) {
                minIndex = i; // 更新最小值的下标
            }
        }
        all3GlobalOptIndividuals.add(globallyOptimalIndividual.get(minIndex));*/

    }

    protected PermutationSolution<Integer> actionset(int i){
        if (i==0){

            int a1 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
            int a2 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
            int a3 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
            int temp = a1;
            if ((globallyOptimalIndividual.get(a1).getObjective(0) >= globallyOptimalIndividual.get(a2).getObjective(0) &&
                    globallyOptimalIndividual.get(a3).getObjective(0) >= globallyOptimalIndividual.get(a2).getObjective(0))
            ) {
                temp = a2;
            }

            if ((globallyOptimalIndividual.get(a1).getObjective(0) >= globallyOptimalIndividual.get(a3).getObjective(0) &&
                    globallyOptimalIndividual.get(a2).getObjective(0) >= globallyOptimalIndividual.get(a3).getObjective(0))
            ) {
                temp = a3;
            }
            all3GlobalOptIndividuals.add(globallyOptimalIndividual.get(temp));
            return globallyOptimalIndividual.get(temp);
        } else if (i==1) {
            if (GbestsetG1.size()==0){
                int a1 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
                int a2 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
                int a3 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
                int temp = a1;
                if ((globallyOptimalIndividual.get(a1).getObjective(0) >= globallyOptimalIndividual.get(a2).getObjective(0) &&
                        globallyOptimalIndividual.get(a3).getObjective(0) >= globallyOptimalIndividual.get(a2).getObjective(0))
                ) {
                    temp = a2;
                }

                if ((globallyOptimalIndividual.get(a1).getObjective(0) >= globallyOptimalIndividual.get(a3).getObjective(0) &&
                        globallyOptimalIndividual.get(a2).getObjective(0) >= globallyOptimalIndividual.get(a3).getObjective(0))
                ) {
                    temp = a3;
                }
                GbestsetG1.add(globallyOptimalIndividual.get(temp));
                return globallyOptimalIndividual.get(temp);
            }else {
                double min = Integer.MAX_VALUE;
                PermutationSolution<Integer> temp = null;
                for (int i1 = 0; i1 < GbestsetG1.size(); i1++) {
                    if (GbestsetG1.get(i1).getObjective(0)<min){
                        temp=GbestsetG1.get(i1);
                        min = GbestsetG1.get(i1).getObjective(0);
                    }
                }
                return temp;
            }
        } else if (i==2) {
            if (GbestsetG1.size()==0){
                int a1 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
                int a2 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
                int a3 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
                int temp = a1;
                if ((globallyOptimalIndividual.get(a1).getObjective(0) >= globallyOptimalIndividual.get(a2).getObjective(0) &&
                        globallyOptimalIndividual.get(a3).getObjective(0) >= globallyOptimalIndividual.get(a2).getObjective(0))
                ) {
                    temp = a2;
                }

                if ((globallyOptimalIndividual.get(a1).getObjective(0) >= globallyOptimalIndividual.get(a3).getObjective(0) &&
                        globallyOptimalIndividual.get(a2).getObjective(0) >= globallyOptimalIndividual.get(a3).getObjective(0))
                ) {
                    temp = a3;
                }
                GbestsetG1.add(globallyOptimalIndividual.get(temp));
                return globallyOptimalIndividual.get(temp);
            }else return GbestsetG1.get(GbestsetG1.size()-1);
        }
        return null;
    }

    public double learnG1(int a, double[][] R, double[][] Q, List<PermutationSolution<Integer>> bestsolution, int next1,int group) {
        int[] nw = EDHHFSPW.nw;
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();

        List<Integer> selectFac = new ArrayList<>();


        List<PermutationSolution<Integer>> solutionnext;
        ArrayList<PermutationSolution<Integer>> groupU1Solutionbefore = new ArrayList<>();
        ArrayList<PermutationSolution<Integer>> groupC2Solutionbefore = new ArrayList<>();
        ArrayList<PermutationSolution<Integer>> groupD3Solutionbefore = new ArrayList<>();
        ArrayList<PermutationSolution<Integer>> groupUNewSolutionbefore = new ArrayList<>();
        if (group==1){
            PermutationSolution<Integer> action = actionset(a);
            GbestsetG1.add(action);
            for (int i = 0; i < groupU1Solution.size(); i++) {
                groupU1Solutionbefore.add(groupU1Solution.get(i));
            }
//        System.out.println(groupU1Solutionbefore+"groupU1Solutionbefore");
            G1PSO(random,nw,action,group);//进行粒子群进化并将结果写进groupU1Solution
            evaluateSwarm(groupU1Solution);

//        System.out.println(groupU1Solution+"groupU1Solution");

            double distance = 0.0;
            for (int i = 0; i < groupU1Solution.size(); i++) {
                double objectivebefore = groupU1Solutionbefore.get(i).getObjective(0);
                double objectivenext = groupU1Solution.get(i).getObjective(0);
                double distance0fobjective = objectivenext - objectivebefore;
                distance = distance + distance0fobjective;
            }
//        System.out.println(distance+"dis");

            double reward = R[next1][a];
            double Qvalue = calculateNewQ(reward, Q[next1][a]);
            Q[next1][a] = Qvalue;
            return distance;
        } else if (group==2) {
            PermutationSolution<Integer> action = actionset(a);
            GbestsetG2.add(action);
            for (int i = 0; i < groupC2Solution.size(); i++) {
                groupC2Solutionbefore.add(groupC2Solution.get(i));
            }
//        System.out.println(groupU1Solutionbefore+"groupU1Solutionbefore");
            G1PSO(random,nw,action,group);//进行粒子群进化并将结果写进groupU1Solution
            evaluateSwarm(groupC2Solution);

//        System.out.println(groupU1Solution+"groupU1Solution");

            double distance = 0.0;
            for (int i = 0; i < groupC2Solution.size(); i++) {
                //todo 下面用归一化对目标值进行修改
                double objective1before = groupC2Solutionbefore.get(i).getObjective(0);
                double objective1next = groupC2Solution.get(i).getObjective(0);
                double objective2before = groupC2Solutionbefore.get(i).getObjective(1);
                double objective2next = groupC2Solution.get(i).getObjective(1);
                double objective3before = groupC2Solutionbefore.get(i).getObjective(2);
                double objective3next = groupC2Solution.get(i).getObjective(2);
                double distance0fobjective1 = objective1next - objective1before;
                distance = ((objective1before-objective1next)/objective1before)+((objective2before-objective2next)/objective2before)+((objective3before-objective3next)/objective3before);

            }
//        System.out.println(distance+"dis");

            double reward = R[next1][a];
            double Qvalue = calculateNewQ(reward, Q[next1][a]);
            Q[next1][a] = Qvalue;
            return distance;

        } else if (group==3) {
            PermutationSolution<Integer> action = actionset(a);
            GbestsetG3.add(action);
            for (int i = 0; i < groupD3Solution.size(); i++) {
                groupD3Solutionbefore.add(groupD3Solution.get(i));
            }
//        System.out.println(groupU1Solutionbefore+"groupU1Solutionbefore");
            G1PSO(random,nw,action,group);//进行粒子群进化并将结果写进groupU1Solution
            evaluateSwarm(groupD3Solution);

//        System.out.println(groupU1Solution+"groupU1Solution");

            double distance = 0.0;
            for (int i = 0; i < groupD3Solution.size(); i++) {
                double objectivebefore = groupD3Solutionbefore.get(i).getObjective(1);
                double objectivenext = groupD3Solution.get(i).getObjective(1);
                double distance0fobjective = objectivenext - objectivebefore;
                distance = distance + distance0fobjective;
            }
//        System.out.println(distance+"dis");

            double reward = R[next1][a];
            double Qvalue = calculateNewQ(reward, Q[next1][a]);
            Q[next1][a] = Qvalue;
            return distance;

        } else if (group==4) {
            PermutationSolution<Integer> action = actionset(a);
            GbestsetG4.add(action);
            for (int i = 0; i < groupUNewSolution.size(); i++) {
                groupUNewSolutionbefore.add(groupUNewSolution.get(i));
            }
//        System.out.println(groupU1Solutionbefore+"groupU1Solutionbefore");
            G1PSO(random,nw,action,group);//进行粒子群进化并将结果写进groupU1Solution
            evaluateSwarm(groupUNewSolution);

//        System.out.println(groupU1Solution+"groupU1Solution");

            double distance = 0.0;
            for (int i = 0; i < groupUNewSolution.size(); i++) {
                double objectivebefore = groupUNewSolutionbefore.get(i).getObjective(2);
                double objectivenext = groupUNewSolution.get(i).getObjective(2);
                double distance0fobjective = objectivenext - objectivebefore;
                distance = distance + distance0fobjective;
            }
//        System.out.println(distance+"dis");

            double reward = R[next1][a];
            double Qvalue = calculateNewQ(reward, Q[next1][a]);
            Q[next1][a] = Qvalue;
            return distance;

        }

return 0;

    }

    public double calculateG1Q1(double[][] R, double[][] Q, int a, int next1, int Qiannext, double distance) {
        // return (r + rew * q);
        //double reward= R[Qiannext][a];
        double reward = distance;
        Q[Qiannext][a] = reward + gamma * maxNextQ(Q[next1]);
        //Q[Qiannext][a] = (1-alpha) * Q[Qiannext][a] + alpha * (reward+ gamma * maxNextQ(Q[next1]));
        return Q[Qiannext][a];
    }

    @Override
    protected void updatePosition(List<PermutationSolution<Integer>> swarm) {
//        System.out.println(groupU1Solution);
//        System.out.println(upGr1HisOptIndividual);
//
//        System.out.println(all3GlobalOptIndividuals);
//        sleep();

        select();
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        double r1, r2;
        double c, m;
        double c_worker;
        double c_machine;
        double m_worker;
        double m_machine;
        int[] nw = DHFSP.nw;
        int group;
        //针对G1调用learn方法


        int QN = (int) Qnums;

        double[][] Q1 = new double[2][actionnum];
        double[][] R1 = new double[2][actionnum];
        for (int j = 0; j < actionnum; j++) {
            Q1[0][j] = 0;
            Q1[1][j] = 0;
        }

        for (int j = 0; j < actionnum; j++) {
            R1[0][j] = 1;
            R1[1][j] = 1;
        }
        int next = 0;
        int actionIndex;
        List<PermutationSolution<Integer>> getswarm1 = null;
        double old0, old1, new0, new1;
        double[] max1 = new double[QN];
        List<List<PermutationSolution<Integer>>> temp1 = new ArrayList<>(QN);
        group=1;
        for (int i = 0; i < QN; i++) {
            double p = random.nextDouble();
            ArrayList<PermutationSolution<Integer>> permutationSolutioncurrent = new ArrayList<>();
            for (int i1 = 0; i1 < groupU1Solution.size(); i1++) {
                permutationSolutioncurrent.add(groupU1Solution.get(i1));
            }
            double[][] currentState = Q1.clone(); // 当前状态
            double currentReward = 0; // 当前奖励
            if (i == 0) {
                actionIndex = random.nextInt(actionnum);
                double distance = learnG1(actionIndex, R1, Q1, groupU1Solution, next,group);
                int Qiannext = next;
                if (distance < 0.0) next = 0;
                else next = 1;
                Q1[Qiannext][actionIndex] = calculateG1Q1(R1, Q1, actionIndex, next, Qiannext, distance);
            } else {
                if (p < 1 - tl) {
                    actionIndex = random.nextInt(actionnum);
                    double distance = learnG1(actionIndex, R1, Q1, groupU1Solution, next,group);
                    int Qiannext = next;
                    if (distance < 0) next = 0;
                    else next = 1;
                    Q1[Qiannext][actionIndex] = calculateG1Q1(R1, Q1, actionIndex, next, Qiannext, distance);
                } else {
//                    actionIndex = getMaxQ(Q);
                    actionIndex = max(Q1[next]);
                    double distance = learnG1(actionIndex, R1, Q1, groupU1Solution, next,group);
                    int Qiannext = next;
                    if (distance < 0.0) next = 0;
                    else next = 1;
                    Q1[Qiannext][actionIndex] = calculateG1Q1(R1, Q1, actionIndex, next, Qiannext, distance);

                    // Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                }

            }
            double distance=0;
            for (int j = 0; j < groupU1Solution.size(); j++) {
                double objectivebefore = permutationSolutioncurrent.get(j).getObjective(0);
                double objectivenext = groupU1Solution.get(j).getObjective(0);
                double distance0fobjective = objectivenext - objectivebefore;
                distance = distance + distance0fobjective;
            }
            max1[i] = distance;
            List<PermutationSolution<Integer>> temp = new ArrayList();
            for (int i1 = 0; i1 < groupU1Solution.size(); i1++) {
                temp.add(groupU1Solution.get(i1));
            }
            temp1.add(i, temp);

//            for (double[] doubles : Q1) {
//                System.out.println(Arrays.toString(doubles));
//            }
//            System.out.println("902行");
//            System.out.println(groupU1Solution);
//            groupU1Solution = temp.get(best);
//            System.out.println(groupU1Solution);


//            groupU1Solution.set(i,swarmtemp.get(i));
            //swarmtemp.add(getswarm1);
        }
        int best = 0;
        for (int y = 1; y < QN; y++) {
            if (max1[best] < max1[y]) {
                best = y;
            }
        }
        for (int i = 0; i < upSize; i++) {
            groupU1Solution.set(i,temp1.get(best).get(i));
        }
//        sleep();


        double[][] Q2 = new double[2][actionnum];
        double[][] R2 = new double[2][actionnum];

        for (int j = 0; j < actionnum; j++) {
            Q2[0][j] = 0;
            Q2[1][j] = 0;
        }

        for (int j = 0; j < actionnum; j++) {
            R2[0][j] = 1;
            R2[1][j] = 1;
        }

        next = 0;
        double[] max2 = new double[QN];
        List<List<PermutationSolution<Integer>>> temp2 = new ArrayList<>(QN);
        group=2;
        for (int i = 0; i < QN; i++) {
            double p = random.nextDouble();
            ArrayList<PermutationSolution<Integer>> permutationSolutioncurrent = new ArrayList<>();
            for (int i1 = 0; i1 < groupC2Solution.size(); i1++) {
                permutationSolutioncurrent.add(groupC2Solution.get(i1));
            }
            double[][] currentState = Q1.clone(); // 当前状态
            double currentReward = 0; // 当前奖励
            if (i == 0) {
                actionIndex = random.nextInt(actionnum);
                double distance = learnG1(actionIndex, R1, Q1, groupC2Solution, next,group);
                int Qiannext = next;
                if (distance < 0.0) next = 0;
                else next = 1;
                Q1[Qiannext][actionIndex] = calculateG1Q1(R1, Q1, actionIndex, next, Qiannext, distance);
            } else {
                if (p < 1 - tl) {
                    actionIndex = random.nextInt(actionnum);
                    double distance = learnG1(actionIndex, R1, Q1, groupC2Solution, next,group);
                    int Qiannext = next;
                    if (distance < 0) next = 0;
                    else next = 1;
                    Q1[Qiannext][actionIndex] = calculateG1Q1(R1, Q1, actionIndex, next, Qiannext, distance);
                } else {
//                    actionIndex = getMaxQ(Q);
                    actionIndex = max(Q1[next]);
                    double distance = learnG1(actionIndex, R1, Q1, groupC2Solution, next,group);
                    int Qiannext = next;
                    if (distance < 0.0) next = 0;
                    else next = 1;
                    Q1[Qiannext][actionIndex] = calculateG1Q1(R1, Q1, actionIndex, next, Qiannext, distance);

                    // Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                }

            }
            double distance=0;
            for (int j = 0; j < groupC2Solution.size(); j++) {
                //todo 下面要改
                double objectivebefore = permutationSolutioncurrent.get(j).getObjective(1);
                double objectivenext = groupC2Solution.get(j).getObjective(1);
                double distance0fobjective = objectivenext - objectivebefore;
                distance = distance + distance0fobjective;
            }
            max2[i] = distance;
            List<PermutationSolution<Integer>> temp = new ArrayList();
            for (int i1 = 0; i1 < groupC2Solution.size(); i1++) {
                temp.add(groupC2Solution.get(i1));
            }
            temp2.add(i, temp);
//            for (double[] doubles : Q1) {
//                System.out.println(Arrays.toString(doubles));
//            }
//            System.out.println("902行");
//            System.out.println(groupU1Solution);
//            groupU1Solution = temp.get(best);
//            System.out.println(groupU1Solution);


//            groupU1Solution.set(i,swarmtemp.get(i));
            //swarmtemp.add(getswarm1);
        }



        double[][] Q3 = new double[2][actionnum];
        double[][] R3 = new double[2][actionnum];

        for (int j = 0; j < actionnum; j++) {
            Q3[0][j] = 0;
            Q3[1][j] = 0;
        }

        for (int j = 0; j < actionnum; j++) {
            R3[0][j] = 1;
            R3[1][j] = 1;
        }

        next = 0;
        double[] max3 = new double[QN];
        List<List<PermutationSolution<Integer>>> temp3 = new ArrayList<>(QN);
        group=3;
        for (int i = 0; i < QN; i++) {
            double p = random.nextDouble();
            ArrayList<PermutationSolution<Integer>> permutationSolutioncurrent = new ArrayList<>();
            for (int i1 = 0; i1 < groupD3Solution.size(); i1++) {
                permutationSolutioncurrent.add(groupD3Solution.get(i1));
            }
            double[][] currentState = Q1.clone(); // 当前状态
            double currentReward = 0; // 当前奖励
            if (i == 0) {
                actionIndex = random.nextInt(actionnum);
                double distance = learnG1(actionIndex, R1, Q1, groupD3Solution, next,group);
                int Qiannext = next;
                if (distance < 0.0) next = 0;
                else next = 1;
                Q1[Qiannext][actionIndex] = calculateG1Q1(R1, Q1, actionIndex, next, Qiannext, distance);
            } else {
                if (p < 1 - tl) {
                    actionIndex = random.nextInt(actionnum);
                    double distance = learnG1(actionIndex, R1, Q1, groupD3Solution, next,group);
                    int Qiannext = next;
                    if (distance < 0) next = 0;
                    else next = 1;
                    Q1[Qiannext][actionIndex] = calculateG1Q1(R1, Q1, actionIndex, next, Qiannext, distance);
                } else {
//                    actionIndex = getMaxQ(Q);
                    actionIndex = max(Q1[next]);
                    double distance = learnG1(actionIndex, R1, Q1, groupD3Solution, next,group);
                    int Qiannext = next;
                    if (distance < 0.0) next = 0;
                    else next = 1;
                    Q1[Qiannext][actionIndex] = calculateG1Q1(R1, Q1, actionIndex, next, Qiannext, distance);

                    // Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                }

            }
            double distance=0;
            for (int j = 0; j < groupD3Solution.size(); j++) {
                double objectivebefore = permutationSolutioncurrent.get(j).getObjective(1);
                double objectivenext = groupD3Solution.get(j).getObjective(1);
                double distance0fobjective = objectivenext - objectivebefore;
                distance = distance + distance0fobjective;
            }
            max3[i] = distance;
            List<PermutationSolution<Integer>> temp = new ArrayList();
            for (int i1 = 0; i1 < groupD3Solution.size(); i1++) {
                temp.add(groupD3Solution.get(i1));
            }
            temp3.add(i, temp);
//            for (double[] doubles : Q1) {
//                System.out.println(Arrays.toString(doubles));
//            }
//            System.out.println("902行");
//            System.out.println(groupU1Solution);
//            groupU1Solution = temp.get(best);
//            System.out.println(groupU1Solution);


//            groupU1Solution.set(i,swarmtemp.get(i));
            //swarmtemp.add(getswarm1);
        }
        best = 0;
        for (int y = 1; y < QN; y++) {
            if (max1[best] < max1[y]) {
                best = y;
            }
        }
        for (int i = 0; i < downSize; i++) {
            groupD3Solution.set(i,temp3.get(best).get(i));
        }





        double[][] Q4 = new double[2][actionnum];
        double[][] R4 = new double[2][actionnum];

        for (int j = 0; j < actionnum; j++) {
            Q4[0][j] = 0;
            Q4[1][j] = 0;
        }

        for (int j = 0; j < actionnum; j++) {
            R4[0][j] = 1;
            R4[1][j] = 1;
        }

        next = 0;
        double[] max4 = new double[QN];
        List<List<PermutationSolution<Integer>>> temp4 = new ArrayList<>(QN);
        group=4;

        for (int i = 0; i < QN; i++) {
            double p = random.nextDouble();
            ArrayList<PermutationSolution<Integer>> permutationSolutioncurrent = new ArrayList<>();
            for (int i1 = 0; i1 < groupUNewSolution.size(); i1++) {
                permutationSolutioncurrent.add(groupUNewSolution.get(i1));
            }
            double[][] currentState = Q1.clone(); // 当前状态
            double currentReward = 0; // 当前奖励
            if (i == 0) {
                actionIndex = random.nextInt(actionnum);
                double distance = learnG1(actionIndex, R1, Q1, groupUNewSolution, next,group);
                int Qiannext = next;
                if (distance < 0.0) next = 0;
                else next = 1;
                Q1[Qiannext][actionIndex] = calculateG1Q1(R1, Q1, actionIndex, next, Qiannext, distance);
            } else {
                if (p < 1 - tl) {
                    actionIndex = random.nextInt(actionnum);
                    double distance = learnG1(actionIndex, R1, Q1, groupUNewSolution, next,group);
                    int Qiannext = next;
                    if (distance < 0) next = 0;
                    else next = 1;
                    Q1[Qiannext][actionIndex] = calculateG1Q1(R1, Q1, actionIndex, next, Qiannext, distance);
                } else {
//                    actionIndex = getMaxQ(Q);
                    actionIndex = max(Q1[next]);
                    double distance = learnG1(actionIndex, R1, Q1, groupUNewSolution, next,group);
                    int Qiannext = next;
                    if (distance < 0.0) next = 0;
                    else next = 1;
                    Q1[Qiannext][actionIndex] = calculateG1Q1(R1, Q1, actionIndex, next, Qiannext, distance);

                    // Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                }

            }
            double distance=0;
            for (int j = 0; j < groupUNewSolution.size(); j++) {
                double objectivebefore = permutationSolutioncurrent.get(j).getObjective(1);
                double objectivenext = groupUNewSolution.get(j).getObjective(1);
                double distance0fobjective = objectivenext - objectivebefore;
                distance = distance + distance0fobjective;
            }
            max4[i] = distance;
            List<PermutationSolution<Integer>> temp = new ArrayList();
            for (int i1 = 0; i1 < groupUNewSolution.size(); i1++) {
                temp.add(groupUNewSolution.get(i1));
            }
            temp4.add(i, temp);
//            for (double[] doubles : Q1) {
//                System.out.println(Arrays.toString(doubles));
//            }
//            System.out.println("902行");
//            System.out.println(groupU1Solution);
//            groupU1Solution = temp.get(best);
//            System.out.println(groupU1Solution);


//            groupU1Solution.set(i,swarmtemp.get(i));
            //swarmtemp.add(getswarm1);
        }
        best = 0;
        for (int y = 1; y < QN; y++) {
            if (max1[best] < max1[y]) {
                best = y;
            }
        }
        for (int i = 0; i < upNewSize; i++) {
            groupUNewSolution.set(i,temp4.get(best).get(i));
        }






//        sleep();











        //PSO结束
        List<PermutationSolution<Integer>> tempSwarm = new ArrayList<>();
        for (int i = 0; i < swarm.size(); i++) {
            tempSwarm.add(swarm.get(i));
        }
        merge(swarm);
        int[] DEswarmtempPdflag = new int[swarmSize];
        for (int i = 0; i < swarmSize; i++) {
            DEswarmtempPdflag[i] = i;
        }

        swarm = PDDRFFselect(swarm, tempSwarm, DEswarmtempPdflag);


    }

    private void G1PSO(Random random, int[] nw, PermutationSolution<Integer> action,int group) {
        double m_worker;
        double c_worker;
        double r1;
        double m;
        double c;
        double c_machine;
        double r2;
        double m_machine;

        if (group==1){
            for (int i = 0; i < upSize; i++) {

                ArrayList<SO> listV = new ArrayList<>();
                ArrayList<SO> listVa = new ArrayList<>();  //用于工厂向量
                //用于工厂向量的DE交换序
                ArrayList<ST> listV2 = new ArrayList<>(); //用于工厂向量
                //用于工厂向量的变异

                int len = 0;
                int len1 = 0;
                Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
                int i1 = r.nextInt(upSize);
                //选择一个粒子
                PermutationSolution<Integer> particle = (PermutationSolution<Integer>) groupU1Solution.get(i).copy();

                //Parameters for velocity equation
                r1 = random.nextDouble() * Rand_k;
                r2 = random.nextDouble() * Rand_k;  //生成一个0~Rand_k的数
                //

                //自身初速度
                SO s1 = new SO(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1),
                        randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                listV.add(s1);
                addNew4JobSequenceVectorByExchangeSequence(particle, listV);

                //历史最优
                listV.clear();
                ArrayList<SO> vtemp1 = getDifferenceOfJobSequenceVectorByExchangeSequence(upGr1HisOptIndividual.get(i1), particle);
                len = (int) (vtemp1.size() * r1);

                for (int j = 0; j < len; j++) {
                    listV.add(vtemp1.get(j));
                }
                addNew4JobSequenceVectorByExchangeSequence(particle, listV);

                c = random.nextDouble();
                m = random.nextDouble();

                //Cross_c
                if (c < Cross_c) {
                    getCrossOfFactoryVectorBySingle(upGr1HisOptIndividual.get(i1), particle);    //单点交叉
                }

                c_worker = random.nextDouble();
                if (c_worker < CrossoverRates4worker) {
                    crossover4workersequence(upGr1HisOptIndividual.get(i1), particle, nw);//工人向量交叉
                }

                c_machine = random.nextDouble();
                if (c_machine < CrossoverRates4machine) {
                    crossover4machinesequence(upGr1HisOptIndividual.get(i1), particle, nw);//工人向量交叉
                }


                if (m < Mutation_m) {
                    //确定针对工厂向量
                    ST q = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                    listV2.add(q);
                    addNew4FactoryVectorByRandom(particle, listV2);
                }

                m_worker = random.nextDouble();
                if (m_worker < mutationRate4worker) {
                    mutation4worker(particle);
                }

                m_machine = random.nextDouble();
                if (m_machine < mutationRate4machine) {
                    mutation4machine(particle);
                }

                //全局最优
                listV.clear();
                listVa.clear();
                listV2.clear();

                ArrayList<SO> vtemp2 = getDifferenceOfJobSequenceVectorByExchangeSequence(action, particle);
                len = (int) (vtemp2.size() * r2);

                for (int j = 0; j < len; j++) {
                    listV.add(vtemp2.get(j));
                }
                addNew4JobSequenceVectorByExchangeSequence(particle, listV);

                c = random.nextDouble();
                m = random.nextDouble();
                if (c < Cross_c) {
                    getCrossOfFactoryVectorBySingle(action, particle);    //单点交叉
                }
                c_worker = random.nextDouble();
                if (c_worker < CrossoverRates4worker) {
                    crossover4workersequence(action, particle, nw);//工人向量交叉
                }
                c_machine = random.nextDouble();
                if (c_machine < CrossoverRates4machine) {
                    crossover4machinesequence(action, particle, nw);//工人向量交叉
                }
                if (m < Mutation_m) {
                    ST q1 = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                    listV2.add(q1);
                    addNew4FactoryVectorByRandom(particle, listV2);
                }
                m_worker = random.nextDouble();
                if (m_worker < mutationRate4worker) {
                    mutation4worker(particle);
                }
                m_machine = random.nextDouble();
                if (m_machine < mutationRate4machine) {
                    mutation4machine(particle);
                }
                groupU1Solution.set(i, particle);
            }
        }else if (group == 2){
            for (int i = 0; i < centralSize; i++) {
                Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
                int i1 = r.nextInt(centralSize);
                ArrayList<SO> listV = new ArrayList<>();
                ArrayList<SO> listVa = new ArrayList<>();
                ArrayList<ST> listV2 = new ArrayList<>();
                int len = 0;
                int len1 = 0;
                PermutationSolution<Integer> particle = (PermutationSolution<Integer>) groupC2Solution.get(i).copy();

                //Parameters for velocity equation
                r1 = random.nextDouble() * Rand_k;
                r2 = random.nextDouble() * Rand_k;  //生成一个0~Rand_k的数
                //

                //自身初速度
                SO s1 = new SO(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1),
                        randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));

                listV.add(s1);
                addNew4JobSequenceVectorByExchangeSequence(particle, listV);

                //历史最优
                listV.clear();
                listVa.clear();
                listV2.clear();

                ArrayList<SO> vtemp1 = getDifferenceOfJobSequenceVectorByExchangeSequence(centralGr2HisOptIndividual.get(i1), particle);
                len = (int) (vtemp1.size() * r1);

                for (int j = 0; j < len; j++) {
                    listV.add(vtemp1.get(j));
                }
                addNew4JobSequenceVectorByExchangeSequence(particle, listV);

                c = random.nextDouble();
                m = random.nextDouble();
                if (c < Cross_c) {
                    getCrossOfFactoryVectorBySingle(centralGr2HisOptIndividual.get(i1), particle);    //单点交叉
                }
                c_worker = random.nextDouble();
                if (c_worker < CrossoverRates4worker) {
                    crossover4workersequence(centralGr2HisOptIndividual.get(i1), particle, nw);//工人向量交叉
                }
                c_machine = random.nextDouble();
                if (c_machine < CrossoverRates4machine) {
                    crossover4machinesequence(centralGr2HisOptIndividual.get(i1), particle, nw);//工人向量交叉
                }
                if (m < Mutation_m) {
                    ST q = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                    listV2.add(q);
                    addNew4FactoryVectorByRandom(particle, listV2);
                }

                m_worker = random.nextDouble();
                if (m_worker < mutationRate4worker) {
                    mutation4worker(particle);
                }

                m_machine = random.nextDouble();
                if (m_machine < mutationRate4machine) {
                    mutation4machine(particle);
                }

                //全局最优
                listV.clear();
                listVa.clear();
                listV2.clear();

                ArrayList<SO> vtemp2 = getDifferenceOfJobSequenceVectorByExchangeSequence(action, particle);
                len = (int) (vtemp2.size() * r2);

                for (int j = 0; j < len; j++) {
                    listV.add(vtemp2.get(j));
                }
                addNew4JobSequenceVectorByExchangeSequence(particle, listV);

                if (c < Cross_c) {
                    getCrossOfFactoryVectorBySingle(action, particle);    //单点交叉
                }
                c_worker = random.nextDouble();
                if (c_worker < CrossoverRates4worker) {
                    crossover4workersequence(action, particle, nw);//工人向量交叉
                }
                c_machine = random.nextDouble();
                if (c_machine < CrossoverRates4machine) {
                    crossover4machinesequence(action, particle, nw);//工人向量交叉
                }
                if (m < Mutation_m) {
                    ST q1 = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                    listV2.add(q1);
                    addNew4FactoryVectorByRandom(particle, listV2);
                }
                m_worker = random.nextDouble();
                if (m_worker < mutationRate4worker) {
//                mutation4worker(particle);
                }
                m_machine = random.nextDouble();
                if (m_machine < mutationRate4machine) {
                    mutation4machine(particle);
                }
                groupC2Solution.set(i, particle);
            }
        } else if (group == 3) {
            for (int i = 0; i < downSize; i++) {
                Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
                int i1 = r.nextInt(downSize);
                ArrayList<SO> listV = new ArrayList<>();
                ArrayList<SO> listVa = new ArrayList<>();
                ArrayList<ST> listV2 = new ArrayList<>();
                int len = 0;
                int len1 = 0;
                PermutationSolution<Integer> particle = (PermutationSolution<Integer>) groupD3Solution.get(i).copy();

                //Parameters for velocity equation
                r1 = random.nextDouble() * Rand_k;
                r2 = random.nextDouble() * Rand_k;
                //自身初速度
                SO s1 = new SO(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1),
                        randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));

                listV.add(s1);
                addNew4JobSequenceVectorByExchangeSequence(particle, listV);

                //历史最优
                listV.clear();
                listVa.clear();
                listV2.clear();
                ArrayList<SO> vtemp1 = getDifferenceOfJobSequenceVectorByExchangeSequence(downGr3HisOptIndividual.get(i1), particle);
                len = (int) (vtemp1.size() * r1);

                for (int j = 0; j < len; j++) {
                    listV.add(vtemp1.get(j));
                }
                addNew4JobSequenceVectorByExchangeSequence(particle, listV);


                c = random.nextDouble();
                m = random.nextDouble();
                if (c < Cross_c) {
                    getCrossOfFactoryVectorBySingle(downGr3HisOptIndividual.get(i1), particle);    //单点交叉
                }
                c_worker = random.nextDouble();
                if (c_worker < CrossoverRates4worker) {
                    crossover4workersequence(downGr3HisOptIndividual.get(i1), particle, nw);//工人向量交叉
                }
                c_machine = random.nextDouble();
                if (c_machine < CrossoverRates4machine) {
                    crossover4machinesequence(downGr3HisOptIndividual.get(i1), particle, nw);//工人向量交叉
                }
                if (m < Mutation_m) {
                    ST q = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                    listV2.add(q);
                    addNew4FactoryVectorByRandom(particle, listV2);
                }
                m_worker = random.nextDouble();
                if (m_worker < mutationRate4worker) {
                    mutation4worker(particle);
                }
                m_machine = random.nextDouble();
                if (m_machine < mutationRate4machine) {
                    mutation4machine(particle);
                }

                //全局最优
                listV.clear();
                listVa.clear();
                listV2.clear();

                ArrayList<SO> vtemp2 = getDifferenceOfJobSequenceVectorByExchangeSequence(action, particle);
                len = (int) (vtemp2.size() * r2);

                for (int j = 0; j < len; j++) {
                    listV.add(vtemp2.get(j));
                }
                addNew4JobSequenceVectorByExchangeSequence(particle, listV);

                c = random.nextDouble();
                m = random.nextDouble();
                if (c < Cross_c) {
                    getCrossOfFactoryVectorBySingle(action, particle);    //单点交叉
                }
                c_worker = random.nextDouble();
                if (c_worker < CrossoverRates4worker) {
                    crossover4workersequence(action, particle, nw);//工人向量交叉
                }
                c_machine = random.nextDouble();
                if (c_machine < CrossoverRates4machine) {
                    crossover4machinesequence(action, particle, nw);//工人向量交叉
                }
                if (m < Mutation_m) {
                    ST q1 = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                    listV2.add(q1);
                    addNew4FactoryVectorByRandom(particle, listV2);
                }
                m_worker = random.nextDouble();
                if (m_worker < mutationRate4worker) {
                    mutation4worker(particle);
                }
                m_machine = random.nextDouble();
                if (m_machine < mutationRate4machine) {
                    mutation4machine(particle);
                }
//

                groupD3Solution.set(i, particle);
            }
        } else if (group == 4) {
            for (int i = 0; i < upNewSize; i++) {
                Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
                int i1 = r.nextInt(upNewSize);
                ArrayList<SO> listV = new ArrayList<>();
                ArrayList<SO> listVa = new ArrayList<>();
                ArrayList<ST> listV2 = new ArrayList<>();
                int len = 0;
                int len1 = 0;
                PermutationSolution<Integer> particle = (PermutationSolution<Integer>) groupUNewSolution.get(i).copy();

                //Parameters for velocity equation
                r1 = random.nextDouble() * Rand_k;
                r2 = random.nextDouble() * Rand_k;
                //自身初速度
                SO s1 = new SO(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1),
                        randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));

                listV.add(s1);
                addNew4JobSequenceVectorByExchangeSequence(particle, listV);

                //历史最优
                listV.clear();
                listVa.clear();
                listV2.clear();
                ArrayList<SO> vtemp1 = getDifferenceOfJobSequenceVectorByExchangeSequence(upNewGr1HisOptIndividual.get(i1), particle);
                len = (int) (vtemp1.size() * r1);

                for (int j = 0; j < len; j++) {
                    listV.add(vtemp1.get(j));
                }
                addNew4JobSequenceVectorByExchangeSequence(particle, listV);

                c = random.nextDouble();
                m = random.nextDouble();
                if (c < Cross_c) {
                    getCrossOfFactoryVectorBySingle(upNewGr1HisOptIndividual.get(i1), particle);    //单点交叉
                }
                c_worker = random.nextDouble();
                if (c_worker < CrossoverRates4worker) {
                    crossover4workersequence(upNewGr1HisOptIndividual.get(i1), particle, nw);//工人向量交叉
                }
                c_machine = random.nextDouble();
                if (c_machine < CrossoverRates4machine) {
                    crossover4machinesequence(upNewGr1HisOptIndividual.get(i1), particle, nw);//工人向量交叉
                }
                if (m < Mutation_m) {
                    ST q = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                    listV2.add(q);
                    addNew4FactoryVectorByRandom(particle, listV2);
                }
                m_worker = random.nextDouble();
                if (m_worker < mutationRate4worker) {
                    mutation4worker(particle);
                }
                m_machine = random.nextDouble();
                if (m_machine < mutationRate4machine) {
                    mutation4machine(particle);
                }

                //全局最优
                listV.clear();
                listVa.clear();
                listV2.clear();

                ArrayList<SO> vtemp2 = getDifferenceOfJobSequenceVectorByExchangeSequence(all3GlobalOptIndividuals.get(3), particle);
                len = (int) (vtemp2.size() * r2);

                for (int j = 0; j < len; j++) {
                    listV.add(vtemp2.get(j));
                }
                addNew4JobSequenceVectorByExchangeSequence(particle, listV);

                c = random.nextDouble();
                m = random.nextDouble();
                if (c < Cross_c) {
                    getCrossOfFactoryVectorBySingle(action, particle);    //单点交叉
                }
                if (c_worker < CrossoverRates4worker) {
                    crossover4workersequence(action, particle, nw);//工人向量交叉
                }
                c_machine = random.nextDouble();
                if (c_machine < CrossoverRates4machine) {
                    crossover4machinesequence(action, particle, nw);//工人向量交叉
                }
                if (m < Mutation_m) {
                    ST q1 = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                    listV2.add(q1);
                    addNew4FactoryVectorByRandom(particle, listV2);
                }
                m_worker = random.nextDouble();
                if (m_worker < mutationRate4worker) {
                    mutation4worker(particle);
                }
                m_machine = random.nextDouble();
                if (m_machine < mutationRate4machine) {
                    mutation4machine(particle);
                }
                groupUNewSolution.set(i, particle);
            }
        }

    }


    //整合
    private void merge(List<PermutationSolution<Integer>> swarm) {
        swarm.clear();
        tempSwarm.clear();

        for (int i = 0; i < upSize; i++) {
            swarm.add((PermutationSolution<Integer>) groupU1Solution.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(upGroup1Population.get(i).size());
            for (int j = 0; j < upGroup1Population.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) upGroup1Population.get(i).get(j).copy());
            }
            tempSwarm.add(A);
        }
        for (int i = 0; i < centralSize; i++) {
            swarm.add((PermutationSolution<Integer>) groupC2Solution.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(centralGroup2Population.get(i).size());
            for (int j = 0; j < centralGroup2Population.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) centralGroup2Population.get(i).get(j).copy());
            }
            tempSwarm.add(A);
        }
        for (int i = 0; i < downSize; i++) {
            swarm.add((PermutationSolution<Integer>) groupD3Solution.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(downGroup3Population.get(i).size());
            for (int j = 0; j < downGroup3Population.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) downGroup3Population.get(i).get(j).copy());
            }
            tempSwarm.add(A);
        }

        for (int i = 0; i < upNewSize; i++) {
            swarm.add((PermutationSolution<Integer>) groupUNewSolution.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(upNewGroup1Population.get(i).size());
            for (int j = 0; j < upNewGroup1Population.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) upNewGroup1Population.get(i).get(j).copy());
            }
            tempSwarm.add(A);
        }

//        System.out.println(tempSwarm.size());

//        System.out.println(upGroup1Population.size());
//        System.out.println(centralGroup2Population.size());
//        System.out.println(downGroup3Population.size());
//        System.out.println(upNewGroup1Population.size());
//        try {
//            Thread.sleep(99999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
    }

    public static ArrayList<List<Integer>> action(int numberOfFactories) {

        List<Integer> nums = new ArrayList<>();
        for (int i = 0; i < numberOfFactories; i++) nums.add(i);
        List<List<Integer>> result = subsets(nums);
        result.remove(0);
        //System.out.println(result);
        //System.out.println("length:" + result.size());
        return (ArrayList<List<Integer>>) result;
    }

    public static List<List<Integer>> subsets(List<Integer> nums) {
        //用于生成给定列表 nums 的所有子集。这个方法通过递归地处理列表中的每个元素，并生成包含和不包含当前元素的所有子集。
        if (nums.size() == 0) return Arrays.asList(new ArrayList[]{new ArrayList<Integer>()});
        // System.out.println("nums:" + nums);

        Integer currentNums = nums.get(nums.size() - 1);
        //System.out.println("currentNums:" + currentNums);
        nums.remove(nums.size() - 1);

        List<List<Integer>> res = subsets(nums);

        List<List<Integer>> res2 = new ArrayList<>();
        //System.out.println("===============================");
        for (List<Integer> re : res) {
            List<Integer> r = new ArrayList<>();
            if (re.size() != 0) {
                for (Integer integer : re) {
                    r.add(integer);
                }
            }
            //System.out.println(r);
            res2.add(r);
        }
        // System.out.println("===============================");
        int size = res.size();
        for (int i = 0; i < size; i++) {
            List<Integer> integers = res.get(i);
            integers.add(currentNums);
            res2.add(integers);
        }
        //System.out.println("result:" + res2);
        return res2;
    }

    //    @Override
    //todo
    protected void perturbation_new(List<PermutationSolution<Integer>> swarm) {

//        try {
//            Thread.sleep(9999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
//        super.setSwarm(evaluateSwarm(swarm));
//        updateVelocity(swarm);
//        List<PermutationSolution<Integer>> swarmtemp1 = new ArrayList<PermutationSolution<Integer>>(swarm.size());
//        int[] DEswarmtempPdflag1 = new int[swarmSize];
//        int group1=1,group2=2,group3=3,group4 = 4;
//
//        for (int i = 0; i < upSize; i++) {
//            PermutationSolution<Integer>  getswarm1 = null;
//            getswarm1=selectFac1(groupU1Solution.get(i),group1);
//            swarmtemp1.add(getswarm1);
//            groupU1Solution.set(i,getswarm1);
//        }
//
//
//        for (int i = 0; i < upNewSize; i++) {
//            PermutationSolution<Integer>  getswarm1 = null;
//
//            getswarm1=selectFac1(groupUNewSolution.get(i),group4);
//            System.out.println("111");
//
//            swarmtemp1.add(getswarm1);
//
//            groupUNewSolution.set(i,getswarm1);
//        }
//
//        for (int i = 0; i < centralSize; i++) {
//            PermutationSolution<Integer>  getswarm1 = null;
//            getswarm1=selectFac1(groupC2Solution.get(i),group2);
//            swarmtemp1.add(getswarm1);
//            groupC2Solution.set(i,getswarm1);
//        }
//
//        for (int i = 0; i < downSize; i++) {
//            PermutationSolution<Integer>  getswarm1 = null;
//            getswarm1=selectFac1(groupD3Solution.get(i),group3);
//            swarmtemp1.add(getswarm1);
//            groupD3Solution.set(i,getswarm1);
//        }
//
//
//        mergeNew(swarmtemp1);
//
//
//        System.out.println("--");
//        System.out.println(swarmtemp1);
//
//
//        swarmtemp1 = evaluateSwarm(swarmtemp1);
//
//        for (int i = 0; i < swarmSize; i++) {
//            DEswarmtempPdflag1[i] = i;
//        }
//        super.setSwarm(PDDRFFselect(swarm,swarmtemp1,DEswarmtempPdflag1));

/*        List<PermutationSolution<Integer>> swarmFac = new ArrayList<PermutationSolution<Integer>>(swarmSize/2);
        for(int i=0;i<swarmFac.size();i++)
        {
            swarmFac.add(selectFac1(swarm).get(i));
        }
        //swarmFac = selectFac1(swarm);
        System.out.println(swarmFac);
        //swarmFac = evaluateSwarm(swarmFac);

        for (int i = 0; i < swarmSize/2; i++) {
            swarm.set(i+swarmSize/2,swarmFac.get(i));
        }*/

/////////////////////////////////////////////////////////////////////////////////////
        int QN = (int) Qnums;
//        QN=50;
        super.setSwarm(evaluateSwarm(swarm));
        updateVelocity(swarm);    //分群

        //////////////////////////////////////////////////////////////////////////////
        //super.setSwarm(evaluateSwarm(swarm));
        List<PermutationSolution<Integer>> swarmtemp = new ArrayList<PermutationSolution<Integer>>(swarm.size());

        int[] DEswarmtempPdflag = new int[swarmSize];


        int group = 1;
        action = action(numberOfFactories);
        int anum = action.size();
//        try {
//            Thread.sleep(999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
        ReplayBuffer replayBuffer = new ReplayBuffer(32); // 设置经验回放池的最大容量
        int batchSize = 8; // 设置每次训练的批量大小
        for (int i = 0; i < upSize; i++) {
            System.out.println(i);

            double[][] Q = new double[2][anum];
            double[][] R = new double[2][anum];
            for (int j = 0; j < anum; j++) {
                Q[0][j] = 0;
                Q[1][j] = 0;
            }

            for (int j = 0; j < anum; j++) {
                R[0][j] = 1;
                R[1][j] = 1;
            }
            //double r = 0.75, s = 0.85;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 0;
            int actionIndex;
            PermutationSolution<Integer> getswarm1 = null;
            double old0, old1, new0, new1;
            double[] max = new double[QN];
            List<PermutationSolution<Integer>> temp = new ArrayList<PermutationSolution<Integer>>(QN);
            for (int k = 0; k < QN; k++) {

                double p = random.nextDouble();

                double[][] currentState = Q.clone(); // 当前状态
                double currentReward = 0; // 当前奖励

                if (k == 0) {
                    actionIndex = random.nextInt(action.size());
                    getswarm1 = learn(actionIndex, R, Q, groupU1Solution.get(i), next, group);
                    int Qiannext = next;
                    if ((getswarm1.getObjective(0) < groupU1Solution.get(i).getObjective(0))) next = 0;
                    else next = 1;
                    old0 = groupU1Solution.get(i).getObjective(0);
                    new0 = getswarm1.getObjective(0);

                    currentReward = new0 - old0; // 计算奖励

//                    Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);
                } else {
                    if (p < 1 - tl) {
                        actionIndex = random.nextInt(action.size());
                        getswarm1 = learn(actionIndex, R, Q, groupU1Solution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(0) < groupU1Solution.get(i).getObjective(0)))
                            next = 0;
                        else next = 1;
                        old0 = groupU1Solution.get(i).getObjective(0);
                        new0 = getswarm1.getObjective(0);

                        currentReward = new0 - old0; // 计算奖励

                        Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);

//                        Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    } else {
                        //actionIndex = getMaxQ(Q);

                        actionIndex = max(Q[next]);
                        getswarm1 = learn(actionIndex, R, Q, groupU1Solution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(0) < groupU1Solution.get(i).getObjective(0)))
                            next = 0;
                        else next = 1;
                        old0 = groupU1Solution.get(i).getObjective(0);
                        new0 = getswarm1.getObjective(0);

                        currentReward = new0 - old0; // 计算奖励

                        Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);

                        // Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    }

                }
                replayBuffer.add(new Experience(currentState, actionIndex, currentReward, Q.clone(), false));

                // 从经验回放池中随机抽取一批经历进行训练
                if (replayBuffer.buffer.size() >= batchSize) {
                    List<Experience> batch = replayBuffer.sample(batchSize);
                    for (Experience exp : batch) {
                        double learningRate = 0.1;
                        double discountFactor = 0.99;
                        double maxNextQ = Math.max(exp.nextState[0][exp.action], exp.nextState[1][exp.action]);
                        double targetQ = exp.reward + discountFactor * maxNextQ;
                        double currentQ = exp.state[0][exp.action];
                        Q[0][exp.action] = currentQ + learningRate * (targetQ - currentQ);
                    }
                }


                max[k] = groupU1Solution.get(i).getObjective(0) - getswarm1.getObjective(0);
                temp.add(k, getswarm1);
            }
            int best = 0;
            for (int y = 1; y < QN; y++) {
                if (max[best] < max[y]) {
                    best = y;
                }
            }
            if (max[best] < max[QN - 1]) {
                swarmtemp.add(getswarm1);
            } else {
                swarmtemp.add(temp.get(best));
            }
//            groupU1Solution.set(i,swarmtemp.get(i));
            //swarmtemp.add(getswarm1);
        }

//        try {
//            Thread.sleep(99999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
//

        ReplayBuffer replayBuffer2 = new ReplayBuffer(32); // 设置经验回放池的最大容量
        group = 2;
        for (int i = 0; i < centralSize; i++) {
            System.out.println(i);

            double[][] Q = new double[2][anum];
            double[][] R = new double[2][anum];
            for (int j = 0; j < anum; j++) {
                Q[0][j] = 0;
                Q[1][j] = 0;
            }

            for (int j = 0; j < anum; j++) {
                R[0][j] = 1;
                R[1][j] = 1;
            }
            //double r = 0.75, s = 0.85;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 1;
            int actionIndex;
            PermutationSolution<Integer> getswarm1 = null;
            double old0, old1, new0, new1, old2, new2;
            double[] max = new double[QN];
            List<PermutationSolution<Integer>> temp = new ArrayList<PermutationSolution<Integer>>(QN);
            for (int k = 0; k < QN; k++) {
                double p = random.nextDouble();
                double[][] currentState = Q.clone(); // 当前状态
                double currentReward = 0; // 当前奖励
                if (k == 0) {
                    actionIndex = random.nextInt(action.size());
                    getswarm1 = learn(actionIndex, R, Q, groupC2Solution.get(i), next, group);
                    int Qiannext = next;
                    if ((getswarm1.getObjective(0) < groupC2Solution.get(i).getObjective(0) && getswarm1.getObjective(1) < groupC2Solution.get(i).getObjective(1) && getswarm1.getObjective(2) < groupC2Solution.get(i).getObjective(2)) ||
                            getswarm1.getObjective(0) < groupC2Solution.get(i).getObjective(0) ||
                            getswarm1.getObjective(1) < groupC2Solution.get(i).getObjective(1) ||
                            getswarm1.getObjective(2) < groupC2Solution.get(i).getObjective(2))
                        next = 0;
                    else next = 1;

                    old0 = groupC2Solution.get(i).getObjective(0);
                    old1 = groupC2Solution.get(i).getObjective(1);
                    old2 = groupC2Solution.get(i).getObjective(2);
                    new0 = getswarm1.getObjective(0);
                    new1 = getswarm1.getObjective(1);
                    new2 = getswarm1.getObjective(2);
                    Q[Qiannext][actionIndex] = calculateNewQ2(R, Q, actionIndex, next, Qiannext, old0, old1, old2, new0, new1, new2);

                    //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                } else {
                    if (p < 1 - tl) {
                        actionIndex = random.nextInt(action.size());
                        getswarm1 = learn(actionIndex, R, Q, groupC2Solution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(0) < groupC2Solution.get(i).getObjective(0) && getswarm1.getObjective(1) < groupC2Solution.get(i).getObjective(1) && getswarm1.getObjective(2) < groupC2Solution.get(i).getObjective(2)) ||
                                getswarm1.getObjective(0) < groupC2Solution.get(i).getObjective(0) ||
                                getswarm1.getObjective(1) < groupC2Solution.get(i).getObjective(1) ||
                                getswarm1.getObjective(2) < groupC2Solution.get(i).getObjective(2))
                            next = 0;
                        else next = 1;
                        old0 = groupC2Solution.get(i).getObjective(0);
                        old1 = groupC2Solution.get(i).getObjective(1);
                        old2 = groupC2Solution.get(i).getObjective(2);
                        new0 = getswarm1.getObjective(0);
                        new1 = getswarm1.getObjective(1);
                        new2 = getswarm1.getObjective(2);
                        currentReward = new0 - old0 + new1 - old1 + new2 - old2; // 计算奖励
                        Q[Qiannext][actionIndex] = calculateNewQ2(R, Q, actionIndex, next, Qiannext, old0, old1, old2, new0, new1, new2);

                        // Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    } else {

                        actionIndex = max(Q[next]);
                        getswarm1 = learn(actionIndex, R, Q, groupC2Solution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(0) < groupC2Solution.get(i).getObjective(0) && getswarm1.getObjective(1) < groupC2Solution.get(i).getObjective(1) && getswarm1.getObjective(2) < groupC2Solution.get(i).getObjective(2)) ||
                                getswarm1.getObjective(0) < groupC2Solution.get(i).getObjective(0) ||
                                getswarm1.getObjective(1) < groupC2Solution.get(i).getObjective(1) ||
                                getswarm1.getObjective(2) < groupC2Solution.get(i).getObjective(2))
                            next = 0;
                        else next = 1;
                        old0 = groupC2Solution.get(i).getObjective(0);
                        old1 = groupC2Solution.get(i).getObjective(1);
                        old2 = groupC2Solution.get(i).getObjective(2);
                        new0 = getswarm1.getObjective(0);
                        new1 = getswarm1.getObjective(1);
                        new2 = getswarm1.getObjective(2);
                        currentReward = new0 - old0 + new1 - old1 + new2 - old2; // 计算奖励
                        Q[Qiannext][actionIndex] = calculateNewQ2(R, Q, actionIndex, next, Qiannext, old0, old1, old2, new0, new1, new2);

                        // Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    }
                }

                replayBuffer2.add(new Experience(currentState, actionIndex, currentReward, Q.clone(), false));

                // 从经验回放池中随机抽取一批经历进行训练
                if (replayBuffer2.buffer.size() >= batchSize) {
                    List<Experience> batch = replayBuffer2.sample(batchSize);
                    for (Experience exp : batch) {
                        double learningRate = 0.1;
                        double discountFactor = 0.99;
                        double maxNextQ = Math.max(exp.nextState[0][exp.action], exp.nextState[1][exp.action]);
                        double targetQ = exp.reward + discountFactor * maxNextQ;
                        double currentQ = exp.state[0][exp.action];
                        Q[0][exp.action] = currentQ + learningRate * (targetQ - currentQ);
                    }
                }
                max[k] = (groupC2Solution.get(i).getObjective(0) - getswarm1.getObjective(0)) + (groupC2Solution.get(i).getObjective(1) - getswarm1.getObjective(1)) + (groupC2Solution.get(i).getObjective(2) - getswarm1.getObjective(2));
                temp.add(k, getswarm1);
            }
            int best = 0;
            for (int y = 1; y < QN; y++) {
                if (max[best] < max[y]) {
                    best = y;
                }
            }
            if (max[best] < max[QN - 1]) {
                swarmtemp.add(getswarm1);
            } else {
                swarmtemp.add(temp.get(best));
            }
            groupC2Solution.set(i, swarmtemp.get(i));
        }


        ReplayBuffer replayBuffer3 = new ReplayBuffer(32); // 设置经验回放池的最大容量
        group = 3;
        for (int i = 0; i < downSize; i++) {
            System.out.println(i);

            double[][] Q = new double[2][anum];
            double[][] R = new double[2][anum];
            for (int j = 0; j < anum; j++) {
                Q[0][j] = 0;
                Q[1][j] = 0;
            }

            for (int j = 0; j < anum; j++) {
                R[0][j] = 1;
                R[1][j] = 1;
            }
            //double r = 0.75, s = 0.85;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 1;
            int actionIndex;
            PermutationSolution<Integer> getswarm1 = null;
            double old0, old1, new0, new1;
            double[] max = new double[QN];
            List<PermutationSolution<Integer>> temp = new ArrayList<PermutationSolution<Integer>>(QN);
            for (int k = 0; k < QN; k++) {
                double p = random.nextDouble();
                double[][] currentState = Q.clone(); // 当前状态
                double currentReward = 0; // 当前奖励
                if (k == 0) {
                    actionIndex = random.nextInt(action.size());
                    getswarm1 = learn(actionIndex, R, Q, groupD3Solution.get(i), next, group);
                    int Qiannext = next;
                    if ((getswarm1.getObjective(1) < groupD3Solution.get(i).getObjective(1)))
                        next = 0;
                    else next = 1;

                    old0 = groupD3Solution.get(i).getObjective(1);
                    new0 = getswarm1.getObjective(1);
                    currentReward = new0 - old0; // 计算奖励
                    Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);
                    //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                } else {
                    if (p < 1 - tl) {
                        actionIndex = random.nextInt(action.size());
                        getswarm1 = learn(actionIndex, R, Q, groupD3Solution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(1) < groupD3Solution.get(i).getObjective(1)))
                            next = 0;
                        else next = 1;
                        old0 = groupD3Solution.get(i).getObjective(1);
                        new0 = getswarm1.getObjective(1);
                        currentReward = new0 - old0; // 计算奖励
                        Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);

                        //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    } else {

                        actionIndex = max(Q[next]);
                        getswarm1 = learn(actionIndex, R, Q, groupD3Solution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(1) < groupD3Solution.get(i).getObjective(1)))
                            next = 0;
                        else next = 1;
                        old0 = groupD3Solution.get(i).getObjective(1);
                        new0 = getswarm1.getObjective(1);
                        currentReward = new0 - old0; // 计算奖励
                        Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);

                        //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    }
                }

                // 添加当前经历到经验回放池
                replayBuffer3.add(new Experience(currentState, actionIndex, currentReward, Q.clone(), false));

                // 从经验回放池中随机抽取一批经历进行训练
                if (replayBuffer3.buffer.size() >= batchSize) {
                    List<Experience> batch = replayBuffer3.sample(batchSize);
                    for (Experience exp : batch) {
                        double learningRate = 0.1;
                        double discountFactor = 0.99;
                        double maxNextQ = Math.max(exp.nextState[0][exp.action], exp.nextState[1][exp.action]);
                        double targetQ = exp.reward + discountFactor * maxNextQ;
                        double currentQ = exp.state[0][exp.action];
                        Q[0][exp.action] = currentQ + learningRate * (targetQ - currentQ);
                    }
                }
                max[k] = groupD3Solution.get(i).getObjective(1) - getswarm1.getObjective(1);
                temp.add(k, getswarm1);
            }
            int best = 0;
            for (int y = 1; y < QN; y++) {
                if (max[best] < max[y]) {
                    best = y;
                }
            }
            if (max[best] < max[QN - 1]) {
                swarmtemp.add(getswarm1);
            } else {
                swarmtemp.add(temp.get(best));
            }
            groupD3Solution.set(i, swarmtemp.get(i));
        }


        ReplayBuffer replayBuffer4 = new ReplayBuffer(32); // 设置经验回放池的最大容量
        group = 4;
        for (int i = 0; i < upNewSize; i++) {
            System.out.println(i);
            double[][] Q = new double[2][anum];
            double[][] R = new double[2][anum];
            for (int j = 0; j < anum; j++) {
                Q[0][j] = 0;
                Q[1][j] = 0;
            }

            for (int j = 0; j < anum; j++) {
                R[0][j] = 1;
                R[1][j] = 1;
            }
            //double r = 0.75, s = 0.85;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 1;
            int actionIndex;
            PermutationSolution<Integer> getswarm1 = null;
            double old0, old1, new0, new1;
            double[] max = new double[QN];
            List<PermutationSolution<Integer>> temp = new ArrayList<PermutationSolution<Integer>>(QN);
            for (int k = 0; k < QN; k++) {
                double p = random.nextDouble();
                double[][] currentState = Q.clone(); // 当前状态
                double currentReward = 0; // 当前奖励
                if (k == 0) {
                    actionIndex = random.nextInt(action.size());
                    getswarm1 = learn(actionIndex, R, Q, groupUNewSolution.get(i), next, group);
                    int Qiannext = next;
                    if ((getswarm1.getObjective(2) < groupUNewSolution.get(i).getObjective(2)))
                        next = 0;
                    else next = 1;

                    old0 = groupUNewSolution.get(i).getObjective(2);
                    new0 = getswarm1.getObjective(2);
                    currentReward = new0 - old0; // 计算奖励
                    Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);
                    //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                } else {
                    if (p < 1 - tl) {
                        actionIndex = random.nextInt(action.size());
                        getswarm1 = learn(actionIndex, R, Q, groupUNewSolution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(2) < groupUNewSolution.get(i).getObjective(2)))
                            next = 0;
                        else next = 1;
                        old0 = groupUNewSolution.get(i).getObjective(2);
                        new0 = getswarm1.getObjective(2);
                        currentReward = new0 - old0; // 计算奖励
                        Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);

                        //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    } else {

                        actionIndex = max(Q[next]);
                        getswarm1 = learn(actionIndex, R, Q, groupUNewSolution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(2) < groupUNewSolution.get(i).getObjective(2)))
                            next = 0;
                        else next = 1;
                        old0 = groupUNewSolution.get(i).getObjective(2);
                        new0 = getswarm1.getObjective(2);
                        currentReward = new0 - old0; // 计算奖励
                        Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);

                        //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    }
                }

                // 添加当前经历到经验回放池
                replayBuffer4.add(new Experience(currentState, actionIndex, currentReward, Q.clone(), false));

                // 从经验回放池中随机抽取一批经历进行训练
                if (replayBuffer4.buffer.size() >= batchSize) {
                    List<Experience> batch = replayBuffer4.sample(batchSize);
                    for (Experience exp : batch) {
                        double learningRate = 0.1;
                        double discountFactor = 0.99;
                        double maxNextQ = Math.max(exp.nextState[0][exp.action], exp.nextState[1][exp.action]);
                        double targetQ = exp.reward + discountFactor * maxNextQ;
                        double currentQ = exp.state[0][exp.action];
                        Q[0][exp.action] = currentQ + learningRate * (targetQ - currentQ);
                    }
                }
                max[k] = groupUNewSolution.get(i).getObjective(2) - getswarm1.getObjective(2);
                temp.add(k, getswarm1);
            }
            int best = 0;
            for (int y = 1; y < QN; y++) {
                if (max[best] < max[y]) {
                    best = y;
                }
            }
            if (max[best] < max[QN - 1]) {
                swarmtemp.add(getswarm1);
            } else {
                swarmtemp.add(temp.get(best));
            }
            groupUNewSolution.set(i, swarmtemp.get(i));
        }

//        try {
//            Thread.sleep(9999999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }

        mergeNew(swarmtemp);

        swarmtemp = selectFac(swarmtemp);

        swarmtemp = evaluateSwarm(swarmtemp);
//        System.out.println(swarmtemp.size());
//        try {
//            Thread.sleep(9999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }

        for (int i = 0; i < swarmSize; i++) {
            DEswarmtempPdflag[i] = i;
        }


        super.setSwarm(PDDRFFselect(swarm, swarmtemp, DEswarmtempPdflag));
//////////////////////////////////////////////////////////////////////////////////////
/*        List<PermutationSolution<Integer>> swarmFac = new ArrayList<PermutationSolution<Integer>>(swarm.size());

        swarmFac=selectFac(swarm);
        swarmFac = evaluateSwarm(swarmFac);

        for (int i = 0; i < swarmSize; i++) {
            DEswarmtempPdflag[i] = i;
        }
        super.setSwarm(PDDRFFselect(swarm,swarmFac,DEswarmtempPdflag));*/
    }


    //没有经验池的版本，20241117之前一直用的
    protected void perturbation_3(List<PermutationSolution<Integer>> swarm) {


//        for (int i1 = 0; i1 < localsearch; i1++) {
//            //工厂间局部搜索  用的时候打开
//            swarm = factorySearch(swarm);
//        }


//        swarmtemp1 = evaluateSwarm(swarmtemp1);

//        for (int i = 0; i < swarmSize; i++) {
//            DEswarmtempPdflag1[i] = i;
//        }
//        super.setSwarm(PDDRFFselect(swarm,swarmtemp1,DEswarmtempPdflag1));
//
//        List<PermutationSolution<Integer>> swarmFac = new ArrayList<PermutationSolution<Integer>>(swarmSize/2);
//        for(int i=0;i<swarmFac.size();i++)
//        {
//            swarmFac.add(selectFac1(swarm).get(i));
//        }
//        //swarmFac = selectFac1(swarm);
//        System.out.println(swarmFac);
//        //swarmFac = evaluateSwarm(swarmFac);
//
//        for (int i = 0; i < swarmSize/2; i++) {
//            swarm.set(i+swarmSize/2,swarmFac.get(i));
//        }

/////////////////////////////////////////////////////////////////////////////////////
        //下面是工厂内部vns
        int QN = (int) Qnums;

        super.setSwarm(evaluateSwarm(swarm));
        updateVelocity(swarm);    //分群

        //////////////////////////////////////////////////////////////////////////////
        //super.setSwarm(evaluateSwarm(swarm));
        List<PermutationSolution<Integer>> swarmtemp = new ArrayList<PermutationSolution<Integer>>(swarm.size());

        int[] DEswarmtempPdflag = new int[swarmSize];


        int group = 1;
        action = action(numberOfFactories);
        int anum = action.size();
//        try {
//            Thread.sleep(999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
//        ReplayBuffer replayBuffer = new ReplayBuffer(10000); // 设置经验回放池的最大容量
//        int batchSize = 32; // 设置每次训练的批量大小


        for (int i = 0; i < upSize; i++) {

            double[][] Q = new double[2][anum];
            double[][] R = new double[2][anum];
            for (int j = 0; j < anum; j++) {
                Q[0][j] = 0;
                Q[1][j] = 0;
            }

            for (int j = 0; j < anum; j++) {
                R[0][j] = 1;
                R[1][j] = 1;
            }
            //double r = 0.75, s = 0.85;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 0;
            int actionIndex;
            PermutationSolution<Integer> getswarm1 = null;
            double old0, old1, new0, new1;
            double[] max = new double[QN];
            List<PermutationSolution<Integer>> temp = new ArrayList<PermutationSolution<Integer>>(QN);

            for (int k = 0; k < QN; k++) {

                double p = random.nextDouble();

                double[][] currentState = Q.clone(); // 当前状态
                double currentReward = 0; // 当前奖励

                if (k == 0) {
                    actionIndex = random.nextInt(action.size());


                    getswarm1 = learn(actionIndex, R, Q, groupU1Solution.get(i), next, group);


                    int Qiannext = next;
                    if ((getswarm1.getObjective(0) < groupU1Solution.get(i).getObjective(0))) next = 0;
                    else next = 1;
                    old0 = groupU1Solution.get(i).getObjective(0);
                    new0 = getswarm1.getObjective(0);

                    currentReward = new0 - old0; // 计算奖励

                    //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);
                } else {
                    if (p < 1 - tl) {
                        actionIndex = random.nextInt(action.size());
                        getswarm1 = learn(actionIndex, R, Q, groupU1Solution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(0) < groupU1Solution.get(i).getObjective(0)))
                            next = 0;
                        else next = 1;
                        old0 = groupU1Solution.get(i).getObjective(0);
                        new0 = getswarm1.getObjective(0);

                        currentReward = new0 - old0; // 计算奖励

                        Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);

                        //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    } else {
                        //actionIndex = getMaxQ(Q);

                        actionIndex = max(Q[next]);
                        getswarm1 = learn(actionIndex, R, Q, groupU1Solution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(0) < groupU1Solution.get(i).getObjective(0)))
                            next = 0;
                        else next = 1;
                        old0 = groupU1Solution.get(i).getObjective(0);
                        new0 = getswarm1.getObjective(0);

                        currentReward = new0 - old0; // 计算奖励

                        Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);

                        // Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    }

                }

//                replayBuffer.add(new Experience(currentState, actionIndex, currentReward, Q.clone(), false));
//
//                // 从经验回放池中随机抽取一批经历进行训练
//                if (replayBuffer.buffer.size() >= batchSize) {
//                    List<Experience> batch = replayBuffer.sample(batchSize);
//                    for (Experience exp : batch) {
//                        double learningRate = 0.1;
//                        double discountFactor = 0.99;
//                        double maxNextQ = Math.max(exp.nextState[0][exp.action], exp.nextState[1][exp.action]);
//                        double targetQ = exp.reward + discountFactor * maxNextQ;
//                        double currentQ = exp.state[0][exp.action];
//                        Q[0][exp.action] = currentQ + learningRate * (targetQ - currentQ);
//                    }
//                }


                max[k] = groupU1Solution.get(i).getObjective(0) - getswarm1.getObjective(0);
                temp.add(k, getswarm1);
            }

            int best = 0;
            for (int y = 1; y < QN; y++) {
                if (max[best] < max[y]) {
                    best = y;
                }
            }
            if (max[best] < max[QN - 1]) {
                swarmtemp.add(getswarm1);
            } else {
                swarmtemp.add(temp.get(best));
            }
//            groupU1Solution.set(i,swarmtemp.get(i));
            //swarmtemp.add(getswarm1);
        }


        //        System.out.println("upSize没问题");
//        try {
//            Thread.sleep(99999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
//
        group = 2;
        for (int i = 0; i < centralSize; i++) {


            double[][] Q = new double[2][anum];
            double[][] R = new double[2][anum];
            for (int j = 0; j < anum; j++) {
                Q[0][j] = 0;
                Q[1][j] = 0;
            }

            for (int j = 0; j < anum; j++) {
                R[0][j] = 1;
                R[1][j] = 1;
            }
            //double r = 0.75, s = 0.85;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 1;
            int actionIndex;
            PermutationSolution<Integer> getswarm1 = null;
            double old0, old1, new0, new1, old2, new2;
            double[] max = new double[QN];
            List<PermutationSolution<Integer>> temp = new ArrayList<PermutationSolution<Integer>>(QN);
            for (int k = 0; k < QN; k++) {
                double p = random.nextDouble();
                if (k == 0) {

                    actionIndex = random.nextInt(action.size());
                    getswarm1 = learn(actionIndex, R, Q, groupC2Solution.get(i), next, group);
                    int Qiannext = next;
                    if ((getswarm1.getObjective(0) < groupC2Solution.get(i).getObjective(0) && getswarm1.getObjective(1) < groupC2Solution.get(i).getObjective(1) && getswarm1.getObjective(2) < groupC2Solution.get(i).getObjective(2)) || getswarm1.getObjective(0) < groupC2Solution.get(i).getObjective(0) || getswarm1.getObjective(1) < groupC2Solution.get(i).getObjective(1) || getswarm1.getObjective(2) < groupC2Solution.get(i).getObjective(2))
                        next = 0;
                    else next = 1;

                    old0 = groupC2Solution.get(i).getObjective(0);
                    old1 = groupC2Solution.get(i).getObjective(1);
                    old2 = groupC2Solution.get(i).getObjective(2);
                    new0 = getswarm1.getObjective(0);
                    new1 = getswarm1.getObjective(1);
                    new2 = getswarm1.getObjective(2);
                    Q[Qiannext][actionIndex] = calculateNewQ2(R, Q, actionIndex, next, Qiannext, old0, old1, old2, new0, new1, new2);

                    //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                } else {

                    if (p < 1 - tl) {


                        actionIndex = random.nextInt(action.size());
                        getswarm1 = learn(actionIndex, R, Q, groupC2Solution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(0) < groupC2Solution.get(i).getObjective(0) && getswarm1.getObjective(1) < groupC2Solution.get(i).getObjective(1) && getswarm1.getObjective(2) < groupC2Solution.get(i).getObjective(2)) || getswarm1.getObjective(0) < groupC2Solution.get(i).getObjective(0) || getswarm1.getObjective(1) < groupC2Solution.get(i).getObjective(1) || getswarm1.getObjective(2) < groupC2Solution.get(i).getObjective(2))
                            next = 0;
                        else next = 1;
                        old0 = groupC2Solution.get(i).getObjective(0);
                        old1 = groupC2Solution.get(i).getObjective(1);
                        old2 = groupC2Solution.get(i).getObjective(2);
                        new0 = getswarm1.getObjective(0);
                        new1 = getswarm1.getObjective(1);
                        new2 = getswarm1.getObjective(2);
                        Q[Qiannext][actionIndex] = calculateNewQ2(R, Q, actionIndex, next, Qiannext, old0, old1, old2, new0, new1, new2);

                        // Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    } else {


                        actionIndex = max(Q[next]);
                        getswarm1 = learn(actionIndex, R, Q, groupC2Solution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(0) < groupC2Solution.get(i).getObjective(0) && getswarm1.getObjective(1) < groupC2Solution.get(i).getObjective(1) && getswarm1.getObjective(2) < groupC2Solution.get(i).getObjective(2)) || getswarm1.getObjective(0) < groupC2Solution.get(i).getObjective(0) || getswarm1.getObjective(1) < groupC2Solution.get(i).getObjective(1) || getswarm1.getObjective(2) < groupC2Solution.get(i).getObjective(2))
                            next = 0;
                        else next = 1;
                        old0 = groupC2Solution.get(i).getObjective(0);
                        old1 = groupC2Solution.get(i).getObjective(1);
                        old2 = groupC2Solution.get(i).getObjective(2);
                        new0 = getswarm1.getObjective(0);
                        new1 = getswarm1.getObjective(1);
                        new2 = getswarm1.getObjective(2);
                        Q[Qiannext][actionIndex] = calculateNewQ2(R, Q, actionIndex, next, Qiannext, old0, old1, old2, new0, new1, new2);

                        // Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    }
                }
                max[k] = (groupC2Solution.get(i).getObjective(0) - getswarm1.getObjective(0)) + (groupC2Solution.get(i).getObjective(1) - getswarm1.getObjective(1)) + (groupC2Solution.get(i).getObjective(2) - getswarm1.getObjective(2));
                temp.add(k, getswarm1);
            }
            int best = 0;
            for (int y = 1; y < QN; y++) {
                if (max[best] < max[y]) {
                    best = y;
                }
            }
            if (max[best] < max[QN - 1]) {
                swarmtemp.add(getswarm1);
            } else {
                swarmtemp.add(temp.get(best));
            }
            groupC2Solution.set(i, swarmtemp.get(i));
        }

//        System.out.println("centralSize没问题");

        group = 3;
        for (int i = 0; i < downSize; i++) {

            double[][] Q = new double[2][anum];
            double[][] R = new double[2][anum];
            for (int j = 0; j < anum; j++) {
                Q[0][j] = 0;
                Q[1][j] = 0;
            }

            for (int j = 0; j < anum; j++) {
                R[0][j] = 1;
                R[1][j] = 1;
            }
            //double r = 0.75, s = 0.85;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 1;
            int actionIndex;
            PermutationSolution<Integer> getswarm1 = null;
            double old0, old1, new0, new1;
            double[] max = new double[QN];
            List<PermutationSolution<Integer>> temp = new ArrayList<PermutationSolution<Integer>>(QN);
            for (int k = 0; k < QN; k++) {
                double p = random.nextDouble();
                if (k == 0) {
                    actionIndex = random.nextInt(action.size());
                    getswarm1 = learn(actionIndex, R, Q, groupD3Solution.get(i), next, group);
                    int Qiannext = next;
                    if ((getswarm1.getObjective(1) < groupD3Solution.get(i).getObjective(1)))
                        next = 0;
                    else next = 1;

                    old0 = groupD3Solution.get(i).getObjective(1);
                    new0 = getswarm1.getObjective(1);
                    Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);
                    //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                } else {
                    if (p < 1 - tl) {
                        actionIndex = random.nextInt(action.size());
                        getswarm1 = learn(actionIndex, R, Q, groupD3Solution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(1) < groupD3Solution.get(i).getObjective(1)))
                            next = 0;
                        else next = 1;
                        old0 = groupD3Solution.get(i).getObjective(1);
                        new0 = getswarm1.getObjective(1);
                        Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);

                        //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    } else {

                        actionIndex = max(Q[next]);
                        getswarm1 = learn(actionIndex, R, Q, groupD3Solution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(1) < groupD3Solution.get(i).getObjective(1)))
                            next = 0;
                        else next = 1;
                        old0 = groupD3Solution.get(i).getObjective(1);
                        new0 = getswarm1.getObjective(1);
                        Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);

                        //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    }
                }
                max[k] = groupD3Solution.get(i).getObjective(1) - getswarm1.getObjective(1);
                temp.add(k, getswarm1);
            }
            int best = 0;
            for (int y = 1; y < QN; y++) {
                if (max[best] < max[y]) {
                    best = y;
                }
            }
            if (max[best] < max[QN - 1]) {
                swarmtemp.add(getswarm1);
            } else {
                swarmtemp.add(temp.get(best));
            }
            groupD3Solution.set(i, swarmtemp.get(i));
        }

//        System.out.println("downSize没问题");
        group = 4;
        for (int i = 0; i < upNewSize; i++) {

            double[][] Q = new double[2][anum];
            double[][] R = new double[2][anum];
            for (int j = 0; j < anum; j++) {
                Q[0][j] = 0;
                Q[1][j] = 0;
            }

            for (int j = 0; j < anum; j++) {
                R[0][j] = 1;
                R[1][j] = 1;
            }
            //double r = 0.75, s = 0.85;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 1;
            int actionIndex;
            PermutationSolution<Integer> getswarm1 = null;
            double old0, old1, new0, new1;
            double[] max = new double[QN];
            List<PermutationSolution<Integer>> temp = new ArrayList<PermutationSolution<Integer>>(QN);
            for (int k = 0; k < QN; k++) {
                double p = random.nextDouble();
                if (k == 0) {
                    actionIndex = random.nextInt(action.size());
                    getswarm1 = learn(actionIndex, R, Q, groupUNewSolution.get(i), next, group);
                    int Qiannext = next;
                    if ((getswarm1.getObjective(2) < groupUNewSolution.get(i).getObjective(2)))
                        next = 0;
                    else next = 1;

                    old0 = groupUNewSolution.get(i).getObjective(2);
                    new0 = getswarm1.getObjective(2);
                    Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);
                    //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                } else {
                    if (p < 1 - tl) {
                        actionIndex = random.nextInt(action.size());
                        getswarm1 = learn(actionIndex, R, Q, groupUNewSolution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(2) < groupUNewSolution.get(i).getObjective(2)))
                            next = 0;
                        else next = 1;
                        old0 = groupUNewSolution.get(i).getObjective(2);
                        new0 = getswarm1.getObjective(2);
                        Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);

                        //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    } else {

                        actionIndex = max(Q[next]);
                        getswarm1 = learn(actionIndex, R, Q, groupUNewSolution.get(i), next, group);
                        int Qiannext = next;
                        if ((getswarm1.getObjective(2) < groupUNewSolution.get(i).getObjective(2)))
                            next = 0;
                        else next = 1;
                        old0 = groupUNewSolution.get(i).getObjective(2);
                        new0 = getswarm1.getObjective(2);
                        Q[Qiannext][actionIndex] = calculateNewQ1(R, Q, actionIndex, next, Qiannext, old0, new0);

                        //Q[Qiannext][actionIndex] = calculateNewQ(R, Q,actionIndex,next,Qiannext);
                    }
                }
                max[k] = groupUNewSolution.get(i).getObjective(2) - getswarm1.getObjective(2);
                temp.add(k, getswarm1);
            }
            int best = 0;
            for (int y = 1; y < QN; y++) {
                if (max[best] < max[y]) {
                    best = y;
                }
            }
            if (max[best] < max[QN - 1]) {
                swarmtemp.add(getswarm1);
            } else {
                swarmtemp.add(temp.get(best));
            }
            groupUNewSolution.set(i, swarmtemp.get(i));
        }

//        System.out.println("upNewSize没问题");
//        try {
//            Thread.sleep(9999999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }

        mergeNew(swarmtemp);

//        swarmtemp = selectFac(swarmtemp);

        swarmtemp = evaluateSwarm(swarmtemp);
//        System.out.println(swarmtemp.size());
//        try {
//            Thread.sleep(9999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }

        for (int i = 0; i < swarmSize; i++) {
            DEswarmtempPdflag[i] = i;
        }


        super.setSwarm(PDDRFFselect(swarm, swarmtemp, DEswarmtempPdflag));


//////////////////////////////////////////////////////////////////////////////////////
/*        List<PermutationSolution<Integer>> swarmFac = new ArrayList<PermutationSolution<Integer>>(swarm.size());

        swarmFac=selectFac(swarm);
        swarmFac = evaluateSwarm(swarmFac);

        for (int i = 0; i < swarmSize; i++) {
            DEswarmtempPdflag[i] = i;
        }
        super.setSwarm(PDDRFFselect(swarm,swarmFac,DEswarmtempPdflag));*/
    }

    protected void perturbation(List<PermutationSolution<Integer>> swarm) {
        updateVelocity(swarm);
        for (int i = 0; i < upSize; i++) {
            int group = 1;
            PermutationSolution<Integer> currentsolution = groupU1Solution.get(i);
            action = action(numberOfFactories);
            Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int index = r.nextInt(action.size());
            List<Integer> actionselect = action.get(index);
//            System.out.println(action.size());
            PermutationSolution<Integer> newsolution;
            newsolution = V_N_Search(currentsolution, actionselect, group);
            groupU1Solution.set(i, newsolution);
//            sleep();
        }

        for (int i = 0; i < centralSize; i++) {
            int group = 2;
            PermutationSolution<Integer> currentsolution = groupC2Solution.get(i);
            action = action(numberOfFactories);
            Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int index = r.nextInt(action.size());
            List<Integer> actionselect = action.get(index);
//            System.out.println(action.size());
            PermutationSolution<Integer> newsolution;
            newsolution = V_N_Search(currentsolution, actionselect, group);
            groupC2Solution.set(i, newsolution);
//            sleep();
        }

        for (int i = 0; i < downSize; i++) {
            int group = 3;
            PermutationSolution<Integer> currentsolution = groupD3Solution.get(i);
            action = action(numberOfFactories);
            Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int index = r.nextInt(action.size());
            List<Integer> actionselect = action.get(index);
//            System.out.println(action.size());
            PermutationSolution<Integer> newsolution;
            newsolution = V_N_Search(currentsolution, actionselect, group);
            groupD3Solution.set(i, newsolution);
//            sleep();
        }

        for (int i = 0; i < upNewSize; i++) {
            int group = 4;
            PermutationSolution<Integer> currentsolution = groupUNewSolution.get(i);
            action = action(numberOfFactories);
            Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int index = r.nextInt(action.size());
            List<Integer> actionselect = action.get(index);
//            System.out.println(action.size());
            PermutationSolution<Integer> newsolution;
            newsolution = V_N_Search(currentsolution, actionselect, group);
            groupUNewSolution.set(i, newsolution);
//            sleep();
        }
    }

    private List<PermutationSolution<Integer>> factorySearch(List<PermutationSolution<Integer>> swarm) {
        //下面是针对工厂间的操作
        super.setSwarm(evaluateSwarm(swarm));
        updateVelocity(swarm);
        List<PermutationSolution<Integer>> swarmtemp1 = new ArrayList<PermutationSolution<Integer>>(swarm.size());
        int[] DEswarmtempPdflag1 = new int[swarmSize];
        int group1 = 1, group2 = 2, group3 = 3, group4 = 4;

        for (int i = 0; i < upSize; i++) {
            PermutationSolution<Integer> getswarm1 = null;
            getswarm1 = selectFac1(groupU1Solution.get(i), group1);
            swarmtemp1.add(getswarm1);
            groupU1Solution.set(i, getswarm1);
        }

        for (int i = 0; i < upNewSize; i++) {
            PermutationSolution<Integer> getswarm1 = null;
            getswarm1 = selectFac1(groupUNewSolution.get(i), group4);
            swarmtemp1.add(getswarm1);
            groupUNewSolution.set(i, getswarm1);
        }

        for (int i = 0; i < centralSize; i++) {
            PermutationSolution<Integer> getswarm1 = null;
            getswarm1 = selectFac1(groupC2Solution.get(i), group2);
            swarmtemp1.add(getswarm1);
            groupC2Solution.set(i, getswarm1);
        }

        for (int i = 0; i < downSize; i++) {
            PermutationSolution<Integer> getswarm1 = null;
            getswarm1 = selectFac1(groupD3Solution.get(i), group3);
            swarmtemp1.add(getswarm1);
            groupD3Solution.set(i, getswarm1);
        }
        mergeNew(swarmtemp1);
        swarm = evaluateSwarm(swarmtemp1);
        return swarm;
    }


    //二元锦标赛法（选三个，取最好）
    private void selectTS() {
        int size = swarmSize / 2;
        upGr1HisOptIndividual.clear();
        centralGr2HisOptIndividual.clear();
        downGr3HisOptIndividual.clear();
        all3GlobalOptIndividuals.clear();

        for (int i = 0; i < size / 3; i++) {
            int a1 = randomGenerator.nextInt(0, upGroup1Population.get(i + size / 3).size() - 1);
            int a2 = randomGenerator.nextInt(0, upGroup1Population.get(i + size / 3).size() - 1);
            int a3 = randomGenerator.nextInt(0, upGroup1Population.get(i + size / 3).size() - 1);
            int temp = a1;
            if (upGroup1Population.get(i + size / 3).get(a1).getObjective(0) >= upGroup1Population.get(i + size / 3).get(a2).getObjective(0) &&
                    upGroup1Population.get(i + size / 3).get(a3).getObjective(0) >= upGroup1Population.get(i + size / 3).get(a2).getObjective(0)) {
                temp = a2;
            }

            if (upGroup1Population.get(i + size / 3).get(a1).getObjective(0) >= upGroup1Population.get(i + size / 3).get(a3).getObjective(0) &&
                    upGroup1Population.get(i + size / 3).get(a2).getObjective(0) >= upGroup1Population.get(i + size / 3).get(a3).getObjective(0)) {
                temp = a3;
            }
            upGr1HisOptIndividual.add(upGroup1Population.get(i + size / 3).get(temp));

        }

        for (int i = 0; i < size - 2 * size / 3; i++) {
            int a1 = randomGenerator.nextInt(0, centralGroup2Population.get(i + size - 2 * size / 3).size() - 1);
            int a2 = randomGenerator.nextInt(0, centralGroup2Population.get(i + size - 2 * size / 3).size() - 1);
            int a3 = randomGenerator.nextInt(0, centralGroup2Population.get(i + size - 2 * size / 3).size() - 1);
            int temp = a1;
            List<Double> bb = new ArrayList<>(centralGroup2Population.get(i + size - 2 * size / 3).size());

            for (int j = 0; j < centralGroup2Population.get(i + size - 2 * size / 3).size(); j++) {
                double count1 = 0;
                double count2 = 0;
                for (int k = 0; k < centralGroup2Population.get(i + size - 2 * size / 3).size(); k++) {
                    if (j != k) {
                        if (centralGroup2Population.get(i + size - 2 * size / 3).get(j).getObjective(0) <= centralGroup2Population.get(i + size - 2 * size / 3).get(k).getObjective(0) &&
                                centralGroup2Population.get(i + size - 2 * size / 3).get(j).getObjective(1) <= centralGroup2Population.get(i + size - 2 * size / 3).get(k).getObjective(1)) {
                            count1 = count1 + 1;
                        }
                        if (centralGroup2Population.get(i + size - 2 * size / 3).get(j).getObjective(0) >= centralGroup2Population.get(i + size - 2 * size / 3).get(k).getObjective(0) &&
                                centralGroup2Population.get(i + size - 2 * size / 3).get(j).getObjective(1) >= centralGroup2Population.get(i + size - 2 * size / 3).get(k).getObjective(1)) {
                            count2 = count2 + 1;
                        }
                    }
                }
                bb.add(count2 + 1 / (count1 + 1));
            }

            if (bb.get(a1) >= bb.get(a2) && bb.get(a3) >= bb.get(a2)) {
                temp = a2;
            }
            if (bb.get(a1) >= bb.get(a3) && bb.get(a2) >= bb.get(a3)) {
                temp = a3;
            }
            centralGr2HisOptIndividual.add(centralGroup2Population.get(i + size - 2 * size / 3).get(temp));

        }

        for (int i = 0; i < size / 3; i++) {
            int a1 = randomGenerator.nextInt(0, downGroup3Population.get(i + size / 3).size() - 1);
            int a2 = randomGenerator.nextInt(0, downGroup3Population.get(i + size / 3).size() - 1);
            int a3 = randomGenerator.nextInt(0, downGroup3Population.get(i + size / 3).size() - 1);
            int temp = a1;
            if (downGroup3Population.get(i + size / 3).get(a1).getObjective(1) >= downGroup3Population.get(i + size / 3).get(a2).getObjective(1) &&
                    downGroup3Population.get(i + size / 3).get(a3).getObjective(1) >= downGroup3Population.get(i + size / 3).get(a2).getObjective(1)) {
                temp = a2;
            }
            if (downGroup3Population.get(i + size / 3).get(a1).getObjective(1) >= downGroup3Population.get(i + size / 3).get(a3).getObjective(1) &&
                    downGroup3Population.get(i + size / 3).get(a2).getObjective(1) >= downGroup3Population.get(i + size / 3).get(a3).getObjective(1)) {
                temp = a3;
            }
            downGr3HisOptIndividual.add(downGroup3Population.get(i + size / 3).get(temp));
        }

        //判断选择全局最优解
        int a1 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        int a2 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        int a3 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        int temp = a1;
        if (globallyOptimalIndividual.get(a1).getObjective(0) >= globallyOptimalIndividual.get(a2).getObjective(0) &&
                globallyOptimalIndividual.get(a3).getObjective(0) >= globallyOptimalIndividual.get(a2).getObjective(0)) {
            temp = a2;
        }

        if (globallyOptimalIndividual.get(a1).getObjective(0) >= globallyOptimalIndividual.get(a3).getObjective(0) &&
                globallyOptimalIndividual.get(a2).getObjective(0) >= globallyOptimalIndividual.get(a3).getObjective(0)) {
            temp = a3;
        }
        all3GlobalOptIndividuals.add(globallyOptimalIndividual.get(temp));


        a1 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        a2 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        a3 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        temp = a1;
        List<Double> cc = new ArrayList<>(globallyOptimalIndividual.size());
        for (int i = 0; i < globallyOptimalIndividual.size(); i++) {
            double count1 = 0;
            double count2 = 0;
            for (int j = 0; j < globallyOptimalIndividual.size(); j++) {
                if (i != j) {
                    if (globallyOptimalIndividual.get(i).getObjective(0) <= globallyOptimalIndividual.get(j).getObjective(0) &&
                            globallyOptimalIndividual.get(i).getObjective(1) <= globallyOptimalIndividual.get(j).getObjective(1) &&
                            globallyOptimalIndividual.get(i).getObjective(2) <= globallyOptimalIndividual.get(j).getObjective(2)) {
                        count1 = count1 + 1;
                    }
                    if (globallyOptimalIndividual.get(i).getObjective(0) >= globallyOptimalIndividual.get(j).getObjective(0) &&
                            globallyOptimalIndividual.get(i).getObjective(1) >= globallyOptimalIndividual.get(j).getObjective(1) &&
                            globallyOptimalIndividual.get(i).getObjective(2) >= globallyOptimalIndividual.get(j).getObjective(2)) {
                        count2 = count2 + 1;
                    }
                }
            }
            cc.add(count2 + 1 / (count1 + 1));
        }

        if (cc.get(a1) >= cc.get(a2) && cc.get(a3) >= cc.get(a2)) {
            temp = a2;
        }
        if (cc.get(a1) >= cc.get(a3) && cc.get(a2) >= cc.get(a3)) {
            temp = a3;
        }
        all3GlobalOptIndividuals.add(globallyOptimalIndividual.get(temp));

        a1 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        a2 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        a3 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        temp = a1;
        if (globallyOptimalIndividual.get(a1).getObjective(1) >= globallyOptimalIndividual.get(a2).getObjective(1) &&
                globallyOptimalIndividual.get(a3).getObjective(1) >= globallyOptimalIndividual.get(a2).getObjective(1)) {
            temp = a2;
        }

        if (globallyOptimalIndividual.get(a1).getObjective(1) >= globallyOptimalIndividual.get(a3).getObjective(1) &&
                globallyOptimalIndividual.get(a2).getObjective(1) >= globallyOptimalIndividual.get(a3).getObjective(1)) {
            temp = a3;
        }
        all3GlobalOptIndividuals.add(globallyOptimalIndividual.get(temp));

    }

    protected PermutationSolution<Integer> selectFac1(PermutationSolution<Integer> swarmtemp, int group) {
        List<PermutationSolution<Integer>> swarmFac = new ArrayList<PermutationSolution<Integer>>(swarmSize / 2);
/*        for(int f = 0; f < swarmSize/2; f++){
            swarmFac.add(swarmtemp.get(f+swarmFac.size()));
        }*/
/*        for(int f = swarmSize/2; f < swarmSize; f++){
            swarmFac.add(swarmtemp.get(f));
        }*/
        //System.out.print(swarmFac);
        //updateVelocity1(swarmFac);    //分群
        //swarmFac.clear();

/*        for(int i=0; i<swarmFac.size()/3; i++){
            int group=1;
            PermutationSolution<Integer>  getswarm = null;
            getswarm = factorySearch(groupU1Solution.get(i), group);
            PermutationSolution<Integer>  getswarm1 = (PermutationSolution<Integer>) getswarm.copy();
            groupU1Solution.set(i,getswarm1);
            swarmFac.set(i,getswarm1);
        }
        for(int i=0; i<swarmFac.size()-2*swarmFac.size()/3; i++){
            int group=2;
            PermutationSolution<Integer>  getswarm = null;
            getswarm = factorySearch(groupC2Solution.get(i), group);
            PermutationSolution<Integer>  getswarm1 = (PermutationSolution<Integer>) getswarm.copy();
            groupC2Solution.set(i,getswarm1);
            swarmFac.set(i,getswarm1);
        }
        for(int i=0; i<swarmFac.size()/3; i++){
            int group=3;*/
        PermutationSolution<Integer> getswarm = null;
        getswarm = factorySearch(swarmtemp, group);

        //mergeNew1(swarmFac);

        return getswarm;
    }

    protected void updateVelocity1(List<PermutationSolution<Integer>> swarm1) {

        upGroup1Population.clear();
        centralGroup2Population.clear();
        downGroup3Population.clear();

        groupU1Solution.clear();
        groupC2Solution.clear();
        groupD3Solution.clear();

        List<PermutationSolution<Integer>> temp1 = new ArrayList<>(swarmSize / 2);
        List<PermutationSolution<Integer>> temp2 = new ArrayList<>(swarmSize / 2);
        List<PermutationSolution<Integer>> temp3 = new ArrayList<>(swarmSize / 2);

        ArrayList<List<PermutationSolution<Integer>>> tempPd1 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize / 2);
        ArrayList<List<PermutationSolution<Integer>>> tempPd2 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize / 2);
        ArrayList<List<PermutationSolution<Integer>>> tempPd3 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize / 2);

        for (int i = 0; i < swarmSize / 2; i++) {
            temp1.add((PermutationSolution<Integer>) swarm1.get(i).copy());
            temp2.add((PermutationSolution<Integer>) swarm1.get(i).copy());
            temp3.add((PermutationSolution<Integer>) swarm1.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(tempSwarm.get(i + swarmSize / 2).size());
            for (int j = 0; j < tempSwarm.get(i + swarmSize / 2).size(); j++) {

                A.add((PermutationSolution<Integer>) tempSwarm.get(i + swarmSize / 2).get(j).copy());
            }

            tempPd1.add(A);
            tempPd2.add(A);
            tempPd3.add(A);
        }

        //划分sub1
        for (int i = 0; i < swarm1.size() / 3; i++) {
            int b = 0;
            for (int j = 1; j < temp1.size(); j++) {
                if (temp1.get(j).getObjective(0) < temp1.get(b).getObjective(0)) {
                    b = j;
                }
            }
            groupU1Solution.add(temp1.get(b));
            upGroup1Population.add(tempPd1.get(b));

            temp1.remove(b);
            tempPd1.remove(b);

        }

        //划分sub2
        List<Double> aa = new ArrayList<>(swarm1.size());
        for (int i = 0; i < swarm1.size(); i++) {
            double count1 = 0;
            double count2 = 0;
            for (int j = 0; j < swarm1.size(); j++) {
                if (i != j) {
                    if (temp2.get(i).getObjective(0) <= temp2.get(j).getObjective(0) &&
                            temp2.get(i).getObjective(1) <= temp2.get(j).getObjective(1)) {
                        count1 = count1 + 1;
                    }
                    if (temp2.get(i).getObjective(0) >= temp2.get(j).getObjective(0) &&
                            temp2.get(i).getObjective(1) >= temp2.get(j).getObjective(1)) {
                        count2 = count2 + 1;
                    }
                }
            }
            aa.add(count2 + 1 / (count1 + 1));
        }

        for (int i = 0; i < swarm1.size() - 2 * swarm1.size() / 3; i++) {
            int b = 0;
            for (int j = 1; j < aa.size(); j++) {
                if (aa.get(j) < aa.get(b)) {
                    b = j;
                }
            }
            groupC2Solution.add(temp2.get(b));
            centralGroup2Population.add(tempPd2.get(b));

            aa.remove(b);
            tempPd2.remove(b);
            temp2.remove(b);
        }

        for (int i = 0; i < swarm1.size() / 3; i++) {
            int b = 0;
            for (int j = 1; j < temp3.size(); j++) {
                if (temp3.get(j).getObjective(1) < temp3.get(b).getObjective(1)) {
                    b = j;
                }
            }
            groupD3Solution.add(temp3.get(b));
            downGroup3Population.add(tempPd3.get(b));

            temp3.remove(b);
            tempPd3.remove(b);
        }

        //selectTS();

    }

    protected List<PermutationSolution<Integer>> selectFac(List<PermutationSolution<Integer>> swarmtemp) {
        List<PermutationSolution<Integer>> swarmFac = new ArrayList<PermutationSolution<Integer>>(swarmSize);
        for (int f = 0; f < swarmSize / 2; f++) {
            swarmFac.add(swarmtemp.get(f + swarmFac.size()));
        }
        for (int f = swarmSize / 2; f < swarmSize; f++) {
            swarmFac.add(swarmtemp.get(f));
        }
        //System.out.print(swarmFac);
        updateVelocity(swarmFac);    //分群
        //swarmFac.clear();

        for (int i = 0; i < upSize; i++) {
            int group = 1;
            PermutationSolution<Integer> getswarm = null;
            getswarm = factorySearch(groupU1Solution.get(i), group);
            //groupU1Solution.set(i,getswarm);
            swarmFac.set(i, getswarm);
        }
        for (int i = 0; i < centralSize; i++) {
            int group = 2;
            PermutationSolution<Integer> getswarm = null;
            getswarm = factorySearch(groupC2Solution.get(i), group);
            //groupC2Solution.set(i,getswarm);
            swarmFac.set(i, getswarm);
        }
        for (int i = 0; i < downSize; i++) {
            int group = 3;
            PermutationSolution<Integer> getswarm = null;
            getswarm = factorySearch(groupD3Solution.get(i), group);
            swarmFac.set(i, getswarm);
            //groupD3Solution.set(i,getswarm);
        }
        for (int i = 0; i < upNewSize; i++) {
            int group = 4;
            PermutationSolution<Integer> getswarm = null;
            getswarm = factorySearch(groupUNewSolution.get(i), group);
            swarmFac.set(i, getswarm);
            //groupD3Solution.set(i,getswarm);
        }
        return swarmFac;
    }

    public PermutationSolution<Integer> factorySearch(PermutationSolution<Integer> bestsolution, int group) {
        int count = 0;
        int max_iterations = 10;

        PermutationSolution<Integer> currentsolution = bestsolution;
        //shaking(solution,k);
        do {
            currentsolution = vnd(currentsolution, group);
            count++;
        }
        while (count <= max_iterations);
        return currentsolution;

    }    //针对工厂间的变邻域搜索

    private PermutationSolution<Integer> vnd(PermutationSolution<Integer> solution, int group) {//solution就是main里的current_solution
        PermutationSolution<Integer> solution1 = (PermutationSolution<Integer>) solution.copy();
        PermutationSolution<Integer> current_solution = solution;
        List<PermutationSolution<Integer>> current_pop1 = new ArrayList<PermutationSolution<Integer>>(1);
        List<PermutationSolution<Integer>> pop1 = new ArrayList<PermutationSolution<Integer>>(1);

        int l = 0;
        while (l < 4) {
            pop1.clear();
            current_pop1.clear();
            current_solution = insert_otherfac(current_solution, group);
            pop1.add(solution);
            current_pop1.add(current_solution);
            current_pop1 = evaluator.evaluate(current_pop1, problem);
            pop1 = evaluator.evaluate(pop1, problem);

            if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) && current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2)) ||
                    (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) ||
                    (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) ||
                    (current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2))) {
                //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                solution1 = current_solution;
                current_solution = insertion_fac(solution1, group);
            } else {
                current_solution = insertion_fac(current_solution, group);
            }
            //current_solution = insertion_fac(current_solution,group);
            pop1.add(solution);
            current_pop1.add(current_solution);
            current_pop1 = evaluator.evaluate(current_pop1, problem);
            pop1 = evaluator.evaluate(pop1, problem);
            if (group == 1) {
                if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))) {
                    //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    //l=0;
                    break;
                } else {
                    l++;
                }
            }
            if (group == 2) {
                if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) && current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2))) {
                    //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    break;
                    //l=0;
                } else {
                    l++;
                }
            }
            if (group == 3) {
                if ((current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    break;
                    //l=0;
                } else {
                    l++;
                }
            }
            if (group == 4) {
                if ((current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2))) {
                    //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    //l=0;
                    break;
                } else {
                    l++;
                }
            }


        }
        return solution;
    }


    public PermutationSolution<Integer> insertion_fac(PermutationSolution<Integer> solution, int group) {
        return org.uma.jmetal.util.research.FactoryNeighborhoods.move(solution, group, true,
                ((org.uma.jmetal.util.research.SchedulingProblemData) ((org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution) solution)
                        .getSchedulingProblem()).getSchedulingInstance());
    }

    public PermutationSolution<Integer> insert_otherfac(PermutationSolution<Integer> solution, int group) {
        return org.uma.jmetal.util.research.FactoryNeighborhoods.move(solution, group, false,
                ((org.uma.jmetal.util.research.SchedulingProblemData) ((org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution) solution)
                        .getSchedulingProblem()).getSchedulingInstance());
    }

    public double calculateNewQ1(double[][] R, double[][] Q, int a, int next1, int Qiannext, double old0, double new0) {
        // return (r + rew * q);
        //double reward= R[Qiannext][a];
        double reward = old0 - new0;
        Q[Qiannext][a] = reward + gamma * maxNextQ(Q[next1]);
        //Q[Qiannext][a] = (1-alpha) * Q[Qiannext][a] + alpha * (reward+ gamma * maxNextQ(Q[next1]));
        return Q[Qiannext][a];
    }

    public double calculateNewQ2(double[][] R, double[][] Q, int a, int next1, int Qiannext, double old0, double old1, double old2, double new0, double new1, double new2) {
        // return (r + rew * q);
        //double reward= R[Qiannext][a];
        double reward = (old0 - new0) + (old1 - new1) + (old2 - new2);
        Q[Qiannext][a] = reward + gamma * maxNextQ(Q[next1]);
        //Q[Qiannext][a] = (1-alpha) * Q[Qiannext][a] + alpha * (reward+ gamma * maxNextQ(Q[next1]));
        return Q[Qiannext][a];
    }

    private double maxNextQ(double[] is) {
        double max = is[0];
        for (int i = 1; i < is.length; ++i) {
            if (is[i] > max) max = is[i];
        }
        return max;
    }

    private int max(double[] is) {
        int max = 0;
        for (int i = 1; i < is.length; ++i) {
            if (is[i] > is[max]) max = i;
        }
        return max;
    }

    private void mergeNew(List<PermutationSolution<Integer>> swarm) {
        //swarm.clear();
        tempSwarm.clear();

        for (int i = 0; i < upSize; i++) {
            //swarm.add((PermutationSolution<Integer>) groupU1Solution.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(upGroup1Population.get(i).size());

            for (int j = 0; j < upGroup1Population.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) upGroup1Population.get(i).get(j).copy());
            }

            tempSwarm.add(A);

        }


        for (int i = 0; i < centralSize; i++) {
            //swarm.add((PermutationSolution<Integer>) groupC2Solution.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(centralGroup2Population.get(i).size());

            for (int j = 0; j < centralGroup2Population.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) centralGroup2Population.get(i).get(j).copy());
            }
            tempSwarm.add(A);
        }

        for (int i = 0; i < downSize; i++) {
            //swarm.add((PermutationSolution<Integer>) groupD3Solution.get(i).copy());
            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(downGroup3Population.get(i).size());
            for (int j = 0; j < downGroup3Population.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) downGroup3Population.get(i).get(j).copy());
            }
            tempSwarm.add(A);
        }

        for (int i = 0; i < upNewSize; i++) {
            //swarm.add((PermutationSolution<Integer>) groupU1Solution.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(upNewGroup1Population.get(i).size());

            for (int j = 0; j < upNewGroup1Population.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) upNewGroup1Population.get(i).get(j).copy());
            }
            tempSwarm.add(A);
        }

    }

    private void mergeNew1(List<PermutationSolution<Integer>> swarm) {
        swarm.clear();
        tempSwarm.clear();

        for (int i = 0; i < swarm.size() / 3; i++) {
            swarm.add((PermutationSolution<Integer>) groupU1Solution.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(upGroup1Population.get(i).size());

            for (int j = 0; j < upGroup1Population.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) upGroup1Population.get(i).get(j).copy());
            }
            tempSwarm.add(A);
        }


        for (int i = 0; i < swarm.size() - 2 * swarm.size() / 3; i++) {
            swarm.add((PermutationSolution<Integer>) groupC2Solution.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(centralGroup2Population.get(i).size());

            for (int j = 0; j < centralGroup2Population.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) centralGroup2Population.get(i).get(j).copy());
            }
            tempSwarm.add(A);
        }

        for (int i = 0; i < swarm.size() / 3; i++) {
            swarm.add((PermutationSolution<Integer>) groupD3Solution.get(i).copy());
            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(downGroup3Population.get(i).size());
            for (int j = 0; j < downGroup3Population.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) downGroup3Population.get(i).get(j).copy());
            }
            tempSwarm.add(A);
        }

    }

    public PermutationSolution<Integer> learn(int a, double[][] R, double[][] Q, PermutationSolution<Integer> bestsolution, int next1, int group) {

        List<Integer> selectFac = new ArrayList<>();
        selectFac = action.get(a);
        PermutationSolution<Integer> solutiont;
        solutiont = V_N_Search(bestsolution, selectFac, group);
/*        if (solutiont.getObjective(0) == bestsolution.getObjective(0) && solutiont.getObjective(1) == bestsolution.getObjective(1)) next1 = 1;
        else next1 = 0;*/
        double reward = R[next1][a];
        double Qvalue = calculateNewQ(reward, Q[next1][a]);
        Q[next1][a] = Qvalue;


        return solutiont;
    }

    public PermutationSolution<Integer> V_N_Search(PermutationSolution<Integer> bestsolution, List<Integer> selectFac, int group) {
        int count = 0;
        int max_iterations = 3;
        List<PermutationSolution<Integer>> current_pop1 = new ArrayList<PermutationSolution<Integer>>(1);
        List<PermutationSolution<Integer>> pop1 = new ArrayList<PermutationSolution<Integer>>(1);
        PermutationSolution<Integer> currentsolution = bestsolution;
        //shaking(solution,k);
        do {
            current_pop1.clear();
            pop1.clear();

            currentsolution = variable_neighborhood_descent(currentsolution, selectFac, group);
            count++;
        }
        while (count <= max_iterations);
        return currentsolution;

    }    //变邻域搜索

    private PermutationSolution<Integer> variable_neighborhood_descent(PermutationSolution<Integer> solution, List<Integer> selectFac, int group) {//solution就是main里的current_solution
        PermutationSolution<Integer> current_solution = (PermutationSolution<Integer>) solution.copy();
        List<PermutationSolution<Integer>> current_pop1 = new ArrayList<PermutationSolution<Integer>>(1);
        List<PermutationSolution<Integer>> pop1 = new ArrayList<PermutationSolution<Integer>>(1);

        int l = 1;
        while (l <= 6) {
//            System.out.println(l);

            if (l == 1) {
                pop1.clear();
                current_pop1.clear();
                current_solution = insertion_neighborhood_new(current_solution, selectFac);
                pop1.add(solution);
                current_pop1.add(current_solution);

                current_pop1 = evaluator.evaluate(current_pop1, problem);
                pop1 = evaluator.evaluate(pop1, problem);
                if (group == 1) {
                    if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 2) {
                    if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) && current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2)) ||
                            (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) ||
                            (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) ||
                            (current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2))

                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 3) {
                    if ((current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 4) {
                    if ((current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
            }

            if (l == 2) {
                pop1.clear();
                current_pop1.clear();

                current_solution = exchange_neighborhood_new(solution, selectFac);
                pop1.add(solution);
                current_pop1.add(current_solution);
                current_pop1 = evaluator.evaluate(current_pop1, (Problem<PermutationSolution<Integer>>) problem);
                pop1 = evaluator.evaluate(pop1, (Problem<PermutationSolution<Integer>>) problem);
                if (group == 1) {
                    if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 2) {
                    if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) && current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2)) ||
                            (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) ||
                            (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) ||
                            (current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 3) {
                    if ((current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 4) {
                    if (current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2)
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }

/*               if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))|| (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) ) )
               {
                //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    //l=0;
                } else {
                    l++;
                }*/
            }

            if (l == 3) {
                pop1.clear();
                current_pop1.clear();

                current_solution = reverse_neighborhood_new(solution, selectFac);
                pop1.add(solution);
                current_pop1.add(current_solution);
                current_pop1 = evaluator.evaluate(current_pop1, (Problem<PermutationSolution<Integer>>) problem);
                pop1 = evaluator.evaluate(pop1, (Problem<PermutationSolution<Integer>>) problem);
                if (group == 1) {
                    if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 2) {
                    if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) && current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2)) ||
                            (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) ||
                            (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) ||
                            (current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 3) {
                    if ((current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 4) {
                    if (current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2)
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }

/*               if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))|| (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) ) )
               {
                //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    //l=0;
                } else {
                    l++;
                }*/
            }

            if (l == 5) {


                pop1.clear();
                current_pop1.clear();

                current_solution = worker_level_insert(solution, selectFac);
                pop1.add(solution);
                current_pop1.add(current_solution);
                current_pop1 = evaluator.evaluate(current_pop1, (Problem<PermutationSolution<Integer>>) problem);
                pop1 = evaluator.evaluate(pop1, (Problem<PermutationSolution<Integer>>) problem);
                if (group == 1) {
                    if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 2) {
                    if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) && current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2)) ||
                            (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) ||
                            (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) ||
                            (current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 3) {
                    if ((current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 4) {
                    if (current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2)
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }

/*               if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))|| (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) ) )
               {
                //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    //l=0;
                } else {
                    l++;
                }*/
            }

            if (l == 4) {


                pop1.clear();
                current_pop1.clear();

                current_solution = worker_load_balancing(solution, selectFac);
                pop1.add(solution);
                current_pop1.add(current_solution);
                current_pop1 = evaluator.evaluate(current_pop1, (Problem<PermutationSolution<Integer>>) problem);
                pop1 = evaluator.evaluate(pop1, (Problem<PermutationSolution<Integer>>) problem);
                if (group == 1) {
                    if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 2) {
                    if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) && current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2)) ||
                            (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) ||
                            (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) ||
                            (current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 3) {
                    if ((current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 4) {
                    if ((current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }

/*               if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))|| (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) ) )
               {
                //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    //l=0;
                } else {
                    l++;
                }*/
            }

            if (l == 6) {

                pop1.clear();
                current_pop1.clear();

                current_solution = worker_exchange(solution, selectFac);
                pop1.add(solution);
                current_pop1.add(current_solution);
                current_pop1 = evaluator.evaluate(current_pop1, (Problem<PermutationSolution<Integer>>) problem);
                pop1 = evaluator.evaluate(pop1, (Problem<PermutationSolution<Integer>>) problem);
                if (group == 1) {
                    if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 2) {
                    if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) && current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2)) ||
                            (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) ||
                            (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) ||
                            (current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 3) {
                    if ((current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }
                if (group == 4) {
                    if (current_pop1.get(0).getObjective(2) < pop1.get(0).getObjective(2)
                    ) {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        l++;
                    } else {
                        l++;
                    }
                }

/*               if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))|| (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) ) )
               {
                //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    //l=0;
                } else {
                    l++;
                }*/
            }
        }
        return solution;
    }


    //工件序列插入
    public PermutationSolution<Integer> insertion_neighborhood(PermutationSolution<Integer> solution, List<Integer> selectFac) {
        Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        PermutationSolution<Integer> solutionNew = problem.createSolution();
        int a, i, j;
        // PermutationSolution<Integer> solutiontemp = problem.createSolution();
        //List<List<Integer>> t = new ArrayList<>();  //存工厂号下对应的工件序列的下标
        //ArrayList<List<Integer>> N = new ArrayList<>();
        int[][] N = new int[numberOfFactories][solution.getNumberOfVariablesid()];       //存相同工厂的工件下标

        List<Integer> v = new ArrayList<>();
        int[] ind = new int[selectFac.size()];     //存工厂号
//对0，1，2工厂的工件顺序排列
        int[][] len = new int[numberOfFactories][1];
        for (int r = 0; r < numberOfFactories; r++) {
            int h = 0;
            for (int y = 0; y < solution.getNumberOfVariablesid(); y++) {
                if (solution.getVariableValueid(y) == r) {  //等于工厂号的下标
                    N[r][h] = y;     //等于工厂号的下标
                    h++;
                }
            }
            len[r][0] = h;   //工厂的工件个数  0，1，2长度
        }            //没问题

        for (int r = 0; r < selectFac.size(); r++) {
            int m;
            int n;//int hao=0;
            ind[r] = selectFac.get(r);  //几号工厂
            int c = ind[r];             //几号工厂
            int[] rList = new int[len[c][0]];
            for (int k = 0; k < len[c][0]; k++) {
                //rList.add(N[r][k]);            // rList里面存的工件的下标
                rList[k] = N[c][k];      // rList里面存的工件的下标
            }          //没问题

            int t = A.nextInt(rList.length); //m = N[r][t];           // rList里面存的工件的下标
            int g = A.nextInt(rList.length); //n = N[r][g];            //t存的是rList里内容的下标   t下标下对应的是工件本身号

            if (t == g) {
                int end = 0;
                int num = 0;
                while (end != -1) {
                    g = A.nextInt(rList.length); //n = N[r][g];
                    //n =A.nextInt(len[r].length);
                    if (t != g) {
                        end = -1;
                    }
                    num++;
                }
                if (t < g) {
                    // i = m;j = n;
                    i = t;
                    j = g;
                } else {
                    //j = m;i = n;
                    i = g;
                    j = t;
                }
            } else {
                if (t < g) {
                    //i = m;j = n;
                    i = t;
                    j = g;
                } else {
                    //j = m;i = n;
                    i = g;
                    j = t;
                }
            }
            //i，j存的是 rList 里内容(粒子下标)的下标         即N[r]里面的下标

            if (i != 0 && j != rList.length - 1) {
                int jobi = rList[i]; //N[r][i];
                int jobj = rList[j];//N[r][j];
                for (a = 0; a < i; a++) {
                    int jobIdx = rList[a];   //工件的下标
                    int temp1 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp1);
                }
                int temp2 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp2);
                for (a = i; a < j; a++) {
                    int jobIdx = rList[a];
                    int jobIdx1 = rList[a + 1];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx1, temp3);
                }
                for (a = j + 1; a <= rList.length - 1; a++) {
                    int jobIdx = rList[a];
                    int temp4 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp4);
                }
            }   //没问题
            else if (i == 0 && i != j && j != rList.length - 1) {
                int jobi = rList[i];
                int jobj = rList[j];
                int temp1 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp1);
                for (a = i; a < j; a++) {
                    int jobIdx = rList[a];
                    int jobIdx1 = rList[a + 1];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx1, temp3);
                }
                for (a = j + 1; a <= rList.length - 1; a++) {
                    int jobIdx = rList[a];
                    int temp4 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp4);
                }

            }     //没问题
            else if (i == 0 && j == rList.length - 1) {
                int jobi = rList[i];
                int jobj = rList[j];
                int temp1 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp1);
                for (a = i; a < rList.length - 1; a++) {
                    int jobIdx = rList[a];
                    int jobIdx1 = rList[a + 1];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx1, temp3);
                }

            }// 没问题
            else {
                int jobi = rList[i];
                int jobj = rList[j];
                int temp = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp);
                for (a = 0; a < i; a++) {
                    int jobIdx = rList[a];
                    int temp1 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp1);
                }
                    /*int temp2 = solutiontemp.getVariableValue(j);
                    solutionNew.setVariableValue(i, temp2);*/
                for (a = i; a < rList.length - 1; a++) {
                    int jobIdx = rList[a];
                    int jobIdx1 = rList[a + 1];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx1, temp3);
                }
            }   //没问题
        }


        ///////////////////////////////////////////////////////


        int[] no = new int[numberOfFactories];
        for (int d = 0; d < numberOfFactories; d++) {
            no[d] = d;
        }                                            //        int [] no={0,1,2};

        for (int d = 0; d < numberOfFactories; d++) {
            for (int l = 0; l < selectFac.size(); l++) {
                if (selectFac.get(l) == no[d]) no[d] = -1;
            }
        }            //没问题

        for (int d = 0; d < numberOfFactories; d++) {
            if (no[d] != -1) {
                for (a = 0; a < len[d][0]; a++) {
                    int jobIdx = N[d][a];
                    int temp = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp);
                }
            }
        }

        for (a = 0; a < solution.getNumberOfVariablesid(); a++) {
            int temp = solution.getVariableValueid(a);
            solutionNew.setVariableValueid(a, temp);
        }

        return solutionNew;
    }


    //20241223 新的工件序列插入
    public PermutationSolution<Integer> insertion_neighborhood_new(PermutationSolution<Integer> solution, List<Integer> selectFac) {


        List<Integer> variables = solution.getVariables();//工件向量
        List<Integer> variablesid = solution.getVariablesid();//工厂向量


        for (int i = 0; i < selectFac.size(); i++) {
            int factory = selectFac.get(i);
            List<Integer> tempfactory = new ArrayList<>();
            List<Integer> tempsequence = new ArrayList<>();
            for (int i1 = 0; i1 < variablesid.size(); i1++) {
                if (variablesid.get(i1) == factory) {
                    tempfactory.add(i1);//工厂向量的部分
                    tempsequence.add(variables.get(i1));//工序向量的部分
                }
            }

            if (tempsequence == null || tempsequence.size() <= 1) {
                continue;
            }
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int chosenIndex = random.nextInt(tempsequence.size());
            Integer chosenElement = tempsequence.get(chosenIndex);
            int newIndex = 0;
            if (chosenIndex > 0) {
                newIndex = random.nextInt(chosenIndex); // 新索引在[0, chosenIndex-1]之间
            }
            tempsequence.remove(chosenIndex);
            tempsequence.add(newIndex, chosenElement);
            for (int j = 0; j < tempfactory.size(); j++) {
                solution.setVariableValue(tempfactory.get(j), tempsequence.get(j));
            }

        }

        return solution;
    }

    //20241223 新的工件序列交换
    public PermutationSolution<Integer> exchange_neighborhood_new(PermutationSolution<Integer> solution, List<Integer> selectFac) {
        List<Integer> variables = solution.getVariables();//工件向量
        List<Integer> variablesid = solution.getVariablesid();//工厂向量


        for (int i = 0; i < selectFac.size(); i++) {
            int factory = selectFac.get(i);
            List<Integer> tempfactory = new ArrayList<>();
            List<Integer> tempsequence = new ArrayList<>();
            for (int i1 = 0; i1 < variablesid.size(); i1++) {
                if (variablesid.get(i1) == factory) {
                    tempfactory.add(i1);//工厂向量的部分
                    tempsequence.add(variables.get(i1));//工序向量的部分
                }
            }

            if (tempsequence == null || tempsequence.size() <= 1) {
                continue;
            }
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int chosenIndex1 = random.nextInt(tempsequence.size());
            int chosenIndex2 = random.nextInt(tempsequence.size());
            if (chosenIndex1 == chosenIndex2) {
                if (chosenIndex2 + 1 == tempsequence.size()) {
                    chosenIndex2 = chosenIndex2 - 1;
                } else if (chosenIndex2 == 0) {
                    chosenIndex2 = chosenIndex2 + 1;
                }
            }
            int tempindex1 = tempsequence.get(chosenIndex1);
            int tempindex2 = tempsequence.get(chosenIndex2);
            tempsequence.set(chosenIndex1, tempindex2);
            tempsequence.set(chosenIndex2, tempindex1);

            for (int j = 0; j < tempfactory.size(); j++) {
                solution.setVariableValue(tempfactory.get(j), tempsequence.get(j));
            }
        }

        return solution;
    }

    //20241223 新的工件序列翻转
    public PermutationSolution<Integer> reverse_neighborhood_new(PermutationSolution<Integer> solution, List<Integer> selectFac) {
        List<Integer> variables = solution.getVariables();//工件向量
        List<Integer> variablesid = solution.getVariablesid();//工厂向量

        for (int i = 0; i < selectFac.size(); i++) {
            int factory = selectFac.get(i);
            List<Integer> tempfactory = new ArrayList<>();
            List<Integer> tempsequence = new ArrayList<>();
            for (int i1 = 0; i1 < variablesid.size(); i1++) {
                if (variablesid.get(i1) == factory) {
                    tempfactory.add(i1);//工厂向量的部分
                    tempsequence.add(variables.get(i1));//工序向量的部分
                }
            }

            if (tempsequence == null || tempsequence.size() <= 1) {
                continue;
            }
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int startIndex = random.nextInt(tempsequence.size());
            int endIndex = random.nextInt(tempsequence.size());
            if (startIndex > endIndex) {
                int temp = startIndex;
                startIndex = endIndex;
                endIndex = temp;
            }


            if (startIndex < 0 || endIndex >= tempsequence.size() || startIndex > endIndex) {
                throw new IllegalArgumentException("索引无效");
            }

            // 使用双指针法反转子列表
            while (startIndex < endIndex) {
                // 交换元素
                Integer temp = tempsequence.get(startIndex);
                tempsequence.set(startIndex, tempsequence.get(endIndex));
                tempsequence.set(endIndex, temp);

                // 移动指针
                startIndex++;
                endIndex--;
            }

            for (int j = 0; j < tempfactory.size(); j++) {
                solution.setVariableValue(tempfactory.get(j), tempsequence.get(j));
            }

        }

        return solution;
    }

    //20250304 工人负载平衡
    public PermutationSolution<Integer> worker_load_balancing(PermutationSolution<Integer> solution, List<Integer> selectFac) {
        int[][][] workerinfactory = DefaultIntegerPermutationSolution.result;
        Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int stage = solution.getNumberOfVariablesworker() / solution.getNumberOfVariables();
        for (int i = 0; i < selectFac.size(); i++) {

            int currentfactory = selectFac.get(i);

            List<Integer> variablesfactory = solution.getVariablesid();

            List<Integer> positions = new ArrayList<>();
            // 遍历列表
            for (int i1 = 0; i1 < variablesfactory.size(); i1++) {
                if (variablesfactory.get(i1) == currentfactory) {
                    positions.add(i1); // 将索引添加到新列表
                }
            }
            for (int i2 = 0; i2 < stage; i2++) {
                List<Integer> temp = new ArrayList<>();
                Map<Integer, Integer> workermap = new HashMap<>();
                for (int i1 = 0; i1 < positions.size(); i1++) {
                    int index = solution.getNumberOfVariables() * i2 + positions.get(i1);
                    temp.add(solution.getVariableValueworker(index));
                    workermap.put(index, solution.getVariableValueworker(index));
                }

                Map<Integer, Integer> countMap = new HashMap<>();
                for (Integer num : temp) {
                    countMap.put(num, countMap.getOrDefault(num, 0) + 1);
                }

                // 找到出现次数最多和最少的数字
                int maxCount = Integer.MIN_VALUE;
                int minCount = Integer.MAX_VALUE;
                List<Integer> maxNumbers = new ArrayList<>();
                List<Integer> minNumbers = new ArrayList<>();

                for (Map.Entry<Integer, Integer> entry : countMap.entrySet()) {
                    int num = entry.getKey();
                    int count = entry.getValue();

                    // 更新最大值
                    if (count > maxCount) {
                        maxCount = count;
                        maxNumbers.clear();
                        maxNumbers.add(num);
                    } else if (count == maxCount) {
                        maxNumbers.add(num);
                    }

                    // 更新最小值
                    if (count < minCount) {
                        minCount = count;
                        minNumbers.clear();
                        minNumbers.add(num);
                    } else if (count == minCount) {
                        minNumbers.add(num);
                    }
                }

                for (Map.Entry<Integer, Integer> entry : workermap.entrySet()) {
                    if (entry.getValue() == maxNumbers.get(0)) {
//                        workermap.put(entry.getKey(), minNumbers.get(0)); // 修改 value 为 minNumbers
                        solution.setVariableValueworker(entry.getKey(), minNumbers.get(0));
                        break; // 只修改第一个符合条件的条目
                    }
                }

            }

        }


        return solution;
    }

    //20250305 工人互换
    public PermutationSolution<Integer> worker_exchange(PermutationSolution<Integer> solution, List<Integer> selectFac) {
        //        PermutationSolution<Integer> solutionNew = problem.createSolution();
//        System.out.println(solution);
        int[][][] workerinfactory = DefaultIntegerPermutationSolution.result;
        double[][] lw = EDHHFSPW.lw;
//        System.out.println("每个工厂中的每个工人的加工能力");
//        for (double[] doubles : lw) {
//            System.out.println(Arrays.toString(doubles));
//        }
//        System.out.println("每个工厂中每个阶段的工人可以选择哪些");
//        for (int[][] ints : workerinfactory) {
//            for (int[] anInt : ints) {
//                System.out.print(Arrays.toString(anInt) + " ");
//            }
//            System.out.println();
//        }
        Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int stage = solution.getNumberOfVariablesworker() / solution.getNumberOfVariables();
        for (int i = 0; i < selectFac.size(); i++) {

            int currentfactory = selectFac.get(i);

            List<Integer> variablesfactory = solution.getVariablesid();

            List<Integer> positions = new ArrayList<>();//是该工厂包含的工件有哪些
            // 遍历列表
            for (int i1 = 0; i1 < variablesfactory.size(); i1++) {
                if (variablesfactory.get(i1) == currentfactory) {
                    positions.add(i1); // 将索引添加到新列表
                }
            }
            //遍历每个阶段
            for (int i2 = 0; i2 < stage; i2++) {
                int[] ints = workerinfactory[currentfactory][i2];
//                System.out.println("第" + currentfactory + "个工厂第" + i2 + "阶段的工人可以选择" + Arrays.toString(ints));
                if (ints.length > 1) {
                    List<Integer> temp = new ArrayList<>();
                    Map<Integer, Integer> workermap = new HashMap<>();
                    for (int i1 = 0; i1 < positions.size(); i1++) {
                        int index1 = solution.getNumberOfVariables() * i2 + positions.get(i1);
                        temp.add(solution.getVariableValueworker(index1));
                        workermap.put(index1, solution.getVariableValueworker(index1));
                    }
                    Map<Integer, List<Map.Entry<Integer, Integer>>> groupedMap = workermap.entrySet().stream()
                            .collect(Collectors.groupingBy(Map.Entry::getValue));
                    List<Integer> keys = new ArrayList<>(groupedMap.keySet());
                    if (keys.size() < 2) {
                        continue;
                    }
                    org.uma.jmetal.util.research.runtime.SeededRandom.shuffle(keys); // 打乱顺序
                    int firstValue = keys.get(0);
                    int secondValue = keys.get(1);

                    // 获取对应的Map
                    List<Map.Entry<Integer, Integer>> firstMap = groupedMap.get(firstValue);
                    List<Map.Entry<Integer, Integer>> secondMap = groupedMap.get(secondValue);

                    // 3. 从选中的Map中取出随机的键值对
                    Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
                    Map.Entry<Integer, Integer> firstEntry = firstMap.get(random.nextInt(firstMap.size()));
                    Map.Entry<Integer, Integer> secondEntry = secondMap.get(random.nextInt(secondMap.size()));

                    Integer key1 = firstEntry.getKey();
                    Integer key2 = secondEntry.getKey();
                    Integer value1 = firstEntry.getValue();
                    Integer value2 = secondEntry.getValue();

                    solution.setVariableValueworker(key1,value2);
                    solution.setVariableValueworker(key2,value1);

                    // 打印结果
//                    System.out.println("随机选择的第一个键值对: " + firstEntry);
//                    System.out.println("随机选择的第二个键值对: " + secondEntry);
//                    System.out.println("分组后的Map: " + groupedMap);
//                    System.out.println("第" + currentfactory + "个工厂的第" + i2 + "阶段");
//                    System.out.println(workermap);
//                    for (Map.Entry<Integer, Integer> entry : workermap.entrySet()) {
//                        if (entry.getValue() == minindex) {
////                            System.out.println("找到的key: " + entry.getKey());
//                            solution.setVariableValueworker(entry.getKey(), maxindex);
//                            break;
//                        }
//                    }

                }
            }
        }
//        System.out.println(solution);
//        sleep();
        return solution;
    }

    //20250305 根据工人能力进行插入
    public PermutationSolution<Integer> worker_level_insert(PermutationSolution<Integer> solution, List<Integer> selectFac) {
//        PermutationSolution<Integer> solutionNew = problem.createSolution();
//        System.out.println(solution);
        int[][][] workerinfactory = DefaultIntegerPermutationSolution.result;
        double[][] lw = EDHHFSPW.lw;
//        System.out.println("每个工厂中的每个工人的加工能力");
//        for (double[] doubles : lw) {
//            System.out.println(Arrays.toString(doubles));
//        }
//        System.out.println("每个工厂中每个阶段的工人可以选择哪些");
//        for (int[][] ints : workerinfactory) {
//            for (int[] anInt : ints) {
//                System.out.print(Arrays.toString(anInt) + " ");
//            }
//            System.out.println();
//        }
        Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int stage = solution.getNumberOfVariablesworker() / solution.getNumberOfVariables();
        for (int i = 0; i < selectFac.size(); i++) {

            int currentfactory = selectFac.get(i);

            List<Integer> variablesfactory = solution.getVariablesid();

            List<Integer> positions = new ArrayList<>();//是该工厂包含的工件有哪些
            // 遍历列表
            for (int i1 = 0; i1 < variablesfactory.size(); i1++) {
                if (variablesfactory.get(i1) == currentfactory) {
                    positions.add(i1); // 将索引添加到新列表
                }
            }
            //遍历每个阶段
            for (int i2 = 0; i2 < stage; i2++) {
                int[] ints = workerinfactory[currentfactory][i2];
//                System.out.println("第" + currentfactory + "个工厂第" + i2 + "阶段的工人可以选择" + Arrays.toString(ints));
                if (ints.length > 1) {
                    double max = 0;
                    double min = Integer.MAX_VALUE;
                    int maxindex = ints[0];
                    int minindex = ints[0];
                    int index = 0;
                    for (int workerindex = ints[0]; workerindex < ints[0] + ints.length; workerindex++) {
                        double workerleveltemp = lw[currentfactory][workerindex];
                        if (workerleveltemp > max) {
                            max = workerleveltemp;
                            maxindex = ints[index];
                        }
                        if (workerleveltemp < min) {
                            min = workerleveltemp;
                            minindex = ints[index];
                        }
                        index++;
                    }
                    List<Integer> temp = new ArrayList<>();
                    Map<Integer, Integer> workermap = new HashMap<>();
                    for (int i1 = 0; i1 < positions.size(); i1++) {
                        int index1 = solution.getNumberOfVariables() * i2 + positions.get(i1);
                        temp.add(solution.getVariableValueworker(index1));
                        workermap.put(index1, solution.getVariableValueworker(index1));
                    }
//                    System.out.println("第" + currentfactory + "个工厂的第" + i2 + "阶段");
//                    System.out.println(workermap);
                    for (Map.Entry<Integer, Integer> entry : workermap.entrySet()) {
                        if (entry.getValue() == minindex) {
//                            System.out.println("找到的key: " + entry.getKey());
                            solution.setVariableValueworker(entry.getKey(), maxindex);
                            break;
                        }
                    }

                }
            }
        }
//        System.out.println(solution);
//        sleep();
        return solution;
    }

    //20241205 机器序列交换
    public PermutationSolution<Integer> exchange_neighborhood_machine(PermutationSolution<Integer> solution, List<Integer> selectFac) {
//        PermutationSolution<Integer> solutionNew = problem.createSolution();
        List<Integer> variables4factory = solution.getVariablesid();
        List<Integer> variables4job = solution.getVariables();
        List<Integer> machine = (List<Integer>) solution.getAttribute("machine");
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();

        // 遍历 selectFac 中的每个工厂
        for (int factory : selectFac) {
            // 找到该工厂对应的工件索引和机器选择
            List<Integer> jobIndices = new ArrayList<>();
            List<Integer> machinesInFactory = new ArrayList<>();
            for (int i = 0; i < variables4factory.size(); i++) {
                if (variables4factory.get(i) == factory) {
                    jobIndices.add(i);
                    machinesInFactory.add(machine.get(i));
                }
            }

            // 随机选择一个机器
            int selectedMachine = machinesInFactory.get(random.nextInt(machinesInFactory.size()));

            // 随机选择一个插入位置
            int insertPosition = random.nextInt(machinesInFactory.size());

            // 插入到随机位置
            machinesInFactory.add(insertPosition, selectedMachine);

            // 更新 machine 列表
            for (int i = 0; i < jobIndices.size(); i++) {
                machine.set(jobIndices.get(i), machinesInFactory.get(i));
            }
        }

        return solution;
    }

    //20241205 机器序列插入
    public PermutationSolution<Integer> insert_neighborhood_machine(PermutationSolution<Integer> solution, List<Integer> selectFac) {
//        PermutationSolution<Integer> solutionNew = problem.createSolution();
        List<Integer> variables4factory = solution.getVariablesid();
        List<Integer> variables4job = solution.getVariables();
        List<Integer> machine = (List<Integer>) solution.getAttribute("machine");
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();

        // 遍历 selectFac 中的每个工厂
        for (int factory : selectFac) {
            // 找到该工厂对应的工件索引和机器选择
            List<Integer> jobIndices = new ArrayList<>();
            List<Integer> machinesInFactory = new ArrayList<>();
            for (int i = 0; i < variables4factory.size(); i++) {
                if (variables4factory.get(i) == factory) {
                    jobIndices.add(i);
                    machinesInFactory.add(machine.get(i));
                }
            }

            // 随机选择一个机器
            int i1 = random.nextInt(machinesInFactory.size());
            int selectedMachine = machinesInFactory.get(i1);
            machinesInFactory.remove(i1);
            // 随机选择一个插入位置
            int insertPosition = random.nextInt(machinesInFactory.size());

            // 插入到随机位置
            machinesInFactory.add(insertPosition, selectedMachine);

            // 更新 machine 列表
            for (int i = 0; i < jobIndices.size(); i++) {
                machine.set(jobIndices.get(i), machinesInFactory.get(i));
            }
        }

        solution.setAttribute("machine", machine);

        return solution;
    }
    //20241205 机器序列倒序


    //工件序列交换
    public PermutationSolution<Integer> exchange_neighborhood(PermutationSolution<Integer> solution, List<Integer> selectFac) {
        Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        PermutationSolution<Integer> solutionNew = problem.createSolution();
        int a, i, j, b;
        // PermutationSolution<Integer> solutiontemp = problem.createSolution();
        //List<List<Integer>> t = new ArrayList<>();  //存工厂号下对应的工件序列的下标
        //ArrayList<List<Integer>> N = new ArrayList<>();
        int[][] N = new int[numberOfFactories][solution.getNumberOfVariablesid()];

        List<Integer> v = new ArrayList<>();
        int[] ind = new int[selectFac.size()];     //存工厂号
//对0，1，2工厂的工件顺序排列
        int[][] len = new int[numberOfFactories][1];
        for (int r = 0; r < numberOfFactories; r++) {
            int h = 0;
            for (int y = 0; y < solution.getNumberOfVariablesid(); y++) {
                if (solution.getVariableValueid(y) == r) {  //等于工厂号的下标
                    N[r][h] = y;     //等于工厂号的下标
                    h++;
                }
            }
            len[r][0] = h;   //工厂的工件个数  0，1，2长度
        }

        for (int r = 0; r < selectFac.size(); r++) {
            int m, n;
            ind[r] = selectFac.get(r);  //几号工厂

            int c = ind[r];
            int[] rList = new int[len[c][0]];
            for (int k = 0; k < len[c][0]; k++) {
                //rList.add(N[r][k]);            // rList里面存的工件的下标
                rList[k] = N[c][k];      // rList里面存的工件的下标
            }

///////////////////////////////////////没问题

            int t = A.nextInt(rList.length); //m = N[r][t];           // rList里面存的工件的下标
            int g = A.nextInt(rList.length); //n = N[r][g];            //t存的是rList里内容的下标   t下标下对应的是工件本身号

            if (t == g) {
                int end = 0;
                while (end != -1) {
                    g = A.nextInt(rList.length); //n = N[r][g];
                    //n =A.nextInt(len[r].length);
                    if (t != g) {
                        end = -1;
                    }
                }
                if (t < g) {
                    // i = m;j = n;
                    i = t;
                    j = g;
                } else {
                    //j = m;i = n;
                    i = g;
                    j = t;
                }
            } else {
                if (t < g) {
                    //i = m;j = n;
                    i = t;
                    j = g;
                } else {
                    //j = m;i = n;
                    i = g;
                    j = t;
                }
            }
            if (i != 0 && (j != rList.length - 1)) {
                for (a = 0; a < i; a++) {
                    int jobIdx = rList[a];
                    int temp1 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp1);
                }
                int jobi = rList[i];
                int jobj = rList[j];
                int temp2 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp2);
                int temp4 = solution.getVariableValue(jobi);
                solutionNew.setVariableValue(jobj, temp4);
                for (a = i + 1; a < j; a++) {
                    int jobIdx = rList[a];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp3);
                }

                for (a = j + 1; a <= rList.length - 1; a++) {
                    int jobIdx = rList[a];
                    int temp5 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp5);
                }
                //System.out.println(solutionNew);
            } else if (i == 0 && j == rList.length - 1) {
                int jobi = rList[i];
                int jobj = rList[j];
                int temp1 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp1);
                int temp2 = solution.getVariableValue(jobi);
                solutionNew.setVariableValue(jobj, temp2);
                for (a = i + 1; a < rList.length - 1; a++) {
                    int jobIdx = rList[a];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp3);
                }
                //System.out.println(solutionNew);
            } else if (i == 0 && j != (rList.length - 1)) {
                int jobi = rList[i];
                int jobj = rList[j];
                int temp1 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp1);
                for (a = i + 1; a < j; a++) {
                    int jobIdx = rList[a];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp3);
                }
                int temp2 = solution.getVariableValue(jobi);
                solutionNew.setVariableValue(jobj, temp2);
                for (a = j + 1; a <= (rList.length - 1); a++) {
                    int jobIdx = rList[a];
                    int temp4 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp4);
                }
                //System.out.println(solutionNew);
            } else {
                //if(i!=0 && j==rList.length-1){
                for (a = 0; a < i; a++) {
                    int jobIdx = rList[a];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp3);
                }
                int jobi = rList[i];
                int jobj = rList[j];
                int temp1 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp1);

                int temp2 = solution.getVariableValue(jobi);
                solutionNew.setVariableValue(jobj, temp2);
                for (a = i + 1; a < (rList.length - 1); a++) {
                    int jobIdx = rList[a];
                    int temp4 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp4);
                }
                //System.out.println(solutionNew);
            }


        }

/////////////////////////////////////////////////////////////
        int[] no = new int[numberOfFactories];
        for (int d = 0; d < numberOfFactories; d++) {
            no[d] = d;
        }
        //int [] no={0,1,2};
        for (int d = 0; d < numberOfFactories; d++) {
            for (int l = 0; l < selectFac.size(); l++) {
                if (selectFac.get(l) == no[d]) no[d] = -1;
            }
        }

        for (int d = 0; d < numberOfFactories; d++) {
            if (no[d] != -1) {
                for (a = 0; a < len[d][0]; a++) {
                    int jobIdx = N[d][a];
                    int temp = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp);
                }
            }
        }
        //System.out.println(solutionNew);

        for (a = 0; a < solution.getNumberOfVariablesid(); a++) {
            int temp = solution.getVariableValueid(a);
            solutionNew.setVariableValueid(a, temp);
        }

        return solutionNew;
    }

    public double calculateNewQ(double r, double q) {
        return (r + gamma * q);
    }

    public int getMaxQ(double[][] Q) {
        int maxQ = 0;
        for (int i = 0; i < Q.length; i++) {
            if (Q[0][i] > Q[0][maxQ]) maxQ = i;
        }
        return maxQ;
    }


    /**
     * @param swarm             没有局部搜索的种群
     * @param swarm2            局部搜索后的种群
     * @param DEswarmtempPdflag
     * @return
     */
    protected List<PermutationSolution<Integer>> PDDRFFselect(List<PermutationSolution<Integer>> swarm,
                                                              List<PermutationSolution<Integer>> swarm2, int[] DEswarmtempPdflag) {

        List<PermutationSolution<Integer>> swarmtemp = new ArrayList<>(swarm.size());

        int swarmSize = swarm.size() + swarm2.size();        // 分群后的原始种群 M(t) + DE后的种群M’(t)
        List<PermutationSolution<Integer>> temp2 = new ArrayList<>(swarmSize);
        ArrayList<List<PermutationSolution<Integer>>> tempPd2 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);
        ArrayList<List<int[]>> tempPd2flag = new ArrayList<List<int[]>>();

        for (int i = 0; i < swarm.size(); i++) {
            temp2.add((PermutationSolution<Integer>) swarm.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(tempSwarm.get(i).size());
            ArrayList<int[]> B = new ArrayList<int[]>();

            for (int j = 0; j < tempSwarm.get(i).size(); j++) {

                A.add((PermutationSolution<Integer>) tempSwarm.get(i).get(j).copy());


            }
            tempPd2.add(A);
            tempPd2flag.add(B);
        }

        for (int i = 0; i < swarm2.size(); i++) {
            temp2.add((PermutationSolution<Integer>) swarm2.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(tempSwarm.get(DEswarmtempPdflag[i]).size());
            ArrayList<int[]> B = new ArrayList<int[]>();

            for (int j = 0; j < tempSwarm.get(DEswarmtempPdflag[i]).size(); j++) {

                A.add((PermutationSolution<Integer>) tempSwarm.get(DEswarmtempPdflag[i]).get(j).copy());
            }
            tempPd2.add(A);
            tempPd2flag.add(B);
        }


        List<Double> aa = new ArrayList<>(swarmSize);    // 原始种群个数的两倍
        for (int i = 0; i < swarmSize; i++) {
            double count1 = 0;
            double count2 = 0;
            for (int j = 0; j < swarmSize; j++) {
                if (i != j) {
                    if (temp2.get(i).getObjective(0) <= temp2.get(j).getObjective(0) &&
                            temp2.get(i).getObjective(1) <= temp2.get(j).getObjective(1)
                            && temp2.get(i).getObjective(2) <= temp2.get(j).getObjective(2)
                    ) {
                        count1 = count1 + 1;
                    }
                    if (temp2.get(i).getObjective(0) >= temp2.get(j).getObjective(0) &&
                            temp2.get(i).getObjective(1) >= temp2.get(j).getObjective(1)
                            && temp2.get(i).getObjective(2) >= temp2.get(j).getObjective(2)
                    ) {
                        count2 = count2 + 1;
                    }
                }
            }
            aa.add(count2 + 1 / (count1 + 1));
        }

        tempSwarm.clear();
        //Pdflag.clear();

        for (int i = 0; i < swarm.size(); i++) {
            int b = 0;
            for (int j = 1; j < aa.size(); j++) {
                if (aa.get(j) < aa.get(b)) {
                    b = j;
                }
            }
            swarmtemp.add(temp2.get(b));
            tempSwarm.add(tempPd2.get(b));
            //Pdflag.add(tempPd2flag.get(b));

            aa.remove(b);
            tempPd2.remove(b);
            temp2.remove(b);
            tempPd2flag.remove(b);
        }
        swarm = swarmtemp;   //新加


//        if (t%10==0){
//            System.out.println(t);
//            System.out.println("--------");
//            for (int i=0;i<swarm.size();i++){
////                System.out.print(swarm.get(i).getObjective(0)+"    "+swarm.get(i).getObjective(1));
//                System.out.println(swarm.get(i).getObjective(0));
//            }
//            for (int i=0;i<swarm.size();i++){
//                System.out.println(swarm.get(i).getObjective(1));
//            }
//            System.out.println("--------");
//        }
//        t=t+1;

//        System.out.println("swarm.size"+swarm.size());
//
//        try {
//            Thread.sleep(999999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
        return swarm;   //  原始种群的个数
    }


    private ArrayList<SO> getDifferenceOfJobSequenceVectorByExchangeSequence(PermutationSolution<Integer> a, PermutationSolution<Integer> b) {
        PermutationSolution<Integer> tempb = (PermutationSolution<Integer>) b.copy();

        int index;
        // 交换子
        SO s;
        // 交换序列
        ArrayList<SO> list = new ArrayList<SO>();
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int boundflag = random.nextInt(b.getNumberOfVariables());

        for (int i = boundflag; i < b.getNumberOfVariables(); i++) {
            if (a.getVariableValue(i) != tempb.getVariableValue(i)) {

                // 在temp中找出与a[i]相同数值的下标index
                index = findSameIndexFromJobSequence(tempb, a.getVariableValue(i));
                // 在temp中交换下标i与下标index的值
                exchangeIndex4JobSequenceVectorByExchangeSequence(tempb, i, index);
                // 记住交换子
                s = new SO(i, index);
                // 保存交换子
                list.add(s);
            }
        }

        for (int i = 0; i < boundflag; i++) {
            if (a.getVariableValue(i) != tempb.getVariableValue(i)) {

                // 在temp中找出与a[i]相同数值的下标index
                index = findSameIndexFromJobSequence(tempb, a.getVariableValue(i));
                // 在temp中交换下标i与下标index的值
                exchangeIndex4JobSequenceVectorByExchangeSequence(tempb, i, index);
                // 记住交换子
                s = new SO(i, index);
                // 保存交换子
                list.add(s);
            }
        }

        return list;
    }

    private int findSameIndexFromJobSequence(PermutationSolution<Integer> a, int num) {
        int index = -1;
        for (int i = 0; i < a.getNumberOfVariables(); i++) {
            if (a.getVariableValue(i) == num) {
                index = i;
                break;
            }
        }
        return index;
    }

    private void getCrossOfFactoryVectorBySingle(PermutationSolution<Integer> a, PermutationSolution<Integer> b) {       //对工厂向量进行单点交叉
        int index;
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int boundflag = random.nextInt(b.getNumberOfVariablesid());          //  随机产生一个单点下标
        for (int i = boundflag; i < b.getNumberOfVariablesid(); i++) {
            index = i;
            cross4FactoryVectorBySingle(a, b, i, index);   //交换下标i与下标index的值
        }
    }

    private void cross4FactoryVectorBySingle(PermutationSolution<Integer> a, PermutationSolution<Integer> b, int index1, int index2) {     //交换值
        int temp1 = a.getVariableValueid(index1);    //工厂
        int temp2 = b.getVariableValueid(index2);
        int stage = a.getNumberOfVariablesworker() / a.getNumberOfVariables();

        int[][][] workerinfactory = DefaultIntegerPermutationSolution.result;
//        System.out.println(a);
//        System.out.println(b);

        for (int i = 0; i < stage; i++) {
//            System.out.println(a.getNumberOfVariables());
            int workerneedexchange = a.getNumberOfVariables() * i + index1;
//            System.out.println("workerneedexchange"+workerneedexchange);
//            System.out.println("index1"+index1);
            int workertemp1 = a.getVariableValueworker(workerneedexchange);
            int workertemp2 = b.getVariableValueworker(workerneedexchange);
            a.setVariableValueworker(workerneedexchange, workertemp2);
            b.setVariableValueworker(workerneedexchange, workertemp1);
        }
//        System.out.println(stage);
//        System.out.println(a);
//        System.out.println(b);

        a.setVariableValueid(index1, temp2);
        b.setVariableValueid(index2, temp1);
//        System.out.println(a);
//        System.out.println(b);
//        sleep();

    }


    private ArrayList<SO> getDifferenceOfFactoryVectorByExchangeSequence(PermutationSolution<Integer> a, PermutationSolution<Integer> b) {
        //TODO 为什么针对工厂向量计算交换序？
        //因为对工厂向量用了DE所以就使用交换序来进行
        //  做差 得到交换序
        PermutationSolution<Integer> tempb = (PermutationSolution<Integer>) b.copy();

        int index;
        // 交换子
        SO s;
        // 交换序列
        ArrayList<SO> list = new ArrayList<SO>();
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int boundflag = random.nextInt(b.getNumberOfVariablesid());          //  随机产生交换序的第一个下标

        for (int i = boundflag; i < b.getNumberOfVariablesid(); i++) {
            if (a.getVariableValueid(i) != tempb.getVariableValueid(i)) {

                // 在temp中找出与a[i]相同数值的下标index
                index = findSameIndexFromFactoryVector(tempb, a.getVariableValueid(i));
                if (index == -1) {
                    continue;
                }
                // 在temp中交换下标i与下标index的值
                exchangeIndex4FactoryVectorByExchangeSequence(tempb, i, index);
                // 记住交换子
                s = new SO(i, index);
                // 保存交换子
                list.add(s);
            }
        }

        for (int i = 0; i < boundflag; i++) {
            if (a.getVariableValueid(i) != tempb.getVariableValueid(i)) {

                // 在temp中找出与a[i]相同数值的下标index
                index = findSameIndexFromFactoryVector(tempb, a.getVariableValueid(i));
                // 在temp中交换下标i与下标index的值
                if (index == -1) {
                    continue;
                }
                exchangeIndex4FactoryVectorByExchangeSequence(tempb, i, index);
                // 记住交换子
                s = new SO(i, index);
                // 保存交换子
                list.add(s);
            }
        }

        return list;
    }

    private int findSameIndexFromFactoryVector(PermutationSolution<Integer> a, int num) {
        int index = -1;
        for (int i = 0; i < a.getNumberOfVariablesid(); i++) {
            if (a.getVariableValueid(i) == num) {
                index = i;
                break;
            }
        }
        return index;
    }

    private void exchangeIndex4JobSequenceVectorByExchangeSequence(PermutationSolution<Integer> a, int index1, int index2) {
        int temp1 = a.getVariableValue(index1);
        int temp2 = a.getVariableValue(index2);

        a.setVariableValue(index1, temp2);
        a.setVariableValue(index2, temp1);

    }

    private void addNew4JobSequenceVectorByExchangeSequence(PermutationSolution<Integer> arr, ArrayList<SO> list) {
        SO s;

        for (int i = 0; i < list.size(); i++) {
            s = list.get(i);

            exchangeIndex4JobSequenceVectorByExchangeSequence(arr, s.getX(), s.getY());

        }

    }

    private void addNew4FactoryVectorByExchangeSequence(PermutationSolution<Integer> arr, ArrayList<SO> list) {
        SO s;
        for (int i = 0; i < list.size(); i++) {
            s = list.get(i);
            exchangeIndex4FactoryVectorByExchangeSequence(arr, s.getX(), s.getY());             //      根据下标交换值
        }
    }

    /***
     *
     * @param arr 解
     * @param list 对于哪一位的工厂进行突变
     */
    private void addNew4FactoryVectorByRandom(PermutationSolution<Integer> arr, ArrayList<ST> list) {
        ST s;
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int factorysize = EDHHFSPW.numberOfMachines_.length;

        for (int i = 0; i < list.size(); i++) {
            s = list.get(i);
            int r = random.nextInt(factorysize); //TODO 为什么写成了3? 难道是因为3个工厂吗？
            exchangeIndex4FactoryVectorByRandom(arr, s.getX(), r);             //   随机选一位数进行改变
        }
    }

    /***
     *
     * @param a 解
     * @param index1 变异的位置
     * @param value 变成哪个
     */
    private void exchangeIndex4FactoryVectorByRandom(PermutationSolution<Integer> a, int index1, int value) {     //交换值
        //int temp1 =  a.getVariableValueid(index1);
//        System.out.println(a);
//        System.out.println("变异位置"+index1);
        a.setVariableValueid(index1, value);
        int[][][] workerinfactory = DefaultIntegerPermutationSolution.result;
        int stage = a.getNumberOfVariablesworker() / a.getNumberOfVariables();
        for (int i = 0; i < stage; i++) {
            int i1 = a.getNumberOfVariables() * i + index1;
            Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int worker = r.nextInt(workerinfactory[value][i].length);
            int workerchoose = workerinfactory[value][i][worker];
            a.setVariableValueworker(i1, workerchoose);
        }
//        System.out.println(a);


    }


    private void exchangeIndex4FactoryVectorByExchangeSequence(PermutationSolution<Integer> a, int index1, int index2) {     //交换值
        int temp1 = a.getVariableValueid(index1);    //工厂
        int temp2 = a.getVariableValueid(index2);
//        System.out.println("index1="+index1);
//        System.out.println("index2="+index2);
        a.setVariableValueid(index1, temp2);
        a.setVariableValueid(index2, temp1);
    }

    private static void sleep() {
        try {
            Thread.sleep(99999);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
    }


    @Override  //更新个体历史最优
    protected void updateLeaders(List<PermutationSolution<Integer>> swarm) {

        //todo 这里也是精英解吗
        //添加
        for (int j = 0; j < swarm.size(); j++) {
            tempSwarm.get(j).add((PermutationSolution<Integer>) swarm.get(j).copy());
//            System.out.println(j);
        }
//        System.out.println("tempswarm.size="+tempSwarm.size());

        //去重
        for (int i = 0; i < swarm.size(); i++) {
            for (int j = 0; j < tempSwarm.get(i).size(); j++) {
                for (int k = j + 1; k < tempSwarm.get(i).size(); k++) {
                    if (tempSwarm.get(i).get(j).getObjective(0) <= tempSwarm.get(i).get(k).getObjective(0) &&
                            tempSwarm.get(i).get(j).getObjective(1) <= tempSwarm.get(i).get(k).getObjective(1) &&
                            tempSwarm.get(i).get(j).getObjective(2) <= tempSwarm.get(i).get(k).getObjective(2)) {
                        tempSwarm.get(i).remove(k);
                        k--;
                    }
                }
                for (int k = j + 1; k < tempSwarm.get(i).size(); k++) {
                    if (tempSwarm.get(i).get(j).getObjective(0) >= tempSwarm.get(i).get(k).getObjective(0) &&
                            tempSwarm.get(i).get(j).getObjective(1) >= tempSwarm.get(i).get(k).getObjective(1) &&
                            tempSwarm.get(i).get(j).getObjective(2) >= tempSwarm.get(i).get(k).getObjective(2)) {
                        tempSwarm.get(i).remove(j);
                        j--;
                        break;
                    }
                }
            }
        }

//        Thread.sleep(999999);
    }


    private int index = 1;

    @Override  //更新全局最优
    protected void updateParticlesMemory(List<PermutationSolution<Integer>> swarm) {


//        System.out.println("swarm.size="+swarm.size());
//        try {
//            Thread.sleep(9999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
        //添加

        //todo 这里是全局最优，也就是精英解？
//        for (int k = 0; k < swarm.size(); k++) {
        for (int k = 0; k < swarm.size(); k++) {
            globallyOptimalIndividual.add((PermutationSolution<Integer>) tempSwarm.get(k).get(tempSwarm.get(k).size() - 1).copy());
        }

        //去重
        for (int i = 0; i < globallyOptimalIndividual.size(); i++) {
            for (int j = i + 1; j < globallyOptimalIndividual.size(); j++) {
                if ((globallyOptimalIndividual.get(i).getObjective(0) <= globallyOptimalIndividual.get(j).getObjective(0) &&
                        globallyOptimalIndividual.get(i).getObjective(1) <= globallyOptimalIndividual.get(j).getObjective(1)
                        && globallyOptimalIndividual.get(i).getObjective(2) <= globallyOptimalIndividual.get(j).getObjective(2)
                )) {
//                    System.out.println("执行了");
                    globallyOptimalIndividual.remove(j);
                    j--;
                }
            }
            for (int j = i + 1; j < globallyOptimalIndividual.size(); j++) {
                if ((globallyOptimalIndividual.get(i).getObjective(0) >= globallyOptimalIndividual.get(j).getObjective(0) &&
                        globallyOptimalIndividual.get(i).getObjective(1) >= globallyOptimalIndividual.get(j).getObjective(1)
                        && globallyOptimalIndividual.get(i).getObjective(2) >= globallyOptimalIndividual.get(j).getObjective(2)
                )) {
                    globallyOptimalIndividual.remove(i);
                    i--;
                    break;
                }
            }
//            Thread.sleep(999999);
        }
//        System.out.println("globallyOptimalIndividual.size"+globallyOptimalIndividual.size());


//        if (t%100==0||t==498)
//        {
//            System.out.println(t);
//            System.out.println("---------------");
//            for (int i=0;i<globallyOptimalIndividual.size();i++){
//                System.out.println(globallyOptimalIndividual.get(i).getObjective(0));
//            }
//            for (int i=0;i<globallyOptimalIndividual.size();i++){
//                System.out.println(globallyOptimalIndividual.get(i).getObjective(1));
//            }
//            System.out.println("---------------");
//        }
//        t=t+1;
        double object1 = Double.MAX_VALUE;
        double object2 = Double.MAX_VALUE;
        double object3 = Double.MAX_VALUE;
        for (PermutationSolution<Integer> integerPermutationSolution : globallyOptimalIndividual) {
            if (object1 > integerPermutationSolution.getObjective(0))
                object1 = integerPermutationSolution.getObjective(0);
            if (object2 > integerPermutationSolution.getObjective(1))
                object2 = integerPermutationSolution.getObjective(1);
            if (object3 > integerPermutationSolution.getObjective(2))
                object3 = integerPermutationSolution.getObjective(2);
        }
        System.out.println("第" + index + "代：" + "object1=" + object1 + " " + "object2=" + object2 + " " + "object3=" + object3);
        index++;
    }

    @Override
    public List<PermutationSolution<Integer>> getResult() {
        return globallyOptimalIndividual;
    }

    @Override
    public String getName() {
        return "MOPSODivideSubgroup";
    }

    @Override
    public String getDescription() {
        return "Optimized MOPSODivideSubgroup";
    }


    //todo
    protected void exchange4WorkerSequence(PermutationSolution<Integer> swarm) {
        int[] nw = DHFSP.nw;
        int[] tempArray = new int[swarm.getVariablesworker().size()];
        for (int i = 0; i < swarm.getVariablesworker().size(); i++) {
            tempArray[i] = swarm.getVariableValueworker(i);
        }
        List<List<Integer>> lists = segmentArray(tempArray, nw);

        for (List<Integer> list : lists) {
            int r1, r2;
            r1 = randomGenerator.nextInt(0, list.size() - 1);
            r2 = randomGenerator.nextInt(0, list.size() - 1);
            if (r1 != r2) {
                exchangeIndex4WorkerSequenceVectorByExchangeSequence(r1, r2, list);
            }
        }
//        System.out.println(swarm);
        int tempindex = 0;
        for (List<Integer> list : lists) {
            for (Integer i : list) {
                swarm.setVariableValueworker(tempindex, i);
                tempindex++;
            }
        }
//        System.out.println(swarm);
//        sleep();
    }

    protected void exchangeIndex4WorkerSequenceVectorByExchangeSequence(int r1, int r2, List<Integer> list) {
//        Integer variableValueworker1 = swarm.getVariableValueworker(r1);
//        Integer variableValueworker2 = swarm.getVariableValueworker(r2);
//        swarm.setVariableValueworker(r1,variableValueworker2);
//        swarm.setVariableValueworker(r2,variableValueworker1);
//        System.out.println(list);
//        System.out.println(r1);
//        System.out.println(r2);
        Integer i1 = list.get(r1);
        Integer i2 = list.get(r2);
        list.set(r1, i2);
        list.set(r2, i1);
    }


    public static List<List<Integer>> segmentArray(int[] solution, int[] nw) {
        List<List<Integer>> segments = new ArrayList<>();
        int currentIndex = 0;

        for (int stepLength : nw) {
            if (currentIndex + stepLength > solution.length) {
                throw new IllegalArgumentException("Step length exceeds the remaining array size");
            }

            // 获取当前步长的子数组
            List<Integer> segment = new ArrayList<>();
            for (int i = currentIndex; i < currentIndex + stepLength; i++) {
                segment.add(solution[i]);
            }

            // 将子数组添加到结果列表中
            segments.add(segment);

            // 更新当前索引
            currentIndex += stepLength;
        }

        return segments;
    }

    //工人交换
    public static void exchangeWorker(int[][] array, List<Integer> rowsToAdjust) {
        Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();

        for (int row : rowsToAdjust) {
            if (row < 0 || row >= array.length) {
                throw new IllegalArgumentException("Row index out of bounds");
            }

            int[] currentRow = array[row];
            int length = currentRow.length;

            if (length < 2) {
                continue; // 如果行长度小于2，无法进行交换
            }

            // 随机选择两个不同的元素索引
            int index1 = A.nextInt(length);
            int index2 = A.nextInt(length);

            // 确保两个索引不同
            while (index1 == index2) {
                index2 = A.nextInt(length);
            }

            // 交换这两个元素
            int temp = currentRow[index1];
            currentRow[index1] = currentRow[index2];
            currentRow[index2] = temp;
        }
    }

    //    工人倒序
    public static void reverseWorker(int[][] array, List<Integer> rowsToAdjust) {
        Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();

        for (int row : rowsToAdjust) {
            if (row < 0 || row >= array.length) {
                throw new IllegalArgumentException("Row index out of bounds");
            }

            int[] currentRow = array[row];
            int length = currentRow.length;

            if (length < 2) {
                continue; // 如果行长度小于2，无法进行调整
            }

            // 随机选择两个不同的元素索引
            int index1 = A.nextInt(length);
            int index2 = A.nextInt(length);

            // 确保两个索引不同
            while (index1 == index2) {
                index2 = A.nextInt(length);
            }

            // 确保 index1 < index2
            if (index1 > index2) {
                int temp = index1;
                index1 = index2;
                index2 = temp;
            }

            // 对选定范围内的元素进行倒序操作
            reverseSubArray(currentRow, index1, index2);
        }
    }

    public static void reverseSubArray(int[] array, int start, int end) {
        while (start < end) {
            int temp = array[start];
            array[start] = array[end];
            array[end] = temp;
            start++;
            end--;
        }
    }


    //工人插入
    public static void insertWorker(List<List<Integer>> matrix, List<Integer> indices) {
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        for (int index : indices) {
            if (index >= 0 && index < matrix.size()) {
                List<Integer> row = matrix.get(index);
                // 随机选择一个元素的位置
                int elementPos = 0;
                while (elementPos == 0) {
                    elementPos = random.nextInt(row.size());
                }

                // 再次随机选择一个新的位置（不能与原位置相同）
                int newPos = elementPos;
                while (newPos == elementPos) {
                    newPos = random.nextInt(elementPos + 1); // 新位置必须在原位置之前

                }
                // 将选中的元素移动到新的位置
                moveElement(row, elementPos, newPos);
            }
        }
    }

    private static void moveElement(List<Integer> row, int fromIndex, int toIndex) {
        int element = row.get(fromIndex);
        // 删除原位置的元素
        row.remove(fromIndex);
        // 插入到新位置
        row.add(toIndex, element);
    }


    public static void replaceWorkerInSolution(int[][] array, List<Integer> replacementList) {
        if (replacementList.size() != countElements(array)) {
            throw new IllegalArgumentException("Replacement list size does not match the number of elements in the array");
        }

        int arrayIndex = 0;

        for (int i = 0; i < array.length; i++) {
            for (int j = 0; j < array[i].length; j++) {
                replacementList.set(arrayIndex++, array[i][j]);
            }
        }
    }

    public static int countElements(int[][] array) {
        int count = 0;
        for (int[] row : array) {
            count += row.length;
        }
        return count;
    }

    //二维数组转一维数组
    public static int[] flatten(int[][] matrix) {
        // 计算总元素数量
        int totalSize = 0;
        for (int[] row : matrix) {
            totalSize += row.length;
        }

        // 创建一维数组
        int[] result = new int[totalSize];
        int index = 0;

        // 遍历二维数组并将元素添加到一维数组中
        for (int[] row : matrix) {
            for (int element : row) {
                result[index++] = element;
            }
        }

        return result;
    }

    public static void crossover4workersequence(PermutationSolution<Integer> HisOptIndividual, PermutationSolution<Integer> particle, int[] nw) {
        List<Integer> variablesworker1 = HisOptIndividual.getVariablesworker();
        List<Integer> variablesworker2 = particle.getVariablesworker();

        List<Integer> variablesid1 = HisOptIndividual.getVariablesid();
        List<Integer> variablesid2 = particle.getVariablesid();

        int numberOfVariables = HisOptIndividual.getNumberOfVariables();//每一阶段的工件数

        int stage = variablesworker1.size() / HisOptIndividual.getNumberOfVariables();
//        System.out.println("stage"+stage);
//        System.out.println(HisOptIndividual);
//        System.out.println(particle);

        for (int i = 0; i < stage; i++) {
            int begin = numberOfVariables * i;
//            int end = numberOfVariables*i+numberOfVariables-1;

            Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int r1 = r.nextInt(numberOfVariables);//5
            int r2 = r.nextInt(numberOfVariables);//9
//            int random1 = r1+begin;
//            int random2 = r2+begin;
//
            if (r1 > r2) {
                int temp;
                temp = r1;
                r1 = r2;
                r2 = temp;
            }
//            System.out.println("第"+i+"阶段的起始是："+r1);
//            System.out.println("第"+i+"阶段的终止是："+r2);

            //getVariablesid()这是工厂向量
//            System.out.println(HisOptIndividual.getVariablesid());
//            System.out.println(HisOptIndividual.getVariableValueid(14));
            for (int i1 = r1; i1 < r2; i1++) {
                int index = i1 + begin;
                if (HisOptIndividual.getVariableValueid(i1) == particle.getVariableValueid(i1)) {
                    Integer variableValueworker1 = HisOptIndividual.getVariableValueworker(index);
                    Integer variableValueworker2 = particle.getVariableValueworker(index);
//                    System.out.println("index"+index+",variableValueworker1:"+variableValueworker1+",variableValueworker2:"+variableValueworker2);
                    HisOptIndividual.setVariableValueworker(index, variableValueworker2);
                    particle.setVariableValueworker(index, variableValueworker1);
                }
            }

        }


//        System.out.println(HisOptIndividual);
//        System.out.println(particle);
//        sleep();
    }

    private static List<int[]> calculateBlocks(int[] nw, int listSize) {
        List<int[]> blocks = new ArrayList<>();
        int currentIndex = 0;

        for (int step : nw) {
            if (currentIndex < listSize) {
                int endIndex = Math.min(currentIndex + step, listSize);
                blocks.add(new int[]{currentIndex, endIndex});
                currentIndex = endIndex;
            }
        }

        // 处理剩余部分，如果有的话
        if (currentIndex < listSize) {
            blocks.add(new int[]{currentIndex, listSize});
        }

        return blocks;
    }

    private static void swapBlocks(List<Integer> a1, List<Integer> a2, int start, int end) {
        // 创建临时列表来保存 a1 的分块
        List<Integer> temp = new ArrayList<>(a1.subList(start, end));

        // 用 a2 的分块替换 a1 的分块
        for (int i = start; i < end; i++) {
            a1.set(i, a2.get(i));
        }

        // 用 a1 的分块（现在在 temp 中）替换 a2 的分块
        for (int i = start; i < end; i++) {
            a2.set(i, temp.get(i - start));
        }
    }

    //机器交叉
    private void crossover4machinesequence(PermutationSolution<Integer> integerPermutationSolution, PermutationSolution<Integer> particle, int[] nw) {

        ArrayList<Integer> machineintegerPermutationSolution = (ArrayList<Integer>) integerPermutationSolution.getAttribute("machine");
        ArrayList<Integer> machineparticle = (ArrayList<Integer>) particle.getAttribute("machine");


        List<Integer> integerPermutationSolutionfactory = integerPermutationSolution.getVariablesid();
        List<Integer> particlefactory = particle.getVariablesid();

        Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int max = r.nextInt(machineintegerPermutationSolution.size() - 1);
        int min = r.nextInt(machineintegerPermutationSolution.size() - 1);
        if (max < min) {
            int temp = 0;
            temp = max;
            max = min;
            min = temp;
        }
        List<Integer> machinetemp1 = new ArrayList<>(machineintegerPermutationSolution.subList(min, max + 1));
        List<Integer> machinetemp2 = new ArrayList<>(machineparticle.subList(min, max + 1));

        List<Integer> factorytemp1 = new ArrayList<>(integerPermutationSolutionfactory.subList(min, max + 1));
        List<Integer> factorytemp2 = new ArrayList<>(particlefactory.subList(min, max + 1));

        int[][] numberOfMachines = EDHHFSPW.numberOfMachines_;


        for (int i = 0; i < machinetemp1.size(); i++) {
            if (factorytemp1.get(i) == factorytemp2.get(i)) {
                int temp1 = machinetemp1.get(i);
                int temp2 = machinetemp2.get(i);
                machinetemp2.set(i, temp1);
                machinetemp1.set(i, temp2);
            } else {
                int temp1 = numberOfMachines[factorytemp1.get(i)][0];
                temp1 = r.nextInt(temp1);
                machinetemp1.set(i, temp1);

                int temp2 = numberOfMachines[factorytemp2.get(i)][0];
                temp2 = r.nextInt(temp2);
                machinetemp2.set(i, temp2);
            }
        }
        for (int i = 0; i < machinetemp1.size(); i++) {
            machineparticle.set(min, machinetemp2.get(i));
            min++;
        }

        particle.setAttribute("machine", machineparticle);

    }

    //工人变异
    private void mutation4worker(PermutationSolution<Integer> particle) {

        List<Integer> variablesworker = particle.getVariablesworker();
        int[] nw = EDHHFSPW.nw;
        Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int stage = particle.getNumberOfVariablesworker() / particle.getNumberOfVariables();
        int[][][] workerinfactory = DefaultIntegerPermutationSolution.result;


        for (int i = 0; i < stage; i++) {
            int index = r.nextInt(particle.getNumberOfVariables());
            int i1 = particle.getNumberOfVariables() * i + index;

            int worker = r.nextInt(workerinfactory[particle.getVariableValueid(index)][i].length);
            int workerchoose = workerinfactory[particle.getVariableValueid(index)][i][worker];
            particle.setVariableValueworker(i1, workerchoose);
        }

    }

    // 根据 nw 数组对 variablesworker 列表进行划分
    private static List<List<Integer>> splitIntoBlocks(List<Integer> variablesworker, int[] nw) {
        List<List<Integer>> blocks = new ArrayList<>();
        int currentIndex = 0;

        for (int size : nw) {
            // 创建一个新的分块
            List<Integer> block = new ArrayList<>(variablesworker.subList(currentIndex, currentIndex + size));
            blocks.add(block);
            currentIndex += size;
        }

        return blocks;
    }


    //机器变异
    private void mutation4machine(PermutationSolution<Integer> particle) {
        ArrayList<Integer> machine = (ArrayList<Integer>) particle.getAttribute("machine");
        List<Integer> variablesid = particle.getVariablesid();
        Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int i = r.nextInt(machine.size());
        int tempfactory = variablesid.get(i);
        int[][] numberOfMachines = EDHHFSPW.numberOfMachines_;
        int numberOfMachine = numberOfMachines[tempfactory][0];

        int temp = r.nextInt(numberOfMachine);
        machine.set(i, temp);
        particle.setAttribute("machine", machine);
    }

}
