package org.uma.jmetal.problem.multiobjective.dfsp;

import org.uma.jmetal.problem.impl.AbstractIntegerPermutationProblem;
import org.uma.jmetal.problem.impl.LCAbstractIntegerPermutationProblem;
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


public class DFSP3 extends AbstractIntegerPermutationProblem {

    protected int numberOfJobs_ ;
    protected int numberOfMachines_ ;
    protected int numberOfFactories ;
    protected int problemflag ;

    protected int[][] timeMatrix_;     // 时间矩阵（问题集中的内容）
    protected int[] timeArray1;      //一维时间和
    protected int[][] jobindex;

    public static int[][] jobFactoryCluster;

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
        timeMatrix_=new int[numberOfMachines_][numberOfJobs_];
        timeArray1 =new int[numberOfJobs_];

        //setJobFactoryCluster(new int[3][numberOfJobs_]);

        //timeArray1 =new int[numberOfJobs_];
        BufferedReader data1 = new BufferedReader(new InputStreamReader(new FileInputStream(filename1)));

        // 读取一行数据，数据格式:
        //number of jobs, number of machines, initial seed, upper bound and lower bound :
        //          20           5   873654221        1278        1232
        //processing times :
        //54 83 15 71 77 36 53 38 27 87 76 91 14 29 12 77 32 87 68 94       //  5行20列

        String lineTxt1 = null;
        lineTxt1 = data1.readLine();
        lineTxt1 = data1.readLine();
        lineTxt1 = data1.readLine();    //无效信息跳过3行

        while ((lineTxt1 = data1.readLine()) != null) {
            //System.out.println(lineTxt1);
            // int shu=0;
            String[] strcol = lineTxt1.split(" ");   // 分割字符串（一个数后面一个空格）
            for(int i=0;i<numberOfJobs_;i++) {
                timeMatrix_[count][i]=Integer.parseInt(strcol[i]);
            }
            count ++;

        }
        data1.close();

        //K_means_cluster();
        //////////////////////////////////////////////////
        int columnIndex = 0;
        double result = 0;
        for (columnIndex = 0; columnIndex < numberOfJobs_; columnIndex++) {
            result = sumColumn(timeMatrix_, columnIndex);
            timeArray1[columnIndex] = (int) result;
        }
/*        int [] a = timeArray1;
        System.out.print(a);*/
        //K-means聚类开始
        int [][] w = new int [2][numberOfJobs_];
        w[0]= timeArray1;
        for (int i = 0; i < w[1].length; i++) {
            w[1][i]=0;
        }

        int k = numberOfFactories;
        int[][] g;
        g = cluster(timeArray1, k);
        jobFactoryCluster = g;
        for (int i = 0; i < g.length; i++) {
            for (int j = 0; j < g[i].length; j++) {
                for (int f = 0; f < timeArray1.length; f++) {
                    if (g[i][j] == timeArray1[f] && w[1][f]==0) {
                        w[1][f]=1;
                        jobFactoryCluster[i][j] = f;
                    }
                }
                //System.out.print("\t");
            }
            //System.out.println();
        }
        System.out.print(jobFactoryCluster);
    }



