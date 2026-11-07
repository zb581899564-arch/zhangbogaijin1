package org.uma.jmetal.util.research.classic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import research.dynamic.ClassResolutionProbe;
import research.dynamic.DynamicJson;

/** Actual loaded scorer, exact crowded-tournament probabilities, no evaluations or quality-based sampling. */
public final class ParentSelectionScores {
    private ParentSelectionScores() { }
    private static int compare(NsgaSelection.Scores score,int a,int b) {
        int c=Integer.compare(score.rank[a],score.rank[b]);return c!=0?c:Double.compare(score.crowding[b],score.crowding[a]);
    }
    private static double[] probabilities(NsgaSelection.Scores score) {
        int n=score.rank.length;double[] result=new double[n],enumerated=new double[n];
        for(int i=0;i<n;i++) {
            int worse=0,ties=0;
            for(int j=0;j<n;j++)if(j!=i){int c=compare(score,i,j);if(c<0)worse++;if(c==0)ties++;}
            result[i]=(1.+2*worse+ties)/(n*(double)n);
        }
        for(int a=0;a<n;a++)for(int b=0;b<n;b++) {
            int c=compare(score,a,b);double unit=1./(n*(double)n);
            if(c<0)enumerated[a]+=unit;else if(c>0)enumerated[b]+=unit;else{enumerated[a]+=unit/2;enumerated[b]+=unit/2;}
        }
        double sum=0;for(int i=0;i<n;i++) {
            if(Math.abs(result[i]-enumerated[i])>1e-12)throw new AssertionError("Tournament probability enumeration differs");sum+=result[i];
        }
        if(Math.abs(sum-1)>1e-12)throw new AssertionError("Tournament probabilities do not sum to1");return result;
    }
    private static Map<String,Object> row(Object... fields) {
        Map<String,Object> out=new LinkedHashMap<>();for(int i=0;i<fields.length;i+=2)out.put((String)fields[i],fields[i+1]);return out;
    }
    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]);System.setProperty("dhfsp.dataDir",input.getParent().toString());
        System.setProperty("dhfsp.setupFile",args[1]);System.setProperty("dhfsp.standbyPower","1");SeededRandom.reset(12170003);
        String[] dims=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW raw=new EDHHFSPW(Integer.parseInt(dims[0]),Integer.parseInt(dims[1]),Integer.parseInt(dims[2]),Integer.parseInt(dims[3]));
        Map<String,List<PermutationSolution<Integer>>> contexts=new LinkedHashMap<>();
        for(String line:Files.readAllLines(Paths.get(args[2]),StandardCharsets.UTF_8)) {
            String[] f=line.split("\t",-1);if(!f[1].equals("CURRENT")||!f[2].equals("CENTER"))continue;
            PermutationSolution<Integer> point=raw.createSolution();String[] values=f[7].split(",");
            for(int k=0;k<3;k++)point.setObjective(k,Double.parseDouble(values[k]));
            contexts.computeIfAbsent(f[0],ignored->new ArrayList<>()).add(point);
        }
        List<Map<String,Object>> output=new ArrayList<>();NsgaSelection selection=new NsgaSelection(()->{});
        for(Map.Entry<String,List<PermutationSolution<Integer>>> item:contexts.entrySet()) {
            if(item.getValue().size()!=47)throw new AssertionError("Wrong actual freeCENTER population");
            NsgaSelection.Scores scores=selection.score(item.getValue());double[] p=probabilities(scores);
            List<Double> crowding=new ArrayList<>();for(double value:scores.crowding)crowding.add(Double.isFinite(value)?value:null);
            output.add(row("context",item.getKey(),"size",47,"rank",scores.rank,"finiteCrowdingOrNull",crowding,"probabilities",p));
        }
        if(output.size()!=6)throw new AssertionError("Missing source contexts");
        Map<String,Object> report=row("status","PASS","contexts",output,"searchFE",0,"decodes",0,
            "classIdentity",ClassResolutionProbe.capture("org.uma.jmetal.util.research.classic.NsgaSelection"));
        Files.write(Paths.get(args[3]),Collections.singletonList(DynamicJson.encode(report)),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
}
