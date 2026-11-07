package org.uma.jmetal.qualityindicator.myqualityindicator.impl;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;

public class Indexs {

    private float GD;
    private float IGD;
    private float HV;
    private float Spacing;
    private float Spread;

    private float varianceGD;
    private float varianceIGD;
    private float varianceHV;
    private float varianceSpacing;
    private float varianceSpread;

    private float[] GDs;
    private float[] IGDs;
    private float[] HVs;
    private float[] Spacings;
    private float[] Spreads;

    public  Indexs(float[] maxvalue,ArrayList<Float[]> Reference,float[][][] Experimental_data) {

//todo 这里的数组大小和运行次数有关
        GDs =        new float[20];
        IGDs =       new float[20];
        HVs =        new float[20];
        Spacings =   new float[20];
        Spreads =    new float[20];

        this.GD = Get_GD(maxvalue, Reference, Experimental_data);
        this.IGD = Get_IGD(maxvalue, Reference, Experimental_data);
        this.HV = Get_HV(maxvalue, Reference, Experimental_data);
        this.Spacing = Get_Spacing(maxvalue, Reference, Experimental_data);
        this.Spread = Get_Spread(maxvalue, Reference, Experimental_data);
    }

    //GD指标//越小越好
    public float Get_GD(float[] maxvalue, ArrayList<Float[]> Reference, float[][][] Experimental_data) {

        float[] Generational_Distance = new float[Experimental_data.length];

        for(int i=0;i<Experimental_data.length;i++){
            if(Experimental_data[i][0][0] == -1){
                break;
            }
            else{
                int effectivelineNum = 0;   //记录该结果中的有效个体数目
                float tempSum = 0;
                for(int j=0;j<Experimental_data[i].length;j++){
                    if(Experimental_data[i][j][0] == -1){
                        break;
                    }
                    else{
                        effectivelineNum = effectivelineNum + 1;
                        float temp_value0;
                        float temp_value1;
                        float temp_value2;
                        float temp_value;
                        temp_value0 = Experimental_data[i][j][0] - Reference.get(0)[0];
                        temp_value1 = Experimental_data[i][j][1] - Reference.get(0)[1];
                        temp_value2 = Experimental_data[i][j][2] - Reference.get(0)[2];
                        temp_value0 = temp_value0 / maxvalue[0];
                        temp_value1 = temp_value1 / maxvalue[1];
                        temp_value2 = temp_value2 / maxvalue[2];
                        temp_value = (float) Math.sqrt((temp_value0 * temp_value0) + (temp_value1 * temp_value1)+ (temp_value2 * temp_value2));
                        float Mix_value = temp_value;
                        for(int k=0;k<Reference.size();k++){
                            temp_value0 = Experimental_data[i][j][0] - Reference.get(k)[0];
                            temp_value1 = Experimental_data[i][j][1] - Reference.get(k)[1];
                            temp_value2 = Experimental_data[i][j][2] - Reference.get(k)[2];
                            temp_value0 = temp_value0 / maxvalue[0];
                            temp_value1 = temp_value1 / maxvalue[1];
                            temp_value2 = temp_value2 / maxvalue[2];
                            temp_value = (float) Math.sqrt((temp_value0 * temp_value0) + (temp_value1 * temp_value1)+ (temp_value2 * temp_value2));
                            if(temp_value < Mix_value){
                                Mix_value = temp_value;
                            }
                        }
                        tempSum = tempSum + Mix_value;
                    }
                }
                Generational_Distance[i] = tempSum / effectivelineNum;
                GDs[i] = Generational_Distance[i];

            }
        }

//        System.out.println(Arrays.toString(Generational_Distance));
//        System.out.println(Generational_Distance.length);
//        try {
//            Thread.sleep(99999);
//        } catch (InterruptedException e) {
//            throw new RuntimeException(e);
//        }

        /*BufferedWriter indicatordataw = new BufferedWriter(new FileWriter(filename+"\\指标数据\\指标结果\\"+problem+"-GD-"+algorithm+".txt"));
        for(int i=0;i<num;i++){
            indicatordataw.write("Generational_Distance["+i+"]        " + Generational_Distance[i]);
            indicatordataw.newLine();
        }
        float average=0;
        for(int i=0;i<num;i++)
            average=average+Generational_Distance[i];
        average=average/num;
        indicatordataw.write("average:        " + average);
        indicatordataw.newLine();
        indicatordataw.close();*/

        float average=0;
        for(int i=0;i<Experimental_data.length;i++)
            average=average+Generational_Distance[i];
        average=average/Experimental_data.length;

        for (int i = 0; i < Experimental_data.length; i++) {
            varianceGD += Math.pow((GDs[i]-average),2);
        }
        varianceGD = varianceGD/Experimental_data.length;
        //Math.sqrt(varianceGD);

        return average;
    }

