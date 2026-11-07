package org.uma.jmetal.problem.multiobjective.dfsp;

import org.uma.jmetal.problem.impl.AbstractIntegerPermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.List;

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


public class DHFSP_MOEAD extends AbstractIntegerPermutationProblem {

    protected int numberOfJobs_ ;
    protected int numberOfStages ;
    protected int [][]numberOfMachines_;
    protected int numberOfFactories ;
    protected double[][][] machineSpeed ;
    protected int [][][] machinePower ;
    protected int problemflag ;

    protected int[][] timeMatrix_;     // 时间矩阵（问题集中的内容）
    protected int[] timeArray1;      //一维时间和
    protected int[][] jobindex;

    public static int[][] jobFactoryCluster;
    public static int[][] machinetime;

/*    public DFSP3(int problemflag, int numberOfJobs, int numberOfMachines, int snumber) {
        super();
    }*/
    //protected int[] factorie_capacity = new int[factories];


    /**
     * Creates a new instance of problem DFSP.
     */

    protected void init(String filename1) throws IOException {
        // 读取数据
        int count=0;
        //numberOfMachines_=new int [numberOfStages];
        numberOfMachines_=new int[numberOfFactories][numberOfStages];
        machineSpeed = new double[numberOfFactories][numberOfStages][5];
        machinePower = new int[numberOfFactories][numberOfStages][5];

        // 原 timeMatrix_=new int[numberOfStages][numberOfJobs_];
        timeMatrix_=new int[numberOfJobs_][numberOfStages];

        BufferedReader data1 = new BufferedReader(new InputStreamReader(new FileInputStream(filename1)));

        // 读取一行数据，数据格式:
        //number of jobs, number of machines, initial seed, upper bound and lower bound :
        //          20           5   873654221        1278        1232
        //processing times :
        //54 83 15 71 77 36 53 38 27 87 76 91 14 29 12 77 32 87 68 94       //  5行20列


        String lineTxt1 = null;
        lineTxt1 = data1.readLine();
        lineTxt1 = data1.readLine();    //无效信息跳过2行


        for(int f=0;f<numberOfFactories;f++) {
            if((lineTxt1 = data1.readLine()) != null ) {
                String[] strcol = lineTxt1.split(",");   // 分割字符串（一个数后面一个空格）
                //System.out.println(lineTxt1);
                for (int i = 0; i < numberOfStages; i++) {
                    numberOfMachines_[f][i] = Integer.parseInt(strcol[i]);
                }
            }
        }
        //System.out.println(numberOfMachines_);

        lineTxt1 = data1.readLine();

        for (int f = 0; f < numberOfFactories; f++) {
            for (int i = 0; i < numberOfStages; i++) {
                if((lineTxt1 = data1.readLine()) != null ) {
                    String[] strcol = lineTxt1.split(",");   // 分割字符串（一个数后面一个空格）
                    //System.out.println(lineTxt1);

                    for (int n = 0; n < numberOfMachines_[f][i]; n++) {
                        machineSpeed[f][i][n] =Double.parseDouble(strcol[n]);
                    }

                }
            }
        }
        //System.out.println(machineSpeed);

        lineTxt1 = data1.readLine();

        for (int f = 0; f < numberOfFactories; f++) {
            //System.out.println(lineTxt1);
            for (int i = 0; i < numberOfStages; i++) {
                if((lineTxt1 = data1.readLine()) != null ) {
                    String[] strcol = lineTxt1.split(",");   // 分割字符串（一个数后面一个空格）
                    for (int n = 0; n < numberOfMachines_[f][i]; n++) {
                        machinePower[f][i][n] =Integer.parseInt(strcol[n]);;
                    }

                }
            }

        }
        //System.out.println(machinePower);

        lineTxt1 = data1.readLine();
        while ((lineTxt1 = data1.readLine()) != null) {
            //System.out.println(lineTxt1);
            // int shu=0;
            String[] strcol = lineTxt1.split(",");   // 分割字符串（一个数后面一个空格）
            for(int i=0;i<numberOfStages;i++) {
                timeMatrix_[count][i]=Integer.parseInt(strcol[i]);
            }
            count ++;
        }
        //System.out.println(timeMatrix_);
        data1.close();
    }


    public static int sumColumn(int[][] timeArray, int columnIndex){
        int row = timeArray.length;
        int sum = 0;
        for (int i = 0 ; i < row ; i++){
            sum += timeArray[i][columnIndex];
        }
        return sum;
    }


