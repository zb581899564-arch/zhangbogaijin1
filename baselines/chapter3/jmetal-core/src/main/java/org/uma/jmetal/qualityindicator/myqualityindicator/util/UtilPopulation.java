package org.uma.jmetal.qualityindicator.myqualityindicator.util;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.Arrays;

public class UtilPopulation {


        private float[][][] Experimental_data;
        private float object1max=-1;
        private float object1min=Float.MAX_VALUE;
        private float object2max=-1;
        private float object2min=Float.MAX_VALUE;

        private float object3max=-1;
        private float object3min=Float.MAX_VALUE;

        public float[][][] getExperimental_data() {
            return Experimental_data;
        }

        public void setExperimental_data(float[][][] experimental_data) {
            Experimental_data = experimental_data;
        }

        public float getObject1max() {
            return object1max;
        }

        public void setObject1max(float object1max) {
            this.object1max = object1max;
        }

        public float getObject1min() {
            return object1min;
        }

        public void setObject1min(float object1min) {
            this.object1min = object1min;
        }

        public float getObject2max() {
            return object2max;
        }

        public void setObject2max(float object2max) {
            this.object2max = object2max;
        }

        public float getObject2min() {
            return object2min;
        }

        public void setObject2min(float object2min) {
            this.object2min = object2min;
        }

        @Override
        public String toString() {
            return "Get_Population{" +
                    "Experimental_data=" + Arrays.toString(Experimental_data) +
                    ", object1max=" + object1max +
                    ", object1min=" + object1min +
                    ", object2max=" + object2max +
                    ", object2min=" + object2min +
                    ", object3max=" + object3max +
                    ", object3min=" + object3min +
                    '}';
        }

        public String MaxandMintoString() {
            return object1max + "," + object1min + "," + object2max +"," + object2min+ "," + object3max +"," + object3min;
        }

        //读实验数据号
        public float[][][] Read_Experimental_data1(String filename,String problem,String algorithm, int num) throws IOException {
            Experimental_data = new float[num][100][2]; //30次实验 30个数组
            for(int i=0;i<num;i++){
                for(int j=0;j<100;j++){
                    Experimental_data[i][j][0] = -1;
                    Experimental_data[i][j][1] = -1;
                }
            }

            BufferedReader data = new BufferedReader(new InputStreamReader(new FileInputStream(filename+problem+"_"+algorithm+".txt")));
            String lineTxt = null;
            int Test_number = 0;
            int One_Test_effectivelineNum = 0;
            while ((lineTxt = data.readLine()) != null) {
                lineTxt = lineTxt.trim();//去除左右的空格
                String[] strcol = lineTxt.split(" ");
                if(!strcol[0].equals("")){
                    Experimental_data[Test_number][One_Test_effectivelineNum][0] = Float.parseFloat(strcol[0]);
                    Experimental_data[Test_number][One_Test_effectivelineNum][1] = Float.parseFloat(strcol[1]);

                    calculateMaxandMin(Experimental_data[Test_number][One_Test_effectivelineNum][0],1);
                    calculateMaxandMin(Experimental_data[Test_number][One_Test_effectivelineNum][1],2);

                    One_Test_effectivelineNum = One_Test_effectivelineNum + 1;
                }
                else{
                    One_Test_effectivelineNum = 0;
                    Test_number = Test_number + 1;
                }
            }
            data.close();

            return Experimental_data;
        }

        private void calculateMaxandMin(float object, int objectnumber){
            if(objectnumber==1){
                if(object1max<object){
                    object1max=object;
                }
                if(object1min>object){
                    object1min=object;
                }
            }else{
                if(object2max<object){
                    object2max=object;
                }
                if(object2min>object){
                    object2min=object;
                }
            }
        }

