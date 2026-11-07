package org.uma.jmetal.util.research.modelglobal;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.search.TrajectoryTrace;
import org.uma.jmetal.util.research.search.GomRecords;
import research.dynamic.DynamicJson;

/** Same read-only bridge plus bounded complete PA model snapshots; no random/evaluation calls. */
public final class PaTrajectoryBridge {
    private static int models;
    private PaTrajectoryBridge() { }
    public static void proposal(int generation,int slot,PaIndividual parent,PaIndividual donor) {
        TrajectoryTrace.paProposal(parent.point,parent.role,slot,generation,donor.point);
    }
    public static void population(String label,List<PaIndividual> values) {
        List<PermutationSolution<Integer>> points=new ArrayList<>();
        for(PaIndividual value:values)points.add(value.point);
        TrajectoryTrace.population(label,points);
        if(!label.equals("PA_MODEL"))return;
        List<Map<String,Object>> rows=new ArrayList<>();
        for(int i=0;i<values.size();i++) {
            PaIndividual value=values.get(i);Map<String,Object> row=GomRecords.raw(value.point);
            row.putAll(GomRecords.row("slot",i,"role",value.role.name(),"paidFE",value.paidFE,
                "resources",value.genome.allocations(),"keys",value.genome.priorities()));rows.add(row);
        }
        Path target=Paths.get(System.getProperty("research.midSupport.models"));
        try { Files.write(target,(DynamicJson.encode(GomRecords.row("model",++models,"points",rows))+"\n").getBytes(StandardCharsets.UTF_8),
                StandardOpenOption.CREATE,StandardOpenOption.APPEND); }
        catch(IOException error){throw new UncheckedIOException(error);}
    }
    public static void program(int slot,PaIndividual value){TrajectoryTrace.program(value.point,slot,value.role);}
}
