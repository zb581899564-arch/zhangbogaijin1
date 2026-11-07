package org.uma.jmetal.differentialevolution.impl;

import org.uma.jmetal.differentialevolution.util.SO;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.Solution;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class DEexecute1<S extends Solution<?>> {

    //选择两个个体，交换序给坏的那个个体
    public List<S> DEexe(List<PermutationSolution<Integer>> population, double Probability){

        List<PermutationSolution<Integer>> populationtemp = new ArrayList<>(population.size());

        for(int i=0;i<population.size();i++){

            populationtemp.add(population.get(i));
        }

        List<Double> PDDRFFF = DEPDDRFFcalculate(populationtemp);
        List<S> child = new ArrayList<>();

        PermutationSolution<Integer> childtemp = null;
        for(int i=0;i<populationtemp.size()/3;i++){

            int[] select =DEselect(populationtemp, PDDRFFF,1);

            childtemp = (PermutationSolution<Integer>) populationtemp.get(select[1]).copy();

            ArrayList<SO> listtemp = minus(populationtemp.get(select[0]), populationtemp.get(select[1]));

            Random A = new Random();
            double random1 =A.nextDouble();
            ArrayList<SO> listall = new ArrayList<SO> ((int)(listtemp.size()*random1*Probability));
            for(int j=0;j<listtemp.size()*random1*Probability;j++){
                listall.add(listtemp.get(j));
            }
            alter(childtemp,listall);
        }
        child.add((S) childtemp);
        for(int i=0;i<populationtemp.size()/3;i++){

            int[] select =DEselect(populationtemp, PDDRFFF,2);
            childtemp = (PermutationSolution<Integer>) populationtemp.get(select[1]).copy();

            ArrayList<SO> listtemp = minus(populationtemp.get(select[0]), populationtemp.get(select[1]));

            Random A = new Random();
            double random1 =A.nextDouble();
            ArrayList<SO> listall = new ArrayList<SO> ((int)(listtemp.size()*random1*Probability));
            for(int j=0;j<listtemp.size()*random1*Probability;j++){
                listall.add(listtemp.get(j));
            }
            alter(childtemp,listall);
        }
        child.add((S) childtemp);
        for(int i=0;i<populationtemp.size()/3;i++){

            int[] select =DEselect(populationtemp, PDDRFFF,3);
            childtemp = (PermutationSolution<Integer>) populationtemp.get(select[1]).copy();

            ArrayList<SO> listtemp = minus(populationtemp.get(select[0]), populationtemp.get(select[1]));

            Random A = new Random();
            double random1 =A.nextDouble();
            ArrayList<SO> listall = new ArrayList<SO> ((int)(listtemp.size()*random1*Probability));
            for(int j=0;j<listtemp.size()*random1*Probability;j++){
                listall.add(listtemp.get(j));
            }
            alter(childtemp,listall);
        }
        child.add((S) childtemp);

        return child;

    }

    private ArrayList<SO> minus(PermutationSolution<Integer> a, PermutationSolution<Integer> b) {
        PermutationSolution<Integer> tempb = (PermutationSolution<Integer>) b.copy();

        int index;
        // 交换子
        SO s;
        // 交换序列
        ArrayList<SO> list = new ArrayList<SO>();
        Random random = new Random();

        for (int i = random.nextInt(b.getNumberOfVariables()); i < b.getNumberOfVariables(); i++) {
            if (a.getVariableValue(i) != tempb.getVariableValue(i)) {

                // 在temp中找出与a[i]相同数值的下标index
                index = findNum(tempb, a.getVariableValue(i));
                // 在temp中交换下标i与下标index的值
                changeIndex(tempb, i, index);
                // 记住交换子
                s = new SO(i, index);
                // 保存交换子
                list.add(s);
            }
        }

        for (int i = 0 ; i < random.nextInt(b.getNumberOfVariables()); i++) {
            if (a.getVariableValue(i) != tempb.getVariableValue(i)) {

                // 在temp中找出与a[i]相同数值的下标index
                index = findNum(tempb, a.getVariableValue(i));
                // 在temp中交换下标i与下标index的值
                changeIndex(tempb, i, index);
                // 记住交换子
                s = new SO(i, index);
                // 保存交换子
                list.add(s);
            }
        }

        return list;
    }

    private int findNum(PermutationSolution<Integer> a, int num) {
        int index = -1;
        for (int i = 0; i < a.getNumberOfVariables(); i++) {
            if (a.getVariableValue(i) == num) {
                index = i;
                break;
            }
        }
        return index;
    }

    private void changeIndex(PermutationSolution<Integer> a, int index1, int index2) {
        int temp1 =  a.getVariableValue(index1);
        int temp2 =  a.getVariableValue(index2);

        a.setVariableValue(index1, temp2);
        a.setVariableValue(index2, temp1);

    }

    private void alter(PermutationSolution<Integer> arr, ArrayList<SO> list) {

        SO s;

        for (int i = 0; i < list.size(); i++) {
            s = list.get(i);
            changeIndex(arr, s.getX(), s.getY());
        }
    }

    //随机选择[1,2,3种]
    //1、适应度1的方向
    //2、适应度2的方向
    //3、PDDR-FF好的方向
    private <S extends Solution<?>> int[] DEselect(List<S> population, List<Double> PDDRFFF, int methodflag) {

        int[] temp = new int[2];

        if(methodflag==1){

            Random r = new Random(1);
            int ran1 ;
            int ran2 ;

            ran1 = r.nextInt(population.size()-1);
            do {
                ran2 = r.nextInt(population.size()-1);
            } while( ran2==ran1);

            if(population.get(ran1).getObjective(0)>=population.get(ran2).getObjective(0)){

                temp[0]=ran2;
                temp[1]=ran1;

            }else{
                temp[0]=ran1;
                temp[1]=ran2;
            }

        }else if(methodflag==2){

            Random r = new Random(1);
            int ran1 ;
            int ran2 ;

            ran1 = r.nextInt(population.size()-1);
            do {
                ran2 = r.nextInt(population.size()-1);
            } while( ran2==ran1);

            if(population.get(ran1).getObjective(1)>=population.get(ran2).getObjective(1)){

                temp[0]=ran2;
                temp[1]=ran1;

            }else{
                temp[0]=ran1;
                temp[1]=ran2;
            }

        }else if(methodflag==3){

            //List<Double> PDDRFFF = DEPDDRFFcalculate(population);
            Random r = new Random(1);
            int ran1 ;
            int ran2 ;

            ran1 = r.nextInt(PDDRFFF.size()-1);
            do {
                ran2 = r.nextInt(PDDRFFF.size()-1);
            } while( ran2==ran1);

            if(PDDRFFF.get(ran2)<=PDDRFFF.get(ran1)){

                temp[0]=ran2;
                temp[1]=ran1;

            }else{
                temp[0]=ran1;
                temp[1]=ran2;
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
                    if(DEpopulation.get(i).getObjective(0)<=DEpopulation.get(j).getObjective(0)&&DEpopulation.get(i).getObjective(1)<=DEpopulation.get(j).getObjective(1)){
                        count1=count1+1;
                    }
                    if(DEpopulation.get(i).getObjective(0)>=DEpopulation.get(j).getObjective(0)&&DEpopulation.get(i).getObjective(1)>=DEpopulation.get(j).getObjective(1)){
                        count2=count2+1;
                    }
                }
            }
            aa.add(count2+1/(count1+1));
        }

        return aa;

    }



}