        //读实验数据号（对比参数用）
        public float[][][] Read_Experimental_data(String folderName,String problem,
                                                  String algorithmName, double rand,double  pmxCrossover,double V1mutationProbability,int swarmSize,
                                                  double DERate ,
                                                  double crossoverRate,double mutationRate,
                                                  double DECrossoverRate, double DEMutationRate,
                                                  int num) throws IOException {

            Experimental_data = new float[num][200][3]; //10次实验 10个数组 //TODO
//            Experimental_data = new float[50][1000][3]; //10次实验 10个数组 //TODO
            for(int i=0;i<num;i++){
                for(int j=0;j<200;j++){
                    Experimental_data[i][j][0] = -1;
                    Experimental_data[i][j][1] = -1;
                    Experimental_data[i][j][2] = -1;
                }
            }

            //String strFilePath = new String(folderName+"solution-"+problem+"-"+algorithm+"_"+R+"_"+swarmsize+"_"+probability+"_"+Cross+"_"+Mutation+".txt");

            StringBuilder sbFileName= new StringBuilder();
//            sbFileName.append(folderName).append("solution-");
            sbFileName.append(folderName).append("object-");
            sbFileName.append(problem).append("-");
//            sbFileName.append(algorithmName).append("_");
            sbFileName.append(algorithmName).append("-");
            sbFileName.append(rand).append("_");
            sbFileName.append(pmxCrossover).append("_");
            sbFileName.append(V1mutationProbability).append("_");
            sbFileName.append(swarmSize).append("_");
            sbFileName.append(crossoverRate).append("_");
            sbFileName.append(mutationRate).append("_");
            sbFileName.append(DERate).append("_");
            sbFileName.append(DECrossoverRate).append("_");
            sbFileName.append(DEMutationRate);
            sbFileName.append(".txt");

            BufferedReader data = new BufferedReader(new InputStreamReader(new FileInputStream(sbFileName.toString())));
            String lineTxt = null;
            int Test_number = 0;
            int One_Test_effectivelineNum = 0;

            while ((lineTxt = data.readLine()) != null) {    //整个文件结束
                if (!lineTxt.equals("")){
                    lineTxt = lineTxt.trim();//去除左右的空格
                    String[] strcol0 = lineTxt.split("\t");
                    String[] strcol = strcol0[0].split(" ");

                    if(!strcol[0].equals("")){
                        Experimental_data[Test_number][One_Test_effectivelineNum][0] = Float.parseFloat(strcol[0]);
                        Experimental_data[Test_number][One_Test_effectivelineNum][1] = Float.parseFloat(strcol[1]);
                        Experimental_data[Test_number][One_Test_effectivelineNum][2] = Float.parseFloat(strcol[2]);
                        One_Test_effectivelineNum = One_Test_effectivelineNum + 1;
                    }
                    //忽略工厂向量
                    data.readLine();
                } else{
                    //空行
                    One_Test_effectivelineNum = 0;
                    Test_number = Test_number + 1;

                }


            }
            data.close();
            return Experimental_data;
        }

