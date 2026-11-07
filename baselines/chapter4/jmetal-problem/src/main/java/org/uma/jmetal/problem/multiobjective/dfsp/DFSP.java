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

public class DFSP extends AbstractIntegerPermutationProblem {

    protected int numberOfJobs_ = 200;
    protected int numberOfMachines_ = 10;
    protected int factories = 3;
    protected int numberOfObjectives = 2;

    protected int[][] timeMatrix_ = new int [numberOfMachines_][numberOfJobs_];
    protected int[] factorie_capacity = new int[factories];


    /**
     * Creates a new instance of problem DFSP.
     */

    protected void calculatefac(){
        //计算jobs除以factories的余数
        int factories_remainder = numberOfJobs_ % factories;
        int fac_count = 0;//计数用

        //计算每个工厂的jobs数量
        for(int i=0;i<factories;i++){

            if(fac_count<factories_remainder){
                factorie_capacity[i]=numberOfJobs_/factories+1;
                fac_count = fac_count+1;
            }else {
                factorie_capacity[i]=numberOfJobs_/factories;
            }
        }

    }

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

        calculatefac();
    }

    public DFSP() throws IOException {
        setNumberOfVariables(numberOfJobs_);
        setNumberOfObjectives(numberOfObjectives);
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

        ArrayList<int[][]> time = calculate(numberOfJobs_,numberOfMachines_,tem);


        f[0] = time.get(0)[numberOfMachines_-1][factorie_capacity[0]-1];

        if(f[0]<time.get(1)[numberOfMachines_-1][factorie_capacity[1]-1]){
            f[0]=time.get(1)[numberOfMachines_-1][factorie_capacity[1]-1];
        }
        if(f[0]<time.get(2)[numberOfMachines_-1][factorie_capacity[2]-1]){
            f[0]=time.get(2)[numberOfMachines_-1][factorie_capacity[2]-1];
        }


        int eva_a=0;
        int eva_b=0;
        int eva_c=0;
        for(int i=0;i<factorie_capacity[0];i++){
            eva_a=eva_a+time.get(0)[numberOfMachines_-1][i];//最后一个机器上的每个job的完工时间之和
        }
        for(int i=0;i<factorie_capacity[1];i++){
            eva_b=eva_b+time.get(1)[numberOfMachines_-1][i];//最后一个机器上的每个job的完工时间之和
        }
        for(int i=0;i<factorie_capacity[2];i++){
            eva_c=eva_c+time.get(2)[numberOfMachines_-1][i];//最后一个机器上的每个job的完工时间之和
        }


        f[1] += eva_a + eva_b + eva_c;

        solution.setObjective(0, f[0]);
        solution.setObjective(1, f[1]);
    }

    //calculate the time table of squence.
    protected ArrayList<int[][]> calculate(int jobNum, int machineNum, int[] tem){

        ArrayList<int[][]> time = new ArrayList<int[][]>(factories);
        int[][] time1=new int [machineNum][factorie_capacity[0]];//存储当前粒子的时间完成表
        int[][] time2=new int [machineNum][factorie_capacity[1]];//存储当前粒子的时间完成表
        int[][] time3=new int [machineNum][factorie_capacity[2]];//存储当前粒子的时间完成表
        //计算第一个时刻表
            time1[0][0] = timeMatrix_[0][tem[0]];
            for (int i = 1; i < factorie_capacity[0]; i++) {
                time1[0][i] = time1[0][i-1] + timeMatrix_[0][tem[i]];
            }//for
            for (int i = 1; i < machineNum; i++) {
                time1[i][0] = time1[i-1][0] + timeMatrix_[i][tem[0]];
            }//for
            for (int i = 1; i < machineNum; i++) {
                for (int j = 1; j < factorie_capacity[0]; j++) {
                    time1[i][j] = Math.max(time1[i-1][j], time1[i][j-1]) + timeMatrix_[i][tem[j]];
                }
            }

        //计算第二个时刻表
        time2[0][0] = timeMatrix_[0][tem[factorie_capacity[0]+0]];
        for (int i = 1; i < factorie_capacity[1]; i++) {
            time2[0][i] = time2[0][i-1] + timeMatrix_[0][tem[factorie_capacity[0]+i]];
        }//for
        for (int i = 1; i < machineNum; i++) {
            time2[i][0] = time2[i-1][0] + timeMatrix_[i][tem[factorie_capacity[0]+0]];
        }//for
        for (int i = 1; i < machineNum; i++) {
            for (int j = 1; j < factorie_capacity[1]; j++) {
                time2[i][j] = Math.max(time2[i-1][j], time2[i][j-1]) + timeMatrix_[i][tem[factorie_capacity[0]+j]];
            }
        }

        //计算第三个时刻表
        time3[0][0] = timeMatrix_[0][tem[factorie_capacity[0]+factorie_capacity[1]+0]];
        for (int i = 1; i < factorie_capacity[2]; i++) {
            time3[0][i] = time3[0][i-1] + timeMatrix_[0][tem[factorie_capacity[0]+factorie_capacity[1]+i]];
        }//for
        for (int i = 1; i < machineNum; i++) {
            time3[i][0] = time3[i-1][0] + timeMatrix_[i][tem[factorie_capacity[0]+factorie_capacity[1]+0]];
        }//for
        for (int i = 1; i < machineNum; i++) {
            for (int j = 1; j < factorie_capacity[2]; j++) {
                time3[i][j] = Math.max(time3[i-1][j], time3[i][j-1]) + timeMatrix_[i][tem[factorie_capacity[0]+factorie_capacity[1]+j]];
            }
        }

        time.add(time1);
        time.add(time2);
        time.add(time3);
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
