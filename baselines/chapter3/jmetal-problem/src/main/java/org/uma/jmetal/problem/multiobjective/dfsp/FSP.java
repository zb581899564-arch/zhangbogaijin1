package org.uma.jmetal.problem.multiobjective.dfsp;

import org.uma.jmetal.problem.impl.AbstractIntegerPermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.List;


//  FSP.java
//
//  Author:
//       hou wenlin
//
//  Copyright (c) 2011 Antonio J. Nebro, Juan J. Durillo

//FSP1  20*5
//FSP2  20*10
//FSP3  20*20
//FSP4  50*5
//FSP5  50*10
//FSP6  50*20
//FSP7  100*5
//FSP8  100*10
//FSP9  100*20
//FSP10  200*10

//


/** Class representing problem FSP */

public class FSP extends AbstractIntegerPermutationProblem {

    protected int numberOfJobs_ = 20;
    protected int numberOfMachines_ = 5;
    protected int[][] timeMatrix_ = new int [numberOfMachines_][numberOfJobs_];

    /**
     * Creates a new instance of problem FSP.
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

    public FSP() throws IOException {
        setNumberOfVariables(numberOfJobs_);
        setNumberOfObjectives(2);
        setNumberOfFactories(1);
        setName("FSP");
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

        int[][] time = calculate(numberOfJobs_,numberOfMachines_,tem);


        f[0] = time[numberOfMachines_-1][numberOfJobs_-1];

        for (int i = 0; i < numberOfJobs_; i++) {
            f[1] += time[numberOfMachines_-1][i];
        }//for

        solution.setObjective(0, f[0]);
        solution.setObjective(1, f[1]);
    }

    //calculate the time table of squence.
    protected int[][] calculate(int jobNum, int machineNum, int tem[]){

        int[][] time = new int[machineNum][jobNum];
        time[0][0] = timeMatrix_[0][tem[0]];
        for (int i = 1; i < jobNum; i++) {
            time[0][i] = time[0][i-1] + timeMatrix_[0][tem[i]];
        }//for
        for (int i = 1; i < machineNum; i++) {
            time[i][0] = time[i-1][0] + timeMatrix_[i][tem[0]];
        }//for
        for (int i = 1; i < machineNum; i++) {
            for (int j = 1; j < jobNum; j++) {
                time[i][j] = Math.max(time[i-1][j], time[i][j-1]) + timeMatrix_[i][tem[j]];
            }
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
}
