package org.uma.jmetal.algorithm.multiobjective.mymohea;

import org.uma.jmetal.algorithm.multiobjective.mypso.util.ST;
import org.uma.jmetal.algorithm.myimpl.AbstractGeneticAlgorithmS;
import org.uma.jmetal.operator.CrossoverOperator;
import org.uma.jmetal.operator.MutationOperator;
import org.uma.jmetal.operator.SelectionOperator;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.problem.multiobjective.dfsp.DHFSP;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;
import org.uma.jmetal.util.solutionattribute.impl.StrengthRawFitness;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class MOHEA<S extends Solution<?>> extends AbstractGeneticAlgorithmS<S, List<S>> {
    protected final int maxIterations;
    protected final SolutionListEvaluator<S> evaluator;
    protected int iterations;
    protected List<S> archive;
    protected final StrengthRawFitness<S> strenghtRawFitness = new StrengthRawFitness<S>();
    //     protected final EnvironmentalSelection<S> environmentalSelection;
    protected int archiveSize;
    protected int VEGAsize;
    protected List<S> Pareto;

    private double Cross_c;
    private double Mutation_m;
    private double CrossoverRates4worker;
    private double CrossoverRates4machine;
    private double mutationRate4worker;
    private double mutationRate4machine;

    protected JMetalRandom randomGenerator;

    public MOHEA(Problem<S> problem, int maxIterations, int populationSize,
                 CrossoverOperator<S> crossoverOperator, MutationOperator<S> mutationOperator,
                 SelectionOperator<List<S>, S> selectionOperator, SolutionListEvaluator<S> evaluator,
                 int numberofarchive, int VEGAsize, double crossoverRate, double mutationRate,double CrossoverRates4worker,double CrossoverRates4machine,double mutationRate4worker,double mutationRate4machine) {
        super(problem);
        this.maxIterations = maxIterations;
        this.setMaxPopulationSize(populationSize);

        this.archiveSize = numberofarchive;
        this.crossoverOperator = crossoverOperator;
        this.mutationOperator = mutationOperator;
        this.selectionOperator = selectionOperator;
        this.VEGAsize = VEGAsize;
        this.archive = new ArrayList<>(numberofarchive);  //精英种群

        this.Pareto = new ArrayList<>();

        this.Mutation_m = mutationRate;
        this.Cross_c = crossoverRate;

        this.CrossoverRates4worker=CrossoverRates4worker;
        this.CrossoverRates4machine=CrossoverRates4machine;
        this.mutationRate4worker=mutationRate4worker;
        this.mutationRate4machine=mutationRate4machine ;
        randomGenerator = JMetalRandom.getInstance();
        //   this.environmentalSelection = new EnvironmentalSelection<S>(populationSize, k);

        // this.archive = null;

        this.evaluator = evaluator;
    }

    @Override
    protected void initProgress() {
        //iterations = 1;
        iterations = getMaxPopulationSize();
    }

    @Override
    protected void updateProgress() {
        //iterations++;
        iterations = iterations + getMaxPopulationSize();     //新加的
    }

    @Override
    protected boolean isStoppingConditionReached() {
        return iterations >= maxIterations;
    }

    @Override
    protected List<S> evaluatePopulation(List<S> population) {

        population = evaluator.evaluate(population, getProblem());

        return population;
    }

    @Override
    protected List<S> selection(List<S> population,int index) {

        population = Deduplication(population);
//            System.out.println(archiveSize);
//            try {
//                Thread.sleep(99999);
//            } catch (InterruptedException e) {
//                throw new RuntimeException(e);
//            }
        archive = executePDDRFFSelection(population, archiveSize);

        double object1 = Double.MAX_VALUE;
        double object2 = Double.MAX_VALUE;
        double object3 = Double.MAX_VALUE;
        for (S integerPermutationSolution : archive) {
            if(object1 > integerPermutationSolution.getObjective(0))object1=integerPermutationSolution.getObjective(0);
            if(object2 > integerPermutationSolution.getObjective(1))object2=integerPermutationSolution.getObjective(1);
            if(object3 > integerPermutationSolution.getObjective(2))object3=integerPermutationSolution.getObjective(2);
        }
        System.out.println("第"+index+"代："+"object1="+object1+" "+"object2="+object2+" "+"object3="+object3);
        index++;

        //archive = evaluatePopulation(archive);
        updatePareto(archive);
        index++;
        return archive;
    }

    protected List<S> Deduplication(List<S> population) {

        for (int i = 0; i < population.size() - 1; i++) {
            for (int j = i + 1; j < population.size(); j++) {

                if (population.get(i).getObjective(0) == population.get(j).getObjective(0) &&
                        population.get(i).getObjective(1) == population.get(j).getObjective(1) &&
                        population.get(i).getObjective(2) == population.get(j).getObjective(2)) {
                    population.remove(j);
                    j--;
                }

            }
        }

        return population;
    }

    protected List<S> executePDDRFFSelection(List<S> population, int numberofarchive) {
        List<S> archivetemp = new ArrayList<>(numberofarchive);
        List<S> populationtemp = new ArrayList<>(population.size());
        for (int i = 0; i < population.size(); i++) {
            populationtemp.add((S) population.get(i).copy());
        }
//        System.out.println(populationtemp.size());
//        System.out.println(populationtemp);

        populationtemp = PDDRFF_Ascending_order(populationtemp);
//        System.out.println(populationtemp.size());
        for (int i = 0; i < numberofarchive; i++) {
            archivetemp.add((S) populationtemp.get(i).copy());
        }
//        System.out.println(archivetemp.size());
//        sleep();

        return archivetemp;
    }

    protected List<S> PDDRFF_Ascending_order(List<S> population) {
        List<S> populationtemp = new ArrayList<>(population.size());
        List<S> Orderpopulation = new ArrayList<>(populationtemp.size());

        for (int i = 0; i < population.size(); i++) {
            populationtemp.add((S) population.get(i).copy());
        }

        double[][] fitnesstemp = new double[populationtemp.size()][2];

        for (int i = 0; i < populationtemp.size(); i++) {
            fitnesstemp[i][0] = i;
            fitnesstemp[i][1] = calculatePDDRFF(populationtemp.get(i), populationtemp);
        }
//        for (double[] doubles : fitnesstemp) {
//            for (double aDouble : doubles) {
//                System.out.println(aDouble+" ");
//            }
//            System.out.println();
//        }
//        System.out.println();
//        try {
//            Thread.sleep(99999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
        for (int i = 0; i < populationtemp.size(); i++) {    //冒泡排序 对fitness序列排序
            double[] temp = new double[2];
            temp[0] = 0;
            temp[1] = 0;
            for (int j = i + 1; j < populationtemp.size(); j++) {
                if (fitnesstemp[j][1] < fitnesstemp[i][1]) {
                    temp[0] = fitnesstemp[i][0];  //交换内容
                    temp[1] = fitnesstemp[i][1];  //交换内容

                    fitnesstemp[i][0] = fitnesstemp[j][0];
                    fitnesstemp[i][1] = fitnesstemp[j][1];

                    fitnesstemp[j][0] = temp[0];
                    fitnesstemp[j][1] = temp[1];
                }
            }
        }

        for (int i = 0; i < populationtemp.size(); i++) {  //按照最小值下标序列覆盖
            Orderpopulation.add(populationtemp.get((int) fitnesstemp[i][0]));
        }
        return Orderpopulation;
    }


    protected double calculatePDDRFF(S individual, List<S> population) {
        // population = evaluatePopulation(population);
        double eval = 0; //初始化为0
        double dominatingNumber = 0;     //个体支配他人的数目
        double dominatedNumber = 0;  // 个体被他人支配数目
        for (int i = 0; i < population.size(); i++) {
            if (isADominateB(individual, population.get(i))) {
                dominatingNumber = dominatingNumber + 1;
            }
            if (isADominateB(population.get(i), individual)) {
                dominatedNumber = dominatedNumber + 1;
            }
        }
        eval = dominatedNumber + (1 / (dominatingNumber + 1));
        return eval;
    }

    protected boolean isADominateB(S individualA, S individualB) {

        double fitnessA[] = new double[2];  //第一组适应度函数  用于对比
        double fitnessB[] = new double[2];  //第二组适应度函数  用于对比
        fitnessA = individualA.getObjectives();
        fitnessB = individualB.getObjectives();
//        for (double v : fitnessA) {
//            System.out.print(v+" ");
//        }
//        try {
//            Thread.sleep(99999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
        if (fitnessA[0] < fitnessB[0] && fitnessA[1] < fitnessB[1] && fitnessA[6] < fitnessB[6]) {
            return true;
        } else if (fitnessA[0] < fitnessB[0] && fitnessA[1] == fitnessB[1] && fitnessA[6] == fitnessB[6]) {
            return true;
        } else if (fitnessA[0] == fitnessB[0] && fitnessA[1] < fitnessB[1] && fitnessA[6] == fitnessB[6]) {
            return true;
        } else if (fitnessA[0] == fitnessB[0] && fitnessA[6] < fitnessB[6] && fitnessA[1] == fitnessB[1]) {
            return true;
        } else if (fitnessA[0] == fitnessB[0] && fitnessA[6] < fitnessB[6] && fitnessA[1] < fitnessB[1]) {
            return true;
        } else if (fitnessA[0] < fitnessB[0] && fitnessA[6] < fitnessB[6] && fitnessA[1] == fitnessB[1]) {
            return true;
        } else if (fitnessA[0] < fitnessB[0] && fitnessA[6] == fitnessB[6] && fitnessA[1] < fitnessB[1]) {
            return true;
        } else {
            return false;
        }
    }

    protected List<S> Create_VEGA_Population1(List<S> population) {
        List<S> VEGA_Population = new ArrayList<>(3 * VEGAsize);
        List<S> VEGA_Population1 = new ArrayList<>(VEGAsize);
        List<S> VEGA_Population2 = new ArrayList<>(VEGAsize);
        List<S> VEGA_Population3 = new ArrayList<>(VEGAsize);

        List<S> tempPopulation = new ArrayList<>(population.size());
        for (int i = 0; i < population.size(); i++) {
            tempPopulation.add((S) population.get(i).copy());
        }

        for (int i = 0; i < VEGAsize; i++) {
            S temp_VEGA_individual1 = Selection_For_Create_VEGA(1, tempPopulation);
            S temp_VEGA_individual2 = Selection_For_Create_VEGA(2, tempPopulation);
            S temp_VEGA_individual3 = Selection_For_Create_VEGA(7, tempPopulation);//20241113
            VEGA_Population1.add(temp_VEGA_individual1);
            VEGA_Population2.add(temp_VEGA_individual2);
            VEGA_Population3.add(temp_VEGA_individual3);
        }

        VEGA_Population.addAll(VEGA_Population1);
        VEGA_Population.addAll(VEGA_Population2);
        VEGA_Population.addAll(VEGA_Population3);

        return VEGA_Population;
    }

    private static void sleep() {
        try {
            Thread.sleep(99999);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
    }

    protected S Selection_For_Create_VEGA(int ObjectiveNum, List<S> population) {

        S Selection_individual = null;

        int temp1 = (int) (org.uma.jmetal.util.research.runtime.SeededRandom.current().nextDouble() * population.size());    //随机生成第一个数
        int temp2 = (int) (org.uma.jmetal.util.research.runtime.SeededRandom.current().nextDouble() * population.size());    //随机生成第二个数
        while (temp1 == temp2) {  //重复了
            temp2 = (int) (org.uma.jmetal.util.research.runtime.SeededRandom.current().nextDouble() * population.size());    //重新随机生成第二个数
        }
//        System.out.println(temp1);
//        System.out.println(temp2);
//        System.out.println(ObjectiveNum);
//        System.out.println(population.get(temp1));
//        System.out.println(population.get(temp2));
//        sleep();

        if (isADominateBOnOneObjective(ObjectiveNum, population.get(temp1), population.get(temp2))) {
            Selection_individual = population.get(temp1);
        }
        if (isADominateBOnOneObjective(ObjectiveNum, population.get(temp2), population.get(temp1))) {
            Selection_individual = population.get(temp2);
        }
        if (Selection_individual == null) { //如果谁也不支配谁  把第一个放入
            Selection_individual = (S) population.get(temp1).copy();
        }
//        System.out.println(Selection_individual);
//        sleep();
        return Selection_individual;
    }

    protected boolean isADominateBOnOneObjective(int ObjectiveNum, S individualA, S individualB) {


        double fitnessA[] = new double[2];  //第一组适应度函数  用于对比
        double fitnessB[] = new double[2];  //第二组适应度函数  用于对比

        fitnessA = individualA.getObjectives();
//        for (double v : fitnessA) {
//            System.out.print(v+" ");
//        }
//        System.out.println();
        fitnessB = individualB.getObjectives();
        if (fitnessA[ObjectiveNum - 1] < fitnessB[ObjectiveNum - 1]) {
            return true;
        } else {
            return false;
        }
    }

    protected List<S> merge(List<S> Population1) {
        List<S> Merge_Population = null;
        if (Population1 != null && archive != null) {   //两个群都不空
            Merge_Population = new ArrayList<>(Population1.size() + archive.size());

            for (int i = 0; i < Population1.size() + archive.size(); i++) {
                if (i < Population1.size()) {//第一个种群
                    Merge_Population.add((S) Population1.get(i).copy());

                } else {//第二个种群
                    Merge_Population.add((S) archive.get(i - Population1.size()).copy());
                }
            }
        } else if (Population1 != null && archive == null) {  //种群1不空 种群2空， 返回种群1
            Merge_Population = new ArrayList<>(Population1.size());
            for (int i = 0; i < Population1.size(); i++) {
                Merge_Population.add((S) Population1.get(i).copy());
            }
        } else if (Population1 == null && archive != null) {  //种群1空 种群2不空， 返回种群2
            Merge_Population = new ArrayList<>(archive.size());
            for (int i = 0; i < archive.size(); i++) {
                Merge_Population.add((S) archive.get(i).copy());
            }

        }

        return Merge_Population;
    }

    @Override
    protected List<S> reproduction(List<S> population) {
        List<S> offSpringPopulation = new ArrayList<>(getMaxPopulationSize());

        while (offSpringPopulation.size() < getMaxPopulationSize()) {
            int crossoverflag;
            int mutationflag = 0;

            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            double c, m;
            c = random.nextDouble();
            int[] nw = DHFSP.nw;
            //m = random.nextDouble();      //加

            List<S> parents = new ArrayList<>(2);
            S candidateFirstParent = selectionOperator.execute(population);
            parents.add(candidateFirstParent);
            S candidateSecondParent;
            candidateSecondParent = selectionOperator.execute(population);
            parents.add(candidateSecondParent);

            List<S> offspring = crossoverOperator.execute(parents); // TODO PMX 只针对job sequence 做交叉 20211009 zhangwq
            //新加对工厂向量的交叉操作
            if (c < Cross_c) {
                offspring = (List<S>) getCrossOfFactoryVectorBySingle((List<PermutationSolution<Integer>>) parents);    //单点交叉
//                System.out.println(offspring);
//                sleep();
            }
            double c_worker = random.nextDouble();
            if (c_worker < CrossoverRates4worker) {
                offspring = (List<S>) crossover4workersequence((List<PermutationSolution<Integer>>) offspring, nw);//工人向量交叉
            }
            double c_machine = random.nextDouble();
            if (c_machine < CrossoverRates4machine) {
                offspring= (List<S>) crossover4machinesequence((List<PermutationSolution<Integer>>) offspring);
            }

            crossoverflag = crossoverOperator.getCrossoverProbabilityflag();

            for (int i = 0; i < offspring.size(); i++) {
                mutationOperator.execute(offspring.get(i)); // TODO 只针对job sequence 做变异 20211009 zhangwq    i
///////新加对工厂变异操作

//                c = random.nextDouble();
//                if (c < Cross_c) {
//                    exchange4WorkerSequence((PermutationSolution<Integer>) offspring.get(i));
//                }

                m = random.nextDouble();
                ArrayList<ST> listV1 = new ArrayList<>();
                if (m < Mutation_m) {
                    ST q = new ST(randomGenerator.nextInt(0, offspring.get(i).getNumberOfVariables() - 1));
                    listV1.add(q);
                    addNew4FactoryVectorByRandom((PermutationSolution<Integer>) offspring.get(i), listV1, i);
                }
                double m_worker = random.nextDouble();
                if (m_worker < mutationRate4worker){
                    mutation4worker((PermutationSolution<Integer>) offspring.get(i));
                }
                double m_machine = random.nextDouble();
                if (m_machine < mutationRate4machine) {
                    mutation4machine((PermutationSolution<Integer>) offspring.get(i));
                }


                mutationflag = mutationflag + mutationOperator.getMutationProbabilityflag();

                offSpringPopulation.add(offspring.get(i));     //i
                if (offSpringPopulation.size() >= getMaxPopulationSize())
                    break;
            }

            if (crossoverflag == 1) {
                iterations = iterations + 2;
            } else {
                iterations = iterations + mutationflag;
            }


        }
        return offSpringPopulation;
    }

    //把精英解添加到pareto
    protected void updatePareto(List<S> population) {

        for (int i = 0; i < population.size(); i++) {
            Pareto.add((S) population.get(i).copy());
        }

        for (int i = 0; i < Pareto.size(); i++) {
            for (int j = i + 1; j < Pareto.size(); j++) {
                if (Pareto.get(i).getObjective(0) <= Pareto.get(j).getObjective(0) &&
                        Pareto.get(i).getObjective(1) <= Pareto.get(j).getObjective(1) &&
                        Pareto.get(i).getObjective(2) <= Pareto.get(j).getObjective(2)) {
                    Pareto.remove(j);
                    j--;
                }
            }

            for (int j = i + 1; j < Pareto.size(); j++) {
                if (Pareto.get(i).getObjective(0) >= Pareto.get(j).getObjective(0) &&
                        Pareto.get(i).getObjective(1) >= Pareto.get(j).getObjective(1) &&
                        Pareto.get(i).getObjective(2) >= Pareto.get(j).getObjective(2)) {
                    Pareto.remove(i);
                    i--;
                    break;
                }
            }
        }
//        System.out.println(Pareto.size());


    }

    private List<PermutationSolution<Integer>> getCrossOfFactoryVectorBySingle(List<PermutationSolution<Integer>> parents) {       //对工厂向量进行单点交叉
        int index;
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        List<PermutationSolution<Integer>> offspring = new ArrayList<>(2);

        offspring.add((PermutationSolution<Integer>) parents.get(0).copy());
        offspring.add((PermutationSolution<Integer>) parents.get(1).copy());
        int boundflag = random.nextInt(offspring.get(1).getNumberOfVariablesid());          //  随机产生一个单点下标
        for (int i = boundflag; i < offspring.get(1).getNumberOfVariablesid(); i++) {
            index = i;
            cross4FactoryVectorBySingle(offspring.get(0), offspring.get(1), i, index);   //交换下标i与下标index的值
        }
        return offspring;
    }

    private void cross4FactoryVectorBySingle(PermutationSolution<Integer> a, PermutationSolution<Integer> b, int index1, int index2) {     //交换值
        int temp1 = a.getVariableValueid(index1);    //工厂
        int temp2 = b.getVariableValueid(index2);

        a.setVariableValueid(index1, temp2);
        b.setVariableValueid(index2, temp1);
    }

    private void addNew4FactoryVectorByRandom(PermutationSolution<Integer> arr, ArrayList<ST> list, int i) {
        ST s;
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();

/*        List<PermutationSolution<Integer>> offspring = new ArrayList<>(1);
        offspring.add((PermutationSolution<Integer>) arr.copy()) ;*/

        for (int j = 0; j < list.size(); j++) {
            s = list.get(j);
            int r = random.nextInt(3);//todo
            //工厂序号分别是 0，1，2 所以生成0-3但不包括3的随机整数来进行突变
            exchangeIndex4FactoryVectorByRandom(arr, s.getX(), r);             //   随机选一位数进行改变
        }
        //return offspring;
    }

    private void exchangeIndex4FactoryVectorByRandom(PermutationSolution<Integer> a, int index1, int value) {     //交换值
        a.setVariableValueid(index1, value);
    }

    @Override
    protected List<S> replacement(List<S> population,
                                  List<S> offspringPopulation) {
        return offspringPopulation;
    }

    @Override
    public List<S> getResult() {
        return Pareto;//有pareto的输出需要用到pareto相关函数
    }

    @Override
    public String getName() {
        return "MOHEA";
    }

    @Override
    public String getDescription() {
        return "Strength Pareto. Evolutionary Algorithm";
    }

    protected void exchange4WorkerSequence(PermutationSolution<Integer> swarm){
        int[] nw = DHFSP.nw;
        int[] tempArray = new int[swarm.getVariablesworker().size()];
        for (int i = 0; i < swarm.getVariablesworker().size(); i++) {
            tempArray[i] = swarm.getVariableValueworker(i);
        }
        List<List<Integer>> lists = segmentArray(tempArray, nw);

        for (List<Integer> list : lists) {
            int r1, r2;
            r1=randomGenerator.nextInt(0,list.size()-1);
            r2=randomGenerator.nextInt(0,list.size()-1);
            if (r1 != r2) {
                exchangeIndex4WorkerSequenceVectorByExchangeSequence(r1,r2,list);
            }
        }
//        System.out.println(swarm);
        int tempindex = 0;
        for (List<Integer> list : lists) {
            for (Integer i : list) {
                swarm.setVariableValueworker(tempindex,i);
                tempindex++;
            }
        }
//        System.out.println(swarm);
//        sleep();
    }

    protected void exchangeIndex4WorkerSequenceVectorByExchangeSequence(int r1,int r2,List<Integer> list){
//        Integer variableValueworker1 = swarm.getVariableValueworker(r1);
//        Integer variableValueworker2 = swarm.getVariableValueworker(r2);
//        swarm.setVariableValueworker(r1,variableValueworker2);
//        swarm.setVariableValueworker(r2,variableValueworker1);
//        System.out.println(list);
//        System.out.println(r1);
//        System.out.println(r2);
        Integer i1 = list.get(r1);
        Integer i2 = list.get(r2);
        list.set(r1,i2);
        list.set(r2,i1);
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


    public static List<PermutationSolution<Integer>> crossover4workersequence(List<PermutationSolution<Integer>> parents, int[] nw) {

        List<Integer> variablesworker1 = parents.get(0).getVariablesworker();
        List<Integer> variablesworker2 = parents.get(1).getVariablesworker();

        List<Integer> variablesid1 = parents.get(0).getVariablesid();
        List<Integer> variablesid2 = parents.get(1).getVariablesid();

        int numberOfVariables = parents.get(0).getNumberOfVariables();//每一阶段的工件数

        int stage = variablesworker1.size() / parents.get(0).getNumberOfVariables();
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
                if (parents.get(0).getVariableValueid(i1) == parents.get(1).getVariableValueid(i1)) {
                    Integer variableValueworker1 = parents.get(0).getVariableValueworker(index);
                    Integer variableValueworker2 = parents.get(1).getVariableValueworker(index);
//                    System.out.println("index"+index+",variableValueworker1:"+variableValueworker1+",variableValueworker2:"+variableValueworker2);
                    parents.get(0).setVariableValueworker(index, variableValueworker2);
                    parents.get(1).setVariableValueworker(index, variableValueworker1);
                }
            }

        }


        return parents;
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


    private List<PermutationSolution<Integer>> crossover4machinesequence(List<PermutationSolution<Integer>> offspring) {
        PermutationSolution<Integer> integerPermutationSolution = offspring.get(0);
        PermutationSolution<Integer> particle = offspring.get(1);


        ArrayList<Integer> machineintegerPermutationSolution = (ArrayList<Integer>) integerPermutationSolution.getAttribute("machine");
        ArrayList<Integer> machineparticle = (ArrayList<Integer>) particle.getAttribute("machine");;
//        ArrayList<Integer> machineintegerPermutationSolution = (ArrayList<Integer>) integerPermutationSolution.getAttribute("machine");
//        ArrayList<Integer> machineparticle = (ArrayList<Integer>) particle.getAttribute("machine");


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

        return offspring;
    }

    //工人变异
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

}
