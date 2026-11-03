package org.uma.jmetal.util.research.modelchecks;

import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;

/** Transcribed Tables 4/5, with standby power explicitly supplied because both tables omit it. */
public final class PaperExamples {
    private PaperExamples() { }
    public static Instance chapter3(double standby) {
        double[][] st = {{8,4},{3,5},{7,4},{6,3},{4,3}};
        double[][][] speed = {{{1,1.2},{1.2}},{{1},{1,1.2}}};
        double[][][] power = {{{7,10},{6}},{{7},{6,8}}};
        double[][][] we = {{{1.2,.8,1},{1.2,.8,1}},{{1.1,.9,1.3},{1.1,.9,1.3}}};
        double[][][] cost = {{{12,8,10},{12,8,10}},{{11,9,13},{11,9,13}}};
        return new Instance("JMS-Tables4-5", ModelKind.CHAPTER3_FIXED_WORKER, st, new double[5][2],
                speed, power, fill(speed, standby), we, cost, "JMS 85(2026) pp5-6 Tables4-5; standby=" + standby + " explicit assumption");
    }
    public static Instance chapter4(double standby) {
        double[][] st = {{10,8},{16,11},{12,12},{9,14},{10,16},{8,15},{13,18},{14,12},{16,10},{9,9}};
        double[][] sut = {{1,1},{3,2},{2,3},{1,3},{2,3},{2,2},{2,1},{2,2},{3,1},{2,1}};
        double[][][] speed = {{{1,1.2,1.3},{1.2,1.1}},{{1,1.1},{1,1.2,.9}}};
        double[][][] power = {{{7,10,12},{9,8}},{{7,8},{7,8,6}}};
        double[][][] we = {{{1.2,1},{.9,1.1}},{{1.1,1.2},{1.2,.9}}};
        double[][][] cost = {{{12,10},{9,11}},{{11,12},{12,9}}};
        return new Instance("ESWA-Tables4-5", ModelKind.CHAPTER4_DUAL_RESOURCE, st, sut,
                speed, power, fill(speed, standby), we, cost, "ESWA306(2026)130934 pp7-8 Tables4-5 actual SUT; standby=" + standby + " explicit assumption");
    }
    private static double[][][] fill(double[][][] shape, double value) {
        double[][][] result = new double[shape.length][][];
        for (int f = 0; f < shape.length; f++) {
            result[f] = new double[shape[f].length][];
            for (int k = 0; k < shape[f].length; k++) {
                result[f][k] = new double[shape[f][k].length]; java.util.Arrays.fill(result[f][k], value);
            }
        }
        return result;
    }
}
