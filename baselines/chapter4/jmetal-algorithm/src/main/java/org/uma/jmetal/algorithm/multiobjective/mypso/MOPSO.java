package org.uma.jmetal.algorithm.multiobjective.mypso;

import org.uma.jmetal.algorithm.impl.AbstractParticleSwarmOptimization;
import org.uma.jmetal.algorithm.multiobjective.mypso.util.ST;
import org.uma.jmetal.differentialevolution.util.SO;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.problem.multiobjective.dfsp.DHFSP;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;


/** Class implementing the OMOPSO algorithm */

@SuppressWarnings("serial")
public class MOPSO extends AbstractParticleSwarmOptimization<PermutationSolution<Integer>, List<PermutationSolution<Integer>>> {
    private Problem<PermutationSolution<Integer>> problem;
    private final SolutionListEvaluator<PermutationSolution<Integer>> evaluator;

    private int swarmSize;
    private int archiveSize;
    private int maxIterations;
    //   private int currentIteration;

    //   private ArrayList<ArrayList<ArrayList<PermutationSolution<Integer>>>> Pd;
    //   private ArrayList<ArrayList<PermutationSolution<Integer>>> Pgd;

    private ArrayList<List<PermutationSolution<Integer>>> Pd ;
    private List<PermutationSolution<Integer>> Pgd ;
    private double Rand_k;
    private double Cross_c;
    private double Mutation_m;

    private double CrossoverRates4worker;
    private double CrossoverRates4machine;
    private double mutationRate4worker;
    private double mutationRate4machine;

    //   private ArrayList<ArrayList<double[]>> vPd;
    //   private ArrayList<double[]> vPgd;

    //  private NonDominatedSolutionListArchive<PermutationSolution<Integer>> epsilonArchive;

    private int currentIteration;
    //    private double eta = 0.0075;
    private JMetalRandom randomGenerator;

    /** Constructor */
    public MOPSO(double crossoverRate, double mutationRate, double rand_k,Problem<PermutationSolution<Integer>> problem, SolutionListEvaluator<PermutationSolution<Integer>> evaluator,
                 int swarmSize, int maxIterations, int archiveSize  ,double CrossoverRates4worker,double CrossoverRates4machine,double mutationRate4worker,double mutationRate4machine) {
        this.problem = problem ;
        this.evaluator = evaluator ;

        this.swarmSize = swarmSize ;
        this.maxIterations = maxIterations ;
        this.archiveSize = archiveSize ;

        this.Rand_k = rand_k;
        this.Mutation_m = mutationRate;
        this.Cross_c = crossoverRate;

        this.CrossoverRates4worker=CrossoverRates4worker;
        this.CrossoverRates4machine=CrossoverRates4machine;
        this.mutationRate4worker=mutationRate4worker;
        this.mutationRate4machine=mutationRate4machine ;

        Pd = new ArrayList<List<PermutationSolution<Integer>>>(swarmSize);
        Pgd = new ArrayList<PermutationSolution<Integer>>();
        //    vPd = new ArrayList<ArrayList<double[]>>();
        //    vPgd = new ArrayList<double[]>();

        //     epsilonArchive = new NonDominatedSolutionListArchive<PermutationSolution<Integer>>(new DominanceComparator<PermutationSolution<Integer>>(eta));
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
            swarm.add(newSolution);
        }

