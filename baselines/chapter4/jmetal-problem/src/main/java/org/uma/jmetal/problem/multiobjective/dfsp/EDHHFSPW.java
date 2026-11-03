package org.uma.jmetal.problem.multiobjective.dfsp;

import org.uma.jmetal.problem.impl.AbstractIntegerPermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.*;
import java.util.stream.IntStream;

//正常的问题输入class，可以输入多种多样的问题，只需要修改jobs,machines的相关参数。
//  DFSP.java
//
//  Author:
//       hou wenlin
//
//  Copyright (c) 2011 Antonio J. Nebro, Juan J. Durillo
//DFSP的修正版本-修改编解码方式（多加一条向量用于划分工厂）
//DFSP的修正版本-修改编解码方式（多加一条向量用于划分工厂）
//DFSP的修正版本-修改编解码方式（多加一条向量用于划分工厂）

//DFSP1  20*5
//DFSP2  20*10
//DFSP3  20*20
//DFSP4  50*5
//DFSP5  50*10
//DFSP6  50*20
//DFSP7  100*5
//DFSP8  100*10
//DFSP9  100*20
//DFSP10  200*10

//


public class EDHHFSPW extends AbstractIntegerPermutationProblem implements org.uma.jmetal.util.research.SchedulingProblemData {
    private final String instanceFile;
    private final org.uma.jmetal.util.research.model.Instance schedulingInstance;
    @Override public org.uma.jmetal.util.research.model.Instance getSchedulingInstance() { return schedulingInstance; }

    @Override public String getInstanceFile() { return instanceFile; }
    @Override public int getWorkerVectorLength() { return numberOfJobs_; }

    protected int numberOfWorker = 0;
    protected int numberOfJobs_;
    protected int numberOfStages;
    public static int[][] numberOfMachines_;
    protected int numberOfFactories;
    protected int numberOfWorkers;
    protected double[][][] machineSpeed;
    protected int[][][] machinePower;
    protected int problemflag;

    protected int[][] timeMatrix_;     // 时间矩阵（问题集中的内容），标准处理时间

    protected int[][] jobindex;

    protected int machineNumber;

    public static int[][] machinetime;

    protected int[][][] machineWorker;

    public static int[] nw;
    public static double[][] lw;
    protected int[][] cw;

    protected double[][][] jobEndPower;
    protected double[][][] time;
    protected double[][][] jobCost;


    /**
     * Creates a new instance of problem DFSP.
     */

    protected void init(String filename1) throws IOException {

//        System.out.println(getNumberOfMachines_());

//        System.out.println("zhixingle");
//        try {
//            Thread.sleep(999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
        // 读取数据
        int count = 0;
        //numberOfMachines_=new int [numberOfStages];
        numberOfMachines_ = new int[numberOfFactories][numberOfStages];
        machineSpeed = new double[numberOfFactories][numberOfStages][5];
        machinePower = new int[numberOfFactories][numberOfStages][5];


        // 原 timeMatrix_=new int[numberOfStages][numberOfJobs_];
        timeMatrix_ = new int[numberOfJobs_][numberOfStages];

//        nw = new int[10];
        //todo
        nw = new int[numberOfFactories];
//        System.out.println(numberOfFactories);
//        sleep();
//        nw = new int[4];
//        nw = new int[5];
        lw = new double[numberOfFactories][numberOfStages * 5];
        cw = new int[numberOfFactories][numberOfStages * 5];

        BufferedReader data1 = new BufferedReader(new InputStreamReader(new FileInputStream(filename1)));

        // 读取一行数据，数据格式:
        //number of jobs, number of machines, initial seed, upper bound and lower bound :
        //          20           5   873654221        1278        1232
        //processing times :
        //54 83 15 71 77 36 53 38 27 87 76 91 14 29 12 77 32 87 68 94       //  5行20列


        String lineTxt1 = null;
        lineTxt1 = data1.readLine();
        lineTxt1 = data1.readLine();    //无效信息跳过2行


        for (int f = 0; f < numberOfFactories; f++) {
            if ((lineTxt1 = data1.readLine()) != null) {
                String[] strcol = lineTxt1.split(",");   // 分割字符串（一个数后面一个空格）
                //System.out.println(lineTxt1);
                for (int i = 0; i < numberOfStages; i++) {
                    numberOfMachines_[f][i] = Integer.parseInt(strcol[i]);
                    machineNumber = machineNumber + Integer.parseInt(strcol[i]);
                }
            }
        }
//        System.out.println(machineNumber);

        lineTxt1 = data1.readLine();

        for (int f = 0; f < numberOfFactories; f++) {
            for (int i = 0; i < numberOfStages; i++) {
                if ((lineTxt1 = data1.readLine()) != null) {
                    String[] strcol = lineTxt1.split(",");   // 分割字符串（一个数后面一个空格）
                    //System.out.println(lineTxt1);

                    for (int n = 0; n < numberOfMachines_[f][i]; n++) {
                        machineSpeed[f][i][n] = Double.parseDouble(strcol[n]);
                    }

                }
            }
        }
        //System.out.println(machineSpeed);

        lineTxt1 = data1.readLine();

        for (int f = 0; f < numberOfFactories; f++) {
            //System.out.println(lineTxt1);
            for (int i = 0; i < numberOfStages; i++) {
                if ((lineTxt1 = data1.readLine()) != null) {
                    String[] strcol = lineTxt1.split(",");   // 分割字符串（一个数后面一个空格）
                    for (int n = 0; n < numberOfMachines_[f][i]; n++) {
                        machinePower[f][i][n] = Integer.parseInt(strcol[n]);
                    }

                }
            }

        }
//        System.out.println(machinePower);


        lineTxt1 = data1.readLine();
        for (int j = 0; j < numberOfJobs_; j++) {
            if ((lineTxt1 = data1.readLine()) != null) {
                String[] strcol = lineTxt1.split(",");   // 分割字符串（一个数后面一个空格）
                for (int i = 0; i < numberOfStages; i++) {
                    timeMatrix_[j][i] = Integer.parseInt(strcol[i]);
                }
            }
        }

        lineTxt1 = data1.readLine();
        lineTxt1 = data1.readLine();
        String[] strcoll = lineTxt1.split(",");

        for (int i = 0; i < numberOfFactories; i++) {
            nw[i] = Integer.parseInt(strcoll[i]);
            numberOfWorker = numberOfWorker + nw[i];
        }


        setNumberOfWorkers(numberOfWorker);
        //System.out.println(Arrays.toString(nw));

//        for (int[] ints : getNumberOfMachines_()) {
//            for (int anInt : ints) {
//                System.out.print(anInt+" ");
//            }
//            System.out.println();
//        }
//        System.out.println();

        lineTxt1 = data1.readLine();
        for (int i = 0; i < numberOfFactories; i++) {
            if ((lineTxt1 = data1.readLine()) != null) {
                String[] strcol = lineTxt1.split(",");
                for (int j = 0; j < nw[i]; j++) {
                    lw[i][j] = Double.parseDouble(strcol[j]);
//                    lw[i][j] = 1;
                }
            }
        }

//        for (double[] doubles : lw) {
//            for (double aDouble : doubles) {
//                System.out.print(aDouble+" ");
//            }
//            System.out.println();
//        }

        lineTxt1 = data1.readLine();
        for (int i = 0; i < numberOfFactories; i++) {
            if ((lineTxt1 = data1.readLine()) != null) {
                String[] strcol = lineTxt1.split(",");
                for (int j = 0; j < nw[i]; j++) {
                    cw[i][j] = Integer.parseInt(strcol[j]);
//                    System.out.print(cw[i][j] + " ");

                }
//                System.out.println();
//                try {
//                    Thread.sleep(99999999);
//                } catch (InterruptedException e) {
//                    throw new RuntimeException(e);
//                }
                //System.out.println(Arrays.toString(cw[i]));
            }
        }

        //每次工人随机选择工厂 很关键
//        for (int i = 0; i < lw.length; i++) {
//            shuffleRowExcludingZeros(lw,cw,i);
//
//        }
//        System.out.println("1");

        //
//        for (double[] doubles : lw) {
//            for (double aDouble : doubles) {
//                System.out.print(aDouble+" ");
//            }
//            System.out.println();
//        }
//        System.out.println();
//
//        for (int[] ints : cw) {
//            for (int anInt : ints) {
//                System.out.print(anInt+" ");
//            }
//            System.out.println();
//        }
//        System.out.println();
//        try {
//            Thread.sleep(99999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }

        //System.out.println("初始化完成");
        data1.close();

        //加工人，分配工人
        machineWorker = new int[numberOfFactories][numberOfStages][5];
        for (int i = 0; i < numberOfFactories; i++) {
            for (int j = 0; j < numberOfStages; j++) {
                for (int h = 0; h < 5; h++) {
                    machineWorker[i][j][h] = -1;
                }
            }
        }

        int a, b, c;
        double speedmin;
        for (int i = 0; i < numberOfFactories; i++) {

            for (int j = 0; j < nw[i]; j++) {

                speedmin = 100;
                a = b = c = 0;
                for (int h = 0; h < numberOfStages; h++) {
                    for (int n = 0; n < numberOfMachines_[i][h]; n++) {
                        if (speedmin > machineSpeed[i][h][n] && machineWorker[i][h][n] == -1) {
                            speedmin = machineSpeed[i][h][n];
                            a = i;
                            b = h;
                            c = n;
                        }
                    }
                }
                machineWorker[a][b][c] = j;

            }
        }

//        int[][] machineWorkerNew = new int[numberOfJobs_][numberOfStages];


//        for (int[][] ints : machineWorker) {
//            for (int[] anInt : ints) {
//                for (int i : anInt) {
//                    System.out.print(i+" ");
//                }
//                System.out.println();
//            }
//            System.out.println();
//        }


//        for (int i : nw) {
//            System.out.print(i+" ");
//        }
//        System.out.println();

//        for (int[][] ints : machineWorker) {
//            for (int[] anInt : ints) {
//                for (int i : anInt) {
//                    System.out.println(i);
//
//                }
//            }
//        }
//        try {
//            Thread.sleep(99999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }

//        for (int i=0; i<numberOfFactories; i++){
//            for (int j=0;j<numberOfStages;j++){
//                for (int h=0;h<numberOfMachines_[i][j];h++){
//                    System.out.print(machineWorker[i][j][h]+" ");
//                }
//                System.out.println();
//            }
//        }
//        System.out.println();
//        System.out.println();
    }


