package org.uma.jmetal.qualityindicator.myqualityindicator.util;

import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;

public class UtilPareto {

    private float[] maxvalue;

    private ArrayList<Float[]> ParetoFront;

    public UtilPareto() {

        maxvalue = new float[3];
        maxvalue[0] = -1;
        maxvalue[1] = -1;
        maxvalue[2] = -1;
        ParetoFront= new ArrayList<Float[]>();
    }


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
    public UtilPareto(String filename, String problem, String[] algorithms, double[] R, int[] swarmsize, double[] rand, double[] Probability, double[] Cross, double[] Mutation) throws IOException {

        ArrayList<Float[]> Data = new ArrayList<>();
        ArrayList<Float[]> temp = null;

        for (int i = 0; i < algorithms.length; i++) {
            for (int j = 0; j < R.length; j++) {
                for (int k = 0; k < swarmsize.length; k++) {

                    temp = Read_Data(filename + problem + "_" + algorithms[i] + "_" + R[j] + "_" + swarmsize[k] + ".txt");
                    maxvalue = updateMaxValueFromList(temp);      //
                    Data = merge(Data, temp);


                }
            }
        }


        maxvalue = updateMaxValueFromList(Data);      //
        ParetoFront = getNondominatedSolutions(Data);     //非支配解


        BufferedWriter bw = new BufferedWriter(new FileWriter(filename + "Pareto_" + problem + "_" + rand + "_" + swarmsize + "_" + Probability + "_" + Cross + "_" + Mutation + ".txt"));

        for (int i = 0; i < ParetoFront.size(); i++) {
            bw.write(ParetoFront.get(i)[0] + " " + ParetoFront.get(i)[1]+" "+ParetoFront.get(i)[2] );
            bw.newLine();
        }
        bw.flush();
        bw.close();
    }

    //生成pareto前沿面，生成文件
    public void getParetoFromFile4OneProblemOneMethodOnePara(String solutionFolderName, String strProblemName, String algorithmName,
                                                             double rand, int swarmSize, double DERate, double crossoverRate, double mutationRate) throws IOException {

        ArrayList<Float[]> data = new ArrayList<>();
        ArrayList<Float[]> temp = null;

        //String strFileName = new String(solutionFolderName + "solution-"+strProblemName + "-" + algorithmName+ "_" +
        //        rand + "_" + swarmSize + "_" + DERate + "_" + crossoverRate + "_" + mutationRate + ".txt");

        StringBuilder sbFileName= new StringBuilder();
        sbFileName.append(solutionFolderName).append("solution-");
        sbFileName.append(strProblemName).append("-");
        sbFileName.append(algorithmName).append("_");
        sbFileName.append(rand).append("_");
        sbFileName.append(swarmSize).append("_");
        sbFileName.append(crossoverRate).append("_");
        sbFileName.append(mutationRate).append("_");
        sbFileName.append(DERate);
        sbFileName.append(".txt");


        //temp = Read_Data(strFileName);
        temp = Read_Data(sbFileName.toString());

        maxvalue = updateMaxValueFromList(temp);

        data = merge(data, temp);

        ParetoFront = getNondominatedSolutions(data);

    }

    //生成pareto前沿面，生成文件
    public void getParetoFromFile4OneProblemOneMethodOnePara(String filepath) throws IOException {

        ArrayList<Float[]> data = new ArrayList<>();
        ArrayList<Float[]> temp = null;


        temp = Read_Data(filepath);

        maxvalue = updateMaxValueFromList(temp);

        data = merge(data, temp);

        ParetoFront = getNondominatedSolutions(data);

//        for (Float[] floats : ParetoFront) {
//            for (Float aFloat : floats) {
//                System.out.print(aFloat+" ");
//            }
//            System.out.println();
//        }

    }

    //生成pareto前沿面，生成文件
    public void getParetoFromFile4OneProblemOneMethod(String folderName, String problemName, String algorithmName,
                                                      double rand, int swarmSize, double DERate, double crossoverRate, double mutationRate) throws IOException {

        ArrayList<Float[]> Data = new ArrayList<>();
        ArrayList<Float[]> temp = null;

       String strFileName = new String(folderName + "solution-"+problemName + "-" + algorithmName + "_" + rand + "_" + swarmSize + "_" + DERate + "_" + crossoverRate + "_" + mutationRate + ".txt");

       temp = Read_Data(strFileName);
        maxvalue = updateMaxValueFromList(temp);
       Data = merge(Data, temp);


        ParetoFront = getNondominatedSolutions(Data);

    }

