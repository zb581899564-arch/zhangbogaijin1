package org.uma.jmetal.util.research.cooperation;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.search.Direction;
import research.dynamic.DynamicJson;

/** Bounded cohort memories use the unchanged, actually loaded FactoryPool implementation. */
final class FactoryValuePools {
    private final FactoryValueRecords records;
    private final EDHHFSPW problem;
    private final Instance in;
    private final Map<String,double[]> objectives;
    private final Map<String,Map<String,FactoryPool>> libraries=new LinkedHashMap<>();
    private final Map<String,List<String[]>> inputs=new HashMap<>();
    private int queries,cases,proxyInitializations;

    FactoryValuePools(FactoryValueRecords parts, EDHHFSPW raw, Instance context, Map<String,double[]> values) {
        records=parts; problem=raw; in=context; objectives=values;
        for (String source:new String[]{"S","U"}) for (String schema:new String[]{"WHOLE_FA","JOBSET"})
            libraries.put(source+":"+schema,new LinkedHashMap<>());
    }

    private List<String[]> population(String text) {
        List<String[]> result=new ArrayList<>(); for (String token:text.split(",")) result.add(token.split(":")); return result;
    }

    private void offer(String source, List<String[]> points, boolean commit) {
        for (String schema:new String[]{"WHOLE_FA","JOBSET"}) {
            Map<String,FactoryPool> library=libraries.get(source+":"+schema); Set<String> live=new HashSet<>();
            for (String[] p:points) for (int f=0; f<in.factories(); f++) {
                String key=records.key(schema,p[0],f,in.jobs()); live.add(key);
                library.computeIfAbsent(key,k->new FactoryPool()).offer(records.points.get(p[0])[f]);
            }
            if (commit) library.keySet().retainAll(live);
        }
    }

    private List<String[]> selected(String source) {
        List<String[]> input=inputs.get(source); List<PermutationSolution<Integer>> proxies=new ArrayList<>();
        for (String[] p:input) {
            PermutationSolution<Integer> proxy=problem.createSolution(); proxyInitializations++;
            double[] values=objectives.get(p[0]); for (int k=0; k<3; k++) proxy.setObjective(k,values[k]);
            if (!p[1].equals("-1")) proxy.setAttribute(FamilyContexts.FAMILY,Integer.parseInt(p[1])); proxies.add(proxy);
        }
        List<Integer> center=new FamilyContexts(in).grouping(proxies,15,source.equals("U")).get(Direction.CENTER);
        List<String[]> result=new ArrayList<>();
        for (int family=-1; family<4; family++) {
            List<Integer> match=new ArrayList<>(); for (int index:center) if (Integer.parseInt(input.get(index)[1])==family) match.add(index);
            if (match.isEmpty()) throw new AssertionError("No planned central receiver");
            result.add(new String[]{input.get(match.get(0))[0],String.valueOf(family),source+":"+family+":FIRST"});
            result.add(new String[]{input.get(match.get(match.size()-1))[0],String.valueOf(family),source+":"+family+":LAST"});
        }
        return result;
    }

    private List<List<String>> choices(String source, String schema, String parent, double cap, List<Integer> missing) {
        List<List<String>> result=new ArrayList<>(); Map<String,FactoryPool> library=libraries.get(source+":"+schema);
        for (int f=0; f<in.factories(); f++) {
            FactoryPool old=library.get(records.key(schema,parent,f,in.jobs())),copy=new FactoryPool();
            if (old==null) missing.add(f); else for (FactoryRecord r:old.records()) copy.offer(r);
            copy.offer(records.points.get(parent)[f]); List<String> feasible=new ArrayList<>();
            for (FactoryRecord r:copy.records()) if (r.objectives[0]<=cap) feasible.add(records.ids.get(r));
            if (feasible.isEmpty()||feasible.size()>8) throw new AssertionError("Query fallback/cap invalid");
            Collections.sort(feasible); result.add(feasible);
        }
        return result;
    }

    private void query(int cycle, long fe, BufferedWriter output) throws Exception {
        Map<String,List<String[]>> unique=new LinkedHashMap<>();
        for (String source:new String[]{"S","U"}) for (String[] receiver:selected(source))
            unique.computeIfAbsent(records.physical(receiver[0])+":"+Double.toHexString(objectives.get(receiver[0])[0]),k->new ArrayList<>()).add(receiver);
        for (List<String[]> aliases:unique.values()) {
            String parent=aliases.get(0)[0]; double cap=objectives.get(parent)[0]; String qid=String.format("q%03d",++queries);
            for (String source:new String[]{"S","U"}) for (String schema:new String[]{"WHOLE_FA","JOBSET"}) {
                List<Integer> missing=new ArrayList<>(); List<List<String>> pool=choices(source,schema,parent,cap,missing);
                Map<String,Object> row=new LinkedHashMap<>(); row.put("request",qid); row.put("cycle",cycle); row.put("fe",fe);
                row.put("parent",parent); row.put("aliases",aliases); row.put("cap",cap); row.put("source",source); row.put("schema",schema);
                row.put("pool",pool); row.put("missingFactoryContexts",missing); output.write(DynamicJson.encode(row)); output.newLine(); cases++;
            }
        }
    }

    Map<String,Object> process(Path events, Path output) throws Exception {
        try (BufferedWriter writer=Files.newBufferedWriter(output,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW)) {
            for (String line:Files.readAllLines(events,StandardCharsets.UTF_8)) {
                String[] c=line.split("\t",-1); String phase=c[1]; int cycle=Integer.parseInt(c[2]); long fe=Long.parseLong(c[3]);
                if (phase.equals("QUERY")) query(cycle,fe,writer);
                else {
                    List<String[]> points=population(c[4]);
                    if (phase.equals("PRE_GLOBAL")) inputs.put(c[0],points); else offer(c[0],points,phase.equals("SURVIVORS"));
                }
            }
        }
        if (queries>40||cases>160) throw new AssertionError("Registered query bound exceeded");
        Map<String,Object> result=new LinkedHashMap<>(); result.put("deduplicatedRequests",queries); result.put("cases",cases);
        result.put("offlineObjectiveOnlyProxyInitializations",proxyInitializations); result.put("extraSearchFE",0); return result;
    }
}