    //读实验数据号（对比参数用）
    public float[][][] Read_Experimental_datapri(String folderName,String problem,
                                              String algorithmName, double rand,int swarmSize,
                                              double DERate ,
                                              double crossoverRate,double mutationRate,
                                              double DECrossoverRate, double DEMutationRate,
                                              int num) throws IOException {
        Experimental_data = new float[num][100][2]; //10次实验 10个数组 //TODO
        for(int i=0;i<num;i++){
            for(int j=0;j<50;j++){
                Experimental_data[i][j][0] = -1;
                Experimental_data[i][j][1] = -1;
            }
        }

        //String strFilePath = new String(folderName+"solution-"+problem+"-"+algorithm+"_"+R+"_"+swarmsize+"_"+probability+"_"+Cross+"_"+Mutation+".txt");

        StringBuilder sbFileName= new StringBuilder();
        sbFileName.append(folderName).append("solution-");
        sbFileName.append(problem).append("-");
        sbFileName.append(algorithmName).append("_");
        sbFileName.append(rand).append("_");
/*        sbFileName.append(pmxCrossover).append("_");
        sbFileName.append(V1mutationProbability).append("_");*/
        sbFileName.append(swarmSize).append("_");
        sbFileName.append(crossoverRate).append("_");
        sbFileName.append(mutationRate).append("_");
        sbFileName.append(DERate).append("_");
        sbFileName.append(DECrossoverRate).append("_");
        sbFileName.append(DEMutationRate);
        sbFileName.append(".txt");

        BufferedReader data = new BufferedReader(new InputStreamReader(new FileInputStream(sbFileName.toString())));
        String lineTxt = null;
        int Test_number = 0;
        int One_Test_effectivelineNum = 0;

        while ((lineTxt = data.readLine()) != null) {    //整个文件结束
            if (!lineTxt.equals("")){
                lineTxt = lineTxt.trim();//去除左右的空格
                String[] strcol0 = lineTxt.split("\t");
                String[] strcol = strcol0[0].split(" ");

                if(!strcol[0].equals("")){
                    Experimental_data[Test_number][One_Test_effectivelineNum][0] = Float.parseFloat(strcol[0]);
                    Experimental_data[Test_number][One_Test_effectivelineNum][1] = Float.parseFloat(strcol[1]);
                    One_Test_effectivelineNum = One_Test_effectivelineNum + 1;
                }
                //忽略工厂向量
                data.readLine();
            } else{
                //空行
                One_Test_effectivelineNum = 0;
                Test_number = Test_number + 1;

            }


        }
        data.close();
        return Experimental_data;
    }


    //读实验数据号（对比参数用）
    public float[][][] Read_Experimental_data_Nonparametric(String folderName,String problem,
                                              String algorithmName,
                                              int num) throws IOException {
        Experimental_data = new float[num][1000][3]; //10次实验 10个数组 //TODO
        for(int i=0;i<num;i++){
            System.out.println("执行了"+i);
            for(int j=0;j<1000;j++){
                Experimental_data[i][j][0] = -1;
                Experimental_data[i][j][1] = -1;
                Experimental_data[i][j][2] = -1;
            }
        }

        //String strFilePath = new String(folderName+"solution-"+problem+"-"+algorithm+"_"+R+"_"+swarmsize+"_"+probability+"_"+Cross+"_"+Mutation+".txt");

        StringBuilder sbFileName= new StringBuilder();
//        sbFileName.append(folderName).append("solution-");

        //todo 这里记得改
        sbFileName.append(folderName).append("object-");
        sbFileName.append(problem).append("-");
        sbFileName.append(algorithmName);
/*        sbFileName.append(rand).append("_");
        sbFileName.append(pmxCrossover).append("_");
        sbFileName.append(V1mutationProbability).append("_");
        sbFileName.append(swarmSize).append("_");
        sbFileName.append(crossoverRate).append("_");
        sbFileName.append(mutationRate).append("_");
        sbFileName.append(DERate).append("_");
        sbFileName.append(DECrossoverRate).append("_");
        sbFileName.append(DEMutationRate);*/
        sbFileName.append(".txt");
//        System.out.println(sbFileName.toString());
        BufferedReader data = new BufferedReader(new InputStreamReader(new FileInputStream(sbFileName.toString())));
        String lineTxt = null;
        int Test_number = 0;
        int One_Test_effectivelineNum = 0;

        while ((lineTxt = data.readLine()) != null) {    //整个文件结束
//            System.out.println(lineTxt);
            if (!lineTxt.equals("")){
                lineTxt = lineTxt.trim();//去除左右的空格

                String[] strcol0 = lineTxt.split("\t");
                String[] strcol = strcol0[0].split(" ");
//                for (String s : strcol0) {
//                    System.out.print(s+" ");
//                }
//                System.out.println(
//                );
//

//                try {
//                    Thread.sleep(99999);
//                } catch (InterruptedException e) {
//                    throw new RuntimeException(e);
//                }
                if(!strcol[0].equals("")){


                    Experimental_data[Test_number][One_Test_effectivelineNum][0] = Float.parseFloat(strcol[0]);
                    Experimental_data[Test_number][One_Test_effectivelineNum][1] = Float.parseFloat(strcol[1]);
                    Experimental_data[Test_number][One_Test_effectivelineNum][2] = Float.parseFloat(strcol[2]);


                    One_Test_effectivelineNum = One_Test_effectivelineNum + 1;
                }
                //忽略工厂向量
//                data.readLine();
//                data.readLine();
//                data.readLine();
//                data.readLine();

            } else{
                //空行
                One_Test_effectivelineNum = 0;
                Test_number = Test_number + 1;

            }
        }
        //System.out.print(Test_number);

        data.close();
        return Experimental_data;
    }


