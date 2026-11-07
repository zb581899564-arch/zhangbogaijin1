package org.uma.jmetal.util.research.search;

/** Closed-form geometry and equal-centroid counterexample; no scheduling-model calls. */
public final class CenterUtilityChecks {
    private CenterUtilityChecks() { }
    private static void equal(double actual,double expected) {
        if(Math.abs(actual-expected)>1e-12)throw new AssertionError(actual+" != "+expected);
    }
    public static void main(String[] args) {
        double[] ref={1,1,1};
        equal(CenterHypervolumeReward.volume(new double[][]{{.5,.5,.5}},ref),.125);
        equal(CenterHypervolumeReward.volume(new double[][]{{.5,.5,.5},{.25,.75,.5}},ref),.15625);
        equal(CenterHypervolumeReward.volume(new double[][]{{.25,.75,.5},{.5,.5,.5},{.5,.5,.5},{2,0,0}},ref),.15625);
        equal(CenterHypervolumeReward.volume(new double[0][],ref),0);
        double[][] before={{.2,.8,.5},{.8,.2,.5}},after={{.4,.6,.5},{.6,.4,.5}};
        equal(CenterHypervolumeReward.volume(before,ref),.14);equal(CenterHypervolumeReward.volume(after,ref),.16);
        for(int k=0;k<3;k++)equal(before[0][k]+before[1][k],after[0][k]+after[1][k]);
        System.out.println("CENTER_UTILITY_CHECKS_PASS exact boxes, duplicates, order, empty/outside box and equal-centroid unequal-HV; zero decoder calls");
    }
}
