package org.uma.jmetal.algorithm.multiobjective.mymohea;

import org.uma.jmetal.algorithm.multiobjective.mypso.util.ST;
import org.uma.jmetal.algorithm.myimpl.AbstractGeneticAlgorithmS;
import org.uma.jmetal.differentialevolution.impl.DE4ExchangeSequence;
import org.uma.jmetal.operator.CrossoverOperator;
import org.uma.jmetal.operator.MutationOperator;
import org.uma.jmetal.operator.SelectionOperator;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.problem.multiobjective.dfsp.DHFSP;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;
import org.uma.jmetal.util.solutionattribute.impl.StrengthRawFitness;
import org.uma.jmetal.problem.multiobjective.dfsp.DFSP3Double;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;


public class MOHEADE <S extends Solution<?>> extends AbstractGeneticAlgorithmS<S, List<S>> {
    protected final int maxIterations;
    protected final SolutionListEvaluator<S> evaluator;
    protected int iterations;
    protected List<S> archive;
    protected final StrengthRawFitness<S> strenghtRawFitness = new StrengthRawFitness<S>();
    //     protected final EnvironmentalSelection<S> environmentalSelection;
    protected int numberofarchive;
    protected int VEGAsize;
    protected double Probability;
    protected List<S> Pareto;

    private double Cross_c;
    private double Mutation_m;

    private double CrossoverRates4worker;
    private double CrossoverRates4machine;
    private double mutationRate4worker;
    private double mutationRate4machine;

    private int[][] K_means;
    private DFSP3Double Clusterindex;

    protected JMetalRandom randomGenerator ;
    public MOHEADE(Problem<S> problem, int maxIterations, int populationSize,
                   CrossoverOperator<S> crossoverOperator, MutationOperator<S> mutationOperator,
                   SelectionOperator<List<S>, S> selectionOperator, SolutionListEvaluator<S> evaluator,
                   int numberofarchive, int VEGAsize, double Probability,double crossoverRate, double mutationRate,double CrossoverRates4worker,double CrossoverRates4machine,double mutationRate4worker,double mutationRate4machine) {
        super(problem);
        this.maxIterations = maxIterations;
        this.setMaxPopulationSize(populationSize);

        this.numberofarchive = numberofarchive;  //中间的精英种群
        this.crossoverOperator = crossoverOperator;
        this.mutationOperator = mutationOperator;
        this.selectionOperator = selectionOperator;
        this.VEGAsize = VEGAsize;
        this.Probability = Probability;
        this.Mutation_m = mutationRate;
        this.Cross_c = crossoverRate;
        this.archive = new ArrayList<>(numberofarchive);  //中间的精英种群

        this.CrossoverRates4worker=CrossoverRates4worker;
        this.CrossoverRates4machine=CrossoverRates4machine;
        this.mutationRate4worker=mutationRate4worker;
        this.mutationRate4machine=mutationRate4machine ;

        randomGenerator = JMetalRandom.getInstance() ;
        this.Pareto = new ArrayList<>();
        //   this.environmentalSelection = new EnvironmentalSelection<S>(populationSize, k);

        // this.archive = null;

        this.evaluator = evaluator;
    }

    @Override
    protected void initProgress() {
        //iterations = 1;
        iterations = getMaxPopulationSize();//初始种群大小
    }

    @Override
    protected void updateProgress() {
        //iterations++;
        iterations = iterations + getMaxPopulationSize();     //新加的
    }


