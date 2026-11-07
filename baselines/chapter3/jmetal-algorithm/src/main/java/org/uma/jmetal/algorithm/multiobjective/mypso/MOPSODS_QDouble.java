package org.uma.jmetal.algorithm.multiobjective.mypso;

//import com.sun.org.apache.bcel.internal.generic.NEW;

import org.uma.jmetal.algorithm.impl.AbstractParticleSwarmOptimization;
import org.uma.jmetal.algorithm.multiobjective.mypso.util.SO;
import org.uma.jmetal.algorithm.multiobjective.mypso.util.ST;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.problem.multiobjective.dfsp.DFSP3Double;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

/*import org.uma.jmetal.runner.lc_psode.sequence1;
import org.uma.jmetal.runner.lc_psode.sequence2;
import org.uma.jmetal.runner.lc_psode.sequence3;*/

/**
 * Class implementing the OMOPSO algorithm
 */

@SuppressWarnings("serial")
public class MOPSODS_QDouble extends AbstractParticleSwarmOptimization<PermutationSolution<Integer>, List<PermutationSolution<Integer>>> {

    private Problem<PermutationSolution<Integer>> problem1;
    private final SolutionListEvaluator<PermutationSolution<Integer>> evaluator;
    private DFSP3Double Clusterindex;
    private int[][] K_means;

    private int swarmSize;
    private int upSize;
    private int centralSize;
    private int downSize;
    //private double Probability;
    private double DErate;
    //    private int archiveSize;
    private int maxIterations;

    private ArrayList<List<PermutationSolution<Integer>>> tempSwarm;
    private List<PermutationSolution<Integer>> globallyOptimalIndividual;
    private ArrayList<List<int[]>> Pdflag;
    private List<int[]> Pgdflag;


    private List<PermutationSolution<Integer>> sub1;
    private List<PermutationSolution<Integer>> sub2;
    private List<PermutationSolution<Integer>> sub3;

    private ArrayList<List<PermutationSolution<Integer>>> Pd1;
    private ArrayList<List<PermutationSolution<Integer>>> Pd2;
    private ArrayList<List<PermutationSolution<Integer>>> Pd3;

    private ArrayList<List<int[]>> Pd1flag;
    private ArrayList<List<int[]>> Pd2flag;
    private ArrayList<List<int[]>> Pd3flag;

    private List<PermutationSolution<Integer>> bb1;
    private List<PermutationSolution<Integer>> bb2;
    private List<PermutationSolution<Integer>> bb3;

    private List<PermutationSolution<Integer>> bb4;

    private int currentIteration;
    private JMetalRandom randomGenerator;  //随机产生器
    private double Rand_k;
    private double Cross_c;
    private double Mutation_m;
    private double DEcrossoverRates;
    private double DEmutationRate;

    private ArrayList<List<Integer>> action;
    private double Qnums;
    private int numberOfFactories = 3;
    private double  tl = 0.7;   //0.8  0.85
    private double gamma = 0.7;

    /**
     * Constructor
     */
    public MOPSODS_QDouble(double crossoverRate, double mutationRate, double rand_k,
                           Problem<PermutationSolution<Integer>> problem1, SolutionListEvaluator<PermutationSolution<Integer>> evaluator,
                           int swarmSize, int maxIterations, int upSize, int centralSize, int downSize, double DERate, double DEcrossoverRates, double DEmutationRate, double Qnums) {
        this.problem1 = problem1;
        this.evaluator = evaluator;

        this.swarmSize = swarmSize;
        this.maxIterations = maxIterations;   //500*200    也就是说经历了500次迭代

        this.upSize = upSize;  //66
        this.centralSize = centralSize;    //68
        this.downSize = downSize;          //66
        this.DErate = DERate;
        this.Rand_k = rand_k;
        this.Mutation_m = mutationRate;
        this.Cross_c = crossoverRate;
        this.DEcrossoverRates = DEcrossoverRates;
        this.DEmutationRate = DEmutationRate;
        this.Qnums=Qnums;
        //this.archiveSize = archiveSize ;

        tempSwarm = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);   // 两层容器
        globallyOptimalIndividual = new ArrayList<PermutationSolution<Integer>>();    //一层容器

        Pdflag = new ArrayList<List<int[]>>(swarmSize);
        Pgdflag = new ArrayList<int[]>();

        sub1 = new ArrayList<>(upSize);
        sub2 = new ArrayList<>(centralSize);
        sub3 = new ArrayList<>(downSize);

        Pd1 = new ArrayList<List<PermutationSolution<Integer>>>(upSize);           // 两层容器
        Pd2 = new ArrayList<List<PermutationSolution<Integer>>>(centralSize);         // 两层容器
        Pd3 = new ArrayList<List<PermutationSolution<Integer>>>(downSize);             // 两层容器

        Pd1flag = new ArrayList<List<int[]>>(upSize);
        Pd2flag = new ArrayList<List<int[]>>(centralSize);
        Pd3flag = new ArrayList<List<int[]>>(downSize);

        bb1 = new ArrayList<PermutationSolution<Integer>>(upSize);
        bb2 = new ArrayList<PermutationSolution<Integer>>(centralSize);
        bb3 = new ArrayList<PermutationSolution<Integer>>(downSize);

        bb4 = new ArrayList<PermutationSolution<Integer>>(3);  //

