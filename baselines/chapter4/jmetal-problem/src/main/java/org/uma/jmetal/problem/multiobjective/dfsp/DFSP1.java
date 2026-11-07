package org.uma.jmetal.problem.multiobjective.dfsp;

import org.uma.jmetal.problem.impl.AbstractIntegerPermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

//  DFSP.java
//
//  Author:
//       hou wenlin
//
//  Copyright (c) 2011 Antonio J. Nebro, Juan J. Durillo
//DFSP的修正版本-修改编解码方式（一个向量表示粒子）
//DFSP的修正版本-修改编解码方式（一个向量表示粒子）
//DFSP的修正版本-修改编解码方式（一个向量表示粒子）

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


/** Class representing problem DFSP */

public class DFSP1 extends AbstractIntegerPermutationProblem {

    protected int numberOfJobs_ = 200;
    protected int numberOfMachines_ = 10;
    protected int factories = 3;

    protected int[][] timeMatrix_ = new int [numberOfMachines_][numberOfJobs_];
    //protected int[] factorie_capacity = new int[factories];


    /**
     * Creates a new instance of problem DFSP.
     */

    protected void init(String filename1) throws IOException {
        // 读取数据
        int count=0;
        timeMatrix_=new int[numberOfMachines_][numberOfJobs_];
        BufferedReader data1 = new BufferedReader(new InputStreamReader(new FileInputStream(filename1)));
        // 读取一行数据，数据格式:
        //number of jobs, number of machines, 	 upper bound and lower bound :
        //          20           5   873654221        1278        1232
        //processing times :
        //54 83 15 71 77 36 53 38 27 87 76 91 14 29 12 77 32 87 68 94
        String lineTxt1 = null;
        lineTxt1 = data1.readLine();
        lineTxt1 = data1.readLine();
        lineTxt1 = data1.readLine();
        while ((lineTxt1 = data1.readLine()) != null) {
            int shu=0;
            String[] strcol = lineTxt1.split(" ");
            for(int i=0;i<numberOfJobs_;i++)
                timeMatrix_[count][i]=Integer.parseInt(strcol[i+shu]);
            count ++;

        }
        data1.close();

    }

    public DFSP1() throws IOException {
        setNumberOfVariables(numberOfJobs_);
        setNumberOfObjectives(2);
        setNumberOfFactories(factories);
        setName("DFSP");
        init("F:\\桌面杂项包\\0-PSO算法研究\\备份代码\\20190827\\flow shop 数据集\\"+numberOfJobs_+"_"+numberOfMachines_+"_1.txt");

    }

    /** Evaluate() method */
    public void evaluate(PermutationSolution<Integer> solution) {

        //f[1]:Makespan.f[2]:TotalFlowTime

        List<Integer> temp = solution.getVariables();

        int [] tem = new int[temp.size()];

        for(int i=0;i<temp.size();i++){

            tem[i] = temp.get(i).intValue();

        }

        double[] f = new double[getNumberOfObjectives()];

        for(int i=0;i<getNumberOfObjectives();i++){
            f[i]=0;
        }

        int[][][] time = calculate(tem);

        //判断makespan
        int[][] temp1 = new int[factories][2];
        for(int i=0;i<factories;i++){

            for(int j=0;j<numberOfJobs_-1;j++){

                if(time[i][numberOfMachines_-1][0]==0){

                    temp1[i][0] = time[i][numberOfMachines_-1][0];
                    temp1[i][1] = 0;
                    break;

                }else
                if(time[i][numberOfMachines_-1][j]!=0 && time[i][numberOfMachines_-1][j+1]==0) {

                    temp1[i][0] = time[i][numberOfMachines_-1][j];
                    temp1[i][1] = j;
                    break;
                }
            }

        }

        int max = 0;
        for(int i=1;i<factories;i++){
            if(temp1[i][0]>temp1[max][0]) {
                max = i;
            }
        }

        f[0] = time[max][numberOfMachines_-1][temp1[max][1]];

        for(int i=0;i<factories;i++){

            for(int j=0;j<=temp1[i][1];j++){

                f[1] = f[1] + time[i][numberOfMachines_-1][j];

            }

        }

        solution.setObjective(0, f[0]);
        solution.setObjective(1, f[1]);
    }