    protected List<S> createInitialPopulation() {      //创建初始种群
        List<PermutationSolution<Integer>> population = new ArrayList<>(getMaxPopulationSize());


        int swarmSize2 = (int) (getMaxPopulationSize()*0.4);
        int swarmSize1 = getMaxPopulationSize() - (int) (getMaxPopulationSize()*0.4);

        PermutationSolution<Integer> newSolution;   //一个粒子
//        K_means = Clusterindex.jobFactoryCluster;
//        int[][] indexArr = K_means;

        for (int t = 0; t < getMaxPopulationSize(); t++) {
            newSolution = (PermutationSolution<Integer>) getProblem().createSolution();
            population.add(newSolution);
        }
//        System.out.println(population);
//        System.out.println(population.size());
//        sleep();
        /*for (int t = 0; t < swarmSize1; t++) {
            newSolution = (PermutationSolution<Integer>) getProblem().createSolution();

            List<Integer> jobArr = new ArrayList<>(newSolution.getNumberOfVariables());
            List<Integer> facArrtemp = new ArrayList<>(newSolution.getNumberOfVariables());
            List<Integer> facArr = new ArrayList<>(newSolution.getNumberOfVariables());
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
                org.uma.jmetal.util.research.runtime.SeededRandom.shuffle(facArrtemp);        //打乱工厂
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
            }
            population.add(newSolution);
        }*/
//        System.out.println(population.size());
//        System.out.println(population);
//        sleep();
        return (List<S>) population;
    }