    public float[][][] Read_Experimental_data_new(String folderName,String problem,
                                              String algorithmName, double rand,double  pmxCrossover,double V1mutationProbability,int swarmSize,
                                              double DERate ,
                                              double crossoverRate,double mutationRate,
                                              double DECrossoverRate, double DEMutationRate,double crossoverRates4worker,double crossoverRates4machine,
                                              double mutionRate4worker,double mutionRate4machine,int localsearch,
                                              int num) throws IOException {



        //String strFilePath = new String(folderName+"solution-"+problem+"-"+algorithm+"_"+R+"_"+swarmsize+"_"+probability+"_"+Cross+"_"+Mutation+".txt");

        StringBuilder sbFileName= new StringBuilder();
//            sbFileName.append(folderName).append("solution-");
        sbFileName.append(folderName).append("object-");
        sbFileName.append(problem).append("-");
//            sbFileName.append(algorithmName).append("_");
        sbFileName.append(algorithmName).append("-");
        sbFileName.append(rand).append("_");
        sbFileName.append(pmxCrossover).append("_");
        sbFileName.append(V1mutationProbability).append("_");
        sbFileName.append(swarmSize).append("_");
        sbFileName.append(crossoverRate).append("_");
        sbFileName.append(mutationRate).append("_");
        sbFileName.append(DERate).append("_");
        sbFileName.append(DECrossoverRate).append("_");
        sbFileName.append(DEMutationRate).append("_");
        sbFileName.append(crossoverRates4worker).append("_");
        sbFileName.append(crossoverRates4machine).append("_");
        sbFileName.append(mutionRate4worker).append("_");
        sbFileName.append(mutionRate4machine).append("_");
        sbFileName.append(localsearch);
        sbFileName.append(".txt");
//        System.out.println(sbFileName.toString());


        BufferedReader data = new BufferedReader(new InputStreamReader(new FileInputStream(sbFileName.toString())));
        String lineTxt = null;
        int Test_number = 0;
        int One_Test_effectivelineNum = 0;

        Experimental_data = new float[num][200][3]; //10次实验 10个数组 //TODO
//            Experimental_data = new float[50][1000][3]; //10次实验 10个数组 //TODO
        for(int i=0;i<num;i++){
            for(int j=0;j<200;j++){
                Experimental_data[i][j][0] = -1;
                Experimental_data[i][j][1] = -1;
                Experimental_data[i][j][2] = -1;
            }
        }

        while ((lineTxt = data.readLine()) != null) {    //整个文件结束
            if (!lineTxt.equals("")){
                lineTxt = lineTxt.trim();//去除左右的空格
                String[] strcol0 = lineTxt.split("\t");
                String[] strcol = strcol0[0].split(" ");

                if(!strcol[0].equals("")){
                    Experimental_data[Test_number][One_Test_effectivelineNum][0] = Float.parseFloat(strcol[0]);
                    Experimental_data[Test_number][One_Test_effectivelineNum][1] = Float.parseFloat(strcol[1]);
                    Experimental_data[Test_number][One_Test_effectivelineNum][2] = Float.parseFloat(strcol[2]);
                    One_Test_effectivelineNum = One_Test_effectivelineNum + 1;
                }
                //忽略工厂向量
//                data.readLine();
            } else{

                //空行
                One_Test_effectivelineNum = 0;
                Test_number = Test_number + 1;

            }

        }

        data.close();
        return Experimental_data;
    }

}
