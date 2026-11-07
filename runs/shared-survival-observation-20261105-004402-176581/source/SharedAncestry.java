package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Compact paid-parent genealogy. The last composed ancestor is an association, not genetic or causal credit. */
final class SharedAncestry {
    static final String PAID="observation.sharedSurvival.paid";
    private final int[] parent, root;
    private final double[][] objectives;
    private final Map<Integer,Root> roots=new LinkedHashMap<>();
    private final Map<String,Long> counts=new LinkedHashMap<>();
    private int last;
    SharedAncestry(int limit) {
        parent=new int[limit+1]; root=new int[limit+1]; objectives=new double[3][limit+1];
    }
    static int id(PermutationSolution<?> s) {
        Object value=s.getAttribute(PAID);return value==null?0:((Number)value).intValue();
    }
    int last() {return last;}
    int root(int paid) {return paid==0?0:root[paid];}
    int parent(int paid) {return parent[paid];}
    boolean composed(int paid) {return roots.containsKey(paid);}
    void count(String key) {counts.put(key,counts.getOrDefault(key,0L)+1);}
    void paid(PermutationSolution<?> s,int paid,int from,boolean composed,String stage,boolean admitted) {
        if(paid!=last+1 || from<0 || from>=paid || id(s)!=paid)throw new AssertionError("Broken paid provenance");
        if(!stage.equals("initialization") && from==0)throw new AssertionError("Noninitial paid proposal lost parent");
        last=paid; parent[paid]=from;
        for(int k=0;k<3;k++)objectives[k][paid]=s.getObjective(k);
        root[paid]=composed?paid:root[from];
        count("paid."+stage); if(admitted)count("externalAdmission."+stage);
        if(composed) {
            roots.put(paid,new Root(paid,from,s.getAttribute("cooperation.family"),admitted));
            count("composedPaid"); if(admitted)count("composedExternalAdmission");
        } else if(root[paid]>0) {
            Root r=roots.get(root[paid]);r.descendantPaid++;
            if(admitted) {
                r.descendantAdmissions++;
                boolean any=false,dominates=true,strict=false;
                for(int k=0;k<3;k++) {
                    any|=objectives[k][paid]<objectives[k][r.fe];
                    dominates&=objectives[k][paid]<=objectives[k][r.fe];
                    strict|=objectives[k][paid]<objectives[k][r.fe];
                }
                if(any)r.admissionsImprovingAnyRootObjective++;
                if(dominates&&strict)r.admissionsDominatingRoot++;
            }
        }
    }
    void selected(int fe,boolean repeatedLineage,boolean child) {
        if(root[fe]==0)return;
        Root r=roots.get(root[fe]);r.selectedExposures++;
        if(child&&fe==r.fe) {
            r.directChildSelected=true;
            if(repeatedLineage)r.directChildSelectedWithSibling=true;
        }
    }
    void localEntry(int fe) {if(root[fe]>0)roots.get(root[fe]).localVisits++;}
    void generationEnd(int fe) {if(root[fe]>0)roots.get(root[fe]).generationEndExposures++;}
    Map<String,Object> finish(List<PermutationSolution<Integer>> archive) {
        List<Map<String,Object>> finalPoints=new ArrayList<>();
        for(PermutationSolution<Integer> s:archive) {
            int fe=id(s);if(fe<=0||fe>last)throw new AssertionError("Final archive lost paid provenance");
            if(root[fe]>0)roots.get(root[fe]).finalPoints++;
            Map<String,Object> p=new LinkedHashMap<>();p.put("paidFE",fe);p.put("parentFE",parent[fe]);
            p.put("lastComposedAncestorFE",root[fe]);p.put("directComposition",composed(fe));p.put("objectives",s.getObjectives());
            finalPoints.add(p);
        }
        List<Map<String,Object>> rootRows=new ArrayList<>();for(Root r:roots.values())rootRows.add(r.row());
        Map<String,Object> out=new LinkedHashMap<>();out.put("successfulFE",last);out.put("counts",counts);
        out.put("roots",rootRows);out.put("finalPoints",finalPoints);return out;
    }
    private static final class Root {
        final int fe,parentFE;final Object family;final boolean admitted;
        boolean directChildSelected,directChildSelectedWithSibling;
        long descendantPaid,descendantAdmissions,admissionsImprovingAnyRootObjective,admissionsDominatingRoot;
        long selectedExposures,localVisits,generationEndExposures,finalPoints;
        Root(int fe,int parent,Object family,boolean admitted) {this.fe=fe;parentFE=parent;this.family=family;this.admitted=admitted;}
        Map<String,Object> row() {
            Map<String,Object> r=new LinkedHashMap<>();r.put("fe",fe);r.put("parentFE",parentFE);r.put("family",family);
            r.put("directExternalAdmission",admitted);r.put("directChildSelected",directChildSelected);
            r.put("directChildSelectedWithSibling",directChildSelectedWithSibling);r.put("descendantPaid",descendantPaid);
            r.put("descendantAdmissions",descendantAdmissions);r.put("admissionsImprovingAnyRootObjective",admissionsImprovingAnyRootObjective);
            r.put("admissionsDominatingRoot",admissionsDominatingRoot);r.put("selectedExposures",selectedExposures);
            r.put("localVisits",localVisits);r.put("generationEndExposures",generationEndExposures);r.put("finalPoints",finalPoints);return r;
        }
    }
}
