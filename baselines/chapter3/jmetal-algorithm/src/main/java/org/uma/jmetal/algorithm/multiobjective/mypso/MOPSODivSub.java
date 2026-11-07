package org.uma.jmetal.algorithm.multiobjective.mypso;

import org.uma.jmetal.algorithm.impl.AbstractParticleSwarmOptimization;
import org.uma.jmetal.algorithm.multiobjective.mypso.util.SO;
import org.uma.jmetal.algorithm.multiobjective.mypso.util.ST;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;


/** Class implementing the OMOPSO algorithm */

@SuppressWarnings("serial")
public class MOPSODivSub extends AbstractParticleSwarmOptimization<PermutationSolution<Integer>, List<PermutationSolution<Integer>>> {

    private Problem<PermutationSolution<Integer>> problem;
    private final SolutionListEvaluator<PermutationSolution<Integer>> evaluator;

    private int swarmSize;
    private int upSize;
    private int centralSize;
    private int downSize;
    private int upNewSize;

//    private int archiveSize;
    private int maxIterations;

    private ArrayList<List<PermutationSolution<Integer>>> tempSwarm ;
    private List<PermutationSolution<Integer>> globallyOptimalIndividual ;

    private List<PermutationSolution<Integer>> groupU1Solution;
    private List<PermutationSolution<Integer>> groupC2Solution;
    private List<PermutationSolution<Integer>> groupD3Solution;
    private List<PermutationSolution<Integer>> groupUNewSolution;

    private ArrayList<List<PermutationSolution<Integer>>> upGroup1Population ;
    private ArrayList<List<PermutationSolution<Integer>>> upNewGroup1Population ;
    private ArrayList<List<PermutationSolution<Integer>>> centralGroup2Population ;
    private ArrayList<List<PermutationSolution<Integer>>> downGroup3Population ;

    private List<PermutationSolution<Integer>> upGr1HisOptIndividual ;
    private List<PermutationSolution<Integer>> upNewGr1HisOptIndividual;
    private List<PermutationSolution<Integer>> centralGr2HisOptIndividual ;
    private List<PermutationSolution<Integer>> downGr3HisOptIndividual ;

    private List<PermutationSolution<Integer>> all3GlobalOptIndividuals ;

    private double CrossoverRates4worker;
    private double CrossoverRates4machine;
    private double mutationRate4worker;
    private double mutationRate4machine;

    private double Rand_k;
    private double Cross_c;
    private double Mutation_m;
    private int currentIteration;
    private JMetalRandom randomGenerator;
    private ArrayList<List<Integer>> action;
    private double Qnums;
    private int numberOfFactories;
    private double gamma = 0.75, tl = 0.85;

    /** Constructor */
    public MOPSODivSub(int factories,double crossoverRate, double mutationRate, double rand_k,Problem<PermutationSolution<Integer>> problem, SolutionListEvaluator<PermutationSolution<Integer>> evaluator,
                       int swarmSize, int maxIterations, int upSize, int centralSize, int downSize ,int upNewSize,double Qnums,double CrossoverRates4worker,double CrossoverRates4machine,double mutationRate4worker,double mutationRate4machine) {
        this.problem = problem ;
        this.evaluator = evaluator ;

        this.swarmSize = swarmSize ;
        this.maxIterations = maxIterations ;
        this.numberOfFactories = factories;
        this.upSize = upSize ;
        this.centralSize = centralSize ;
        this.downSize = downSize ;
        this.upNewSize = upNewSize ;
        this.Mutation_m = mutationRate;
        this.Cross_c = crossoverRate;
        this.Rand_k = rand_k;
   //     this.archiveSize = archiveSize ;
        this.Qnums = Qnums;
        tempSwarm = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);
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

        this.CrossoverRates4worker=CrossoverRates4worker;
        this.CrossoverRates4machine=CrossoverRates4machine;
        this.mutationRate4worker=mutationRate4worker;
        this.mutationRate4machine=mutationRate4machine ;


