package org.uma.jmetal.algorithm.multiobjective.mymohea.util;

import org.apache.commons.lang3.tuple.Pair;
import org.apache.commons.math3.genetics.Population;
import org.uma.jmetal.operator.SelectionOperator;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.SolutionListUtils;
import org.uma.jmetal.util.comparator.StrengthFitnessComparator;
import org.uma.jmetal.util.solutionattribute.impl.LocationAttribute;
import org.uma.jmetal.util.solutionattribute.impl.StrengthRawFitness;

import java.util.*;

/**
 * @author Juanjo Durillo
 * @param <S>
 */
@SuppressWarnings("serial")
public class PDDRFFSelection<S extends Solution<?>> implements SelectionOperator<List<S>,List<S>> {

    private int solutionsToSelect ;
    private StrengthRawFitness<S> strengthRawFitness ;

    public PDDRFFSelection(int solutionsToSelect) {
        this(solutionsToSelect, 1) ;
    }

    public PDDRFFSelection(int solutionsToSelect, int k) {
        this.solutionsToSelect = solutionsToSelect ;
        this.strengthRawFitness = new StrengthRawFitness<>(k) ;
    }

    @Override
    public List<S> execute(List<S> s) {
        return null;
    }

    public List<S> execute(List<S> population, int numberofarchive){
        List<S> archivetemp = new ArrayList<>(numberofarchive);
        List<S> populationtemp = new ArrayList<>(population.size());
        populationtemp.addAll(population);
        populationtemp = PDDRFF_Ascending_order(populationtemp);

        for(int i=0;i<numberofarchive;i++){
            archivetemp.add(populationtemp.get(i));
        }
        return archivetemp;
    }

    protected List<S> PDDRFF_Ascending_order(List<S> population){
        List<S> populationtemp = new ArrayList<>(population.size());
        List<S> Orderpopulation = new ArrayList<>(population.size());

        populationtemp.addAll(population);
        double[][] fitnesstemp = new double[population.size()][2];

        for(int i=0;i<population.size();i++){
            fitnesstemp[i][0] = i;
            fitnesstemp[i][1] = Calculated_PDDRFF(population.get(i),population);
        }

        for(int i=0;i<population.size();i++){    //冒泡排序 对fitness序列排序
            double[] temp = new double[2];
            temp[0] = 0;
            temp[1] = 0;
            for(int j=i+1;j<population.size();j++){
                if(fitnesstemp[j][1] < fitnesstemp[i][1]){
                    temp[0] = fitnesstemp[i][0];  //交换内容
                    temp[1] = fitnesstemp[i][1];  //交换内容

                    fitnesstemp[i][0] = fitnesstemp[j][0];
                    fitnesstemp[i][1] = fitnesstemp[j][1];

                    fitnesstemp[j][0] = temp[0];
                    fitnesstemp[j][1] = temp[1];
                }
            }
        }

        for(int i=0;i<population.size();i++){  //按照最小值下标序列覆盖
            Orderpopulation.add(population.get((int) fitnesstemp[i][0]));
        }
        return Orderpopulation;
    }


    protected double Calculated_PDDRFF(S individual, List<S> population){
       // population = evaluatePopulation(population);
        double eval = 0; //初始化为0
        double DominateTime = 0;     //个体支配他人的数目
        double BedominatedTime = 0;  // 个体被他人支配数目
        for(int i=0;i<population.size();i++){
            if(A_dominant_B(individual,population.get(i))){
                DominateTime = DominateTime + 1;
            }
            if(A_dominant_B(population.get(i),individual)){
                BedominatedTime = BedominatedTime + 1;
            }
        }
        eval = BedominatedTime + (1/(DominateTime+1));
        return eval;
    }

    protected boolean A_dominant_B(S individualA, S individualB){

        double fitnessA[]=new double[2];  //第一组适应度函数  用于对比
        double fitnessB[]=new double[2];  //第二组适应度函数  用于对比
        fitnessA = individualA.getObjectives();
        fitnessB = individualB.getObjectives();
        if(fitnessA[0]<fitnessB[0] && fitnessA[1]<fitnessB[1]){
            return true;
        }
        else if(fitnessA[0]<fitnessB[0] && fitnessA[1]==fitnessB[1]){
            return true;
        }
        else if(fitnessA[0]==fitnessB[0] && fitnessA[1]<fitnessB[1]){
            return true;
        }
        else{
            return false;
        }
    }


}
