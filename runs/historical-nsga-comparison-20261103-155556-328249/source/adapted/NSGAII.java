package org.uma.jmetal.algorithm.multiobjective.nsgaii;

import org.uma.jmetal.algorithm.impl.AbstractGeneticAlgorithm;
import org.uma.jmetal.algorithm.multiobjective.mypso.util.ST;
import org.uma.jmetal.operator.CrossoverOperator;
import org.uma.jmetal.operator.MutationOperator;
import org.uma.jmetal.operator.SelectionOperator;
import org.uma.jmetal.operator.impl.mutation.PermutationSwapMutation;
import org.uma.jmetal.operator.impl.selection.RankingAndCrowdingSelection;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.problem.multiobjective.dfsp.DHFSP;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;
import org.uma.jmetal.util.SolutionListUtils;
import org.uma.jmetal.util.comparator.DominanceComparator;
import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Random;

/**
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 */
@SuppressWarnings("serial")
public class NSGAII<S extends Solution<?>> extends AbstractGeneticAlgorithm<S, List<S>> {
    protected final int maxEvaluations;

    protected final SolutionListEvaluator<S> evaluator;

    protected int evaluations;
    protected Comparator<S> dominanceComparator;

    protected int matingPoolSize;
    protected int offspringPopulationSize;
    protected JMetalRandom randomGenerator ;
    private double Cross_c;
    private double Mutation_m;
    private double CrossoverRates4worker;
    private double CrossoverRates4machine;
    private double mutationRate4worker;
    private double mutationRate4machine;
    /**
     * Constructor
     */
    public NSGAII(Problem<S> problem, int maxEvaluations, int populationSize,
                  int matingPoolSize, int offspringPopulationSize,
                  CrossoverOperator<S> crossoverOperator, MutationOperator<S> mutationOperator,
                  SelectionOperator<List<S>, S> selectionOperator, SolutionListEvaluator<S> evaluator,double crossoverRate, double mutationRate,double CrossoverRates4worker,double CrossoverRates4machine,double mutationRate4worker,double mutationRate4machine) {
        this(problem, maxEvaluations, populationSize, matingPoolSize, offspringPopulationSize,
                crossoverOperator, mutationOperator, selectionOperator, new DominanceComparator<S>(), evaluator,crossoverRate,mutationRate,CrossoverRates4worker,CrossoverRates4machine,mutationRate4worker,mutationRate4machine);
    }

    /**
     * Constructor
     */
    public NSGAII(Problem<S> problem, int maxEvaluations, int populationSize,
                  int matingPoolSize, int offspringPopulationSize,
                  CrossoverOperator<S> crossoverOperator, MutationOperator<S> mutationOperator,
                  SelectionOperator<List<S>, S> selectionOperator, Comparator<S> dominanceComparator,
                  SolutionListEvaluator<S> evaluator,double crossoverRate, double mutationRate,double CrossoverRates4worker,double CrossoverRates4machine,double mutationRate4worker,double mutationRate4machine) {
        super(problem);
        this.maxEvaluations = maxEvaluations;
        setMaxPopulationSize(populationSize);
        ;

        this.crossoverOperator = crossoverOperator;
        this.mutationOperator = mutationOperator;
        this.selectionOperator = selectionOperator;

        this.evaluator = evaluator;
        this.dominanceComparator = dominanceComparator;

        this.matingPoolSize = matingPoolSize;
        this.offspringPopulationSize = offspringPopulationSize;

        this.Mutation_m = mutationRate;
        this.Cross_c = crossoverRate;


        this.CrossoverRates4worker=CrossoverRates4worker;
        this.CrossoverRates4machine=CrossoverRates4machine;
        this.mutationRate4worker=mutationRate4worker;
        this.mutationRate4machine=mutationRate4machine ;


        randomGenerator = JMetalRandom.getInstance() ;
    }

    @Override
    protected void initProgress() {
        evaluations = getMaxPopulationSize();
        //evaluations=1;
    }

    @Override
    protected void updateProgress() {
        //evaluations += offspringPopulationSize ;
        //evaluations++ ;


        evaluations = evaluations + getMaxPopulationSize();  //新加的
    }

