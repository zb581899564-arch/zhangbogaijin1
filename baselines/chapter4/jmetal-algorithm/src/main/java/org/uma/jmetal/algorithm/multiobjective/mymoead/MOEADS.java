package org.uma.jmetal.algorithm.multiobjective.mymoead;

import org.uma.jmetal.algorithm.multiobjective.moead.util.MOEADUtils;
import org.uma.jmetal.algorithm.multiobjective.mypso.util.ST;
import org.uma.jmetal.operator.CrossoverOperator;
import org.uma.jmetal.operator.MutationOperator;
import org.uma.jmetal.operator.impl.crossover.DifferentialEvolutionCrossoverS;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.problem.multiobjective.dfsp.DHFSP;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Class implementing the MOEA/D-DE algorithm described in :
 * Hui Li; Qingfu Zhang, "Multiobjective Optimization Problems With Complicated Pareto Sets,
 * MOEA/D and NSGA-II," Evolutionary Computation, IEEE Transactions on , vol.13, no.2, pp.284,302,
 * April 2009. doi: 10.1109/TEVC.2008.925798
 *
 * @author Antonio J. Nebro
 * @version 1.0
 */
@SuppressWarnings("serial")
public class MOEADS<S extends Solution<?>> extends AbstractMOEADS<S> {
    protected DifferentialEvolutionCrossoverS differentialEvolutionCrossover;
    private double Cross_c;
    private double Mutation_m;
    private int numberOfFactories;

    private double CrossoverRates4worker;
    private double CrossoverRates4machine;
    private double mutationRate4worker;
    private double mutationRate4machine;


    public MOEADS(int factories, Problem<S> problem,
                  int populationSize,
                  int resultPopulationSize,
                  int maxEvaluations,
                  MutationOperator<S> mutation,
                  CrossoverOperator<S> crossover,
                  FunctionType functionType,
                  String dataDirectory,
                  double neighborhoodSelectionProbability,
                  int maximumNumberOfReplacedSolutions,
                  int neighborSize, double crossoverRate, double mutationRate,double CrossoverRates4worker,double CrossoverRates4machine,double mutationRate4worker,double mutationRate4machine) {
        super(problem, populationSize, resultPopulationSize, maxEvaluations, crossover, mutation, functionType,
                dataDirectory, neighborhoodSelectionProbability, maximumNumberOfReplacedSolutions,
                neighborSize);
        this.numberOfFactories = factories;
        this.Mutation_m = mutationRate;
        this.Cross_c = crossoverRate;
        this.CrossoverRates4worker=CrossoverRates4worker;
        this.CrossoverRates4machine=CrossoverRates4machine;
        this.mutationRate4worker=mutationRate4worker;
        this.mutationRate4machine=mutationRate4machine ;

        differentialEvolutionCrossover = new DifferentialEvolutionCrossoverS();
    }