    //构造函数
    public EDHHFSPW(int numberOfJobs, int numberOfStages, int numberOfFactories, int problemId) throws IOException {

/*                            jobIndexIds = new int[]{10};              //5,10,20,50,100
                            stageIndexIds = new int[]{2};
                            factoryIndexIds = new int[]{3};
                            problemIndexIds = new int[]{1};*/

        setNumberOfVariables(numberOfJobs);
        setNumberOfObjectives(3);
        setNumberOfFactories(numberOfFactories);
        setNumberOfStages(numberOfStages);
        setNumberOfWorkers(18);


        setName("DHFSP");
        this.setNumberOfJobs_(numberOfJobs);
//        this.setNumberOfMachines_(numberOfMachines);
        this.setNumberOfFactories_(numberOfFactories);
        this.setNumberOfStages(numberOfStages);
        this.setNumberOfWorkers(numberOfWorkers);

        //this.setProblemflag(problemflag);
//        timeMatrix_ = new int[numberOfJobs][numberOfStages];
//        for (int[] ints : timeMatrix_) {
//            for (int anInt : ints) {
//                System.out.print(anInt+" ");
//            }
//            System.out.println();
//        }
//        System.out.println();
//        sleep();
        //idleflag = new int[numberOfMachines_];

        instanceFile = org.uma.jmetal.util.research.SchedulingInstanceFiles.resolve(
                numberOfJobs, numberOfStages, numberOfFactories, problemId);
        init(instanceFile);
        schedulingInstance = org.uma.jmetal.util.research.SchedulingEvaluation.load(instanceFile, 4, numberOfJobs, numberOfStages);
    }


    private void setNumberOfMachines_(int[][] numberOfMachines_) {
        this.numberOfMachines_ = numberOfMachines_;
    }


    /**
     * Evaluate() method
     */
    public void evaluate(PermutationSolution<Integer> solution) throws ArrayIndexOutOfBoundsException {
        org.uma.jmetal.util.research.SchedulingEvaluation.evaluate(solution, schedulingInstance);
    }


/*
*   14,13,13,11,6
    14,13,12,12,10,9
    14,13,13,11,10,7,6
*
* */

