package org.uma.jmetal.runner.lc_psode;

//import org.uma.jmetal.problem.multiobjective.dfsp.MNIFSP;

import org.uma.jmetal.problem.multiobjective.dfsp.*;
import org.uma.jmetal.qualityindicator.myqualityindicator.impl.Indexs;
import org.uma.jmetal.qualityindicator.myqualityindicator.util.UtilPareto;
import org.uma.jmetal.qualityindicator.myqualityindicator.util.UtilPopulation;
//import org.uma.jmetal.runner.myalgorithm.MOHEADERun;
import org.uma.jmetal.problem.PermutationProblem;
//import org.uma.jmetal.runner.myalgorithm.MOPSODivideSubgroupRun;
import org.uma.jmetal.solution.PermutationSolution;


import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;


public class  ALLAlgorithmRun {

    protected static int[]    jobIndexIds ;
    protected static int[]    stageIndexIds ;
    protected static int[]    factoryIndexIds;
    protected static int[]    machineIndexIds ;
    protected static int[]    problemIndexIds;
    protected static int runTime;
//    protected static int maxGen =50;
    protected static int maxGen =50;

    protected static int maxGen4myalgorgorithm = 20;
    //String[] algorithms = {"MOPSODSDE","MOPSODS","MOPSO","MOHEA","MOHEADE","NSGAII","SPEA2","MOEAD"};
    protected static   String[] algorithms;

    protected static  String solutionFolderNameNonparametric = "E:/DHFSP-4/data result/";//原始数据路径 //TODO 创建result-solution 保存生成的solution
//    protected static  String solutionFolderName = "E:/DHFSP/data result/";//原始数据路径 //TODO 创建result-solution 保存生成的solution

    protected static  String  solutionFolderName = "E:/DHFSP-4/50%/";//跑指标的时候
    protected static  String solutionFolderName1 = "E:/DHFSP-4/DOE/";//原始数据路径 //TODO 创建result-solution 保存生成的solution
    protected static  String indexFolderName = "E:/DHFSP-4/indicator data/";//指标数据路径//TODO 创建result-index 保存指标结果数据

    protected static PermutationProblem<PermutationSolution<Integer>> problem;
    protected static PermutationProblem<PermutationSolution<Integer>> problem1;

    protected static int[] swarmSizes;
    protected static double[] rangesOfR1R2;
    protected static double[] DERates;
    protected static   double[] crossoverRates;
    protected static  double[] mutationRates;
    protected static  double[] DEcrossoverRates;

    protected static double[]  crossoverRates4worker ;
    protected static double[]  mutationRates4worker ;
    protected static double[]  mutationRates4machine ;
    protected static double[]  crossoverRates4machine ;

//    protected static double[]  mutationRates4worker;

    protected static  double[] DEmutationRates;
    protected static  double[] pmxCrossover;

    protected static  double[] V1mutationProbability;

    protected static   boolean isFirstRun = false;
    protected static   boolean Nonparametric = false;

    //此代码不能同时跑原始数据和指标，所有原始数据跑完之后才能跑指标
    public static void main(String[] args) throws Exception {
        throw new IllegalStateException("Use scripts/run_baseline.py: legacy batch bypasses the model/budget contract");
    }