    public static int[][] cluster(int[] p, int k) {
        // 存放聚类旧的聚类中心
        int[] c = new int[k];
        // 存放新计算的聚类中心
        int[] nc = new int[k];
        // 存放放回结果
        int[][] g;
        // 初始化聚类中心
        // 经典方法是随机选取 k 个
        // 聚类中心的选取不影响最终结果
        for (int i = 0; i < k; i++)
            c[i] = p[i];
        // 循环聚类，更新聚类中心
        // 到聚类中心不变为止
        while (true) {
            // 根据聚类中心将元素分类
            g = group(p, c);
            // 计算分类后的聚类中心
            for (int i = 0; i < g.length; i++) {
                nc[i] = center(g[i]);
            }
            // 如果聚类中心不同
            if (!equal(nc, c)) {
                // 为下一次聚类准备
                c = nc;
                nc = new int[k];
            } else // 聚类结束
                break;
        }
        // 返回聚类结果
        return g;
    }
    /*
     * 聚类中心函数
     * 简单的一维聚类返回其算数平均值
     * 可扩展
     */
    public static int center(int[] p) {
        return sum(p) / p.length;
    }
    /*
     * 给定 double 型数组 p 和聚类中心 c。
     * 根据 c 将 p 中元素聚类。返回二维数组。
     * 存放各组元素。
     */
    public static int[][] group(int[] p, int[] c) {
        // 中间变量，用来分组标记
        int[] gi = new int[p.length];
        // 考察每一个元素 pi 同聚类中心 cj 的距离
        // pi 与 cj 的距离最小则归为 j 类
        for (int i = 0; i < p.length; i++) {
            // 存放距离
            double[] d = new double[c.length];
            // 计算到每个聚类中心的距离
            for (int j = 0; j < c.length; j++) {
                d[j] = distance(p[i], c[j]);
            }
            // 找出最小距离，返回最小值的下标
            int ci = min(d);
            // 标记属于哪一组
            gi[i] = ci;
        }
        // 存放分组结果
        int[][] g = new int[c.length][];
        // 遍历每个聚类中心，分组
        for (int i = 0; i < c.length; i++) {
            // 中间变量，记录聚类后每一组的大小
            int s = 0;
            // 计算每一组的长度
            for (int j = 0; j < gi.length; j++)
                if (gi[j] == i)
                    s++;
            // 存储每一组的成员
            g[i] = new int[s];
            s = 0;
            // 根据分组标记将各元素归位
            for (int j = 0; j < gi.length; j++)
                if (gi[j] == i) {
                    g[i][s] = p[j];
                    s++;
                }
        }
        // 返回分组结果
        return g;
    }

    /*
     * 计算两个点之间的距离， 这里采用最简单得一维欧氏距离， 可扩展。
     */
    public static double distance(double x, double y) {
        return Math.abs(x - y);
    }

    /*
     * 返回给定 double 数组各元素之和。
     */
    public static int sum(int[] p) {
        int sum = 0;
        for (int i = 0; i < p.length; i++)
            sum += p[i];
        return sum;
    }

    /*
     * 给定 double 类型数组，返回最小值得下标。
     */
    public static int min(double[] p) {
        int i = 0;
        double m = p[0];
        for (int j = 1; j < p.length; j++) {
            if (p[j] < m) {
                i = j;
                m = p[j];
            }
        }
        return i;
    }

    /*
     * 判断两个 double 数组是否相等。 长度一样且对应位置值相同返回真。
     */
    public static boolean equal(int[] a, int[] b) {
        if (a.length != b.length)
            return false;
        else {
            for (int i = 0; i < a.length; i++) {
                if (a[i] != b[i])
                    return false;
            }
        }
        return true;
    }



    //自己
    public DHFSP_MOEAD(int numberOfJobs , int numberOfStages, int numberOfFactories, int problemId) throws IOException {

        setNumberOfVariables(numberOfJobs);
        setNumberOfObjectives(2);
        setNumberOfFactories(numberOfFactories);
        setNumberOfStages(numberOfStages);

        setName("DHFSP");
        this.setNumberOfJobs_(numberOfJobs);
    //this.setNumberOfMachines_(numberOfMachines);
        this.setNumberOfFactories_(numberOfFactories);
        this.setNumberOfStages(numberOfStages);

        //this.setProblemflag(problemflag);
        timeMatrix_ = new int[numberOfJobs][numberOfStages];
        //idleflag = new int[numberOfMachines_];

        StringBuffer sbInputFileName = new StringBuffer();
        String strFolderName = new String("/Users/mumumu/Desktop/"); //TODO 修改输入数据目录
        //init("C:\\LocalDisk\\0.research\\journal-proposal-ZhangLiHouYangGen-PSO-DE-DFSP\\data-FSP\\" + numberOfJobs_ + "_" + numberOfMachines_ + "_"+snumber+".txt");
        sbInputFileName.append(strFolderName);
        sbInputFileName.append(numberOfJobs).append("_");
        sbInputFileName.append(numberOfStages).append("_");
        sbInputFileName.append(numberOfFactories);
        sbInputFileName.append("_").append(problemId);
        sbInputFileName.append(".txt");
        init(sbInputFileName.toString());
    }

/*    private void setProblemflag(int problemflag) {
        this.problemflag= problemflag;
    }   */   // 带flag的暂时没用

    private void setNumberOfMachines_(int [][] numberOfMachines_) {
        this.numberOfMachines_ = numberOfMachines_;
    }



