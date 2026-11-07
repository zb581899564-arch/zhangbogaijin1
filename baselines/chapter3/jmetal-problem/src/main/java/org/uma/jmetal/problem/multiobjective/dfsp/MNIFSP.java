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

//

public class MNIFSP extends AbstractIntegerPermutationProblem {

    protected int problemflag;
    protected int numberOfJobs_ ;
    protected int numberOfMachines_ ;
    protected int[][] timeMatrix_ ;
    protected int[] idleflag ;

    protected void init(String filename1) throws IOException {
        // 读取数据

        BufferedReader data1 = new BufferedReader(new InputStreamReader(new FileInputStream(filename1)));
        String lineTxt1 = null;
        lineTxt1 = data1.readLine();
        for (int i = 0; i < numberOfJobs_; i++) {
            if ((lineTxt1 = data1.readLine()) != null) {
                String[] strcol = lineTxt1.split("\t");
                for (int j = 0; j < numberOfMachines_; j++) {
                    timeMatrix_[i][j] = Integer.parseInt(strcol[j * 2 + 2]);
                }
            }
        }

        lineTxt1 = data1.readLine();
        lineTxt1 = data1.readLine();
        if ((lineTxt1 = data1.readLine()) != null) {
            String[] strcol = lineTxt1.split(" ");
            for (int j = 0; j < numberOfMachines_; j++)
                idleflag[j] = Integer.parseInt(strcol[j]);
        }

        data1.close();

        /*for (int i = 0; i < numberOfJobs_; i++) {
            for(int j=0;j<numberOfMachines_;j++)
                System.out.print(timeMatrix_[i][j]+" ");
            System.out.println();

        }

        for(int j=0;j<numberOfMachines_;j++)
            System.out.println(idleflag[j]);*/

    }

    public MNIFSP() throws IOException {
        setNumberOfVariables(numberOfJobs_);
        setNumberOfObjectives(2);
        setNumberOfFactories(1);
        setName("MNIFSP");
        init("F:\\桌面杂项包\\0-PSO算法研究\\备份代码\\20190827\\MNI-FSP数据集\\" + problemflag + "\\I_" + problemflag + "_" + numberOfJobs_ + "_" + numberOfMachines_ + "_2.txt");
    }

    public MNIFSP(int problemflag, int numberOfJobs_ ,int numberOfMachines_,int snumber) throws IOException {
        setNumberOfVariables(numberOfJobs_);
        setNumberOfObjectives(2);
        setNumberOfFactories(1);
        setName("MNIFSP");
        this.setNumberOfJobs_(numberOfJobs_);
        this.setNumberOfMachines_(numberOfMachines_);
        this.setProblemflag(problemflag);
        timeMatrix_ = new int[numberOfJobs_][numberOfMachines_];
        idleflag = new int[numberOfMachines_];
        init("E:\\WeChat Files\\wxid_aif1po3281ye22\\FileStorage\\File\\2020-12\\flow shop 数据集\\" + numberOfJobs_ + "_" + numberOfMachines_ + "_"+snumber+".txt");
    }

    /**
     * Evaluate() method
     */
    public void evaluate(PermutationSolution<Integer> solution) {

        //f[1]:Makespan.f[2]:TotalFlowTime

        List<Integer> temp = solution.getVariables();

        int[] tem = new int[temp.size()];

        for (int i = 0; i < temp.size(); i++) {

            tem[i] = temp.get(i).intValue();

        }

        double[] f = new double[getNumberOfObjectives()];

        for (int i = 0; i < getNumberOfObjectives(); i++) {
            f[i] = 0;
        }

        int[][] time = calculate(numberOfJobs_, numberOfMachines_, tem);


        f[0] = time[numberOfMachines_ - 1][numberOfJobs_ - 1];

        for (int i = 0; i < numberOfJobs_; i++) {
            f[1] += time[numberOfMachines_ - 1][i];
        }//for

        solution.setObjective(0, f[0]);
        solution.setObjective(1, f[1]);
    }