    private static void runAllMethods() throws Exception {
        //problemflag = new int[]{1, 2, 3, 4, 5, 6, 7};
//        jobIndexIds = new int[]{100}; //202110 测试DOE用，20211010
//        machineIndexIds = new int[]{10};//202110 测试DOE用，，20211010
//        problemIndexIds = new int[]{1};//202110 测试DOE用，，20211010

        jobIndexIds = new int[]{150};              //5,10,20,50,100
        //stageIndexIds = new int[]{2,5,8};          //2,5,8

        stageIndexIds = new int[]{8};
        //factoryIndexIds = new int[]{3,4,5};          //2,3,4,5,6\


        factoryIndexIds = new int[]{5};

        //machineIndexIds = new int[]{10};
        problemIndexIds = new int[]{1};

/*      jobIndexIds =       new int[]{20, 50, 100};
        machineIndexIds =   new int[]{5, 10, 20};
        problemIndexIds =   new int[]{1};*/

        //runTime =           10; //运行次数
        runTime =          20;


        //目标全 最好 目标差和目标123
        //algorithms =        new String[] {"MOPSODS-DE","MOPSODS","MOPSO","MOHEA","NSGAII","SPEA2","MOEAD"};
//        algorithms =        new String[] {"MAPSO-QLS","MOEA-LS","MOPSODS-DE","MOHEA-DE","SPEA2","NSGA-II","MOPSO"}; //这个  20241119这个是全部都跑
        algorithms =        new String[] {"QL-MOHPSO","MOPSODS-DE","MOHEA-DE","SPEA2","NSGA-II","MOPSO","MOHPSO-Q"}; //这个  20241119这个是除了主算法的对比算法
        //algorithms =        new String[] {"MAPSO-QLS", "MOPSODS-DE","MOHEA-DE","SPEA2","NSGA-II"}; //这个
//        algorithms =        new String[] {"MAPSO-QLS"};//20241119 这个是只有主算法
//        algorithms =        new String[] {"SPEA2"};//20250313 把NSGAII和SPEA2改好了
//        algorithms =        new String[] {"MOHPSO-Q"};//20250314 改MOEA-LS
//


//        algorithms =        new String[] {"MOPSO"};
        swarmSizes = new int[]{100}; //20211002 包含DE参数一起测试, 20211004结果 200最好
        rangesOfR1R2 = new double[]{0.4}; //20211020测试用   0.6
        crossoverRates = new double[]{0.2}; ////20241214
        mutationRates = new double[]{0.06}; ////20241214
        crossoverRates4worker = new double[]{0.4};//20241214
        crossoverRates4machine = new double[]{0.3};
        mutationRates4worker = new double[]{0.1};//20241214
        mutationRates4machine = new double[]{0.25};

        pmxCrossover= new double[]{40};            //Q迭代次数
        double[] DEcrossoverRates = new double[]{0.8};    //学习率
        double[] DEmutationRates = new double[]{0.9};     //贪婪率
        int[] localsearch= new int[]{40};     //局部搜索次数

        V1mutationProbability=new double[]{0};
        DERates=new double[]{0};

        isFirstRun = true; //运行算法时，改为 true,运行指标时，改为 false
//        isFirstRun = false;
//        Nonparametric= false;  //没有参数时，改为 true,有参数时，改为 false
        Nonparametric= true;  //没有参数时，改为 true,有参数时，改为 false
        //跑原数据
        if (isFirstRun) {
            for (int j = 0; j < jobIndexIds.length; j++) {
                for (int k = 0; k < stageIndexIds.length; k++) {
                    for (int i = 0; i < factoryIndexIds.length; i++) { //可能是problem id, 这里只用第一个问题
                        for (int p = 0; p < problemIndexIds.length; p++) {

                        //problem1 = (PermutationProblem<PermutationSolution<Integer>>) new DHFSP_MOEAD(jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i],problemIndexIds[0]);
                        //problem = (PermutationProblem<PermutationSolution<Integer>>) new DFSP3single(jobIndexIds[j], machineIndexIds[k], problemIndexIds[i]);
                        problem = (PermutationProblem<PermutationSolution<Integer>>) new EDHHFSPW(jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i],problemIndexIds[0]);
/*                            jobIndexIds = new int[]{10};              //5,10,20,50,100
                            stageIndexIds = new int[]{2};
                            factoryIndexIds = new int[]{3};
                            problemIndexIds = new int[]{1};*/
                        // allslgorithmexe(problem, numberOfJobs[j], numberOfMachines[k], snumber[0], SwarmSize[3] / 3, SwarmSize[3] -  (SwarmSize[3] / 3)*2, SwarmSize[3] / 3, Probability, SwarmSize[3], 500 * SwarmSize[3], datafile, indexfile);
                        //测试参数x
                        for (int m = 0; m < algorithms.length; m++) {
                            for (int r = 0; r < rangesOfR1R2.length; r++) {
                                for (int s = 0; s < swarmSizes.length; s++) {
                                    for (int t = 0; t < crossoverRates.length; t++) {
                                        for (int o = 0; o < mutationRates.length; o++) {
                                            for (int q = 0; q < pmxCrossover.length; q++) {
                                                for (int a = 0; a < V1mutationProbability.length; a++) {
                                                    for (int w = 0; w < DERates.length; w++) {
                                                        for (int z = 0; z < DEcrossoverRates.length; z++) {
                                                            for (int x = 0; x < DEmutationRates.length; x++) {
                                                                for (int u = 0; u < crossoverRates4worker.length; u++) {
                                                                    for (int c = 0; c < crossoverRates4machine.length; c++) {
                                                                        for (int b = 0; b < mutationRates4worker.length; b++) {
                                                                            for (int v = 0; v < mutationRates4machine.length; v++) {
                                                                                for (int d = 0; d < localsearch.length; d++) {
                                                                                    if (algorithms[m].equals("QL-MOHPSO")) { //我的算法
                                                                                        MOPSODivSubDERun.mainexe(problem,
                                                                                                jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
//                                                                            swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                                swarmSizes[s],
                                                                                                rangesOfR1R2[r],
                                                                                                crossoverRates[t], mutationRates[o], pmxCrossover[q], 0,
                                                                                                0, DEcrossoverRates[z], DEmutationRates[x], maxGen * swarmSizes[s], //100*50
                                                                                                solutionFolderNameNonparametric, indexFolderName, runTime, Nonparametric,crossoverRates4worker[u], crossoverRates4machine[c], mutationRates4worker[b], mutationRates4machine[v],
                                                                                                localsearch[d]);
                                                                                    }
                                                                                    if (algorithms[m].equals("MOHPSO-Q")) { //我的算法
                                                                                        MOHPSOQRun.mainexe(problem,
                                                                                                jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
//                                                                            swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                                swarmSizes[s],
                                                                                                rangesOfR1R2[r],
                                                                                                crossoverRates[t], mutationRates[o], pmxCrossover[q], 0,
                                                                                                0, DEcrossoverRates[z], DEmutationRates[x], maxGen * swarmSizes[s], //100*50
                                                                                                solutionFolderNameNonparametric, indexFolderName, runTime, Nonparametric,crossoverRates4worker[u], crossoverRates4machine[c], mutationRates4worker[b], mutationRates4machine[v],
                                                                                                localsearch[d]);
                                                                                    }
                                                                                    if (algorithms[m].equals("MOPSODSQDouble")) {

                                                                                        MOPSODS_QDoubleRun.mainexe(problem1,
                                                                                                jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                                //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                                swarmSizes[s],
                                                                                                0.4,
                                                                                                0.1, 0.02, 0, 0,
                                                                                                0, 0, 0, maxGen * swarmSizes[s],
                                                                                                solutionFolderNameNonparametric, indexFolderName, runTime, Nonparametric);
                                                                                    }
                                                                                    if (algorithms[m].equals("MOPSODSDE_Kmeans")) {

                                                                                        MOPSODSDE_KmeansRun.mainexe(problem,
                                                                                                jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                                //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                                swarmSizes[s],
                                                                                                rangesOfR1R2[r],
                                                                                                crossoverRates[t], mutationRates[o], pmxCrossover[q], 0,
                                                                                                DERates[w], DEcrossoverRates[z], DEmutationRates[x], maxGen * swarmSizes[s],
                                                                                                solutionFolderNameNonparametric, indexFolderName, runTime, Nonparametric);
                                                                                    }
                                                                                    if (algorithms[m].equals("MOPSODS_Kmeans")) {

                                                                                        MOPSODS_KmeansRun.mainexe(problem,
                                                                                                jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                                //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                                swarmSizes[s],
                                                                                                rangesOfR1R2[r],
                                                                                                crossoverRates[t], mutationRates[o], pmxCrossover[q], 0,
                                                                                                DERates[w], DEcrossoverRates[z], DEmutationRates[x], maxGen * swarmSizes[s],
                                                                                                solutionFolderNameNonparametric, indexFolderName, runTime, Nonparametric);
                                                                                    }
                                                                                    if (algorithms[m].equals("MOPSODS-DE")) {
                                                                                        MOPSODivSubRun.mainexe(problem,
                                                                                                jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                                //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                                swarmSizes[s],
                                                                                                0.4,
                                                                                                0.1, 0.02, 10, 0,
                                                                                                0, 0, 0,
                                                                                                0.4,0.3,0.1,0.25,
                                                                                                maxGen * swarmSizes[s],
                                                                                                solutionFolderNameNonparametric, indexFolderName, runTime, Nonparametric);
                                                                                    }

                                                                                    //MOPSORun.mainexe(problem,numberOfJobs,numberOfMachines,snumber,upSize,centralSize,downSize,Probability,SwarmSize,MaxIterations,datafile,indexfile);
                                                                                    if (algorithms[m].equals("MOPSO")) {
                                                                                        MOPSORun.mainexe(problem,
                                                                                                jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                                //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                                swarmSizes[s],
                                                                                                0.4,
                                                                                                0.3, 0.02, 0, 0,
                                                                                                0, 0, 0,
                                                                                                0.4,0.3,0.08,0.15,
                                                                                                maxGen * swarmSizes[s],
                                                                                                solutionFolderNameNonparametric, indexFolderName, runTime, Nonparametric);
                                                                                    }
                                                                                    //MOHEARun.mainexe(problem,numberOfJobs,numberOfMachines,snumber,upSize,centralSize,downSize,Probability,SwarmSize,MaxIterations,datafile,indexfile);
                                                                                    if (algorithms[m].equals("MOHEA-DE")) {
                                                                                        MOHEARun.mainexe(problem,
                                                                                                jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                                //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                                swarmSizes[s],
                                                                                                0,
                                                                                                0.2, 0.08, 0.6, 0.3,
                                                                                                0.7, 0, 0,
                                                                                                0.4,0.4,0.15,0.15,
                                                                                                maxGen * swarmSizes[s] * 2,
                                                                                                solutionFolderNameNonparametric, indexFolderName, runTime, Nonparametric);
                                                                                    }
                                                                                    //MOHEADERun.mainexe(problem,numberOfJobs,numberOfMachines,snumber,upSize,centralSize,downSize,Probability,SwarmSize,MaxIterations,datafile,indexfile);
                                                                                    if (algorithms[m].equals("MOHEADE")) {
                                                                                        MOHEADERun.mainexe(problem,
                                                                                                jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                                //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                                swarmSizes[s],
                                                                                                0,
                                                                                                0.2, 0.08, 0.6, 0.3,
                                                                                                0.7, 0, 0,
                                                                                                0.4,0.4,0.15,0.15,
                                                                                                maxGen * swarmSizes[s] * 2,
                                                                                                solutionFolderNameNonparametric, indexFolderName, runTime, Nonparametric);
                                                                                    }

                                                                                    //NSGAIIRun.mainexe(problem,numberOfJobs,numberOfMachines,snumber,upSize,centralSize,downSize,Probability,SwarmSize,MaxIterations,datafile,indexfile);
                                                                                    if (algorithms[m].equals("NSGA-II")) {
                                                                                        NSGAIIRun.mainexe(problem,
                                                                                                jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                                //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                                swarmSizes[s],
                                                                                                0,
                                                                                                0.2, 0.04, 0.4, 0.2,
                                                                                                DERates[w], DEcrossoverRates[z], DEmutationRates[x],
                                                                                                0.3,0.4,0.1,0.15,
                                                                                                maxGen * swarmSizes[s],
                                                                                                solutionFolderNameNonparametric, indexFolderName, runTime, Nonparametric);
                                                                                    }
                                                                                    //SPEA2Run.mainexe(problem,numberOfJobs,numberOfMachines,snumber,upSize,centralSize,downSize,Probability,SwarmSize,MaxIterations,datafile,indexfile);
                                                                                    if (algorithms[m].equals("SPEA2")) {
                                                                                        SPEA2Run.mainexe(problem,
                                                                                                jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                                //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                                swarmSizes[s],
                                                                                                0,
                                                                                                0.3, 0.04, 0.3, 0.3,
                                                                                                0.3,0.4,0.15,0.05,
                                                                                                DERates[w], DEcrossoverRates[z], DEmutationRates[x],

                                                                                                maxGen * swarmSizes[s],
                                                                                                solutionFolderNameNonparametric, indexFolderName, runTime, Nonparametric);
                                                                                    }
                                                                                    //MOEADRun.mainexe(problem,numberOfJobs,numberOfMachines,snumber,upSize,centralSize,downSize,Probability,SwarmSize,MaxIterations,datafile,indexfile);
                                                                                    if (algorithms[m].equals("MOEA-LS")) {
                                                                                        MOEADRun.mainexe(problem,
                                                                                                jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                                //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                                swarmSizes[s],
                                                                                                0,
                                                                                                0.1, 0.04, 0.8, 0.4,
                                                                                                0, 0, 0,
                                                                                                maxGen * swarmSizes[s],
                                                                                                solutionFolderNameNonparametric, indexFolderName, runTime, Nonparametric,0.2, 0.02, 0.8, 0.2);
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            }
            System.out.println("原数据计算完成");
        } else {

            if (Nonparametric) {
//无参
                calculateSolutions(solutionFolderName, indexFolderName, algorithms);
                runningIndex(solutionFolderName, indexFolderName, algorithms);
            }
            else{   //有参
                calculateRefSolutions(solutionFolderName, indexFolderName, algorithms, rangesOfR1R2,pmxCrossover ,V1mutationProbability, swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
                runningIndex1(solutionFolderName, indexFolderName, algorithms, rangesOfR1R2,pmxCrossover ,V1mutationProbability, swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
            }
            System.out.println("指标计算完成");
        }
        //System.out.println("指标计算完成");
    }

    static int number = 0;
    //20241230
    private static void runMOPSODSDE4DOE() throws Exception {
        maxGen =10;
        //20211010 由于组合次数太多，比便于计算，因此先确定没有DE情况下参数
        //参考MOPSODS的方法实验的结果。
        jobIndexIds = new int[]{20};              //5,10,20,50,100
        stageIndexIds = new int[]{2};          //2,5,8
        factoryIndexIds = new int[]{3};          //2,3,4,5,6
        problemIndexIds = new int[]{1};
        runTime = 10; //运行次数

//        algorithms = new String[] {"MOPSODSDE"};
//        algorithms = new String[] {"MOPSODSDE"};
        algorithms = new String[] {"MAPSO-QLS"};


        //int[] swarmSizes = new int[]{50,75,100,125,150,175,200}; //20211001测试过
        //int[] swarmSizes = new int[]{50,100,150,200}; //20211002测试过 200最好
//        swarmSizes = new int[]{50}; //20211002 包含DE参数一起测试, 20211004结果 200最好
        swarmSizes = new int[]{100}; //20211002 包含DE参数一起测试, 20211004结果 200最好
//        rangesOfR1R2 = new double[]{0.2, 0.4, 0.6, 0.8, 1.0}; //20211020测试用   0.6
        rangesOfR1R2 = new double[]{0.4}; //20211020测试用   0.6
        crossoverRates = new double[]{0.2}; ////20241214
        mutationRates = new double[]{0.06}; ////20241214
        crossoverRates4worker = new double[]{0.4};//20241214
        crossoverRates4machine = new double[]{0.3};
        mutationRates4worker = new double[]{0.1};//20241214
        mutationRates4machine = new double[]{0.25};
        //double[] rangesOfR1R2 = new double[]{0.1,0.2,0.3,0.4,0.5}; // 20211001测试过 趋势是增加的。
        //double[] rangesOfR1R2 = new double[]{0.2,0.4,0.6,0.8,1.0}; //20211002测试过，0.6最好
        //double[] rangesOfR1R2 = new double[]{0.4}; //20211002 包含DE参数一起测试, 20211004结果 0.6最好
        //rangesOfR1R2 = new double[]{0.2, 0.4, 0.6, 0.8, 1.0}; //20211010测试用
        //rangesOfR1R2 = new double[]{0.2, 0.4, 0.6, 0.8}; //20211020测试用   0.8

//        rangesOfR1R2 = new double[]{0.2}; //20211020测试用   0.6

        //double[] crossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5}; // 20211001测试过 趋势是增加的。
        //double[] crossoverRates = new double[]{0.1,0.3,0.5,0.7,0.9}; // 20211002测试过 0.5最好
        //double[] crossoverRates = new double[]{0.3};

        //没用到
//        crossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5}; ////20211010     //1020 0.3     //LS工厂间
//        crossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5,0.6,0.7}; ////20211010     //1020 0.3     //LS工厂间

        //double[] mutationRates = new double[]{0.05,0.10,0.15,0.20}; //20211001测试过，趋势是越小越好
        //double[] mutationRates = new double[]{0.02}; ////20211002 包含DE参数一起测试, 20211004结果 0.02最好
//        mutationRates = new double[]{0.02,0.04,0.06,0.08,0.1}; ////20211002 包含DE参数一起测试, 20211004结果 0.02最好    1020 0.06
        //mutationRates = new double[]{ 0.04, 0.06, 0.08, 0.10};       //1020 0.04

//        crossoverRates4worker = new double[]{0.1,0.2,0.3,0.4,0.5,0.6,0.7};

//        pmxCrossover= new double[]{30,40,50};            //Q
        pmxCrossover= new double[]{30,40,50,60};            //Q迭代次数
        double[] DEcrossoverRates = new double[]{0.6,0.7,0.8,0.9};    //学习率
        double[] DEmutationRates = new double[]{0.6,0.7,0.8,0.9};     //贪婪率
        int[] localsearch= new int[]{10,20,30,40};     //局部搜索次数

        V1mutationProbability = new double[]{0};
        //double[] DERates = new double[]{0.1,0.3,0.5,0.7,0.9}; //20211002 优化过其他参数后，单独测试DE概率用,结果基本0.5最好。
        double[] DERates = new double[]{0}; //20211002 包含DE参数一起测试, 20211004结果 0.5最好  没用到
        //double[] DERates = new double[]{0.2,0.4,0.6,0.8,1.0}; //220211010测试用
        //DERates = new double[]{0.2,0.4,0.6,0.8,1.0}; //220211010测试用
        //DERates = new double[]{0.2,0.4,0.6,0.8}; //220211020测试用    0.4

//        double[] DEcrossoverRates = new double[]{0.7,0.8,0.9};    //学习率
        //double[] DEcrossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5};////20211010
        //DEcrossoverRates = new double[]{0.1, 0.2, 0.3,0.4};////20211010      0.1

//        double[] DEmutationRates = new double[]{0.7,0.8,0.9};     //贪婪率
        //double[] DEmutationRates = new double[]{0.02,0.04,0.06,0.08,0.10};////20211010
        //DEmutationRates = new double[]{0.02, 0.04, 0.06, 0.08};////20211010    0.06       //后测0.02
        //DEmutationRates =0.06   DEcrossoverRates=0.2  DERates=1.0   10次测试最好参数   20211012
        //4*3*3*3*3=108*3=324
        //4*3*3*3=108


//        isFirstRun = false; //运行算法时，改为 true,运行指标时，改为false
        isFirstRun = true; //运行算法时，改为 true,运行指标时，改为false
        isFirstRun = false;   //运行指标时，改为false
        Nonparametric = false;

        //跑原数据
        if (isFirstRun) {
            for (int j = 0; j < jobIndexIds.length; j++) {
                for (int k = 0; k < stageIndexIds.length; k++) {
                    for (int i = 0; i < factoryIndexIds.length; i++) {
                        for (int p = 0; p < problemIndexIds.length; p++) {

                            problem = (PermutationProblem<PermutationSolution<Integer>>) new DHFSP(jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i],problemIndexIds[0]);
                            //测试参数
                            for (int m = 0; m < algorithms.length; m++) {
                                for (int r = 0; r < rangesOfR1R2.length; r++) {
                                    for (int s = 0; s < swarmSizes.length; s++) {
                                        for (int t = 0; t < crossoverRates.length; t++) {
                                            for (int o = 0; o < mutationRates.length; o++) {
                                                for (int q = 0; q < pmxCrossover.length; q++) {
                                                    for (int a = 0; a < V1mutationProbability.length; a++) {
                                                        for (int w = 0; w < DERates.length; w++) {
                                                            for (int z = 0; z < DEcrossoverRates.length; z++) {
                                                                for (int x = 0; x < DEmutationRates.length; x++) {
                                                                    for (int u = 0; u < crossoverRates4worker.length; u++) {
                                                                        for (int c = 0; c < crossoverRates4machine.length; c++) {
                                                                            for (int b = 0; b < mutationRates4worker.length; b++) {
                                                                                for (int v = 0; v < mutationRates4machine.length; v++) {
                                                                                for (int d = 0; d < localsearch.length; d++) {
                                                                                    if (algorithms[m].equals("MAPSO-QLS")) {
                                                                                        MOPSODivSubDERun.mainexe(problem,
                                                                                                jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                                //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                                swarmSizes[s],
                                                                                                rangesOfR1R2[r],
                                                                                                crossoverRates[t], mutationRates[o], pmxCrossover[q], V1mutationProbability[a],
                                                                                                DERates[w], DEcrossoverRates[z], DEmutationRates[x], maxGen * swarmSizes[s],
                                                                                                solutionFolderName, indexFolderName, runTime, Nonparametric, crossoverRates4worker[u], crossoverRates4machine[c], mutationRates4worker[b], mutationRates4machine[v],
                                                                                                localsearch[d]);


                                                                                    }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }

                                                                    }

                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }}
            System.out.println("原数据计算完成");
//            System.out.println(number);
        } else {
            //注意第一个参数的目录
//            calculateSolutions(solutionFolderName1, indexFolderName, algorithms);
//            runningIndex(solutionFolderName1, indexFolderName, algorithms);
            calculateRefSolutions_new(solutionFolderName1, indexFolderName, algorithms, rangesOfR1R2,pmxCrossover ,V1mutationProbability, swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates,crossoverRates4worker,crossoverRates4machine,mutationRates4worker,mutationRates4machine,localsearch);    //带参数
//            runningIndex1(solutionFolderName1, indexFolderName, algorithms, rangesOfR1R2,pmxCrossover ,V1mutationProbability, swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
            runningIndexnew(solutionFolderName1, indexFolderName, algorithms, rangesOfR1R2,pmxCrossover ,V1mutationProbability, swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates,crossoverRates4worker,crossoverRates4machine,mutationRates4worker,mutationRates4machine,localsearch);    //带参数
            System.out.println("指标计算完成");
        }
    }
    //20241230
    private static void runMOHEA4DOE() throws Exception {
        //先测试MOPSODS的方法实验的结果，没有DE操作
        jobIndexIds = new int[]{20};              //5,10,20,50,100
        stageIndexIds = new int[]{2};          //2,5,8
        factoryIndexIds = new int[]{3};          //2,3,4,5,6
        problemIndexIds = new int[]{1};
        runTime = 10; //运行次数

        algorithms = new String[] {"MOHEA"};

        //int[] swarmSizes = new int[]{50,75,100,125,150,175,200}; //20211001测试过
        //int[] swarmSizes = new int[]{50,100,150,200}; //20211002测试过 200最好
        swarmSizes = new int[]{100}; //20211002 包含DE参数一起测试, 20211004结果 200最好

        //double[] rangesOfR1R2 = new double[]{0.1,0.2,0.3,0.4,0.5}; // 20211001测试过 趋势是增加的。
        //double[] rangesOfR1R2 = new double[]{0.2,0.4,0.6,0.8,1.0}; //20211002测试过，0.6最好
        //double[] rangesOfR1R2 = new double[]{0.6}; //20211002 包含DE参数一起测试, 20211004结果 0.6最好
        rangesOfR1R2 = new double[]{0}; //20211010测试用

        //pmxCrossover= new double[]{0.2,0.4,0.6,0.8};     //0.8最好
        //V1mutationProbability = new double[]{0.05, 0.1, 0.15, 0.2};     //0.2最好

        pmxCrossover= new double[]{0.8};     //0.8最好
        V1mutationProbability = new double[]{0.2};     //0.2最好
        //double[] crossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5}; // 20211001测试过 趋势是增加的。
        //double[] crossoverRates = new double[]{0.1,0.3,0.5,0.7,0.9}; // 20211002测试过 0.5最好
        //crossoverRates = new double[]{0.2, 0.4, 0.6, 0.8}; ////20211010        //0.2最好
        crossoverRates = new double[]{0.2};
        //double[] mutationRates = new double[]{0.05,0.10,0.15,0.20}; //20211001测试过，趋势是越小越好
        //double[] mutationRates = new double[]{0.02}; ////20211002 包含DE参数一起测试, 20211004结果 0.02最好
        //mutationRates = new double[]{0.02, 0.04, 0.06, 0.08, 0.10}; ////20211002 包含DE参数一起测试, 20211004结果 0.02最好     //0.02最好
        mutationRates = new double[]{0.02};

        //double[] DERates = new double[]{0.1,0.3,0.5,0.7,0.9}; //20211002 优化过其他参数后，单独测试DE概率用,结果基本0.5最好。
        //double[] DERates = new double[]{0.5}; //20211002 包含DE参数一起测试, 20211004结果 0.5最好
        //double[] DERates = new double[]{0.2,0.4,0.6,0.8,1.0}; //220211010测试用
        DERates = new double[]{0}; //220211010测试用

        //double[] DEcrossoverRates = new double[]{0.1};
        //double[] DEcrossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5};////20211010
        DEcrossoverRates = new double[]{0};////20211010

        //double[] DEmutationRates = new double[]{0.02};
        //double[] DEmutationRates = new double[]{0.02,0.04,0.06,0.08,0.10};////20211010
        DEmutationRates = new double[]{0};////20211010

        crossoverRates4worker = new double[]{0.4};//20241214
        crossoverRates4machine = new double[]{0.3};
        mutationRates4worker = new double[]{0.1};//20241214
        mutationRates4machine = new double[]{0.25};


        isFirstRun = true; //运行算法时，改为true,运行指标时，改为false
//        isFirstRun = false;   //运行指标时，改为false

        //跑原数据
        if (isFirstRun) {
            for (int j = 0; j < jobIndexIds.length; j++) {
                for (int k = 0; k < stageIndexIds.length; k++) {
                    for (int i = 0; i < factoryIndexIds.length; i++) {
                        for (int p = 0; p < problemIndexIds.length; p++) {

                            problem = (PermutationProblem<PermutationSolution<Integer>>) new DHFSP(jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i],problemIndexIds[0]);
                        //测试参数
                        for (int m = 0; m < algorithms.length; m++) {
                            for (int r = 0; r < rangesOfR1R2.length; r++) {
                                for (int s = 0; s < swarmSizes.length; s++) {
                                    for (int t = 0; t < crossoverRates.length; t++) {
                                        for (int o = 0; o < mutationRates.length; o++) {
                                            for (int q = 0; q < pmxCrossover.length; q++) {
                                                for (int a = 0; a < V1mutationProbability.length; a++) {
                                            for (int w = 0; w < DERates.length; w++) {
                                                for (int z = 0; z < DEcrossoverRates.length; z++) {
                                                    for (int x = 0; x < DEmutationRates.length; x++) {
                                                        for (int u = 0; u < crossoverRates4worker.length; u++) {
                                                            for (int c = 0; c < crossoverRates4machine.length; c++) {
                                                                for (int b = 0; b < mutationRates4worker.length; b++) {
                                                                    for (int v = 0; v < mutationRates4machine.length; v++) {
                                                                        if (algorithms[m].equals("MOHEA")) {
                                                                            MOHEARun.mainexe(problem,
                                                                                    jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                    //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                    swarmSizes[s],
                                                                                    rangesOfR1R2[r],
                                                                                    crossoverRates[t], mutationRates[o],
                                                                                    pmxCrossover[q], V1mutationProbability[a],
                                                                                    DERates[w], DEcrossoverRates[z], DEmutationRates[x],
                                                                                    crossoverRates4worker[u],crossoverRates4machine[c],mutationRates4worker[b],mutationRates4machine[v],
                                                                                    maxGen * swarmSizes[s],
                                                                                    solutionFolderName, indexFolderName, runTime, Nonparametric);
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }}
                    }
                }
            }System.out.println("原数据计算完成");
        } else {

            calculateRefSolutions(solutionFolderName, indexFolderName, algorithms, rangesOfR1R2,pmxCrossover ,V1mutationProbability,swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
            runningIndex1(solutionFolderName, indexFolderName, algorithms, rangesOfR1R2, pmxCrossover ,V1mutationProbability,swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
            System.out.println("指标计算完成");}

    }


    //20241230
    private static void runMOPSODS4DOE() throws Exception {
        //先测试MOPSODS的方法实验的结果，没有DE操作
        jobIndexIds = new int[]{20};              //5,10,20,50,100
        stageIndexIds = new int[]{2};          //2,5,8
        factoryIndexIds = new int[]{3};          //2,3,4,5,6
        problemIndexIds = new int[]{1};
        runTime = 10; //运行次数

        algorithms = new String[] {"MOPSODS"};

        //int[] swarmSizes = new int[]{50,75,100,125,150,175,200}; //20211001测试过
        //int[] swarmSizes = new int[]{50,100,150,200}; //20211002测试过 200最好
        swarmSizes = new int[]{100}; //20211002 包含DE参数一起测试, 20211004结果 200最好

        //double[] rangesOfR1R2 = new double[]{0.1,0.2,0.3,0.4,0.5}; // 20211001测试过 趋势是增加的。
        //double[] rangesOfR1R2 = new double[]{0.2,0.4,0.6,0.8,1.0}; //20211002测试过，0.6最好
        //double[] rangesOfR1R2 = new double[]{0.6}; //20211002 包含DE参数一起测试, 20211004结果 0.6最好
        rangesOfR1R2 = new double[]{0.2, 0.4, 0.6, 0.8, 1.0}; //20211010测试用
        //rangesOfR1R2 = new double[]{ 0.4};
        pmxCrossover= new double[]{0};
        V1mutationProbability = new double[]{0};
        //double[] crossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5}; // 20211001测试过 趋势是增加的。
        //double[] crossoverRates = new double[]{0.1,0.3,0.5,0.7,0.9}; // 20211002测试过 0.5最好
        crossoverRates = new double[]{ 0.1,  0.2,  0.3,  0.4, 0.5}; ////20211010
        //crossoverRates = new double[]{0.3};
        //double[] mutationRates = new double[]{0.05,0.10,0.15,0.20}; //20211001测试过，趋势是越小越好
        //double[] mutationRates = new double[]{0.02}; ////20211002 包含DE参数一起测试, 20211004结果 0.02最好
        mutationRates = new double[]{0.02, 0.04, 0.06, 0.08, 0.10}; ////20211002 包含DE参数一起测试, 20211004结果 0.02最好
        //mutationRates = new double[]{0.02};
        //double[] DERates = new double[]{0.1,0.3,0.5,0.7,0.9}; //20211002 优化过其他参数后，单独测试DE概率用,结果基本0.5最好。
        //double[] DERates = new double[]{0.5}; //20211002 包含DE参数一起测试, 20211004结果 0.5最好
        //double[] DERates = new double[]{0.2,0.4,0.6,0.8,1.0}; //220211010测试用
        DERates = new double[]{0}; //220211010测试用


        crossoverRates4worker = new double[]{0.4};//20241214
        crossoverRates4machine = new double[]{0.3};
        mutationRates4worker = new double[]{0.1};//20241214
        mutationRates4machine = new double[]{0.25};

        //double[] DEcrossoverRates = new double[]{0.1};
        //double[] DEcrossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5};////20211010
        DEcrossoverRates = new double[]{0};////20211010

        //double[] DEmutationRates = new double[]{0.02};
        //double[] DEmutationRates = new double[]{0.02,0.04,0.06,0.08,0.10};////20211010
        DEmutationRates = new double[]{0};////20211010

        isFirstRun = true; //运行算法时，改为true,运行指标时，改为false
//        isFirstRun = false;   //运行指标时，改为false

        //跑原数据
        if (isFirstRun) {
            for (int j = 0; j < jobIndexIds.length; j++) {
                for (int k = 0; k < stageIndexIds.length; k++) {
                    for (int i = 0; i < factoryIndexIds.length; i++) {
                        for (int p = 0; p < problemIndexIds.length; p++) {

                        problem = (PermutationProblem<PermutationSolution<Integer>>) new DHFSP(jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i],problemIndexIds[0]);
                        //测试参数
                        for (int m = 0; m < algorithms.length; m++) {
                            for (int r = 0; r < rangesOfR1R2.length; r++) {
                                for (int s = 0; s < swarmSizes.length; s++) {
                                    for (int t = 0; t < crossoverRates.length; t++) {
                                        for (int o = 0; o < mutationRates.length; o++) {
                                            for (int q = 0; q < pmxCrossover.length; q++) {
                                                for (int a = 0; a < V1mutationProbability.length; a++) {
                                                    for (int w = 0; w < DERates.length; w++) {
                                                        for (int z = 0; z < DEcrossoverRates.length; z++) {
                                                            for (int x = 0; x < DEmutationRates.length; x++) {
                                                                for (int u = 0; u < crossoverRates4worker.length; u++) {
                                                                    for (int c = 0; c < crossoverRates4machine.length; c++) {
                                                                        for (int b = 0; b < mutationRates4worker.length; b++) {
                                                                            for (int v = 0; v < mutationRates4machine.length; v++) {
                                                                                if (algorithms[m].equals("MOPSODS")) {
                                                                                    MOPSODivSubRun.mainexe(problem,
                                                                                            jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                            //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                            swarmSizes[s],
                                                                                            0.4,
                                                                                            0.1, 0.02, 0, 0,
                                                                                            0, 0, 0,
                                                                                            crossoverRates4worker[u],crossoverRates4machine[c],mutationRates4worker[b],mutationRates4machine[v],
                                                                                            maxGen * swarmSizes[s],
                                                                                            solutionFolderNameNonparametric, indexFolderName, runTime, Nonparametric);
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                            }
                        }
                    }
                }}
            }System.out.println("原数据计算完成");
        } else {

            calculateRefSolutions(solutionFolderName, indexFolderName, algorithms, rangesOfR1R2,pmxCrossover , V1mutationProbability,swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
            runningIndex1(solutionFolderName, indexFolderName, algorithms, rangesOfR1R2,pmxCrossover ,V1mutationProbability, swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
            System.out.println("指标计算完成");}

    }

    //20241230
    private static void runMOPSO4DOE() throws Exception {
        //先测试MOPSODS的方法实验的结果，没有DE操作
        jobIndexIds = new int[]{20};              //5,10,20,50,100
        stageIndexIds = new int[]{2};          //2,5,8
        factoryIndexIds = new int[]{3};          //2,3,4,5,6
        problemIndexIds = new int[]{1};
        runTime = 10; //运行次数

        algorithms = new String[] {"MOPSO"};

        //int[] swarmSizes = new int[]{50,75,100,125,150,175,200}; //20211001测试过
        //int[] swarmSizes = new int[]{50,100,150,200}; //20211002测试过 200最好
        swarmSizes = new int[]{100}; //20211002 包含DE参数一起测试, 20211004结果 200最好

        //double[] rangesOfR1R2 = new double[]{0.1,0.2,0.3,0.4,0.5}; // 20211001测试过 趋势是增加的。
        //double[] rangesOfR1R2 = new double[]{0.2,0.4,0.6,0.8,1.0}; //20211002测试过，0.6最好
        //double[] rangesOfR1R2 = new double[]{0.6}; //20211002 包含DE参数一起测试, 20211004结果 0.6最好
        rangesOfR1R2 = new double[]{0.4}; //20211010测试用
        pmxCrossover= new double[]{0};
        V1mutationProbability = new double[]{0};
        //double[] crossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5}; // 20211001测试过 趋势是增加的。
        //double[] crossoverRates = new double[]{0.1,0.3,0.5,0.7,0.9}; // 20211002测试过 0.5最好
        crossoverRates = new double[]{0.3}; ////20211010

        //double[] mutationRates = new double[]{0.05,0.10,0.15,0.20}; //20211001测试过，趋势是越小越好
        //double[] mutationRates = new double[]{0.02}; ////20211002 包含DE参数一起测试, 20211004结果 0.02最好
        mutationRates = new double[]{0.02}; ////20211002 包含DE参数一起测试, 20211004结果 0.02最好

        //double[] DERates = new double[]{0.1,0.3,0.5,0.7,0.9}; //20211002 优化过其他参数后，单独测试DE概率用,结果基本0.5最好。
        //double[] DERates = new double[]{0.5}; //20211002 包含DE参数一起测试, 20211004结果 0.5最好
        //double[] DERates = new double[]{0.2,0.4,0.6,0.8,1.0}; //220211010测试用
        DERates = new double[]{0}; //220211010测试用

        //double[] DEcrossoverRates = new double[]{0.1};
        //double[] DEcrossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5};////20211010
        DEcrossoverRates = new double[]{0};////20211010

        //double[] DEmutationRates = new double[]{0.02};
        //double[] DEmutationRates = new double[]{0.02,0.04,0.06,0.08,0.10};////20211010
        DEmutationRates = new double[]{0};////20211010

        crossoverRates4worker = new double[]{0.4};//20241214
        crossoverRates4machine = new double[]{0.3};
        mutationRates4worker = new double[]{0.1};//20241214
        mutationRates4machine = new double[]{0.25};


        isFirstRun = true; //运行算法时，改为true,运行指标时，改为false
        //isFirstRun = false;   //运行指标时，改为false

        //跑原数据
        if (isFirstRun) {
            for (int j = 0; j < jobIndexIds.length; j++) {
                for (int k = 0; k < stageIndexIds.length; k++) {
                    for (int i = 0; i < factoryIndexIds.length; i++) {
                        for (int p = 0; p < problemIndexIds.length; p++) {

                            problem = (PermutationProblem<PermutationSolution<Integer>>) new DHFSP(jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i],problemIndexIds[0]);
                        //测试参数
                        for (int m = 0; m < algorithms.length; m++) {
                            for (int r = 0; r < rangesOfR1R2.length; r++) {
                                for (int s = 0; s < swarmSizes.length; s++) {
                                    for (int t = 0; t < crossoverRates.length; t++) {
                                        for (int o = 0; o < mutationRates.length; o++) {
                                            for (int q = 0; q < pmxCrossover.length; q++) {
                                                for (int a = 0; a < V1mutationProbability.length; a++) {
                                                    for (int w = 0; w < DERates.length; w++) {
                                                        for (int z = 0; z < DEcrossoverRates.length; z++) {
                                                            for (int x = 0; x < DEmutationRates.length; x++) {
                                                                for (int u = 0; u < crossoverRates4worker.length; u++) {
                                                                    for (int c = 0; c < crossoverRates4machine.length; c++) {
                                                                        for (int b = 0; b < mutationRates4worker.length; b++) {
                                                                            for (int v = 0; v < mutationRates4machine.length; v++) {
                                                                                if (algorithms[m].equals("MOPSO")) {
                                                                                    MOPSORun.mainexe(problem,
                                                                                            jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                            //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                            swarmSizes[s],
                                                                                            rangesOfR1R2[r],
                                                                                            crossoverRates[t], mutationRates[o], pmxCrossover[q], V1mutationProbability[a],
                                                                                            DERates[w], DEcrossoverRates[z], DEmutationRates[x],
                                                                                            crossoverRates4worker[u],crossoverRates4machine[c],mutationRates4worker[b],mutationRates4machine[v],

                                                                                            maxGen * swarmSizes[s],
                                                                                            solutionFolderName, indexFolderName, runTime, Nonparametric);
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                            }}
                        }
                    }
                }
            }
            System.out.println("原数据计算完成");
        } else {

            calculateRefSolutions(solutionFolderName1, indexFolderName, algorithms, rangesOfR1R2,pmxCrossover , V1mutationProbability,swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
            runningIndex1(solutionFolderName1, indexFolderName, algorithms, rangesOfR1R2,pmxCrossover ,V1mutationProbability, swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
            System.out.println("指标计算完成");
        }
    }

    private static void runMOEAD4DOE() throws Exception {
        //先测试MOPSODS的方法实验的结果，没有DE操作
        jobIndexIds = new int[]{20};              //5,10,20,50,100
        stageIndexIds = new int[]{2};          //2,5,8
        factoryIndexIds = new int[]{3};          //2,3,4,5,6
        problemIndexIds = new int[]{1};
        runTime = 10; //运行次数
        int[] localsearch= new int[]{0};     //局部搜索次数
        algorithms = new String[] {"MOEAD"};

        //int[] swarmSizes = new int[]{50,75,100,125,150,175,200}; //20211001测试过
        //int[] swarmSizes = new int[]{50,100,150,200}; //20211002测试过 200最好
        swarmSizes = new int[]{50}; //20211002 包含DE参数一起测试, 20211004结果 200最好

        //double[] rangesOfR1R2 = new double[]{0.1,0.2,0.3,0.4,0.5}; // 20211001测试过 趋势是增加的。
        //double[] rangesOfR1R2 = new double[]{0.2,0.4,0.6,0.8,1.0}; //20211002测试过，0.6最好
        //double[] rangesOfR1R2 = new double[]{0.6}; //20211002 包含DE参数一起测试, 20211004结果 0.6最好
        rangesOfR1R2 = new double[]{0}; //20211010测试用

        //pmxCrossover= new double[]{0.2,0.4,0.6,0.8};   //0.8
        //V1mutationProbability = new double[]{0.1, 0.2, 0.3, 0.4};     //0.4

        pmxCrossover= new double[]{0.8};   //0.8
        V1mutationProbability = new double[]{0.4};     //0.4
        //double[] crossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5}; // 20211001测试过 趋势是增加的。
        //double[] crossoverRates = new double[]{0.1,0.3,0.5,0.7,0.9}; // 20211002测试过 0.5最好
        //crossoverRates = new double[]{0.1, 0.2, 0.3, 0.4}; ////20211010   //0.1
        crossoverRates = new double[]{0.1};
        //double[] mutationRates = new double[]{0.05,0.10,0.15,0.20}; //20211001测试过，趋势是越小越好
        //double[] mutationRates = new double[]{0.02}; ////20211002 包含DE参数一起测试, 20211004结果 0.02最好
        //mutationRates = new double[]{0.02, 0.04, 0.06, 0.08, 0.10}; ////20211002 包含DE参数一起测试, 20211004结果 0.02最好    //0.04
        mutationRates = new double[]{0.04};
        //double[] DERates = new double[]{0.1,0.3,0.5,0.7,0.9}; //20211002 优化过其他参数后，单独测试DE概率用,结果基本0.5最好。
        //double[] DERates = new double[]{0.5}; //20211002 包含DE参数一起测试, 20211004结果 0.5最好
        //double[] DERates = new double[]{0.2,0.4,0.6,0.8,1.0}; //220211010测试用
        DERates = new double[]{0}; //220211010测试用

        //double[] DEcrossoverRates = new double[]{0.1};
        //double[] DEcrossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5};////20211010
        DEcrossoverRates = new double[]{0};////20211010

        //double[] DEmutationRates = new double[]{0.02};
        //double[] DEmutationRates = new double[]{0.02,0.04,0.06,0.08,0.10};////20211010
        DEmutationRates = new double[]{0};////20211010

        crossoverRates4worker = new double[]{0.4};//20241214
        crossoverRates4machine = new double[]{0.3};
        mutationRates4worker = new double[]{0.1};//20241214
        mutationRates4machine = new double[]{0.25};


        isFirstRun = true; //运行算法时，改为true,运行指标时，改为false
//        isFirstRun = false;   //运行指标时，改为false

        //跑原数据
        if (isFirstRun) {
            for (int j = 0; j < jobIndexIds.length; j++) {
                for (int k = 0; k < stageIndexIds.length; k++) {
                    for (int i = 0; i < factoryIndexIds.length; i++) {
                        for (int p = 0; p < problemIndexIds.length; p++) {

                            problem = (PermutationProblem<PermutationSolution<Integer>>) new DHFSP(jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i],problemIndexIds[0]);
                        //测试参数
                        for (int m = 0; m < algorithms.length; m++) {
                            for (int r = 0; r < rangesOfR1R2.length; r++) {
                                for (int s = 0; s < swarmSizes.length; s++) {
                                    for (int t = 0; t < crossoverRates.length; t++) {
                                        for (int o = 0; o < mutationRates.length; o++) {
                                            for (int q = 0; q < pmxCrossover.length; q++) {
                                                for (int a = 0; a < V1mutationProbability.length; a++) {
                                                    for (int w = 0; w < DERates.length; w++) {
                                                        for (int z = 0; z < DEcrossoverRates.length; z++) {
                                                            for (int x = 0; x < DEmutationRates.length; x++) {
                                                                for (int u = 0; u < crossoverRates4worker.length; u++) {
                                                                    for (int c = 0; c < crossoverRates4machine.length; c++) {
                                                                        for (int b = 0; b < mutationRates4worker.length; b++) {
                                                                            for (int v = 0; v < mutationRates4machine.length; v++) {
                                                                                    if (algorithms[m].equals("MOEAD")) {
                                                                                        MOEADRun.mainexe(problem,
                                                                                                jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                                //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                                swarmSizes[s],
                                                                                                rangesOfR1R2[r],
                                                                                                crossoverRates[t], mutationRates[o],
                                                                                                pmxCrossover[q], V1mutationProbability[a],
                                                                                                DERates[w], DEcrossoverRates[z], DEmutationRates[x], maxGen * swarmSizes[s],
                                                                                                solutionFolderName, indexFolderName, runTime, Nonparametric, crossoverRates4worker[u], crossoverRates4machine[c], mutationRates4worker[b], mutationRates4machine[v]);

                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        } }
                    }
                }
            }System.out.println("原数据计算完成");
        } else {

            calculateRefSolutions(solutionFolderName, indexFolderName, algorithms, rangesOfR1R2,pmxCrossover ,V1mutationProbability,swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
            runningIndex1(solutionFolderName, indexFolderName, algorithms, rangesOfR1R2, pmxCrossover ,V1mutationProbability,swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
            System.out.println("指标计算完成");}

    }
    //20241230
    private static void runNSGAII4DOE() throws Exception {
        //先测试MOPSODS的方法实验的结果，没有DE操作
        jobIndexIds = new int[]{20};              //5,10,20,50,100
        stageIndexIds = new int[]{2};          //2,5,8
        factoryIndexIds = new int[]{3};          //2,3,4,5,6
        problemIndexIds = new int[]{1};
        runTime = 10; //运行次数

        algorithms = new String[] {"NSGAII"};

        //int[] swarmSizes = new int[]{50,75,100,125,150,175,200}; //20211001测试过
        //int[] swarmSizes = new int[]{50,100,150,200}; //20211002测试过 200最好
        swarmSizes = new int[]{100}; //20211002 包含DE参数一起测试, 20211004结果 200最好

        //double[] rangesOfR1R2 = new double[]{0.1,0.2,0.3,0.4,0.5}; // 20211001测试过 趋势是增加的。
        //double[] rangesOfR1R2 = new double[]{0.2,0.4,0.6,0.8,1.0}; //20211002测试过，0.6最好
        //double[] rangesOfR1R2 = new double[]{0.6}; //20211002 包含DE参数一起测试, 20211004结果 0.6最好
        rangesOfR1R2 = new double[]{0}; //20211010测试用

        //pmxCrossover= new double[]{0.2,0.4,0.6,0.8};     //0.4
        //V1mutationProbability = new double[]{0.1, 0.2, 0.3, 0.4};     //0.4
        pmxCrossover= new double[]{0.4};     //0.4
        V1mutationProbability = new double[]{0.4};     //0.4

        //double[] crossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5}; // 20211001测试过 趋势是增加的。
        //double[] crossoverRates = new double[]{0.1,0.3,0.5,0.7,0.9}; // 20211002测试过 0.5最好
        //crossoverRates = new double[]{0.1, 0.2, 0.3, 0.4}; ////20211010     //0.2
        crossoverRates = new double[]{0.2}; ////20211010     //0.2

        //double[] mutationRates = new double[]{0.05,0.10,0.15,0.20}; //20211001测试过，趋势是越小越好
        //double[] mutationRates = new double[]{0.02}; ////20211002 包含DE参数一起测试, 20211004结果 0.02最好
        //mutationRates = new double[]{0.02, 0.04, 0.06, 0.08, 0.10}; ////20211002 包含DE参数一起测试, 20211004结果 0.02最好      //0.04
        mutationRates = new double[]{0.04};
        //double[] DERates = new double[]{0.1,0.3,0.5,0.7,0.9}; //20211002 优化过其他参数后，单独测试DE概率用,结果基本0.5最好。
        //double[] DERates = new double[]{0.5}; //20211002 包含DE参数一起测试, 20211004结果 0.5最好
        //double[] DERates = new double[]{0.2,0.4,0.6,0.8,1.0}; //220211010测试用
        DERates = new double[]{0}; //220211010测试用

        //double[] DEcrossoverRates = new double[]{0.1};
        //double[] DEcrossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5};////20211010
        DEcrossoverRates = new double[]{0};////20211010

        //double[] DEmutationRates = new double[]{0.02};
        //double[] DEmutationRates = new double[]{0.02,0.04,0.06,0.08,0.10};////20211010
        DEmutationRates = new double[]{0};////20211010

        crossoverRates4worker = new double[]{0.4};//20241214
        crossoverRates4machine = new double[]{0.3};
        mutationRates4worker = new double[]{0.1};//20241214
        mutationRates4machine = new double[]{0.25};

        isFirstRun = true; //运行算法时，改为true,运行指标时，改为false
//        isFirstRun = false;   //运行指标时，改为false

        //跑原数据
        if (isFirstRun) {
            for (int j = 0; j < jobIndexIds.length; j++) {
                for (int k = 0; k < stageIndexIds.length; k++) {
                    for (int i = 0; i < factoryIndexIds.length; i++) {
                        for (int p = 0; p < problemIndexIds.length; p++) {

                            problem = (PermutationProblem<PermutationSolution<Integer>>) new DHFSP(jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i],problemIndexIds[0]);
                        //测试参数
                        for (int m = 0; m < algorithms.length; m++) {
                            for (int r = 0; r < rangesOfR1R2.length; r++) {
                                for (int s = 0; s < swarmSizes.length; s++) {
                                    for (int t = 0; t < crossoverRates.length; t++) {
                                        for (int o = 0; o < mutationRates.length; o++) {
                                            for (int q = 0; q < pmxCrossover.length; q++) {
                                                for (int a = 0; a < V1mutationProbability.length; a++) {
                                                    for (int w = 0; w < DERates.length; w++) {
                                                        for (int z = 0; z < DEcrossoverRates.length; z++) {
                                                            for (int x = 0; x < DEmutationRates.length; x++) {
                                                                for (int u = 0; u < crossoverRates4worker.length; u++) {
                                                                    for (int c = 0; c < crossoverRates4machine.length; c++) {
                                                                        for (int b = 0; b < mutationRates4worker.length; b++) {
                                                                            for (int v = 0; v < mutationRates4machine.length; v++) {
                                                                                if (algorithms[m].equals("NSGAII")) {
                                                                                    NSGAIIRun.mainexe(problem,
                                                                                            jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                            //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                            swarmSizes[s],
                                                                                            rangesOfR1R2[r],
                                                                                            crossoverRates[t], mutationRates[o],
                                                                                            pmxCrossover[q], V1mutationProbability[a],
                                                                                            DERates[w], DEcrossoverRates[z], DEmutationRates[x],
                                                                                            crossoverRates4worker[u],crossoverRates4machine[c],mutationRates4worker[b],mutationRates4machine[v],
                                                                                            maxGen * swarmSizes[s],
                                                                                            solutionFolderName, indexFolderName, runTime, Nonparametric);
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }}
                    }
                }
            }System.out.println("原数据计算完成");
        } else {

            calculateRefSolutions(solutionFolderName, indexFolderName, algorithms, rangesOfR1R2,pmxCrossover ,V1mutationProbability,swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
            runningIndex1(solutionFolderName, indexFolderName, algorithms, rangesOfR1R2, pmxCrossover ,V1mutationProbability,swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
            System.out.println("指标计算完成");}

    }

    //20241230
    private static void runSPEA24DOE() throws Exception {
        //先测试MOPSODS的方法实验的结果，没有DE操作
        jobIndexIds = new int[]{20};              //5,10,20,50,100
        stageIndexIds = new int[]{2};          //2,5,8
        factoryIndexIds = new int[]{3};          //2,3,4,5,6
        problemIndexIds = new int[]{1};
        runTime = 10; //运行次数

        algorithms = new String[] {"SPEA2"};

        //int[] swarmSizes = new int[]{50,75,100,125,150,175,200}; //20211001测试过
        //int[] swarmSizes = new int[]{50,100,150,200}; //20211002测试过 200最好
        swarmSizes = new int[]{100}; //20211002 包含DE参数一起测试, 20211004结果 200最好

        //double[] rangesOfR1R2 = new double[]{0.1,0.2,0.3,0.4,0.5}; // 20211001测试过 趋势是增加的。
        //double[] rangesOfR1R2 = new double[]{0.2,0.4,0.6,0.8,1.0}; //20211002测试过，0.6最好
        //double[] rangesOfR1R2 = new double[]{0.6}; //20211002 包含DE参数一起测试, 20211004结果 0.6最好
        rangesOfR1R2 = new double[]{0}; //20211010测试用

        //pmxCrossover= new double[]{0.2,0.4,0.6,0.8};
        //V1mutationProbability = new double[]{0.1, 0.2, 0.3, 0.4};
        pmxCrossover= new double[]{0.4};
        V1mutationProbability = new double[]{0.4};

        //double[] crossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5}; // 20211001测试过 趋势是增加的。
        //double[] crossoverRates = new double[]{0.1,0.3,0.5,0.7,0.9}; // 20211002测试过 0.5最好
        //crossoverRates = new double[]{0.1, 0.2, 0.3, 0.4};
        crossoverRates = new double[]{0.1};

        //double[] mutationRates = new double[]{0.05,0.10,0.15,0.20}; //20211001测试过，趋势是越小越好
        //double[] mutationRates = new double[]{0.02}; ////20211002 包含DE参数一起测试, 20211004结果 0.02最好
        //mutationRates = new double[]{0.02, 0.04, 0.06, 0.08, 0.10};
        mutationRates = new double[]{0.02};

        //double[] DERates = new double[]{0.1,0.3,0.5,0.7,0.9}; //20211002 优化过其他参数后，单独测试DE概率用,结果基本0.5最好。
        //double[] DERates = new double[]{0.5}; //20211002 包含DE参数一起测试, 20211004结果 0.5最好
        //double[] DERates = new double[]{0.2,0.4,0.6,0.8,1.0}; //220211010测试用
        DERates = new double[]{0}; //220211010测试用

        //double[] DEcrossoverRates = new double[]{0.1};
        //double[] DEcrossoverRates = new double[]{0.1,0.2,0.3,0.4,0.5};////20211010
        DEcrossoverRates = new double[]{0};////20211010

        //double[] DEmutationRates = new double[]{0.02};
        //double[] DEmutationRates = new double[]{0.02,0.04,0.06,0.08,0.10};////20211010
        DEmutationRates = new double[]{0};////20211010

        crossoverRates4worker = new double[]{0.4};//20241214
        crossoverRates4machine = new double[]{0.3};
        mutationRates4worker = new double[]{0.1};//20241214
        mutationRates4machine = new double[]{0.25};

        isFirstRun = true; //运行算法时，改为true,运行指标时，改为false
//        isFirstRun = false;   //运行指标时，改为false

        //跑原数据
        if (isFirstRun) {
            for (int j = 0; j < jobIndexIds.length; j++) {
                for (int k = 0; k < stageIndexIds.length; k++) {
                    for (int i = 0; i < factoryIndexIds.length; i++) {
                        for (int p = 0; p < problemIndexIds.length; p++) {

                            problem = (PermutationProblem<PermutationSolution<Integer>>) new DHFSP(jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i],problemIndexIds[0]);
                        //测试参数
                        for (int m = 0; m < algorithms.length; m++) {
                            for (int r = 0; r < rangesOfR1R2.length; r++) {
                                for (int s = 0; s < swarmSizes.length; s++) {
                                    for (int t = 0; t < crossoverRates.length; t++) {
                                        for (int o = 0; o < mutationRates.length; o++) {
                                            for (int q = 0; q < pmxCrossover.length; q++) {
                                                for (int a = 0; a < V1mutationProbability.length; a++) {
                                                    for (int w = 0; w < DERates.length; w++) {
                                                        for (int z = 0; z < DEcrossoverRates.length; z++) {
                                                            for (int x = 0; x < DEmutationRates.length; x++) {
                                                                for (int u = 0; u < crossoverRates4worker.length; u++) {
                                                                    for (int c = 0; c < crossoverRates4machine.length; c++) {
                                                                        for (int b = 0; b < mutationRates4worker.length; b++) {
                                                                            for (int v = 0; v < mutationRates4machine.length; v++) {
                                                                                if (algorithms[m].equals("SPEA2")) {
                                                                                    SPEA2Run.mainexe(problem,
                                                                                            jobIndexIds[j], stageIndexIds[k], factoryIndexIds[i], problemIndexIds[0],
                                                                                            //swarmSizes[s] / 3, swarmSizes[s] - (swarmSizes[s] / 3) * 2, swarmSizes[s] / 3,
                                                                                            swarmSizes[s],
                                                                                            rangesOfR1R2[r],
                                                                                            crossoverRates[t], mutationRates[o],
                                                                                            pmxCrossover[q], V1mutationProbability[a],
                                                                                            DERates[w], DEcrossoverRates[z], DEmutationRates[x], crossoverRates4worker[u],crossoverRates4machine[c],mutationRates4worker[b],mutationRates4machine[v],
                                                                                            maxGen * swarmSizes[s],
                                                                                            solutionFolderName, indexFolderName, runTime, Nonparametric);
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }}
                    }
                }
            }System.out.println("原数据计算完成");
        } else {

            calculateRefSolutions(solutionFolderName, indexFolderName, algorithms, rangesOfR1R2,pmxCrossover ,V1mutationProbability,swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
            runningIndex1(solutionFolderName, indexFolderName, algorithms, rangesOfR1R2, pmxCrossover ,V1mutationProbability,swarmSizes, DERates, crossoverRates, mutationRates, DEcrossoverRates, DEmutationRates);    //带参数
            System.out.println("指标计算完成");}

    }

    //计算一个问题的最终合并后的非支配解，并计算边界值（最坏值），保存到文件里
    private static void calculateRefSolutions(String solutionFolderName,
                                              String indexFolderName,
                                              String[] algorithms,
                                              double[] rand,
                                              double[] pmxCrossover ,
                                              double[] V1mutationProbability,
                                              int[] swarmSize,
                                              double[] DERates,
                                              double[] crossoverRates,
                                              double[] mutationRates,
                                              double[] DEcrossoverRates,
                                              double[] DEmutationRates) throws IOException {
        //跑指标数据（自己写的指标代码，不是jmetal自带的代码）
        int indexCount = 0;


        for (int j = 0; j < jobIndexIds.length; j++) {
            for (int k = 0; k < stageIndexIds.length; k++) {
                for (int i = 0; i < factoryIndexIds.length; i++) {
                    for (int p = 0; p < problemIndexIds.length; p++) {
                        //
                        String strProblemName = new String(jobIndexIds[j] + "_" + stageIndexIds[k] + "_" + factoryIndexIds[i]+ "_" + problemIndexIds[p]);
                        //String strProblemName = new String(jobIndexIds[j] + "_" + machineIndexIds[k] + "_" + problemIndexIds[i]);
                        //String strFilePath4outputAllPareto4oneProblem = new String(indexFolderName+"Pareto_"+strProblemName+".txt");

                        //计算一个问题的所有非支配解
                        UtilPareto pareto4OneProblem = new UtilPareto();

                        for (int a = 0; a < algorithms.length; a++) {
                            //计算一个问题的一个方法的非支配解
                            UtilPareto pareto4OneProblemOneMethod = new UtilPareto();

                            for (int x = 0; x < rand.length; x++) {
                                for (int q = 0; q < pmxCrossover.length; q++) {
                                    for (int y = 0; y < V1mutationProbability.length; y++) {
                                        for (int c = 0; c < swarmSize.length; c++) {
                                            for (int t = 0; t < crossoverRates.length; t++) {
                                                for (int m = 0; m < mutationRates.length; m++) {
                                                    for (int v = 0; v < DERates.length; v++) {
                                                        for (int g = 0; g < DEcrossoverRates.length; g++) {
                                                            for (int d = 0; d < DEmutationRates.length; d++) {
                                                                //针对一个问题的一个方法的一个参数，得出该问题的Pareto前沿面
                                                                //String inputFileName = new String(solutionFolderName + "solution-"+strProblemName+"-"+algorithms[a]+ "_" +
                                                                //        rand[x] + "_" + swarmSize[c] + "_" + DERates[v] + "_" + crossoverRates[t] + "_" + mutationRates[m] + ".txt");

                                                                StringBuilder sbFileName = new StringBuilder();
//                                                                sbFileName.append(solutionFolderName).append("solution-");
                                                                sbFileName.append(solutionFolderName).append("object-");
                                                                sbFileName.append(strProblemName).append("-");
//                                                                sbFileName.append(algorithms[a]).append("_");
                                                                sbFileName.append(algorithms[a]).append("-");//之前是_
                                                                sbFileName.append(rand[x]).append("_");
                                                                sbFileName.append(pmxCrossover[q]).append("_");
                                                                sbFileName.append(V1mutationProbability[y]).append("_");
                                                                sbFileName.append(swarmSize[c]).append("_");
                                                                sbFileName.append(crossoverRates[t]).append("_");
                                                                sbFileName.append(mutationRates[m]).append("_");
                                                                sbFileName.append(DERates[v]).append("_");
                                                                sbFileName.append(DEcrossoverRates[g]).append("_");
                                                                sbFileName.append(DEmutationRates[d]);
                                                                sbFileName.append(".txt");

                                                                indexCount++;
                                                                System.out.println(indexCount + sbFileName.toString());

                                                                UtilPareto pareto4onePara = new UtilPareto();
                                                                pareto4onePara.getParetoFromFile4OneProblemOneMethodOnePara(sbFileName.toString());

                                                                pareto4OneProblemOneMethod.updateParetoFromData(pareto4onePara.getParetoFront());

//                                                                for (Float[] floats : pareto4onePara.getParetoFront()) {
//                                                                    for (Float aFloat : floats) {
//                                                                        System.out.print(aFloat+" ");
//                                                                    }
//                                                                    System.out.println();
//                                                                }
//                                                                System.out.println();
                                                                pareto4OneProblemOneMethod.updateMaxValue(pareto4onePara.getMaxvalue());
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            pareto4OneProblemOneMethod.outputPareto4OneProblemOneMethod(indexFolderName, strProblemName, algorithms[a]);

                            pareto4OneProblem.updateParetoFromData(pareto4OneProblemOneMethod.getParetoFront());
                            pareto4OneProblem.updateMaxValue(pareto4OneProblemOneMethod.getMaxvalue());

                        }


                        pareto4OneProblem.outputPareto4OneProblem(indexFolderName, strProblemName);
                        pareto4OneProblem.outputMaxValue4OneProblem(indexFolderName, strProblemName);
                    }
                }
            }}
    }


    //跑带参数的指标
    private static void runningIndex1(String solutionFolderName,
                                      String indexFolderName,
                                      String[] algorithms,
                                      double[] rangesOfR1R2,
                                      double[] pmxCrossover ,
                                      double[] V1mutationProbability,
                                      int[] swarmSizes,
                                      double[] DERates,
                                      double[] crossoverRates,
                                      double[] mutationRates,
                                      double[] DEcrossoverRates,
                                      double[] DEmutationRates) throws IOException {
        //跑指标数据（自己写的指标代码，不是jmetal自带的代码）
        BufferedWriter bw = new BufferedWriter(new FileWriter(indexFolderName + "IndexsResults.txt"));
        BufferedWriter bw1 = new BufferedWriter(new FileWriter(indexFolderName + "IndexsResults1.txt"));
        BufferedWriter bw2 = new BufferedWriter(new FileWriter(indexFolderName + "Results.txt"));

        //预输出表头
        bw.write("no. of jobs, no. of manchines, problem id, method, range of r1 and r2,pmxCrossover ,V1mutationProbability, popsize, crossover rate, mutation rate, DE rate, DEcrossoverRates, DEmutationRates, run, GD, IGD, HV, Spacing, Spread");
        bw.newLine();

        bw1.write("problemName,algorithmName,indexName,01,02,03,04,05,06,07,08,09,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30");
        bw1.newLine();

        //bw2.write("problemName,algorithmName,indexName,average,variance");
        //bw2.newLine();


        for (int j = 0; j < jobIndexIds.length; j++) {
            for (int k = 0; k < stageIndexIds.length; k++) {
                for (int i = 0; i < factoryIndexIds.length; i++) {
                    for (int p = 0; p < problemIndexIds.length; p++) {
                        //计算一个问题的所有非支配解
                        UtilPareto pareto4OneProblem = new UtilPareto();

                        String strProblemName = new String(jobIndexIds[j] + "_" + stageIndexIds[k] + "_" + factoryIndexIds[i]+ "_" + problemIndexIds[p]);
                        String strFileNameOfParetoAll = new String(indexFolderName + "Pareto_" + strProblemName + ".txt");
                        String strFileNameOfMaxValue = new String(indexFolderName + "MaxValue_" + strProblemName + ".txt");

                        pareto4OneProblem.getParetoFromOneProblem(indexFolderName, strProblemName);
                        pareto4OneProblem.getMaxValueFromOneProblem(indexFolderName, strProblemName);

                        for (int a = 0; a < algorithms.length; a++) {

                            for (int x = 0; x < rangesOfR1R2.length; x++) {
                                for (int q = 0; q < pmxCrossover.length; q++) {
                                    for (int y = 0; y < V1mutationProbability.length; y++) {
                                        for (int c = 0; c < swarmSizes.length; c++) {
                                            for (int t = 0; t < crossoverRates.length; t++) {
                                                for (int m = 0; m < mutationRates.length; m++) {
                                                    for (int v = 0; v < DERates.length; v++) {
                                                        for (int g = 0; g < DEcrossoverRates.length; g++) {
                                                            for (int d = 0; d < DEmutationRates.length; d++) {
                                                                //针对相同问题编号，得出该问题的Pareto前沿面

                                                                ArrayList<Indexs> indexsArrayList = new ArrayList<>();

                                                                //读取原始数据，计算出目标值的最大最小值
                                                                UtilPopulation populationclass = new UtilPopulation();
                                                                float[][][] population = populationclass.Read_Experimental_data(solutionFolderName,
                                                                        strProblemName, algorithms[a], rangesOfR1R2[x],pmxCrossover [q],V1mutationProbability[y],swarmSizes[c],
                                                                        DERates[v], crossoverRates[t], mutationRates[m],
                                                                        DEcrossoverRates[g], DEmutationRates[d], runTime);

                                                            /*float[][][] population = populationclass.Read_Experimental_datapri(solutionFolderName,
                                                                    strProblemName, algorithms[a], rangesOfR1R2[x],swarmSizes[c],
                                                                    DERates[v], crossoverRates[t], mutationRates[m],
                                                                    DEcrossoverRates[g], DEmutationRates[d], runTime);*/



                                                                String s = populationclass.MaxandMintoString();   //目标1，2的最大最小值

                                                                //计算指标值
                                                                Indexs indexs = new Indexs(pareto4OneProblem.getMaxvalue(), pareto4OneProblem.getParetoFront(), population);

                                                                for (int e = 1; e <= runTime; e++) {   //新加的

                                                                    //写问题名
                                                                    bw.write(jobIndexIds[j] + "," +
                                                                            stageIndexIds[k] + "," +
                                                                            factoryIndexIds[i] + "," +
                                                                            problemIndexIds[p] + "," +
                                                                            algorithms[a] + "," +
                                                                            rangesOfR1R2[x] + "," +
                                                                            pmxCrossover[q] + "," +
                                                                            V1mutationProbability[y] + "," +
                                                                            swarmSizes[c] + "," +
                                                                            crossoverRates[t] + "," +
                                                                            mutationRates[m] + "," +
                                                                            DERates[v] + "," +
                                                                            DEcrossoverRates[g] + "," +
                                                                            DEmutationRates[d] + "," +
                                                                            e);
                                                                    //bw2.write(numberOfJobs[j] + "," + numberOfMachines[k] + "," + snumber[0] + "," + rand[x] + "," + SwarmSize[c] + "," + Probability[v] + "," + e);

                                                                    //写数据
                                                                    bw.write("," + indexs.indexstoString(e));
                                                                    bw.newLine();
                                                                    bw.flush();
                                                                    // indexsArrayList.add(indexs);
                                                                }

                                                                bw1.write(jobIndexIds[j] + "," +
                                                                        stageIndexIds[k] + "," +
                                                                        factoryIndexIds[i] + "," +
                                                                        problemIndexIds[p] + "," +
                                                                        algorithms[a] + "," +
                                                                        rangesOfR1R2[x] + "," +
                                                                        pmxCrossover[q] + "," +
                                                                        V1mutationProbability[y] + "," +
                                                                        swarmSizes[c] + "," +
                                                                        crossoverRates[t] + "," +
                                                                        mutationRates[m] + "," +
                                                                        DERates[v] + "," +
                                                                        DEcrossoverRates[g] + "," +
                                                                        DEmutationRates[d]);
                                                                bw1.write("," + indexs.indexstoString1());
                                                                bw1.newLine();
                                                                bw1.flush();


                                                                bw2.write(jobIndexIds[j] + "," +
                                                                        stageIndexIds[k] + "," +
                                                                        factoryIndexIds[i] + "," +
                                                                        problemIndexIds[p] + "," +
                                                                        algorithms[a] + "," +
                                                                        rangesOfR1R2[x] + "," +
                                                                        pmxCrossover[q] + "," +
                                                                        V1mutationProbability[y] + "," +
                                                                        swarmSizes[c] + "," +
                                                                        crossoverRates[t] + "," +
                                                                        mutationRates[m] + "," +
                                                                        DERates[v] + "," +
                                                                        DEcrossoverRates[g] + "," +
                                                                        DEmutationRates[d]);
                                                                bw2.write("," + algorithms[a]);
                                                                bw2.write("," + indexs.toString());
                                                                bw2.newLine();
                                                                bw2.flush();

                                                                indexsArrayList.add(indexs);
                                                                //bw1.newLine();
                                                                // }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        bw.flush();
                        bw2.flush();
                    }}
            }
        }

        bw.flush();
        bw.close();

        bw2.flush();
        bw2.close();

    }



    private static void calculateSolutions(String solutionFolderName,
                                           String indexFolderName,
                                           String[] algorithms) throws IOException {
        //跑指标数据（自己写的指标代码，不是jmetal自带的代码）
        int indexCount = 0;


        for (int j = 0; j < jobIndexIds.length; j++) {
            for (int k = 0; k < stageIndexIds.length; k++) {
                for (int i = 0; i < factoryIndexIds.length; i++) {
                    for (int p = 0; p < problemIndexIds.length; p++) { ////可能是problem id, 这里只用第一个问题
                        //
                        String strProblemName = new String(jobIndexIds[j] + "_" + stageIndexIds[k] + "_" + factoryIndexIds[i]+ "_" + problemIndexIds[p]);
                        System.out.println(strProblemName);
                        //String strFilePath4outputAllPareto4oneProblem = new String(indexFolderName+"Pareto_"+strProblemName+".txt");

                        //计算一个问题的所有非支配解
                        UtilPareto pareto4OneProblem = new UtilPareto();

                        for (int a = 0; a < algorithms.length; a++) {
                            //计算一个问题的一个方法的非支配解
                            UtilPareto pareto4OneProblemOneMethod = new UtilPareto();
                            //针对一个问题的一个方法的一个参数，得出该问题的Pareto前沿面
                            //String inputFileName = new String(solutionFolderName + "solution-"+strProblemName+"-"+algorithms[a]+ "_" +
                            //        rand[x] + "_" + swarmSize[c] + "_" + DERates[v] + "_" + crossoverRates[t] + "_" + mutationRates[m] + ".txt");

                            StringBuilder sbFileName = new StringBuilder();
                            sbFileName.append(solutionFolderName).append("object-");
                            sbFileName.append(strProblemName).append("-");
                            //sbFileName.append(algorithms[a]).append("_");
                            sbFileName.append(algorithms[a]);
                            sbFileName.append(".txt");

                            indexCount++;
                            System.out.println(indexCount + sbFileName.toString());

                            UtilPareto pareto4onePara = new UtilPareto();

                            pareto4onePara.getParetoFromFile4OneProblemOneMethodOnePara(sbFileName.toString());

                            pareto4OneProblemOneMethod.updateParetoFromData(pareto4onePara.getParetoFront());
                            pareto4OneProblemOneMethod.updateMaxValue(pareto4onePara.getMaxvalue());



                                                        /*}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }*/
                            pareto4OneProblemOneMethod.outputPareto4OneProblemOneMethod(indexFolderName, strProblemName, algorithms[a]);

                            pareto4OneProblem.updateParetoFromData(pareto4OneProblemOneMethod.getParetoFront());
                            pareto4OneProblem.updateMaxValue(pareto4OneProblemOneMethod.getMaxvalue());



                        }


                        pareto4OneProblem.outputPareto4OneProblem(indexFolderName, strProblemName);
                        pareto4OneProblem.outputMaxValue4OneProblem(indexFolderName, strProblemName);
                    }
                }
            }}
    }


    //跑带参数的指标
    private static void runningIndex(String solutionFolderName,
                                     String indexFolderName,
                                     String[] algorithms
    ) throws IOException {
        //跑指标数据（自己写的指标代码，不是jmetal自带的代码）
        BufferedWriter bw = new BufferedWriter(new FileWriter(indexFolderName + "IndexsResults.txt"));
        BufferedWriter bw1 = new BufferedWriter(new FileWriter(indexFolderName + "IndexsResults1.txt"));
        BufferedWriter bw2 = new BufferedWriter(new FileWriter(indexFolderName + "Results.txt"));

        //预输出表头
        bw.write("no. of jobs, no. of manchines, problem id, method, range of r1 and r2,pmxCrossover ,V1mutationProbability, popsize, crossover rate, mutation rate, DE rate, DEcrossoverRates, DEmutationRates, run, GD, IGD, HV, Spacing, Spread");
        bw.newLine();

        bw1.write("problemName,algorithmName,indexName,01,02,03,04,05,06,07,08,09,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30");
        bw1.newLine();

        //bw2.write("problemName,algorithmName,indexName,average,variance");
        //bw2.newLine();

        for (int j = 0; j < jobIndexIds.length; j++) {
            for (int k = 0; k < stageIndexIds.length; k++) {
                for (int i = 0; i < factoryIndexIds.length; i++) {
                    for (int p = 0; p < problemIndexIds.length; p++) {
                        //计算一个问题的所有非支配解
                        UtilPareto pareto4OneProblem = new UtilPareto();

                        String strProblemName = new String(jobIndexIds[j] + "_" + stageIndexIds[k] + "_" + factoryIndexIds[i]+ "_" + problemIndexIds[p]);
                        String strFileNameOfParetoAll = new String(indexFolderName + "Pareto_" + strProblemName + ".txt");
                        String strFileNameOfMaxValue = new String(indexFolderName + "MaxValue_" + strProblemName + ".txt");

                        pareto4OneProblem.getParetoFromOneProblem(indexFolderName, strProblemName);
                        pareto4OneProblem.getMaxValueFromOneProblem(indexFolderName, strProblemName);

                        for (int a = 0; a < algorithms.length; a++) {
//                            System.out.println(a);
                            //针对相同问题编号，得出该问题的Pareto前沿面

                            ArrayList<Indexs> indexsArrayList = new ArrayList<>();

                            //读取原始数据，计算出目标值的最大最小值
                            UtilPopulation populationclass = new UtilPopulation();
                            float[][][] population = populationclass.Read_Experimental_data_Nonparametric(solutionFolderName,
                                    strProblemName, algorithms[a], runTime);

                            String s = populationclass.MaxandMintoString();   //目标1，2的最大最小值

                            //计算指标值
                            Indexs indexs = new Indexs(pareto4OneProblem.getMaxvalue(), pareto4OneProblem.getParetoFront(), population);

                            for (int e = 1; e <= runTime; e++) {   //新加的

                                //写问题名
                                bw.write(jobIndexIds[j] + "," +
                                        stageIndexIds[k] + "," +
                                        factoryIndexIds[i] + "," +
                                        problemIndexIds[p] + "," +
                                        algorithms[a] + "," +
                                        e);
                                //写数据
                                bw.write("," + indexs.indexstoString(e));
                                bw.newLine();
                                bw.flush();
                            }

                            bw1.write(jobIndexIds[j] + "_" +
                                    stageIndexIds[k] + "_" +
                                    factoryIndexIds[i] + "_" +
                                    problemIndexIds[p] + "," +
                                    algorithms[a]);
                            //写数据
                            bw1.write("," + indexs.indexstoString1());
                            bw1.newLine();
                            bw1.flush();


                            bw2.write(jobIndexIds[j] + "_" +
                                    stageIndexIds[k] + "_" +
                                    factoryIndexIds[i] + "_" +
                                    problemIndexIds[p] + "," +
                                    algorithms[a] );
                            //bw2.write("," + algorithms[a]);
                            bw2.write("," + indexs.toString());
                            bw2.newLine();
                            bw2.flush();

                            indexsArrayList.add(indexs);
                        }

                        bw.flush();
                        bw1.flush();
                        bw2.flush();
                    }
                }}
        }

        bw.flush();
        bw.close();

        bw1.flush();
        bw1.close();

        bw2.flush();
        bw2.close();

    }




    private static void calculateRefSolutions_new(String solutionFolderName,
                                              String indexFolderName,
                                              String[] algorithms,
                                              double[] rand,
                                              double[] pmxCrossover ,
                                              double[] V1mutationProbability,
                                              int[] swarmSize,
                                              double[] DERates,
                                              double[] crossoverRates,
                                              double[] mutationRates,
                                              double[] DEcrossoverRates,
                                              double[] DEmutationRates,double[] crossoverRates4worker,double[] crossoverRates4machine,double[] mutationRates4worker,double[] mutationRates4machine,
                                                  int[] localsearch) throws IOException {
        //跑指标数据（自己写的指标代码，不是jmetal自带的代码）
        int indexCount = 0;


        for (int j = 0; j < jobIndexIds.length; j++) {
            for (int k = 0; k < stageIndexIds.length; k++) {
                for (int i = 0; i < factoryIndexIds.length; i++) {
                    for (int p = 0; p < problemIndexIds.length; p++) {
                        //
                        String strProblemName = new String(jobIndexIds[j] + "_" + stageIndexIds[k] + "_" + factoryIndexIds[i]+ "_" + problemIndexIds[p]);
                        //String strProblemName = new String(jobIndexIds[j] + "_" + machineIndexIds[k] + "_" + problemIndexIds[i]);
                        //String strFilePath4outputAllPareto4oneProblem = new String(indexFolderName+"Pareto_"+strProblemName+".txt");

                        //计算一个问题的所有非支配解
                        UtilPareto pareto4OneProblem = new UtilPareto();

                        for (int a = 0; a < algorithms.length; a++) {
                            //计算一个问题的一个方法的非支配解
                            UtilPareto pareto4OneProblemOneMethod = new UtilPareto();

                            for (int x = 0; x < rand.length; x++) {
                                for (int q = 0; q < pmxCrossover.length; q++) {
                                    for (int y = 0; y < V1mutationProbability.length; y++) {
                                        for (int c = 0; c < swarmSize.length; c++) {
                                            for (int t = 0; t < crossoverRates.length; t++) {
                                                for (int m = 0; m < mutationRates.length; m++) {
                                                    for (int v = 0; v < DERates.length; v++) {
                                                        for (int g = 0; g < DEcrossoverRates.length; g++) {
                                                            for (int d = 0; d < DEmutationRates.length; d++) {
                                                                for (int u = 0; u < crossoverRates4worker.length; u++) {
                                                                    for (int z = 0; z < crossoverRates4machine.length; z++) {
                                                                        for (int b = 0; b < mutationRates4worker.length; b++) {
                                                                            for (int h = 0; h < mutationRates4machine.length; h++) {
                                                                                for (int n = 0; n < localsearch.length; n++) {


                                                                                //针对一个问题的一个方法的一个参数，得出该问题的Pareto前沿面
                                                                                //String inputFileName = new String(solutionFolderName + "solution-"+strProblemName+"-"+algorithms[a]+ "_" +
                                                                                //        rand[x] + "_" + swarmSize[c] + "_" + DERates[v] + "_" + crossoverRates[t] + "_" + mutationRates[m] + ".txt");

                                                                                StringBuilder sbFileName = new StringBuilder();
//                                                                                sbFileName.append(solutionFolderName).append("solution-");
                                                                                sbFileName.append(solutionFolderName).append("object-");
                                                                                sbFileName.append(strProblemName).append("-");
//                                                                                sbFileName.append(algorithms[a]).append("_");
                                                                                sbFileName.append(algorithms[a]).append("-");//之前是_
                                                                                sbFileName.append(rand[x]).append("_");
                                                                                sbFileName.append(pmxCrossover[q]).append("_");
                                                                                sbFileName.append(V1mutationProbability[y]).append("_");
                                                                                sbFileName.append(swarmSize[c]).append("_");
                                                                                sbFileName.append(crossoverRates[t]).append("_");
                                                                                sbFileName.append(mutationRates[m]).append("_");
                                                                                sbFileName.append(DERates[v]).append("_");
                                                                                sbFileName.append(DEcrossoverRates[g]).append("_");
                                                                                sbFileName.append(DEmutationRates[d]).append("_");
                                                                                sbFileName.append(crossoverRates4worker[u]).append("_");
                                                                                sbFileName.append(crossoverRates4machine[z]).append("_");
                                                                                sbFileName.append(mutationRates4worker[b]).append("_");
                                                                                sbFileName.append(mutationRates4machine[h]).append("_");
                                                                                sbFileName.append(localsearch[n]);
                                                                                sbFileName.append(".txt");

                                                                                indexCount++;
                                                                                System.out.println(indexCount + sbFileName.toString());

                                                                                UtilPareto pareto4onePara = new UtilPareto();
                                                                                pareto4onePara.getParetoFromFile4OneProblemOneMethodOnePara(sbFileName.toString());

                                                                                pareto4OneProblemOneMethod.updateParetoFromData(pareto4onePara.getParetoFront());

//                                                                                for (Float[] floats : pareto4onePara.getParetoFront()) {
//                                                                                    for (Float aFloat : floats) {
//                                                                                        System.out.print(aFloat+" ");
//                                                                                    }
//                                                                                    System.out.println();
//                                                                                }
//                                                                                System.out.println();
                                                                                pareto4OneProblemOneMethod.updateMaxValue(pareto4onePara.getMaxvalue());

                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            pareto4OneProblemOneMethod.outputPareto4OneProblemOneMethod(indexFolderName, strProblemName, algorithms[a]);

                            pareto4OneProblem.updateParetoFromData(pareto4OneProblemOneMethod.getParetoFront());
                            pareto4OneProblem.updateMaxValue(pareto4OneProblemOneMethod.getMaxvalue());

                        }


                        pareto4OneProblem.outputPareto4OneProblem(indexFolderName, strProblemName);
                        pareto4OneProblem.outputMaxValue4OneProblem(indexFolderName, strProblemName);
                    }
                }
            }}
    }
    private static void runningIndexnew(String solutionFolderName,
                                      String indexFolderName,
                                      String[] algorithms,
                                      double[] rangesOfR1R2,
                                      double[] pmxCrossover ,
                                      double[] V1mutationProbability,
                                      int[] swarmSizes,
                                      double[] DERates,
                                      double[] crossoverRates,
                                      double[] mutationRates,
                                      double[] DEcrossoverRates,
                                      double[] DEmutationRates,
                                        double[] crossoverRates4worker,double[] crossoverRates4machine,
                                        double[] mutationRates4worker,double[] mutationRates4machine,int[] localsearch) throws IOException {
        //跑指标数据（自己写的指标代码，不是jmetal自带的代码）
        BufferedWriter bw = new BufferedWriter(new FileWriter(indexFolderName + "IndexsResults.txt"));
        BufferedWriter bw1 = new BufferedWriter(new FileWriter(indexFolderName + "IndexsResults1.txt"));
        BufferedWriter bw2 = new BufferedWriter(new FileWriter(indexFolderName + "Results.txt"));

        //预输出表头
        bw.write("no. of jobs, no. of manchines, problem id, method, range of r1 and r2,pmxCrossover ,V1mutationProbability, popsize, crossover rate, mutation rate, DE rate, DEcrossoverRates, DEmutationRates, crossoverRates4worker, crossoverRates4machine, mutationRates4worker, mutationRates4machine, localsearch, run, GD, IGD, HV, Spacing, Spread");
        bw.newLine();

        bw1.write("problemName,algorithmName,indexName,01,02,03,04,05,06,07,08,09,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30");
        bw1.newLine();

        //bw2.write("problemName,algorithmName,indexName,average,variance");
        //bw2.newLine();


        for (int j = 0; j < jobIndexIds.length; j++) {
            for (int k = 0; k < stageIndexIds.length; k++) {
                for (int i = 0; i < factoryIndexIds.length; i++) {
                    for (int p = 0; p < problemIndexIds.length; p++) {
                        //计算一个问题的所有非支配解
                        UtilPareto pareto4OneProblem = new UtilPareto();

                        String strProblemName = new String(jobIndexIds[j] + "_" + stageIndexIds[k] + "_" + factoryIndexIds[i]+ "_" + problemIndexIds[p]);
                        String strFileNameOfParetoAll = new String(indexFolderName + "Pareto_" + strProblemName + ".txt");
                        String strFileNameOfMaxValue = new String(indexFolderName + "MaxValue_" + strProblemName + ".txt");

                        pareto4OneProblem.getParetoFromOneProblem(indexFolderName, strProblemName);
                        pareto4OneProblem.getMaxValueFromOneProblem(indexFolderName, strProblemName);

                        for (int a = 0; a < algorithms.length; a++) {

                            for (int x = 0; x < rangesOfR1R2.length; x++) {
                                for (int q = 0; q < pmxCrossover.length; q++) {
                                    for (int y = 0; y < V1mutationProbability.length; y++) {
                                        for (int c = 0; c < swarmSizes.length; c++) {
                                            for (int t = 0; t < crossoverRates.length; t++) {
                                                for (int m = 0; m < mutationRates.length; m++) {
                                                    for (int v = 0; v < DERates.length; v++) {
                                                        for (int g = 0; g < DEcrossoverRates.length; g++) {
                                                            for (int d = 0; d < DEmutationRates.length; d++) {
                                                                for (int u = 0; u < crossoverRates4worker.length; u++) {
                                                                    for (int z = 0; z < crossoverRates4machine.length; z++) {
                                                                        for (int b = 0; b < mutationRates4worker.length; b++) {
                                                                            for (int h = 0; h < mutationRates4machine.length; h++) {
                                                                                for (int n = 0; n < localsearch.length; n++) {


                                                                                //针对相同问题编号，得出该问题的Pareto前沿面

                                                                                ArrayList<Indexs> indexsArrayList = new ArrayList<>();

                                                                                //读取原始数据，计算出目标值的最大最小值
                                                                                UtilPopulation populationclass = new UtilPopulation();
//                                                                float[][][] population = populationclass.Read_Experimental_data(solutionFolderName,
//                                                                        strProblemName, algorithms[a], rangesOfR1R2[x],pmxCrossover [q],V1mutationProbability[y],swarmSizes[c],
//                                                                        DERates[v], crossoverRates[t], mutationRates[m],
//                                                                        DEcrossoverRates[g], DEmutationRates[d], runTime);

                                                            /*float[][][] population = populationclass.Read_Experimental_datapri(solutionFolderName,
                                                                    strProblemName, algorithms[a], rangesOfR1R2[x],swarmSizes[c],
                                                                    DERates[v], crossoverRates[t], mutationRates[m],
                                                                    DEcrossoverRates[g], DEmutationRates[d], runTime);*/

                                                                                float[][][] population = populationclass.Read_Experimental_data_new(solutionFolderName,
                                                                                        strProblemName, algorithms[a], rangesOfR1R2[x], pmxCrossover[q], V1mutationProbability[y], swarmSizes[c],
                                                                                        DERates[v], crossoverRates[t], mutationRates[m],
                                                                                        DEcrossoverRates[g], DEmutationRates[d], crossoverRates4worker[u], crossoverRates4machine[z],mutationRates4worker[b],mutationRates4machine[h],localsearch[n],runTime);
//                                                                    for (float[][] floats : population) {
//                                                                        for (float[] aFloat : floats) {
//                                                                            System.out.println(Arrays.toString(aFloat));
//                                                                        }
//                                                                        System.out.println();
//                                                                    }
//                                                                    try {
//                                                                        Thread.sleep(999999);
//                                                                    } catch (InterruptedException e) {
//                                                                        throw new RuntimeException(e);
//                                                                    }
                                                                                String s = populationclass.MaxandMintoString();   //目标1，2的最大最小值

                                                                                //计算指标值
                                                                                Indexs indexs = new Indexs(pareto4OneProblem.getMaxvalue(), pareto4OneProblem.getParetoFront(), population);

                                                                                for (int e = 1; e <= runTime; e++) {   //新加的

                                                                                    //写问题名
                                                                                    bw.write(jobIndexIds[j] + "," +
                                                                                            stageIndexIds[k] + "," +
                                                                                            factoryIndexIds[i] + "," +
                                                                                            problemIndexIds[p] + "," +
                                                                                            algorithms[a] + "," +
                                                                                            rangesOfR1R2[x] + "," +
                                                                                            pmxCrossover[q] + "," +
                                                                                            V1mutationProbability[y] + "," +
                                                                                            swarmSizes[c] + "," +
                                                                                            crossoverRates[t] + "," +
                                                                                            mutationRates[m] + "," +
                                                                                            DERates[v] + "," +
                                                                                            DEcrossoverRates[g] + "," +
                                                                                            DEmutationRates[d] + "," +
                                                                                            crossoverRates4worker[u] + "," +
                                                                                            crossoverRates4machine[z] + "," +
                                                                                            mutationRates4worker[b] + "," +
                                                                                            mutationRates4machine[h] + "," +
                                                                                            localsearch[n] + "," +
                                                                                            e);
                                                                                    //bw2.write(numberOfJobs[j] + "," + numberOfMachines[k] + "," + snumber[0] + "," + rand[x] + "," + SwarmSize[c] + "," + Probability[v] + "," + e);

                                                                                    //写数据
                                                                                    bw.write("," + indexs.indexstoString(e));
                                                                                    bw.newLine();
                                                                                    bw.flush();
                                                                                    // indexsArrayList.add(indexs);
                                                                                }

                                                                                bw1.write(jobIndexIds[j] + "," +
                                                                                        stageIndexIds[k] + "," +
                                                                                        factoryIndexIds[i] + "," +
                                                                                        problemIndexIds[p] + "," +
                                                                                        algorithms[a] + "," +
                                                                                        rangesOfR1R2[x] + "," +
                                                                                        pmxCrossover[q] + "," +
                                                                                        V1mutationProbability[y] + "," +
                                                                                        swarmSizes[c] + "," +
                                                                                        crossoverRates[t] + "," +
                                                                                        mutationRates[m] + "," +
                                                                                        DERates[v] + "," +
                                                                                        DEcrossoverRates[g] + "," +
                                                                                        DEmutationRates[d] + "," +
                                                                                        crossoverRates4worker[u] + "," +
                                                                                        crossoverRates4machine[z]+ "," +
                                                                                        mutationRates4worker[b]+ "," +
                                                                                        mutationRates4machine[h]+ "," +
                                                                                        localsearch[n]);
                                                                                bw1.write("," + indexs.indexstoString1());
                                                                                bw1.newLine();
                                                                                bw1.flush();


                                                                                bw2.write(jobIndexIds[j] + "," +
                                                                                        stageIndexIds[k] + "," +
                                                                                        factoryIndexIds[i] + "," +
                                                                                        problemIndexIds[p] + "," +
                                                                                        algorithms[a] + "," +
                                                                                        rangesOfR1R2[x] + "," +
                                                                                        pmxCrossover[q] + "," +
                                                                                        V1mutationProbability[y] + "," +
                                                                                        swarmSizes[c] + "," +
                                                                                        crossoverRates[t] + "," +
                                                                                        mutationRates[m] + "," +
                                                                                        DERates[v] + "," +
                                                                                        DEcrossoverRates[g] + "," +
                                                                                        DEmutationRates[d] + "," +
                                                                                        crossoverRates4worker[u] + "," +
                                                                                        crossoverRates4machine[z]+ "," +
                                                                                        mutationRates4worker[b]+ "," +
                                                                                        mutationRates4machine[h]+ "," +
                                                                                        localsearch[n]);
                                                                                bw2.write("," + algorithms[a]);
                                                                                bw2.write("," + indexs.toString());
                                                                                bw2.newLine();
                                                                                bw2.flush();

                                                                                indexsArrayList.add(indexs);
                                                                                //bw1.newLine();
                                                                                // }
                                                                            }

                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }

                        bw.flush();
                        bw2.flush();
                    }}
            }
        }

        bw.flush();
        bw.close();

        bw2.flush();
        bw2.close();

    }
}
