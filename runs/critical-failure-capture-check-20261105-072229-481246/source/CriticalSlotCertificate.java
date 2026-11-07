package org.uma.jmetal.util.research.search;

/** Necessary condition only: an unchanged maximizer prevents strict global makespan reduction. */
final class CriticalSlotCertificate {
    private CriticalSlotCertificate() { }
    static boolean impossible(double[] factory,int selected) {
        if(factory.length==0||selected<0||selected>=factory.length)throw new IllegalArgumentException("Invalid factory certificate");
        double maximum=Double.NEGATIVE_INFINITY;
        for(double value:factory){if(!Double.isFinite(value))throw new IllegalArgumentException("Nonfinite factory time");maximum=Math.max(maximum,value);}
        for(int f=0;f<factory.length;f++)if(f!=selected&&factory[f]==maximum)return true;return false;
    }
    static void fixtures() {
        if(!impossible(new double[]{5,10,3},0)||impossible(new double[]{5,10,3},1)
            ||!impossible(new double[]{10,10,3},0)||!impossible(new double[]{10,10,3},1)
            ||!impossible(new double[]{10,10,3},2)||impossible(new double[]{10},0))
            throw new AssertionError("Critical factory certificate fixture failed");
    }
}