    //生成pareto前沿面，生成文件
    public void getParetoFromFile4OneProblemOneMethod_output(String folderName, String problemName, String algorithmName,
                                                             double rand, int swarmSize, double DERate, double crossoverRate, double mutationRate) throws IOException {

        ArrayList<Float[]> Data = new ArrayList<>();
        ArrayList<Float[]> temp = null;

        //for (int i = 0; i < algorithmName.length; i++) {

            String strFileName = new String(folderName + "solution-"+problemName + "-" + algorithmName + "_" + rand + "_" + swarmSize + "_" + DERate + "_" + crossoverRate + "_" + mutationRate + ".txt");

            temp = Read_Data(strFileName);
        maxvalue = updateMaxValueFromList(temp);
            Data = merge(Data, temp);
        //}



        ParetoFront = getNondominatedSolutions(Data);

        String strOutputFileName = new String(folderName + "Pareto_" + problemName + "_" + rand + "_" + swarmSize + "_" + DERate + "_" + crossoverRate + "_" + mutationRate + ".txt");

        BufferedWriter bw = new BufferedWriter(new FileWriter(strOutputFileName));

        for (int i = 0; i < ParetoFront.size(); i++) {
            bw.write(ParetoFront.get(i)[0] + " " + ParetoFront.get(i)[1]);
            bw.newLine();
        }
        bw.flush();
        bw.close();
    }

    //生成pareto前沿面，生成文件
    public void updateParetoFromData(ArrayList<Float[]> dataFrom) throws IOException {

        ArrayList<Float[]> data = new ArrayList<>();
        ArrayList<Float[]> temp = null;

        temp = dataFrom;

        maxvalue = updateMaxValueFromList(temp);

        data = ParetoFront;

        data = merge(data, temp);

//        for (Float[] datum : data) {
//            for (Float v : datum) {
//                System.out.print(v+" ");
//            }
//            System.out.println();
//        }

        ParetoFront = getNondominatedSolutions(data);

    }

    //输出某个问题的某个算法的Pareto
    public void outputPareto4OneProblemOneMethod(String folderName, String problem, String algorithm) throws IOException {

        //StringBuffer sbFileName = new StringBuffer();
        //sbFileName.append(folderName).append("Pareto_").append(problem).append("_").append(algorithm).append(".txt");

        String strFileName = new String(folderName+"Pareto_"+problem+"_"+algorithm+".txt");

        BufferedWriter bw = new BufferedWriter(new FileWriter(strFileName));

        for (int i = 0; i < ParetoFront.size(); i++) {
            bw.write(ParetoFront.get(i)[0] + " " + ParetoFront.get(i)[1]+ " " + ParetoFront.get(i)[2]);
            bw.newLine();
        }
        bw.flush();
        bw.close();
    }

    //输出某个问题的Pareto
    public void outputPareto4OneProblem(String folderName, String problem) throws IOException {

        String strFileName = new String(folderName+"Pareto_"+problem+".txt");

        BufferedWriter bw = new BufferedWriter(new FileWriter(strFileName));

        for (int i = 0; i < ParetoFront.size(); i++) {
            bw.write(ParetoFront.get(i)[0] + " " + ParetoFront.get(i)[1]+ " " + ParetoFront.get(i)[2]);
            bw.newLine();
        }
        bw.flush();
        bw.close();
    }

    //读取某个问题的Pareto
    public void getParetoFromOneProblem(String folderName, String problem) throws IOException {

        String strFileName = new String(folderName+"Pareto_"+problem+".txt");
        System.out.println(strFileName);
        ParetoFront = new ArrayList<>();
        BufferedReader data = new BufferedReader(new InputStreamReader(new FileInputStream(strFileName)));
        String lineTxt = null;

        while ((lineTxt = data.readLine()) != null ) {
            if (!lineTxt.equals("")){
                lineTxt = lineTxt.trim();//去除左右的空格
                String[] strcol = lineTxt.split(" ");

                if (!strcol[0].equals("")) {
                    Float[] temp = new Float[3];
                    temp[0] = Float.parseFloat(strcol[0]);
                    temp[1] = Float.parseFloat(strcol[1]);
                    temp[2] = Float.parseFloat(strcol[2]);

                    ParetoFront.add(temp);
                }
            }
        }
        data.close();
    }

    //输出某个问题的Pareto
    public void outputMaxValue4OneProblem(String folderName, String problem) throws IOException {

        String strFileName = new String(folderName+"MaxValue_"+problem+".txt");

        BufferedWriter bw = new BufferedWriter(new FileWriter(strFileName));

        for (int i = 0; i < maxvalue.length; i++) {

            bw.write(String.valueOf(maxvalue[i]));
            bw.write(" ");
        }
        bw.flush();
        bw.close();
    }