    @Override
    public void run() {
        initializePopulation();
        initializeUniformWeight();
        initializeNeighborhood();
        idealPoint.update(population);

        //   evaluations = 0;
        evaluations = populationSize;
        int index = 0;
        do {
            int[] nw = DHFSP.nw;

            Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
            double c, m;
            c = random.nextDouble();
            m = random.nextDouble();      //加

            int[] permutation = new int[populationSize];


            MOEADUtils.randomPermutation(permutation, populationSize);

            for (int i = 0; i < populationSize; i++) {
                int subProblemId = permutation[i];

                NeighborType neighborType = chooseNeighborType();

                List<S> parents = parentSelection(subProblemId, neighborType);
//                System.out.println(parents);
                differentialEvolutionCrossover.setCurrentSolution((PermutationSolution<Integer>) population.get(subProblemId));

                List<S> children = (List<S>) differentialEvolutionCrossover.execute((List<PermutationSolution<Integer>>) parents);
//                System.out.println(children);
//                sleep();
//新加对工厂向量的操作
                if (c < Cross_c) {
                    children = (List<S>) getCrossOfFactoryVectorBySingle((List<PermutationSolution<Integer>>) parents);    //单点交叉

                }
                double c_worker = random.nextDouble();
                if (c_worker < CrossoverRates4worker) {
                    children = (List<S>) crossover4workersequence((List<PermutationSolution<Integer>>) children, nw);//工人向量交叉
                }
                double c_machine = random.nextDouble();
                if (c_machine < CrossoverRates4machine) {
                    children= (List<S>) crossover4machinesequence((List<PermutationSolution<Integer>>) children);
                }

                int crossoverflag = differentialEvolutionCrossover.getCrossoverProbabilityflag();

//////新加对工厂向量的操作
                ArrayList<ST> listV = new ArrayList<>();
                if (m < Mutation_m) {
                    ST q = new ST(randomGenerator.nextInt(0, children.get(0).getNumberOfVariables() - 1));
                    listV.add(q);
                    children = (List<S>) addNew4FactoryVectorByRandom((List<PermutationSolution<Integer>>) children, listV);
                }

                double m_worker = random.nextDouble();
                if (m_worker < mutationRate4worker){
                    mutation4worker((PermutationSolution<Integer>) children.get(0));
                }
                double m_machine = random.nextDouble();
                if (m_machine < mutationRate4machine) {
                    mutation4machine((PermutationSolution<Integer>) children.get(0));
                }


                S child = children.get(0);
                //PermutationSolution<Integer> child = children.get(0) ;

                mutationOperator.execute(child);
                int mutationflag = mutationOperator.getMutationProbabilityflag();
//新加对工厂向量的操作
                /*ArrayList<ST> listV = new ArrayList<>();
                if (m < Mutation_m) {
                    ST q = new ST(randomGenerator.nextInt(0, child.getNumberOfVariables() - 1));
                    listV.add(q);
                     child= (S) addNew4FactoryVectorByRandom((List<PermutationSolution<Integer>>) child, listV);
                }*/

                problem.evaluate(child);

                if (crossoverflag == 1 || mutationflag == 1) {
                    evaluations++;
                }

                idealPoint.update(child.getObjectives());
                updateNeighborhood(child, subProblemId, neighborType);
            }
            //evaluations++;


            for (int i = 0; i < populationSize / 2; i++) {
                PermutationSolution<Integer> getswarm1 = null;
                int g1 = 1;
                getswarm1 = selectFac1((PermutationSolution<Integer>) population.get(i), g1);
                population.set(i, (S) getswarm1);
            }
            for (int i = populationSize / 2; i < populationSize; i++) {
                PermutationSolution<Integer> getswarm1 = null;
                int g2 = 3;
                getswarm1 = selectFac1((PermutationSolution<Integer>) population.get(i), g2);
                population.set(i, (S) getswarm1);
            }
//            System.out.println("population.size()"+population.size());
//            sleep();
            double object1 = Double.MAX_VALUE;
            double object2 = Double.MAX_VALUE;
            double object3 = Double.MAX_VALUE;
            for (S integerPermutationSolution : population) {
                if(object1 > integerPermutationSolution.getObjective(0))object1=integerPermutationSolution.getObjective(0);
                if(object2 > integerPermutationSolution.getObjective(1))object2=integerPermutationSolution.getObjective(1);
                if(object3 > integerPermutationSolution.getObjective(2))object3=integerPermutationSolution.getObjective(2);
            }
            System.out.println("第"+index+"代："+"object1="+object1+" "+"object2="+object2+" "+"object3="+object3);
            index++;
        } while (evaluations < maxEvaluations);

    }