    //calculate the time table of squence of Mixed noidel.//论文里的方法
    protected int[][] calculateNoidel(int jobNum, int machineNum, int tem[]) {

        int[][] time = new int[machineNum][jobNum];
        int[][] F = new int[jobNum][machineNum - 1];

        for (int i = 0; i < machineNum - 1; i++) {
            F[0][i] = timeMatrix_[tem[0]][i];
        }

        /*for (int i = 1; i < jobNum - 1; i++) {
            F[i][0] = timeMatrix_[i][0];
        }*/

        for (int i = 1; i < jobNum; i++) {

            for (int j = 0; j < machineNum - 1; j++) {
                F[i][j] = Math.max(F[i - 1][j] - timeMatrix_[tem[i]][j], 0) + timeMatrix_[tem[i]][j + 1];
            }
        }

        for (int i = 0; i < machineNum - 1; i++) {
            time[machineNum - 1][jobNum - 1] += F[jobNum - 1][i];
        }
        for (int i = 0; i < jobNum; i++) {
            time[machineNum - 1][jobNum - 1] += timeMatrix_[tem[i]][0];
        }

        for (int i = machineNum - 2; i >= 0; i--) {
            time[i][jobNum - 1] = time[i + 1][jobNum - 1] - F[jobNum - 1][i];
        }

        for (int j = machineNum - 1; j >= 0; j--) {
            for (int i = jobNum - 2; i >= 0; i--) {
                time[j][i] = time[j][i + 1] - timeMatrix_[tem[i + 1]][j];
            }
        }

        /*int[][] temp = new int[machineNum][jobNum];

        System.out.println();
        System.out.println("论文方法：");
        System.out.println("开始时间：");
        for (int i = 0; i < machineNum; i++) {
            for (int j = 0; j < jobNum; j++) {
                temp[i][j] = time[i][j] - timeMatrix_[tem[j]][i];
                System.out.print(temp[i][j]+" ");
            }
        }
        System.out.println();
        System.out.println("持续时间：");
        for (int i = 0; i < machineNum; i++) {
            for (int j = 0; j < jobNum; j++) {
                System.out.print(timeMatrix_[tem[j]][i]+" ");
            }
        }
        System.out.println();
        System.out.println("Y轴位置：");
        for (int i = 0; i < machineNum; i++) {
            for (int j = 0; j < jobNum; j++) {
                System.out.print(i+" ");
            }
        }
        System.out.println();
        System.out.println("工序号：");
        for (int i = 0; i < machineNum; i++) {
            for (int j = 0; j < jobNum; j++) {
                System.out.print(j+" ");
            }
        }

        System.out.println();System.out.println();System.out.println();*/

        return time;
    }

    //calculate the time table of squence of Mixed noidel.//我写的方法
    protected int[][] calculate(int jobNum, int machineNum, int tem[]) {

        int[][] time = new int[machineNum][jobNum];
        //第一个作业在第一个机器上的完成时间
        time[0][0] = timeMatrix_[tem[0]][0];
        //第一个机器上的完成时间
        for (int i = 1; i < jobNum; i++) {
            time[0][i] = time[0][i - 1] + timeMatrix_[tem[i]][0];
        }//for

        for (int i = 1; i < machineNum; i++) {

            time[i][0] = time[i - 1][0] + timeMatrix_[tem[0]][i];
            for (int j = 1; j < jobNum; j++) {
                time[i][j] = Math.max(time[i - 1][j], time[i][j - 1]) + timeMatrix_[tem[j]][i];
            }

            if (idleflag[i] == 1) {

                for (int j = jobNum - 2; j >= 0; j--) {
                    time[i][j] = time[i][j + 1] - timeMatrix_[tem[j + 1]][i];
                }

            }
        }
        return time;

    }//calculate


    /*public static void main(String[] args) throws IOException {
        init("F:\\桌面杂项包\\0-PSO算法研究\\备份代码\\20190827\\MNI-FSP数据集\\7\\I_7_50_10_1.txt");
        for (int i = 0; i < numberOfJobs_; i++) {
            for(int j=0;j<numberOfMachines_;j++)
                System.out.print(timeMatrix_[i][j]+" ");
            System.out.println();

        }

        for(int j=0;j<numberOfMachines_;j++)
            System.out.println(idleflag[j]);

        int tem[] = {4, 43, 9, 48, 34, 0, 8, 49, 28, 3, 15, 44, 11, 22, 36, 39, 20, 6, 26, 14, 41, 47, 46, 32, 37, 30, 1, 45, 31, 23, 29, 5, 42, 40, 7, 27, 33, 24, 38, 21, 16, 19, 18, 25, 12, 2, 17, 13, 35, 10};

        int[][] calculate = calculate(50, 10, tem);
        int[][] calculateNoidel = calculateNoidel(50, 10, tem);
        for (int i = 0; i < calculateNoidel.length; i++) {
            for (int j = 0; j < calculate[0].length; j++) {
                System.out.print(calculate[i][j] + ",");
            }
            System.out.println();
            for (int j = 0; j < calculateNoidel[0].length; j++) {
                System.out.print(calculateNoidel[i][j] + " ");
            }
            System.out.println();
        }
        for (int i = 0; i < idleflag.length; i++) {
            System.out.println(idleflag[i]);
        }

    }*/

    @Override
    public int getPermutationLength() {
        return numberOfJobs_;
    }

//    @Override
//    public int getNumberOfWorkers() {
//        return 0;
//    }

    public int getProblemflag() {
        return problemflag;
    }

    public int[] getIdleflag() {
        return idleflag;
    }

    public void setProblemflag(int problemflag) {
        this.problemflag = problemflag;
    }

    public void setNumberOfJobs_(int numberOfJobs_) {
        this.numberOfJobs_ = numberOfJobs_;
    }

    public void setNumberOfMachines_(int numberOfMachines_) {
        this.numberOfMachines_ = numberOfMachines_;
    }
}
