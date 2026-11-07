package org.uma.jmetal.util.research.modelglobal;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import research.dynamic.DynamicJson;

/** Optional evidence, independent of the paid path and working RNG. */
public final class PaTypedTrace implements AutoCloseable {
    private final BufferedWriter writer;
    public PaTypedTrace() {
        String target=System.getProperty("research.pa.typedTrace");
        try { writer=target==null?null:Files.newBufferedWriter(Paths.get(target),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW); }
        catch(IOException error){throw new UncheckedIOException(error);}
    }
    public void step(int generation,int slot,int step,int termIndex,PaTypedTerm term,PaTypedDonors donor,long fe) {
        if(writer==null)return;
        emit(row("generation",generation,"slot",slot,"step",step,"termIndex",termIndex,"kind",term.kind.name(),
            "jobs",term.jobs(),"donorSlot",donor.slot,"eligibleCount",donor.eligibleCount,"rank",donor.rank,"paidFE",fe));
    }
    public void emit(Map<String,Object> row) {
        if(writer==null)return;
        try{writer.write(DynamicJson.encode(row));writer.newLine();}catch(IOException error){throw new UncheckedIOException(error);}
    }
    public void close(){if(writer!=null)try{writer.close();}catch(IOException error){throw new UncheckedIOException(error);}}
    public static Map<String,Object> row(Object... pairs){
        Map<String,Object> result=new LinkedHashMap<>();for(int i=0;i<pairs.length;i+=2)result.put((String)pairs[i],pairs[i+1]);return result;
    }
    public static Map<String,Object> state(PaIndividual point){
        return row("id",point.id,"paidFE",point.paidFE,"role",point.role.name(),"hash",point.hash,
            "resources",point.genome.allocations(),"keys",point.genome.priorities(),"objectives",point.objectives());
    }
}