        return swarm;
    }

    @Override
    protected List<PermutationSolution<Integer>> evaluateSwarm(List<PermutationSolution<Integer>> swarm) {
        swarm = evaluator.evaluate(swarm, (Problem<PermutationSolution<Integer>>) problem);
        return swarm ;
    }

    @Override
    protected void initializeLeader(List<PermutationSolution<Integer>> swarm) {
        for(int i=0;i<swarmSize;i++) {
            Pgd.add((PermutationSolution<Integer>) swarm.get(i).copy());
        }
    }

    @Override
    protected void initializeParticlesMemory(List<PermutationSolution<Integer>> swarm)  {
        for (int i = 0; i < swarm.size(); i++) {
            ArrayList<PermutationSolution<Integer>> A = new ArrayList<PermutationSolution<Integer>>();
            A.add((PermutationSolution<Integer>) swarm.get(i).copy());
            Pd.add(A);
        }
    }

    @Override
    protected void initializeVelocity(List<PermutationSolution<Integer>> swarm) {

    }

    @Override
    protected void updatePosition(List<PermutationSolution<Integer>> swarm) {

    }

    @Override
    protected void perturbation(List<PermutationSolution<Integer>> swarm) {
    }

    @Override
    protected void updateVelocity(List<PermutationSolution<Integer>> swarm)  {
        double r1, r2;
        double c, m;
        int[] nw = DHFSP.nw;
        PermutationSolution<Integer> bestGlobal;

        for (int i = 0; i < swarmSize; i++) {
            //Random random = null;
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            ArrayList<SO> listV = new ArrayList<>();
            double ra = 0.0;
            int len = 0;
            PermutationSolution<Integer> particle = (PermutationSolution<Integer>) swarm.get(i).copy();
            PermutationSolution<Integer> bestParticle;

            int a = randomGenerator.nextInt(0,Pd.get(i).size()-1);
            int b = randomGenerator.nextInt(0,Pd.get(i).size()-1);
            bestParticle = Pd.get(i).get(b);

            if((a!=b)&&
                    (Pd.get(i).get(a).getObjective(0) <= Pd.get(i).get(b).getObjective(0)) &&
                    (Pd.get(i).get(a).getObjective(1)<=Pd.get(i).get(b).getObjective(1))&&
                    (Pd.get(i).get(a).getObjective(2)<=Pd.get(i).get(b).getObjective(2))){
                bestParticle= Pd.get(i).get(a);
            }

            a = randomGenerator.nextInt(0,Pgd.size()-1);
            b = randomGenerator.nextInt(0,Pgd.size()-1);
            bestGlobal = Pgd.get(b);

            if((a!=b)&&
                    (Pgd.get(a).getObjective(1)<=Pgd.get(b).getObjective(1)) &&
                    (Pgd.get(a).getObjective(0)<=Pgd.get(b).getObjective(0))&&
                    (Pgd.get(a).getObjective(2)<=Pgd.get(b).getObjective(2))){
                bestGlobal= Pgd.get(a);
            }

            //Parameters for velocity equation
            r1 = random.nextDouble() * Rand_k;
            r2 = random.nextDouble() * Rand_k;
            //

            //自身初速度
/*            SO s1 = new SO(randomGenerator.nextInt(0,particle.getNumberOfVariables()-1),
                    randomGenerator.nextInt(0,particle.getNumberOfVariables()-1));

            listV.add(s1);
            alter(particle,listV);*/

            //历史最优
            //listV.clear();
            ArrayList<SO> vtemp1 = getDifferenceOfJobSequenceVectorByExchangeSequence(bestParticle, particle);
            //ArrayList<SO> listVa = new ArrayList<>();
            ArrayList<ST> listV2 = new ArrayList<>();
            len = (int) (vtemp1.size() * r1);

            for(int j=0;j<len;j++){
                listV.add(vtemp1.get(j));
            }
            addNew4JobSequenceVectorByExchangeSequence(particle,listV);
            c = random.nextDouble();
            m = random.nextDouble();
            if (c < Cross_c) {
                /*ArrayList<SO> vtempa = getDifferenceOfFactoryVectorByExchangeSequence(bb1.get(i), particle); //针对工厂向量的差异
                len1 = (int) (vtempa.size() * r1);
                for (int j = 0; j < len1; j++) {
                    listVa.add(vtempa.get(j));
                }
                addNew4FactoryVectorByExchangeSequence(particle, listVa);*/
                getCrossOfFactoryVectorBySingle(bestParticle, particle);    //单点交叉

            }

            double c_worker = random.nextDouble();
            if (c_worker < CrossoverRates4worker) {
//                ArrayList<SO> vtempa = getDifferenceOfFactoryVectorByExchangeSequence(upGr1HisOptIndividual.get(i), particle); //针对工厂向量的差异
//                len1 = (int) (vtempa.size() * r1);
//                for (int j = 0; j < len1; j++) {
//                    listVa.add(vtempa.get(j));
//                }
//                addNew4FactoryVectorByExchangeSequence(particle, listVa);
//                exchange4WorkerSequence(particle);
                crossover4workersequence(bestParticle,particle,nw);//工人向量交叉

            }

            double c_machine = random.nextDouble();
            if (c_machine < CrossoverRates4machine) {
//                ArrayList<SO> vtempa = getDifferenceOfFactoryVectorByExchangeSequence(upGr1HisOptIndividual.get(i), particle); //针对工厂向量的差异
//                len1 = (int) (vtempa.size() * r1);
//                for (int j = 0; j < len1; j++) {
//                    listVa.add(vtempa.get(j));
//                }
//                addNew4FactoryVectorByExchangeSequence(particle, listVa);
//                exchange4WorkerSequence(particle);
                crossover4machinesequence(bestParticle,particle,nw);//工人向量交叉
            }

            if (m < Mutation_m) {
                //确定针对工厂向量
                ST q = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                listV2.add(q);
                addNew4FactoryVectorByRandom(particle, listV2);
            }

            double m_worker = random.nextDouble();
            if (m_worker < mutationRate4worker){
                mutation4worker(particle);
            }
            double m_machine = random.nextDouble();
            if (m_machine < mutationRate4machine) {
                mutation4machine(particle);
            }


            //全局最优
            listV.clear();
            ArrayList<SO> vtemp2 = getDifferenceOfJobSequenceVectorByExchangeSequence(bestGlobal, particle);
            len = (int) (vtemp2.size() * r2);

            for(int j=0;j<len;j++){
                listV.add(vtemp2.get(j));
            }
            addNew4JobSequenceVectorByExchangeSequence(particle,listV);

            c = random.nextDouble();
            m = random.nextDouble();
            if (c < Cross_c) {
                getCrossOfFactoryVectorBySingle(bestGlobal, particle);    //单点交叉

            }
            if (m < Mutation_m) {
                //确定针对工厂向量
                ST q = new ST(randomGenerator.nextInt(0, particle.getNumberOfVariables() - 1));
                listV2.add(q);
                addNew4FactoryVectorByRandom(particle, listV2);
            }
            swarm.set(i, particle);

        }
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

    private ArrayList<SO> minus1(PermutationSolution<Integer> a, PermutationSolution<Integer> b) {

        PermutationSolution<Integer> tempb = (PermutationSolution<Integer>) b.copy();

        int index;
        // 交换子
        SO s;
        // 交换序列
        ArrayList<SO> list = new ArrayList<SO>();
        for (int i = 0; i < b.getNumberOfVariables(); i++) {
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

    private void exchangeIndex4JobSequenceVectorByExchangeSequence(PermutationSolution<Integer> a, int index1, int index2) {
        int temp1 =  a.getVariableValue(index1);
        int temp2 =  a.getVariableValue(index2);

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

    @Override
    protected void updateLeaders(List<PermutationSolution<Integer>> swarm) {

        //添加
        for(int j=0;j<swarm.size();j++){
            Pd.get(j).add((PermutationSolution<Integer>) swarm.get(j).copy());
        }

        //去重
        for(int i=0;i<swarm.size();i++){
            for(int j=0;j<Pd.get(i).size();j++){
                for(int k=j+1;k<Pd.get(i).size();k++){
                    if(Pd.get(i).get(j).getObjective(0)<=Pd.get(i).get(k).getObjective(0)&&
                            Pd.get(i).get(j).getObjective(1)<=Pd.get(i).get(k).getObjective(1)){
                        Pd.get(i).remove(k);
                        k--;
                    }
                }
                for(int k=j+1;k<Pd.get(i).size();k++){
                    if(Pd.get(i).get(j).getObjective(0)>=Pd.get(i).get(k).getObjective(0)&&
                            Pd.get(i).get(j).getObjective(1)>=Pd.get(i).get(k).getObjective(1)){
                        Pd.get(i).remove(j);
                        j--;
                        break;
                    }
                }
            }
        }
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
    private void getCrossOfFactoryVectorBySingle(PermutationSolution<Integer> a,PermutationSolution<Integer> b) {       //对工厂向量进行单点交叉
        int index;
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int boundflag = random.nextInt(b.getNumberOfVariablesid());          //  随机产生一个单点下标
        for (int i = boundflag; i < b.getNumberOfVariablesid(); i++) {
            index = i;
            cross4FactoryVectorBySingle(a, b, i, index);   //交换下标i与下标index的值
        }
    }
    private void cross4FactoryVectorBySingle(PermutationSolution<Integer> a,PermutationSolution<Integer> b, int index1, int index2) {     //交换值
        int temp1 = a.getVariableValueid(index1);    //工厂
        int temp2 = b.getVariableValueid(index2);

        a.setVariableValueid(index1, temp2);
        b.setVariableValueid(index2, temp1);
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
    private void exchangeIndex4FactoryVectorByRandom(PermutationSolution<Integer> a, int index1, int value) {     //交换值
        //int temp1 =  a.getVariableValueid(index1);
        a.setVariableValueid(index1, value);
    }
    @Override
    public List<PermutationSolution<Integer>> getResult() {
        return Pgd;
    }

    private int index = 1;

    /**
     * Update leaders method
     * @param swarm List of solutions (swarm)
     */
    @Override
    protected void updateParticlesMemory(List<PermutationSolution<Integer>> swarm) {

        //添加
        for (int k = 0; k < swarm.size(); k++){
            Pgd.add((PermutationSolution<Integer>) Pd.get(k).get(Pd.get(k).size()-1).copy());
        }

        //去重
        for(int i=0;i<Pgd.size();i++){
            for(int j=i+1;j<Pgd.size();j++){
                if(Pgd.get(i).getObjective(0)<=Pgd.get(j).getObjective(0)&&
                        Pgd.get(i).getObjective(1)<=Pgd.get(j).getObjective(1)){
                    Pgd.remove(j);
                    j--;
                }
            }
            for(int j=i+1;j<Pgd.size();j++){
                if(Pgd.get(i).getObjective(0)>=Pgd.get(j).getObjective(0)&&
                        Pgd.get(i).getObjective(1)>=Pgd.get(j).getObjective(1)){
                    Pgd.remove(i);
                    i--;
                    break;
                }
            }
        }

        double object1 = Double.MAX_VALUE;
        double object2 = Double.MAX_VALUE;
        double object3 = Double.MAX_VALUE;
        for (PermutationSolution<Integer> integerPermutationSolution : Pgd) {
            if(object1 > integerPermutationSolution.getObjective(0))object1=integerPermutationSolution.getObjective(0);
            if(object2 > integerPermutationSolution.getObjective(1))object2=integerPermutationSolution.getObjective(1);
            if(object3 > integerPermutationSolution.getObjective(2))object3=integerPermutationSolution.getObjective(2);
        }
        System.out.println("第"+index+"代："+"object1="+object1+" "+"object2="+object2+" "+"object3="+object3);
        index++;

    }
    private void mutation4worker(PermutationSolution<Integer> particle){

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
        machine.set(numberOfMachine, temp);
        particle.setAttribute("machine", machine);
    }
    @Override public String getName() {
        return "MOPSO" ;
    }

    @Override public String getDescription() {
        return "Optimized MOPSO" ;
    }

}