    /** Evaluate() method */
    public void evaluate(PermutationSolution<Integer> solution) throws ArrayIndexOutOfBoundsException {    //这是一个粒子，一群粒子的话是用List<PermutationSolution<Integer>>

        //f[1]:Makespan.f[2]:TotalFlowTime

        List<Integer> temp = solution.getVariables();  //工件向量
        List<Integer> tempid = solution.getVariablesid();   //工厂向量

        int [][] tem = new int[2][temp.size()];    //tem相当于一个粒子

        for(int i=0;i<temp.size();i++){

            tem[0][i] = temp.get(i).intValue();
            tem[1][i] = tempid.get(i).intValue();
//tem相当于一个粒子
        }
        //System.out.print(tem);

        double[] f = new double[getNumberOfObjectives()];

        for(int i=0;i<getNumberOfObjectives();i++){
            f[i]=0;
        }

        double[][][] time = calculate(tem);
        //double[][][] time = calculate(tem);
        double[][][] jobEndPower = calculatePower(tem);
        //System.out.println(time);

        double[] makespanTemp= new double[numberOfFactories];
        //记录所有工厂的makespan
        for(int i=0; i<numberOfFactories; i++){
            int maxtimeindex =0;
            for(int j=1;j<numberOfJobs_;j++){

                if(time[i][numberOfStages-1][maxtimeindex]<time[i][numberOfStages-1][j]){
                    maxtimeindex=j;
                }
            }
            makespanTemp[i]=time[i][numberOfStages-1][maxtimeindex];
        }

/*        int[][] temp1 = new int[numberOfFactories][2];//temp1[i][0]记录的是makespan；temp1[i][1]记录的是当前工厂最后一个job的位置
        for(int i=0;i<numberOfFactories;i++){

            for(int j=0;j<numberOfJobs_;j++){

                if(time[i][numberOfStages-1][j]!=0 && time[i][numberOfStages-1][j+1]==0) {//相当于是判断工厂里面第j位是否是最后一位

                    temp1[i][0] = time[i][numberOfStages-1][j];
                    temp1[i][1] = j;
                    break;
                }
            }

        }*/

        //判断makespan的最大值
        int max = 0; int min = 0;
        for(int i=1;i<numberOfFactories;i++){
            if(makespanTemp[i]>makespanTemp[max]) {
                max = i;
            }
            if(makespanTemp[i]<makespanTemp[min]) {
                min = i;
            }
        }

        //目标一的值
        f[0] = makespanTemp[max];
        //f[1] = time[max][numberOfMachines_-1][temp1[max][1]];      //  假设只有一个目标，让两个目标值相等
/*        f[3]=max;
        f[2]=min;*/

        //计算所有工厂的最大流
        int[] ftemp= new int[numberOfFactories];
        for(int i=0;i<numberOfFactories;i++){

            for(int j=0;j<numberOfJobs_;j++){   //time[i][numberOfStages-1][numberOfJobs_]
                ftemp[i] += time[i][numberOfStages-1][j];
                // f[1] = f[1] + time[i][numberOfMachines_-1][j];
            }
        }


        for(int i=0;i<numberOfFactories;i++){
            for(int j=0;j<numberOfStages;j++){
                for(int k=0;k<numberOfJobs_;k++){
                    f[1]=f[1]+jobEndPower[i][j][k];
                }
            }
        }

        //判断那个工厂的最大流最大
/*        int maxflowtimeindex=0;   //ftemp[0];
        int minindex=0;
            for (int i = 1; i < ftemp.length; i++) {
                if (ftemp[i] > ftemp[maxflowtimeindex]) {
                    maxflowtimeindex=i;
                }
                if (ftemp[i] > ftemp[minindex]) {
                    minindex=i;
                }
            }

            f[1] = ftemp[maxflowtimeindex];*/
/*            f[4] = minindex;
            f[5] = maxflowtimeindex;*/


 /*       //判断那个工厂的最大流最大
        f[1] = ftemp[0];
        if(ftemp[1]>f[1]){
            f[1] = ftemp[1];
        }
        if(ftemp[2]>f[1]){
            f[1] = ftemp[2];
        }                //目标2*/                    //之前

        solution.setObjective(0, f[0]);
        solution.setObjective(1, f[1]);
/*        solution.setObjective(2, f[2]);
        solution.setObjective(3, f[3]);
        solution.setObjective(4, f[4]);
        solution.setObjective(5, f[5]);*/
    }

    //calculate the time table of sequence.    计算序列的时间表
    /*
     int [][] tem = new int[2][temp.size()];

        for(int i=0;i<temp.size();i++){
            tem[0][i] = temp.get(i).intValue();
            tem[1][i] = tempid.get(i).intValue();
        }
     */

