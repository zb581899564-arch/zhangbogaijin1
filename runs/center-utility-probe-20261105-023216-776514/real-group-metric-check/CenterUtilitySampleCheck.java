package org.uma.jmetal.util.research.search;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Compare the new Java indicator with trusted metric values on fixed real retained groups. */
public final class CenterUtilitySampleCheck {
    private CenterUtilitySampleCheck() { }
    private static double[] vector(String value) {return Arrays.stream(value.split(",")).mapToDouble(Double::parseDouble).toArray();}
    public static void main(String[] args) throws Exception {
        int count=0;double largest=0;
        for(String line:Files.readAllLines(Paths.get(args[0]),StandardCharsets.UTF_8)) {
            String[] fields=line.split("\t",-1);String[] rows=fields[3].split(";");double[][] points=new double[rows.length][];
            for(int i=0;i<rows.length;i++)points[i]=vector(rows[i]);
            double expected=Double.parseDouble(fields[2]);double actual=CenterHypervolumeReward.volume(points,vector(fields[1]));
            largest=Math.max(largest,Math.abs(expected-actual));
            if(Math.abs(expected-actual)>1e-12)throw new AssertionError("Indicator disagreement at "+fields[0]+": "+actual+" versus "+expected);
            count++;
        }
        System.out.println("CENTER_REAL_GROUP_METRIC_CHECK_PASS cases="+count+" maxAbsoluteError="+largest+" zero decoder calls");
    }
}
