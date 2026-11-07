package org.uma.jmetal.util;

import org.uma.jmetal.qualityindicator.impl.*;
import org.uma.jmetal.qualityindicator.impl.hypervolume.PISAHypervolume;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.fileoutput.SolutionListOutput;
import org.uma.jmetal.util.fileoutput.impl.DefaultFileOutputContext;
import org.uma.jmetal.util.front.Front;
import org.uma.jmetal.util.front.imp.ArrayFront;
import org.uma.jmetal.util.front.util.FrontNormalizer;
import org.uma.jmetal.util.front.util.FrontUtils;
import org.uma.jmetal.util.point.PointSolution;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;

import java.io.BufferedWriter;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;

/**
 * Abstract class for Runner classes
 *
 * @author Antonio J. Nebro <antonio@lcc.uma.es>
 */
public abstract class AbstractAlgorithmRunner {
  /**
   * Write the population into two files and prints some data on screen
   * @param population
   */
  public static void printFinalSolutionSet(List<? extends Solution<?>> population) {

    new SolutionListOutput(population)
        .setSeparator("\t")
        .setVarFileOutputContext(new DefaultFileOutputContext("VAR.tsv"))
        .setFunFileOutputContext(new DefaultFileOutputContext("FUN.tsv"))
        .print();

    JMetalLogger.logger.info("Random seed: " + JMetalRandom.getInstance().getSeed());
    JMetalLogger.logger.info("Objectives values have been written to file FUN.tsv");
    JMetalLogger.logger.info("Variables values have been written to file VAR.tsv");
  }

  /**
   * Print all the available quality indicators
   * @param population
   * @param paretoFrontFile
   * @throws FileNotFoundException
   */
  public static <S extends Solution<?>> void printQualityIndicators(List<S> population, String paretoFrontFile)   //自带函数，直接输出指标
      throws FileNotFoundException {
    Front referenceFront = new ArrayFront(paretoFrontFile);
    FrontNormalizer frontNormalizer = new FrontNormalizer(referenceFront) ;
  //  FrontNormalizer frontNormalizer1 = new FrontNormalizer(population) ; //现加的

    Front normalizedReferenceFront = frontNormalizer.normalize(referenceFront) ;//标准化前沿面
    Front normalizedFront = frontNormalizer.normalize(new ArrayFront(population)) ;//标准化种群
    List<PointSolution> normalizedPopulation = FrontUtils
        .convertFrontToSolutionList(normalizedFront) ;//将标准化种群转成数组形式

    String outputString = "\n" ;
    outputString += "Hypervolume (N) : " +
        new PISAHypervolume<PointSolution>(normalizedReferenceFront).evaluate(normalizedPopulation) + "\n";
    outputString += "Hypervolume     : " +
        new PISAHypervolume<S>(referenceFront).evaluate(population) + "\n";
    outputString += "Epsilon (N)     : " +
        new Epsilon<PointSolution>(normalizedReferenceFront).evaluate(normalizedPopulation) +
        "\n" ;
    outputString += "Epsilon         : " +
        new Epsilon<S>(referenceFront).evaluate(population) + "\n" ;  //找种群中的点和前沿面个体的适应度值差距最大的那个。每个适应度中的最大，和前沿面个体的最小，种群中的最大。
    outputString += "GD (N)          : " +
        new GenerationalDistance<PointSolution>(normalizedReferenceFront).evaluate(normalizedPopulation) + "\n"; //种群中的每个点到前沿面的距离差的平方和，求平方根，再单位化。
    outputString += "GD              : " +
        new GenerationalDistance<S>(referenceFront).evaluate(population) + "\n";
    outputString += "IGD (N)         : " +
        new InvertedGenerationalDistance<PointSolution>(normalizedReferenceFront).evaluate(normalizedPopulation) + "\n"; //前沿面中的每个点到种群的距离差的平方和，求平方根，再单位化。
    outputString +="IGD             : " +
        new InvertedGenerationalDistance<S>(referenceFront).evaluate(population) + "\n";
    outputString += "IGD+ (N)        : " +
        new InvertedGenerationalDistancePlus<PointSolution>(normalizedReferenceFront).evaluate(normalizedPopulation) + "\n"; //前沿面中的每个点到种群的距离差之和，再单位化。
    outputString += "IGD+            : " +
        new InvertedGenerationalDistancePlus<S>(referenceFront).evaluate(population) + "\n";
    outputString += "Spread (N)      : " +
        new Spread<PointSolution>(normalizedReferenceFront).evaluate(normalizedPopulation) + "\n";
    outputString += "Spread          : " +
        new Spread<S>(referenceFront).evaluate(population) + "\n";
//    outputString += "R2 (N)          : " +
//        new R2<List<DoubleSolution>>(normalizedReferenceFront).runAlgorithm(normalizedPopulation) + "\n";
//    outputString += "R2              : " +
//        new R2<List<? extends Solution<?>>>(referenceFront).runAlgorithm(population) + "\n";
    outputString += "Error ratio     : " +
        new ErrorRatio<List<? extends Solution<?>>>(referenceFront).evaluate(population) + "\n"; //ErrorRatio=种群中不在pareto上的点的个数/种群总个数；
    
    JMetalLogger.logger.info(outputString);
  }