    //计算HV指标//越大越好
    public float Get_HV(float[] maxvalue, ArrayList<Float[]> Reference, float[][][] Experimental_data) {
        float HV[]=new float[Experimental_data.length];

        for(int i=0;i<Experimental_data.length;i++){
            if(Experimental_data[i][0][0] == -1){
                break;
            }
            else {
                int effectivelineNum = 0;   //记录该结果中的有效个体数目
                //计有效数
                for (int j = 0; j < Experimental_data[i].length; j++) {
                    if (Experimental_data[i][j][0] == -1) {
                        break;
                    } else {
                        effectivelineNum = effectivelineNum + 1;
                    }
                }

                // 把有效个体抽出来
                float[][] temp_Experimental_data = new float[effectivelineNum][2];
                for (int j = 0; j < effectivelineNum; j++) {
                    temp_Experimental_data[j] = Experimental_data[i][j];
                }

                float temp1[][]=Fitness_Ascending_order(temp_Experimental_data);
                float sum=0;
//                sum=(maxvalue[0]-temp1[0][0])/maxvalue[0]*(maxvalue[1]-temp1[0][1])/maxvalue[1];
                sum=(maxvalue[0]-temp1[0][0])/maxvalue[0]*(maxvalue[1]-temp1[0][1])/maxvalue[1]*(maxvalue[2]-temp1[0][2])/maxvalue[2];
                for(int j=1;j<temp1.length;j++){
                    sum=sum+(maxvalue[0]-temp1[j][0])/maxvalue[0]*(temp1[j-1][1]-temp1[j][1])/maxvalue[1]*(maxvalue[2]-temp1[j][2])/maxvalue[2];
                }


                HV[i]=sum;
                HVs[i] = HV[i];

            }
        }

        /*BufferedWriter indicatordataw = new BufferedWriter(new FileWriter(filename+"\\指标数据\\指标结果\\"+problem+"-HV-"+algorithm+".txt"));
        for(int i=0;i<num;i++){
            indicatordataw.write("HV["+i+"]        "+HV[i]);
            indicatordataw.newLine();
        }
        float average=0;
        for(int i=0;i<num;i++)
            average=average+HV[i];
        average=average/num;
        indicatordataw.write("average:        " + average);
        indicatordataw.newLine();
        indicatordataw.close();*/

        float average=0;
        for(int i=0;i<Experimental_data.length;i++)
            average=average+HV[i];
        average=average/Experimental_data.length;

        for (int i = 0; i < Experimental_data.length; i++) {
            varianceHV += Math.pow((HVs[i]-average),2);
        }
        varianceHV = varianceHV/Experimental_data.length;

        return average;

    }

    //IGD指标//越小越好
    public float Get_IGD(float[] maxvalue, ArrayList<Float[]> Reference, float[][][] Experimental_data) {


        float[] Inverted_Generational_Distance = new float[Experimental_data.length];

        for(int i=0;i<Experimental_data.length;i++){
            if(Experimental_data[i][0][0] == -1){
                break;
            }
            else{
                int effectivelineNum = 0;   //记录该结果中的有效个体数目
                //计有效数
                for(int j=0;j<Experimental_data[i].length;j++){
                    if(Experimental_data[i][j][0] == -1){
                        break;
                    }
                    else{
                        effectivelineNum = effectivelineNum + 1;
                    }
                }

                // 把有效个体抽出来
                float[][] temp_Experimental_data = new float[effectivelineNum][2];
                for(int j=0;j<effectivelineNum;j++){
                    temp_Experimental_data[j] = Experimental_data[i][j];
                }

                //计算参考平面上的点   到 输入的实验数据点的最短距离
                float temp_value0;
                float temp_value1;
                float temp_value2;
                float temp_value;
                float tempSum = 0;
                for(int j=0;j<Reference.size();j++){
                    temp_value0 = Reference.get(j)[0] - temp_Experimental_data[0][0];
                    temp_value1 = Reference.get(j)[1] - temp_Experimental_data[0][1];
                    temp_value2 = Reference.get(j)[2] - temp_Experimental_data[0][2];
                    temp_value0 = temp_value0 / maxvalue[0];
                    temp_value1 = temp_value1 / maxvalue[1];
                    temp_value2 = temp_value2 / maxvalue[2];
                    temp_value = (float) Math.sqrt((temp_value0 * temp_value0) + (temp_value1 * temp_value1)+ (temp_value2 * temp_value2));
                    float Min_Distance = temp_value;

                    for(int k=0;k<effectivelineNum;k++){
                        temp_value0 = Reference.get(j)[0] - temp_Experimental_data[k][0];
                        temp_value1 = Reference.get(j)[1] - temp_Experimental_data[k][1];
                        temp_value2 = Reference.get(j)[2] - temp_Experimental_data[k][2];
                        temp_value0 = temp_value0 / maxvalue[0];
                        temp_value1 = temp_value1 / maxvalue[1];
                        temp_value2 = temp_value2 / maxvalue[2];
                        temp_value = (float) Math.sqrt((temp_value0 * temp_value0) + (temp_value1 * temp_value1)+ (temp_value2 * temp_value2));
                        if(temp_value < Min_Distance){
                            Min_Distance = temp_value;
                        }
                    }
                    tempSum = tempSum + Min_Distance;
                }
                Inverted_Generational_Distance[i] = tempSum / Reference.size();
                IGDs[i] = Inverted_Generational_Distance[i];
            }
        }

        float average=0;
        for(int i=0;i<Experimental_data.length;i++)
            average=average+Inverted_Generational_Distance[i];
        average=average/Experimental_data.length;

        for (int i = 0; i < Experimental_data.length; i++) {
            varianceIGD += Math.pow((IGDs[i]-average),2);
        }
        varianceIGD = varianceIGD/Experimental_data.length;

        return average;
    }

