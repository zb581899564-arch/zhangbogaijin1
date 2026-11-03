package org.uma.jmetal.solution.impl;

import org.uma.jmetal.problem.PermutationProblem;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;

import java.io.*;
import java.util.*;

/**
 * Defines an implementation of solution composed of a permuation of integers
 *
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 */
@SuppressWarnings("serial")
public class DefaultIntegerPermutationSolution                     //编码
    extends AbstractGenericSolutionWithid<Integer, PermutationProblem<?>>
    implements PermutationSolution<Integer> {

  public static int[][][] result;
  protected int problemflag ;

  public PermutationProblem<?> getSchedulingProblem() { return problem; }

  static int n = 0;  // 工厂数
  static int s = 0;  // 阶段数
  static int j = 0;  // 阶段数

  //protected int[][] timeMatrix_;     // 时间矩阵（问题集中的内容）
  //protected int[] timeArray1;      //一维时间和
//  protected int[][] jobindex = new int[500][500];





  /** Constructor */
  public DefaultIntegerPermutationSolution(PermutationProblem<?> problem) {
    super(problem);
    org.uma.jmetal.util.research.model.Instance instance = ((org.uma.jmetal.util.research.SchedulingProblemData) problem).getSchedulingInstance();
    org.uma.jmetal.util.research.SchedulingEncoding.initialize(this, instance);
    result = new int[instance.factories()][instance.stages()][];
    for (int f = 0; f < instance.factories(); f++) {
      for (int k = 0; k < instance.stages(); k++) {
        result[f][k] = new int[instance.workers(f, k)];
        for (int w = 0; w < result[f][k].length; w++) result[f][k][w] = w;
      }
    }
    }

  /** Copy Constructor */
  public DefaultIntegerPermutationSolution(DefaultIntegerPermutationSolution solution) {
    super(solution.problem) ;
    for (int i = 0; i < problem.getNumberOfObjectives(); i++) {
      setObjective(i, solution.getObjective(i)) ;
    }

    for (int i = 0; i < problem.getNumberOfVariables(); i++) {
      setVariableValue(i, solution.getVariableValue(i));          //工件向量
    }

    for (int i = 0; i < problem.getNumberOfVariables(); i++) {
      setVariableValueid(i, solution.getVariableValueid(i));        //工厂向量
    }

//    for (int i = 0 ; i < problem.getNumberOfVariables(); i++){
//      setVariableValueworker(i,solution.getVariableValueworker(i));
//    }




    //todo

    for (int i = 0 ; i < solution.getNumberOfVariablesworker(); i++){
      setVariableValueworker(i,solution.getVariableValueworker(i));
    }
    getVariablesworker().removeIf(item->item==null);
    for (int i = 0; i < solution.getVariablesmachine().size(); i++) {
      setVariableValuemachine(i, solution.getVariableValuemachine(i));
    }
    attributes = new HashMap<Object, Object>(solution.attributes) ;
    attributes.put("worker", getVariablesworker());
    attributes.put("machine", getVariablesmachine());
  }



  @Override public String getVariableValueString(int index) {
    return getVariableValue(index).toString();
  }

  @Override
  public DefaultIntegerPermutationSolution copy() {
    return new DefaultIntegerPermutationSolution(this);
  }

	@Override
	public Map<Object, Object> getAttributes() {
		return attributes;
	}


  public static void shuffleArray(int[] array) {
    Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
    for (int i = array.length - 1; i > 0; i--) {
      // 随机选择一个索引 j，使得 0 <= j <= i
      int j = random.nextInt(i + 1);

      // 交换 array[i] 和 array[j]
      int temp = array[i];
      array[i] = array[j];
      array[j] = temp;
    }
  }


  public static List<Integer> readfile(String s){
    List<Integer> numbers = new ArrayList<>();
    String filePath = s;
    String targetLine = "number of workers in each factory:";

    try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
      String line;
      boolean foundTargetLine = false;

      while ((line = br.readLine()) != null) {
        if (foundTargetLine) {
          String[] parts = line.split(",");
          for (String part : parts) {
            try {
              int number = Integer.parseInt(part.trim());
              numbers.add(number);
            } catch (NumberFormatException e) {
            }
          }
          break;
        }
        if (line.trim().equals(targetLine)) {
          foundTargetLine = true;
        }
      }
      if (!foundTargetLine) {
      } else {
        // 如果找到了目标行但没有下一行
        if (line == null) {
        }
      }
    } catch (IOException e) {
      e.printStackTrace();
    }
    return numbers;
  }


  public static int[][] readFactoryData(String filePath) {
    BufferedReader br = null;
    int[][] numberOfMachines = null;

    try {
      br = new BufferedReader(new FileReader(filePath));
      String firstLine = br.readLine();
      String[] firstLineParts = firstLine.split(" ");
      n = Integer.parseInt(firstLineParts[0]);  // 工厂数
      s = Integer.parseInt(firstLineParts[1]);  // 阶段数
      j = Integer.parseInt(firstLineParts[2]);  // 工件数

      numberOfMachines = new int[n][s];

      String line;
      boolean foundHeader = false;
      int factoryIndex = 0;  // 用于记录当前工厂的索引
      while ((line = br.readLine()) != null) {
        if (line.equals("number of machines at each stage in each factory:")) {
          foundHeader = true;
          continue;
        }

        if (foundHeader && factoryIndex < n) {
          String[] parts = line.split(",");
          for (int i = 0; i < parts.length; i++) {
            numberOfMachines[factoryIndex][i] = Integer.parseInt(parts[i].trim());
          }
          factoryIndex++;
        }
      }
    } catch (IOException e) {
      e.printStackTrace();
    } finally {
      if (br != null) {
        try {
          br.close();
        } catch (IOException e) {
          e.printStackTrace();
        }
      }
    }

    return numberOfMachines;
  }

  //工件均匀分布到机器
  public static int[]  encodeMachineSelectionEvenly(int[][] numberOfMachines, List<Integer> VariableValueid) {

    int j = VariableValueid.size();  // 工件数
    int s = 1;  // 阶段数，这里仍然假设只有一个阶段
    int[] machineSelection = new int[s * j];

    for (int stage = 0; stage < s; stage++) {
      Map<Integer, List<Integer>> factoryToJobs = new HashMap<>();

      // 分配工件到各工厂
      for (int job = 0; job < j; job++) {
        int factory = VariableValueid.get(job);
        factoryToJobs.computeIfAbsent(factory, k -> new ArrayList<>()).add(job);
      }



      // 对每个工厂进行均匀分配
      for (Map.Entry<Integer, List<Integer>> entry : factoryToJobs.entrySet()) {
        int factory = entry.getKey();
        List<Integer> jobs = entry.getValue();
        int machineCount = numberOfMachines[factory][stage];
        int jobsPerMachine = jobs.size() / machineCount;  // 每个机器应分配的标准工件数
        int extraJobs = jobs.size() % machineCount;  // 额外的工件数

        // 均匀分配工件到机器
        int machineIndex = 0;
        for (int i = 0; i < jobs.size(); i++) {
          if (i < extraJobs) {
            machineIndex = i % machineCount;  // 前extraJobs个工件分配时，每台机器多分配一个工件
          } else {
            machineIndex = (i - extraJobs) / jobsPerMachine;  // 剩余工件按照标准数量分配
          }
          int jobIndex = jobs.get(i);
          machineSelection[stage * j + jobIndex] = machineIndex;
        }
      }
    }

    return machineSelection;
  }

  //工件随机分布到机器
  public static int[] encodeMachineSelectionRandomly(int[][] numberOfMachines, List<Integer> factorySelection) {


    int j = factorySelection.size();  // 工件数
    int[] machineSelection = new int[j];
    Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();

    for (int job = 0; job < j; job++) {
      int factory = factorySelection.get(job);  // 获取工件选择的工厂编号
      int machineCount = numberOfMachines[factory][0];  // 获取该工厂第一阶段的机器数

      if (machineCount == 0) {
        throw new IllegalArgumentException("Factory " + factory + " has no machines in the first stage.");
      }

      // 随机分配工件到该工厂的第一阶段的某台机器
      int assignedMachine = random.nextInt(machineCount);
      machineSelection[job] = assignedMachine;
    }
//    System.out.println(Arrays.toString(machineSelection));
//    System.out.println(factorySelection);
//
//    try {
//      Thread.sleep(999999);
//    } catch (InterruptedException e) {
//      throw new RuntimeException(e);
//    }


    return machineSelection;
  }

	//增加的部分（没用到，不需要）
  /*
  @Override
  public Integer getVariableValueid(int index) {
    return variablesid.get(index);
  }

  @Override
  public List<Integer> getVariablesid() {
    return variablesid;
  }

  @Override
  public void setVariableValueid(int index, Integer value) {
    variablesid.set(index, value);
  }

  @Override
  public int getNumberOfVariablesid() {
    return variablesid.size();
  }

   */

}