  public static <S extends Solution<?>> void printQualityIndicatorstest(List<S> population, String paretoFrontFile, String algorithmname)     //自定义函数，输出指标到文件
          throws IOException {
    Front referenceFront = new ArrayFront(paretoFrontFile);
    FrontNormalizer frontNormalizer = new FrontNormalizer(referenceFront) ;
    //  FrontNormalizer frontNormalizer1 = new FrontNormalizer(population) ; //现加的

    Front normalizedReferenceFront = frontNormalizer.normalize(referenceFront) ;//标准化前沿面
    Front normalizedFront = frontNormalizer.normalize(new ArrayFront(population)) ;//标准化种群
    List<PointSolution> normalizedPopulation = FrontUtils
            .convertFrontToSolutionList(normalizedFront) ;//将标准化种群转成数组形式

    BufferedWriter bw = new BufferedWriter(new FileWriter("F:\\桌面杂项包\\0-PSO算法研究\\()--PSO-DE-DFSP\\"+algorithmname+"_数据.txt",true));

    bw.write("Hypervolume (N) : " +
            new PISAHypervolume<PointSolution>(normalizedReferenceFront).evaluate(normalizedPopulation)+" ");

    bw.write("GD (N)          : " +
            new GenerationalDistance<PointSolution>(normalizedReferenceFront).evaluate(normalizedPopulation)+" ");

    bw.write("IGD (N)         : " +
            new InvertedGenerationalDistance<PointSolution>(normalizedReferenceFront).evaluate(normalizedPopulation)+" ");

    bw.write("Spread (N)      : " +
            new Spread<PointSolution>(normalizedReferenceFront).evaluate(normalizedPopulation)+" ");
    bw.newLine();

    bw.flush();
    bw.close();

  }