    //Spacing指标//越小越好
    public float Get_Spacing(float[] maxvalue, ArrayList<Float[]> Reference, float[][][] Experimental_data){
        int boo[]=new int[Experimental_data.length];
        float[] Spacing = new float[Experimental_data.length];

        for(int i=0;i<Experimental_data.length;i++){
            if(Experimental_data[i][0][0] == -1){
                break;
            }
            else{
                int effectivelineNum = 0;   //记录该结果中的有效个体数目
                //计有效数
                for(int j=0;j<Experimental_data[i].length;j++){
                    if(Experimental_data[i][j][0] == -1){
                        break;
                    }
                    else{
                        effectivelineNum = effectivelineNum + 1;
                    }
                }
                if(effectivelineNum==1){
                    boo[i]=1;
                    Spacing[i] = 1;
                    Spacings[i] = Spacing[i];
                }else{

                    // 把有效个体抽出来
                    float[][] temp_Experimental_data = new float[effectivelineNum][2];
                    for(int j=0;j<effectivelineNum;j++){
                        temp_Experimental_data[j] = Experimental_data[i][j];
                    }

                    //抽完了 排序
                    temp_Experimental_data = Fitness_Ascending_order(temp_Experimental_data);


                    //极限点计算完     计算非支配解集中 相邻解间的欧式距离
                    float temp_value0;
                    float temp_value1;
                    float temp_value2;
                    float temp_value;

                    float temp_sum = 0;
                    float[] temp_distance = new float[effectivelineNum-1];
                    for(int j=0;j<effectivelineNum-1;j++){
                        temp_value0 = (temp_Experimental_data[j][0] - temp_Experimental_data[j+1][0])/maxvalue[0];
                        temp_value1 = (temp_Experimental_data[j][1] - temp_Experimental_data[j+1][1])/maxvalue[1];
                        temp_value2 = (temp_Experimental_data[j][2] - temp_Experimental_data[j+1][2])/maxvalue[2];
                        temp_value = (float) Math.sqrt((temp_value0 * temp_value0) + (temp_value1 * temp_value1)+ (temp_value2 * temp_value2));
                        temp_distance[j] = temp_value;
                        temp_sum = temp_sum + temp_value;
                    }

                    //算好了每个相邻间的距离，计算平均值
                    float ava_distance = temp_sum / (effectivelineNum-1);

                    //计算每一个相邻距离  和 平均距离的差  汇总
                    temp_sum = 0;
                    for(int j=0;j<effectivelineNum-1;j++){
                        temp_sum = temp_sum + (temp_distance[j] - ava_distance) * (temp_distance[j] - ava_distance);
                    }

                    //计算Spacing
                    Spacing[i] = (float) Math.sqrt(temp_sum / (effectivelineNum-1));
                    Spacings[i] = Spacing[i];
                }
            }
        }

        float average=0;
        int number=0;

        for(int i=0;i<Experimental_data.length;i++)
            if(boo[i]!=1){
                average=average+Spacing[i];
                number=number+1;
            }
        if(number==0){
            average = 0;
        }else{
            average=average/number;
        }

        for (int i = 0; i < Experimental_data.length; i++) {
            if(boo[i]!=1) {
                varianceSpacing += Math.pow((Spacings[i] - average), 2);
            }
        }
        if(number==0){
            varianceSpacing = 0;
        }else {
            varianceSpacing = varianceSpacing / number;
        }
        return average;

    }