    private static void sleep() {
        try {
            Thread.sleep(999999);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
    }


    protected PermutationSolution<Integer> selectFac1(PermutationSolution<Integer> swarmtemp, int group) {
        PermutationSolution<Integer> getswarm = null;
        getswarm = factorySearch(swarmtemp, group);

        //mergeNew1(swarmFac);

        return getswarm;
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
        while (l < 2) {
            pop1.clear();
            current_pop1.clear();
            current_solution = insert_otherfac(current_solution, group);
            pop1.add(solution);
            current_pop1.add(current_solution);

            /*problem.evaluate((S) current_solution);
            problem.evaluate((S) solution);*/

            //current_pop1 = evaluator.evaluate(current_pop1, problem);
            //pop1 = evaluator.evaluate(pop1, problem);

            if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                solution1 = current_solution;
                current_solution = insertion_fac(solution1, group);
            } else {
                current_solution = insertion_fac(current_solution, group);
            }
            //current_solution = insertion_fac(current_solution,group);
            pop1.add(solution);
            current_pop1.add(current_solution);

            /*problem.evaluate((S) current_pop1);
            problem.evaluate((S) pop1);*/

            //current_pop1 = evaluator.evaluate(current_pop1, problem);
            //pop1 = evaluator.evaluate(pop1, problem);
            if (group == 1) {
                if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    //l=0;
                    break;
                } else {
                    l++;
                }
            }
            if (group == 2) {

                if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    break;
                    //l=0;
                } else {
                    l++;
                }
            }
            if (group == 3) {
                if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1)) || (current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0))) {
                    //if ((current_pop1.get(0).getObjective(0) < pop1.get(0).getObjective(0) && current_pop1.get(0).getObjective(1) < pop1.get(0).getObjective(1))) {
                    solution = current_solution;
                    break;
                    //l=0;
                } else {
                    l++;
                }
            }


        }
        return solution;
    }

    public PermutationSolution<Integer> insertion_fac(PermutationSolution<Integer> solution, int group) {
        Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        PermutationSolution<Integer> solutionNew = (PermutationSolution<Integer>) solution.copy();
        int a, i, j;
        // PermutationSolution<Integer> solutiontemp = problem.createSolution();
        //List<List<Integer>> t = new ArrayList<>();  //存工厂号下对应的工件序列的下标
        //ArrayList<List<Integer>> N = new ArrayList<>();
        int[][] N = new int[numberOfFactories][solution.getNumberOfVariablesid()];       //存相同工厂的工件下标

        List<Integer> v = new ArrayList<>();
        int[] ind = new int[numberOfFactories];     //存工厂号

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
        //System.out.print(len);
//        System.out.print(N);
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();

        int maxfac1 = random.nextInt(numberOfFactories);
        int[] rListmax = new int[len[maxfac1][0]];
        for (int k = 0; k < len[maxfac1][0]; k++) {
            rListmax[k] = N[maxfac1][k];      // rList里面存相应工厂号下的工件的下标
        }
        //System.out.print(rList1);
        int minfac1 = random.nextInt(numberOfFactories);
        int[] rListmin = new int[len[minfac1][0]];
        for (int k = 0; k < len[minfac1][0]; k++) {
            rListmin[k] = N[minfac1][k];      // rList里面存相应工厂号下的工件的下标
        }
        // System.out.print(rList1);
        int maxfac2 = random.nextInt(numberOfFactories);
        int[] rListmax1 = new int[len[maxfac2][0]];
        for (int k = 0; k < len[maxfac2][0]; k++) {
            rListmax1[k] = N[maxfac2][k];      // rList里面存相应工厂号下的工件的下标
        }
        int minfac2 = random.nextInt(numberOfFactories);
        int[] rListmin1 = new int[len[minfac2][0]];
        for (int k = 0; k < len[minfac2][0]; k++) {
            rListmin1[k] = N[minfac2][k];      // rList里面存相应工厂号下的工件的下标
        }
        //System.out.print(rList1);
        //System.out.print(solution);
        if (group == 1) {
            int[] listtemp1 = rListmax;
            int[] listtemp2 = rListmin;

            int max = A.nextInt(listtemp1.length);
            int min = A.nextInt(listtemp2.length);

            int jobindexa = listtemp1[max];    //工件下标
            int jobindexb = listtemp2[min];
            int joba = solution.getVariableValue(jobindexa);
            int jobb = solution.getVariableValue(jobindexb);
            solutionNew.setVariableValue(jobindexa, jobb);
            solutionNew.setVariableValue(jobindexb, joba);
            // System.out.print(solutionNew);
        }


        if (group == 3) {
            int[] listtemp1 = rListmax1;
            int[] listtemp2 = rListmin1;
            if (listtemp1.length!=0&&listtemp2.length!=0){
                int max = A.nextInt(listtemp1.length);
                int min = A.nextInt(listtemp2.length);

                int jobindexa = listtemp1[max];    //工件下标
                int jobindexb = listtemp2[min];
                int joba = solution.getVariableValue(jobindexa);
                int jobb = solution.getVariableValue(jobindexb);
                solutionNew.setVariableValue(jobindexa, jobb);
                solutionNew.setVariableValue(jobindexb, joba);
            }

        }

        return solutionNew;
    }

    public PermutationSolution<Integer> insert_otherfac(PermutationSolution<Integer> solution, int group) {
        Random A = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        PermutationSolution<Integer> solutionNew = (PermutationSolution<Integer>) solution.copy();
        int a, i, j;
        // PermutationSolution<Integer> solutiontemp = problem.createSolution();
        //List<List<Integer>> t = new ArrayList<>();  //存工厂号下对应的工件序列的下标
        //ArrayList<List<Integer>> N = new ArrayList<>();
        int[][] N = new int[numberOfFactories][solution.getNumberOfVariablesid()];       //存相同工厂的工件下标

        List<Integer> v = new ArrayList<>();
        int[] ind = new int[numberOfFactories];     //存工厂号

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
        //System.out.print(len);
//        System.out.print(N);

        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        //int r = random.nextInt(3);
        int maxfac1 = random.nextInt(numberOfFactories / 2);
        int[] rListmaxa = new int[len[maxfac1][0]];
        for (int k = 0; k < len[maxfac1][0]; k++) {
            rListmaxa[k] = N[maxfac1][k];      // rList里面存相应工厂号下的工件的下标
        }
        //System.out.print(rList1);
        int minfac1 = random.nextInt(numberOfFactories / 2) + numberOfFactories / 2;
        int[] rListmina = new int[len[minfac1][0]];
        for (int k = 0; k < len[minfac1][0]; k++) {
            rListmina[k] = N[minfac1][k];      // rList里面存相应工厂号下的工件的下标
        }
        // System.out.print(rList1);
        int maxfac2 = random.nextInt(numberOfFactories / 2);
        int[] rListmax1 = new int[len[maxfac2][0]];
        for (int k = 0; k < len[maxfac2][0]; k++) {
            rListmax1[k] = N[maxfac2][k];      // rList里面存相应工厂号下的工件的下标
        }
        int minfac2 = random.nextInt(numberOfFactories / 2) + numberOfFactories / 2;
        int[] rListmin1 = new int[len[minfac2][0]];
        for (int k = 0; k < len[minfac2][0]; k++) {
            rListmin1[k] = N[minfac2][k];      // rList里面存相应工厂号下的工件的下标
        }
        //System.out.print(rList1);
        //System.out.print(solution);
        if (group == 1 && len[maxfac1][0] - len[minfac1][0] > 2) {
            int[] listtemp1 = rListmaxa;
            int[] listtemp2 = rListmina;

            int max = A.nextInt(listtemp1.length);
            //int min = A.nextInt(listtemp2.length);

            int jobindexa = listtemp1[max];    //工件下标
            //int jobindexb = listtemp2[min];
            //int joba = solution.getVariableValue(jobindexa);
            //int jobb = solution.getVariableValue(jobindexb);
            solutionNew.setVariableValueid(jobindexa, minfac1);
            // System.out.print(solutionNew);
        }


        if (group == 3) {
            int[] listtemp1 = rListmax1;
            int[] listtemp2 = rListmin1;


            if (listtemp1.length!=0){
                int max = A.nextInt(listtemp1.length);
                //int min = A.nextInt(listtemp2.length);

                int jobindexa = listtemp1[max];    //工件下标
                //int jobindexb = listtemp2[min];
                //int joba = solution.getVariableValue(jobindexa);
                //int jobb = solution.getVariableValue(jobindexb);
                //solutionNew.setVariableValue(jobindexa,jobb);
                //solutionNew.setVariableValue(jobindexb,joba);
                solutionNew.setVariableValueid(jobindexa, minfac2);
            }

        }

        return solutionNew;
    }


    protected void initializePopulation() {
        population = new ArrayList<>(populationSize);
        for (int i = 0; i < populationSize; i++) {
            S newSolution = (S) problem.createSolution();

            problem.evaluate(newSolution);
            population.add(newSolution);
        }
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

    private List<PermutationSolution<Integer>> addNew4FactoryVectorByRandom(List<PermutationSolution<Integer>> arr, ArrayList<ST> list) {
        ST s;
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        List<PermutationSolution<Integer>> offspring = new ArrayList<>(1);

        offspring.add((PermutationSolution<Integer>) arr.get(0).copy());
        for (int i = 0; i < list.size(); i++) {
            s = list.get(i);
            int r = random.nextInt(3);
            //工厂序号分别是 0，1，2 所以生成0-3但不包括3的随机整数来进行突变
            exchangeIndex4FactoryVectorByRandom(offspring.get(0), s.getX(), r);             //   随机选一位数进行改变
        }
        return offspring;
    }

    private void exchangeIndex4FactoryVectorByRandom(PermutationSolution<Integer> a, int index1, int value) {     //交换值
        a.setVariableValueid(index1, value);
    }

    @Override
    public String getName() {
        return "MOEAD";
    }

    @Override
    public String getDescription() {
        return "Multi-Objective Evolutionary Algorithm based on Decomposition";
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