        randomGenerator = JMetalRandom.getInstance() ;
    }

    @Override protected void initProgress() {
        currentIteration = swarmSize;
        //currentIteration = 1;
        //    crowdingDistance.computeDensityEstimator(leaderArchive.getSolutionList());
    }

    @Override protected void updateProgress() {
        currentIteration = currentIteration + swarmSize;
        //currentIteration += 1;
        //   crowdingDistance.computeDensityEstimator(leaderArchive.getSolutionList());
    }

    @Override protected boolean isStoppingConditionReached() {
        return currentIteration >= maxIterations;
    }

    @Override
    protected List<PermutationSolution<Integer>> createInitialSwarm() {
        List<PermutationSolution<Integer>> swarm = new ArrayList<>(swarmSize);

        PermutationSolution<Integer> newSolution;

        for (int i = 0; i < swarmSize; i++) {

            newSolution =  problem.createSolution();
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
            swarm.add(newSolution);
        }
//        System.out.println(swarm);
//        sleep();
        return swarm;
    }

    private static void sleep() {
        try {
            Thread.sleep(999999);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    protected List<PermutationSolution<Integer>> evaluateSwarm(List<PermutationSolution<Integer>> swarm) {
        swarm = evaluator.evaluate(swarm, (Problem<PermutationSolution<Integer>>) problem);
        //currentIteration=currentIteration+swarmSize;
        return swarm ;
    }

    @Override
    protected void initializeLeader(List<PermutationSolution<Integer>> swarm) {
        for(int i=0;i<swarmSize;i++) {
            globallyOptimalIndividual.add(tempSwarm.get(i).get(0));
        }
    }

    @Override
    protected void initializeParticlesMemory(List<PermutationSolution<Integer>> swarm)  {
        for (int i = 0; i < swarm.size(); i++) {
            ArrayList<PermutationSolution<Integer>> A = new ArrayList<PermutationSolution<Integer>>();
            A.add(swarm.get(i));
            tempSwarm.add(A);
        }
    }

    @Override
    protected void initializeVelocity(List<PermutationSolution<Integer>> swarm) {

    }

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
                if ((temp1.get(j).getObjective(0) < temp1.get(b).getObjective(0)) &&
                        (temp1.get(j).getObjective(1) < temp1.get(b).getObjective(1))) {
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
                if ((temp3.get(j).getObjective(1) < temp3.get(b).getObjective(1)) &&
                        (temp3.get(j).getObjective(2) < temp3.get(b).getObjective(2))) {
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
                if ((temp4.get(j).getObjective(2) < temp4.get(b).getObjective(2)) &&
                        (temp4.get(j).getObjective(0) < temp4.get(b).getObjective(0))) {
                    b = j;
                }
            }
            groupUNewSolution.add(temp4.get(b));
            upNewGroup1Population.add(tempPd4.get(b));

            temp4.remove(b);
            tempPd4.remove(b);
        }

        select();

    }

    //分群
    protected void updateVelocity1(List<PermutationSolution<Integer>> swarm) {

        upGroup1Population.clear();
        centralGroup2Population.clear();
        downGroup3Population.clear();

        groupU1Solution.clear();
        groupC2Solution.clear();
        groupD3Solution.clear();

        List<PermutationSolution<Integer>> temp1 = new ArrayList<>(swarmSize);
        List<PermutationSolution<Integer>> temp2 = new ArrayList<>(swarmSize);
        List<PermutationSolution<Integer>> temp3 = new ArrayList<>(swarmSize);

        ArrayList<List<PermutationSolution<Integer>>> tempPd1 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);
        ArrayList<List<PermutationSolution<Integer>>> tempPd2 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);
        ArrayList<List<PermutationSolution<Integer>>> tempPd3 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);

        for(int i=0;i<swarmSize;i++){
            temp1.add(swarm.get(i));
            temp2.add(swarm.get(i));
            temp3.add(swarm.get(i));
            tempPd1.add(tempSwarm.get(i));
            tempPd2.add(tempSwarm.get(i));
            tempPd3.add(tempSwarm.get(i));
        }

        //划分sub1
        for(int i=0;i<upSize;i++){
            int b=0;
            for(int j=1;j<temp1.size();j++){
                if(temp1.get(j).getObjective(0)<temp1.get(b).getObjective(0)){
                    b=j;
                }
            }
            groupU1Solution.add(temp1.get(b));
            upGroup1Population.add(tempPd1.get(b));

            temp1.remove(b);
            tempPd1.remove(b);

        }

        //划分sub2
        List<Double> aa = new ArrayList<>(swarmSize);
        for(int i=0;i<swarmSize;i++){
            double count1 = 0;
            double count2 = 0;
            for(int j=0;j<swarmSize;j++){
                if(i!=j){
                    if(temp2.get(i).getObjective(0)<=temp2.get(j).getObjective(0)&&
                            temp2.get(i).getObjective(1)<=temp2.get(j).getObjective(1)){
                        count1=count1+1;
                    }
                    if(temp2.get(i).getObjective(0)>=temp2.get(j).getObjective(0)&&
                            temp2.get(i).getObjective(1)>=temp2.get(j).getObjective(1)){
                        count2=count2+1;
                    }
                }
            }
            aa.add(count2+1/(count1+1));
        }

        for(int i=0;i<centralSize;i++){
            int b=0;
            for(int j=1;j<aa.size();j++){
                if(aa.get(j)<aa.get(b)){
                    b=j;
                }
            }
            groupC2Solution.add(temp2.get(b));
            centralGroup2Population.add(tempPd2.get(b));

            aa.remove(b);
            tempPd2.remove(b);
            temp2.remove(b);
        }

        for(int i=0;i<downSize;i++){
            int b=0;
            for(int j=1;j<temp3.size();j++){
                if(temp3.get(j).getObjective(1)<temp3.get(b).getObjective(1)){
                    b=j;
                }
            }
            groupD3Solution.add(temp3.get(b));
            downGroup3Population.add(tempPd3.get(b));

            temp3.remove(b);
            tempPd3.remove(b);
        }

        select();

    }

    //二元锦标赛法（选三个，取最好）
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
                    upGroup1Population.get(i).get(a3).getObjective(0) >= upGroup1Population.get(i).get(a2).getObjective(0)) &&
                    (upGroup1Population.get(i).get(a1).getObjective(1) >= upGroup1Population.get(i).get(a2).getObjective(1) &&
                            upGroup1Population.get(i).get(a3).getObjective(1) >= upGroup1Population.get(i).get(a2).getObjective(1))
            ) {
                temp = a2;
            }

            if ((upGroup1Population.get(i).get(a1).getObjective(0) >= upGroup1Population.get(i).get(a3).getObjective(0) &&
                    upGroup1Population.get(i).get(a2).getObjective(0) >= upGroup1Population.get(i).get(a3).getObjective(0)) &&
                    (upGroup1Population.get(i).get(a1).getObjective(1) >= upGroup1Population.get(i).get(a3).getObjective(0) &&
                            upGroup1Population.get(i).get(a2).getObjective(1) >= upGroup1Population.get(i).get(a3).getObjective(0))
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
                    downGroup3Population.get(i).get(a3).getObjective(1) >= downGroup3Population.get(i).get(a2).getObjective(1)) &&
                    (downGroup3Population.get(i).get(a1).getObjective(2) >= downGroup3Population.get(i).get(a2).getObjective(2) &&
                            downGroup3Population.get(i).get(a3).getObjective(2) >= downGroup3Population.get(i).get(a2).getObjective(2))
            ) {
                temp = a2;
            }
            if ((downGroup3Population.get(i).get(a1).getObjective(1) >= downGroup3Population.get(i).get(a3).getObjective(1) &&
                    downGroup3Population.get(i).get(a2).getObjective(1) >= downGroup3Population.get(i).get(a3).getObjective(1)) &&
                    (downGroup3Population.get(i).get(a1).getObjective(2) >= downGroup3Population.get(i).get(a3).getObjective(2) &&
                            downGroup3Population.get(i).get(a2).getObjective(2) >= downGroup3Population.get(i).get(a3).getObjective(2))
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
                    upNewGroup1Population.get(i).get(a3).getObjective(2) >= upNewGroup1Population.get(i).get(a2).getObjective(2)) &&
                    (upNewGroup1Population.get(i).get(a1).getObjective(0) >= upNewGroup1Population.get(i).get(a2).getObjective(0) &&
                            upNewGroup1Population.get(i).get(a3).getObjective(0) >= upNewGroup1Population.get(i).get(a2).getObjective(0))
            ) {
                temp = a2;
            }
            if ((upNewGroup1Population.get(i).get(a1).getObjective(2) >= upNewGroup1Population.get(i).get(a3).getObjective(2) &&
                    upNewGroup1Population.get(i).get(a2).getObjective(2) >= upNewGroup1Population.get(i).get(a3).getObjective(2)) &&
                    (upNewGroup1Population.get(i).get(a1).getObjective(0) >= upNewGroup1Population.get(i).get(a3).getObjective(0) &&
                            upNewGroup1Population.get(i).get(a2).getObjective(0) >= upNewGroup1Population.get(i).get(a3).getObjective(0))
            ) {
                temp = a3;
            }
            upNewGr1HisOptIndividual.add(upNewGroup1Population.get(i).get(temp));
        }


        //判断选择全局最优解
        int a1 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        int a2 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        int a3 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        int temp = a1;
        if ((globallyOptimalIndividual.get(a1).getObjective(0) >= globallyOptimalIndividual.get(a2).getObjective(0) &&
                globallyOptimalIndividual.get(a3).getObjective(0) >= globallyOptimalIndividual.get(a2).getObjective(0)) &&
                (globallyOptimalIndividual.get(a1).getObjective(1) >= globallyOptimalIndividual.get(a2).getObjective(1) &&
                        globallyOptimalIndividual.get(a3).getObjective(1) >= globallyOptimalIndividual.get(a2).getObjective(1))
        ) {
            temp = a2;
        }

        if ((globallyOptimalIndividual.get(a1).getObjective(0) >= globallyOptimalIndividual.get(a3).getObjective(0) &&
                globallyOptimalIndividual.get(a2).getObjective(0) >= globallyOptimalIndividual.get(a3).getObjective(0)) &&
                (globallyOptimalIndividual.get(a1).getObjective(1) >= globallyOptimalIndividual.get(a3).getObjective(1) &&
                        globallyOptimalIndividual.get(a2).getObjective(1) >= globallyOptimalIndividual.get(a3).getObjective(1))
        ) {
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
        if ((globallyOptimalIndividual.get(a1).getObjective(1) >= globallyOptimalIndividual.get(a2).getObjective(1) &&
                globallyOptimalIndividual.get(a3).getObjective(1) >= globallyOptimalIndividual.get(a2).getObjective(1)) &&
                (globallyOptimalIndividual.get(a1).getObjective(2) >= globallyOptimalIndividual.get(a2).getObjective(2) &&
                        globallyOptimalIndividual.get(a3).getObjective(2) >= globallyOptimalIndividual.get(a2).getObjective(2))
        ) {
            temp = a2;
        }

        if ((globallyOptimalIndividual.get(a1).getObjective(1) >= globallyOptimalIndividual.get(a3).getObjective(1) &&
                globallyOptimalIndividual.get(a2).getObjective(1) >= globallyOptimalIndividual.get(a3).getObjective(1)) &&
                (globallyOptimalIndividual.get(a1).getObjective(2) >= globallyOptimalIndividual.get(a3).getObjective(2) &&
                        globallyOptimalIndividual.get(a2).getObjective(2) >= globallyOptimalIndividual.get(a3).getObjective(2))
        ) {
            temp = a3;
        }
        all3GlobalOptIndividuals.add(globallyOptimalIndividual.get(temp));


        a1 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        a2 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        a3 = randomGenerator.nextInt(0, globallyOptimalIndividual.size() - 1);
        temp = a1;
        if ((globallyOptimalIndividual.get(a1).getObjective(2) >= globallyOptimalIndividual.get(a2).getObjective(2) &&
                globallyOptimalIndividual.get(a3).getObjective(2) >= globallyOptimalIndividual.get(a2).getObjective(2)) &&
                (globallyOptimalIndividual.get(a1).getObjective(0) >= globallyOptimalIndividual.get(a2).getObjective(0) &&
                        globallyOptimalIndividual.get(a3).getObjective(0) >= globallyOptimalIndividual.get(a2).getObjective(0))
        ) {
            temp = a2;
        }

        if ((globallyOptimalIndividual.get(a1).getObjective(2) >= globallyOptimalIndividual.get(a3).getObjective(2) &&
                globallyOptimalIndividual.get(a2).getObjective(2) >= globallyOptimalIndividual.get(a3).getObjective(2)) &&
                (globallyOptimalIndividual.get(a1).getObjective(0) >= globallyOptimalIndividual.get(a3).getObjective(0) &&
                        globallyOptimalIndividual.get(a2).getObjective(0) >= globallyOptimalIndividual.get(a3).getObjective(0))
        ) {
            temp = a3;
        }
        all3GlobalOptIndividuals.add(globallyOptimalIndividual.get(temp));

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

    //加DE操作
/*    @Override
    protected void perturbation(List<PermutationSolution<Integer>> swarm) {

        //int QN=(int)Qnums;
        //在分群后加DE操作
        //swarm = evaluateSwarm(swarm);
        *//*super.setSwarm(evaluateSwarm(swarm));
        updateVelocity(swarm);    //分群
        //////////////////////////////////////////////////////////////////////////////
        List<PermutationSolution<Integer>> swarmtemp = new ArrayList<PermutationSolution<Integer>>(swarm.size());

        int[] DEswarmtempPdflag = new int[swarmSize];


        int group=1;
        action = action(numberOfFactories);
        int anum = action.size();
        int[] swarmgroup={upSize,centralSize,downSize};

        for (int i = 0; i < swarm.size(); i++) {
            double[][] Q = new double[2][anum];
            double[][] R = new double[2][anum];
            for (int j = 0; j < anum; j++) {
                Q[0][j] = 0;
                Q[1][j] = 0;
            }

            for (int j = 0; j < anum; j++) {
                if (action.get(j).size() == 1) {
                    R[0][j] = 3;
                    R[1][j] = 1;
                }
                if (action.get(j).size() == 2) {
                    R[0][j] = 2;
                    R[1][j] = 2;
                }
                if (action.get(j).size() == 3) {
                    R[0][j] = 1;
                    R[1][j] = 3;
                }
            }
            //double r = 0.75, s = 0.85;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 1;    //状态0 新粒子比原本粒子好，状态1 新粒子没有原来粒子好
            int actionIndex;
            PermutationSolution<Integer>  getswarm1 = null;
            for (int k = 0; k < 20; k++) {
                double p = random.nextDouble();
                if (k == 0) {
                    actionIndex = random.nextInt(action.size());
                    getswarm1=learn(actionIndex, R, Q, swarm.get(i), next);
                    if ((getswarm1.getObjective(0) < swarm.get(i).getObjective(0) && getswarm1.getObjective(1) < swarm.get(i).getObjective(1)) || getswarm1.getObjective(0) < swarm.get(i).getObjective(0) ||getswarm1.getObjective(1) < swarm.get(i).getObjective(1)) next = 0;
                    else next = 1;
                    //actionIndex = getMaxQ(Q);
                } else {
                    if (p < 1 - tl) {
                        actionIndex = random.nextInt(action.size());

                        getswarm1=learn(actionIndex, R, Q, swarm.get(i), next);
                        if ((getswarm1.getObjective(0) < swarm.get(i).getObjective(0) && getswarm1.getObjective(1) < swarm.get(i).getObjective(1)) || getswarm1.getObjective(0) < swarm.get(i).getObjective(0) ||getswarm1.getObjective(1) < swarm.get(i).getObjective(1)) next = 0;
                        else next = 1;
                    } else {
                        //actionIndex = getMaxQ(Q);

                        actionIndex = random.nextInt(action.size());
                        getswarm1=learn(actionIndex, R, Q, swarm.get(i), next);
                        if ((getswarm1.getObjective(0) < swarm.get(i).getObjective(0) && getswarm1.getObjective(1) < swarm.get(i).getObjective(1)) || getswarm1.getObjective(0) < swarm.get(i).getObjective(0) ||getswarm1.getObjective(1) < swarm.get(i).getObjective(1)) next = 0;
                        else next = 1;
                    }
                }
            }
            swarmtemp.add(getswarm1);
            DEswarmtempPdflag[i] = i;
            //System.out.println(Arrays.deepToString(Q));

        }
        swarmtemp = evaluateSwarm(swarmtemp);
        super.setSwarm(PDDRFFselect(swarm,swarmtemp,DEswarmtempPdflag));*//*

        super.setSwarm(evaluateSwarm(swarm));
        updateVelocity(swarm);    //分群
        //////////////////////////////////////////////////////////////////////////////
        //super.setSwarm(evaluateSwarm(swarm));
        List<PermutationSolution<Integer>> swarmtemp = new ArrayList<PermutationSolution<Integer>>(swarm.size());
        List<PermutationSolution<Integer>> swarmtemp1 = new ArrayList<PermutationSolution<Integer>>(swarm.size());
        int[] DEswarmtempPdflag = new int[swarmSize];

        int group=1;
        action = action(numberOfFactories);
        int anum = action.size();
        int[] swarmgroup={upSize,centralSize,downSize};

        for (int i = 0; i < upSize; i++) {
            double[][] Q = new double[2][anum];
            double[][] R = new double[2][anum];
            for (int j = 0; j < anum; j++) {
                Q[0][j] = 0;
                Q[1][j] = 0;
            }

            for (int j = 0; j < anum; j++) {
                if (action.get(j).size() == 1) {
                    R[0][j] = 3;
                    R[1][j] = 1;
                }
                if (action.get(j).size() == 2) {
                    R[0][j] = 2;
                    R[1][j] = 2;
                }
                if (action.get(j).size() == 3) {
                    R[0][j] = 1;
                    R[1][j] = 3;
                }
            }
            //double r = 0.75, s = 0.85;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 0;
            int actionIndex;
            PermutationSolution<Integer>  getswarm1 = null;
           // for (int k = 0; k < 20; k++) {
                actionIndex = random.nextInt(action.size());
                getswarm1=learn(actionIndex, R, Q, groupU1Solution.get(i), next,group);
           // }
            swarmtemp.add(getswarm1);
        }
        group=2;
        for (int i = 0; i < centralSize; i++) {
            double[][] Q = new double[2][anum];
            double[][] R = new double[2][anum];
            for (int j = 0; j < anum; j++) {
                Q[0][j] = 0;
                Q[1][j] = 0;
            }
            for (int j = 0; j < anum; j++) {
                if (action.get(j).size() == 1) {
                    R[0][j] = 3;
                    R[1][j] = 1;
                }
                if (action.get(j).size() == 2) {
                    R[0][j] = 2;
                    R[1][j] = 2;
                }
                if (action.get(j).size() == 3) {
                    R[0][j] = 1;
                    R[1][j] = 3;
                }
            }
            //double r = 0.75, s = 0.85;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 0;
            int actionIndex;
            PermutationSolution<Integer>  getswarm1 = null;
           // for (int k = 0; k < 20; k++) {
                actionIndex = random.nextInt(action.size());
                getswarm1=learn(actionIndex, R, Q, groupC2Solution.get(i), next,group);
           // }
            swarmtemp.add(getswarm1);
        }
        group=3;
        for (int i = 0; i < downSize; i++) {
            double[][] Q = new double[2][anum];
            double[][] R = new double[2][anum];
            for (int j = 0; j < anum; j++) {
                Q[0][j] = 0;
                Q[1][j] = 0;
            }

            for (int j = 0; j < anum; j++) {
                if (action.get(j).size() == 1) {
                    R[0][j] = 3;
                    R[1][j] = 1;
                }
                if (action.get(j).size() == 2) {
                    R[0][j] = 2;
                    R[1][j] = 2;
                }
                if (action.get(j).size() == 3) {
                    R[0][j] = 1;
                    R[1][j] = 3;
                }
            }
            //double r = 0.75, s = 0.85;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 0;
            int actionIndex;
            PermutationSolution<Integer>  getswarm1 = null;
            //for (int k = 0; k < 20; k++) {
                actionIndex = random.nextInt(action.size());
                getswarm1=learn(actionIndex, R, Q, groupD3Solution.get(i), next,group);
            //}
            //groupD3Solution.set(i,getswarm1);
            swarmtemp.add(getswarm1);
        }
        mergeNew(swarmtemp);

        swarmtemp = evaluateSwarm(swarmtemp);

        for (int i = 0; i < swarmSize; i++) {
            DEswarmtempPdflag[i] = i;
        }
        super.setSwarm(PDDRFFselect(swarm,swarmtemp,DEswarmtempPdflag));

    }*/
    //加DE操作
    @Override
    protected void perturbation(List<PermutationSolution<Integer>> swarm) {
        /*int QN=(int)Qnums;
        //在分群后加DE操作
        //swarm = evaluateSwarm(swarm);
        super.setSwarm(evaluateSwarm(swarm));
        updateVelocity(swarm);    //分群
        //////////////////////////////////////////////////////////////////////////////
        //super.setSwarm(evaluateSwarm(swarm));
        List<PermutationSolution<Integer>> swarmtemp = new ArrayList<PermutationSolution<Integer>>(swarm.size());

        int[] DEswarmtempPdflag = new int[swarmSize];


        int group=1;
        action = action(numberOfFactories);
        int anum = action.size();

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

            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 1;
            int actionIndex;
            PermutationSolution<Integer>  getswarm1 = null;
            actionIndex = random.nextInt(action.size());
            getswarm1=learn(actionIndex, R, Q, groupU1Solution.get(i), next,group);
            swarmtemp.add(getswarm1);
        }
        group=2;
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
            PermutationSolution<Integer>  getswarm1 = null;
            actionIndex = random.nextInt(action.size());
            getswarm1=learn(actionIndex, R, Q, groupC2Solution.get(i), next,group);
            swarmtemp.add(getswarm1);
        }
        group=3;
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
            PermutationSolution<Integer>  getswarm1 = null;
            actionIndex = random.nextInt(action.size());
            getswarm1=learn(actionIndex, R, Q, groupD3Solution.get(i), next,group);
            swarmtemp.add(getswarm1);
        }
        mergeNew(swarmtemp);

        swarmtemp = evaluateSwarm(swarmtemp);

        for (int i = 0; i < swarmSize; i++) {
            DEswarmtempPdflag[i] = i;
        }
        super.setSwarm(PDDRFFselect(swarm,swarmtemp,DEswarmtempPdflag));*/
    }
    
    public double calculateNewQ1 ( double[][] R,double[][] Q,int a,int next1,int Qiannext,double old0,double old1,double new0,double new1)
    {
        // return (r + rew * q);
        //double reward= R[Qiannext][a];
        double reward =old0-new0+(old1-new1);
        Q[Qiannext][a] = reward+ gamma * maxNextQ(Q[next1]);
        //Q[Qiannext][a] = (1-alpha) * Q[Qiannext][a] + alpha * (reward+ gamma * maxNextQ(Q[next1]));
        return Q[Qiannext][a];
    }
    private  double maxNextQ(double[] is) {
        double max = is[0];
        for(int i = 1; i < is.length; ++i) {
            if(is[i] > max) max = is[i];
        }
        return max;
    }
    private  int max(double[] is) {
        int max = 0;
        for(int i = 1; i < is.length; ++i) {
            if(is[i] > is[max]) max = i;
        }
        return max;
    }
    private void mergeNew (List < PermutationSolution < Integer >> swarm) {
        //swarm.clear();
        tempSwarm.clear();

        for (int i = 0; i < upSize; i++) {
            // swarm.add((PermutationSolution<Integer>) groupU1Solution.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(upGroup1Population.get(i).size());

            for (int j = 0; j < upGroup1Population.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) upGroup1Population.get(i).get(j).copy());
            }
            tempSwarm.add(A);
        }


        for (int i = 0; i < centralSize; i++) {
            // swarm.add((PermutationSolution<Integer>) groupC2Solution.get(i).copy());

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

    }
   /* public PermutationSolution<Integer> learn(int a, double[][] R, double[][] Q, PermutationSolution<Integer> bestsolution, int next1) {

        List<Integer> selectFac = new ArrayList<>();
        selectFac = action.get(a);
        PermutationSolution<Integer> solutiont;
        solutiont = V_N_Search(bestsolution, selectFac);
*//*        if (solutiont.getObjective(0) == bestsolution.getObjective(0) && solutiont.getObjective(1) == bestsolution.getObjective(1)) next1 = 1;
        else next1 = 0;*//*
        double reward = R[next1][a];
        double Qvalue = calculateNewQ(reward, Q[next1][a]);
        Q[next1][a] = Qvalue;
        return solutiont;
    }

    public PermutationSolution<Integer> V_N_Search(PermutationSolution<Integer> bestsolution, List<Integer> selectFac) {
        int count = 0;
        int max_iterations = 1;
        List<PermutationSolution<Integer>> current_pop1 = new ArrayList<PermutationSolution<Integer>>(1);
        List<PermutationSolution<Integer>> pop1 = new ArrayList<PermutationSolution<Integer>>(1);
        PermutationSolution<Integer> currentsolution = bestsolution;
        //shaking(solution,k);
        do {
            current_pop1.clear();
            pop1.clear();

            currentsolution = variable_neighborhood_descent(currentsolution, selectFac);
            count++;
        }
        while (count <= max_iterations);
        return currentsolution;

    }    //变邻域搜索

    private PermutationSolution<Integer> variable_neighborhood_descent(PermutationSolution<Integer> solution, List<Integer> selectFac) {//solution就是main里的current_solution
        PermutationSolution<Integer> current_solution = solution;
        List<PermutationSolution<Integer>> current_pop1 = new ArrayList<PermutationSolution<Integer>>(1);
        List<PermutationSolution<Integer>> pop1 = new ArrayList<PermutationSolution<Integer>>(1);

        int l =1;
        while (l <= 2) {
            if (l == 1) {
                pop1.clear();
                current_pop1.clear();

                current_solution = insertion_neighborhood(current_solution, selectFac);
                pop1.add(solution);
                current_pop1.add(current_solution);
                current_pop1 = evaluator.evaluate(current_pop1, problem);
                pop1 = evaluator.evaluate(pop1, problem);

                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))   || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) )
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
                    } else {
                        l++;
                    }


            }

            if (l == 2) {
                pop1.clear();
                current_pop1.clear();

                current_solution = exchange_neighborhood(solution, selectFac);
                pop1.add(solution);
                current_pop1.add(current_solution);
                current_pop1 = evaluator.evaluate(current_pop1, (Problem<PermutationSolution<Integer>>) problem);
                pop1 = evaluator.evaluate(pop1, (Problem<PermutationSolution<Integer>>) problem);


               if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))|| (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) ) )
               {
                //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    //l=0;
                } else {
                    l++;
                }
            }
            //else{return solution;}
            //l++;
        }
        return solution;
    }*/
   public PermutationSolution<Integer> learn(int a, double[][] R, double[][] Q, PermutationSolution<Integer> bestsolution, int next1,int group) {

       List<Integer> selectFac = new ArrayList<>();
       selectFac = action.get(a);
       PermutationSolution<Integer> solutiont;
       solutiont = V_N_Search(bestsolution, selectFac,group);
/*        if (solutiont.getObjective(0) == bestsolution.getObjective(0) && solutiont.getObjective(1) == bestsolution.getObjective(1)) next1 = 1;
        else next1 = 0;*/
/*       double reward = R[next1][a];
       double Qvalue = calculateNewQ(reward, Q[next1][a]);
       Q[next1][a] = Qvalue;*/
       return solutiont;
   }

    public PermutationSolution<Integer> V_N_Search(PermutationSolution<Integer> bestsolution, List<Integer> selectFac,int group) {
        int count = 0;
        int max_iterations = 3;
        List<PermutationSolution<Integer>> current_pop1 = new ArrayList<PermutationSolution<Integer>>(1);
        List<PermutationSolution<Integer>> pop1 = new ArrayList<PermutationSolution<Integer>>(1);
        PermutationSolution<Integer> currentsolution = bestsolution;
        //shaking(solution,k);
        do {
            current_pop1.clear();
            pop1.clear();

            currentsolution = variable_neighborhood_descent(currentsolution, selectFac,group);
            count++;
        }
        while (count <= max_iterations);
        return currentsolution;

    }    //变邻域搜索

    private PermutationSolution<Integer> variable_neighborhood_descent(PermutationSolution<Integer> solution, List<Integer> selectFac,int group) {//solution就是main里的current_solution
        PermutationSolution<Integer> current_solution = solution;
        List<PermutationSolution<Integer>> current_pop1 = new ArrayList<PermutationSolution<Integer>>(1);
        List<PermutationSolution<Integer>> pop1 = new ArrayList<PermutationSolution<Integer>>(1);

        int l =1;
        while (l <= 2) {
            if (l == 1) {
                pop1.clear();
                current_pop1.clear();

                current_solution = insertion_neighborhood(current_solution, selectFac);
                pop1.add(solution);
                current_pop1.add(current_solution);
                current_pop1 = evaluator.evaluate(current_pop1, problem);
                pop1 = evaluator.evaluate(pop1, problem);
                if(group==1){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) ||(current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) ) )
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
                    } else {
                        l++;
                    }
                }
                if(group==2){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) ))
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
                    } else {
                        l++;
                    }
                }
                if(group==3){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) ) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) )
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
                    } else {
                        l++;
                    }
                }
            }

            if (l == 2) {
                pop1.clear();
                current_pop1.clear();

                current_solution = exchange_neighborhood(solution, selectFac);
                pop1.add(solution);
                current_pop1.add(current_solution);
                current_pop1 = evaluator.evaluate(current_pop1, (Problem<PermutationSolution<Integer>>) problem);
                pop1 = evaluator.evaluate(pop1, (Problem<PermutationSolution<Integer>>) problem);
                if(group==1){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) )  )
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
                    } else {
                        l++;
                    }
                }
                if(group==2){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))  || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))|| (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) ) )
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
                    } else {
                        l++;
                    }
                }
                if(group==3){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) ) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)))
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
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
            //else{return solution;}
            //l++;
        }
        return solution;
    }

    public PermutationSolution<Integer> insertion_neighborhood(PermutationSolution<Integer> solution, List<Integer> selectFac) {
        Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        PermutationSolution<Integer> solutionNew  = problem.createSolution();
        int a, i , j;
        // PermutationSolution<Integer> solutiontemp = problem.createSolution();
        //List<List<Integer>> t = new ArrayList<>();  //存工厂号下对应的工件序列的下标
        //ArrayList<List<Integer>> N = new ArrayList<>();
        int [][] N= new int[numberOfFactories][solution.getNumberOfVariablesid()];       //存相同工厂的工件下标

        List<Integer> v = new ArrayList<>();
        int[] ind = new int[selectFac.size()];     //存工厂号
//对0，1，2工厂的工件顺序排列
        int [][] len=new int[numberOfFactories][1];
        for (int r = 0; r < numberOfFactories; r++) {
            int h=0;
            for (int y = 0; y < solution.getNumberOfVariablesid(); y++) {
                if (solution.getVariableValueid(y) == r) {  //等于工厂号的下标
                    N[r][h]=y;     //等于工厂号的下标
                    h++;
                }
            }
            len[r][0]=h;   //工厂的工件个数  0，1，2长度
        }            //没问题

        for (int r = 0; r < selectFac.size(); r++) {
            int m;int n;//int hao=0;
            ind[r] = selectFac.get(r);  //几号工厂
            int c=ind[r];             //几号工厂
            int[] rList=new int [len[c][0]];
            for(int k=0;k<len[c][0];k++){
                //rList.add(N[r][k]);            // rList里面存的工件的下标
                rList[k]=N[c][k];      // rList里面存的工件的下标
            }          //没问题

            int t = A.nextInt(rList.length); //m = N[r][t];           // rList里面存的工件的下标
            int g = A.nextInt(rList.length); //n = N[r][g];            //t存的是rList里内容的下标   t下标下对应的是工件本身号

            if(t==g ) {
                int end=0;
                int num=0;
                while(end!=-1){
                    g=A.nextInt(rList.length); //n = N[r][g];
                    //n =A.nextInt(len[r].length);
                    if(t!=g){
                        end=-1;
                    }
                    num++;
                }
                if (t < g) {
                    // i = m;j = n;
                    i=t; j=g;
                } else {
                    //j = m;i = n;
                    i=g; j=t;
                }
            }
            else{
                if (t < g) {
                    //i = m;j = n;
                    i=t; j=g;
                } else {
                    //j = m;i = n;
                    i=g; j=t;
                }
            }
            //i，j存的是 rList 里内容(粒子下标)的下标         即N[r]里面的下标

            if ( i != 0&&j != rList.length-1) {
                int jobi=rList[i]; //N[r][i];
                int jobj=rList[j];//N[r][j];
                for (a = 0; a < i; a++) {
                    int jobIdx=rList[a];   //工件的下标
                    int temp1 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp1);
                }
                int temp2 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp2);
                for (a = i; a < j; a++) {
                    int jobIdx=rList[a];
                    int jobIdx1=rList[a+1];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx1, temp3);
                }
                for (a = j + 1; a <= rList.length-1; a++) {
                    int jobIdx=rList[a];
                    int temp4 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp4);
                }
            }   //没问题
            else if (i == 0 && i != j && j!= rList.length-1) {
                int jobi=rList[i];
                int jobj=rList[j];
                int temp1 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp1);
                for (a = i; a < j; a++) {
                    int jobIdx=rList[a];
                    int jobIdx1=rList[a+1];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx1, temp3);
                }
                for (a = j + 1; a <= rList.length-1; a++) {
                    int jobIdx=rList[a];
                    int temp4 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp4);
                }

            }     //没问题
            else if (i == 0 && j== rList.length-1) {
                int jobi=rList[i];
                int jobj=rList[j];
                int temp1 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp1);
                for (a = i; a < rList.length-1; a++) {
                    int jobIdx=rList[a];
                    int jobIdx1=rList[a+1];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx1, temp3);
                }

            }// 没问题
            else
            {
                int jobi=rList[i];
                int jobj=rList[j];
                int temp = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp);
                for (a = 0; a < i; a++) {
                    int jobIdx=rList[a];
                    int temp1 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp1);
                }
                    /*int temp2 = solutiontemp.getVariableValue(j);
                    solutionNew.setVariableValue(i, temp2);*/
                for (a = i; a < rList.length-1; a++) {
                    int jobIdx=rList[a];
                    int jobIdx1=rList[a+1];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx1, temp3);
                }
            }   //没问题
        }


        ///////////////////////////////////////////////////////


        int [] no=new int[numberOfFactories];
        for(int d=0;d<numberOfFactories;d++){
            no[d]=d;
        }                                            //        int [] no={0,1,2};

        for(int d=0;d<numberOfFactories;d++){
            for(int l=0;l<selectFac.size();l++) {
                if(selectFac.get(l)==no[d]) no[d]=-1;
            }
        }            //没问题

        for(int d=0;d<numberOfFactories;d++){
            if(no[d]!=-1 ){
                for (a = 0; a < len[d][0]; a++) {
                    int jobIdx=N[d][a];
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

    public PermutationSolution<Integer> exchange_neighborhood(PermutationSolution < Integer > solution, List < Integer > selectFac){
        Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        PermutationSolution<Integer> solutionNew  = problem.createSolution();
        int a, i, j,b;
        // PermutationSolution<Integer> solutiontemp = problem.createSolution();
        //List<List<Integer>> t = new ArrayList<>();  //存工厂号下对应的工件序列的下标
        //ArrayList<List<Integer>> N = new ArrayList<>();
        int [][] N= new int[numberOfFactories][solution.getNumberOfVariablesid()];

        List<Integer> v = new ArrayList<>();
        int[] ind = new int[selectFac.size()];     //存工厂号
//对0，1，2工厂的工件顺序排列
        int [][] len=new int[numberOfFactories][1];
        for (int r = 0; r < numberOfFactories; r++) {
            int h=0;
            for (int y = 0; y < solution.getNumberOfVariablesid(); y++) {
                if (solution.getVariableValueid(y) == r) {  //等于工厂号的下标
                    N[r][h]=y;     //等于工厂号的下标
                    h++;
                }
            }
            len[r][0]=h;   //工厂的工件个数  0，1，2长度
        }

        for (int r = 0; r < selectFac.size(); r++) {
            int m,n;
            ind[r] = selectFac.get(r);  //几号工厂

            int c=ind[r];
            int[] rList=new int [len[c][0]];
            for(int k=0;k<len[c][0];k++){
                //rList.add(N[r][k]);            // rList里面存的工件的下标
                rList[k]=N[c][k];      // rList里面存的工件的下标
            }

///////////////////////////////////////没问题

            int t = A.nextInt(rList.length); //m = N[r][t];           // rList里面存的工件的下标
            int g = A.nextInt(rList.length); //n = N[r][g];            //t存的是rList里内容的下标   t下标下对应的是工件本身号

            if(t==g ) {
                int end=0;
                while(end!=-1){
                    g=A.nextInt(rList.length); //n = N[r][g];
                    //n =A.nextInt(len[r].length);
                    if(t!=g){
                        end=-1;
                    }
                }
                if (t < g) {
                    // i = m;j = n;
                    i=t; j=g;
                } else {
                    //j = m;i = n;
                    i=g; j=t;
                }
            }
            else{
                if (t < g) {
                    //i = m;j = n;
                    i=t; j=g;
                } else {
                    //j = m;i = n;
                    i=g; j=t;
                }
            }
            if(i!=0 &&(j!=rList.length-1)){
                for (a=0; a<i; a++){
                    int jobIdx=rList[a];
                    int temp1 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp1);
                }
                int jobi=rList[i];
                int jobj=rList[j];
                int temp2 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp2);
                int temp4 =  solution.getVariableValue(jobi);
                solutionNew.setVariableValue(jobj,temp4);
                for (a=i+1; a<j; a++){
                    int jobIdx=rList[a];
                    int temp3 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp3);
                }

                for (a=j+1; a<=rList.length-1; a++){
                    int jobIdx=rList[a];
                    int temp5 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp5);
                }
                //System.out.println(solutionNew);
            }
            else if(i==0 && j==rList.length-1){
                int jobi=rList[i];
                int jobj=rList[j];
                int temp1 =  solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi,temp1);
                int temp2 =  solution.getVariableValue(jobi);
                solutionNew.setVariableValue(jobj,temp2);
                for (a=i+1; a<rList.length-1; a++){
                    int jobIdx=rList[a];
                    int temp3 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp3);
                }
                //System.out.println(solutionNew);
            }

            else if(i==0 && j!=(rList.length-1)){
                int jobi=rList[i];
                int jobj=rList[j];
                int temp1 =  solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi,temp1);
                for (a=i+1; a<j; a++){
                    int jobIdx=rList[a];
                    int temp3 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp3);
                }
                int temp2 =  solution.getVariableValue(jobi);
                solutionNew.setVariableValue(jobj,temp2);
                for (a=j+1; a<=(rList.length-1); a++){
                    int jobIdx=rList[a];
                    int temp4 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp4);
                }
                //System.out.println(solutionNew);
            }
            else{
                //if(i!=0 && j==rList.length-1){
                for (a=0; a<i; a++){
                    int jobIdx=rList[a];
                    int temp3 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp3);
                }
                int jobi=rList[i];
                int jobj=rList[j];
                int temp1 =  solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi,temp1);

                int temp2 =  solution.getVariableValue(jobi);
                solutionNew.setVariableValue(jobj,temp2);
                for (a=i+1; a<(rList.length-1); a++){
                    int jobIdx=rList[a];
                    int temp4 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp4);
                }
                //System.out.println(solutionNew);
            }


        }