        randomGenerator = JMetalRandom.getInstance();
    }

    public MOPSODS_QDouble(SolutionListEvaluator<PermutationSolution<Integer>> evaluator) {
        this.evaluator = evaluator;
    }

    @Override
    protected void initProgress() {    //第一次进化次数就是种群大小
        currentIteration = swarmSize;
        //currentIteration = 1;
        //    crowdingDistance.computeDensityEstimator(leaderArchive.getSolutionList());
    }

    @Override
    protected void updateProgress() {    //更新次数累加
        currentIteration = currentIteration + swarmSize;
        //currentIteration += 1;
        //   crowdingDistance.computeDensityEstimator(leaderArchive.getSolutionList());
    }

    @Override
    protected boolean isStoppingConditionReached() {  //是否达到终止条件
        return currentIteration >= maxIterations;
    }

    @Override
    protected List<PermutationSolution<Integer>> createInitialSwarm() {      //创建初始种群
        List<PermutationSolution<Integer>> swarm = new ArrayList<>(swarmSize);

        PermutationSolution<Integer> newSolution;   //一个粒子

        K_means = Clusterindex.jobFactoryCluster;

        for (int t = 0; t < swarmSize; t++) {

            newSolution = problem1.createSolution();
            //System.out.print(newSolution);
            //newSolution =

            /*int[][] indexArr = K_means;

            List<Integer> jobArr = new ArrayList<>(problem.getNumberOfVariables());
            //List<Integer> jobArrtemp = new ArrayList<>(problem.getNumberOfVariables());
            List<Integer> facArrtemp = new ArrayList<>(problem.getNumberOfVariables());
            List<Integer> facArr = new ArrayList<>(problem.getNumberOfVariables());
            Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            for (int i = 0; i < indexArr.length; i++) {
                //randomSequence.add(indexArr[0][i]);
                for(int k = 0;k<indexArr[i].length;k++){
                    jobArr.add(indexArr[i][k]);
                }
                org.uma.jmetal.util.research.runtime.SeededRandom.shuffle(jobArr);

                if((indexArr[i].length) % 3 ==0){
                    for(int j = 0; j<indexArr[i].length; j=j+3){
                        facArrtemp.add(0);
                        facArrtemp.add(1);
                        facArrtemp.add(2);
                    }
                }
                else{
                    int mark = (indexArr[i].length) % 3;
                    for(int j = 0; j<indexArr[i].length-mark; j=j+3){
                        facArrtemp.add(0);
                        facArrtemp.add(1);
                        facArrtemp.add(2);
                    }
                    for(int j = indexArr[i].length-mark; j<indexArr[i].length; j++) {
                        facArrtemp.add(r.nextInt(3));
                    }
                }
                //org.uma.jmetal.util.research.runtime.SeededRandom.shuffle(facArrtemp);        //打乱工厂
                for(int k = 0;k<indexArr[i].length;k++){
                    facArr.add(facArrtemp.get(k));
                }
                facArrtemp.clear();
            }

            for (int i = 0; i < newSolution.getNumberOfVariables(); i++) {
                newSolution.setVariableValue(i, jobArr.get(i)) ;      //工件向量序列
            }

            for (int i = 0; i < newSolution.getNumberOfVariablesid(); i++) {
                newSolution.setVariableValueid(i, facArr.get(i)) ;         //工厂向量序列
            }*/

            swarm.add(newSolution);
        }

/*        for (int t = swarmSize/2; t < swarmSize; t++) {
            newSolution = problem.createSolution();
            swarm.add(newSolution);
        }*/

        return swarm;
    }

    @Override
    protected List<PermutationSolution<Integer>> evaluateSwarm(List<PermutationSolution<Integer>> swarm) {    //评估
        swarm = evaluator.evaluate(swarm, (Problem<PermutationSolution<Integer>>) problem1);    //  具体实现在DFSP3
        //currentIteration=currentIteration+swarmSize;
        return swarm;
    }

    @Override
    protected void initializeLeader(List<PermutationSolution<Integer>> swarm) {
        for (int i = 0; i < swarmSize; i++) {
            globallyOptimalIndividual.add(tempSwarm.get(i).get(0));  //tempSwarm 是arraylist  Pgd是list      // 初始化全局最优解  //历史最优的第一个作为全局
            Pgdflag.add(Pdflag.get(i).get(0));
        }
    }

    @Override
    protected void initializeParticlesMemory(List<PermutationSolution<Integer>> swarm) {
        for (int i = 0; i < swarm.size(); i++) {                                          // swarmSize的区别
            ArrayList<PermutationSolution<Integer>> A = new ArrayList<PermutationSolution<Integer>>();
            A.add(swarm.get(i));
            tempSwarm.add(A);                       //  初始化历史最优解

            int[] b = new int[2];
            b[0] = b[1] = 0;
            ArrayList<int[]> c = new ArrayList<int[]>();          //一层容器
            c.add(b);
            Pdflag.add(c);

        }

    }

    @Override
    protected void initializeVelocity(List<PermutationSolution<Integer>> swarm) {

    }

    //分群
    protected void updateVelocity(List<PermutationSolution<Integer>> swarm) {           //分群更新速度

        Pd1.clear();
        Pd2.clear();
        Pd3.clear();
        Pd1flag.clear();
        Pd2flag.clear();
        Pd3flag.clear();
        sub1.clear();
        sub2.clear();
        sub3.clear();

        List<PermutationSolution<Integer>> temp1 = new ArrayList<>(swarmSize);    //单层
        List<PermutationSolution<Integer>> temp2 = new ArrayList<>(swarmSize);
        List<PermutationSolution<Integer>> temp3 = new ArrayList<>(swarmSize);

        ArrayList<List<PermutationSolution<Integer>>> tempPd1 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);    //双层   就相当于pd
        ArrayList<List<PermutationSolution<Integer>>> tempPd2 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);
        ArrayList<List<PermutationSolution<Integer>>> tempPd3 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);

        ArrayList<List<int[]>> tempPd1falg = new ArrayList<List<int[]>>();
        ArrayList<List<int[]>> tempPd2falg = new ArrayList<List<int[]>>();
        ArrayList<List<int[]>> tempPd3falg = new ArrayList<List<int[]>>();

        for (int i = 0; i < swarmSize; i++) {
            temp1.add((PermutationSolution<Integer>) swarm.get(i).copy());
            temp2.add((PermutationSolution<Integer>) swarm.get(i).copy());
            temp3.add((PermutationSolution<Integer>) swarm.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(tempSwarm.get(i).size());    // A用于存粒子的每一个历史最优
            ArrayList<int[]> B = new ArrayList<int[]>(Pdflag.get(i).size());

            for (int j = 0; j < tempSwarm.get(i).size(); j++) {

                A.add((PermutationSolution<Integer>) tempSwarm.get(i).get(j).copy());    //存每一个粒子的所有历史最优解    单层

                int[] tempB = new int[2];

                tempB[0] = Pdflag.get(i).get(j)[0];
                tempB[1] = Pdflag.get(i).get(j)[1];
                B.add(tempB);  //  暂时不用
            }

            tempPd1.add(A);      //两层   //但A是单层
            tempPd2.add(A);         //就相当于pd
            tempPd3.add(A);

            tempPd1falg.add(B);
            tempPd2falg.add(B);
            tempPd3falg.add(B);

        }

        //划分sub1
        for (int i = 0; i < upSize; i++) {
            int b = 0;
            for (int j = 1; j < temp1.size(); j++) {
                if (temp1.get(j).getObjective(0) < temp1.get(b).getObjective(0)) {
                    b = j;
                }
            }
            sub1.add(temp1.get(b));
            Pd1.add(tempPd1.get(b));
            Pd1flag.add(tempPd1falg.get(b));

            temp1.remove(b);     //单层
            tempPd1.remove(b);      //双层
            tempPd1falg.remove(b);

        }

        //划分sub2
        List<Double> aa = new ArrayList<>(swarmSize);
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
            // 计算每一个粒子的适应值
            aa.add(count2 + 1 / (count1 + 1));       //eval = q + 1/(p+1)    q是支配s的粒子个数  p是被s支配的粒子个数
        }

        for (int i = 0; i < centralSize; i++) {
            int b = 0;
            for (int j = 1; j < aa.size(); j++) {
                if (aa.get(j) < aa.get(b)) {
                    b = j;
                }
            }
            sub2.add(temp2.get(b));
            Pd2.add(tempPd2.get(b));
            Pd2flag.add(tempPd2falg.get(b));

            aa.remove(b);
            tempPd2.remove(b);
            temp2.remove(b);
            tempPd2falg.remove(b);
        }
//   划分sub3
        for (int i = 0; i < downSize; i++) {
            int b = 0;
            for (int j = 1; j < temp3.size(); j++) {
                if (temp3.get(j).getObjective(1) < temp3.get(b).getObjective(1)) {
                    b = j;
                }
            }
            sub3.add(temp3.get(b));
            Pd3.add(tempPd3.get(b));
            Pd3flag.add(tempPd3falg.get(b));

            temp3.remove(b);
            tempPd3.remove(b);
            tempPd3falg.remove(b);
        }