/*    public void K_means_cluster() throws IOException {
        // 读取数据
        int count=0;
        timeMatrix_=new int[numberOfMachines_][numberOfJobs_];
        timeArray1 =new int[numberOfJobs_];
 *//*       BufferedReader data1 = new BufferedReader(new InputStreamReader(new FileInputStream(filename1)));

        // 读取一行数据，数据格式:
        //number of jobs, number of machines, initial seed, upper bound and lower bound :
        //          20           5   873654221        1278        1232
        //processing times :
        //54 83 15 71 77 36 53 38 27 87 76 91 14 29 12 77 32 87 68 94       //  5行20列

        String lineTxt1 = null;
        lineTxt1 = data1.readLine();
        lineTxt1 = data1.readLine();
        lineTxt1 = data1.readLine();    //无效信息跳过3行

        while ((lineTxt1 = data1.readLine()) != null) {
            //System.out.println(lineTxt1);
            // int shu=0;
            String[] strcol = lineTxt1.split(" ");   // 分割字符串（一个数后面一个空格）
            for(int i=0;i<numberOfJobs_;i++) {
                timeMatrix_[count][i]=Integer.parseInt(strcol[i]);
            }
            count ++;

        }
        data1.close();*//*


        //计算时间矩阵各项列的和（计算每个工件在所有机器上花费的时间和）
        int columnIndex = 0;
        double result = 0;
        for (columnIndex = 0; columnIndex < numberOfJobs_; columnIndex++) {
            result = sumColumn(timeMatrix_, columnIndex);
            timeArray1[columnIndex] = (int) result;
        }

        //K-means聚类开始
        int k = numberOfFactories;
        int[][] g;
        g = cluster(timeArray1, k);
        //int[][] index = new int[500][500];
        for (int i = 0; i < g.length; i++) {
            for (int j = 0; j < g[i].length; j++) {
                for (int f = 0; f < timeArray1.length; f++) {
                    if (g[i][j] == timeArray1[f]) {
                        getJobFactoryCluster()[i][j] = f;
                        //System.out.print(index[i][j]+"   ");
                }


                }
            }
        }

    }*/



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
    public DFSP3(int numberOfJobs ,int numberOfMachines,int problemId) throws IOException {

        setNumberOfVariables(numberOfJobs);
        setNumberOfObjectives(2);   //TODO 2个目标
        setNumberOfFactories(3);    //TODO 无参数的 写死了，3个factory

        setName("DFSP3");
        this.setNumberOfJobs_(numberOfJobs);
        this.setNumberOfMachines_(numberOfMachines);

        //this.setProblemflag(problemflag);
        timeMatrix_ = new int[numberOfJobs][numberOfMachines];
        //idleflag = new int[numberOfMachines_];

        StringBuffer sbInputFileName = new StringBuffer();
        String strFolderName = new String("F:\\侯文林数据包\\问题集\\flow shop 数据集\\"); //TODO 修改输入数据目录
        //init("C:\\LocalDisk\\0.research\\journal-proposal-ZhangLiHouYangGen-PSO-DE-DFSP\\data-FSP\\" + numberOfJobs_ + "_" + numberOfMachines_ + "_"+snumber+".txt");
        sbInputFileName.append(strFolderName);
        sbInputFileName.append(numberOfJobs).append("_");
        sbInputFileName.append(numberOfMachines);
        sbInputFileName.append("_").append(problemId);
        sbInputFileName.append(".txt");
        init(sbInputFileName.toString());
    }