/////////////////////////////////////////////////////////////
        int [] no=new int[numberOfFactories];
        for(int d=0;d<numberOfFactories;d++){
            no[d]=d;
        }
        //int [] no={0,1,2};
        for(int d=0;d<numberOfFactories;d++){
            for(int l=0;l<selectFac.size();l++) {
                if(selectFac.get(l)==no[d]) no[d]=-1;
            }
        }

        for(int d=0;d<numberOfFactories;d++){
            if(no[d]!=-1 ){
                for (a = 0; a < len[d][0]; a++) {
                    int jobIdx=N[d][a];
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

    public double calculateNewQ ( double r, double q)
    {
        return (r + gamma * q);
    }

    public int getMaxQ ( double[][] Q){
        int maxQ = 0;
        for (int i = 0; i < Q.length; i++) {
            if (Q[0][i] > Q[0][maxQ]) maxQ = i;
        }
        return maxQ;
    }







    //@Override
 /*   protected void perturbation(List<PermutationSolution<Integer>> swarm) {
    }*/

/*    public static ArrayList<List<Integer>> action(int numberOfFactories) {

        List<Integer> nums = new ArrayList<>();
        for (int i = 0; i < numberOfFactories; i++) nums.add(i);
        List<List<Integer>> result = subsets(nums);
        result.remove(0);
        //System.out.println(result);
        //System.out.println("length:" + result.size());
        return (ArrayList<List<Integer>>) result;
    }

    public static List<List<Integer>> subsets(List<Integer> nums) {
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

    //加DE操作
    @Override
    protected void perturbation(List<PermutationSolution<Integer>> swarm) {

        //int QN=(int)Qnums;
        //在分群后加DE操作
        //swarm = evaluateSwarm(swarm);
        super.setSwarm(evaluateSwarm(swarm));
        updateVelocity(swarm);    //分群
        //////////////////////////////////////////////////////////////////////////////
        List<PermutationSolution<Integer>> swarmtemp = new ArrayList<PermutationSolution<Integer>>(swarm.size());

        int[] DEswarmtempPdflag = new int[swarmSize];


        int group=1;
        action = action(numberOfFactories);
        int anum = action.size();
        int[] swarmgroup={upSize,centralSize,downSize};

        for (int i = 0; i < upSize; i++) {

            //double r = 0.75, s = 0.85;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 0;
            int actionIndex;
            PermutationSolution<Integer>  getswarm1 = null;
            for (int k = 0; k < 30; k++) {
                    actionIndex = random.nextInt(action.size());
                    getswarm1=learn(actionIndex, groupU1Solution.get(i), next,group);
                groupU1Solution.set(i,getswarm1);
            }
            swarmtemp.add(getswarm1);
        }
        group=2;
        for (int i = 0; i < centralSize; i++) {

            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 0;
            int actionIndex;
            PermutationSolution<Integer>  getswarm1 = null;
            for (int k = 0; k < 30; k++) {
                    actionIndex = random.nextInt(action.size());
                    getswarm1=learn(actionIndex, groupC2Solution.get(i), next,group);
                groupC2Solution.set(i,getswarm1);
            }
            swarmtemp.add(getswarm1);
        }
        group=3;
        for (int i = 0; i < downSize; i++) {

            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 0;
            int actionIndex;
            PermutationSolution<Integer>  getswarm1 = null;
            for (int k = 0; k < 30; k++) {
                actionIndex = random.nextInt(action.size());
                getswarm1 =learn(actionIndex,  groupD3Solution.get(i), next,group);
                groupD3Solution.set(i,getswarm1);
            }
            swarmtemp.add(getswarm1);
        }
        mergeNew(swarmtemp);

        swarmtemp = evaluateSwarm(swarmtemp);

        for (int i = 0; i < swarmSize; i++) {
            DEswarmtempPdflag[i] = i;
        }
        super.setSwarm(PDDRFFselect(swarm,swarmtemp,DEswarmtempPdflag));

    }
    private void mergeNew (List < PermutationSolution < Integer >> swarm) {
        //swarm.clear();
        tempSwarm.clear();

        for (int i = 0; i < upSize; i++) {
            // swarm.add((PermutationSolution<Integer>) groupU1Solution.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(upGroup1Population.get(i).size());

            for (int j = 0; j < upGroup1Population.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) upGroup1Population.get(i).get(j).copy());
            }
            tempSwarm.add(A);
        }


        for (int i = 0; i < centralSize; i++) {
            // swarm.add((PermutationSolution<Integer>) groupC2Solution.get(i).copy());

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

    }
    public PermutationSolution<Integer> learn(int a, PermutationSolution<Integer> bestsolution, int next1,int group) {

        List<Integer> selectFac = new ArrayList<>();
        selectFac = action.get(a);
        PermutationSolution<Integer> solutiont;
        solutiont = V_N_Search(bestsolution, selectFac, group);
*//*        if (solutiont.getObjective(0) == bestsolution.getObjective(0) && solutiont.getObjective(1) == bestsolution.getObjective(1)) next1 = 1;
        else next1 = 0;*//*
        *//*double reward = R[next1][a];
        double Qvalue = calculateNewQ(reward, Q[next1][a]);
        Q[next1][a] = Qvalue;*//*
        return solutiont;
    }

    public PermutationSolution<Integer> V_N_Search(PermutationSolution<Integer> bestsolution, List<Integer> selectFac,int group) {
        int count = 0;
        int max_iterations = 1;
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

    private PermutationSolution<Integer> variable_neighborhood_descent(PermutationSolution<Integer> solution, List<Integer> selectFac,int group) {//solution就是main里的current_solution
        PermutationSolution<Integer> current_solution = solution;
        List<PermutationSolution<Integer>> current_pop1 = new ArrayList<PermutationSolution<Integer>>(1);
        List<PermutationSolution<Integer>> pop1 = new ArrayList<PermutationSolution<Integer>>(1);

        int l = 2;
        while (l <= 2) {
            if (l == 1) {
                pop1.clear();
                current_pop1.clear();

                current_solution = insertion_neighborhood(current_solution, selectFac);
                pop1.add(solution);
                current_pop1.add(current_solution);
                current_pop1 = evaluator.evaluate(current_pop1, problem);
                pop1 = evaluator.evaluate(pop1, problem);
*//*                if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) == pop1.get(0).getObjective(0) &&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) &&current_pop1.get(0).getObjective(1) == pop1.get(0).getObjective(1)) )
                {*//*
                if(group==1){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))  )
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
                    } else {
                        l++;
                    }
                }
                if(group==2){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))  )
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
                    } else {
                        l++;
                    }
                }
                if(group==3){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) ) )
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
                    } else {
                        l++;
                    }
                }
                *//*if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    //l=0;
                } else {
                    l++;
                }*//*
            }

            if (l == 2) {
                pop1.clear();
                current_pop1.clear();

                current_solution = exchange_neighborhood(solution, selectFac);
                pop1.add(solution);
                current_pop1.add(current_solution);
                current_pop1 = evaluator.evaluate(current_pop1, (Problem<PermutationSolution<Integer>>) problem);
                pop1 = evaluator.evaluate(pop1, (Problem<PermutationSolution<Integer>>) problem);


*//*               if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) == pop1.get(0).getObjective(0) &&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) &&current_pop1.get(0).getObjective(1) == pop1.get(0).getObjective(1)) )
               {*//*
                if(group==1){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))  )
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
                    } else {
                        l++;
                    }
                }
                if(group==2){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))  )
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
                    } else {
                        l++;
                    }
                }
                if(group==3){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) ) )
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
                    } else {
                        l++;
                    }
                }
                *//*if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    //l=0;
                } else {
                    l++;
                }*//*
            }
            //else{return solution;}
            //l++;
        }
        return solution;
    }

    public PermutationSolution<Integer> insertion_neighborhood(PermutationSolution<Integer> solution, List<Integer> selectFac) {
        Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        PermutationSolution<Integer> solutionNew  = problem.createSolution();
        int a, i , j;
        // PermutationSolution<Integer> solutiontemp = problem.createSolution();
        //List<List<Integer>> t = new ArrayList<>();  //存工厂号下对应的工件序列的下标
        //ArrayList<List<Integer>> N = new ArrayList<>();
        int [][] N= new int[numberOfFactories][solution.getNumberOfVariablesid()];       //存相同工厂的工件下标

        List<Integer> v = new ArrayList<>();
        int[] ind = new int[selectFac.size()];     //存工厂号
//对0，1，2工厂的工件顺序排列
        int [][] len=new int[numberOfFactories][1];
        for (int r = 0; r < numberOfFactories; r++) {
            int h=0;
            for (int y = 0; y < solution.getNumberOfVariablesid(); y++) {
                if (solution.getVariableValueid(y) == r) {  //等于工厂号的下标
                    N[r][h]=y;     //等于工厂号的下标
                    h++;
                }
            }
            len[r][0]=h;   //工厂的工件个数  0，1，2长度
        }

        for (int r = 0; r < selectFac.size(); r++) {
            int m;int n;//int hao=0;
            ind[r] = selectFac.get(r);  //几号工厂
            int c=ind[r];
            int[] rList=new int [len[c][0]];
            for(int k=0;k<len[c][0];k++){
                //rList.add(N[r][k]);            // rList里面存的工件的下标
                rList[k]=N[c][k];      // rList里面存的工件的下标
            }

            int t=A.nextInt(rList.length); //m = N[r][t];           // rList里面存的工件的下标
            int g=A.nextInt(rList.length); //n = N[r][g];            //t存的是rList里内容的下标   t下标下对应的是工件本身号

            if(t==g) {
                int end=0;
                while(end!=-1){
                    g=A.nextInt(rList.length); //n = N[r][g];
                    //n =A.nextInt(len[r].length);
                    if(t!=g){
                        end=-1;
                    }
                }
                if (t < g) {
                    // i = m;j = n;
                    i=t; j=g;
                } else {
                    //j = m;i = n;
                    i=g; j=t;
                }
            }
            else{
                if (t < g) {
                    //i = m;j = n;
                    i=t; j=g;
                } else {
                    //j = m;i = n;
                    i=g; j=t;
                }
            }
            //i，j存的是 rList 里内容(粒子下标)的下标         即N[r]里面的下标

            if ( i != 0&&j != rList.length-1) {
                int jobi=rList[i]; //N[r][i];
                int jobj=rList[j];//N[r][j];
                for (a = 0; a < i; a++) {
                    int jobIdx=rList[a];   //工件的下标
                    int temp1 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp1);
                }
                int temp2 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp2);
                for (a = i; a < j; a++) {
                    int jobIdx=rList[a];
                    int jobIdx1=rList[a+1];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx1, temp3);
                }
                for (a = j + 1; a <= rList.length-1; a++) {
                    int jobIdx=rList[a];
                    int temp4 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp4);
                }
            }
            else if (i == 0 && i != j && j!= rList.length-1) {
                int jobi=rList[i];
                int jobj=rList[j];
                int temp1 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp1);
                for (a = i; a < j; a++) {
                    int jobIdx=rList[a];
                    int jobIdx1=rList[a+1];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx1, temp3);
                }
                for (a = j + 1; a <= rList.length-1; a++) {
                    int jobIdx=rList[a];
                    int temp4 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp4);
                }

            }
            else if (i == 0 && j== rList.length-1) {
                int jobi=rList[i];
                int jobj=rList[j];
                int temp1 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp1);
                for (a = i; a < rList.length-1; a++) {
                    int jobIdx=rList[a];
                    int jobIdx1=rList[a+1];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx1, temp3);
                }

            }
            else
            {
                int jobi=rList[i];
                int jobj=rList[j];
                int temp = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp);
                for (a = 0; a < i; a++) {
                    int jobIdx=rList[a];
                    int temp1 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx, temp1);
                }
                    *//*int temp2 = solutiontemp.getVariableValue(j);
                    solutionNew.setVariableValue(i, temp2);*//*
                for (a = i; a < rList.length-1; a++) {
                    int jobIdx=rList[a];
                    int jobIdx1=rList[a+1];
                    int temp3 = solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx1, temp3);
                }
            }
        }


        ///////////////////////////////////////////////////////

        int [] no={0,1,2};
        for(int d=0;d<numberOfFactories;d++){
            for(int l=0;l<selectFac.size();l++) {
                if(selectFac.get(l)==no[d]) no[d]=-1;
            }
        }

        for(int d=0;d<numberOfFactories;d++){
            if(no[d]!=-1 ){
                for (a = 0; a < len[d][0]; a++) {
                    int jobIdx=N[d][a];
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
    public PermutationSolution<Integer> reversion_neighborhood (PermutationSolution < Integer > solution, List < Integer > selectFac){
        Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        PermutationSolution<Integer> solutionNew  = problem.createSolution();
        int a, i, j,b;
        PermutationSolution<Integer> solutiontemp = problem.createSolution();
        //List<List<Integer>> t = new ArrayList<>();  //存工厂号下对应的工件序列的下标
        //ArrayList<List<Integer>> N = new ArrayList<>();
        int [][] N= new int[3][solution.getNumberOfVariablesid()];

        List<Integer> v = new ArrayList<>();
        int[] ind = new int[selectFac.size()];     //存工厂号
//对0，1，2工厂的工件顺序排列
        int [][] len=new int[3][1];
        for (int r = 0; r < numberOfFactories; r++) {
            int h=0;
            for (int y = 0; y < solution.getNumberOfVariablesid(); y++) {
                if (solution.getVariableValueid(y) == r) {  //等于工厂号的下标
                    N[r][h]=y;     //等于工厂号的下标
                    h++;
                    //System.out.println(N[r]);
                    // x++;
                }
            }
            len[r][0]=h;   //工厂的工件个数  0，1，2长度
        }
        int nums = 0;
        int[] flag = new int[numberOfFactories];
        int[] flagBeg = new int[numberOfFactories];
        for (int r = 0; r < numberOfFactories; r++) {
            for (int y = 0; y < len[r][0]; y++) {
                int temp1 = solution.getVariableValue(N[r][y]);    //工件号
                solutiontemp.setVariableValue(nums, temp1);
                //int temp2 =  solution.getVariableValueid(NEW.get(r).get(y));    //工厂号
                solutiontemp.setVariableValueid(nums, r);
                //solutionNew.setVariableValueid(nums,solutionNew.getVariableValue(nums));
                nums++;
            }
            flagBeg[r]=nums-len[r][0];
            flag[r] = nums - 1; //工厂的最后一个下标
        }

        for (int r = 0; r < selectFac.size(); r++) {
            int m, n;
            ind[r] = selectFac.get(r);  //几号工厂
            if (ind[r] != 0) {
                m = A.nextInt(len[ind[r]][0]) +flagBeg[ind[r]];
                n = A.nextInt(len[ind[r]][0]) +flagBeg[ind[r]];

                if (m < n) {
                    i = m;
                    j = n;
                } else {
                    j = m;
                    i = n;
                }
                if (i != j && i != flagBeg[ind[r]] && (j != flag[ind[r]])) {
                    for (a = (flag[ind[r] - 1] +1); a <= i; a++) {
                        int temp1 = solutiontemp.getVariableValue(a);
                        solutionNew.setVariableValue(a, temp1);
                    }
                    for (a = j; a <= flag[ind[r]]; a++) {
                        int temp2 = solutiontemp.getVariableValue(a);
                        solutionNew.setVariableValue(a, temp2);
                    }
                    if ((j - i) % 2 != 0) {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + (x / 2); a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    } else {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + x / 2; a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    }
                }

                if (i != j && i == flagBeg[ind[r]] && (j == flag[ind[r]])) {
                    int temp1 = solutiontemp.getVariableValue(j);
                    solutionNew.setVariableValue(i, temp1);
                    int temp2 = solutiontemp.getVariableValue(i);
                    solutionNew.setVariableValue(j, temp2);
                    if ((j - i) % 2 != 0) {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + (x / 2); a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    } else {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + x / 2; a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    }
                }
                if (i != j && i == flagBeg[ind[r]] && (j != flag[ind[r]])) {
                    int temp1 = solutiontemp.getVariableValue(i);
                    solutionNew.setVariableValue(i, temp1);
                    if ((j - i) % 2 != 0) {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + (x / 2); a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    } else {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + x / 2; a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    }
                    for (a = j; a <= flag[ind[r]]; a++) {
                        int temp5 = solutiontemp.getVariableValue(a);
                        solutionNew.setVariableValue(a, temp5);
                    }

                }
                if (i != j && i != flagBeg[ind[r]] && (j == flag[ind[r]])) {
                    int temp1 = solutiontemp.getVariableValue(j);
                    solutionNew.setVariableValue(j, temp1);
                    for (a = (flag[ind[r] - 1] +1); a <= i; a++) {
                        int temp5 = solutiontemp.getVariableValue(a);
                        solutionNew.setVariableValue(a, temp5);
                    }
                    if ((j - i) % 2 != 0) {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + (x / 2); a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    } else {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + x / 2; a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    }
                }

            } else {//工厂从0开始
                m = A.nextInt(flag[ind[r]]);
                n = A.nextInt(flag[ind[r]]);

                if (m < n) {
                    i = m;
                    j = n;
                } else {
                    j = m;
                    i = n;
                }
                if (i != j && i != 0 && (j != flag[ind[r]])) {
                    for (a = 0; a <= i; a++) {
                        int temp1 = solutiontemp.getVariableValue(a);
                        solutionNew.setVariableValue(a, temp1);
                    }
                    for (a = j; a <= flag[ind[r]]; a++) {
                        int temp2 = solutiontemp.getVariableValue(a);
                        solutionNew.setVariableValue(a, temp2);
                    }
                    if ((j - i) % 2 != 0) {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + (x / 2); a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    } else {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + x / 2; a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    }
                }

                if (i != j && i == 0 && (j == flag[ind[r]])) {
                    int temp1 = solutiontemp.getVariableValue(j);
                    solutionNew.setVariableValue(i, temp1);
                    int temp2 = solutiontemp.getVariableValue(i);
                    solutionNew.setVariableValue(j, temp2);
                    if ((j - i) % 2 != 0) {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + (x / 2); a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    } else {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + x / 2; a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    }
                }
                if (i != j && i == 0 && (j != flag[ind[r]])) {
                    int temp1 = solutiontemp.getVariableValue(i);
                    solutionNew.setVariableValue(i, temp1);
                    if ((j - i) % 2 != 0) {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + (x / 2); a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    } else {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + x / 2; a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    }
                    for (a = j; a <= flag[ind[r]]; a++) {
                        int temp5 = solutiontemp.getVariableValue(a);
                        solutionNew.setVariableValue(a, temp5);
                    }

                }
                if (i != j && i != 0 && (j == flag[ind[r]])) {
                    int temp1 = solutiontemp.getVariableValue(j);
                    solutionNew.setVariableValue(j, temp1);
                    for (a = 0; a <= i; a++) {
                        int temp5 = solutiontemp.getVariableValue(a);
                        solutionNew.setVariableValue(a, temp5);
                    }
                    if ((j - i) % 2 != 0) {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + (x / 2); a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    } else {
                        int x = j - i - 1;
                        for (a = i + 1, b = j - 1; a <= i + x / 2; a++, b--) {
                            int temp3 = solutiontemp.getVariableValue(b);
                            solutionNew.setVariableValue(a, temp3);
                            int temp4 = solutiontemp.getVariableValue(a);
                            solutionNew.setVariableValue(b, temp4);
                        }
                    }
                }

            }
        }

        int [] no={0,1,2};
        for(int d=0;d<numberOfFactories;d++){
            for(int l=0;l<selectFac.size();l++) {
                if(selectFac.get(l)==no[d]) no[d]=-1;
            }
        }

        for(int d=0;d<numberOfFactories;d++){
            if(no[d]!=-1){
                for (a = flagBeg[d]; a < len[d][0]; a++) {
                    int temp = solutiontemp.getVariableValue(a);
                    solutionNew.setVariableValue(a, temp);
                }

            }
        }
*//*            for (a = 0; a < solutiontemp.getNumberOfVariablesid(); a++) {
                int temp = solutiontemp.getVariableValueid(a);
                solutionNew.setVariableValueid(a, temp);
            }*//*
        return solutionNew;
    }


    public PermutationSolution<Integer> exchange_neighborhood(PermutationSolution < Integer > solution, List < Integer > selectFac){
        Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        PermutationSolution<Integer> solutionNew  = problem.createSolution();
        int a, i, j,b;
        // PermutationSolution<Integer> solutiontemp = problem.createSolution();
        //List<List<Integer>> t = new ArrayList<>();  //存工厂号下对应的工件序列的下标
        //ArrayList<List<Integer>> N = new ArrayList<>();
        int [][] N= new int[3][solution.getNumberOfVariablesid()];

        List<Integer> v = new ArrayList<>();
        int[] ind = new int[selectFac.size()];     //存工厂号
//对0，1，2工厂的工件顺序排列
        int [][] len=new int[3][1];
        for (int r = 0; r < numberOfFactories; r++) {
            int h=0;
            for (int y = 0; y < solution.getNumberOfVariablesid(); y++) {
                if (solution.getVariableValueid(y) == r) {  //等于工厂号的下标
                    N[r][h]=y;     //等于工厂号的下标
                    h++;
                }
            }
            len[r][0]=h;   //工厂的工件个数  0，1，2长度
        }

        for (int r = 0; r < selectFac.size(); r++) {
            int m,n;
            ind[r] = selectFac.get(r);  //几号工厂

            int c=ind[r];
            int[] rList=new int [len[c][0]];
            for(int k=0;k<len[c][0];k++){
                //rList.add(N[r][k]);            // rList里面存的工件的下标
                rList[k]=N[c][k];      // rList里面存的工件的下标
            }


            int t=A.nextInt(rList.length); //m = N[r][t];           // rList里面存的工件的下标
            int g=A.nextInt(rList.length); //n = N[r][g];            //t存的是rList里内容的下标   t下标下对应的是工件本身号

            if(t==g) {
                int end=0;
                while(end!=-1){
                    g=A.nextInt(rList.length); //n = N[r][g];
                    //n =A.nextInt(len[r].length);
                    if(t!=g){
                        end=-1;
                    }
                }
                if (t < g) {
                    // i = m;j = n;
                    i=t; j=g;
                } else {
                    //j = m;i = n;
                    i=g; j=t;
                }
            }
            else{
                if (t < g) {
                    //i = m;j = n;
                    i=t; j=g;
                } else {
                    //j = m;i = n;
                    i=g; j=t;
                }
            }
            if(i!=0 &&(j!=rList.length-1)){
                for (a=0; a<i; a++){
                    int jobIdx=rList[a];
                    int temp1 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp1);
                }
                int jobi=rList[i];
                int jobj=rList[j];
                int temp2 = solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi, temp2);
                for (a=i+1; a<j; a++){
                    int jobIdx=rList[a];
                    int temp3 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp3);
                }
                int temp4 =  solution.getVariableValue(jobi);
                solutionNew.setVariableValue(jobj,temp4);
                for (a=j+1; a<=rList.length-1; a++){
                    int jobIdx=rList[a];
                    int temp5 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp5);
                }
            }
            if(i==0 && j==rList.length-1-1){
                int jobi=rList[i];
                int jobj=rList[j];
                int temp1 =  solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi,temp1);
                int temp2 =  solution.getVariableValue(jobi);
                solutionNew.setVariableValue(jobj,temp2);
                for (a=i+1; a<rList.length-1; a++){
                    int jobIdx=rList[a];
                    int temp3 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp3);
                }
            }

            if(i==0 && j!=rList.length-1){
                int jobi=rList[i];
                int jobj=rList[j];
                int temp1 =  solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi,temp1);
                for (a=i+1; a<j; a++){
                    int jobIdx=rList[a];
                    int temp3 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp3);
                }
                int temp2 =  solution.getVariableValue(jobi);
                solutionNew.setVariableValue(jobj,temp2);
                for (a=j+1; a<=rList.length-1; a++){
                    int jobIdx=rList[a];
                    int temp3 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp3);
                }
            }

            if(i!=0 && j==rList.length-1){
                int jobi=rList[i];
                int jobj=rList[j];
                int temp1 =  solution.getVariableValue(jobj);
                solutionNew.setVariableValue(jobi,temp1);
                for (a=0; a<i; a++){
                    int jobIdx=rList[a];
                    int temp3 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp3);
                }
                int temp2 =  solution.getVariableValue(jobi);
                solutionNew.setVariableValue(jobj,temp2);
                for (a=i+1; a<=rList.length-1; a++){
                    int jobIdx=rList[a];
                    int temp3 =  solution.getVariableValue(jobIdx);
                    solutionNew.setVariableValue(jobIdx,temp3);
                }
            }


        }

/////////////////////////////////////////////////////////////
        int [] no={0,1,2};
        for(int d=0;d<numberOfFactories;d++){
            for(int l=0;l<selectFac.size();l++) {
                if(selectFac.get(l)==no[d]) no[d]=-1;
            }
        }

        for(int d=0;d<numberOfFactories;d++){
            if(no[d]!=-1 ){
                for (a = 0; a < len[d][0]; a++) {
                    int jobIdx=N[d][a];
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

    public double calculateNewQ ( double r, double q)
    {
        return (r + rew * q);
    }

    public int getMaxQ ( double[][] Q){
        int maxQ = 0;
        for (int i = 0; i < Q.length; i++) {
            if (Q[0][i] > Q[0][maxQ]) maxQ = i;
        }
        return maxQ;
    }*/
    protected List<PermutationSolution<Integer>> PDDRFFselect (List < PermutationSolution < Integer >> swarm,
                                                               List < PermutationSolution < Integer >> swarm2,int[] DEswarmtempPdflag){

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
        return swarm;   //  原始种群的个数
    }

    @Override
    protected void updatePosition(List<PermutationSolution<Integer>> swarm)  {
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        double r1, r2;
        double c, m;
        for (int i = 0; i < upSize; i++) {

            ArrayList<SO> listV = new ArrayList<>();
            ArrayList<SO> listVa = new ArrayList<>();  //用于工厂向量
            //用于工厂向量的DE交换序
            ArrayList<ST> listV2 = new ArrayList<>(); //用于工厂向量
            //用于工厂向量的变异

            int len = 0;
            int len1 = 0;
            PermutationSolution<Integer> particle = (PermutationSolution<Integer>) groupU1Solution.get(i).copy();

            //Parameters for velocity equation
            r1 = random.nextDouble() * Rand_k;
            r2 = random.nextDouble() * Rand_k;  //生成一个0~Rand_k的数
            //

            //自身初速度
            SO s1 = new SO(randomGenerator.nextInt(0,particle.getNumberOfVariables()-1),
                    randomGenerator.nextInt(0,particle.getNumberOfVariables()-1));

            listV.add(s1);
            addNew4JobSequenceVectorByExchangeSequence(particle,listV);

            //历史最优
            listV.clear();
            ArrayList<SO> vtemp1 = getDifferenceOfJobSequenceVectorByExchangeSequence(upGr1HisOptIndividual.get(i), particle);
            len = (int) (vtemp1.size() * r1);

            for(int j=0;j<len;j++){
                listV.add(vtemp1.get(j));
            }
            addNew4JobSequenceVectorByExchangeSequence(particle,listV);

/*            c = random.nextDouble();
            m = random.nextDouble();
            if (c < Cross_c) {
                *//*ArrayList<SO> vtempa = getDifferenceOfFactoryVectorByExchangeSequence(upGr1HisOptIndividual.get(i), particle); //针对工厂向量的差异
                len1 = (int) (vtempa.size() * r1);
                for (int j = 0; j < len1; j++) {
                    listVa.add(vtempa.get(j));
                }
                addNew4FactoryVectorByExchangeSequence(particle, listVa);*//*
                getCrossOfFactoryVectorBySingle(upGr1HisOptIndividual.get(i) ,particle);    //单点交叉

            }
            if (m < Mutation_m) {
                //确定针对工厂向量
                ST q = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                listV2.add(q);
                addNew4FactoryVectorByRandom(particle, listV2);
            }*/

            //全局最优
            listV.clear();
            listVa.clear();
            listV2.clear();

            ArrayList<SO> vtemp2 = getDifferenceOfJobSequenceVectorByExchangeSequence(all3GlobalOptIndividuals.get(0), particle);
            len = (int) (vtemp2.size() * r2);

            for(int j=0;j<len;j++){
                listV.add(vtemp2.get(j));
            }
            addNew4JobSequenceVectorByExchangeSequence(particle,listV);

/*            c = random.nextDouble();
            m = random.nextDouble();
            if (c < Cross_c) {
               *//* ArrayList<SO> vtempa1 = getDifferenceOfFactoryVectorByExchangeSequence(all3GlobalOptIndividuals.get(0), particle);
                len1 = (int) (vtempa1.size() * r2);
                for (int j = 0; j < len1; j++) {
                    listVa.add(vtempa1.get(j));
                }
                addNew4FactoryVectorByExchangeSequence(particle, listVa);*//*
                getCrossOfFactoryVectorBySingle(all3GlobalOptIndividuals.get(0), particle);    //单点交叉
            }
            if (m < Mutation_m) {
                ST q1 = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                listV2.add(q1);
                addNew4FactoryVectorByRandom(particle, listV2);
            }*/
            groupU1Solution.set(i, particle);
        }

        for (int i = 0; i < centralSize; i++) {

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
            SO s1 = new SO(randomGenerator.nextInt(0,particle.getNumberOfVariables()-1),
                    randomGenerator.nextInt(0,particle.getNumberOfVariables()-1));

            listV.add(s1);
            addNew4JobSequenceVectorByExchangeSequence(particle,listV);

            //历史最优
            listV.clear();
            listVa.clear();
            listV2.clear();

            ArrayList<SO> vtemp1 = getDifferenceOfJobSequenceVectorByExchangeSequence(centralGr2HisOptIndividual.get(i), particle);
            len = (int) (vtemp1.size() * r1);

            for(int j=0;j<len;j++){
                listV.add(vtemp1.get(j));
            }
            addNew4JobSequenceVectorByExchangeSequence(particle,listV);

/*            c = random.nextDouble();
            m = random.nextDouble();
            if (c < Cross_c) {
                *//*ArrayList<SO> vtempa = getDifferenceOfFactoryVectorByExchangeSequence(centralGr2HisOptIndividual.get(i), particle);
                len1 = (int) (vtempa.size() * r1);
                for (int j = 0; j < len1; j++) {
                    listVa.add(vtempa.get(j));
                }
                addNew4FactoryVectorByExchangeSequence(particle, listVa);*//*
                getCrossOfFactoryVectorBySingle(centralGr2HisOptIndividual.get(i), particle);    //单点交叉
            }
            if (m < Mutation_m) {
                ST q = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                listV2.add(q);
                addNew4FactoryVectorByRandom(particle, listV2);
            }*/

            //全局最优
            listV.clear();
            listVa.clear();
            listV2.clear();

            ArrayList<SO> vtemp2 = getDifferenceOfJobSequenceVectorByExchangeSequence(all3GlobalOptIndividuals.get(1), particle);
            len = (int) (vtemp2.size() * r2);

            for(int j=0;j<len;j++){
                listV.add(vtemp2.get(j));
            }
            addNew4JobSequenceVectorByExchangeSequence(particle,listV);

/*            if (c < Cross_c) {
                *//*ArrayList<SO> vtempa1 = getDifferenceOfFactoryVectorByExchangeSequence(all3GlobalOptIndividuals.get(1), particle);
                len1 = (int) (vtempa1.size() * r2);
                for (int j = 0; j < len1; j++) {
                    listVa.add(vtempa1.get(j));
                }
                addNew4FactoryVectorByExchangeSequence(particle, listVa);*//*
                getCrossOfFactoryVectorBySingle(all3GlobalOptIndividuals.get(1), particle);    //单点交叉
            }
            if (m < Mutation_m) {
                ST q1 = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                listV2.add(q1);
                addNew4FactoryVectorByRandom(particle, listV2);
            }*/
            groupC2Solution.set(i, particle);
        }

        for (int i = 0; i < downSize; i++) {

            ArrayList<SO> listV = new ArrayList<>();
            ArrayList<SO> listVa = new ArrayList<>();
            ArrayList<ST> listV2 = new ArrayList<>();
            int len = 0;
            int len1 = 0;
            PermutationSolution<Integer> particle = (PermutationSolution<Integer>) groupD3Solution.get(i).copy();

            //Parameters for velocity equation
            r1 = random.nextDouble();
            r2 = random.nextDouble();
            //自身初速度
            SO s1 = new SO(randomGenerator.nextInt(0,particle.getNumberOfVariables()-1),
                    randomGenerator.nextInt(0,particle.getNumberOfVariables()-1));

            listV.add(s1);
            addNew4JobSequenceVectorByExchangeSequence(particle,listV);

            //历史最优
            listV.clear();
            listVa.clear();
            listV2.clear();
            ArrayList<SO> vtemp1 = getDifferenceOfJobSequenceVectorByExchangeSequence(downGr3HisOptIndividual.get(i), particle);
            len = (int) (vtemp1.size() * r1);

            for(int j=0;j<len;j++){
                listV.add(vtemp1.get(j));
            }
            addNew4JobSequenceVectorByExchangeSequence(particle,listV);

/*            c = random.nextDouble();
            m = random.nextDouble();
            if (c < Cross_c) {
                *//*ArrayList<SO> vtempa = getDifferenceOfFactoryVectorByExchangeSequence(downGr3HisOptIndividual.get(i), particle);
                len1 = (int) (vtempa.size() * r1);
                for (int j = 0; j < len1; j++) {
                    listVa.add(vtempa.get(j));
                }
                addNew4FactoryVectorByExchangeSequence(particle, listVa);*//*
                getCrossOfFactoryVectorBySingle(downGr3HisOptIndividual.get(i), particle);    //单点交叉
            }
            if (m < Mutation_m) {
                ST q = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                listV2.add(q);
                addNew4FactoryVectorByRandom(particle, listV2);
            }*/

            //全局最优
            listV.clear();
            listVa.clear();
            listV2.clear();

            ArrayList<SO> vtemp2 = getDifferenceOfJobSequenceVectorByExchangeSequence(all3GlobalOptIndividuals.get(2), particle);
            len = (int) (vtemp2.size() * r2);

            for(int j=0;j<len;j++){
                listV.add(vtemp2.get(j));
            }
            addNew4JobSequenceVectorByExchangeSequence(particle,listV);

/*            c = random.nextDouble();
            m = random.nextDouble();
            if (c < Cross_c) {
                *//*ArrayList<SO> vtempa1 = getDifferenceOfFactoryVectorByExchangeSequence(all3GlobalOptIndividuals.get(2), particle);
                len1 = (int) (vtempa1.size() * r2);
                for (int j = 0; j < len1; j++) {
                    listVa.add(vtempa1.get(j));
                }
                addNew4FactoryVectorByExchangeSequence(particle, listVa);*//*
                getCrossOfFactoryVectorBySingle(all3GlobalOptIndividuals.get(2), particle);    //单点交叉
            }
            if (m < Mutation_m) {
                ST q1 = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                listV2.add(q1);
                addNew4FactoryVectorByRandom(particle, listV2);
            }*/
            groupD3Solution.set(i, particle);
        }

        merge(swarm);

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

        for (int i = 0 ; i < boundflag; i++) {
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

    private void getCrossOfFactoryVectorBySingle(PermutationSolution<Integer> a,PermutationSolution<Integer> b) {       //对工厂向量进行单点交叉
        int index;
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int boundflag = random.nextInt(b.getNumberOfVariablesid());          //  随机产生一个单点下标
        for (int i = boundflag; i < b.getNumberOfVariablesid(); i++) {
            index = i;
            cross4FactoryVectorBySingle(a, b, i, index);   //交换下标i与下标index的值
        }
    }


    private ArrayList<SO> getDifferenceOfFactoryVectorByExchangeSequence(PermutationSolution<Integer> a, PermutationSolution<Integer> b) {    //TODO 为什么针对工厂向量计算交换序？
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
        int temp1 =  a.getVariableValue(index1);
        int temp2 =  a.getVariableValue(index2);

        a.setVariableValue(index1, temp2);
        a.setVariableValue(index2, temp1);
        //System.out.print(a);
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

    private void addNew4FactoryVectorByRandom(PermutationSolution<Integer> arr, ArrayList<ST> list) {
        ST s;
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        for (int i = 0; i < list.size(); i++) {
            s = list.get(i);
            int r = random.nextInt(3); //TODO 为什么写成了3? 难道是因为3个工厂吗？
            exchangeIndex4FactoryVectorByRandom(arr, s.getX(), r);             //   随机选一位数进行改变
        }
    }

    private void cross4FactoryVectorBySingle(PermutationSolution<Integer> a,PermutationSolution<Integer> b, int index1, int index2) {     //交换值
        int temp1 = a.getVariableValueid(index1);    //工厂
        int temp2 = b.getVariableValueid(index2);

        a.setVariableValueid(index1, temp2);
        b.setVariableValueid(index2, temp1);
    }

    private void exchangeIndex4FactoryVectorByExchangeSequence(PermutationSolution<Integer> a, int index1, int index2) {     //交换值
        int temp1 = a.getVariableValueid(index1);    //工厂
        int temp2 = a.getVariableValueid(index2);

        a.setVariableValueid(index1, temp2);
        a.setVariableValueid(index2, temp1);
    }

    private void exchangeIndex4FactoryVectorByRandom(PermutationSolution<Integer> a, int index1, int value) {     //交换值
        //int temp1 =  a.getVariableValueid(index1);
        a.setVariableValueid(index1, value);
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
            if(object1 > integerPermutationSolution.getObjective(0))object1=integerPermutationSolution.getObjective(0);
            if(object2 > integerPermutationSolution.getObjective(1))object2=integerPermutationSolution.getObjective(1);
            if(object3 > integerPermutationSolution.getObjective(2))object3=integerPermutationSolution.getObjective(2);
        }
        System.out.println("第"+index+"代："+"object1="+object1+" "+"object2="+object2+" "+"object3="+object3);
        index++;
    }

    @Override
    public List<PermutationSolution<Integer>> getResult() {
        return globallyOptimalIndividual;
    }

    @Override public String getName() {
        return "MOPSODivideSubgroup" ;
    }

    @Override public String getDescription() {
        return "Optimized MOPSODivideSubgroup" ;
    }

}