// 分完群进行选择
        select();

    }

    //二元锦标赛法（选三个，取最好）
    private void select() {
        bb1.clear();
        bb2.clear();
        bb3.clear();
        //  分别存放的是 三个种群中 每一个粒子历史最优中随机出来的最好的一个
        bb4.clear();

        for (int i = 0; i < upSize; i++) {
            int a1 = randomGenerator.nextInt(0, Pd1.get(i).size() - 1);
            int a2 = randomGenerator.nextInt(0, Pd1.get(i).size() - 1);
            int a3 = randomGenerator.nextInt(0, Pd1.get(i).size() - 1);
            int temp = a1;
            if (Pd1.get(i).get(a1).getObjective(0) >= Pd1.get(i).get(a2).getObjective(0) &&
                    Pd1.get(i).get(a3).getObjective(0) >= Pd1.get(i).get(a2).getObjective(0)) {
                temp = a2;
            }

            if (Pd1.get(i).get(a1).getObjective(0) >= Pd1.get(i).get(a3).getObjective(0) &&
                    Pd1.get(i).get(a2).getObjective(0) >= Pd1.get(i).get(a3).getObjective(0)) {
                temp = a3;
            }
            bb1.add(Pd1.get(i).get(temp));
            Pd1flag.get(i).get(temp)[0]++;//历史更新时，统计值加1

        }

        for (int i = 0; i < centralSize; i++) {
            int a1 = randomGenerator.nextInt(0, Pd2.get(i).size() - 1);
            int a2 = randomGenerator.nextInt(0, Pd2.get(i).size() - 1);
            int a3 = randomGenerator.nextInt(0, Pd2.get(i).size() - 1);
            int temp = a1;
            List<Double> bb = new ArrayList<>(Pd2.get(i).size());

            for (int j = 0; j < Pd2.get(i).size(); j++) {
                double count1 = 0;
                double count2 = 0;
                for (int k = 0; k < Pd2.get(i).size(); k++) {
                    if (j != k) {
                        if (Pd2.get(i).get(j).getObjective(0) <= Pd2.get(i).get(k).getObjective(0) &&
                                Pd2.get(i).get(j).getObjective(1) <= Pd2.get(i).get(k).getObjective(1)) {
                            count1 = count1 + 1;
                        }
                        if (Pd2.get(i).get(j).getObjective(0) >= Pd2.get(i).get(k).getObjective(0) &&
                                Pd2.get(i).get(j).getObjective(1) >= Pd2.get(i).get(k).getObjective(1)) {
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
            bb2.add(Pd2.get(i).get(temp));
            Pd2flag.get(i).get(temp)[0]++;

        }

        for (int i = 0; i < downSize; i++) {
            int a1 = randomGenerator.nextInt(0, Pd3.get(i).size() - 1);
            int a2 = randomGenerator.nextInt(0, Pd3.get(i).size() - 1);
            int a3 = randomGenerator.nextInt(0, Pd3.get(i).size() - 1);
            int temp = a1;
            if (Pd3.get(i).get(a1).getObjective(1) >= Pd3.get(i).get(a2).getObjective(1) &&
                    Pd3.get(i).get(a3).getObjective(1) >= Pd3.get(i).get(a2).getObjective(1)) {
                temp = a2;
            }
            if (Pd3.get(i).get(a1).getObjective(1) >= Pd3.get(i).get(a3).getObjective(1) &&
                    Pd3.get(i).get(a2).getObjective(1) >= Pd3.get(i).get(a3).getObjective(1)) {
                temp = a3;
            }
            bb3.add(Pd3.get(i).get(temp));    // 在三个历史最优里选一个最好的
            Pd3flag.get(i).get(temp)[0]++;
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
        bb4.add(globallyOptimalIndividual.get(temp));
        // Pgdflag.get(temp)[0]++;

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
                            globallyOptimalIndividual.get(i).getObjective(1) <= globallyOptimalIndividual.get(j).getObjective(1)) {
                        count1 = count1 + 1;
                    }
                    if (globallyOptimalIndividual.get(i).getObjective(0) >= globallyOptimalIndividual.get(j).getObjective(0) &&
                            globallyOptimalIndividual.get(i).getObjective(1) >= globallyOptimalIndividual.get(j).getObjective(1)) {
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
        bb4.add(globallyOptimalIndividual.get(temp));
        //Pgdflag.get(temp)[0]++;
//
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
        bb4.add(globallyOptimalIndividual.get(temp));
        // Pgdflag.get(temp)[0]++;

    }





    //更新粒子位置
    @Override
    protected void updatePosition(List<PermutationSolution<Integer>> swarm) {

        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        double r1, r2;
        double c, m;

        for (int i = 0; i < upSize; i++) {

            ArrayList<SO> listV = new ArrayList<>(); //TODO 用于哪个向量
            // 用于工件向量
            ArrayList<SO> listVa = new ArrayList<>();  //TODO 用于哪个向量
            //用于工厂向量的交换序
            ArrayList<ST> listV2 = new ArrayList<>(); //TODO 用于哪个向量
            //用于工厂向量的变异

            int len = 0;
            int len1 = 0;
            PermutationSolution<Integer> particle = (PermutationSolution<Integer>) sub1.get(i).copy();   //一维
            //System.out.print(particle);


            //Parameters for velocity equation
            r1 = random.nextDouble() * Rand_k;
            r2 = random.nextDouble() * Rand_k;  //生成一个0~Rand_k的数
            particle=addNew4JobSequenceVector(particle);


            //历史最优
            //listV.clear();
            particle=getDifferenceOfJobSequenceVector(bb1.get(i), particle,r1);

/*            c = random.nextDouble();
            m = random.nextDouble();
            if (c < Cross_c) {//TODO 确认此交叉针对的是工厂向量   //yes
                getCrossOfFactoryVectorBySingle(bb1.get(i), particle);    //单点交叉

            }
            if (m < Mutation_m) {////TODO 确认此变异针对的是工厂向量       //yes
                ST q = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                listV2.add(q);
                addNew4FactoryVectorByRandom(particle, listV2);
            }*/

            //全局最优
            particle=getDifferenceOfJobSequenceVector(bb4.get(0), particle,r2);

/*            c = random.nextDouble();
            m = random.nextDouble();
            if (c < Cross_c) {
                getCrossOfFactoryVectorBySingle(bb4.get(0), particle);    //单点交叉
            }
            if (m < Mutation_m) {
                ST q1 = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                listV2.add(q1);
                addNew4FactoryVectorByRandom(particle, listV2);
            }*/
            sub1.set(i, particle);
        }

        for (int i = 0; i < centralSize; i++) {

            ArrayList<SO> listV = new ArrayList<>();
            ArrayList<SO> listVa = new ArrayList<>(); //zj
            ArrayList<ST> listV2 = new ArrayList<>();
            int len = 0;
            int len1 = 0;
            PermutationSolution<Integer> particle = (PermutationSolution<Integer>) sub2.get(i).copy();

            //Parameters for velocity equation
            r1 = random.nextDouble() * Rand_k;
            r2 = random.nextDouble() * Rand_k;

            //自身初速度
            particle=addNew4JobSequenceVector(particle);

            //历史最优
            listV.clear();
            listVa.clear();
            listV2.clear();


            particle=getDifferenceOfJobSequenceVector(bb2.get(i), particle,r1);

/*            c = random.nextDouble();
            m = random.nextDouble();
            if (c < Cross_c) {
                *//*ArrayList<SO> vtempa = getDifferenceOfFactoryVectorByExchangeSequence(bb2.get(i), particle);
                len1 = (int) (vtempa.size() * r1);
                for (int j = 0; j < len1; j++) {
                    listVa.add(vtempa.get(j));
                }
                addNew4FactoryVectorByExchangeSequence(particle, listVa);*//*
                getCrossOfFactoryVectorBySingle(bb2.get(i), particle);    //单点交叉
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
            c = random.nextDouble();
            m = random.nextDouble();


            particle=getDifferenceOfJobSequenceVector(bb4.get(1), particle,r2);

/*            if (c < Cross_c) {
                *//*ArrayList<SO> vtempa1 = getDifferenceOfFactoryVectorByExchangeSequence(bb4.get(1), particle);
                len1 = (int) (vtempa1.size() * r2);
                for (int j = 0; j < len1; j++) {
                    listVa.add(vtempa1.get(j));
                }
                addNew4FactoryVectorByExchangeSequence(particle, listVa);*//*
                getCrossOfFactoryVectorBySingle(bb4.get(1), particle);    //单点交叉
            }
            if (m < Mutation_m) {
                ST q1 = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                listV2.add(q1);
                addNew4FactoryVectorByRandom(particle, listV2);
            }*/
            sub2.set(i, particle);
        }

        for (int i = 0; i < downSize; i++) {

            ArrayList<SO> listV = new ArrayList<>();
            ArrayList<SO> listVa = new ArrayList<>();
            ArrayList<ST> listV2 = new ArrayList<>();
            int len = 0;
            int len1 = 0;
            PermutationSolution<Integer> particle = (PermutationSolution<Integer>) sub3.get(i).copy();

            //Parameters for velocity equation
            r1 = random.nextDouble() * Rand_k;
            r2 = random.nextDouble() * Rand_k;
            //自身初速度
            particle=addNew4JobSequenceVector(particle);

            //历史最优
            listV.clear();
            listVa.clear();
            listV2.clear();

            particle=getDifferenceOfJobSequenceVector(bb3.get(i), particle,r1);

/*            c = random.nextDouble();
            m = random.nextDouble();
            if (c < Cross_c) {
                *//*ArrayList<SO> vtempa = getDifferenceOfFactoryVectorByExchangeSequence(bb3.get(i), particle);
                len1 = (int) (vtempa.size() * r1);
                for (int j = 0; j < len1; j++) {
                    listVa.add(vtempa.get(j));
                }
                addNew4FactoryVectorByExchangeSequence(particle, listVa);*//*
                getCrossOfFactoryVectorBySingle(bb3.get(i), particle);    //单点交叉
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

            particle=getDifferenceOfJobSequenceVector(bb4.get(2), particle,r2);

/*            c = random.nextDouble();
            m = random.nextDouble();
            if (c < Cross_c) {
                *//*ArrayList<SO> vtempa1 = getDifferenceOfFactoryVectorByExchangeSequence(bb4.get(2), particle);
                len1 = (int) (vtempa1.size() * r2);
                for (int j = 0; j < len1; j++) {
                    listVa.add(vtempa1.get(j));
                }
                addNew4FactoryVectorByExchangeSequence(particle, listVa);*//*
                getCrossOfFactoryVectorBySingle(bb4.get(2), particle);    //单点交叉
            }
            if (m < Mutation_m) {
                ST q1 = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                listV2.add(q1);
                addNew4FactoryVectorByRandom(particle, listV2);
            }*/

            sub3.set(i, particle);
        }

        merge(swarm);

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
    @Override
    protected void perturbation(List<PermutationSolution<Integer>> swarm) {

    }


/*    protected void perturbation(List<PermutationSolution<Integer>> swarm) {
    int QN=(int)Qnums;
        //在分群后加DE操作
        //swarm = evaluateSwarm(swarm);
        super.setSwarm(evaluateSwarm(swarm));

        List<PermutationSolution<Integer>> swarmtemp = new ArrayList<PermutationSolution<Integer>>(swarm.size());
        int[] DEswarmtempPdflag = new int[swarmSize];

       *//* action = action(numberOfFactories);
        int anum = action.size();

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
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int next = 0;
            int actionIndex;
            PermutationSolution<Integer>  getswarm1 = null;
            for (int k = 0; k < 20; k++) {
                double p = random.nextDouble();
                if (k == 0) {
                    actionIndex = random.nextInt(action.size());
                    getswarm1=learn(actionIndex, R, Q, swarm.get(i), next);
                    if ((getswarm1.getObjective(0) == swarm.get(i).getObjective(0) && getswarm1.getObjective(1) == swarm.get(i).getObjective(1)) || getswarm1.getObjective(0) < swarm.get(i).getObjective(0) ||getswarm1.getObjective(1) < swarm.get(i).getObjective(1)) next = 1;
                    else next = 0;
                    //actionIndex = getMaxQ(Q);
                } else {
                    if (p < 1 - tl) {
                        actionIndex = getMaxQ(Q);
                        getswarm1=learn(actionIndex, R, Q, swarm.get(i), next);
                        if ((getswarm1.getObjective(0) == swarm.get(i).getObjective(0) && getswarm1.getObjective(1) == swarm.get(i).getObjective(1)) || getswarm1.getObjective(0) < swarm.get(i).getObjective(0) ||getswarm1.getObjective(1) < swarm.get(i).getObjective(1)) next = 1;
                        else next = 0;
                    } else {
                        actionIndex = random.nextInt(action.size());
                        getswarm1=learn(actionIndex, R, Q, swarm.get(i), next);
                        if ((getswarm1.getObjective(0) == swarm.get(i).getObjective(0) && getswarm1.getObjective(1) == swarm.get(i).getObjective(1)) || getswarm1.getObjective(0) < swarm.get(i).getObjective(0) ||getswarm1.getObjective(1) < swarm.get(i).getObjective(1)) next = 1;
                        else next = 0;
                    }
                }
            }
            swarmtemp.add(getswarm1);
            DEswarmtempPdflag[i] = i;
        }*//*

        for(int i=0;i<swarm.size();i++){
            int[] select =DEselect(swarm);
            swarmtemp.add(DEJobFactory(swarm, DErate, select));
            DEswarmtempPdflag[i] = select[1];

        }
        swarmtemp = evaluateSwarm(swarmtemp);

        //swarm = PDDRFFselect(swarm, swarmtemp, DEswarmtempPdflag);
        super.setSwarm(PDDRFFselect(swarm,swarmtemp,DEswarmtempPdflag));

    }*/

    public PermutationSolution<Integer> learn(int a, double[][] R, double[][] Q, PermutationSolution<Integer> bestsolution, int next1,int group) {

        List<Integer> selectFac = new ArrayList<>();
        selectFac = action.get(a);
        PermutationSolution<Integer> solutiont;
        solutiont = V_N_Search(bestsolution, selectFac,group);
/*        if (solutiont.getObjective(0) == bestsolution.getObjective(0) && solutiont.getObjective(1) == bestsolution.getObjective(1)) next1 = 1;
        else next1 = 0;*/
        //double reward = R[next1][a];
/*        double Qvalue = calculateNewQ(reward, Q[next1][a]);
        Q[next1][a] = Qvalue;*/   //之前

        //Q[next1][a] = (1-alpha)*Q[next1][a]+alpha*(reward+ gamma*maxNextQ(Q[a]));


        return solutiont;
    }

/*    public double calculateNewQ ( double[][] R,double[][] Q,int a,int next1,int Qiannext)
    {
       // return (r + rew * q);
        double reward = R[Qiannext][a];
        Q[Qiannext][a] = (1-alpha) * Q[Qiannext][a] + alpha * (reward+ gamma * maxNextQ(Q[next1]));
        return Q[Qiannext][a];
    }*/
    public double calculateNewQ1 ( double[][] R,double[][] Q,int a,int next1,int Qiannext,double old0,double old1,double new0,double new1)
    {
        // return (r + rew * q);
        //double reward= R[Qiannext][a];
        double reward =old0-new0+(old1-new1);
        Q[Qiannext][a] = reward+ gamma * maxNextQ(Q[next1]);
        //Q[Qiannext][a] = (1-alpha) * Q[Qiannext][a] + alpha * (reward+ gamma * maxNextQ(Q[next1]));
        return Q[Qiannext][a];
    }

    private  int max(double[] is) {
        int max = 0;
        for(int i = 1; i < is.length; ++i) {
            if(is[i] > is[max]) max = i;
        }
        return max;
    }

    private  double maxNextQ(double[] is) {
        double max = is[0];
        for(int i = 1; i < is.length; ++i) {
            if(is[i] > max) max = is[i];
        }
        return max;
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
                current_pop1 = evaluator.evaluate(current_pop1, problem1);
                pop1 = evaluator.evaluate(pop1, problem1);
                if(group==1){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))  || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) ))
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
                    } else {
                        l++;
                    }
                }
                if(group==2){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))|| (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) ))
                    {
                        //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                        solution = current_solution;
                        //l=0;
                    } else {
                        l++;
                    }
                }
                if(group==3){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))|| (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) ) )
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
                current_pop1 = evaluator.evaluate(current_pop1, (Problem<PermutationSolution<Integer>>) problem1);
                pop1 = evaluator.evaluate(pop1, (Problem<PermutationSolution<Integer>>) problem1);
                if(group==1){
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) ) )
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
                    if((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)&&current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))|| (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1) ) )
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
        PermutationSolution<Integer> solutionNew  = problem1.createSolution();
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
            int c=ind[r];
            int[] rList=new int [len[c][0]];
            for(int k=0;k<len[c][0];k++){
                //rList.add(N[r][k]);            // rList里面存的工件的下标
                rList[k]=N[c][k];      // rList里面存的工件的下标
            }          //没问题

            int t=A.nextInt(rList.length); //m = N[r][t];           // rList里面存的工件的下标
            int g=A.nextInt(rList.length); //n = N[r][g];            //t存的是rList里内容的下标   t下标下对应的是工件本身号
            //int t=0; //m = N[r][t];           // rList里面存的工件的下标
            //int g=rList.length-1; //n = N[r][g];

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

        int [] no={0,1,2};
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
            PermutationSolution<Integer> solutionNew  = problem1.createSolution();
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

