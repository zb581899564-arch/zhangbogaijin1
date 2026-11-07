package org.uma.jmetal.differentialevolution.impl;

import org.uma.jmetal.differentialevolution.util.SO;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.Solution;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class DE4ExchangeSequence<S extends Solution<?>> {

    //选择两个个体，交换序给坏的那个个体（对每个粒子做）输入的是List<S>格式
    public List<PermutationSolution<Integer>> executeDEProcess(List<S> population, double Probability){

        List<PermutationSolution<Integer>> populationtemp = new ArrayList<>(population.size());

        for(int i=0;i<population.size();i++){

            populationtemp.add((PermutationSolution<Integer>)population.get(i));
        }

        List<PermutationSolution<Integer>> child = new ArrayList<>(populationtemp.size());

        for(int i=0;i<populationtemp.size();i++){

            int[] select =DEselect(populationtemp);
//System.out.println(select[0]+"    "+select[1]);

            if(select[0]!=select[1]){
                PermutationSolution<Integer> childtemp = (PermutationSolution<Integer>) populationtemp.get(select[1]).copy();

                ArrayList<SO> listtemp = getDifferenceOfJobSequenceVectorByExchangeSequence(populationtemp.get(select[0]), populationtemp.get(select[1]));

                Random A = new Random();
                double random1 =A.nextDouble();
                ArrayList<SO> listall = new ArrayList<SO> ((int)(listtemp.size()*random1*Probability));
                for(int j=0;j<listtemp.size()*random1*Probability;j++){
                    listall.add(listtemp.get(j));
                }
                alter(childtemp,listall);
                child.add(childtemp);
            }

        }

        return child;

    }



    //a为优秀解，b为普通解，b要向a学习
    private ArrayList<SO> getDifferenceOfJobSequenceVectorByExchangeSequence(PermutationSolution<Integer> a, PermutationSolution<Integer> b) {
        PermutationSolution<Integer> tempb = (PermutationSolution<Integer>) b.copy();

        int index;
        // 交换子
        SO s;
        // 交换序列
        ArrayList<SO> list = new ArrayList<SO>();
        Random random = new Random();
        int boundflag=random.nextInt(b.getNumberOfVariables());

        for (int i = boundflag; i < b.getNumberOfVariables(); i++) {
            if (a.getVariableValue(i) != tempb.getVariableValue(i)) {

                // 在temp中找出与a[i]相同数值的下标index
                index = findSameIndexFromJobSequence(tempb, a.getVariableValue(i));
                // 在temp中交换下标i与下标index的值
                exchangeIndex4JobSequenceVectorByExchangeSequence(tempb, i, index);
                // 记住交换子
                s = new SO(i, index);
                // 保存交换子
                list.add(s);
            }
        }

        for (int i = 0 ; i < boundflag; i++) {
            if (a.getVariableValue(i) != tempb.getVariableValue(i)) {

                // 在temp中找出与a[i]相同数值的下标index
                index = findSameIndexFromJobSequence(tempb, a.getVariableValue(i));
                // 在temp中交换下标i与下标index的值
                exchangeIndex4JobSequenceVectorByExchangeSequence(tempb, i, index);
                // 记住交换子
                s = new SO(i, index);
                // 保存交换子
                list.add(s);
            }
        }

        return list;
    }

    private int findSameIndexFromJobSequence(PermutationSolution<Integer> a, int num) {
        int index = -1;
        for (int i = 0; i < a.getNumberOfVariables(); i++) {
            if (a.getVariableValue(i) == num) {
                index = i;
                break;
            }
        }
        return index;
    }

    private void exchangeIndex4JobSequenceVectorByExchangeSequence(PermutationSolution<Integer> a, int index1, int index2) {
        int temp1 =  a.getVariableValue(index1);
        int temp2 =  a.getVariableValue(index2);

        a.setVariableValue(index1, temp2);
        a.setVariableValue(index2, temp1);

    }

    private void alter(PermutationSolution<Integer> arr, ArrayList<SO> list) {

        SO s;

        for (int i = 0; i < list.size(); i++) {
            s = list.get(i);
            exchangeIndex4JobSequenceVectorByExchangeSequence(arr, s.getX(), s.getY());
        }
    }

    //随机选择
    private <S extends Solution<?>> int[] DEselect(List<PermutationSolution<Integer>> swarm) {

        Random r = new Random(1);

        int ran1 ;
        int ran2 ;

        ran1 = r.nextInt(swarm.size()-1);
//System.out.println(ran1);

        int[] temp = new int[2];


        while(swarm.size()>1&&(ran2 = r.nextInt(swarm.size()-1))!=ran1){

            if(swarm.get(ran1).getObjective(0)<swarm.get(ran2).getObjective(0) ||
                    swarm.get(ran1).getObjective(1)<swarm.get(ran2).getObjective(1)||
                    swarm.get(ran1).getObjective(6)<swarm.get(ran2).getObjective(6)){
                temp[0] = ran1;
                temp[1] = ran2;
                break;
            }else{
                temp[0] = ran2;
                temp[1] = ran1;
                break;
            }
        }

        return temp;

    }

    private <S extends Solution<?>> List<Double> DEPDDRFFcalculate(List<S> population) {

        List<S> DEpopulation = population;

        List<Double> aa = new ArrayList<>(DEpopulation.size());
        for(int i=0;i<DEpopulation.size();i++){
            double count1 = 0;
            double count2 = 0;
            for(int j=0;j<DEpopulation.size();j++){
                if(i!=j){
                    if(DEpopulation.get(i).getObjective(0)<=DEpopulation.get(j).getObjective(0)&&
                            DEpopulation.get(i).getObjective(1)<=DEpopulation.get(j).getObjective(1)){
                        count1=count1+1;
                    }
                    if(DEpopulation.get(i).getObjective(0)>=DEpopulation.get(j).getObjective(0)&&
                            DEpopulation.get(i).getObjective(1)>=DEpopulation.get(j).getObjective(1)){
                        count2=count2+1;
                    }
                }
            }
            aa.add(count2+1/(count1+1));
        }

        return aa;

    }
}