    //Spread指标//越小越好
    public float Get_Spread(float[] maxvalue, ArrayList<Float[]> Reference, float[][][] Experimental_data){
        int boo[]=new int[Experimental_data.length];
        float[] Spread = new float[Experimental_data.length];  //一个实验 一个Spread

        for(int i=0;i<Experimental_data.length;i++){
            if(Experimental_data[i][0][0] == -1){
                break;
            }
            else{
                int effectivelineNum = 0;   //记录该结果中的有效个体数目
                //计有效数
                for(int j=0;j<Experimental_data[i].length;j++){
                    if(Experimental_data[i][j][0] == -1){
                        break;
                    }
                    else{
                        effectivelineNum = effectivelineNum + 1;
                    }
                }
                if(effectivelineNum==1){
                    boo[i]=1;
                    Spread[i] = 1;
                    Spreads[i] = Spread[i];
                }else{
                    // 把有效个体抽出来
                    float[][] temp_Experimental_data = new float[effectivelineNum][2];
                    for(int j=0;j<effectivelineNum;j++){
                        temp_Experimental_data[j] = Experimental_data[i][j];
                    }

                    //抽完了 排序
                    temp_Experimental_data = Fitness_Ascending_order(temp_Experimental_data);

                    //排序完了开始计算
                    //计算实验结果的极限点df
                    float df;
                    float temp_value0;
                    float temp_value1;
                    float temp_value2;
                    float temp_value;
                    temp_value0 = (temp_Experimental_data[0][0] - Reference.get(0)[0])/maxvalue[0];
                    temp_value1 = (temp_Experimental_data[0][1] - Reference.get(0)[1])/maxvalue[1];
                    temp_value2 = (temp_Experimental_data[0][2] - Reference.get(0)[1])/maxvalue[2];
                    temp_value = (float) Math.sqrt((temp_value0 * temp_value0) + (temp_value1 * temp_value1)+ (temp_value2 * temp_value2));
                    df = temp_value;
                    //计算实验结果的极限点dl
                    float dl;
                    temp_value0 = (temp_Experimental_data[effectivelineNum-1][0] - Reference.get(Reference.size()-1)[0])/maxvalue[0];
                    temp_value1 = (temp_Experimental_data[effectivelineNum-1][1] - Reference.get(Reference.size()-1)[1])/maxvalue[1];
                    temp_value2 = (temp_Experimental_data[effectivelineNum-1][2] - Reference.get(Reference.size()-1)[2])/maxvalue[2];
                    temp_value = (float) Math.sqrt((temp_value0 * temp_value0) + (temp_value1 * temp_value1)+ (temp_value2 * temp_value2));
                    dl = temp_value;

                    //极限点计算完     计算非支配解集中 相邻解间的欧式距离
                    float temp_sum = 0;
                    float[] temp_distance = new float[effectivelineNum-1];
                    for(int j=0;j<effectivelineNum-1;j++){
                        temp_value0 = (temp_Experimental_data[j][0] - temp_Experimental_data[j+1][0])/maxvalue[0];
                        temp_value1 = (temp_Experimental_data[j][1] - temp_Experimental_data[j+1][1])/maxvalue[1];
                        temp_value2 = (temp_Experimental_data[j][2] - temp_Experimental_data[j+1][2])/maxvalue[2];
                        temp_value = (float) Math.sqrt((temp_value0 * temp_value0) + (temp_value1 * temp_value1)+ (temp_value2 * temp_value2));
                        temp_distance[j] = temp_value;
                        temp_sum = temp_sum + temp_value;
                    }

                    //算好了每个相邻间的距离，计算平均值
                    float ava_distance = temp_sum / (effectivelineNum-1);

                    //计算每一个相邻距离  和 平均距离的差  汇总
                    temp_sum = 0;
                    for(int j=0;j<effectivelineNum-1;j++){
                        temp_sum = temp_sum + Math.abs(temp_distance[j] - ava_distance);
                    }

                    //计算Spread
                    Spread[i] = (df + dl + temp_sum) / (df + dl + (effectivelineNum-1)*ava_distance);
                    Spreads[i] = Spread[i];
                }
            }
        }

        float average=0;
        int number=0;
        for(int i=0;i<Experimental_data.length;i++)
            if(boo[i]!=1){
                average=average+Spread[i];
                number=number+1;
            }
        if(number==0){
            average = 0;
        }else{
            average=average/number;
        }

        for (int i = 0; i < Experimental_data.length; i++) {
            if(boo[i]!=1) {
                varianceSpread += Math.pow((Spreads[i] - average), 2);
            }
        }
        if(number==0){
            varianceSpread = 0;
        }else {
            varianceSpread = varianceSpread / number;
        }

        return average;
    }

