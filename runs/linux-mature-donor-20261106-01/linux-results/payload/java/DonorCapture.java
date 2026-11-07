package org.uma.jmetal.util.research.search;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.modelglobal.FourVectors;
import research.dynamic.DynamicJson;

/** Observation only: one prespecified mature pre-global population and its paid proposals. */
public final class DonorCapture {
    private static BufferedWriter points;
    private static Path out;
    private static long before, after, count, shared;
    private static boolean active, done;
    private DonorCapture() { }
    public static void pre(Map<Direction,List<Particle>> groups) {
        String folder=System.getProperty("research.donor.capture");
        if(folder==null||active||done)return;
        long fe=GomRunScope.require().run.budget().successful();
        if(fe<Long.getLong("research.donor.captureAt",250000L))return;
        before=fe;out=Paths.get(folder);
        try {
            Files.createDirectories(out);
            points=Files.newBufferedWriter(out.resolve("points.tsv"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
            int index=0;
            for(Direction role:Direction.values())for(Particle p:groups.get(role))write("P",index++,fe,role,p.current);
            if(index!=100)throw new AssertionError("Expected100receivers");
            active=true;
        }catch(IOException e){throw new UncheckedIOException(e);}
    }
    public static void paid(PermutationSolution<Integer> p,boolean composed,Direction role) {
        if(!active)return;
        long fe=GomRunScope.require().run.budget().successful();
        try{write(composed?"S":"G",count++,fe,role,p);if(composed)shared++;}
        catch(IOException e){throw new UncheckedIOException(e);}
    }
    public static void post() {
        if(!active)return;
        after=GomRunScope.require().run.budget().successful();
        if(count!=5000||after-before!=count)throw new AssertionError("Incomplete global supply block");
        try {
            points.close();
            double[][] archive=GomRunScope.require().archive();
            Files.write(out.resolve("background.json"),DynamicJson.encode(archive).getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
            try(BufferedWriter writer=Files.newBufferedWriter(out.resolve("background.tsv"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW)) {
                for(double[] p:archive)writer.write(p[0]+"\t"+p[1]+"\t"+p[2]+"\n");
            }
            Map<String,Object> receipt=GomRecords.row("passed",true,"beforeGlobalFE",before,"afterGlobalFE",after,
                "receivers",100,"globalPaidCandidates",count,"sharedPaidCandidates",shared,"ordinaryPaidCandidates",count-shared,
                "backgroundPoints",archive.length,"pointSource","Already paid by the recorded fee; P uses upper-bound paidByFE, not earliest birth",
                "readOnly",true,"captureThreshold",Long.getLong("research.donor.captureAt",250000L),"loaded",
                research.dynamic.ClassResolutionProbe.capture("org.uma.jmetal.util.research.search.DonorCapture","org.uma.jmetal.util.research.search.CanonicalHmopso"));
            Files.write(out.resolve("capture.json"),DynamicJson.encode(receipt).getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
        }catch(Exception e){throw new IllegalStateException("Capture finalization failed",e);}
        active=false;done=true;
    }
    private static void write(String kind,long index,long fe,Direction role,PermutationSolution<Integer> p)throws IOException {
        FourVectors v=GomRecords.vectors(p);Object family=p.getAttribute("cooperation.family");double[] o=p.getObjectives();
        points.write(kind+"\t"+index+"\t"+fe+"\t"+role.name()+"\t"+(family==null?-1:family)+"\t"+o[0]+","+o[1]+","+o[2]);
        for(int[] a:new int[][]{v.jobs(),v.factories(),v.machines(),v.workers()}) {
            points.write("\t");for(int i=0;i<a.length;i++){if(i>0)points.write(",");points.write(Integer.toString(a[i]));}
        }
        points.newLine();
    }
}
