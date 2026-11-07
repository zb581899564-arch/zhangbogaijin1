package org.uma.jmetal.qualityindicator.myqualityindicator.util;

import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.front.Front;

import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class Get_Pareto {

    private float[] maxvalue;

    private ArrayList<Float[]> ParetoFront;



    public float[] getMaxvalue() {
        return maxvalue;
    }

    public void setMaxvalue(float[] maxvalue) {
        this.maxvalue = maxvalue;
    }

    public ArrayList<Float[]> getParetoFront() {
        return ParetoFront;
    }

    public void setParetoFront(ArrayList<Float[]> paretoFront) {
        ParetoFront = paretoFront;
    }

    @Override
    public String toString() {
        return "Get_Pareto{" +
                "maxvalue=" + Arrays.toString(maxvalue) +
                ", ParetoFront=" + ParetoFront +
                '}';
    }

    //生成pareto前沿面，生成文件
    public Get_Pareto(String filename,String problem,String[] algorithms, double[] R, int[] swarmsize) throws IOException {

        ArrayList<Float[]> Data = new ArrayList<>();
        ArrayList<Float[]> temp = null;

        for (int i = 0; i < algorithms.length; i++) {
            for (int j = 0; j < R.length; j++) {
                for (int k = 0; k < swarmsize.length; k++) {
                    temp = Read_Data(filename+problem+"_"+algorithms[i]+"_"+R[j]+"_"+swarmsize[k]+".txt");

                    /*for (int h = 0; h < temp.size(); h++) {
                        System.out.println(temp.get(h)[0]+" "+temp.get(h)[1]);
                    }
                    System.out.println("*************************************");*/

                    Data = mager(Data,temp);
                }
            }
        }

        /*for (int i = 0; i < Data.size(); i++) {
            System.out.println(Data.get(i)[0]+" "+Data.get(i)[1]);
        }
        System.out.println("*************************************");*/

        maxvalue = Get_Maxvalue(Data);
        ParetoFront = Get_Nondominated(Data);

        /*for (int i = 0; i < ParetoFront.size(); i++) {
            System.out.println(ParetoFront.get(i)[0]+" "+ParetoFront.get(i)[1]);
        }
        System.out.println("---------------------------");*/

        BufferedWriter bw = new BufferedWriter(new FileWriter(filename+"Pareto_"+problem+".txt"));

        for(int i=0;i<ParetoFront.size();i++){
            bw.write(ParetoFront.get(i)[0]+" "+ParetoFront.get(i)[1]);
            bw.newLine();
        }
        bw.flush();
        bw.close();
    }

    //生成pareto前沿面，生成文件
    public Get_Pareto(String filename,String problem,String[] algorithms) throws IOException {

        ArrayList<Float[]> Data = new ArrayList<>();
        ArrayList<Float[]> temp = null;

        for (int i = 0; i < algorithms.length; i++) {
            temp = Read_Data(filename+problem+"-"+algorithms[i]+".txt");

            Data = mager(Data,temp);
        }

        /*for (int i = 0; i < Data.size(); i++) {
            System.out.println(Data.get(i)[0]+" "+Data.get(i)[1]);
        }
        System.out.println("*************************************");*/

        maxvalue = Get_Maxvalue(Data);
        ParetoFront = Get_Nondominated(Data);

        /*for (int i = 0; i < ParetoFront.size(); i++) {
            System.out.println(ParetoFront.get(i)[0]+" "+ParetoFront.get(i)[1]);
        }
        System.out.println("---------------------------");*/

        BufferedWriter bw = new BufferedWriter(new FileWriter(filename+"Pareto_"+problem+".txt"));

        for(int i=0;i<ParetoFront.size();i++){
            bw.write(ParetoFront.get(i)[0]+" "+ParetoFront.get(i)[1]);
            bw.newLine();
        }
        bw.flush();
        bw.close();
    }

    //生成单目标最大值，用于归一化和HV参考点
    public float[] Get_Maxvalue(ArrayList<Float[]> Data) throws IOException{

        maxvalue=new float[2];

        maxvalue[0]=Data.get(0)[0];
        maxvalue[1]=Data.get(0)[1];

        for(int i=1;i<Data.size();i++){
            if(maxvalue[0]<Data.get(i)[0]){
                maxvalue[0]=Data.get(i)[0];
            }
            if(maxvalue[1]<Data.get(i)[1]){
                maxvalue[1]=Data.get(i)[1];
            }
        }

        return maxvalue;
    }


    protected ArrayList<Float[]> mager(ArrayList<Float[]> swarm1, ArrayList<Float[]> swarm2)  {
        ArrayList<Float[]> temp = new ArrayList<Float[]>();

        for(int i=0;i<swarm1.size();i++){
            temp.add(swarm1.get(i));
        }

        for(int i=0;i<swarm2.size();i++){
            temp.add(swarm2.get(i));
        }

        return temp;

    }


    public ArrayList<Float[]> Get_Nondominated (ArrayList<Float[]> populationIndex) throws IOException{
        ArrayList<Float[]> result = new ArrayList<Float[]>();

        for (int i = 0; i < populationIndex.size(); i++) {
            result.add(populationIndex.get(i));
        }

        //去重
        for(int i=0;i<result.size();i++){
            for(int j=i+1;j<result.size();j++){
                if(result.get(i)[0]<=result.get(j)[0]&&result.get(i)[1]<=result.get(j)[1]){
                    result.remove(j);
                    j--;
                }
            }
            for(int j=i+1;j<result.size();j++){
                if(result.get(i)[0]>=result.get(j)[0]&&result.get(i)[1]>=result.get(j)[1]){
                    result.remove(i);
                    i--;
                    break;
                }
            }
        }

        return result;

    }


    //依照文件路径读取指标数据
    public ArrayList<Float[]> Read_Data(String File_path) throws IOException{

        ArrayList<Float[]> tempdata =new ArrayList<>();
        BufferedReader data = new BufferedReader(new InputStreamReader(new FileInputStream(File_path)));
        String lineTxt = null;

        while ((lineTxt = data.readLine()) != null) {
            lineTxt = lineTxt.trim();//去除左右的空格
            String[] strcol = lineTxt.split(" ");

            if(!strcol[0].equals("")){
                Float[] temp = new Float[2];
                temp[0] = Float.parseFloat(strcol[0]);
                temp[1] = Float.parseFloat(strcol[1]);

                tempdata.add(temp);
            }
        }
        data.close();

        /*for (int h = 0; h < tempdata.size(); h++) {
            System.out.println(tempdata.get(h)[0]+" "+tempdata.get(h)[1]);
        }
        System.out.println("--------------------------");*/

        return tempdata;
    }


}
