package org.uma.jmetal.problem.multiobjective.dfsp;

//正常的问题输入class，可以输入多种多样的问题，只需要修改jobs,machines的相关参数。
import org.uma.jmetal.problem.impl.AbstractIntegerPermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.List;

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


/** Class representing problem DFSP */

public class DFSP2 extends AbstractIntegerPermutationProblem {

    protected int numberOfJobs_ = 50;
    protected int numberOfMachines_ = 10;
    protected int numberOfFactories = 3;

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

    public DFSP2() throws IOException {
        setNumberOfVariables(numberOfJobs_);
        setNumberOfFactories(numberOfFactories);
        setNumberOfObjectives(2);
        setName("DFSP");
        init("E:\\WeChat Files\\wxid_aif1po3281ye22\\FileStorage\\File\\2020-12\\flow shop 数据集\\"+numberOfJobs_+"_"+numberOfMachines_+"_1.txt");

    }

    public DFSP2(int a,int b) throws IOException {
        setNumberOfVariables(a);
        setNumberOfFactories(b);
        setNumberOfObjectives(2);
        setName("DFSP");
        init("E:\\WeChat Files\\wxid_aif1po3281ye22\\FileStorage\\File\\2020-12\\flow shop 数据集\\"+numberOfJobs_+"_"+numberOfMachines_+"_1.txt");

    }

    /** Evaluate() method */
    public void evaluate(PermutationSolution<Integer> solution) {

        //f[1]:Makespan.f[2]:TotalFlowTime

        List<Integer> temp = solution.getVariables();
        List<Integer> tempid = solution.getVariablesid();

        int [][] tem = new int[2][temp.size()];

        for(int i=0;i<temp.size();i++){

            tem[0][i] = temp.get(i).intValue();
            tem[1][i] = tempid.get(i).intValue();

        }

        double[] f = new double[getNumberOfObjectives()];

        for(int i=0;i<getNumberOfObjectives();i++){
            f[i]=0;
        }

        int[][][] time = calculate(tem);



        //判断makespan
        int[][] temp1 = new int[numberOfFactories][2];
        for(int i=0;i<numberOfFactories;i++){

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
        for(int i=1;i<numberOfFactories;i++){
            if(temp1[i][0]>temp1[max][0]) {
                max = i;
            }
        }

        f[0] = time[max][numberOfMachines_-1][temp1[max][1]];

        for(int i=0;i<numberOfFactories;i++){

            for(int j=0;j<=temp1[i][1];j++){

                f[1] = f[1] + time[i][numberOfMachines_-1][j];

            }

        }

        solution.setObjective(0, f[0]);
        solution.setObjective(1, f[1]);
    }

    //calculate the time table of squence.
    protected int[][][] calculate(int[][] tem){

        int[][][] time=new int [numberOfFactories][numberOfMachines_][numberOfJobs_];//存储当前粒子的时间完成表
        int[][] timefactories = new int[numberOfFactories][numberOfJobs_];

        for(int i=0;i<timefactories.length;i++){
            for(int j=0;j<timefactories[i].length;j++){
                timefactories[i][j] = -1;
            }
        }

        int [] count = new int[numberOfFactories];
        for(int i=0;i<tem[1].length;i++){
            count[tem[1][i]] = count[tem[1][i]]+1;

            for(int j=0;j<tem[0].length;j++){
                if(timefactories[tem[1][i]][j]==-1){
                    timefactories[tem[1][i]][j] = tem[0][i];
                    break;
                }
            }
        }

        for(int i=0;i<numberOfFactories;i++){

            time[i][0][0] = timeMatrix_[0][timefactories[i][0]];
            for(int j=1;j<count[i];j++) {
                time[i][0][j] = time[i][0][j - 1] + timeMatrix_[0][timefactories[i][j]];
            }

            for(int j=1;j<numberOfMachines_;j++) {
                time[i][j][0] = time[i][j-1][0] + timeMatrix_[j][timefactories[i][0]];
            }


            for (int k = 1; k < numberOfMachines_; k++) {
                for (int m = 1; m < count[i]; m++) {
                    time[i][k][m] = Math.max(time[i][k-1][m], time[i][k][m-1]) + timeMatrix_[k][timefactories[i][m]];
                }
            }

        }

        return time;

    }//calculate

    @Override
    public int getPermutationLength() {
        return numberOfJobs_;
    }
    /*
    public int getfactories() {
        return factories;
    }

     */
}
