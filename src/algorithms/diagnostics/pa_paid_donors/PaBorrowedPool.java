package org.uma.jmetal.util.research.modelglobal;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.Direction;
import research.dynamic.DynamicJson;

/** Past paid complete schedules only. Pool views never enter the working population or archive for free. */
public final class PaBorrowedPool {
    private static Instance validationInstance;
    private static DynamicParameters validationParameters;
    public static void validation(Instance instance,DynamicParameters parameters){validationInstance=instance;validationParameters=parameters;}
    private final PaPaidEvaluation evaluation;
    private final boolean graft=System.getProperty("research.pa.borrowMode","NONE").equals("GRAFT");
    private final List<PaIndividual> original=new ArrayList<>(),view=new ArrayList<>();
    private final BufferedWriter trace;
    private final long seed=Long.parseLong(System.getProperty("research.pa.borrowSeed","0"));
    private long externalReads,liveReads,fullQA,neutralViews;

    PaBorrowedPool(PaPaidEvaluation evaluator,PaIndividual template){
        evaluation=evaluator;
        if(!Arrays.asList("NONE","GRAFT").contains(System.getProperty("research.pa.borrowMode","NONE")))throw new IllegalArgumentException("Unknown borrowmode");
        String file=System.getProperty("research.pa.borrowTSV"),audit=System.getProperty("research.pa.borrowTrace");
        try{
            trace=audit==null?null:Files.newBufferedWriter(Paths.get(audit),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
            if(file!=null)for(String line:Files.readAllLines(Paths.get(file),StandardCharsets.UTF_8)){
                String[] f=line.split("\t"),obj=f[3].split(",");double[] objectives=new double[3];for(int k=0;k<3;k++)objectives[k]=Double.parseDouble(obj[k]);
                long born=Long.parseLong(f[2]);if(born<1 || born>50000)throw new IllegalArgumentException("Teacher not paid by50k");
                FourVectors genes=new FourVectors(integers(f[4]),integers(f[5]),integers(f[6]),integers(f[7]));
                PaIndividual point=evaluation.borrowed(genes,objectives,born,-1-original.size(),template);
                original.add(point);check(point);
            }
            if(file!=null && original.size()!=100)throw new IllegalArgumentException("Expected100memoryslots");
            view.addAll(original);emit(-1);
        }catch(IOException error){throw new UncheckedIOException(error);}
    }
    private static int[] integers(String text){String[] parts=text.split(",");int[] values=new int[parts.length];for(int i=0;i<parts.length;i++)values[i]=Integer.parseInt(parts[i]);return values;}
    private void check(PaIndividual point){
        if(!Boolean.getBoolean("research.pa.borrowQA"))return;
        if(validationInstance==null || validationParameters==null)throw new IllegalStateException("BorrowQAcontextmissing");
        FourVectors genes=point.genome.toVectors();
        DynamicSchedule full=DynamicDecoder.full(validationInstance,validationParameters,genes.jobs(),genes.factories(),genes.machines(),genes.workers(),()->{});
        DynamicValidator.validate(validationInstance,validationParameters,full);
        if(!Arrays.equals(full.objectives(),point.objectives()))throw new AssertionError("Past source objective differs");
        fullQA++;
    }
    void refresh(int generation){
        view.clear();
        for(int i=0;i<original.size();i++){
            PaIndividual source=original.get(i);Random noise=new Random(seed ^ (0x632be59bd9b4e019L*generation+0x9e3779b97f4a7c15L*i));
            TypedScheduleGenome genes=FactoryKeyReencoder.apply(evaluation.catalog(),source.genome,noise);
            PaIndividual alias=evaluation.borrowedView(genes,source);view.add(alias);neutralViews++;check(alias);
        }
        emit(generation);
    }
    public static final class Choice {
        public final int slot;public final PaIndividual point;
        Choice(int index,PaIndividual value){slot=index;point=value;}
    }
    Choice choose(List<PaIndividual> population,int receiver){
        int live=population.size()-1,extra=graft?view.size():0;
        int draw=SeededRandom.current().nextInt(live+extra);
        if(draw<live){int slot=draw>=receiver?draw+1:draw;liveReads++;return new Choice(slot,population.get(slot));}
        int index=draw-live;externalReads++;return new Choice(-1-index,view.get(index));
    }
    private void emit(int generation){
        if(trace==null)return;
        List<Map<String,Object>> points=new ArrayList<>();
        for(PaIndividual point:view){Map<String,Object> row=new LinkedHashMap<>();row.put("id",point.id);row.put("paidFE",point.paidFE);row.put("role",point.role.name());
            row.put("hash",point.hash);row.put("resources",point.genome.allocations());row.put("keys",point.genome.priorities());row.put("objectives",point.objectives());points.add(row);}
        Map<String,Object> row=new LinkedHashMap<>();row.put("generation",generation);row.put("points",points);
        try{trace.write(DynamicJson.encode(row));trace.newLine();}catch(IOException error){throw new UncheckedIOException(error);}
    }
    Map<String,Object> finish(){
        if(trace!=null)try{trace.close();}catch(IOException error){throw new UncheckedIOException(error);}
        Map<String,Object> result=new LinkedHashMap<>();result.put("borrow.mode",graft?"GRAFT":"NONE");result.put("borrow.memory",original.size());
        result.put("borrow.externalReads",externalReads);result.put("borrow.liveReads",liveReads);result.put("borrow.neutralViews",neutralViews);result.put("borrow.fullQA",fullQA);return result;
    }
}
