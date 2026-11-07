package org.uma.jmetal.util.research.modelglobal;

import java.util.*;
import java.util.function.Consumer;
import org.uma.jmetal.util.research.search.Direction;

/** Isolated policy only: original archives, donors, genome operations and role labels stay native. */
public final class PaRegionalPolicy {
    private static Consumer<Map<String,Object>> observer=unused->{ };
    private static PaRegionalPolicy last;
    private final String mode;private final CenterTargets targets;
    private long observed,central,boundary,differences;
    private PaRegionalPolicy(String label) {
        mode=label;
        if(!Arrays.asList("OFF","REGIONAL","NO_SPECIALIST").contains(mode))throw new IllegalArgumentException("Unknown regional mode");
        if(mode.equals("OFF"))targets=null;
        else {
            String[] fields=System.getProperty("research.paRegional.scale","").split(",");
            if(fields.length!=3)throw new IllegalArgumentException("Three frozen scales required");
            targets=new CenterTargets(new double[]{Double.parseDouble(fields[0]),Double.parseDouble(fields[1]),Double.parseDouble(fields[2])});
        }
    }
    public static PaRegionalPolicy configured(){last=new PaRegionalPolicy(System.getProperty("research.paRegional.mode","OFF"));return last;}
    public static void observe(Consumer<Map<String,Object>> listener){observer=Objects.requireNonNull(listener);}
    public static Map<String,Object> diagnostics(){return last==null?Collections.emptyMap():last.summary();}
    public void initial(int slot,PaIndividual point) {
        if(targets==null)return;
        Direction expected=slot<15?Direction.MAKESPAN:slot<70?Direction.CENTER:slot<85?Direction.ENERGY:Direction.WORKER_COST;
        if(point.role!=expected||point.paidFE!=++observed)throw new AssertionError("Native initial roles/paid order required");
        targets.initial(slot,point.objectives());
        if(targets.ready()) {
            Map<String,Object> row=row("targets");row.put("paidFE",observed);row.put("columns",targets.columns());
            row.put("directions",CenterTargets.directions());row.put("ideal",targets.ideal());row.put("assignmentCost",targets.assignmentCost());observer.accept(row);
        }
    }
    public void paid(PaIndividual child) {
        if(targets==null)return;
        if(!targets.ready()||child.paidFE!=++observed)throw new AssertionError("One policy observation per paid candidate required");
        targets.observe(child.objectives());
    }
    public boolean accepts(int slot,PaIndividual parent,PaIndividual child,PaInternalArchive.Flags flags,boolean nativeAccepted) {
        if(targets==null)return nativeAccepted;
        boolean accepted;Double old=null,next=null;
        if(parent.role==Direction.CENTER) {
            int[] w=targets.weight(slot);old=targets.score(parent.objectives(),w);next=targets.score(child.objectives(),w);
            accepted=next<=old;central++;
        } else {
            accepted=mode.equals("NO_SPECIALIST")?PaInternalArchive.weaklyDominates(child.objectives(),parent.objectives())||!flags.dominated:nativeAccepted;boundary++;
        }
        if(accepted!=nativeAccepted)differences++;
        Map<String,Object> row=row("decision");row.put("paidFE",child.paidFE);row.put("slot",slot);row.put("role",parent.role.name());
        row.put("parentId",parent.id);row.put("childId",child.id);row.put("ideal",targets.ideal());row.put("parentScore",old);row.put("childScore",next);
        row.put("nativeAccepted",nativeAccepted);row.put("accepted",accepted);observer.accept(row);return accepted;
    }
    private Map<String,Object> row(String kind){Map<String,Object> row=new LinkedHashMap<>();row.put("kind",kind);row.put("mode",mode);return row;}
    private Map<String,Object> summary() {
        Map<String,Object> row=row("summary");row.put("observedPaid",observed);row.put("targetsReady",targets!=null&&targets.ready());
        row.put("centerComparisons",central);row.put("boundaryComparisons",boundary);row.put("nativeDecisionDifferences",differences);
        row.put("ideal",targets==null?null:targets.ideal());return row;
    }
}
