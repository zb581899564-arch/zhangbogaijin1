package org.uma.jmetal.util.research.cooperation;

import java.util.*;

/** Untruncated paid factory objective envelopes, never queried by the search itself. */
public final class PoolRetentionTrace {
    private static final boolean ENABLED=Boolean.getBoolean("research.poolRetention.trace");
    private static final IdentityHashMap<FactoryPool,List<FactoryRecord>> envelopes=new IdentityHashMap<>();
    private static long offers,equalObjectives,dominated,accepted,nanos;
    private static int peakWidth;
    private PoolRetentionTrace() { }

    static void observe(FactoryPool pool,FactoryRecord candidate) {
        if(!ENABLED)return;
        long start=System.nanoTime();offers++;
        List<FactoryRecord> records=envelopes.computeIfAbsent(pool,key->new ArrayList<>());
        for(FactoryRecord r:records) {
            if(Arrays.equals(r.objectives,candidate.objectives)){equalObjectives++;nanos+=System.nanoTime()-start;return;}
            if(r.dominates(candidate)){dominated++;nanos+=System.nanoTime()-start;return;}
        }
        records.removeIf(candidate::dominates);records.add(candidate);accepted++;
        peakWidth=Math.max(peakWidth,records.size());nanos+=System.nanoTime()-start;
    }

    @SuppressWarnings("unchecked")
    static Map<String,Object> pool(FactoryPool[][] pools,FamilyContexts contexts,double energyScale,double wageScale) {
        Map<String,Object> result=PoolPhaseAudit.pool(pools,contexts,energyScale,wageScale);
        List<Map<String,Object>> families=(List<Map<String,Object>>)result.get("families");
        for(int family=0;family<pools.length;family++) {
            List<List<Map<String,Object>>> factories=new ArrayList<>();
            for(FactoryPool p:pools[family]) {
                List<Map<String,Object>> records=new ArrayList<>();
                for(FactoryRecord r:envelopes.getOrDefault(p,Collections.emptyList()))records.add(record(r));
                factories.add(records);
            }
            families.get(family).put("fullFactories",factories);
        }
        return result;
    }

    private static Map<String,Object> record(FactoryRecord r) {
        Map<String,Object> out=new LinkedHashMap<>();out.put("jobs",r.jobs.clone());out.put("machines",r.machines.clone());
        out.put("workers",r.workers.clone());out.put("objectives",r.objectives.clone());
        out.put("paidFE",r.paidFE);out.put("stage",r.stage);out.put("producer",r.producer);return out;
    }

    public static Map<String,Object> diagnostics() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("enabled",ENABLED);out.put("offers",offers);
        out.put("equalObjectiveRejected",equalObjectives);out.put("dominatedRejected",dominated);out.put("accepted",accepted);
        out.put("factoryEnvelopes",envelopes.size());out.put("peakObjectiveEnvelopeWidth",peakWidth);
        out.put("collectionSeconds",nanos/1e9);return out;
    }
}