///////////////////////////////////////没问题

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
            //System.out.println(solutionNew);

            for (a = 0; a < solution.getNumberOfVariablesid(); a++) {
                int temp = solution.getVariableValueid(a);
                solutionNew.setVariableValueid(a, temp);
            }

            return solutionNew;
        }



        public int getMaxQ ( double[][] Q){
            int maxQ = 0;
            for (int i = 0; i < Q.length; i++) {
                if (Q[0][i] > Q[0][maxQ]) maxQ = i;
            }
            return maxQ;
        }


        //选择两个个体，交换序给坏的那个个体（对每个粒子做）输入的是List<S>格式
/*    private PermutationSolution<Integer> DEexe(List<PermutationSolution<Integer>> population, double DErate, int[] select) {

        PermutationSolution<Integer> childtemp = (PermutationSolution<Integer>) population.get(select[1]).copy();   //较差的粒子

        ArrayList<SO> listtemp = getDifferenceOfJobSequenceVectorByExchangeSequence(population.get(select[0]), population.get(select[1]));   // 得到的交换序
        // ArrayList<SO> listtemp1 = minus1(population.get(select[0]), population.get(select[1]));   // 得到的交换序  zj


        ArrayList<SO> listVa = new ArrayList<>(); //zj
        ArrayList<ST> listVb = new ArrayList<>();

        Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        double random1 = A.nextDouble();
        ArrayList<SO> listall = new ArrayList<SO>((int) (listtemp.size() * random1 * DErate));
        //ArrayList<SO> listall1 = new ArrayList<SO> ((int)(listtemp.size()*random1*DErate));  //ZJ

        for (int j = 0; j < listtemp.size() * random1 * DErate; j++) {
            listall.add(listtemp.get(j));
        }
*//*            for(int j=0;j<listtemp1.size()*random1*DErate;j++){
                listall1.add(listtemp1.get(j));   //zj
            }*//*

        alter(childtemp, listall);    // 交换序交换值
        //alter1(childtemp,listall1);    // 交换序交换值
        return childtemp;  // 返回新的交换过后的序列  粒子

    }*/

        private void alter (PermutationSolution < Integer > arr, ArrayList < SO > list){           //交换序

            SO s;
// 几对交换序  就交换几次
            for (int i = 0; i < list.size(); i++) {
                s = list.get(i);
                exchangeIndex4JobSequenceVectorByExchangeSequence(arr, s.getX(), s.getY());   // 交换值
            }

        }


        private void alter1 (PermutationSolution < Integer > arr, ArrayList < SO > list){           //交换序  zj

            SO s;
// 几对交换序  就交换几次
            for (int i = 0; i < list.size(); i++) {
                s = list.get(i);
                exchangeIndex4FactoryVectorByExchangeSequence(arr, s.getX(), s.getY());   // 交换值
            }

        }


        //随机选择
        private <S extends Solution<?>>int[] DEselect (List < PermutationSolution < Integer >> swarm) {

            Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();

            int ran1 = 0;
            int ran2 = 0;

            ran1 = r.nextInt(swarm.size() - 1);

            int[] temp = new int[2];

            while (swarm.size() > 1 && (ran2 = r.nextInt(swarm.size() - 1)) != ran1) {

                if (swarm.get(ran1).getObjective(0) < swarm.get(ran2).getObjective(0) ||
                        swarm.get(ran1).getObjective(1) < swarm.get(ran2).getObjective(1)) {
                    temp[0] = ran1;
                    temp[1] = ran2;
                    break;
                } else {
                    temp[0] = ran2;
                    temp[1] = ran1;
                    break;
                }     // 为了DE操作做准备       [0]比[1]好
            }

            return temp;

        }

    protected List<PermutationSolution<Integer>> PDDRFF(List<PermutationSolution<Integer>> swarm,
                                                        List<PermutationSolution<Integer>> swarm2) {

        List<PermutationSolution<Integer>> swarmtemp = new ArrayList<>(swarmSize);

        int newswarmSize = swarm.size() + swarm2.size();        // 分群后的原始种群 M(t) + DE后的种群M’(t)
        List<PermutationSolution<Integer>> temp2 = new ArrayList<>(newswarmSize);     //两倍
        ArrayList<List<PermutationSolution<Integer>>> tempPd2 = new ArrayList<List<PermutationSolution<Integer>>>(newswarmSize);    //两倍

        for (int i = 0; i < swarm.size(); i++) {
            temp2.add((PermutationSolution<Integer>) swarm.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(tempSwarm.get(i).size());

            for (int j = 0; j < tempSwarm.get(i).size(); j++) {

                A.add((PermutationSolution<Integer>) tempSwarm.get(i).get(j).copy());

            }
            tempPd2.add(A);
        }

        for (int i = 0; i < swarm2.size(); i++) {
            temp2.add((PermutationSolution<Integer>) swarm2.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(tempSwarm.get(i).size());    //例:DEswarmtempPdflag[i]是3号粒子的下标3   //tempSwarm.get(DEswarmtempPdflag[i].size()是原种群3号粒子的历史个体的大小

            for (int j = 0; j < tempSwarm.get(i).size(); j++) {

                A.add((PermutationSolution<Integer>) tempSwarm.get(i).get(j).copy());

            }
            tempPd2.add(A);           //存随机选出的不好的粒子的历史状况   //这些粒子DE后 可能得到些改善
        }

        List<Double> aa = new ArrayList<>(newswarmSize);    // 原始种群个数的两倍
        for (int i = 0; i < newswarmSize; i++) {       //原始种群个数的两倍
            double count1 = 0;
            double count2 = 0;
            for (int j = 0; j < newswarmSize; j++) {
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

        for (int i = 0; i < swarm.size(); i++) {     //原始种群的数量
            int b = 0;
            for (int j = 1; j < aa.size(); j++) {
                if (aa.get(j) < aa.get(b)) {
                    b = j;
                }
            }
            swarmtemp.add(temp2.get(b));
            tempSwarm.add(tempPd2.get(b));

            aa.remove(b);
            tempPd2.remove(b);
            temp2.remove(b);
        }
        //swarm = swarmtemp;   //新加
        return swarm;   //  原始种群的个数
    }
        protected List<PermutationSolution<Integer>> PDDRFFselect (List < PermutationSolution < Integer >> swarm1,
                List < PermutationSolution < Integer >> swarm2,int[] DEswarmtempPdflag){
            //protected List<PermutationSolution<Integer>> PDDRFFselect(List<PermutationSolution<Integer>> swarm1,List<PermutationSolution<Integer>> swarm2) {

            List<PermutationSolution<Integer>> swarmtemp = new ArrayList<>(swarm1.size());

            int swarmSize = swarm1.size() + swarm2.size();        // 分群后的原始种群 M(t) + DE后的种群M’(t)
            List<PermutationSolution<Integer>> temp2 = new ArrayList<>(swarmSize);
            ArrayList<List<PermutationSolution<Integer>>> tempPd2 = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);
            ArrayList<List<int[]>> tempPd2flag = new ArrayList<List<int[]>>();

            for (int i = 0; i < swarm1.size(); i++) {
                temp2.add((PermutationSolution<Integer>) swarm1.get(i).copy());

                ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(tempSwarm.get(i).size());
                ArrayList<int[]> B = new ArrayList<int[]>();

                for (int j = 0; j < tempSwarm.get(i).size(); j++) {

                    A.add((PermutationSolution<Integer>) tempSwarm.get(i).get(j).copy());

                    int b[] = new int[2];
                    b[0] = Pdflag.get(i).get(j)[0];
                    b[1] = Pdflag.get(i).get(j)[1];
                    B.add(b);

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

                    int b[] = new int[2];
                    b[0] = Pdflag.get(DEswarmtempPdflag[i]).get(j)[0];
                    b[1] = Pdflag.get(DEswarmtempPdflag[i]).get(j)[1];
                    B.add(b);

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
            Pdflag.clear();

            for (int i = 0; i < swarm1.size(); i++) {
                int b = 0;
                for (int j = 1; j < aa.size(); j++) {
                    if (aa.get(j) < aa.get(b)) {
                        b = j;
                    }
                }
                swarmtemp.add(temp2.get(b));
                tempSwarm.add(tempPd2.get(b));
                Pdflag.add(tempPd2flag.get(b));

                aa.remove(b);
                tempPd2.remove(b);
                temp2.remove(b);
                tempPd2flag.remove(b);
            }
            //swarm = swarmtemp;   //新加
            return swarmtemp;   //  原始种群的个数
        }

        protected List<PermutationSolution<Integer>> mager
        (List < PermutationSolution < Integer >> swarm1, List < PermutationSolution < Integer >> swarm2){
            List<PermutationSolution<Integer>> temp = new ArrayList<PermutationSolution<Integer>>();

            for (int i = 0; i < swarm1.size(); i++) {
                temp.add(swarm1.get(i));
            }

            for (int i = 0; i < swarm2.size(); i++) {
                temp.add(swarm2.get(i));
            }

            return temp;

        }

    private void mergeNew (List < PermutationSolution < Integer >> swarm) {
        //swarm.clear();
        tempSwarm.clear();
        Pdflag.clear();

        for (int i = 0; i < upSize; i++) {
            //swarm.add((PermutationSolution<Integer>) sub1.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(Pd1.get(i).size());
            ArrayList<int[]> B = new ArrayList<int[]>(Pd1.get(i).size());

            for (int j = 0; j < Pd1.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) Pd1.get(i).get(j).copy());
                int[] b = new int[2];
                b[0] = Pd1flag.get(i).get(j)[0];
                b[1] = Pd1flag.get(i).get(j)[1];
                B.add(b);
            }

            tempSwarm.add(A);
            Pdflag.add(B);
        }


        for (int i = 0; i < centralSize; i++) {
            //swarm.add((PermutationSolution<Integer>) sub2.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(Pd2.get(i).size());
            ArrayList<int[]> B = new ArrayList<int[]>(Pd2.get(i).size());

            for (int j = 0; j < Pd2.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) Pd2.get(i).get(j).copy());
                int[] b = new int[2];
                b[0] = Pd2flag.get(i).get(j)[0];
                b[1] = Pd2flag.get(i).get(j)[1];
                B.add(b);
            }
            tempSwarm.add(A);
            Pdflag.add(B);
        }

        for (int i = 0; i < downSize; i++) {
            //swarm.add((PermutationSolution<Integer>) sub3.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(Pd3.get(i).size());
            ArrayList<int[]> B = new ArrayList<int[]>(Pd3.get(i).size());
            for (int j = 0; j < Pd3.get(i).size(); j++) {
                A.add((PermutationSolution<Integer>) Pd3.get(i).get(j).copy());
                int[] b = new int[2];
                b[0] = Pd3flag.get(i).get(j)[0];
                b[1] = Pd3flag.get(i).get(j)[1];
                B.add(b);
            }
            tempSwarm.add(A);
            Pdflag.add(B);
        }

    }


        //整合
        private void merge (List < PermutationSolution < Integer >> swarm) {
            swarm.clear();
            tempSwarm.clear();
            Pdflag.clear();

            for (int i = 0; i < upSize; i++) {
                swarm.add((PermutationSolution<Integer>) sub1.get(i).copy());

                ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(Pd1.get(i).size());
                ArrayList<int[]> B = new ArrayList<int[]>(Pd1.get(i).size());

                for (int j = 0; j < Pd1.get(i).size(); j++) {
                    A.add((PermutationSolution<Integer>) Pd1.get(i).get(j).copy());
                    int[] b = new int[2];
                    b[0] = Pd1flag.get(i).get(j)[0];
                    b[1] = Pd1flag.get(i).get(j)[1];
                    B.add(b);
                }

                tempSwarm.add(A);
                Pdflag.add(B);
            }


            for (int i = 0; i < centralSize; i++) {
                swarm.add((PermutationSolution<Integer>) sub2.get(i).copy());

                ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(Pd2.get(i).size());
                ArrayList<int[]> B = new ArrayList<int[]>(Pd2.get(i).size());

                for (int j = 0; j < Pd2.get(i).size(); j++) {
                    A.add((PermutationSolution<Integer>) Pd2.get(i).get(j).copy());
                    int[] b = new int[2];
                    b[0] = Pd2flag.get(i).get(j)[0];
                    b[1] = Pd2flag.get(i).get(j)[1];
                    B.add(b);
                }
                tempSwarm.add(A);
                Pdflag.add(B);
            }

            for (int i = 0; i < downSize; i++) {
                swarm.add((PermutationSolution<Integer>) sub3.get(i).copy());

                ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(Pd3.get(i).size());
                ArrayList<int[]> B = new ArrayList<int[]>(Pd3.get(i).size());
                for (int j = 0; j < Pd3.get(i).size(); j++) {
                    A.add((PermutationSolution<Integer>) Pd3.get(i).get(j).copy());
                    int[] b = new int[2];
                    b[0] = Pd3flag.get(i).get(j)[0];
                    b[1] = Pd3flag.get(i).get(j)[1];
                    B.add(b);
                }
                tempSwarm.add(A);
                Pdflag.add(B);
            }

        }

        /**
         * 针对工序向量做交换序的差异
         * @param a
         * @param b
         * @return
         */
        private ArrayList<SO> getDifferenceOfJobSequenceVectorByExchangeSequence
        (PermutationSolution < Integer > a, PermutationSolution < Integer > b){     //  做差 得到交换序
            PermutationSolution<Integer> tempb = (PermutationSolution<Integer>) b.copy();

            int index;
            // 交换子
            SO s;
            // 交换序列
            ArrayList<SO> list = new ArrayList<SO>();
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int boundflag = random.nextInt(b.getNumberOfVariables());          //  随机产生交换序的第一个下标

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

    private PermutationSolution<Integer> getDifferenceOfJobSequenceVector
            (PermutationSolution < Integer > a, PermutationSolution < Integer > b,Double r){
            //  做差 得到交换序
        PermutationSolution<Integer> tempb = (PermutationSolution<Integer>) b.copy();

        //List<Integer> temp = new ArrayList<>(a.getNumberOfVariables());
        for(int i=0;i<a.getNumberOfVariables();i++){
            tempb.setVariableValue(i, (int) (r*(a.getVariableValue(i)-b.getVariableValue(i))));
        }

        return tempb;
    }

        private void getCrossOfFactoryVectorBySingle
        (PermutationSolution < Integer > a, PermutationSolution < Integer > b){       //对工厂向量进行单点交叉
            int index;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            int boundflag = random.nextInt(b.getNumberOfVariablesid());          //  随机产生一个单点下标
            for (int i = boundflag; i < b.getNumberOfVariablesid(); i++) {
                index = i;
                cross4FactoryVectorBySingle(a, b, i, index);   //交换下标i与下标index的值
            }
        }

        private void cross4FactoryVectorBySingle (PermutationSolution < Integer > a, PermutationSolution < Integer > b,
        int index1, int index2){     //交换值
            int temp1 = a.getVariableValueid(index1);    //工厂
            int temp2 = b.getVariableValueid(index2);

            a.setVariableValueid(index1, temp2);
            b.setVariableValueid(index2, temp1);
        }


        private ArrayList<SO> getDifferenceOfFactoryVectorByExchangeSequence
        (PermutationSolution < Integer > a, PermutationSolution < Integer > b){    //TODO 为什么针对工厂向量计算交换序？

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


        private int findSameIndexFromJobSequence (PermutationSolution < Integer > a,int num){
            int index = -1;
            for (int i = 0; i < a.getNumberOfVariables(); i++) {
                if (a.getVariableValue(i) == num) {
                    index = i;
                    break;
                }
            }
            return index;
        }


        private int findSameIndexFromFactoryVector (PermutationSolution < Integer > a,int num){
            int index = -1;
            for (int i = 0; i < a.getNumberOfVariablesid(); i++) {
                if (a.getVariableValueid(i) == num) {
                    index = i;
                    break;
                }
            }
            return index;
        }


        private void exchangeIndex4JobSequenceVectorByExchangeSequence (PermutationSolution < Integer > a,int index1,
        int index2){     //交换值
            int temp1 = a.getVariableValue(index1);   //工件
            int temp2 = a.getVariableValue(index2);

            a.setVariableValue(index1, temp2);
            a.setVariableValue(index2, temp1);

        }

        //zj
        private void exchangeIndex4FactoryVectorByExchangeSequence (PermutationSolution < Integer > a,int index1,
        int index2){     //交换值
            int temp1 = a.getVariableValueid(index1);    //工厂
            int temp2 = a.getVariableValueid(index2);

            a.setVariableValueid(index1, temp2);
            a.setVariableValueid(index2, temp1);
        }

        private void exchangeIndex4FactoryVectorByRandom (PermutationSolution < Integer > a,int index1, int value)
        {     //交换值
            //int temp1 =  a.getVariableValueid(index1);
            a.setVariableValueid(index1, value);
        }

    private PermutationSolution < Integer > addNew4JobSequenceVector
            (PermutationSolution < Integer > arr){

        PermutationSolution<Integer> temp = (PermutationSolution<Integer>) arr.copy();
  /*      Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int ran1 = 0; int ran2=0;
        ran1 = r.nextInt();  ran2 = r.nextInt();
        arr.getVariableValue(ran1);
        arr.getVariableValue(ran2);
        temp.setVariableValue(ran1, arr.getVariableValue(ran2));
        temp.setVariableValue(ran2, arr.getVariableValue(ran1));*/
  for(int i=0;i<arr.getNumberOfVariables();i++){

      arr.setVariableValue(i,arr.getVariableValue(i)+6);
  }
        return arr;
    }

        private void addNew4JobSequenceVectorByExchangeSequence
        (PermutationSolution < Integer > arr, ArrayList < SO > list){
            SO s;

            for (int i = 0; i < list.size(); i++) {
                s = list.get(i);
                exchangeIndex4JobSequenceVectorByExchangeSequence(arr, s.getX(), s.getY());             //      根据下标交换值
            }
        }

        //zj
        private void addNew4FactoryVectorByExchangeSequence (PermutationSolution < Integer > arr, ArrayList < SO > list)
        {
            SO s;
            for (int i = 0; i < list.size(); i++) {
                s = list.get(i);
                exchangeIndex4FactoryVectorByExchangeSequence(arr, s.getX(), s.getY());             //      根据下标交换值
            }
        }

        private void addNew4FactoryVectorByRandom (PermutationSolution < Integer > arr, ArrayList < ST > list){
            ST s;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            for (int i = 0; i < list.size(); i++) {
                s = list.get(i);
                int r = random.nextInt(3); //TODO 为什么写成了3? 难道是因为3个工厂吗？
                //工厂序号分别是 0，1，2 所以生成0-3但不包括3的随机整数来进行突变
                exchangeIndex4FactoryVectorByRandom(arr, s.getX(), r);             //   随机选一位数进行改变
            }
        }


        @Override  //更新个体历史最优
        protected void updateLeaders (List < PermutationSolution < Integer >> swarm) {

            //System.out.println(swarm.size());
            //添加
            for (int j = 0; j < swarm.size(); j++) {
                tempSwarm.get(j).add((PermutationSolution<Integer>) swarm.get(j).copy());

                int b[] = new int[2];
                b[0] = b[1] = 0;
                Pdflag.get(j).add(b);
            }

            //去重     只留一个个体历史最优
            for (int i = 0; i < swarm.size(); i++) {
                for (int j = 0; j < tempSwarm.get(i).size(); j++) {
                    for (int k = j + 1; k < tempSwarm.get(i).size(); k++) {
                        if (tempSwarm.get(i).get(j).getObjective(0) <= tempSwarm.get(i).get(k).getObjective(0) &&
                                tempSwarm.get(i).get(j).getObjective(1) <= tempSwarm.get(i).get(k).getObjective(1)) {
                            tempSwarm.get(i).remove(k);
                            Pdflag.get(i).remove(k);
                            k--;
                        }
                    }
                    for (int k = j + 1; k < tempSwarm.get(i).size(); k++) {
                        if (tempSwarm.get(i).get(j).getObjective(0) >= tempSwarm.get(i).get(k).getObjective(0) &&
                                tempSwarm.get(i).get(j).getObjective(1) >= tempSwarm.get(i).get(k).getObjective(1)) {
                            tempSwarm.get(i).remove(j);
                            Pdflag.get(i).remove(j);
                            j--;
                            break;
                        }
                    }
                }
            }


        }

        @Override  //更新全局最优
        protected void updateParticlesMemory (List < PermutationSolution < Integer >> swarm) {

            //添加
            for (int k = 0; k < swarm.size(); k++) {
                globallyOptimalIndividual.add((PermutationSolution<Integer>) tempSwarm.get(k).get(tempSwarm.get(k).size() - 1).copy());

                int b[] = new int[2];
                b[0] = b[1] = 0;
                // Pgdflag.add(b);
            }

            //去重
            for (int i = 0; i < globallyOptimalIndividual.size(); i++) {
                for (int j = i + 1; j < globallyOptimalIndividual.size(); j++) {
                    if (globallyOptimalIndividual.get(i).getObjective(0) <= globallyOptimalIndividual.get(j).getObjective(0) &&
                            globallyOptimalIndividual.get(i).getObjective(1) <= globallyOptimalIndividual.get(j).getObjective(1)) {
                        globallyOptimalIndividual.remove(j);
                        //Pgdflag.remove(j);
                        j--;
                    }
                }
                for (int j = i + 1; j < globallyOptimalIndividual.size(); j++) {
                    if (globallyOptimalIndividual.get(i).getObjective(0) >= globallyOptimalIndividual.get(j).getObjective(0) &&
                            globallyOptimalIndividual.get(i).getObjective(1) >= globallyOptimalIndividual.get(j).getObjective(1)) {
                        globallyOptimalIndividual.remove(i);
                        //Pgdflag.remove(i);
                        i--;
                        break;
                    }
                }
            }
        }

        @Override
        public List<PermutationSolution<Integer>> getResult () {
            return globallyOptimalIndividual;
        }

        @Override
        public String getName () {
            return "MOPSODivideSubgroup";
        }

        @Override
        public String getDescription () {
            return "Optimized MOPSODivideSubgroup";
        }


        private void job (PermutationSolution < Integer > bb1, PermutationSolution < Integer > particle,
        double r, ArrayList<SO > list){    //只动工件向量

            ArrayList<SO> vtemp1 = getDifferenceOfJobSequenceVectorByExchangeSequence(bb1, particle);
            int len = (int) (vtemp1.size() * r);

            for (int j = 0; j < len; j++) {
                list.add(vtemp1.get(j));
            }
            addNew4JobSequenceVectorByExchangeSequence(particle, list);
        }

        private void fac (PermutationSolution < Integer > bb1, PermutationSolution < Integer > particle,
        double r, ArrayList<SO > list){     //只动工厂向量   交叉

            ArrayList<SO> vtempa = getDifferenceOfFactoryVectorByExchangeSequence(bb1, particle);
            int len1 = 1;
            for (int j = 0; j < len1; j++) {
                list.add(vtempa.get(j));
            }
            addNew4FactoryVectorByExchangeSequence(particle, list);
        }

        private void fac1 (PermutationSolution < Integer > particle, ArrayList < ST > list){             //突变
            ST q = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
            list.add(q);
            addNew4FactoryVectorByRandom(particle, list);
        }


        private PermutationSolution<Integer> DEJobFactory (List < PermutationSolution < Integer >> population,
        double DErate, int[] select){    //工件工厂向量都操作
            PermutationSolution<Integer> childtemp = (PermutationSolution<Integer>) population.get(select[1]).copy();   //较差的粒子
            ArrayList<SO> listtemp = getDifferenceOfJobSequenceVectorByExchangeSequence(population.get(select[0]), population.get(select[1]));   // 得到的交换序
            Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            double random1 = A.nextDouble();
            ArrayList<SO> listall = new ArrayList<SO>((int) (listtemp.size() * random1 * DErate));

            for (int j = 0; j < listtemp.size() * random1 * DErate; j++) {
                listall.add(listtemp.get(j));
            }
            alter(childtemp, listall);    // 交换序交换

            //ArrayList<SO> listtemp1 = getDifferenceOfFactoryVectorByExchangeSequence(population.get(select[0]), population.get(select[1]));   // 得到的交换序  zj
            double c, m;
            c = A.nextDouble();
            m = A.nextDouble();
            if (c < DEcrossoverRates) {
          /*  ArrayList<SO> listall1 = new ArrayList<SO>((int) (listtemp1.size() * random1 * DErate));  //ZJ

            for (int j = 0; j < listtemp1.size() * random1 * DErate; j++) {
                listall1.add(listtemp1.get(j));
            }
            alter1(childtemp, listall1);    // 交换序交换值*/
                getCrossOfFactoryVectorBySingle(population.get(select[0]), childtemp);    //单点交叉
            }
            if (m < DEmutationRate) {
                ArrayList<ST> list = new ArrayList<>();
                //PermutationSolution<Integer> childtemp = (PermutationSolution<Integer>) population.get(select[1]).copy();   //较差的粒子
                ST q = new ST(randomGenerator.nextInt(0, childtemp.getNumberOfVariables() - 1));
                list.add(q);
                addNew4FactoryVectorByRandom(childtemp, list);
            }

            return childtemp;  // 返回新的交换过后的序列  粒子
        }

        private PermutationSolution<Integer> DE2 (List < PermutationSolution < Integer >> population,double DErate,
        int[] select){    //只动工件向量
            PermutationSolution<Integer> childtemp = (PermutationSolution<Integer>) population.get(select[1]).copy();   //较差的粒子

            ArrayList<SO> listtemp1 = getDifferenceOfFactoryVectorByExchangeSequence(population.get(select[0]), population.get(select[1]));   // 得到的交换序  zj

            Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            double random1 = A.nextDouble();
            double t;
            t = A.nextDouble();
            //ArrayList<SO> listall1 = new ArrayList<SO>((int) (listtemp1.size() ));
            if (t <= 0.5) {
                ArrayList<SO> listall1 = new ArrayList<SO>((int) (listtemp1.size() * random1 * DErate));  //ZJ

                for (int j = 0; j < listtemp1.size() * random1 * DErate; j++) {
                    listall1.add(listtemp1.get(j));
                }
                alter1(childtemp, listall1);    // 交换序交换值
            } else {
                ArrayList<ST> list = new ArrayList<>();
                //PermutationSolution<Integer> childtemp = (PermutationSolution<Integer>) population.get(select[1]).copy();   //较差的粒子
                ST q = new ST(randomGenerator.nextInt(0, childtemp.getNumberOfVariables() - 1));
                list.add(q);
                addNew4FactoryVectorByRandom(childtemp, list);
            }
            return childtemp;  // 返回新的交换过后的序列
        }

        private PermutationSolution<Integer> DE2t (List < PermutationSolution < Integer >> population,int[] select)
        {    //只动工件向量
            ArrayList<ST> list = new ArrayList<>();
            PermutationSolution<Integer> childtemp = (PermutationSolution<Integer>) population.get(select[1]).copy();   //较差的粒子
            ST q = new ST(randomGenerator.nextInt(0, childtemp.getNumberOfVariables() - 1));
            list.add(q);
            addNew4FactoryVectorByRandom(childtemp, list);
            return childtemp;

        }
        /*protected List<PermutationSolution<Integer>> PDDRFF(List<PermutationSolution<Integer>> swarm,
                                                        List<PermutationSolution<Integer>> swarm2) {

        List<PermutationSolution<Integer>> swarmtemp = new ArrayList<>(swarmSize);

        int newswarmSize = swarm.size() + swarm2.size();        // 分群后的原始种群 M(t) + DE后的种群M’(t)
        List<PermutationSolution<Integer>> temp2 = new ArrayList<>(newswarmSize);     //两倍
        ArrayList<List<PermutationSolution<Integer>>> tempPd2 = new ArrayList<List<PermutationSolution<Integer>>>(newswarmSize);    //两倍

        for (int i = 0; i < swarm.size(); i++) {
            temp2.add((PermutationSolution<Integer>) swarm.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(tempSwarm.get(i).size());

            for (int j = 0; j < tempSwarm.get(i).size(); j++) {

                A.add((PermutationSolution<Integer>) tempSwarm.get(i).get(j).copy());

            }
            tempPd2.add(A);
        }

        for (int i = 0; i < swarm2.size(); i++) {
            temp2.add((PermutationSolution<Integer>) swarm2.get(i).copy());

            ArrayList<PermutationSolution<Integer>> A = new ArrayList<>(tempSwarm.get(i).size());    //例:DEswarmtempPdflag[i]是3号粒子的下标3   //tempSwarm.get(DEswarmtempPdflag[i].size()是原种群3号粒子的历史个体的大小

            for (int j = 0; j < tempSwarm.get(i).size(); j++) {

                A.add((PermutationSolution<Integer>) tempSwarm.get(i).get(j).copy());

            }
            tempPd2.add(A);           //存随机选出的不好的粒子的历史状况   //这些粒子DE后 可能得到些改善
        }

        List<Double> aa = new ArrayList<>(newswarmSize);    // 原始种群个数的两倍
        for (int i = 0; i < newswarmSize; i++) {       //原始种群个数的两倍
            double count1 = 0;
            double count2 = 0;
            for (int j = 0; j < newswarmSize; j++) {
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

        for (int i = 0; i < swarm.size(); i++) {     //原始种群的数量
            int b = 0;
            for (int j = 1; j < aa.size(); j++) {
                if (aa.get(j) < aa.get(b)) {
                    b = j;
                }
            }
            swarmtemp.add(temp2.get(b));
            tempSwarm.add(tempPd2.get(b));

            aa.remove(b);
            tempPd2.remove(b);
            temp2.remove(b);
        }
        swarm = swarmtemp;   //新加
        return swarm;   //  原始种群的个数
    }*/
//更新粒子位置
  /*       @Override
       protected void updatePosition(List<PermutationSolution<Integer>> swarm)  {

            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            double r1, r2;
            for (int i = 0; i < upSize; i++) {

                ArrayList<SO> listV = new ArrayList<>();
                ArrayList<SO> listVa = new ArrayList<>(); //zj
                ArrayList<ST> listV2 = new ArrayList<>();

                int len = 0;
                //int len1 = 0;
                PermutationSolution<Integer> particle = (PermutationSolution<Integer>) sub1.get(i).copy();   //一维

                //Parameters for velocity equation
                r1 = random.nextDouble()*Rand_k;
                r2 = random.nextDouble()*Rand_k;  //生成一个0~Rand_k的数


                //自身初速度
                SO s1 = new SO(randomGenerator.nextInt(0,particle.getNumberOfVariables()-1),
                        randomGenerator.nextInt(0,particle.getNumberOfVariables()-1));
                listV.add(s1);
                add(particle,listV);

//历史最优
                listV.clear();

                listVa.clear();     //用于工厂交叉
                listV2.clear();      //用于工厂突变


                ArrayList<SO> vtemp1 = minus(bb1.get(i), particle);
                len = (int) (vtemp1.size() * r1);

                for(int j=0;j<len;j++){
                    listV.add(vtemp1.get(j));
                }
                add(particle,listV);

                //全局最优
                listV.clear();
                listVa.clear();
                listV2.clear();

                ArrayList<SO> vtemp2 = minus(bb4.get(0), particle);
                len = (int) (vtemp2.size() * r2);

                for(int j=0;j<len;j++){
                    listV.add(vtemp2.get(j));
                }
                add(particle,listV);
                sub1.set(i, particle);
            }

            for (int i = 0; i < centralSize; i++) {

                ArrayList<SO> listV = new ArrayList<>();
                ArrayList<SO> listVa = new ArrayList<>(); //zj
                ArrayList<ST> listV2 = new ArrayList<>();
                int len = 0;int len1 = 0;
                PermutationSolution<Integer> particle = (PermutationSolution<Integer>) sub2.get(i).copy();

                //Parameters for velocity equation
                r1 = random.nextDouble()*Rand_k;
                r2 = random.nextDouble()*Rand_k;

                //自身初速度
                SO s1 = new SO(randomGenerator.nextInt(0,particle.getNumberOfVariables()-1),
                        randomGenerator.nextInt(0,particle.getNumberOfVariables()-1));

                listV.add(s1);
                add(particle,listV);

                //历史最优
                listV.clear();
                listVa.clear();
                listV2.clear();
                ArrayList<SO> vtemp1 = minus(bb2.get(i), particle);
                len = (int) (vtemp1.size() * r1);

                for(int j=0;j<len;j++){
                    listV.add(vtemp1.get(j));
                }

                add(particle,listV);

                //全局最优
                listV.clear();
                listVa.clear();
                listV2.clear();

                ArrayList<SO> vtemp2 = minus(bb4.get(1), particle);
                len = (int) (vtemp2.size() * r2);

                for(int j=0;j<len;j++){
                    listV.add(vtemp2.get(j));
                }
                add(particle,listV);
                sub2.set(i, particle);
            }

            for (int i = 0; i < downSize; i++) {

                ArrayList<SO> listV = new ArrayList<>();
                ArrayList<SO> listVa = new ArrayList<>(); //zj
                ArrayList<ST> listV2 = new ArrayList<>();
                int len = 0; int len1 = 0;
                PermutationSolution<Integer> particle = (PermutationSolution<Integer>) sub3.get(i).copy();

                //Parameters for velocity equation
                r1 = random.nextDouble()*Rand_k;
                r2 = random.nextDouble()*Rand_k;
                //自身初速度
                SO s1 = new SO(randomGenerator.nextInt(0,particle.getNumberOfVariables()-1),
                        randomGenerator.nextInt(0,particle.getNumberOfVariables()-1));

                listV.add(s1);
                add(particle,listV);

                //历史最优
                listV.clear();
                listVa.clear();
                listV2.clear();

                ArrayList<SO> vtemp1 = minus(bb3.get(i), particle);
                len = (int) (vtemp1.size() * r1);
                for(int j=0;j<len;j++){
                    listV.add(vtemp1.get(j));
                }
                add(particle,listV);

                //全局最优
                listV.clear();
                listVa.clear();
                listV2.clear();

                ArrayList<SO> vtemp2 = minus(bb4.get(2), particle);
                len = (int) (vtemp2.size() * r2);

                for(int j=0;j<len;j++){
                    listV.add(vtemp2.get(j));
                }
                add(particle,listV);

                sub3.set(i, particle);
            }

            zhenghe(swarm);
        }


        //加DE操作
        @Override
        protected void perturbation(List<PermutationSolution<Integer>> swarm) {


            //在分群后加DE操作
            swarm =evaluateSwarm(swarm);
            //super.setSwarm(evaluateSwarm(swarm));
            List<PermutationSolution<Integer>> swarmtemp = new ArrayList<PermutationSolution<Integer>>(swarm.size());

            int[] DEswarmtempPdflag = new int[swarmSize];
            double o,t;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            for(int i=0;i<swarm.size();i++){
                int[] select =DEselect(swarm);                 // 随机选择   【0】【1】

                swarmtemp.add(DEexe(swarm,DErate,select));
                //swarmtemp.add(DEexe(swarm,DErate,select));              // 交换序
                DEswarmtempPdflag[i] = select[1];   //
            }

            swarmtemp = evaluateSwarm(swarmtemp);     //DE操作后的种群
            swarm = PDDRFFselect(swarm,swarmtemp,DEswarmtempPdflag);
            //super.setSwarm(PDDRFFselect(swarm,swarmtemp,DEswarmtempPdflag));//第一个参数是swarm种群，第二个是DE得到的种群
        }*/
    }