    protected double[][][] calculate(int[][] solution) throws ArrayIndexOutOfBoundsException{

        for(int i=0;i<solution[0].length;i++){
            //System.out.print("\t="+solution[0][i]);
        }
        //System.out.println();
        for(int i=0;i<solution[1].length;i++){
            //System.out.print("\t="+solution[1][i]);
        }
        //System.out.println();

        double[][][] jobEndPower = new double[numberOfFactories][numberOfStages][numberOfJobs_];
        double[][][] time = new double[numberOfFactories][numberOfStages][numberOfJobs_];  //存储当前粒子的时间完成表
        int[][] timefactories = new int[numberOfFactories][numberOfJobs_];  //三个一维向量  一维向量的空间大小是所有工件的数量大小

        for(int i=0;i<timefactories.length;i++){                                //获取行的长度
            for(int j=0;j<timefactories[i].length;j++){
                timefactories[i][j] = -1;                                             //三个一维空间的里的数都先存放-1
            }
        }

        int [] count = new int[numberOfFactories];          //记录每个工厂的job数

        //完成了把job分配给工厂的功能，并且记录了每个工厂的job数
        for(int i=0;i<solution[1].length;i++){
            // System.out.println(count.length);
            /*System.out.println(numberOfFactories);
            System.out.println(numberOfMachines_);
            System.out.println(numberOfJobs_);*/
            //  tem[1][i] 是工厂向量里面的值
            count[solution[1][i]] = count[solution[1][i]]+1;  //记录工厂（tem[1][i]）里面的jobs数，每次加1    //也就是说 计算几个1 几个2 几个3

            //把job分给对应工厂
            for(int j=0;j<solution[0].length;j++){
                int factoryIndex = solution[1][i];
                if(timefactories[factoryIndex][j]==-1){
                    timefactories[factoryIndex][j] = solution[0][i];
                    break;   //很重要
                }
            }
        }

        // int [] tempjob=new int[numberOfFactories];
        //System.out.println("每个工厂的Job顺序：");
        for(int i=0;i<numberOfFactories;i++) {
            for (int j = 0; j < numberOfJobs_; j++) {
                if(timefactories[i][j]!=-1){
                }
                //System.out.print(" " + timefactories[i][j]);
            }
            //System.out.println();
        }

        //System.out.println("每个工厂的Job数量：");
        for(int mm=0;mm<count.length;mm++){
            //System.out.print("---"+count[mm]);
        }
        //System.out.println();

        //计算公式部分
        //System.out.println("遍历每个工厂的Job：");

        int endflag[][]=new int[numberOfFactories][1];

        for(int i=0;i<numberOfFactories;i++) {
            //System.out.println("工厂："+i);

            double[][][] starttime = new double[count[i]][][];//第几个工件第几道工序在第几台并行机上开始加工的时间；
            double[][][] finishtime = new double[count[i]][][];//第几个工件第几道工序在第几台并行机上完成加工的时间；

            //int[][] machinetime ;
            int [] jobtemp= new int [count[i]];         //每个工厂的job都有哪些
            for(int x=0; x<count[i];x++) {
                jobtemp[x]=timefactories[i][x];       //每个工厂的job(号)排列
            }
            //System.out.println(jobtemp);
            double [][] jobtimeTemp = new double [count[i]][numberOfStages];        //作业j的第s阶段的完成时间
            double [] pretimetemp= new double[count[i]];     // count[i]——记录每个工厂的job数

            for(int s=0;s<numberOfStages;s++) {
                double[] machinetimePre=new double [numberOfMachines_[i][s]];
                double machinetime[][][]= new double[numberOfFactories][numberOfStages][numberOfMachines_[i][s]];

                starttime = new double[numberOfJobs_][numberOfStages][numberOfMachines_[i][s]];
                finishtime = new double[numberOfJobs_][numberOfStages][numberOfMachines_[i][s]];

                // if(numberOfMachines_[s]==1){
                // int jobIndex = timefactories[i][0];

                //得到第一个阶段第一个机器上的第一个job的加工时间
                if(s==0) {
                    time[i][s][jobtemp[0]] = timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0];
                    jobtimeTemp[0][s]=time[i][s][jobtemp[0]];                    // 第一个工件的完成时间
                    jobEndPower[i][s][jobtemp[0]] = timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0] * machinePower[i][s][0];
                }
                else{      //得到除第一阶段的其他阶段的第一个机器上的第一个job的加工时间
                    time[i][s][jobtemp[0]] = time[i][s-1][jobtemp[0]]+ timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0];
                    jobtimeTemp[0][s]=time[i][s][jobtemp[0]];
                    jobEndPower[i][s][jobtemp[0]] = timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0] * machinePower[i][s][0];
                }



                if (numberOfMachines_[i][s] == 1){                // 如果第i个工厂的第s阶段的机器数量是1
                    for (int j = 1; j < count[i]; j++) {
                        //jobIndex=jobtemp[j];     Math.max(machinetime[i][s][n],pretimetemp[k])
                        if(s==0) {
                            time[i][s][jobtemp[j]] = time[i][s][jobtemp[j - 1]] + timeMatrix_[jobtemp[j]][0] / machineSpeed[i][s][0];
                            jobtimeTemp[j][s] = time[i][s][jobtemp[j]];
                            jobEndPower[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0] * machinePower[i][s][0];
                        }
                        else{
                            time[i][s][jobtemp[j]] = Math.max(time[i][s][jobtemp[j - 1]], time[i][s - 1][jobtemp[j]]) + timeMatrix_[jobtemp[j]][0] / machineSpeed[i][s][0];
                            jobtimeTemp[j][s] = time[i][s][jobtemp[j]];
                            jobEndPower[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0] * machinePower[i][s][0] + (time[i][s][jobtemp[j]]-time[i][s][jobtemp[j-1]]-timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0]);
                        }
                    }
                }
                else {
                    for(int k=1;k<count[i];k++){
                        int [] machineOfJobnumber = new int [numberOfMachines_[i][s]];
                        machinetime[i][s][0] = time[i][s][jobtemp[0]];   // 第几工厂第几阶段的第一个机器处理完第一个工件的结束时间
                        machineOfJobnumber[0]+=1;
                        machinetimePre[0]=machinetime[i][s][0];
                        double min=machinetime[i][s][0];        //先记录第s阶段的第一台并行机器的当前工作时间；
                        int n=0;
                        for (int p=0; p<numberOfMachines_[i][s]; p++) //与其他并行机器进行比较，找出时间最小的机器；
                        {
                            if (min>machinetime[i][s][p])
                            {
                                min=machinetime[i][s][p];
                                n=p;      //机器号
                                machineOfJobnumber[n]+=1;
                            }
                        }
                        int q=jobtemp[k];                //按顺序提取工厂i第一阶段中的工件号，对工件进行加工；
                        if(s==0){
                            starttime[q][s][n]=Math.max(machinetime[i][s][n],pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                            machinetime[i][s][n]=starttime[q][s][n]+timeMatrix_[q][s]/machineSpeed[i][s][n]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                            finishtime[q][s][n]=machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                            jobtimeTemp[k][s]=finishtime[q][s][n];
                            jobEndPower[i][s][q] = timeMatrix_[q][s] / machineSpeed[i][s][n] * machinePower[i][s][n] ;
                            machinetimePre[n]=machinetime[i][s][n];
                        }
                        else{
                            //pretimetemp[k]= time[i][s-1][q];//新加的
                            if(machineOfJobnumber[n]==1){
                                starttime[q][s][n]=Math.max(machinetime[i][s][n],pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                                machinetime[i][s][n]=starttime[q][s][n]+timeMatrix_[q][s]/machineSpeed[i][s][n]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                                finishtime[q][s][n]=machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                                jobtimeTemp[k][s]=finishtime[q][s][n];
                                jobEndPower[i][s][jobtemp[k]] = timeMatrix_[jobtemp[k]][s] / machineSpeed[i][s][n] * machinePower[i][s][n] ;
                                machinetimePre[n]=machinetime[i][s][n];
                            }
                            else{
                                starttime[q][s][n]=Math.max(machinetime[i][s][n],pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                                machinetime[i][s][n]=starttime[q][s][n]+timeMatrix_[q][s]/machineSpeed[i][s][n]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                                finishtime[q][s][n]=machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                                jobtimeTemp[k][s]=finishtime[q][s][n];
                                jobEndPower[i][s][jobtemp[k]] = timeMatrix_[jobtemp[k]][s] / machineSpeed[i][s][n] * machinePower[i][s][n] + (starttime[q][s][n]-machinetimePre[n]);
                                machinetimePre[n]=machinetime[i][s][n];
                            }
                        }
                    }
                }

                int[] flg2 = new int [count[i]];           //生成暂时数组，便于将 jobtemp 和 jobtimeTemp 中的工件重新排列；
                for(int k=0; k<count[i]; k++)
                {
                    flg2[k]=jobtemp[k];
                }

                for (int e=0; e<count[i]; e++)
                {
                    for(int w=0; w<count[i]-1-e; w++)      // 由于 jobtimeTemp 存储工件上一道工序的完工时间，在进行下一道工序生产时，按照先完工先生产的原则，
                    {                                            //因此，该循环的目的在于将 jobtimeTemp 中按照加工时间从小到大排列，同时 jobtemp 相应进行变换，来记录 jobtimeTemp 中的工件号；
                        if (jobtimeTemp[w][s]>jobtimeTemp[w+1][s])
                        {
                            double flg5=jobtimeTemp[w][s];
                            int flg6=flg2[w];
                            jobtimeTemp[w]=jobtimeTemp[w+1];
                            flg2[w]=flg2[w+1];
                            jobtimeTemp[w+1][s]=flg5;
                            flg2[w+1]=flg6;
                        }
                    }
                }                                      //对上一阶段的工件完工时间进行排序

                for(int j=0; j<count[i]; j++)    //更新 jobtemp，jobtimeTemp 的数据，开始下一道工序；
                {
                    jobtemp[j] = flg2[j];
                    pretimetemp[j] = jobtimeTemp[j][s];
                    time[i][s][jobtemp[j]] = jobtimeTemp[j][s];
                }
            }
        }
        return time;
    }//calculate

    protected double[][][] calculatePower(int[][] solution) throws ArrayIndexOutOfBoundsException{

        for(int i=0;i<solution[0].length;i++){
            //System.out.print("\t="+solution[0][i]);
        }
        //System.out.println();
        for(int i=0;i<solution[1].length;i++){
            //System.out.print("\t="+solution[1][i]);
        }
        //System.out.println();

        double[][][] jobEndPower = new double[numberOfFactories][numberOfStages][numberOfJobs_];
        double[][][] time = new double[numberOfFactories][numberOfStages][numberOfJobs_];  //存储当前粒子的时间完成表
        int[][] timefactories = new int[numberOfFactories][numberOfJobs_];  //三个一维向量  一维向量的空间大小是所有工件的数量大小

        for(int i=0;i<timefactories.length;i++){                                //获取行的长度
            for(int j=0;j<timefactories[i].length;j++){
                timefactories[i][j] = -1;                                             //三个一维空间的里的数都先存放-1
            }
        }

        int [] count = new int[numberOfFactories];          //记录每个工厂的job数

        //完成了把job分配给工厂的功能，并且记录了每个工厂的job数
        for(int i=0;i<solution[1].length;i++){
            // System.out.println(count.length);
            /*System.out.println(numberOfFactories);
            System.out.println(numberOfMachines_);
            System.out.println(numberOfJobs_);*/
            //  tem[1][i] 是工厂向量里面的值
            count[solution[1][i]] = count[solution[1][i]]+1;  //记录工厂（tem[1][i]）里面的jobs数，每次加1    //也就是说 计算几个1 几个2 几个3

            //把job分给对应工厂
            for(int j=0;j<solution[0].length;j++){
                int factoryIndex = solution[1][i];
                if(timefactories[factoryIndex][j]==-1){
                    timefactories[factoryIndex][j] = solution[0][i];
                    break;   //很重要
                }
            }
        }

        // int [] tempjob=new int[numberOfFactories];
        //System.out.println("每个工厂的Job顺序：");
        for(int i=0;i<numberOfFactories;i++) {
            for (int j = 0; j < numberOfJobs_; j++) {
                if(timefactories[i][j]!=-1){
                }
                //System.out.print(" " + timefactories[i][j]);
            }
            //System.out.println();
        }

        //System.out.println("每个工厂的Job数量：");
        for(int mm=0;mm<count.length;mm++){
            //System.out.print("---"+count[mm]);
        }
        //System.out.println();

        //计算公式部分
        //System.out.println("遍历每个工厂的Job：");

        int endflag[][]=new int[numberOfFactories][1];

        for(int i=0;i<numberOfFactories;i++) {
            //System.out.println("工厂："+i);

            double[][][] starttime ;//第几个工件第几道工序在第几台并行机上开始加工的时间；
            double[][][] finishtime;//第几个工件第几道工序在第几台并行机上完成加工的时间；

            //int[][] machinetime ;
            int [] jobtemp= new int [count[i]];         //每个工厂的job都有哪些
            for(int x=0; x<count[i];x++) {
                jobtemp[x]=timefactories[i][x];       //每个工厂的job(号)排列
            }
            //System.out.println(jobtemp);
            double [][] jobtimeTemp = new double [count[i]][numberOfStages];        //作业j的第s阶段的完成时间
            double [] pretimetemp= new double[count[i]];     // count[i]——记录每个工厂的job数
            int [][] jobOfwhichMachine=new int[numberOfStages][numberOfJobs_];   //某阶段某工件的加工机器号

            for(int s = 0; s < numberOfStages; s++) {
                for(int m = 0; m < numberOfJobs_; m++) {
                    jobOfwhichMachine[s][m]=-1;
                }
            }
            for(int s=0;s<numberOfStages;s++) {
                double[] machinetimePre=new double [numberOfMachines_[i][s]];
                double machinetime[][][]= new double[numberOfFactories][numberOfStages][numberOfMachines_[i][s]];

                starttime = new double[numberOfJobs_][numberOfStages][numberOfMachines_[i][s]];
                finishtime = new double[numberOfJobs_][numberOfStages][numberOfMachines_[i][s]];


                // if(numberOfMachines_[s]==1){
                // int jobIndex = timefactories[i][0];

                //得到第一个阶段第一个机器上的第一个job的加工时间
                if(s==0) {
                    time[i][s][jobtemp[0]] = timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0];
                    jobtimeTemp[0][s]=time[i][s][jobtemp[0]];                    // 第一个工件的完成时间
                    jobEndPower[i][s][jobtemp[0]] = timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0] * machinePower[i][s][0];
                    jobOfwhichMachine[s][jobtemp[0]]=0;
                }
                else{      //得到除第一阶段的其他阶段的第一个机器上的第一个job的加工时间
                    time[i][s][jobtemp[0]] = time[i][s-1][jobtemp[0]]+ timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0];
                    jobtimeTemp[0][s]=time[i][s][jobtemp[0]];
                    jobEndPower[i][s][jobtemp[0]] = timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0] * machinePower[i][s][0];
                    jobOfwhichMachine[s][jobtemp[0]]=0;
                }



                if (numberOfMachines_[i][s] == 1){                // 如果第i个工厂的第s阶段的机器数量是1
                    for (int j = 1; j < count[i]; j++) {
                        //jobIndex=jobtemp[j];     Math.max(machinetime[i][s][n],pretimetemp[k])
                        if(s==0) {
                            time[i][s][jobtemp[j]] = time[i][s][jobtemp[j - 1]] + timeMatrix_[jobtemp[j]][0] / machineSpeed[i][s][0];
                            jobtimeTemp[j][s] = time[i][s][jobtemp[j]];
                            jobEndPower[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0] * machinePower[i][s][0];
                            jobOfwhichMachine[s][jobtemp[j]]=0;
                        }
                        else{
                            time[i][s][jobtemp[j]] = Math.max(time[i][s][jobtemp[j - 1]], time[i][s - 1][jobtemp[j]]) + timeMatrix_[jobtemp[j]][0] / machineSpeed[i][s][0];
                            jobtimeTemp[j][s] = time[i][s][jobtemp[j]];
                            jobEndPower[i][s][jobtemp[j]] = timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0] * machinePower[i][s][0] + (time[i][s][jobtemp[j]]-time[i][s][jobtemp[j-1]]-timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0]);
                            jobOfwhichMachine[s][jobtemp[j]]=0;
                        }
                    }
                }
                else {
                    for(int k=1;k<count[i];k++){
                        int [] machineOfJobnumber = new int [numberOfMachines_[i][s]];
                        machinetime[i][s][0] = time[i][s][jobtemp[0]];   // 第几工厂第几阶段的第一个机器处理完第一个工件的结束时间
                        machineOfJobnumber[0]+=1;
                        machinetimePre[0]=machinetime[i][s][0];
                        double min=machinetime[i][s][0];        //先记录第s阶段的第一台并行机器的当前工作时间；
                        int n=0;
                        for (int p=0; p<numberOfMachines_[i][s]; p++) //与其他并行机器进行比较，找出时间最小的机器；
                        {
                            if (min>machinetime[i][s][p])
                            {
                                min=machinetime[i][s][p];
                                n=p;      //机器号
                                machineOfJobnumber[n]+=1;
                            }
                        }
                        jobOfwhichMachine[s][jobtemp[k]]=n;
                        int q=jobtemp[k];                //按顺序提取工厂i第一阶段中的工件号，对工件进行加工；
                        if(s==0){
                            starttime[q][s][n]=Math.max(machinetime[i][s][n],pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                            machinetime[i][s][n]=starttime[q][s][n]+timeMatrix_[q][s]/machineSpeed[i][s][n]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                            finishtime[q][s][n]=machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                            jobtimeTemp[k][s]=finishtime[q][s][n];
                            jobEndPower[i][s][q] = timeMatrix_[q][s] / machineSpeed[i][s][n] * machinePower[i][s][n] ;
                            machinetimePre[n]=machinetime[i][s][n];
                        }
                        else{
                            //pretimetemp[k]= time[i][s-1][q];//新加的
                            if(machineOfJobnumber[n]==1){
                                starttime[q][s][n]=Math.max(machinetime[i][s][n],pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                                machinetime[i][s][n]=starttime[q][s][n]+timeMatrix_[q][s]/machineSpeed[i][s][n]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                                finishtime[q][s][n]=machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                                jobtimeTemp[k][s]=finishtime[q][s][n];
                                jobEndPower[i][s][jobtemp[k]] = timeMatrix_[jobtemp[k]][s] / machineSpeed[i][s][n] * machinePower[i][s][n] ;
                                machinetimePre[n]=machinetime[i][s][n];
                            }
                            else{
                                starttime[q][s][n]=Math.max(machinetime[i][s][n],pretimetemp[k]);  //开始加工时间取该机器的当前时间和该工件上一道工序完工时间的最大值；
                                machinetime[i][s][n]=starttime[q][s][n]+timeMatrix_[q][s]/machineSpeed[i][s][n]; //机器的累计加工时间等于机器开始加工的时刻，加上该工件加工所用的时间；
                                finishtime[q][s][n]=machinetime[i][s][n];                 //工件的完工时间就是该机器当前的累计加工时间；
                                jobtimeTemp[k][s]=finishtime[q][s][n];
                                jobEndPower[i][s][jobtemp[k]] = timeMatrix_[jobtemp[k]][s] / machineSpeed[i][s][n] * machinePower[i][s][n] + (starttime[q][s][n]-machinetimePre[n]);
                                machinetimePre[n]=machinetime[i][s][n];
                            }
                        }
                    }
                }

                int[] flg2 = new int [count[i]];           //生成暂时数组，便于将 jobtemp 和 jobtimeTemp 中的工件重新排列；
                for(int k=0; k<count[i]; k++)
                {
                    flg2[k]=jobtemp[k];
                }

                for (int e=0; e<count[i]; e++)
                {
                    for(int w=0; w<count[i]-1-e; w++)      // 由于 jobtimeTemp 存储工件上一道工序的完工时间，在进行下一道工序生产时，按照先完工先生产的原则，
                    {                                            //因此，该循环的目的在于将 jobtimeTemp 中按照加工时间从小到大排列，同时 jobtemp 相应进行变换，来记录 jobtimeTemp 中的工件号；
                        if (jobtimeTemp[w][s]>jobtimeTemp[w+1][s])
                        {
                            double flg5=jobtimeTemp[w][s];
                            int flg6=flg2[w];
                            jobtimeTemp[w]=jobtimeTemp[w+1];
                            flg2[w]=flg2[w+1];
                            jobtimeTemp[w+1][s]=flg5;
                            flg2[w+1]=flg6;
                        }
                    }
                }                                      //对上一阶段的工件完工时间进行排序

                for(int j=0; j<count[i]; j++)    //更新 jobtemp，jobtimeTemp 的数据，开始下一道工序；
                {
                    jobtemp[j] = flg2[j];
                    pretimetemp[j] = jobtimeTemp[j][s];
                    time[i][s][jobtemp[j]] = jobtimeTemp[j][s];
                }
                //int flag = jobtemp[count[i]-1];
            }
            //endflag[numberOfFactories-1][0]=jobtemp[count[i]];
            //time[numberOfFactories][numberOfStages-1-1][0]= jobtemp[count[i]-1];

/*            int totaltime=0;
            for (int g=0; g<numberOfMachines_[numberOfStages]; g++) //比较最后一道工序机器的累计加工时间，最大时间就是该流程的加工时间；
                if (totaltime<machinetime[numberOfStages-1][g])
                {
                    totaltime=machinetime[numberOfStages-1][g];
                }*/

/*            for(int r=0; r<count[i]; r++)  //将数组归零，便于下一个个体的加工时间统计；
                for(int j=0; j<numberOfStages; j++)
                    for(int t=0; t<numberOfMachines_[j]; t++)
                    {
                        starttime[r][j][t]=0;
                        finishtime[r][j][t]=0;
                        //machinetime[j][t]=0;
                    }*/
            // makespan=totaltime;


            // System.out.println(time);
            double [][][]timesort = new double[numberOfFactories][numberOfStages][numberOfJobs_];
            int [][]sortjobindex=new int [numberOfStages][numberOfJobs_];
            for(int s=0;s<numberOfStages;s++){
                for(int j=0;j<numberOfJobs_;j++){
                    timesort[i][s][j]=time[i][s][j];
                    sortjobindex[s][j]=j;
                }
            }
            double temp; int indextemp;
            for(int s=0;s<numberOfStages;s++){
                for(int j=0;j<numberOfJobs_;j++){
                    for (int k =0; k < numberOfJobs_-1-j; k++) {  //直接选择排序(两重for循环排序)
                        if (timesort[i][s][k]<timesort[i][s][k+1]) {
                            temp = timesort[i][s][k];
                            timesort[i][s][k] = timesort[i][s][k+1];
                            timesort[i][s][k+1] = temp;

                            indextemp=sortjobindex[s][k];
                            sortjobindex[s][k]=sortjobindex[s][k+1];
                            sortjobindex[s][k+1]=indextemp;
                        }
                    }
                }
            }

            double [] StartOfstageNext= new double[numberOfJobs_];
            double [] StartOfnextjob= new double[numberOfJobs_];
            starttime = new double[numberOfJobs_][numberOfStages][5];
            finishtime = new double[numberOfJobs_][numberOfStages][5];
            for(int s=numberOfStages-1;s>0;s--){

                int [][]machineofJobs=new int [numberOfMachines_[i][s]][count[i]];
                //System.out.println(machineofJobs);
                for(int m = 0; m < numberOfMachines_[i][s]; m++) {
                    int n=0;
                    for(int k=0;k < count[i]; k++) {
                        machineofJobs[m][k]=-1;
                        if (jobOfwhichMachine[s][sortjobindex[s][k]] == m) {
                            machineofJobs[m][n]=sortjobindex[s][k];
                            n++;
                        }
                    }
                }

                if(s==numberOfStages-1){
                    if (numberOfMachines_[i][s] == 1){                // 如果第i个工厂的第s阶段的机器数量是1
                        starttime[sortjobindex[s][0]][s][0]=timesort[i][s][0]-timeMatrix_[jobtemp[0]][s] / machineSpeed[i][s][0];
                        for (int j = 1; j < count[i]; j++) {
                            starttime[sortjobindex[s][j]][s][0]=timesort[i][s][j-1]-timeMatrix_[jobtemp[j-1]][s] / machineSpeed[i][s][0]-timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0];
                            time[i][s][sortjobindex[s][j]]=starttime[sortjobindex[s][j]][s][0]+timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0];
                            finishtime[sortjobindex[s][j]][s][0]=time[i][s][sortjobindex[s][j]];
                            jobEndPower[i][s][jobtemp[j]]=timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][0]*machinePower[i][s][0];
                        }
                    }
                    else {
                        for (int j = 0; j < count[i]; j++) {
                            int sameMachine = jobOfwhichMachine[s][sortjobindex[s][j]];
                            int jobnext=-1;
                            for (int k = 0; k < count[i]; k++) {
                                if (machineofJobs[sameMachine][k] == sortjobindex[s][j]) {
                                    jobnext = k;
                                    if (jobnext == 0) {
                                        StartOfnextjob[sortjobindex[s][j]] = timesort[i][s][0];
                                    } else {
                                        StartOfnextjob[sortjobindex[s][j]] = starttime[machineofJobs[sameMachine][k - 1]][s][sameMachine];
                                    }
                                }
                            }
                            //int machineOfindex=jobOfwhichMachine[s][sortjobindex[s][j]];
                            starttime[sortjobindex[s][j]][s][sameMachine] = Math.min(timesort[i][s][0], StartOfnextjob[sortjobindex[s][j]]) - timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][sameMachine];
                            finishtime[sortjobindex[s][j]][s][sameMachine]=starttime[sortjobindex[s][j]][s][sameMachine]+timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][sameMachine];
                            jobEndPower[i][s][jobtemp[j]]=StartOfnextjob[sortjobindex[s][j]]- finishtime[sortjobindex[s][j]][s][sameMachine]+ timeMatrix_[jobtemp[j]][s] / machineSpeed[i][s][sameMachine]*machinePower[i][s][sameMachine];
                        }
                    }

                }
                else{//不是最后一阶段
                    int sameMachine0 = jobOfwhichMachine[s][sortjobindex[s][0]];
                    int sameMachineup = jobOfwhichMachine[s+1][sortjobindex[s][0]];
                    starttime[sortjobindex[s][0]][s][sameMachine0] = Math.max(timesort[i][s][0], starttime[sortjobindex[s][0]][s+1][sameMachineup]) - timeMatrix_[sortjobindex[s][0]][s] / machineSpeed[i][s][sameMachine0];
                    finishtime[sortjobindex[s][0]][s][sameMachine0]=starttime[sortjobindex[s][0]][s][sameMachine0]+timeMatrix_[sortjobindex[s][0]][s] / machineSpeed[i][s][sameMachine0];
                    jobEndPower[i][s][jobtemp[0]]=timeMatrix_[sortjobindex[s][0]][s] / machineSpeed[i][s][sameMachine0]*machinePower[i][s][sameMachine0];
                    for (int j = 1; j < count[i]; j++) {
                        //StartOfstageNext[sortjobindex[s+1][j]];
                        int sameMachine = jobOfwhichMachine[s][sortjobindex[s][j]];
                        int ma=jobOfwhichMachine[s+1][sortjobindex[s][j]];
                        StartOfstageNext[sortjobindex[s][j]]=starttime[sortjobindex[s][j]][s+1][ma];
                        int jobnext=-1;
                        for (int k = 0; k < count[i]; k++) {
                            if (machineofJobs[sameMachine][k] == sortjobindex[s][j]) {
                                jobnext = k;
                                if (jobnext == 0) {
                                    StartOfnextjob[sortjobindex[s][j]] = StartOfstageNext[sortjobindex[s][j]];
                                } else {
                                    StartOfnextjob[sortjobindex[s][j]] = starttime[machineofJobs[sameMachine][k - 1]][s][sameMachine];
                                }
                            }
                        }
                        //int machineOfindex=jobOfwhichMachine[s][sortjobindex[s][j]];
                        // System.out.println(timesort[i][s][0]+"+"+StartOfstageNext[sortjobindex[s][j]]);
                        double mintempt=Math.min(timesort[i][s][0],StartOfstageNext[sortjobindex[s][j]]);
                        double mintempt1= Math.min(mintempt, StartOfnextjob[sortjobindex[s][j]]);
                        //System.out.println(mintempt1);
                        starttime[sortjobindex[s][j]][s][sameMachine] = Math.min(mintempt, StartOfnextjob[sortjobindex[s][j]]) - timeMatrix_[sortjobindex[s][j]][s] / machineSpeed[i][s][sameMachine];
                        //System.out.println(starttime);
                        finishtime[sortjobindex[s][j]][s][sameMachine]=starttime[sortjobindex[s][j]][s][sameMachine]+timeMatrix_[sortjobindex[s][j]][s] / machineSpeed[i][s][sameMachine];
                        jobEndPower[i][s][jobtemp[j]]=StartOfnextjob[sortjobindex[s][j]]- finishtime[sortjobindex[s][j]][s][sameMachine]+ timeMatrix_[sortjobindex[s][j]][s] / machineSpeed[i][s][sameMachine]*machinePower[i][s][sameMachine];

                    }
                }

            }

        }



        return jobEndPower;
    }//calculate

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
//        return 0;
//    }


    public void setNumberOfFactories_(int numberOfFactories) {
        this.numberOfFactories = numberOfFactories;
    }

    public void setNumberOfStages(int numberOfStages) {
        this.numberOfStages = numberOfStages;
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

/*    public int[][] getJobFactoryCluster() {
        return jobFactoryCluster;
    }

    public void setJobFactoryCluster(int[][] jobFactoryCluster) {
        this.jobFactoryCluster = jobFactoryCluster;
    }*/
}