    //读取某个问题的最坏值
    public void getMaxValueFromOneProblem(String folderName, String problem) throws IOException {

        String strFileName = new String(folderName+"MaxValue_"+problem+".txt");

        maxvalue = new float[3];
        BufferedReader data = new BufferedReader(new InputStreamReader(new FileInputStream(strFileName)));
        String lineTxt = null;

        while ((lineTxt = data.readLine()) != null ) {
            if (!lineTxt.equals("")){
                lineTxt = lineTxt.trim();//去除左右的空格
                String[] strcol = lineTxt.split(" ");

                if (!strcol[0].equals("")) {
                    Float[] temp = new Float[2];
                    maxvalue[0]  = Float.parseFloat(strcol[0]);
                    maxvalue[1]  = Float.parseFloat(strcol[1]);
                    maxvalue[2]  = Float.parseFloat(strcol[2]);

                }
            }
        }
        data.close();
    }


    //生成单目标最大值，用于归一化和HV参考点
    public float[] updateMaxValueFromList(ArrayList<Float[]> Data) throws IOException {

        //maxvalue = new float[2];

        //maxvalue[0] = Data.get(0)[0];
        //maxvalue[1] = Data.get(0)[1];

        for (int i = 1; i < Data.size(); i++) {
            if (maxvalue[0] < Data.get(i)[0]) {
                maxvalue[0] = Data.get(i)[0];
            }
            if (maxvalue[1] < Data.get(i)[1]) {
                maxvalue[1] = Data.get(i)[1];
            }
            if (maxvalue[2] < Data.get(i)[2]) {
                maxvalue[2] = Data.get(i)[2];
            }
        }

        return maxvalue;
    }
    //生成pareto前沿面，生成文件
    public void updateMaxValue(float[] dataFrom) throws IOException {

        if (maxvalue[0] < dataFrom[0]) {
            maxvalue[0] = dataFrom[0];
        }
        if (maxvalue[1] < dataFrom[1]) {
            maxvalue[1] = dataFrom[1];
        }
        if (maxvalue[2] < dataFrom[2]) {
            maxvalue[2] = dataFrom[2];
        }
    }

    protected ArrayList<Float[]> merge(ArrayList<Float[]> swarm1, ArrayList<Float[]> swarm2) {
        ArrayList<Float[]> temp = new ArrayList<Float[]>();

        for (int i = 0; i < swarm1.size(); i++) {
            temp.add(swarm1.get(i));
        }

        for (int i = 0; i < swarm2.size(); i++) {
            temp.add(swarm2.get(i));
        }
//        for (Float[] floats : temp) {
//            for (Float aFloat : floats) {
//                System.out.print(aFloat+" ");
//            }
//            System.out.println();
//        }
        return temp;

    }


    public ArrayList<Float[]> getNondominatedSolutions(ArrayList<Float[]> populationIndex) throws IOException {
        ArrayList<Float[]> result = new ArrayList<Float[]>();

        for (int i = 0; i < populationIndex.size(); i++) {
            result.add(populationIndex.get(i));
//            for (Float[] index : populationIndex) {
//                for (Float v : index) {
//                    System.out.print(v+" ");
//                }
//                System.out.println();
//            }
        }

        //去重
        for (int i = 0; i < result.size(); i++) {
            for (int j = i + 1; j < result.size(); j++) {
                if (result.get(i)[0] <= result.get(j)[0] && result.get(i)[1] <= result.get(j)[1] && result.get(i)[2] <= result.get(j)[2]) {
                    result.remove(j);
                    j--;
                }
            }
            for (int j = i + 1; j < result.size(); j++) {
                if (result.get(i)[0] >= result.get(j)[0] && result.get(i)[1] >= result.get(j)[1] && result.get(i)[2] >= result.get(j)[2]) {
                    result.remove(i);
                    i--;
                    break;
                }
            }
        }
//        for (Float[] floats : result) {
//            for (Float aFloat : floats) {
//                System.out.print(aFloat+" ");
//            }
//            System.out.println();
//        }
//        System.out.println();
        return result;

    }


    //依照文件路径读取指标数据
    public ArrayList<Float[]> Read_Data(String filePath) throws IOException {
//        System.out.println(filePath);
        ArrayList<Float[]> tempdata = new ArrayList<>();
        BufferedReader data = new BufferedReader(new InputStreamReader(new FileInputStream(filePath)));
        String lineTxt = null;

        while ((lineTxt = data.readLine()) != null ) {
            if (!lineTxt.equals("")){
                lineTxt = lineTxt.trim();//去除左右的空格
                String[] strcol0 = lineTxt.split("\t");
                String[] strcol = strcol0[0].split(" ");

                if (!strcol[0].equals("")) {
                    Float[] temp = new Float[3];
                    temp[0] = Float.parseFloat(strcol[0]);
                    temp[1] = Float.parseFloat(strcol[1]);
                    temp[2] = Float.parseFloat(strcol[2]);
//                    for (Float v : temp) {
//                        System.out.print(v+" ");
//                    }
                    tempdata.add(temp);
                }
//                data.readLine();
            }

        }

        data.close();

        return tempdata;
    }

}
