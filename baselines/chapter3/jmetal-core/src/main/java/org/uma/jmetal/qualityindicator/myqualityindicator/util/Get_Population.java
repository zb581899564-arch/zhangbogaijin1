package org.uma.jmetal.qualityindicator.myqualityindicator.util;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.Arrays;

public class Get_Population {

    private float[][][] Experimental_data;
    private float object1max=-1;
    private float object1min=Float.MAX_VALUE;
    private float object2max=-1;
    private float object2min=Float.MAX_VALUE;

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
                '}';
    }

    public String MaxandMintoString() {
        return object1max + "," + object1min + "," + object2max +"," + object2min;
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

        BufferedReader data = new BufferedReader(new InputStreamReader(new FileInputStream(filename+problem+"-"+algorithm+".txt")));
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
    public float[][][] Read_Experimental_data(String filename,String problem,String algorithm, double R, int swarmsize, int num) throws IOException {
        Experimental_data = new float[num][100][2]; //30次实验 30个数组
        for(int i=0;i<num;i++){
            for(int j=0;j<100;j++){
                Experimental_data[i][j][0] = -1;
                Experimental_data[i][j][1] = -1;
            }
        }

        BufferedReader data = new BufferedReader(new InputStreamReader(new FileInputStream(filename+problem+"_"+algorithm+"_"+R+"_"+swarmsize+".txt")));
        String lineTxt = null;
        int Test_number = 0;
        int One_Test_effectivelineNum = 0;
        while ((lineTxt = data.readLine()) != null) {
            lineTxt = lineTxt.trim();//去除左右的空格
            String[] strcol = lineTxt.split(" ");
            if(!strcol[0].equals("")){
                Experimental_data[Test_number][One_Test_effectivelineNum][0] = Float.parseFloat(strcol[0]);
                Experimental_data[Test_number][One_Test_effectivelineNum][1] = Float.parseFloat(strcol[1]);
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



}