    protected double[][][] calculate(int[][] solution) throws ArrayIndexOutOfBoundsException {
        //工人分配到机器
        //extracted(solution);
//        for (int[] ints : solution) {
//            System.out.println(Arrays.toString(ints));
//        }

        int[] worker = new int[solution[2].length];//工人向量


        jobEndPower = new double[numberOfFactories][numberOfStages][numberOfJobs_];
        time = new double[numberOfFactories][numberOfStages][numberOfJobs_];  //存储当前粒子的时间完成表  第几个工厂的第几个阶段的第几个工件的时间
        jobCost = new double[numberOfFactories][numberOfStages][numberOfJobs_];

        int[][] timefactories = new int[numberOfFactories][numberOfJobs_];  //三个一维向量  一维向量的空间大小是所有工件的数量大小

        for (int i = 0; i < timefactories.length; i++) {                                //获取行的长度
            for (int j = 0; j < timefactories[i].length; j++) {
                timefactories[i][j] = -1;                                             //三个一维空间的里的数都先存放-1
            }
        }

        int[] count = new int[numberOfFactories];          //记录每个工厂的job数
//        System.out.println("count"+count);

        //完成了把job分配给工厂的功能，并且记录了每个工厂的job数
        for (int i = 0; i < solution[1].length; i++) {
            count[solution[1][i]] = count[solution[1][i]] + 1;  //记录工厂（tem[1][i]）里面的jobs数，每次加1    //也就是说 计算几个1 几个2 几个3
            //把job分给对应工厂
            for (int j = 0; j < solution[0].length; j++) {
                int factoryIndex = solution[1][i];
                if (timefactories[factoryIndex][j] == -1) {
                    timefactories[factoryIndex][j] = solution[0][i];
                    break;   //很重要
                }
            }
        }

//        for (int[] timefactory : timefactories) {
//            for (int i : timefactory) {
//                System.out.print(i+" ");
//            }
//            System.out.println();
//        }
//        System.out.println();
//        sleep();
//        for (int i : count) {
//            System.out.print(i+" ");
//        }
//        System.out.println();

        //计算公式部分
        //System.out.println("遍历每个工厂的Job：");

        int endflag[][] = new int[numberOfFactories][1];

//        int[][] partitionedArray = createPartitionedArray(solution[3], numberOfJobs_);
//        for (int[] ints : partitionedArray) {
//            for (int anInt : ints) {
//                System.out.print(anInt+" ");
//            }
//            System.out.println();
//        }
//        System.out.println();
//        sleep();

        for (int i = 0; i < numberOfFactories; i++) {

            for (int j = 0; j < numberOfJobs_; j++) {
                if (timefactories[i][j] != -1) {
                }
                //System.out.print(" " + timefactories[i][j]);
            }
            //System.out.println();
        }






        //遍历每个工厂
        for (int i = 0; i < numberOfFactories; i++) {
            if (count[i] == 0) {
                continue;
            }

//            System.out.println(machineWorker.length+"长度");
//            没用到
//            int[] worker = new int[nw[i]];
//            for (int x=0;x<nw[i];x++){
//                worker[x]=0;
//            }


//            想一下怎么改第一次的工人分配。
//            nw是每个阶段的工人数量
//            cw是工人花费，lw是工人水平
//            s是阶段数
//            jobtemp[]是每个工厂的的工件的顺序

            double[][][] starttime = new double[numberOfJobs_][][];//第几个工件第几道工序在第几台并行机上开始加工的时间；
            double[][][] finishtime = new double[numberOfJobs_][][];//第几个工件第几道工序在第几台并行机上完成加工的时间；

            //int[][] machinetime ;
            int[] jobtemp = new int[count[i]];         //每个工厂的job都有哪些


            for (int x = 0; x < count[i]; x++) {
                jobtemp[x] = timefactories[i][x];       //每个工厂的job(号)排列
            }
            int[] firstStageMachineSelect = new int[jobtemp.length];
            for (int i1 = 0; i1 < firstStageMachineSelect.length; i1++) {
                firstStageMachineSelect[i1] = solution[3][findElementIndex(solution[0],jobtemp[i1])];
            }
//            System.out.println("jobtemp"+Arrays.toString(jobtemp));
//            System.out.println("firstStageMachineSelect"+Arrays.toString(firstStageMachineSelect));



//            System.out.println();
//            for (int i1 : jobtemp) {
//                System.out.print(i1+" ");
//            }
//            System.out.println();


            //System.out.println(jobtemp);
            double[][] jobtimeTemp = new double[count[i]][numberOfStages];        //作业j的第s阶段的完成时间
            double[] pretimetemp = new double[count[i]];     // count[i]——记录每个工厂的job数



            for (int s = 0; s < numberOfStages; s++) {
                int temp = s*numberOfJobs_;
                List<Integer> tempWorker = new ArrayList<Integer>(numberOfJobs_);
                for (int i1 = temp; i1 < numberOfJobs_*(s+1); i1++) {
                    tempWorker.add(solution[2][i1]);
                }
//                System.out.println(tempWorker);
//                sleep();
                ArrayList<Integer> workerSequence = new ArrayList();

                double[] machinetimePre = new double[numberOfMachines_[i][s]];
                double machinetime[][][] = new double[numberOfFactories][numberOfStages][numberOfMachines_[i][s]];

                starttime = new double[numberOfJobs_][numberOfStages][numberOfMachines_[i][s]];
                finishtime = new double[numberOfJobs_][numberOfStages][numberOfMachines_[i][s]];
                //todo 20241128
//                if(s==0){
//
//                    if(numberOfMachines_[i][s]==1){
//                        for (int j = 0; j < jobtemp.length; j++) {
//                            if(j==0){
//                                time[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][0] / machineSpeed[i][s][firstStageMachineSelect[j]] / lw[i][machineWorker[i][s][firstStageMachineSelect[j]]];
//                                jobtimeTemp[j][s] = time[i][s][jobtemp[j]];
//                                jobEndPower[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][firstStageMachineSelect[j]] / lw[i][machineWorker[i][s][firstStageMachineSelect[j]]] * machinePower[i][s][firstStageMachineSelect[j]];
//                                jobCost[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][firstStageMachineSelect[j]] / lw[i][machineWorker[i][s][firstStageMachineSelect[j]]] * cw[i][machineWorker[i][s][firstStageMachineSelect[j]]];
//                                continue;
//                            }
//                            time[i][s][jobtemp[j]] = time[i][s][jobtemp[j - 1]] + timeMatrix_[jobtemp[j]][firstStageMachineSelect[j]] / machineSpeed[i][s][firstStageMachineSelect[j]] / lw[i][machineWorker[i][s][firstStageMachineSelect[j]]];
//                            jobtimeTemp[j][s] = time[i][s][jobtemp[j]];
//                            jobEndPower[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][firstStageMachineSelect[j]] / lw[i][machineWorker[i][s][firstStageMachineSelect[j]]] * machinePower[i][s][firstStageMachineSelect[j]];
//                            jobCost[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][firstStageMachineSelect[j]] / lw[i][machineWorker[i][s][firstStageMachineSelect[j]]] * cw[i][machineWorker[i][s][firstStageMachineSelect[j]]];
//                        }
//                    }
//                    else {
//                        for (int j = 0; j < jobtemp.length; j++) {
////                      starttime第几个工件第几道工序在第几台并行机上开始加工的时间；
//
//                            starttime[jobtemp[j]][s][firstStageMachineSelect[j]] = machinetime[i][s][firstStageMachineSelect[j]];  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
//                            machinetime[i][s][firstStageMachineSelect[j]] = starttime[jobtemp[j]][s][firstStageMachineSelect[j]] + timeMatrix_[jobtemp[j]][0] / machineSpeed[i][s][firstStageMachineSelect[j]] / lw[i][machineWorker[i][s][firstStageMachineSelect[j]]]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
//                            finishtime[jobtemp[j]][s][firstStageMachineSelect[j]] = machinetime[i][s][firstStageMachineSelect[j]];                 //工件的完工时间就是该机器当前的累计加工时间；
//                            jobtimeTemp[j][s] = finishtime[jobtemp[j]][s][firstStageMachineSelect[j]];
//
//                            //下面这行原来没有
////                            time[i][s][q] = jobtimeTemp[k][s];
//                            jobEndPower[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][firstStageMachineSelect[j]] / lw[i][machineWorker[i][s][firstStageMachineSelect[j]]] * machinePower[i][s][firstStageMachineSelect[j]];
//                            jobCost[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][firstStageMachineSelect[j]] / lw[i][machineWorker[i][s][firstStageMachineSelect[j]]] * cw[i][machineWorker[i][s][firstStageMachineSelect[j]]];
//                            machinetimePre[firstStageMachineSelect[j]] = machinetime[i][s][firstStageMachineSelect[j]];
//                        }
//                    }
//
//                    int[] flg2 = new int[count[i]];           //生成暂时数组，便于将 jobtemp 和 jobtimeTemp 中的工件重新排列；
//                    for (int k = 0; k < count[i]; k++) {
//                        flg2[k] = jobtemp[k];
//                    }
//
//                    for (int e = 0; e < count[i]; e++) {
//                        for (int w = 0; w < count[i] - 1 - e; w++)      // 由于 jobtimeTemp 存储工件上一道工序的完工时间，在进行下一道工序生产时，按照先完工先生产的原则，
//                        {                                            //因此，该循环的目的在于将 jobtimeTemp 中按照加工时间从小到大排列，同时 jobtemp 相应进行变换，来记录 jobtimeTemp 中的工件号；
//                            if (jobtimeTemp[w][s] > jobtimeTemp[w + 1][s]) {
//                                double flg5 = jobtimeTemp[w][s];
//                                int flg6 = flg2[w];
//                                jobtimeTemp[w] = jobtimeTemp[w + 1];
//                                flg2[w] = flg2[w + 1];
//                                jobtimeTemp[w + 1][s] = flg5;
//                                flg2[w + 1] = flg6;
//                            }
//                        }
//                    }                                      //对上一阶段的工件完工时间进行排序
//
//                    for (int j = 0; j < count[i]; j++)    //更新 jobtemp，jobtimeTemp 的数据，开始下一道工序；
//                    {
//                        jobtemp[j] = flg2[j];
//                        pretimetemp[j] = jobtimeTemp[j][s];
//
//                        time[i][s][jobtemp[j]] = jobtimeTemp[j][s];
//                    }
//                    continue;
//
//                }

//                for (int j = 0; j < numberOfMachines_[i][s]; j++) {
//                    System.out.print(machineWorker[i][s][j]+ " ");
//                    workerSequence.add(machineWorker[i][s][j]);
//
//                }
////                System.out.println();
//                System.out.println(workerSequence);

//                得到第一个阶段第一个机器上的第一个job的加工时间
                if(s==0) {
//                    machineWorker[i][s][n]  第i个工厂上第s阶段的第n个机器。
//                    time = new double[numberOfFactories][numberOfStages][numberOfJobs_];  //存储当前粒子的时间完成表  第几个工厂的第几个阶段的第几个工件的时间
//                    System.out.println(i+" "+s+" "+jobtemp[0]);

//                    System.out.println("jobtemp[0]: " + jobtemp[0]);
//                    sleep();



                    //i是工厂，s是阶段

                    try {
                        // 尝试执行可能抛出 ArrayIndexOutOfBoundsException 的代码
//                        time[i][s][jobtemp[0]] = timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0] / lw[i][machineWorker[i][s][0]];
                        time[i][s][jobtemp[0]] = (timeMatrix_[jobtemp[0]][s] + timeMatrix_[jobtemp[0]][s] * 0.1) / machineSpeed[i][s][0] / lw[i][worker[jobtemp[0]]];
//                        System.out.println(timeMatrix_[jobtemp[0]][s]);
//                        System.out.println(machineSpeed[i][s][0]);
//                        System.out.println(lw[i][worker[jobtemp[0]]]);
//                        System.out.println(time[i][s][jobtemp[0]]);
                    } catch (ArrayIndexOutOfBoundsException e) {

                        // 捕获异常并处理
                        System.out.println("Caught ArrayIndexOutOfBoundsException: " + e.getMessage());
                        System.out.println("jobtemp"+jobtemp.length);
                        System.out.println("i: " + i);
                        System.out.println("s: " + s);
                        System.out.println("time dimensions: " + time.length + ", " + time[0].length + ", " + time[0][0].length);
                        System.out.println("timeMatrix_ dimensions: " + timeMatrix_.length + ", " + timeMatrix_[0].length);
                        System.out.println("machineSpeed dimensions: " + machineSpeed.length + ", " + machineSpeed[0].length + ", " + machineSpeed[0][0].length);
                        System.out.println("lw dimensions: " + lw.length + ", " + lw[0].length);
                        System.out.println("machineWorker dimensions: " + machineWorker.length + ", " + machineWorker[0].length + ", " + machineWorker[0][0].length);
                        System.out.println("Time factories allocation:");

                        for (int i1 : count) {
                            System.out.print(i1+" ");
                        }
                        System.out.println();
                        System.out.println("jobtemp[0]: " + jobtemp[0]);

                        continue;

                        // 可以在这里记录错误日志、重置某些状态或采取其他补救措施
                        // 例如，记录错误日志
                        // Logger.getLogger(Example.class.getName()).log(Level.SEVERE, null, e);
                    }
//                    time[i][s][jobtemp[0]] = timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0]/ lw[i][machineWorker[i][s][0]];

//                    System.out.println("i是"+i);
//                    System.out.println("s是"+s);
//                    System.out.println("jobtemp是"+jobtemp[0]);
//                    System.out.println(time[i][s][jobtemp[0]]);
//
//                    System.out.println(timeMatrix_[jobtemp[0]][s]);
//                    System.out.println(machineSpeed[i][s][0]);
//                    System.out.println(lw[i][machineWorker[i][s][0]]);

//                    sleep();
//                    System.out.println("time[i][s][jobtemp[0]]"+time[i][s][jobtemp[0]]);
//                    System.out.println("timeMatrix_[jobtemp[0]][s]"+timeMatrix_[jobtemp[0]][s]);


                    jobtimeTemp[0][s]=time[i][s][jobtemp[0]];                    // 第一个工件的完成时间
//                    System.out.println(jobtimeTemp[0][s]);
//                    sleep();

                    jobEndPower[i][s][jobtemp[0]] = (timeMatrix_[jobtemp[0]][s] + timeMatrix_[jobtemp[0]][s] * 0.1) / machineSpeed[i][s][0]/ lw[i][worker[jobtemp[0]]] * machinePower[i][s][0];

                    jobCost[i][s][jobtemp[0]] = (timeMatrix_[jobtemp[0]][s] + timeMatrix_[jobtemp[0]][s] * 0.1) / machineSpeed[i][s][0]/ lw[i][worker[jobtemp[0]]] *cw[i][worker[jobtemp[0]]];
//                    System.out.println("lw"+lw[i][machineWorker[i][s][0]]);
//                    System.out.println("cw"+cw[i][machineWorker[i][s][0]]);
//                    System.out.println("machineWorker="+machineWorker[i][s][0]);
//                    System.out.println("cw="+cw[i][machineWorker[i][s][0]]);
                }
                else{      //得到除第一阶段的其他阶段的第一个机器上的第一个job的加工时间
                    time[i][s][jobtemp[0]] = time[i][s-1][jobtemp[0]]+ (timeMatrix_[jobtemp[0]][s] + timeMatrix_[jobtemp[0]][s] * 0.1) / machineSpeed[i][s][0]/ lw[i][worker[jobtemp[0]]];
                    jobtimeTemp[0][s]=time[i][s][jobtemp[0]];
                    jobEndPower[i][s][jobtemp[0]] = (timeMatrix_[jobtemp[0]][s] + timeMatrix_[jobtemp[0]][s] * 0.1) / machineSpeed[i][s][0]/ lw[i][worker[jobtemp[0]]] * machinePower[i][s][0];

                    jobCost[i][s][jobtemp[0]] = (timeMatrix_[jobtemp[0]][s] + timeMatrix_[jobtemp[0]][s] * 0.1) / machineSpeed[i][s][0]/ lw[i][worker[jobtemp[0]]] * cw[i][worker[jobtemp[0]]];
                }




                if (numberOfMachines_[i][s] == 1) {                // 如果第i个工厂的第s阶段的机器数量是1
                    for (int j = 1; j < count[i]; j++) {
                        //jobIndex=jobtemp[j];     Math.max(machinetime[i][s][n],pretimetemp[k])
                        if (s == 0) {
                            time[i][s][jobtemp[j]] = time[i][s][jobtemp[j - 1]] + (timeMatrix_[jobtemp[j]][0] + timeMatrix_[jobtemp[j]][0] * 0.1) / machineSpeed[i][s][0] / lw[i][worker[jobtemp[j]]];
                            jobtimeTemp[j][s] = time[i][s][jobtemp[j]];
                            jobEndPower[i][s][jobtemp[j]] = (timeMatrix_[jobtemp[j]][s] + timeMatrix_[jobtemp[j]][s] * 0.1) / machineSpeed[i][s][0] / lw[i][worker[jobtemp[j]]] * machinePower[i][s][0];

                            jobCost[i][s][jobtemp[j]] = (timeMatrix_[jobtemp[j]][s] + timeMatrix_[jobtemp[j]][s] * 0.1) / machineSpeed[i][s][0] / lw[i][worker[jobtemp[j]]] * cw[i][worker[jobtemp[j]]];
                        } else {
                            time[i][s][jobtemp[j]] = Math.max(time[i][s][jobtemp[j - 1]], time[i][s - 1][jobtemp[j]]) + (timeMatrix_[jobtemp[j]][s] + timeMatrix_[jobtemp[j]][s] * 0.1) / machineSpeed[i][s][0] / lw[i][worker[jobtemp[j]]];
                            jobtimeTemp[j][s] = time[i][s][jobtemp[j]];
                            jobEndPower[i][s][jobtemp[j]] = (timeMatrix_[jobtemp[j]][s] + timeMatrix_[jobtemp[j]][s] * 0.1) / machineSpeed[i][s][0] / lw[i][worker[jobtemp[j]]] * machinePower[i][s][0] + (time[i][s][jobtemp[j]] - time[i][s][jobtemp[j - 1]] - timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0] / lw[i][worker[jobtemp[j]]]);

                            jobCost[i][s][jobtemp[j]] = (timeMatrix_[jobtemp[j]][s] + timeMatrix_[jobtemp[j]][s] * 0.1) / machineSpeed[i][s][0] / lw[i][worker[jobtemp[j]]] * cw[i][worker[jobtemp[j]]] + (time[i][s][jobtemp[j]] - time[i][s][jobtemp[j - 1]] - timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0] / lw[i][worker[jobtemp[j]]]) * cw[i][worker[jobtemp[j]]];
                        }
                    }
                } else {
                    for (int k = 1; k < count[i]; k++) {
                        int[] machineOfJobnumber = new int[numberOfMachines_[i][s]];
                        machinetime[i][s][0] = time[i][s][jobtemp[0]];   // 第几工厂第几阶段的第一个机器处理完第一个工件的结束时间
                        machineOfJobnumber[0] += 1;
                        machinetimePre[0] = machinetime[i][s][0];
                        double min = machinetime[i][s][0];        //先记录第s阶段的第一台并行机器的当前工作时间；
                        int n = 0;
                        for (int p = 0; p < numberOfMachines_[i][s]; p++) //与其他并行机器进行比较，找出时间最小的机器；
                        {
                            if (min > machinetime[i][s][p]) {
                                min = machinetime[i][s][p];
                                n = p;      //机器号
                                machineOfJobnumber[n] += 1;
                            }
                        }
                        int q = jobtemp[k];                //按顺序提取工厂i第一阶段中的工件号，对工件进行加工；
                        if (s == 0) {
                            starttime[q][s][n] = Math.max(machinetime[i][s][n], pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                            machinetime[i][s][n] = starttime[q][s][n] + (timeMatrix_[q][s] + timeMatrix_[q][s] * 0.1) / machineSpeed[i][s][n] / lw[i][worker[jobtemp[k]]]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                            finishtime[q][s][n] = machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                            jobtimeTemp[k][s] = finishtime[q][s][n];

                            //下面这行原来没有
//                            time[i][s][q] = jobtimeTemp[k][s];
                            jobEndPower[i][s][q] = (timeMatrix_[q][s] + timeMatrix_[q][s] * 0.1) / machineSpeed[i][s][n] / lw[i][worker[jobtemp[k]]] * machinePower[i][s][n];

                            jobCost[i][s][q] = (timeMatrix_[q][s] + timeMatrix_[q][s] * 0.1) / machineSpeed[i][s][n] / lw[i][worker[jobtemp[k]]] * cw[i][worker[jobtemp[k]]];
                            machinetimePre[n] = machinetime[i][s][n];
                        } else {
                            //pretimetemp[k]= time[i][s-1][q];//新加的
                            if (machineOfJobnumber[n] == 1) {
                                starttime[q][s][n] = Math.max(machinetime[i][s][n], pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                                machinetime[i][s][n] = starttime[q][s][n] + (timeMatrix_[q][s] + timeMatrix_[q][s] * 0.1) / machineSpeed[i][s][n] / lw[i][worker[jobtemp[k]]]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                                finishtime[q][s][n] = machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                                jobtimeTemp[k][s] = finishtime[q][s][n];

                                //下面这行原来没有
//                                time[i][s][q] = jobtimeTemp[k][s];
                                jobEndPower[i][s][jobtemp[k]] = (timeMatrix_[jobtemp[k]][s] + timeMatrix_[jobtemp[k]][s] * 0.1) / machineSpeed[i][s][n] / lw[i][worker[jobtemp[k]]] * machinePower[i][s][n];

                                jobCost[i][s][jobtemp[k]] = (timeMatrix_[jobtemp[k]][s] + timeMatrix_[jobtemp[k]][s] * 0.1) / machineSpeed[i][s][n] / lw[i][worker[jobtemp[k]]] * cw[i][worker[jobtemp[k]]];
                                machinetimePre[n] = machinetime[i][s][n];
                            } else {
                                starttime[q][s][n] = Math.max(machinetime[i][s][n], pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                                machinetime[i][s][n] = starttime[q][s][n] + (timeMatrix_[jobtemp[q]][s] + timeMatrix_[jobtemp[q]][s] * 0.1) / machineSpeed[i][s][n] / lw[i][worker[jobtemp[k]]]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                                finishtime[q][s][n] = machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                                jobtimeTemp[k][s] = finishtime[q][s][n];

                                //下面这行原来没有
//                                time[i][s][q] = jobtimeTemp[k][s];
                                jobEndPower[i][s][jobtemp[k]] = (timeMatrix_[jobtemp[k]][s] + timeMatrix_[jobtemp[k]][s] * 0.1) / machineSpeed[i][s][n] / lw[i][worker[jobtemp[k]]] * machinePower[i][s][n] + (starttime[q][s][n] - machinetimePre[n]);

                                jobCost[i][s][jobtemp[k]] = (timeMatrix_[jobtemp[k]][s] + timeMatrix_[jobtemp[k]][s] * 0.1) / machineSpeed[i][s][n] / lw[i][worker[jobtemp[k]]] * cw[i][worker[jobtemp[k]]] + (starttime[q][s][n] - machinetimePre[n]) * cw[i][worker[jobtemp[k]]];
                                machinetimePre[n] = machinetime[i][s][n];
                            }
                        }
                    }
                }


                int[] flg2 = new int[count[i]];           //生成暂时数组，便于将 jobtemp 和 jobtimeTemp 中的工件重新排列；
                for (int k = 0; k < count[i]; k++) {
                    flg2[k] = jobtemp[k];
                }

                for (int e = 0; e < count[i]; e++) {
                    for (int w = 0; w < count[i] - 1 - e; w++)      // 由于 jobtimeTemp 存储工件上一道工序的完工时间，在进行下一道工序生产时，按照先完工先生产的原则，
                    {                                            //因此，该循环的目的在于将 jobtimeTemp 中按照加工时间从小到大排列，同时 jobtemp 相应进行变换，来记录 jobtimeTemp 中的工件号；
                        if (jobtimeTemp[w][s] > jobtimeTemp[w + 1][s]) {
                            double flg5 = jobtimeTemp[w][s];
                            int flg6 = flg2[w];
                            jobtimeTemp[w] = jobtimeTemp[w + 1];
                            flg2[w] = flg2[w + 1];
                            jobtimeTemp[w + 1][s] = flg5;
                            flg2[w + 1] = flg6;
                        }
                    }
                }                                      //对上一阶段的工件完工时间进行排序

                for (int j = 0; j < count[i]; j++)    //更新 jobtemp，jobtimeTemp 的数据，开始下一道工序；
                {
                    jobtemp[j] = flg2[j];
                    pretimetemp[j] = jobtimeTemp[j][s];

                    time[i][s][jobtemp[j]] = jobtimeTemp[j][s];
                }
//                for (double[][] doubles : machinetime) {
//                    for (double[] aDouble : doubles) {
//                        for (double v : aDouble) {
//                            System.out.print(v+" ");
//                        }
//                        System.out.println();
//                    }
//                    System.out.println();
//                }

            }

        }


//        sleep();


////        假设 numberOfFactories, numberOfStages, numberOfJobs_ 已经被定义并正确初始化
//        for (int f = 0; f < numberOfFactories; f++) {
//            System.out.println("Factory " + (f + 1) + " Job Cost Matrix:");
//            for (int s1 = 0; s1 < numberOfStages; s1++) {
//                System.out.print("Stage " + (s1 + 1) + ": ");
//                for (int j = 0; j < numberOfJobs_; j++) {
//                    // 注意：在实际代码中，确保 jobCost[f][s][j] 已经被赋值
//                    System.out.printf("%.2f ", jobCost[f][s1][j]);
//                }
//                System.out.println();
//            }
//            System.out.println(); // 空行，用于分隔不同工厂的输出
//        }
//
//        // 假设 numberOfFactories, numberOfStages, numberOfJobs_ 已经被定义并正确初始化
//        for (int f = 0; f < numberOfFactories; f++) {
//            System.out.println("Factory " + (f + 1) + " Job Time Matrix:");
//            for (int s2 = 0; s2 < numberOfStages; s2++) {
//                System.out.print("Stage " + (s2 + 1) + ": ");
//                for (int j = 0; j < numberOfJobs_; j++) {
//                    // 注意：在实际代码中，确保 jobCost[f][s][j] 已经被赋值
//                    System.out.printf("%.2f ", time[f][s2][j]);
//                }
//                System.out.println();
//            }
//            System.out.println(); // 空行，用于分隔不同工厂的输出
//        }
//        // 假设 numberOfFactories, numberOfStages, numberOfJobs_ 已经被定义并正确初始化
//        for (int f = 0; f < numberOfFactories; f++) {
//            System.out.println("Factory " + (f + 1) + " Job Power Matrix:");
//            for (int s3 = 0; s3 < numberOfStages; s3++) {
//                System.out.print("Stage " + (s3 + 1) + ": ");
//                for (int j = 0; j < numberOfJobs_; j++) {
//                    // 注意：在实际代码中，确保 jobCost[f][s][j] 已经被赋值
//                    System.out.printf("%.2f ", jobEndPower[f][s3][j]);
//                }
//                System.out.println();
//            }
//            System.out.println(); // 空行，用于分隔不同工厂的输出
//        }
//        sleep();
        return time;
    }//calculate


    private static void sleep() {
        try {
            Thread.sleep(99999);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
    }

    private void extracted(int[][] solution) {
        //        for (double[] doubles : lw) {
//            for (double aDouble : doubles) {
//                System.out.print(aDouble+" ");
//            }
//            System.out.println();
//        }
//        System.out.println();
//
//        for (int[] ints : cw) {
//            for (int anInt : ints) {
//                System.out.print(anInt+" ");
//            }
//            System.out.println();
//        }
//        System.out.println();
//
//        for (int[][] ints : machineWorker) {
//            for (int[] anInt : ints) {
//                for (int i : anInt) {
//                    System.out.print(i+" ");
//                }
//                System.out.println();
//            }
//            System.out.println();
//        }

//        //每次工人随机选择工厂
//        for (int i = 0; i < lw.length; i++) {
//            shuffleRowExcludingZeros(lw,cw,i);
//
//        }


//        for (double[] doubles : lw) {
//            for (double aDouble : doubles) {
//                System.out.print(aDouble+" ");
//            }
//            System.out.println();
//        }
//        System.out.println();
//
//        for (int[] ints : cw) {
//            for (int anInt : ints) {
//                System.out.print(anInt+" ");
//            }
//            System.out.println();
//        }
//        System.out.println();
//
//        for (int i1 : nw) {
//            System.out.print(i1+" ");
//        }
//            System.out.println();
//
//        try {
//            Thread.sleep(99999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
//
//        for (double[][] doubles : machineSpeed) {
//            for (double[] aDouble : doubles) {
//                for (double v : aDouble) {
//                    System.out.print(v+" ");
//                }
//                System.out.println();
//            }
//            System.out.println(">");
//        }


//        System.out.println(">");
        int total = 0;
        for (int i : nw) {
            total = total + i;
        }
//        System.out.println(total);
//        sleep();
        int[] workerSequenceTemp = new int[total];
        for (int i = 2; i < 3; i++) {
            for (int i1 = 0; i1 < total; i1++) {
//                System.out.print(solution[i][i1]+" ");
                workerSequenceTemp[i1] = solution[i][i1];
            }
        }
//        System.out.println();
//        System.out.println(Arrays.toString(workerSequenceTemp));
//        sleep();
//                try {
//            Thread.sleep(99999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }

        List<List<Integer>> lists = segmentArray(workerSequenceTemp, nw);
//        List<List<Integer>> transformedLists = transformLists(lists);
//        System.out.println(lists);
//        sleep();
//        System.out.println("transformedLists"+transformedLists);
//        int[] tempp = new int[total];
//        int index = 0;
//        for (List<Integer> transformedList : transformedLists) {
//            for (Integer i : transformedList) {
//                tempp[index++] = i;
//            }
//        }
//        for (int i : tempp) {
//            System.out.print(i+" ");
//        }
//        System.out.println();
//        for (int i = 2; i < solution.length; i++) {
//            for (int i1 = 0; i1 < total; i1++) {
//                solution[i][i1] = tempp[i1];
//            }
//        }

//        for (int i = 2; i < solution.length; i++) {
//            for (int i1 = 0; i1 < solution[2].length; i1++) {
//                System.out.print(solution[2][i1]+" ");
//            }
//        }
//        System.out.println();
//        System.out.println(lists);
//        try {
//            Thread.sleep(99999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }
        machineWorker = new int[numberOfFactories][numberOfStages][5];  //第几个工厂第几个阶段的第几个机器
        for (int i = 0; i < numberOfFactories; i++) {
            for (int j = 0; j < numberOfStages; j++) {
                for (int h = 0; h < 5; h++) {
                    machineWorker[i][j][h] = -1;
                }
            }
        }
//        for (int[] ints : numberOfMachines_) {
//            for (int anInt : ints) {
//                System.out.print(anInt+" ");
//            }
//            System.out.println();
//        }
//        System.out.println();
//sleep();

        int a, b, c;
        double speedmin;
        for (int i = 0; i < numberOfFactories; i++) {//工厂数
            int temp = 0;
            for (int i1 = 0; i1 < numberOfStages; i1++) {//阶段数
                for (int j = 0; j < numberOfMachines_[i][i1]; j++) { //工厂i的第i1阶段的机器数
//                    machineWorker[i][i1][j] = transformedLists.get(i).get(temp);//第几个工厂第几个阶段的第几个机器
                    machineWorker[i][i1][j] = lists.get(i).get(temp);//第几个工厂第几个阶段的第几个机器
//                    System.out.println(temp);
                    temp++;
                }
            }

        }

//        for (int[][] ints : machineWorker) {
//            for (int[] anInt : ints) {
//                for (int i : anInt) {
//                    System.out.print(i+" ");
//                }
//                System.out.println();
//            }
//            System.out.println();
//        }
//
//sleep();

    }


    public static int[][] createPartitionedArray(int[] originalArray, int num) {
        // 计算二维数组的行数
        int numRows = (int) Math.ceil((double) originalArray.length / num);

        // 创建二维数组
        int[][] tempSequence = new int[numRows][];

        // 填充二维数组
        for (int i = 0; i < numRows; i++) {
            int start = i * num;
            int end = Math.min(start + num, originalArray.length);
            int length = end - start;
            tempSequence[i] = new int[length];
            System.arraycopy(originalArray, start, tempSequence[i], 0, length);
        }

        return tempSequence;
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

    public static List<List<Integer>> transformLists(List<List<Integer>> lists) {
        List<List<Integer>> transformedLists = new ArrayList<>();

        for (List<Integer> list : lists) {
            // 对子列表进行变换
            List<Integer> transformedList = transformList(list);
            // 将变换后的子列表添加到结果列表中
            transformedLists.add(transformedList);
        }

        return transformedLists;
    }

    public static List<Integer> transformList(List<Integer> list) {
        // 创建一个映射，存储每个数字的原始索引
        Map<Integer, Integer> originalIndices = new HashMap<>();
        for (int i = 0; i < list.size(); i++) {
            originalIndices.put(list.get(i), i);
        }

        // 对子列表进行排序
        List<Integer> sortedList = new ArrayList<>(list);
        Collections.sort(sortedList);

        // 创建变换后的列表
        List<Integer> transformedList = new ArrayList<>(Collections.nCopies(list.size(), 0));
        for (int i = 0; i < sortedList.size(); i++) {
            int originalIndex = originalIndices.get(sortedList.get(i));
            transformedList.set(originalIndex, i);
        }

        return transformedList;
    }


    public static OptionalInt findIndex(int[] arr, int target) {
        return IntStream.range(0, arr.length)
                .filter(i -> arr[i] == target)
                .findFirst();
    }

    private static void shuffleRowExcludingZeros(double[][] a1, int[][] a2, int rowIndex) {
        List<Integer> indices = new ArrayList<>();
        for (int j = 0; j < a1[rowIndex].length; j++) {
            if (a1[rowIndex][j] != 0) {
                indices.add(j);
            }
        }

        // 打乱非0元素的索引
        org.uma.jmetal.util.research.runtime.SeededRandom.shuffle(indices);

        // 使用一个临时数组来存储打乱后的值（或者你可以直接在原数组上进行交换，但这样更清晰）
        double[] tempA1Row = a1[rowIndex].clone();
        int[] tempA2Row = a2[rowIndex].clone();

        // 将打乱后的值放回到原数组中（跳过0值元素的位置）
        int k = 0; // 用于跟踪indices中的索引
        for (int j = 0; j < a1[rowIndex].length; j++) {
            if (a1[rowIndex][j] != 0) {
                a1[rowIndex][j] = tempA1Row[indices.get(k)];
                a2[rowIndex][j] = tempA2Row[indices.get(k)];
                k++;
            }
        }
    }

    public static int findElementIndex(int[] array, int target) {
        for (int i = 0; i < array.length; i++) {
            if (array[i] == target) {
                return i;  // 返回找到的索引
            }
        }
        return -1;  // 如果没有找到，返回-1
    }

    protected void calculate1(int[][] solution) throws ArrayIndexOutOfBoundsException {

        for (int i = 0; i < solution[0].length; i++) {
            //System.out.print("\t="+solution[0][i]);
        }
        //System.out.println();
        for (int i = 0; i < solution[1].length; i++) {
            //System.out.print("\t="+solution[1][i]);
        }
        //System.out.println();

//        double[][][] jobEndPower = new double[numberOfFactories][numberOfStages][numberOfJobs_];
//        double[][][] time = new double[numberOfFactories][numberOfStages][numberOfJobs_];  //存储当前粒子的时间完成表

        jobEndPower = new double[numberOfFactories][numberOfStages][numberOfJobs_];
        time = new double[numberOfFactories][numberOfStages][numberOfJobs_];

        int[][] timefactories = new int[numberOfFactories][numberOfJobs_];  //三个一维向量  一维向量的空间大小是所有工件的数量大小

        for (int i = 0; i < timefactories.length; i++) {                                //获取行的长度
            for (int j = 0; j < timefactories[i].length; j++) {
                timefactories[i][j] = -1;                                             //三个一维空间的里的数都先存放-1
            }
        }

        int[] count = new int[numberOfFactories];          //记录每个工厂的job数

        //完成了把job分配给工厂的功能，并且记录了每个工厂的job数
        for (int i = 0; i < solution[1].length; i++) {
            // System.out.println(count.length);
            /*System.out.println(numberOfFactories);
            System.out.println(numberOfMachines_);
            System.out.println(numberOfJobs_);*/
            //  tem[1][i] 是工厂向量里面的值
            count[solution[1][i]] = count[solution[1][i]] + 1;  //记录工厂（tem[1][i]）里面的jobs数，每次加1    //也就是说 计算几个1 几个2 几个3

            //把job分给对应工厂
            for (int j = 0; j < solution[0].length; j++) {
                int factoryIndex = solution[1][i];
                if (timefactories[factoryIndex][j] == -1) {
                    timefactories[factoryIndex][j] = solution[0][i];
                    break;   //很重要
                }
            }
        }
        //计算公式部分
        //System.out.println("遍历每个工厂的Job：");

        int endflag[][] = new int[numberOfFactories][1];

        //加工人
        int[][][] seqofw = new int[numberOfFactories][numberOfStages][numberOfJobs_];

        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        for (int i = 0; i < numberOfFactories; i++) {
            for (int j = 0; j < numberOfStages; j++) {
                for (int h = 0; h < count[i]; h++) {
                    seqofw[i][j][h] = random.nextInt(nw[i]);
                }
            }
        }

        int[] jobFactory = new int[numberOfJobs_];
        for (int i = 0; i < numberOfFactories; i++) {
            for (int j = 0; j < count[i]; j++) {
                jobFactory[timefactories[i][j]] = i;
            }
        }
        for (int i : jobFactory) {
            System.out.print(i + " ");
        }
//        sleep();

        for (int i = 0; i < numberOfFactories; i++) {
            //System.out.println("工厂："+i);

            double[][][] starttime = new double[numberOfJobs_][][];//第几个工件第几道工序在第几台并行机上开始加工的时间；
            double[][][] finishtime = new double[numberOfJobs_][][];//第几个工件第几道工序在第几台并行机上完成加工的时间；

            //int[][] machinetime ;
            int[] jobtemp = new int[count[i]];         //每个工厂的job都有哪些
            for (int x = 0; x < count[i]; x++) {
                jobtemp[x] = timefactories[i][x];       //每个工厂的job(号)排列
            }
            //System.out.println(jobtemp);
            double[][] jobtimeTemp = new double[count[i]][numberOfStages];        //作业j的第s阶段的完成时间
            double[] pretimetemp = new double[count[i]];     // count[i]——记录每个工厂的job数

            for (int s = 0; s < numberOfStages; s++) {
                double[] machinetimePre = new double[numberOfMachines_[i][s]];
                double machinetime[][][] = new double[numberOfFactories][numberOfStages][numberOfMachines_[i][s]];

                starttime = new double[numberOfJobs_][numberOfStages][numberOfMachines_[i][s]];
                finishtime = new double[numberOfJobs_][numberOfStages][numberOfMachines_[i][s]];

                // if(numberOfMachines_[s]==1){
                // int jobIndex = timefactories[i][0];

                //得到第一个阶段第一个机器上的第一个job的加工时间
                if (s == 0) {
                    time[i][s][jobtemp[0]] = timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0];
                    jobtimeTemp[0][s] = time[i][s][jobtemp[0]];                    // 第一个工件的完成时间
                    jobEndPower[i][s][jobtemp[0]] = timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0] * machinePower[i][s][0];
                } else {      //得到除第一阶段的其他阶段的第一个机器上的第一个job的加工时间
                    time[i][s][jobtemp[0]] = time[i][s - 1][jobtemp[0]] + timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0];
                    jobtimeTemp[0][s] = time[i][s][jobtemp[0]];
                    jobEndPower[i][s][jobtemp[0]] = timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0] * machinePower[i][s][0];
                }


                if (numberOfMachines_[i][s] == 1) {                // 如果第i个工厂的第s阶段的机器数量是1
                    for (int j = 1; j < count[i]; j++) {
                        //jobIndex=jobtemp[j];     Math.max(machinetime[i][s][n],pretimetemp[k])
                        if (s == 0) {
                            time[i][s][jobtemp[j]] = time[i][s][jobtemp[j - 1]] + timeMatrix_[jobtemp[j]][0] / machineSpeed[i][s][0];
                            jobtimeTemp[j][s] = time[i][s][jobtemp[j]];
                            jobEndPower[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0] * machinePower[i][s][0];
                        } else {
                            time[i][s][jobtemp[j]] = Math.max(time[i][s][jobtemp[j - 1]], time[i][s - 1][jobtemp[j]]) + timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0];
                            jobtimeTemp[j][s] = time[i][s][jobtemp[j]];
                            jobEndPower[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0] * machinePower[i][s][0] + (time[i][s][jobtemp[j]] - time[i][s][jobtemp[j - 1]] - timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0]);
                        }
                    }
                } else {
                    for (int k = 1; k < count[i]; k++) {
                        int[] machineOfJobnumber = new int[numberOfMachines_[i][s]];
                        machinetime[i][s][0] = time[i][s][jobtemp[0]];   // 第几工厂第几阶段的第一个机器处理完第一个工件的结束时间
                        machineOfJobnumber[0] += 1;
                        machinetimePre[0] = machinetime[i][s][0];
                        double min = machinetime[i][s][0];        //先记录第s阶段的第一台并行机器的当前工作时间；
                        int n = 0;
                        for (int p = 0; p < numberOfMachines_[i][s]; p++) //与其他并行机器进行比较，找出时间最小的机器；
                        {
                            if (min > machinetime[i][s][p]) {
                                min = machinetime[i][s][p];
                                n = p;      //机器号
                                machineOfJobnumber[n] += 1;
                            }
                        }
                        int q = jobtemp[k];                //按顺序提取工厂i第一阶段中的工件号，对工件进行加工；
                        if (s == 0) {
                            starttime[q][s][n] = Math.max(machinetime[i][s][n], pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                            machinetime[i][s][n] = starttime[q][s][n] + timeMatrix_[q][s] / machineSpeed[i][s][n]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                            finishtime[q][s][n] = machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                            jobtimeTemp[k][s] = finishtime[q][s][n];
                            time[i][s][q] = jobtimeTemp[k][s];
                            jobEndPower[i][s][q] = timeMatrix_[q][s] / machineSpeed[i][s][n] * machinePower[i][s][n];
                            machinetimePre[n] = machinetime[i][s][n];
                        } else {
                            //pretimetemp[k]= time[i][s-1][q];//新加的
                            if (machineOfJobnumber[n] == 1) {
                                starttime[q][s][n] = Math.max(machinetime[i][s][n], pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                                machinetime[i][s][n] = starttime[q][s][n] + timeMatrix_[q][s] / machineSpeed[i][s][n]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                                finishtime[q][s][n] = machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                                jobtimeTemp[k][s] = finishtime[q][s][n];
                                time[i][s][q] = jobtimeTemp[k][s];
                                jobEndPower[i][s][jobtemp[k]] = timeMatrix_[jobtemp[k]][s] / machineSpeed[i][s][n] * machinePower[i][s][n];
                                machinetimePre[n] = machinetime[i][s][n];
                            } else {
                                starttime[q][s][n] = Math.max(machinetime[i][s][n], pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                                machinetime[i][s][n] = starttime[q][s][n] + timeMatrix_[q][s] / machineSpeed[i][s][n]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                                finishtime[q][s][n] = machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                                jobtimeTemp[k][s] = finishtime[q][s][n];
                                time[i][s][q] = jobtimeTemp[k][s];
                                jobEndPower[i][s][jobtemp[k]] = timeMatrix_[jobtemp[k]][s] / machineSpeed[i][s][n] * machinePower[i][s][n] + (starttime[q][s][n] - machinetimePre[n]);
                                machinetimePre[n] = machinetime[i][s][n];
                            }
                        }
                    }
                }

                int[] flg2 = new int[count[i]];           //生成暂时数组，便于将 jobtemp 和 jobtimeTemp 中的工件重新排列；
                for (int k = 0; k < count[i]; k++) {
                    flg2[k] = jobtemp[k];
                }

                for (int e = 0; e < count[i]; e++) {
                    for (int w = 0; w < count[i] - 1 - e; w++)      // 由于 jobtimeTemp 存储工件上一道工序的完工时间，在进行下一道工序生产时，按照先完工先生产的原则，
                    {                                            //因此，该循环的目的在于将 jobtimeTemp 中按照加工时间从小到大排列，同时 jobtemp 相应进行变换，来记录 jobtimeTemp 中的工件号；
                        if (jobtimeTemp[w][s] > jobtimeTemp[w + 1][s]) {
                            double flg5 = jobtimeTemp[w][s];
                            int flg6 = flg2[w];
                            jobtimeTemp[w] = jobtimeTemp[w + 1];
                            flg2[w] = flg2[w + 1];
                            jobtimeTemp[w + 1][s] = flg5;
                            flg2[w + 1] = flg6;
                        }
                    }
                }                                      //对上一阶段的工件完工时间进行排序

                for (int j = 0; j < count[i]; j++)    //更新 jobtemp，jobtimeTemp 的数据，开始下一道工序；
                {
                    jobtemp[j] = flg2[j];
                    pretimetemp[j] = jobtimeTemp[j][s];
                    //time[i][s][jobtemp[j]] = jobtimeTemp[j][s];
                }
            }
        }


//        for (int j=0;j<numberOfStages;j++){
//            for (int i=0;i<numberOfFactories;i++){
//                for (int h=0;h<count[i];h++){
//                    System.out.print(seqofw[i][j][h]+" ");
//                }
//                System.out.print("  ");
//            }
//            System.out.println();
//        }
//        System.out.println();


//        return time;
    }//calculate

