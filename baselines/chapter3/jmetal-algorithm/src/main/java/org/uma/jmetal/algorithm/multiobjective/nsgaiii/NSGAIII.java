//package org.uma.jmetal.algorithm.multiobjective.nsgaiii;
//
//import org.uma.jmetal.algorithm.impl.AbstractGeneticAlgorithm;
//import org.uma.jmetal.algorithm.multiobjective.mypso.util.ST;
//import org.uma.jmetal.algorithm.multiobjective.nsgaiii.util.EnvironmentalSelection;
//import org.uma.jmetal.algorithm.multiobjective.nsgaiii.util.ReferencePoint;
//import org.uma.jmetal.problem.multiobjective.dfsp.DHFSP;
//import org.uma.jmetal.solution.DoubleSolution;
//import org.uma.jmetal.solution.PermutationSolution;
//import org.uma.jmetal.solution.Solution;
//import org.uma.jmetal.util.JMetalLogger;
//import org.uma.jmetal.util.SolutionListUtils;
//import org.uma.jmetal.util.evaluator.SolutionListEvaluator;
//import org.uma.jmetal.util.pseudorandom.JMetalRandom;
//import org.uma.jmetal.util.solutionattribute.Ranking;
//import org.uma.jmetal.util.solutionattribute.impl.DominanceRanking;
//
//import java.util.ArrayList;
//import java.util.List;
//import java.util.Random;
//import java.util.Vector;
//
///**
// * Created by ajnebro on 30/10/14.
// * Modified by Juanjo on 13/11/14
// *
// * This implementation is based on the code of Tsung-Che Chiang
// * http://web.ntnu.edu.tw/~tcchiang/publications/nsga3cpp/nsga3cpp.htm
// */
//@SuppressWarnings("serial")
//public class NSGAIII<S extends Solution<?>> extends AbstractGeneticAlgorithm<S, List<S>> {
//  protected int iterations ;
//  protected int maxIterations ;
//  protected int evaluations;
//  protected SolutionListEvaluator<S> evaluator ;
//
//  protected JMetalRandom randomGenerator ;
//
//  protected Vector<Integer> numberOfDivisions  ;
//  protected List<ReferencePoint<S>> referencePoints = new Vector<>() ;
//
//  /** Constructor */
//  public NSGAIII(NSGAIIIBuilder<S> builder) { // can be created from the NSGAIIIBuilder within the same package
//    super(builder.getProblem()) ;
//    maxIterations = builder.getMaxIterations() ;
//
//    crossoverOperator =  builder.getCrossoverOperator() ;
//    mutationOperator  =  builder.getMutationOperator() ;
////    selectionOperator =  builder.getSelectionOperator() ;
//
//    evaluator = builder.getEvaluator() ;
//
//    /// NSGAIII
//    numberOfDivisions = new Vector<>(1) ;
//    numberOfDivisions.add(12) ; // Default value for 3D problems
//
//    (new ReferencePoint<S>()).generateReferencePoints(referencePoints,getProblem().getNumberOfObjectives() , numberOfDivisions);
//
//    int populationSize = referencePoints.size();
//    while (populationSize%4>0) {
//      populationSize++;
//    }
//
//    setMaxPopulationSize(populationSize);
//
//    JMetalLogger.logger.info("rpssize: " + referencePoints.size()); ;
//  }
//
//  @Override
//  protected void initProgress() {
//    evaluations = getMaxPopulationSize();
//  }
//
//  @Override
//  protected void updateProgress() {
//    evaluations = evaluations + getMaxPopulationSize();
//  }
//
//  @Override
//  protected boolean isStoppingConditionReached() {
//    return iterations >= maxIterations;
//  }
//
//  @Override
//  protected List<S> evaluatePopulation(List<S> population) {
//    population = evaluator.evaluate(population, getProblem());
//
//    return population;
//  }
//
//  @Override
//  protected List<S> selection(List<S> population) {
//    List<S> matingPopulation = new ArrayList<>(population.size()) ;
//    for (int i = 0; i < getMaxPopulationSize(); i++) {
//      S solution = (S) selectionOperator.execute((List<DoubleSolution>) population);
//      matingPopulation.add(solution) ;
//    }
//
//    return matingPopulation;
//  }
//
//  @Override
//  protected List<S> reproduction(List<S> population) {
////    List<S> offspringPopulation = new ArrayList<>(getMaxPopulationSize());
////    for (int i = 0; i < getMaxPopulationSize(); i+=2) {
////      List<S> parents = new ArrayList<>(2);
////      parents.add(population.get(i));
////      parents.add(population.get(Math.min(i + 1, getMaxPopulationSize()-1)));
////
////      List<S> offspring = crossoverOperator.execute(parents);
////
////      mutationOperator.execute(offspring.get(0));
////      mutationOperator.execute(offspring.get(1));
////
////      offspringPopulation.add(offspring.get(0));
////      offspringPopulation.add(offspring.get(1));
////    }
//
//
//
//    int numberOfParents = crossoverOperator.getNumberOfRequiredParents();
//
//    checkNumberOfParents(population, numberOfParents);
//
//    List<S> offspringPopulation = new ArrayList<>(getMaxPopulationSize());
//    for (int i = 0; i < population.size(); i += numberOfParents) {
////            int crossoverflag = 0;
////            int mutationflag = 0;
////
////            Random random = new Random();
////            double c, m;
////            c = random.nextDouble();
////
////            List<S> parents = new ArrayList<>(numberOfParents);
////            for (int j = 0; j < numberOfParents; j++) {
////                parents.add(population.get(i + j));
////            }
////
//////            System.out.println(parents);
////            List<S> offspring = crossoverOperator.execute(parents);
//////
//////            System.out.println(offspring);
//////            try {
//////                Thread.sleep(99999);
//////            } catch (InterruptedException e) {
//////                throw new RuntimeException(e);
//////            }
////
////            //新加对工厂向量的交叉操作
////            if (c < Cross_c) {
////                offspring=(List<S>) getCrossOfFactoryVectorBySingle((List<PermutationSolution<Integer>>) parents);    //单点交叉
////                for (S s : offspring) {
////                    exchange4WorkerSequence((PermutationSolution<Integer>) s);
////                }
////            }
////            crossoverflag = crossoverOperator.getCrossoverProbabilityflag();
////
////            for (S s : offspring) {
////                mutationOperator.execute(s);
////
////                ///////新加对工厂变异操作
////                m = random.nextDouble();
////                ArrayList<ST> listV1 = new ArrayList<>();
////                if (m < Mutation_m) {
////                    ST q = new ST(randomGenerator.nextInt(0, s.getNumberOfVariables() - 1));
////                    listV1.add(q);
////                    addNew4FactoryVectorByRandom((PermutationSolution<Integer>) s, listV1,i);
////
////                }
////
////                mutationflag = mutationflag + mutationOperator.getMutationProbabilityflag();
////
////                offspringPopulation.add(s);
////                if (offspringPopulation.size() >= offspringPopulationSize)
////                    break;
////            }
////
////
////            if (crossoverflag == 1) {
////                evaluations = evaluations + 2;
////            } else {
////                evaluations = evaluations + mutationflag;
////            }
//
//      //20241228
//      Random random = new Random();
//      double c = random.nextDouble();
//      double m = random.nextDouble();
//      int crossoverflag = 0;
//      int mutationflag = 0;
//      int[] nw = DHFSP.nw;
//
//      List<S> parents = new ArrayList<>(numberOfParents);  //numberOfParents = 2
//      for (int j = 0; j < numberOfParents; j++) {
//        parents.add(population.get(i + j));
//      }
//
//
//      List<S> offspring = crossoverOperator.execute(parents);
//      double Cross_c = 0.3;
//      double CrossoverRates4worker= 0.3;
//      double CrossoverRates4machine= 0.3;
//      double Mutation_m= 0.3;
//      double mutationRate4worker= 0.3;
//      double mutationRate4machine= 0.3;
//      if (c < Cross_c) {
//        offspring=(List<S>) getCrossOfFactoryVectorBySingle((List<PermutationSolution<Integer>>) parents);    //单点交叉
//      }
//      double c_worker = random.nextDouble();
//      if (c_worker < CrossoverRates4worker) {
//        offspring = (List<S>) crossover4workersequence((List<PermutationSolution<Integer>>) offspring, nw);//工人向量交叉
//      }
//      double c_machine = random.nextDouble();
//      if (c_machine < CrossoverRates4machine) {
//        offspring= (List<S>) crossover4machinesequence((List<PermutationSolution<Integer>>) offspring);
//      }
//
//      crossoverflag = crossoverOperator.getCrossoverProbabilityflag();
//
//      //变异
//      for (S s : offspring) {
//        mutationOperator.execute(s);
//
//        ///////新加对工厂变异操作
//        m = random.nextDouble();
//        ArrayList<ST> listV1 = new ArrayList<>();
//        if (m < Mutation_m) {
//          ST q = new ST(randomGenerator.nextInt(0, s.getNumberOfVariables() - 1));
//          listV1.add(q);
//          addNew4FactoryVectorByRandom((PermutationSolution<Integer>) s, listV1,i);
//        }
//
//        double m_worker = random.nextDouble();
//        if (m_worker < mutationRate4worker){
//          mutation4worker((PermutationSolution<Integer>) s);
//        }
//        double m_machine = random.nextDouble();
//        if (m_machine < mutationRate4machine) {
//          mutation4machine((PermutationSolution<Integer>) s);
//        }
//
//
//
//        mutationflag = mutationflag + mutationOperator.getMutationProbabilityflag();
//
//        offspringPopulation.add(s);
//        if (offspringPopulation.size() >= getMaxPopulationSize())
//          break;
//      }
//
//
//      if (crossoverflag == 1) {
//
//        evaluations = evaluations + 2;
//      } else {
//        evaluations = evaluations + mutationflag;
//      }
//
//    }
//    return offspringPopulation;
//
//
//
//  }
//
//
//  private List<ReferencePoint<S>> getReferencePointsCopy() {
//	  List<ReferencePoint<S>> copy = new ArrayList<>();
//	  for (ReferencePoint<S> r : this.referencePoints) {
//		  copy.add(new ReferencePoint<>(r));
//	  }
//	  return copy;
//  }
//
//  @Override
//  protected List<S> replacement(List<S> population, List<S> offspringPopulation) {
//
//	List<S> jointPopulation = new ArrayList<>();
//    jointPopulation.addAll(population) ;
//    jointPopulation.addAll(offspringPopulation) ;
//
//    Ranking<S> ranking = computeRanking(jointPopulation);
//
//    //List<Solution> pop = crowdingDistanceSelection(ranking);
//    List<S> pop = new ArrayList<>();
//    List<List<S>> fronts = new ArrayList<>();
//    int rankingIndex = 0;
//    int candidateSolutions = 0;
//    while (candidateSolutions < getMaxPopulationSize()) {
//      fronts.add(ranking.getSubfront(rankingIndex));
//      candidateSolutions += ranking.getSubfront(rankingIndex).size();
//      if ((pop.size() + ranking.getSubfront(rankingIndex).size()) <= getMaxPopulationSize())
//        addRankedSolutionsToPopulation(ranking, rankingIndex, pop);
//      rankingIndex++;
//    }
//
//    // A copy of the reference list should be used as parameter of the environmental selection
//    EnvironmentalSelection<S> selection =
//            new EnvironmentalSelection<>(fronts,getMaxPopulationSize(),getReferencePointsCopy(),
//                    getProblem().getNumberOfObjectives());
//
//    pop = selection.execute(pop);
//
//    return pop;
//  }
//
//  @Override
//  public List<S> getResult() {
//    return getNonDominatedSolutions(getPopulation()) ;
//  }
//
//  protected Ranking<S> computeRanking(List<S> solutionList) {
//    Ranking<S> ranking = new DominanceRanking<>() ;
//    ranking.computeRanking(solutionList) ;
//
//    return ranking ;
//  }
//
//  protected void addRankedSolutionsToPopulation(Ranking<S> ranking, int rank, List<S> population) {
//    List<S> front ;
//
//    front = ranking.getSubfront(rank);
//
//    for (int i = 0 ; i < front.size(); i++) {
//      population.add(front.get(i));
//    }
//  }
//
//  protected List<S> getNonDominatedSolutions(List<S> solutionList) {
//    return SolutionListUtils.getNondominatedSolutions(solutionList) ;
//  }
//
//  @Override public String getName() {
//    return "NSGAIII" ;
//  }
//
//  @Override public String getDescription() {
//    return "Nondominated Sorting Genetic Algorithm version III" ;
//  }
//
//
//  public static List<PermutationSolution<Integer>> crossover4workersequence(List<PermutationSolution<Integer>> parents, int[] nw) {
//    PermutationSolution<Integer> HisOptIndividual = parents.get(0);
//    PermutationSolution<Integer> particle = parents.get(1);
//    List<Integer> a1 = HisOptIndividual.getVariablesworker();
//    List<Integer> a2 = particle.getVariablesworker();
//    if (a1 == null || a2 == null || nw == null || a1.isEmpty() || a2.isEmpty() || nw.length == 0) {
//      throw new IllegalArgumentException("Lists and steps array must not be null or empty");
//    }
//
//    // 确保两个列表长度相同
//    if (a1.size() != a2.size()) {
//      throw new IllegalArgumentException("Lists must have the same length");
//    }
//
//    // 计算分块的起始和结束位置
//    List<int[]> blocks = calculateBlocks(nw, a1.size());
//
//    // 随机选择一个分块
//    Random random = new Random();
//    int blockIndex = random.nextInt(blocks.size());
//
//
//    // 获取选中的分块范围
//    int[] selectedBlock = blocks.get(blockIndex);
//    int start = selectedBlock[0];
//    int end = selectedBlock[1];
//
//    // 交换分块内容
//    swapBlocks(a1, a2, start, end);
//    for (int i2 = 0; i2 < a2.size(); i2++) {
//      particle.setVariableValueworker(i2,a2.get(i2));
//    }
//
//    return parents;
//  }
//
//  private static List<int[]> calculateBlocks(int[] nw, int listSize) {
//    List<int[]> blocks = new ArrayList<>();
//    int currentIndex = 0;
//
//    for (int step : nw) {
//      if (currentIndex < listSize) {
//        int endIndex = Math.min(currentIndex + step, listSize);
//        blocks.add(new int[]{currentIndex, endIndex});
//        currentIndex = endIndex;
//      }
//    }
//
//    // 处理剩余部分，如果有的话
//    if (currentIndex < listSize) {
//      blocks.add(new int[]{currentIndex, listSize});
//    }
//
//    return blocks;
//  }
//
//  private static void swapBlocks(List<Integer> a1, List<Integer> a2, int start, int end) {
//    // 创建临时列表来保存 a1 的分块
//    List<Integer> temp = new ArrayList<>(a1.subList(start, end));
//
//    // 用 a2 的分块替换 a1 的分块
//    for (int i = start; i < end; i++) {
//      a1.set(i, a2.get(i));
//    }
//
//    // 用 a1 的分块（现在在 temp 中）替换 a2 的分块
//    for (int i = start; i < end; i++) {
//      a2.set(i, temp.get(i - start));
//    }
//  }
//
//
//  private List<PermutationSolution<Integer>> crossover4machinesequence(List<PermutationSolution<Integer>> offspring) {
//    PermutationSolution<Integer> integerPermutationSolution = offspring.get(0);
//    PermutationSolution<Integer> particle = offspring.get(1);
//
//
//    ArrayList<Integer> machineintegerPermutationSolution = (ArrayList<Integer>) integerPermutationSolution.getAttribute("machine");
//    ArrayList<Integer> machineparticle = (ArrayList<Integer>) particle.getAttribute("machine");;
//
//    List<Integer> integerPermutationSolutionfactory = integerPermutationSolution.getVariablesid();
//    List<Integer> particlefactory = particle.getVariablesid();
//
//    Random r = new Random();
//    int max = r.nextInt(machineintegerPermutationSolution.size()-1);
//    int min = r.nextInt(machineintegerPermutationSolution.size()-1);
//    if (max<min){
//      int temp = 0;
//      temp = max;
//      max = min;
//      min = temp;
//    }
//    List<Integer> machinetemp1 = new ArrayList<>(machineintegerPermutationSolution.subList(min, max + 1));
//    List<Integer> machinetemp2 = new ArrayList<>(machineparticle.subList(min, max + 1));
//
//    List<Integer> factorytemp1 = new ArrayList<>(integerPermutationSolutionfactory.subList(min, max + 1));
//    List<Integer> factorytemp2 = new ArrayList<>(particlefactory.subList(min, max + 1));
//
//    int[][] numberOfMachines = DHFSP.numberOfMachines_;
//    for (int i = 0; i < machinetemp1.size(); i++) {
//      if (factorytemp1.get(i)==factorytemp2.get(i)){
//        int temp1 = machinetemp1.get(i);
//        int temp2 = machinetemp2.get(i);
//        machinetemp2.set(i,temp1);
//        machinetemp1.set(i,temp2);
//      }
//      else {
//        int temp1 =numberOfMachines[factorytemp1.get(i)][0];
//        temp1 = r.nextInt(temp1);
//        machinetemp1.set(i,temp1);
//
//        int temp2 =numberOfMachines[factorytemp2.get(i)][0];
//        temp2 = r.nextInt(temp2);
//        machinetemp2.set(i,temp2);
//      }
//    }
//    for (int i = 0; i < machinetemp1.size(); i++) {
//      machineparticle.set(min,machinetemp2.get(i));
//      min++;
//    }
//
//    particle.setAttribute("machine",machineparticle);
//    return offspring;
//  }
//
//  //工人变异
//  private void mutation4worker(PermutationSolution<Integer> particle){
//    List<Integer> variablesworker = particle.getVariablesworker();
//    int[] nw = DHFSP.nw;
//    Random random = new Random();
//    List<List<Integer>> blocks = splitIntoBlocks(variablesworker, nw);
//
//    // 2. 随机选择一个分块
//    int selectedBlockIndex = random.nextInt(blocks.size());
//    List<Integer> selectedBlock = blocks.get(selectedBlockIndex);
//
//    // 3. 在选中的分块中随机选择两个位置的元素进行交换
//    if (selectedBlock.size() > 1) {  // 确保分块中有足够的元素可以交换
//      int pos1 = random.nextInt(selectedBlock.size());
//      int pos2 = random.nextInt(selectedBlock.size());
//      while (pos1 == pos2) {  // 确保两个位置不同
//        pos2 = random.nextInt(selectedBlock.size());
//      }
//
//      // 交换两个位置的元素
//      int temp = selectedBlock.get(pos1);
//      selectedBlock.set(pos1, selectedBlock.get(pos2));
//      selectedBlock.set(pos2, temp);
//    }
//
//    // 4. 将所有分块重新合并为一个列表
//    List<Integer> result = new ArrayList<>();
//    for (List<Integer> block : blocks) {
//      result.addAll(block);
//    }
//
//    for (int i = 0; i < result.size(); i++) {
//      particle.setVariableValueworker(i,result.get(i));
//    }
//  }
//
//  // 根据 nw 数组对 variablesworker 列表进行划分
//  private static List<List<Integer>> splitIntoBlocks(List<Integer> variablesworker, int[] nw) {
//    List<List<Integer>> blocks = new ArrayList<>();
//    int currentIndex = 0;
//
//    for (int size : nw) {
//      // 创建一个新的分块
//      List<Integer> block = new ArrayList<>(variablesworker.subList(currentIndex, currentIndex + size));
//      blocks.add(block);
//      currentIndex += size;
//    }
//
//    return blocks;
//  }
//
//
//  //机器变异
//  private void mutation4machine(PermutationSolution<Integer> particle) {
//    ArrayList<Integer> machine = (ArrayList<Integer>) particle.getAttribute("machine");
//    List<Integer> variablesid = particle.getVariablesid();
//    Random r = new Random();
//    int i = r.nextInt(machine.size());
//    int tempfactory = variablesid.get(i);
//    int[][] numberOfMachines = DHFSP.numberOfMachines_;
//    int numberOfMachine = numberOfMachines[tempfactory][0];
//
//    int temp = r.nextInt(numberOfMachine);
//    machine.set(numberOfMachine,temp);
//    particle.setAttribute("machine",machine);
//  }
//
//  private List<PermutationSolution<Integer>> getCrossOfFactoryVectorBySingle(List<PermutationSolution<Integer>> parents) {       //对工厂向量进行单点交叉
//    int index;
//    Random random = new Random();
//    List<PermutationSolution<Integer>> offspring = new ArrayList<>(2);
//
//    offspring.add((PermutationSolution<Integer>) parents.get(0).copy()) ;
//    offspring.add((PermutationSolution<Integer>) parents.get(1).copy()) ;
//    int boundflag = random.nextInt(offspring.get(1).getNumberOfVariablesid());          //  随机产生一个单点下标
//    for (int i = boundflag; i < offspring.get(1).getNumberOfVariablesid(); i++) {
//      index = i;
//      cross4FactoryVectorBySingle(offspring.get(0), offspring.get(1), i, index);   //交换下标i与下标index的值
//    }
//    return offspring;
//  }
//
//  private void cross4FactoryVectorBySingle(PermutationSolution<Integer> a,PermutationSolution<Integer> b, int index1, int index2) {     //交换值
//    int temp1 = a.getVariableValueid(index1);    //工厂
//    int temp2 = b.getVariableValueid(index2);
//
//    a.setVariableValueid(index1, temp2);
//    b.setVariableValueid(index2, temp1);
//  }
//
//  private void addNew4FactoryVectorByRandom(PermutationSolution<Integer> arr, ArrayList<ST> list,int i) {
//    ST s;
//    Random random = new Random();
//
///*        List<PermutationSolution<Integer>> offspring = new ArrayList<>(1);
//        offspring.add((PermutationSolution<Integer>) arr.copy()) ;*/
//
//    for (int j = 0; j < list.size(); j++) {
//      s = list.get(j);
//      int r = random.nextInt(3);
//      //工厂序号分别是 0，1，2 所以生成0-3但不包括3的随机整数来进行突变
//      exchangeIndex4FactoryVectorByRandom(arr, s.getX(), r);             //   随机选一位数进行改变
//    }
//    //return offspring;
//  }
//
//  private void exchangeIndex4FactoryVectorByRandom(PermutationSolution<Integer> a, int index1, int value) {     //交换值
//    a.setVariableValueid(index1, value);
//  }
//
//
//}