  public static <S extends Solution<?>> void printQualityRanktest(List<S> population)         //自定义函数，输出Rank到文件
          throws IOException {

    List<S> populationtemp = population;
    int[][] dominancetimes = new int[populationtemp.size()][populationtemp.size()+1];
    int[] dominanceRank = new int[populationtemp.size()];

    for(int i=0;i<populationtemp.size();i++){
      for(int j=0;j<populationtemp.size();j++){
        if(i!=j){
          if(populationtemp.get(i).getObjective(1)>populationtemp.get(j).getObjective(1) && populationtemp.get(i).getObjective(0)>populationtemp.get(j).getObjective(0) ){
            dominancetimes[i][0] = dominancetimes[i][0]+1; //计算被支配数
            dominancetimes[i][dominancetimes[i][0]] = j; //记录被那些个体支配
          }
        }
      }
    }

    for(int i=0;i<populationtemp.size();i++){
      for(int j=1;j<dominancetimes[i][0];j++){
        dominanceRank[i] = (1+dominancetimes[dominancetimes[i][j]][0]);
      }
      dominanceRank[i]++;
    }

    double sum = 0; //计算Rank和
    for(int i=0;i<populationtemp.size();i++){
      sum = sum+dominanceRank[i];
    }

    double Rankaverage = sum/populationtemp.size(); //计算Rank平均值

    BufferedWriter bw = new BufferedWriter(new FileWriter("C:\\Users\\Administrator\\Desktop\\测试数据\\Rank数据.txt",true));
    bw.write(String.valueOf(Rankaverage));//输出当代Rank平均值
    bw.newLine();
    /*
    for(int i=0;i<population.size();i++){
      bw.write(String.valueOf(populationtemp.get(i).getObjective(0) + ";" + populationtemp.get(i).getObjective(1)));
      bw.newLine();
    }

     */

    bw.flush();
    bw.close();

  }

  public static <S extends Solution<?>> void printQualityDensitytest(List<S> population,int fitnesscellsize1,int fitnesscellsize2)   //自定义函数，输出Densitytest到文件
          throws IOException {

    List<S> populationtemp = population;

    double fitness1max =0;
    double fitness1min =0;
    double fitness2max =0;
    double fitness2min =0;

    fitness1max = populationtemp.get(0).getObjective(0);
    fitness1min = populationtemp.get(0).getObjective(0);
    fitness2max = populationtemp.get(0).getObjective(1);
    fitness2min = populationtemp.get(0).getObjective(1);

    for(int i=1;i<populationtemp.size();i++){

      if(fitness1max<populationtemp.get(i).getObjective(0)){
        fitness1max = populationtemp.get(i).getObjective(0);
      }

      if(fitness1min>populationtemp.get(i).getObjective(0)){
        fitness1min = populationtemp.get(i).getObjective(0);
      }

      if(fitness2max<populationtemp.get(i).getObjective(1)){
        fitness2max = populationtemp.get(i).getObjective(1);
      }

      if(fitness2min>populationtemp.get(i).getObjective(1)){
        fitness2min = populationtemp.get(i).getObjective(1);
      }

    }

    int[][] denditytest = new int[fitnesscellsize1][fitnesscellsize2];
    double fitnessde1 = (fitness1max-fitness1min)/fitnesscellsize1;
    double fitnessde2 = (fitness2max-fitness2min)/fitnesscellsize2;
    //int[][] dendityplace = new int[populationtemp.size()][2];

    for(int i=0;i<populationtemp.size();i++){
      int a = (int) ((populationtemp.get(i).getObjective(0)-fitness1min)/fitnessde1);
      int b = (int) ((populationtemp.get(i).getObjective(1)-fitness2min)/fitnessde2);

      if(a>=fitnesscellsize1){
        a--;
      }
      if(b>=fitnesscellsize2){
        b--;
      }

      denditytest[a][b] = denditytest[a][b]+1;

      //dendityplace[i][0] = a;
     // dendityplace[i][1] = b;
    }

    double sum=0;
    for(int i=0;i<fitnesscellsize1;i++){
      for(int j=0;j<fitnesscellsize2;j++){
        sum = sum + denditytest[i][j] * denditytest[i][j];
      }
    }

    double averagedensity = (double) (sum/(fitnesscellsize1*fitnesscellsize2));

    BufferedWriter bw = new BufferedWriter(new FileWriter("C:\\Users\\Administrator\\Desktop\\测试数据\\Density数据.txt",true));
    bw.write(String.valueOf(averagedensity));//输出当代Rank平均值
    bw.newLine();
    bw.flush();
    bw.close();

  }

}