    private static void sleep() {
        try {
            Thread.sleep(999999);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
    }


    @Override
    protected boolean isStoppingConditionReached() {
        return iterations >= maxIterations;
    }

    @Override
    protected List<S> evaluatePopulation(List<S> population) {
        population = evaluator.evaluate(population, getProblem());
//        System.out.println(population);
//        sleep();
        return population;
    }

    @Override
    protected List<S> selection(List<S> population,int index) {

        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        double rantemp = random.nextDouble();
        //加DE
        DE4ExchangeSequence exchangeSequence = new DE4ExchangeSequence();
        //archive = A.DEexe(archive,Probability*rantemp);
        archive = exchangeSequence.executeDEProcess(PDDRFFSelectionexecute(population, numberofarchive), Probability * rantemp);//对A'（t)PDDR-FF之后 ==A'（t+1），对A'（t+1）做DE
        archive = evaluatePopulation(archive);


        int listnumber = population.size() + numberofarchive;
        List<S> union = new ArrayList<>(listnumber);

        for (int i = 0; i < archive.size(); i++) {
            union.add((S) archive.get(i).copy());
        }

        for (int i = 0; i < population.size(); i++) {
            union.add((S) population.get(i).copy());
        }

        archive = PDDRFFSelectionexecute(union, numberofarchive);
        archive = evaluatePopulation(archive);

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

        updatePareto(archive);
        return archive;
    }

    protected List<S> PDDRFFSelectionexecute(List<S> population, int numberofarchive) {
        List<S> archivetemp = new ArrayList<>(numberofarchive);
        List<S> populationtemp = new ArrayList<>(population.size());
        for (int i = 0; i < population.size(); i++) {
            populationtemp.add((S) population.get(i).copy());
        }

        populationtemp = PDDRFF_Ascending_order(populationtemp);

        for (int i = 0; i < numberofarchive; i++) {
            archivetemp.add((S) populationtemp.get(i).copy());
        }
//        System.out.println(archivetemp);
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
        double DominateTime = 0;     //个体支配他人的数目
        double BedominatedTime = 0;  // 个体被他人支配数目
        for (int i = 0; i < population.size(); i++) {
            if (isADiminateB(individual, population.get(i))) {
                DominateTime = DominateTime + 1;
            }
            if (isADiminateB(population.get(i), individual)) {
                BedominatedTime = BedominatedTime + 1;
            }
        }
        eval = BedominatedTime + (1 / (DominateTime + 1));
        return eval;
    }

    protected boolean isADiminateB(S individualA, S individualB) {

        double fitnessA[] = new double[2];  //第一组适应度函数  用于对比
        double fitnessB[] = new double[2];  //第二组适应度函数  用于对比
        fitnessA = individualA.getObjectives();
        fitnessB = individualB.getObjectives();
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

    protected List<S> Create_VEGA_Population1(List<S> population) {//todo 20241113
//        System.out.println(VEGAsize);
//        sleep();
        List<S> VEGA_Population = new ArrayList<>(3 * VEGAsize);
        List<S> VEGA_Population1 = new ArrayList<>(VEGAsize);
        List<S> VEGA_Population2 = new ArrayList<>(VEGAsize);
        List<S> VEGA_Population3 = new ArrayList<>(VEGAsize);

        List<S> tempPopulation = new ArrayList<>(population.size());
        for (int i = 0; i < population.size(); i++) {
            tempPopulation.add((S) population.get(i).copy());
        }

        for (int i = 0; i < VEGAsize; i++) {
            S temp_VEGA_individua1 = Selection_For_Create_VEGA(1, tempPopulation);
            S temp_VEGA_individua2 = Selection_For_Create_VEGA(2, tempPopulation);
            S temp_VEGA_individua3 = Selection_For_Create_VEGA(7, tempPopulation);
            VEGA_Population1.add(temp_VEGA_individua1);
            VEGA_Population2.add(temp_VEGA_individua2);
            VEGA_Population3.add(temp_VEGA_individua3);
        }

        VEGA_Population.addAll(VEGA_Population1);
        VEGA_Population.addAll(VEGA_Population2);
        VEGA_Population.addAll(VEGA_Population3);

        return VEGA_Population;

    }

    protected S Selection_For_Create_VEGA(int ObjectiveNum, List<S> population) {

        S Selection_individual = null;

        int temp1 = (int) (org.uma.jmetal.util.research.runtime.SeededRandom.current().nextDouble() * population.size());    //随机生成第一个数
        int temp2 = (int) (org.uma.jmetal.util.research.runtime.SeededRandom.current().nextDouble() * population.size());    //随机生成第二个数
        while (temp1 == temp2) {  //重复了
            temp2 = (int) (org.uma.jmetal.util.research.runtime.SeededRandom.current().nextDouble() * population.size());    //重新随机生成第二个数
        }

        if (isADominateBOnOneObjective(ObjectiveNum, population.get(temp1), population.get(temp2))) {
            Selection_individual = population.get(temp1);
        }
        if (isADominateBOnOneObjective(ObjectiveNum, population.get(temp2), population.get(temp1))) {
            Selection_individual = population.get(temp2);
        }
        if (Selection_individual == null) { //如果谁也不支配谁  把第一个放入
            Selection_individual = (S) population.get(temp1).copy();
        }
        return Selection_individual;
    }

    protected boolean isADominateBOnOneObjective(int ObjectiveNum, S individualA, S individualB) {


        double fitnessA[] = new double[2];  //第一组适应度函数  用于对比
        double fitnessB[] = new double[2];  //第二组适应度函数  用于对比

        fitnessA = individualA.getObjectives();
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
        int[] nw = DHFSP.nw;
        while (offSpringPopulation.size() < getMaxPopulationSize()) {
            List<S> parents = new ArrayList<>(2);
            S candidateFirstParent = selectionOperator.execute(population);
            parents.add(candidateFirstParent);
            S candidateSecondParent;
            candidateSecondParent = selectionOperator.execute(population);
            parents.add(candidateSecondParent);

            int crossoverflag;
            int mutationflag = 0;
            //新增加的
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            double c, m;
            c = random.nextDouble();
            List<S> offspring = crossoverOperator.execute(parents); //TODO 应该是只针对job sequence向量做运算
            //新加对工厂向量的交叉操作
            if (c > Cross_c) {
//                System.out.println(c);
//                System.out.println(Cross_c);
//                sleep();
                offspring=(List<S>) getCrossOfFactoryVectorBySingle((List<PermutationSolution<Integer>>) parents);    //单点交叉
                for (int i = 0; i < offspring.size(); i++) {
                    exchange4WorkerSequence((PermutationSolution<Integer>) offspring.get(i));
                }
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
                mutationOperator.execute(offspring.get(i)); //TODO 应该是只针对job sequence向量做运算

                //新加对工厂变异操作
                m = random.nextDouble();
                ArrayList<ST> listV1 = new ArrayList<>();
                if (m < Mutation_m) {
                    ST q = new ST(randomGenerator.nextInt(0, offspring.get(i).getNumberOfVariables() - 1));
                    listV1.add(q);
                    addNew4FactoryVectorByRandom((PermutationSolution<Integer>) offspring.get(i), listV1,i);
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

                offSpringPopulation.add(offspring.get(i));
                if (offSpringPopulation.size() >= getMaxPopulationSize())
                    break;
            }

            if (crossoverflag == 1) {
                iterations = iterations + 2;
            } else {
                iterations = iterations + mutationflag;
            }

        }


/*            List<S> offspring = crossoverOperator.execute(parents);
            mutationOperator.execute(offspring.get(0));
            offSpringPopulation.add(offspring.get(0));*/     //之前的
            return offSpringPopulation;
        }


   //把精英解添加到pareto
    protected void updatePareto(List<S> population){
        for(int i=0;i<population.size();i++){
            Pareto.add((S) population.get(i).copy());
        }


        for(int i=0;i<Pareto.size();i++){
            for(int j=i+1;j<Pareto.size();j++){
                if(Pareto.get(i).getObjective(0)<=Pareto.get(j).getObjective(0) &&
                        Pareto.get(i).getObjective(1)<=Pareto.get(j).getObjective(1)&&
                        Pareto.get(i).getObjective(2)<=Pareto.get(j).getObjective(2)){
                    Pareto.remove(j);
                    j--;
                }
            }

            for(int j=i+1;j<Pareto.size();j++){
                if(Pareto.get(i).getObjective(0)>=Pareto.get(j).getObjective(0) &&
                        Pareto.get(i).getObjective(1)>=Pareto.get(j).getObjective(1)&&
                        Pareto.get(i).getObjective(2)>=Pareto.get(j).getObjective(2)){
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

        offspring.add((PermutationSolution<Integer>) parents.get(0).copy()) ;
        offspring.add((PermutationSolution<Integer>) parents.get(1).copy()) ;
        int boundflag = random.nextInt(offspring.get(1).getNumberOfVariablesid());          //  随机产生一个单点下标
        for (int i = boundflag; i < offspring.get(1).getNumberOfVariablesid(); i++) {
            index = i;
            cross4FactoryVectorBySingle(offspring.get(0), offspring.get(1), i, index);   //交换下标i与下标index的值
        }
        return offspring;
    }

    private void cross4FactoryVectorBySingle(PermutationSolution<Integer> a,PermutationSolution<Integer> b, int index1, int index2) {     //交换值
        int temp1 = a.getVariableValueid(index1);    //工厂
        int temp2 = b.getVariableValueid(index2);

        a.setVariableValueid(index1, temp2);
        b.setVariableValueid(index2, temp1);
    }

    private void addNew4FactoryVectorByRandom(PermutationSolution<Integer> arr, ArrayList<ST> list,int i) {
        ST s;
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        for (int j = 0; j < list.size(); j++) {
            s = list.get(j);
            int r = random.nextInt(3);
            //工厂序号分别是 0，1，2 所以生成0-3但不包括3的随机整数来进行突变
            exchangeIndex4FactoryVectorByRandom(arr, s.getX(), r);             //   随机选一位数进行改变
        }
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
//            System.out.println(archive.size());
//            System.out.println(Pareto.size());
            return archive;//有pareto的输出，需要pareto的相关函数
        }

        @Override public String getName() {
            return "MOHEADE" ;
        }

        @Override public String getDescription() {
            return "Strength Pareto. Evolutionary Algorithm" ;
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
        PermutationSolution<Integer> HisOptIndividual = parents.get(0);
        PermutationSolution<Integer> particle = parents.get(1);
        List<Integer> a1 = HisOptIndividual.getVariablesworker();
        List<Integer> a2 = particle.getVariablesworker();
        if (a1 == null || a2 == null || nw == null || a1.isEmpty() || a2.isEmpty() || nw.length == 0) {
            throw new IllegalArgumentException("Lists and steps array must not be null or empty");
        }

        // 确保两个列表长度相同
        if (a1.size() != a2.size()) {
            throw new IllegalArgumentException("Lists must have the same length");
        }

        // 计算分块的起始和结束位置
        List<int[]> blocks = calculateBlocks(nw, a1.size());

        // 随机选择一个分块
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int blockIndex = random.nextInt(blocks.size());


        // 获取选中的分块范围
        int[] selectedBlock = blocks.get(blockIndex);
        int start = selectedBlock[0];
        int end = selectedBlock[1];

        // 交换分块内容
        swapBlocks(a1, a2, start, end);
        for (int i2 = 0; i2 < a2.size(); i2++) {
            particle.setVariableValueworker(i2,a2.get(i2));
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

        List<Integer> integerPermutationSolutionfactory = integerPermutationSolution.getVariablesid();
        List<Integer> particlefactory = particle.getVariablesid();

        Random r = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int max = r.nextInt(machineintegerPermutationSolution.size()-1);
        int min = r.nextInt(machineintegerPermutationSolution.size()-1);
        if (max<min){
            int temp = 0;
            temp = max;
            max = min;
            min = temp;
        }
        List<Integer> machinetemp1 = new ArrayList<>(machineintegerPermutationSolution.subList(min, max + 1));
        List<Integer> machinetemp2 = new ArrayList<>(machineparticle.subList(min, max + 1));

        List<Integer> factorytemp1 = new ArrayList<>(integerPermutationSolutionfactory.subList(min, max + 1));
        List<Integer> factorytemp2 = new ArrayList<>(particlefactory.subList(min, max + 1));

        int[][] numberOfMachines = DHFSP.numberOfMachines_;
        for (int i = 0; i < machinetemp1.size(); i++) {
            if (factorytemp1.get(i)==factorytemp2.get(i)){
                int temp1 = machinetemp1.get(i);
                int temp2 = machinetemp2.get(i);
                machinetemp2.set(i,temp1);
                machinetemp1.set(i,temp2);
            }
            else {
                int temp1 =numberOfMachines[factorytemp1.get(i)][0];
                temp1 = r.nextInt(temp1);
                machinetemp1.set(i,temp1);

                int temp2 =numberOfMachines[factorytemp2.get(i)][0];
                temp2 = r.nextInt(temp2);
                machinetemp2.set(i,temp2);
            }
        }
        for (int i = 0; i < machinetemp1.size(); i++) {
            machineparticle.set(min,machinetemp2.get(i));
            min++;
        }

        particle.setAttribute("machine",machineparticle);
        return offspring;
    }

    //工人变异
    private void mutation4worker(PermutationSolution<Integer> particle){
        List<Integer> variablesworker = particle.getVariablesworker();
        int[] nw = DHFSP.nw;
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        List<List<Integer>> blocks = splitIntoBlocks(variablesworker, nw);

        // 2. 随机选择一个分块
        int selectedBlockIndex = random.nextInt(blocks.size());
        List<Integer> selectedBlock = blocks.get(selectedBlockIndex);

        // 3. 在选中的分块中随机选择两个位置的元素进行交换
        if (selectedBlock.size() > 1) {  // 确保分块中有足够的元素可以交换
            int pos1 = random.nextInt(selectedBlock.size());
            int pos2 = random.nextInt(selectedBlock.size());
            while (pos1 == pos2) {  // 确保两个位置不同
                pos2 = random.nextInt(selectedBlock.size());
            }

            // 交换两个位置的元素
            int temp = selectedBlock.get(pos1);
            selectedBlock.set(pos1, selectedBlock.get(pos2));
            selectedBlock.set(pos2, temp);
        }

        // 4. 将所有分块重新合并为一个列表
        List<Integer> result = new ArrayList<>();
        for (List<Integer> block : blocks) {
            result.addAll(block);
        }

        for (int i = 0; i < result.size(); i++) {
            particle.setVariableValueworker(i,result.get(i));
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
        int[][] numberOfMachines = DHFSP.numberOfMachines_;
        int numberOfMachine = numberOfMachines[tempfactory][0];

        int temp = r.nextInt(numberOfMachine);
        machine.set(numberOfMachine,temp);
        particle.setAttribute("machine",machine);
    }

}