    //加入前判断
    protected int[][][] judgeandaddintofactory(int[][][] time, int temp){

        int[][] temp1 = new int[factories][2];

        for(int i=0;i<factories;i++){

            for(int j=0;j<numberOfJobs_-1;j++){

                if(time[i][numberOfMachines_-1][0]==0){

                    temp1[i][0] = time[i][numberOfMachines_-1][0];
                    temp1[i][1] = -1;
                    break;

                }else
                    if(time[i][numberOfMachines_-1][j]!=0 && time[i][numberOfMachines_-1][j+1]==0) {

                        temp1[i][0] = time[i][numberOfMachines_-1][j];
                        temp1[i][1] = j;
                        break;
                    }
            }

        }

        int min = 0;
        for(int i=1;i<factories;i++){
            if(temp1[i][0]<temp1[min][0]) {
                min = i;
            }
        }

        //时间累加--计算完成时间
        if(temp1[min][1]==-1){
            time[min][0][temp1[min][1]+1] = timeMatrix_[0][temp];
            for(int i=1;i<numberOfMachines_;i++){
                time[min][i][temp1[min][1]+1] = time[min][i-1][temp1[min][1]+1] + timeMatrix_[i][temp];
            }
        }else {
            time[min][0][temp1[min][1]+1] = time[min][0][temp1[min][1]] + timeMatrix_[0][temp];
            for(int i=1;i<numberOfMachines_;i++){
                time[min][i][temp1[min][1]+1] = Math.max( time[min][i][temp1[min][1]], time[min][i-1][temp1[min][1]+1] ) + timeMatrix_[i][temp];
            }
        }

        return time;

    }


    //内部子程序
    protected int[][][] addintoallfactory(int[][][] time, int temp){

        int[][][] timetemp = new int[factories][numberOfMachines_][numberOfJobs_];

        for(int i=0;i<factories;i++){
            for(int j=0;j<numberOfMachines_;j++){
                for(int k=0;k<numberOfJobs_;k++){
                 timetemp[i][j][k] = time[i][j][k];
                }
            }
        }

        int[][] temp1 = new int[factories][2];

        for(int i=0;i<factories;i++){

            for(int j=0;j<numberOfJobs_-1;j++){

                if(timetemp[i][numberOfMachines_-1][0]==0){

                    temp1[i][0] = timetemp[i][numberOfMachines_-1][0];
                    temp1[i][1] = -1;
                    break;

                }else
                if(timetemp[i][numberOfMachines_-1][j]!=0 && timetemp[i][numberOfMachines_-1][j+1]==0) {

                    temp1[i][0] = timetemp[i][numberOfMachines_-1][j];
                    temp1[i][1] = j;
                    break;
                }
            }
        }

        for(int i=0;i<factories;i++){
            //时间累加--计算完成时间
            if(temp1[i][1]==-1){
                timetemp[i][0][temp1[i][1]+1] = timeMatrix_[0][temp];
                for(int j=1;j<numberOfMachines_;j++){
                    timetemp[i][j][temp1[i][1]+1] = timetemp[i][j-1][temp1[i][1]+1] + timeMatrix_[j][temp];
                }
            }else {
                timetemp[i][0][temp1[i][1]+1] = timetemp[i][0][temp1[i][1]] + timeMatrix_[0][temp];
                for(int j=1;j<numberOfMachines_;j++){
                    timetemp[i][j][temp1[i][1]+1] = Math.max( timetemp[i][j][temp1[i][1]], timetemp[i][j-1][temp1[i][1]+1] ) + timeMatrix_[j][temp];
                }
            }

        }
        return timetemp;
    }

    //加入后判断
    protected int[][][] judgeandaddintofactory1(int[][][] time, int temp){

        int[][][] timetemp = addintoallfactory(time, temp);

        int[][] temp1 = new int[factories][2];

        for(int i=0;i<factories;i++){

            for(int j=0;j<numberOfJobs_-1;j++){

                if(timetemp[i][numberOfMachines_-1][0]==0){

                    temp1[i][0] = timetemp[i][numberOfMachines_-1][0];
                    temp1[i][1] = -1;
                    break;

                }else
                if(timetemp[i][numberOfMachines_-1][j]!=0 && timetemp[i][numberOfMachines_-1][j+1]==0) {

                    temp1[i][0] = timetemp[i][numberOfMachines_-1][j];
                    temp1[i][1] = j;
                    break;
                }
            }

        }

        int min = 0;
        for(int i=1;i<factories;i++){
            if(temp1[i][0]<temp1[min][0]) {
                min = i;
            }
        }

        time[min] = timetemp[min];

        return time;

    }


    //calculate the time table of squence.
    protected int[][][] calculate(int[] tem){

        int[][][] time=new int [factories][numberOfMachines_][numberOfJobs_];//存储当前粒子的时间完成表

        for(int i=0;i<tem.length;i++){
            time = judgeandaddintofactory(time,tem[i]);
        }

        return time;

    }//calculate

    @Override
    public int getPermutationLength() {
        return numberOfJobs_;
    }

//    @Override
//    public int getNumberOfWorkers() {
//        return 0;
//    }
    /*
    public int getfactories() {
        return factories;
    }

     */
}
