
//  DFSP1.java
//
//  Author:
//       hou wenlin
//
//  Copyright (c) 2011 Antonio J. Nebro, Juan J. Durillo

//


/** Class representing problem FSP */


package org.uma.jmetal.problem.multiobjective.dfsp;

import org.uma.jmetal.problem.impl.AbstractIntegerPermutationProblem;
import org.uma.jmetal.solution.PermutationSolution;
import java.util.List;

public class TestFSP extends AbstractIntegerPermutationProblem {

    protected int[][] timeMatrix_ = new int[][] {
            { 74, 26, 84, 41,  3, 46, 39, 90, 62, 63, 74,  4, 37, 75, 72, 30, 43, 95, 41, 97 },
            { 70, 92, 36, 70, 37, 36, 42, 34, 29, 80, 91, 56, 71, 14, 31, 75, 80, 73, 32, 56 },
            { 84, 20, 64, 44, 69, 63, 94, 86, 66, 97, 25, 90, 12, 62, 83, 32, 12, 38, 22, 92 },
            { 63, 61, 46,  6, 83, 49, 78, 84, 97, 56, 76,  9, 38, 21, 80, 47, 24, 95, 80, 65 },
            { 72, 91, 21, 70, 12, 67, 65, 90, 47, 82, 62,  3, 84, 30, 91,  5, 11, 41, 14, 28 },
            { 78, 58, 53, 17, 36,  3, 83, 91, 73, 81, 74,  2, 31, 37, 78, 74, 51, 41, 78, 26 },
            { 33, 70, 10, 45, 70,  2, 92, 50, 54, 64, 44,  4, 99, 43, 43, 11, 60, 53, 45, 63 },
            { 87, 20, 71, 95, 71, 99, 79, 19, 41, 74,  8, 55, 87, 87, 37, 52, 36,  6, 42, 30 },
            {  3, 86,  3, 89, 57, 27, 28, 88, 48, 26, 58,  6, 33,  3, 25, 61, 93, 69, 53, 47 },
            { 28, 36, 39, 63, 66, 44, 18, 67, 17, 84,  9, 33, 80, 27, 42, 60, 96, 81, 31, 88 }
    };

    protected int numberOfJobs_ = timeMatrix_[0].length;
    protected int numberOfMachines_ = timeMatrix_.length;

    /**
     * Creates a new instance of problem FSP.
     */

    public TestFSP() {

        setNumberOfVariables(numberOfJobs_);
        setNumberOfObjectives(2);
        setName("TestFSP");

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
}