    @Override
    protected boolean isStoppingConditionReached() {
        return evaluations >= maxEvaluations;
    }

    @Override
    protected List<S> evaluatePopulation(List<S> population) {
        population = evaluator.evaluate(population, getProblem());

        return population;
    }

    /**
     * This method iteratively applies a {@link SelectionOperator} to the population to fill the mating pool population.
     *
     * @param population
     * @return The mating pool population
     */
    @Override
    protected List<S> selection(List<S> population) {
        List<S> matingPopulation = new ArrayList<>(population.size());
        for (int i = 0; i < matingPoolSize; i++) {
            S solution = selectionOperator.execute(population);
            matingPopulation.add(solution);
        }

        return matingPopulation;
    }

    /**
     * This methods iteratively applies a {@link CrossoverOperator} a  {@link MutationOperator} to the population to
     * create the offspring population. The population size must be divisible by the number of parents required
     * by the {@link CrossoverOperator}; this way, the needed parents are taken sequentially from the population.
     * <p>
     * The number of solutions returned by the {@link CrossoverOperator} must be equal to the offspringPopulationSize
     * state variable
     *
     * @param matingPool
     * @return The new created offspring population
     */
    @Override
    protected List<S> reproduction(List<S> matingPool) {
        int numberOfParents = crossoverOperator.getNumberOfRequiredParents();

        checkNumberOfParents(matingPool, numberOfParents);

        List<S> offspringPopulation = new ArrayList<>(offspringPopulationSize);
        for (int i = 0; i < matingPool.size(); i += numberOfParents) {
//            int crossoverflag = 0;
//            int mutationflag = 0;
//
//            Random random = new Random();
//            double c, m;
//            c = random.nextDouble();
//
//            List<S> parents = new ArrayList<>(numberOfParents);
//            for (int j = 0; j < numberOfParents; j++) {
//                parents.add(population.get(i + j));
//            }
//
////            System.out.println(parents);
//            List<S> offspring = crossoverOperator.execute(parents);
////
////            System.out.println(offspring);
////            try {
////                Thread.sleep(99999);
////            } catch (InterruptedException e) {
////                throw new RuntimeException(e);
////            }
//
//            //新加对工厂向量的交叉操作
//            if (c < Cross_c) {
//                offspring=(List<S>) getCrossOfFactoryVectorBySingle((List<PermutationSolution<Integer>>) parents);    //单点交叉
//                for (S s : offspring) {
//                    exchange4WorkerSequence((PermutationSolution<Integer>) s);
//                }
//            }
//            crossoverflag = crossoverOperator.getCrossoverProbabilityflag();
//
//            for (S s : offspring) {
//                mutationOperator.execute(s);
//
//                ///////新加对工厂变异操作
//                m = random.nextDouble();
//                ArrayList<ST> listV1 = new ArrayList<>();
//                if (m < Mutation_m) {
//                    ST q = new ST(randomGenerator.nextInt(0, s.getNumberOfVariables() - 1));
//                    listV1.add(q);
//                    addNew4FactoryVectorByRandom((PermutationSolution<Integer>) s, listV1,i);
//
//                }
//
//                mutationflag = mutationflag + mutationOperator.getMutationProbabilityflag();
//
//                offspringPopulation.add(s);
//                if (offspringPopulation.size() >= offspringPopulationSize)
//                    break;
//            }
//
//
//            if (crossoverflag == 1) {
//                evaluations = evaluations + 2;
//            } else {
//                evaluations = evaluations + mutationflag;
//            }

            //20241228
            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            double c = random.nextDouble();
            double m = random.nextDouble();
            int crossoverflag = 0;
            int mutationflag = 0;
            int[] nw = DHFSP.nw;

            List<S> parents = new ArrayList<>(numberOfParents);  //numberOfParents = 2
            for (int j = 0; j < numberOfParents; j++) {
                parents.add(population.get(i + j));
            }


            List<S> offspring = crossoverOperator.execute(parents);

            if (c < Cross_c) {
                offspring=(List<S>) getCrossOfFactoryVectorBySingle((List<PermutationSolution<Integer>>) parents);    //单点交叉
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

            //变异
            for (S s : offspring) {
                mutationOperator.execute(s);

                ///////新加对工厂变异操作
                m = random.nextDouble();
                ArrayList<ST> listV1 = new ArrayList<>();
                if (m < Mutation_m) {
                    ST q = new ST(randomGenerator.nextInt(0, s.getNumberOfVariables() - 1));
                    listV1.add(q);
                    addNew4FactoryVectorByRandom((PermutationSolution<Integer>) s, listV1,i);
                }

                double m_worker = random.nextDouble();
                if (m_worker < mutationRate4worker){
                    mutation4worker((PermutationSolution<Integer>) s);
                }
                double m_machine = random.nextDouble();
                if (m_machine < mutationRate4machine) {
                    mutation4machine((PermutationSolution<Integer>) s);
                }



                mutationflag = mutationflag + mutationOperator.getMutationProbabilityflag();

                offspringPopulation.add(s);
                if (offspringPopulation.size() >= offspringPopulationSize)
                    break;
            }


            if (crossoverflag == 1) {

                evaluations = evaluations + 2;
            } else {
                evaluations = evaluations + mutationflag;
            }

        }
        return offspringPopulation;
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

    @Override
    protected List<S> replacement(List<S> population, List<S> offspringPopulation) {
        List<S> jointPopulation = new ArrayList<>();
        jointPopulation.addAll(population);
        jointPopulation.addAll(offspringPopulation);

        RankingAndCrowdingSelection<S> rankingAndCrowdingSelection;
        rankingAndCrowdingSelection = new RankingAndCrowdingSelection<S>(getMaxPopulationSize(), dominanceComparator);



        return rankingAndCrowdingSelection.execute(jointPopulation);
    }

    private void addNew4FactoryVectorByRandom(PermutationSolution<Integer> arr, ArrayList<ST> list,int i) {
        ST s;
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        int factorysize = EDHHFSPW.numberOfMachines_.length;
/*        List<PermutationSolution<Integer>> offspring = new ArrayList<>(1);
        offspring.add((PermutationSolution<Integer>) arr.copy()) ;*/

        for (int j = 0; j < list.size(); j++) {
            s = list.get(j);
            int r = random.nextInt(factorysize);
            //工厂序号分别是 0，1，2 所以生成0-3但不包括3的随机整数来进行突变
            exchangeIndex4FactoryVectorByRandom(arr, s.getX(), r);             //   随机选一位数进行改变
        }
        //return offspring;
    }

    private void exchangeIndex4FactoryVectorByRandom(PermutationSolution<Integer> a, int index1, int value) {     //交换值
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
    }

    @Override
    public List<S> getResult() {

        return SolutionListUtils.getNondominatedSolutions(getPopulation());
    }

    @Override
    public String getName() {
        return "NSGAII";
    }

    @Override
    public String getDescription() {
        return "Nondominated Sorting Genetic Algorithm version II";
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




//20250313
//    public static List<PermutationSolution<Integer>> crossover4workersequence(List<PermutationSolution<Integer>> parents, int[] nw) {
//        PermutationSolution<Integer> HisOptIndividual = parents.get(0);
//        PermutationSolution<Integer> particle = parents.get(1);
//        List<Integer> a1 = HisOptIndividual.getVariablesworker();
//        List<Integer> a2 = particle.getVariablesworker();
//        if (a1 == null || a2 == null || nw == null || a1.isEmpty() || a2.isEmpty() || nw.length == 0) {
//            throw new IllegalArgumentException("Lists and steps array must not be null or empty");
//        }
//
//        // 确保两个列表长度相同
//        if (a1.size() != a2.size()) {
//            throw new IllegalArgumentException("Lists must have the same length");
//        }
//
//        // 计算分块的起始和结束位置
//        List<int[]> blocks = calculateBlocks(nw, a1.size());
//
//        // 随机选择一个分块
//        Random random = new Random();
//        int blockIndex = random.nextInt(blocks.size());
//
//
//        // 获取选中的分块范围
//        int[] selectedBlock = blocks.get(blockIndex);
//        int start = selectedBlock[0];
//        int end = selectedBlock[1];
//
//        // 交换分块内容
//        swapBlocks(a1, a2, start, end);
//        for (int i2 = 0; i2 < a2.size(); i2++) {
//            particle.setVariableValueworker(i2,a2.get(i2));
//        }
//
//        return parents;
//
//
//
//
//
//
//    }

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

//20250313
//    private List<PermutationSolution<Integer>> crossover4machinesequence(List<PermutationSolution<Integer>> offspring) {
//        PermutationSolution<Integer> integerPermutationSolution = offspring.get(0);
//        PermutationSolution<Integer> particle = offspring.get(1);
//
//
//        ArrayList<Integer> machineintegerPermutationSolution = (ArrayList<Integer>) integerPermutationSolution.getAttribute("machine");
//        ArrayList<Integer> machineparticle = (ArrayList<Integer>) particle.getAttribute("machine");;
//
//        List<Integer> integerPermutationSolutionfactory = integerPermutationSolution.getVariablesid();
//        List<Integer> particlefactory = particle.getVariablesid();
//
//        Random r = new Random();
//        int max = r.nextInt(machineintegerPermutationSolution.size()-1);
//        int min = r.nextInt(machineintegerPermutationSolution.size()-1);
//        if (max<min){
//            int temp = 0;
//            temp = max;
//            max = min;
//            min = temp;
//        }
//        List<Integer> machinetemp1 = new ArrayList<>(machineintegerPermutationSolution.subList(min, max + 1));
//        List<Integer> machinetemp2 = new ArrayList<>(machineparticle.subList(min, max + 1));
//
//        List<Integer> factorytemp1 = new ArrayList<>(integerPermutationSolutionfactory.subList(min, max + 1));
//        List<Integer> factorytemp2 = new ArrayList<>(particlefactory.subList(min, max + 1));
//
//        int[][] numberOfMachines = DHFSP.numberOfMachines_;
//        for (int i = 0; i < machinetemp1.size(); i++) {
//            if (factorytemp1.get(i)==factorytemp2.get(i)){
//                int temp1 = machinetemp1.get(i);
//                int temp2 = machinetemp2.get(i);
//                machinetemp2.set(i,temp1);
//                machinetemp1.set(i,temp2);
//            }
//            else {
//                int temp1 =numberOfMachines[factorytemp1.get(i)][0];
//                temp1 = r.nextInt(temp1);
//                machinetemp1.set(i,temp1);
//
//                int temp2 =numberOfMachines[factorytemp2.get(i)][0];
//                temp2 = r.nextInt(temp2);
//                machinetemp2.set(i,temp2);
//            }
//        }
//        for (int i = 0; i < machinetemp1.size(); i++) {
//            machineparticle.set(min,machinetemp2.get(i));
//            min++;
//        }
//
//        particle.setAttribute("machine",machineparticle);
//        return offspring;
//    }

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

//20250313
    //工人变异
//    private void mutation4worker(PermutationSolution<Integer> particle){
//        List<Integer> variablesworker = particle.getVariablesworker();
//        int[] nw = DHFSP.nw;
//        Random random = new Random();
//        List<List<Integer>> blocks = splitIntoBlocks(variablesworker, nw);
//
//        // 2. 随机选择一个分块
//        int selectedBlockIndex = random.nextInt(blocks.size());
//        List<Integer> selectedBlock = blocks.get(selectedBlockIndex);
//
//        // 3. 在选中的分块中随机选择两个位置的元素进行交换
//        if (selectedBlock.size() > 1) {  // 确保分块中有足够的元素可以交换
//            int pos1 = random.nextInt(selectedBlock.size());
//            int pos2 = random.nextInt(selectedBlock.size());
//            while (pos1 == pos2) {  // 确保两个位置不同
//                pos2 = random.nextInt(selectedBlock.size());
//            }
//
//            // 交换两个位置的元素
//            int temp = selectedBlock.get(pos1);
//            selectedBlock.set(pos1, selectedBlock.get(pos2));
//            selectedBlock.set(pos2, temp);
//        }
//
//        // 4. 将所有分块重新合并为一个列表
//        List<Integer> result = new ArrayList<>();
//        for (List<Integer> block : blocks) {
//            result.addAll(block);
//        }
//
//        for (int i = 0; i < result.size(); i++) {
//            particle.setVariableValueworker(i,result.get(i));
//        }
//    }


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