    //将非支配解集 按某一目标顺序排序   输出排序过的非支配解集（因为为非支配解集，按任意目标排序即可 默认按第1个目标排序）
    public float[][] Fitness_Ascending_order(float[][] SolutionSet){
        float[][] fitness = new float[SolutionSet.length][2];
        for(int i=0;i<SolutionSet.length;i++){   //将所有个体 该目标的适应度添加到fitness中
            fitness[i][0] = i;
            fitness[i][1] = SolutionSet[i][0];
        }

        for(int i=0;i<SolutionSet.length;i++){    //冒泡排序 对fitness序列排序
            float[] temp = new float[2];
            temp[0] = 0;
            temp[1] = 0;
            for(int j=i+1;j<SolutionSet.length;j++){
                if(fitness[j][1] < fitness[i][1]){
                    temp[0] = fitness[i][0];  //交换内容
                    temp[1] = fitness[i][1];  //交换内容

                    fitness[i][0] = fitness[j][0];
                    fitness[i][1] = fitness[j][1];

                    fitness[j][0] = temp[0];
                    fitness[j][1] = temp[1];
                }
            }
        }
        float[][] Order_Population = new float[SolutionSet.length][3];
        for(int i=0;i<SolutionSet.length;i++){  //按照最小值下标序列覆盖
            Order_Population[i][0] = SolutionSet[(int) fitness[i][0]][0];
            Order_Population[i][1] = SolutionSet[(int) fitness[i][0]][1];
            Order_Population[i][2] = SolutionSet[(int) fitness[i][0]][2];
        }
        return Order_Population;
    }

    public String indexstoString1(){
        return "GD," + arraytostring1(GDs) +
                ",IGD," + arraytostring1(IGDs) +
                ",HV," + arraytostring1(HVs) +
                ",Spacing,"+ arraytostring1(Spacings) +
                ",Spread,"+ arraytostring1(Spreads)
                ;
    }     //原始


    public String indexstoString(int e){
        int a=e;
        return arraytostring(GDs,a)+","+arraytostring(IGDs,a)+","+arraytostring(HVs,a)+
                ","+arraytostring(Spacings,a)+","+arraytostring(Spreads,a);
    }


    public String arraytostring(float[] arrays,int a){
        StringBuffer str = new StringBuffer();
        //for (int i = 0; i < arrays.length-1; i++) {
            str.append(arrays[a-1]);
        //}
        //str.append(arrays[arrays.length-1]);

        return str.toString();
    }




    public String arraytostring1(float[] arrays){
        StringBuffer str = new StringBuffer();
        for (int i = 0; i < arrays.length-1; i++) {
            str.append(arrays[i]+",");
        }
        str.append(arrays[arrays.length-1]);

        return str.toString();
    }     //原始

    public float getGD() {
        return GD;
    }

    public void setGD(float GD) {
        this.GD = GD;
    }

    public float getIGD() {
        return IGD;
    }

    public void setIGD(float IGD) {
        this.IGD = IGD;
    }

    public float getHV() {
        return HV;
    }

    public void setHV(float HV) {
        this.HV = HV;
    }

    public float getSpacing() {
        return Spacing;
    }

    public void setSpacing(float spacing) {
        Spacing = spacing;
    }

    public float getSpread() {
        return Spread;
    }

    public void setSpread(float spread) {
        Spread = spread;
    }

    @Override
    public String toString() {
        return "GD," + GD + ","+ Math.sqrt(varianceGD) +
                ",IGD," + IGD + "," + Math.sqrt(varianceIGD) +
                ",HV," + HV + "," + Math.sqrt(varianceHV) +
                ",Spacing," + Spacing + "," + Math.sqrt(varianceSpacing) +
                ",Spread," + Spread + "," + Math.sqrt(varianceSpread);
    }

    //for rank
    public String toStringforRank() {
        return GD + " " + IGD + " " + HV + " " + Spacing + " " + Spread;
    }

    //for paper
    public String toStringforPaper() {
        return GD + " " + Math.sqrt(varianceGD) + " " + IGD + " " + Math.sqrt(varianceIGD) + " " + HV + " " + Math.sqrt(varianceHV) + " " + Spacing + " " + Math.sqrt(varianceSpacing) + " " + Spread + " " + Math.sqrt(varianceSpread);
    }
}