    protected void calculate2(int[][] solution) throws ArrayIndexOutOfBoundsException {

        for (int i = 0; i < solution[0].length; i++) {
            //System.out.print("\t="+solution[0][i]);
        }
        //System.out.println();
        for (int i = 0; i < solution[1].length; i++) {
            //System.out.print("\t="+solution[1][i]);
        }
        //System.out.println();

//        double[][][] jobEndPower = new double[numberOfFactories][numberOfStages][numberOfJobs_];
//        double[][][] time = new double[numberOfFactories][numberOfStages][numberOfJobs_];  //存储当前粒子的时间完成表

        jobEndPower = new double[numberOfFactories][numberOfStages][numberOfJobs_];
        time = new double[numberOfFactories][numberOfStages][numberOfJobs_];

        int[][] timefactories = new int[numberOfFactories][numberOfJobs_];  //三个一维向量  一维向量的空间大小是所有工件的数量大小

        for (int i = 0; i < timefactories.length; i++) {                                //获取行的长度
            for (int j = 0; j < timefactories[i].length; j++) {
                timefactories[i][j] = -1;                                             //三个一维空间的里的数都先存放-1
            }
        }

        int[] count = new int[numberOfFactories];          //记录每个工厂的job数

        //完成了把job分配给工厂的功能，并且记录了每个工厂的job数
        for (int i = 0; i < solution[1].length; i++) {
            // System.out.println(count.length);
            /*System.out.println(numberOfFactories);
            System.out.println(numberOfMachines_);
            System.out.println(numberOfJobs_);*/
            //  tem[1][i] 是工厂向量里面的值
            count[solution[1][i]] = count[solution[1][i]] + 1;  //记录工厂（tem[1][i]）里面的jobs数，每次加1    //也就是说 计算几个1 几个2 几个3

            //把job分给对应工厂
            for (int j = 0; j < solution[0].length; j++) {
                int factoryIndex = solution[1][i];
                if (timefactories[factoryIndex][j] == -1) {
                    timefactories[factoryIndex][j] = solution[0][i];
                    break;   //很重要
                }
            }
        }
        //计算公式部分
        //System.out.println("遍历每个工厂的Job：");

        int endflag[][] = new int[numberOfFactories][1];

        for (int i = 0; i < numberOfFactories; i++) {
            //System.out.println("工厂："+i);

            double[][][] starttime = new double[numberOfJobs_][][];//第几个工件第几道工序在第几台并行机上开始加工的时间；
            double[][][] finishtime = new double[numberOfJobs_][][];//第几个工件第几道工序在第几台并行机上完成加工的时间；

            //int[][] machinetime ;
            int[] jobtemp = new int[count[i]];         //每个工厂的job都有哪些
            for (int x = 0; x < count[i]; x++) {
                jobtemp[x] = timefactories[i][x];       //每个工厂的job(号)排列
            }
            //System.out.println(jobtemp);
            double[][] jobtimeTemp = new double[count[i]][numberOfStages];        //作业j的第s阶段的完成时间
            double[] pretimetemp = new double[count[i]];     // count[i]——记录每个工厂的job数

            for (int s = 0; s < numberOfStages; s++) {
                double[] machinetimePre = new double[numberOfMachines_[i][s]];
                double machinetime[][][] = new double[numberOfFactories][numberOfStages][numberOfMachines_[i][s]];

                starttime = new double[numberOfJobs_][numberOfStages][numberOfMachines_[i][s]];
                finishtime = new double[numberOfJobs_][numberOfStages][numberOfMachines_[i][s]];

                // if(numberOfMachines_[s]==1){
                // int jobIndex = timefactories[i][0];

                //得到第一个阶段第一个机器上的第一个job的加工时间
                if (s == 0) {
                    time[i][s][jobtemp[0]] = timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0];
                    jobtimeTemp[0][s] = time[i][s][jobtemp[0]];                    // 第一个工件的完成时间
                    jobEndPower[i][s][jobtemp[0]] = timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0] * machinePower[i][s][0];
                } else {      //得到除第一阶段的其他阶段的第一个机器上的第一个job的加工时间
                    time[i][s][jobtemp[0]] = time[i][s - 1][jobtemp[0]] + timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0];
                    jobtimeTemp[0][s] = time[i][s][jobtemp[0]];
                    jobEndPower[i][s][jobtemp[0]] = timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0] * machinePower[i][s][0];
                }


                if (numberOfMachines_[i][s] == 1) {                // 如果第i个工厂的第s阶段的机器数量是1
                    for (int j = 1; j < count[i]; j++) {
                        //jobIndex=jobtemp[j];     Math.max(machinetime[i][s][n],pretimetemp[k])
                        if (s == 0) {
                            time[i][s][jobtemp[j]] = time[i][s][jobtemp[j - 1]] + timeMatrix_[jobtemp[j]][0] / machineSpeed[i][s][0];
                            jobtimeTemp[j][s] = time[i][s][jobtemp[j]];
                            jobEndPower[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0] * machinePower[i][s][0];
                        } else {
                            time[i][s][jobtemp[j]] = Math.max(time[i][s][jobtemp[j - 1]], time[i][s - 1][jobtemp[j]]) + timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0];
                            jobtimeTemp[j][s] = time[i][s][jobtemp[j]];
                            jobEndPower[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0] * machinePower[i][s][0] + (time[i][s][jobtemp[j]] - time[i][s][jobtemp[j - 1]] - timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0]);
                        }
                    }
                } else {
                    for (int k = 1; k < count[i]; k++) {
                        int[] machineOfJobnumber = new int[numberOfMachines_[i][s]];
                        machinetime[i][s][0] = time[i][s][jobtemp[0]];   // 第几工厂第几阶段的第一个机器处理完第一个工件的结束时间
                        machineOfJobnumber[0] += 1;
                        machinetimePre[0] = machinetime[i][s][0];
                        double min = machinetime[i][s][0];        //先记录第s阶段的第一台并行机器的当前工作时间；
                        int n = 0;
                        for (int p = 0; p < numberOfMachines_[i][s]; p++) //与其他并行机器进行比较，找出时间最小的机器；
                        {
                            if (min > machinetime[i][s][p]) {
                                min = machinetime[i][s][p];
                                n = p;      //机器号
                                machineOfJobnumber[n] += 1;
                            }
                        }
                        int q = jobtemp[k];                //按顺序提取工厂i第一阶段中的工件号，对工件进行加工；
                        if (s == 0) {
                            starttime[q][s][n] = Math.max(machinetime[i][s][n], pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                            machinetime[i][s][n] = starttime[q][s][n] + timeMatrix_[q][s] / machineSpeed[i][s][n]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                            finishtime[q][s][n] = machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                            jobtimeTemp[k][s] = finishtime[q][s][n];
                            time[i][s][q] = jobtimeTemp[k][s];
                            jobEndPower[i][s][q] = timeMatrix_[q][s] / machineSpeed[i][s][n] * machinePower[i][s][n];
                            machinetimePre[n] = machinetime[i][s][n];
                        } else {
                            //pretimetemp[k]= time[i][s-1][q];//新加的
                            if (machineOfJobnumber[n] == 1) {
                                starttime[q][s][n] = Math.max(machinetime[i][s][n], pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                                machinetime[i][s][n] = starttime[q][s][n] + timeMatrix_[q][s] / machineSpeed[i][s][n]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                                finishtime[q][s][n] = machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                                jobtimeTemp[k][s] = finishtime[q][s][n];
                                time[i][s][q] = jobtimeTemp[k][s];
                                jobEndPower[i][s][jobtemp[k]] = timeMatrix_[jobtemp[k]][s] / machineSpeed[i][s][n] * machinePower[i][s][n];
                                machinetimePre[n] = machinetime[i][s][n];
                            } else {
                                starttime[q][s][n] = Math.max(machinetime[i][s][n], pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                                machinetime[i][s][n] = starttime[q][s][n] + timeMatrix_[q][s] / machineSpeed[i][s][n]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                                finishtime[q][s][n] = machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                                jobtimeTemp[k][s] = finishtime[q][s][n];
                                time[i][s][q] = jobtimeTemp[k][s];
                                jobEndPower[i][s][jobtemp[k]] = timeMatrix_[jobtemp[k]][s] / machineSpeed[i][s][n] * machinePower[i][s][n] + (starttime[q][s][n] - machinetimePre[n]);
                                machinetimePre[n] = machinetime[i][s][n];
                            }
                        }
                    }
                }

                int[] flg2 = new int[count[i]];           //生成暂时数组，便于将 jobtemp 和 jobtimeTemp 中的工件重新排列；
                for (int k = 0; k < count[i]; k++) {
                    flg2[k] = jobtemp[k];
                }

                for (int e = 0; e < count[i]; e++) {
                    for (int w = 0; w < count[i] - 1 - e; w++)      // 由于 jobtimeTemp 存储工件上一道工序的完工时间，在进行下一道工序生产时，按照先完工先生产的原则，
                    {                                            //因此，该循环的目的在于将 jobtimeTemp 中按照加工时间从小到大排列，同时 jobtemp 相应进行变换，来记录 jobtimeTemp 中的工件号；
                        if (jobtimeTemp[w][s] > jobtimeTemp[w + 1][s]) {
                            double flg5 = jobtimeTemp[w][s];
                            int flg6 = flg2[w];
                            jobtimeTemp[w] = jobtimeTemp[w + 1];
                            flg2[w] = flg2[w + 1];
                            jobtimeTemp[w + 1][s] = flg5;
                            flg2[w + 1] = flg6;
                        }
                    }
                }                                      //对上一阶段的工件完工时间进行排序

                for (int j = 0; j < count[i]; j++)    //更新 jobtemp，jobtimeTemp 的数据，开始下一道工序；
                {
                    jobtemp[j] = flg2[j];
                    pretimetemp[j] = jobtimeTemp[j][s];
                    //time[i][s][jobtemp[j]] = jobtimeTemp[j][s];
                }
            }
        }
//        return jobEndPower;
    }//calculate0


    @Override
    public int getPermutationLength() {
        return numberOfJobs_;
    }

    public void setNumberOfJobs_(int numberOfJobs_) {
        this.numberOfJobs_ = numberOfJobs_;
    }

    public int[][] getNumberOfMachines_() {
        return numberOfMachines_;
    }


    @Override
    public int getNumberOfFactories() {
        return numberOfFactories;
    }

//    @Override
//    public int getNumberOfWorkers() {
//        return numberOfWorker;
//    }


    public void setNumberOfFactories_(int numberOfFactories) {
        this.numberOfFactories = numberOfFactories;
    }

    public void setNumberOfStages(int numberOfStages) {
        this.numberOfStages = numberOfStages;
    }

    public void setNumberOfWorkers(int numberOfWorkers) {
        this.numberOfWorkers = numberOfWorkers;
    }

    public int getNumberOfStages() {
        return numberOfStages;
    }

    public int getProblemflag() {
        return problemflag;
    }

    public int getNumberOfJobs_() {
        return numberOfJobs_;
    }

    public int[] getnw() {
        return nw;
    }

/*    public int[][] getJobFactoryCluster() {
        return jobFactoryCluster;
    }

    public void setJobFactoryCluster(int[][] jobFactoryCluster) {
        this.jobFactoryCluster = jobFactoryCluster;
    }*/


}