/*    private void setProblemflag(int problemflag) {
        this.problemflag= problemflag;
    }   */   // 带flag的暂时没用

    private void setNumberOfMachines_(int numberOfMachines_) {
        this.numberOfMachines_ = numberOfMachines_;
    }


    public DFSP3() throws IOException {
        setNumberOfVariables(numberOfJobs_);
        setNumberOfFactories(3);
        setNumberOfObjectives(2);
        setName("DFSP");

        StringBuffer sbInputFileName = new StringBuffer();
        String strFolderName = new String("F:\\侯文林数据包\\问题集\\flow shop 数据集\\");//TODO 修改输入数据目录
        //init("C:\\LocalDisk\\0.research\\journal-proposal-ZhangLiHouYangGen-PSO-DE-DFSP\\data-FSP\\" + numberOfJobs_ + "_" + numberOfMachines_ + "_"+snumber+".txt");
        sbInputFileName.append(strFolderName).append(numberOfJobs_).append("_").append(numberOfMachines_).append("_").append("1").append(".txt");


        //init("C:\\LocalDisk\\0.research\\journal-proposal-ZhangLiHouYangGen-PSO-DE-DFSP\\data-FSP\\"+numberOfJobs_+"_"+numberOfMachines_+"_1.txt");
        init(sbInputFileName.toString());
    }    //没用到这个

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
        System.out.print(tem);

        double[] f = new double[getNumberOfObjectives()];

        for(int i=0;i<getNumberOfObjectives();i++){
            f[i]=0;
        }

        int[][][] time = calculate(tem);
        System.out.println(time);

        //记录所有工厂的makespan
        int[][] temp1 = new int[numberOfFactories][2];//temp1[i][0]记录的是makespan；temp1[i][1]记录的是当前工厂最后一个job的位置
        for(int i=0;i<numberOfFactories;i++){

            for(int j=0;j<numberOfJobs_-1;j++){


                if(time[i][numberOfMachines_-1][0]==0){//相当于是判断工厂里面第0位是否是最后一位

                    temp1[i][0] = time[i][numberOfMachines_-1][0];  //记录makespan
                    temp1[i][1] = 0;   //记录工厂里面的job数：0
                    break;

                }else
                if(time[i][numberOfMachines_-1][j]!=0 && time[i][numberOfMachines_-1][j+1]==0) {//相当于是判断工厂里面第j位是否是最后一位

                    temp1[i][0] = time[i][numberOfMachines_-1][j];
                    temp1[i][1] = j;
                    break;
                }
            }

        }

        //判断makespan的最大值
        int max = 0;
        for(int i=1;i<numberOfFactories;i++){
            if(temp1[i][0]>temp1[max][0]) {
                max = i;
            }
        }

        //目标一的值
        f[0] = time[max][numberOfMachines_-1][temp1[max][1]];
        //f[1] = time[max][numberOfMachines_-1][temp1[max][1]];      //  假设只有一个目标，让两个目标值相等


        //计算所有工厂的最大流
        double[] ftemp= new double[numberOfFactories];
        for(int i=0;i<numberOfFactories;i++){

            for(int j=0;j<=temp1[i][1];j++){
                ftemp[i] += time[i][numberOfMachines_-1][j];
                // f[1] = f[1] + time[i][numberOfMachines_-1][j];
            }
        }
        //判断那个工厂的最大流最大
        double maxflowtime=ftemp[0];
            for (int i = 1; i < ftemp.length; i++) {
                if (ftemp[i] >maxflowtime) {
                    maxflowtime=ftemp[i];
                }
            }
                f[1] = maxflowtime;

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
    }

    //calculate the time table of sequence.    计算序列的时间表
    /*
     int [][] tem = new int[2][temp.size()];

        for(int i=0;i<temp.size();i++){
            tem[0][i] = temp.get(i).intValue();
            tem[1][i] = tempid.get(i).intValue();
        }
     */

    protected int[][][] calculate(int[][] solution) throws ArrayIndexOutOfBoundsException{


        for(int i=0;i<solution[0].length;i++){
            //System.out.print("\t="+solution[0][i]);
        }
        //System.out.println();
        for(int i=0;i<solution[1].length;i++){
            //System.out.print("\t="+solution[1][i]);
        }
        //System.out.println();


        int[][][] time = new int [numberOfFactories][numberOfMachines_][numberOfJobs_];  //存储当前粒子的时间完成表
        int[][] timefactories = new int[numberOfFactories][numberOfJobs_];  // 三个一维向量  一维向量的空间大小是所有工件的数量大小

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
        //System.out.println("每个工厂的Job顺序：");
        for(int i=0;i<numberOfFactories;i++) {
            for (int j = 0; j < numberOfJobs_; j++) {
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
        for(int i=0;i<numberOfFactories;i++){
            //System.out.println("工厂："+i);
            int jobIndex=timefactories[i][0];
            //System.out.print(jobIndex);
            // 工厂 机器 工件
            if (jobIndex == -1){
                //System.out.println("-------------------------ERROR: -1");
            }
            else
            {
                //得到第一个机器上的第一个job的加工时间
                time[i][0][0] = timeMatrix_[0][jobIndex];

                //计算第一个机器上的Job的完成时间，因为没有空闲，所以直接累加
                int timeEnd=0;
                for(int j=1;j<count[i];j++) {
                    jobIndex =timefactories[i][j];
                    //System.out.print(">"+jobIndex);
                    time[i][0][j] = time[i][0][j - 1] + timeMatrix_[0][jobIndex];
                    timeEnd =time[i][0][j];
                    //System.out.println("Time: "+time[i][0][j]);
                }
                //System.out.println(" Time: "+timeEnd);

                //第二个机器上及其以后机器上的第一个job的加工时间
                for(int j=1;j<numberOfMachines_;j++) {
                    jobIndex=timefactories[i][0];
                    //System.out.print("<"+jobIndex);
                    time[i][j][0] = time[i][j-1][0] + timeMatrix_[j][jobIndex];
                    timeEnd =time[i][j][0];
                }
                //System.out.println(" Time: "+timeEnd);

                for (int k = 1; k < numberOfMachines_; k++) {
                    for (int m = 1; m < count[i]; m++) {
                        jobIndex = timefactories[i][m];
                        //System.out.print("~"+jobIndex);
                        time[i][k][m] = Math.max(time[i][k-1][m], time[i][k][m-1]) + timeMatrix_[k][jobIndex];
                        timeEnd =time[i][k][m] ;
                    }
                    //System.out.println();
                }
                //System.out.println(" Time: "+timeEnd);
            }
        }

        return time;

    }//calculate

    @Override
    public int getPermutationLength() {
        return numberOfJobs_;
    }

    public void setNumberOfJobs_(int numberOfJobs_) {
        this.numberOfJobs_ = numberOfJobs_;
    }

    public int getNumberOfMachines_() {
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

    @Override
    public void setNumberOfFactories(int numberOfFactories) {
        this.numberOfFactories = numberOfFactories;
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




