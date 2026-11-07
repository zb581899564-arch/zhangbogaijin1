package org.uma.jmetal.util.research.model;

import java.nio.ByteBuffer;
import java.security.*;
import java.util.*;

/** Read-only historical-factory reuse audit. Never returns a cached schedule to the decoder. */
public final class FactoryCachePotential {
    private static final int CAPACITY=8192;
    private static final boolean ENABLED=Boolean.getBoolean("research.factoryCache.observe");
    private static final LinkedHashMap<Key,Entry> table=new LinkedHashMap<>(32,.75f,true);
    private static Instance context; private static DynamicParameters parameters;
    private static long evaluations,requests,hits,additionalHits,saved,original,evictions,verified;
    private static long cachedIntegers,cachedOperations,peakIntegers,peakOperations;
    private FactoryCachePotential() { }
    private static final class Key {
        final int[] genes; private final int hash;
        Key(int[] value) {genes=value;hash=Arrays.hashCode(value);}
        @Override public int hashCode() {return hash;}
        @Override public boolean equals(Object other) {return other instanceof Key && Arrays.equals(genes,((Key)other).genes);}
    }
    private static final class Entry {
        final byte[] digest; final int operations;
        Entry(byte[] value,int n) {digest=value;operations=n;}
    }
    private static Key key(int f,int[] js,int[] fa,int[] ma,int[] wa) {
        int count=0;for(int value:fa)if(value==f)count++;
        int[] genes=new int[1+4*count];genes[0]=f;int q=1;
        for(int i=0;i<js.length;i++)if(fa[i]==f) {genes[q++]=js[i];genes[q++]=ma[i];genes[q++]=wa[i];genes[q++]=f;}
        return new Key(genes);
    }
    private static int recomputed(Instance in,Key key,DynamicSchedule previous) {
        int n=(key.genes.length-1)/4;if(previous==null)return n*in.stages();
        List<DynamicStep> old=previous.factorySteps(key.genes[0]);int q=0;
        while(q<n && q<old.size()) {
            DynamicStep op=old.get(q);int p=1+4*q;
            if(op.stage()!=0||op.job()!=key.genes[p]||op.machine()!=key.genes[p+1]||op.worker()!=key.genes[p+2])break;
            q++;
        }
        return q==n && old.size()==n*in.stages()?0:n*in.stages()-q;
    }
    private static byte[] digest(List<DynamicStep> steps) {
        try {
            MessageDigest digest=MessageDigest.getInstance("SHA-256");ByteBuffer buffer=ByteBuffer.allocate(120);
            for(DynamicStep op:steps) {
                buffer.clear();buffer.putInt(op.job()).putInt(op.factory()).putInt(op.stage()).putInt(op.machine()).putInt(op.worker());
                for(double value:new double[]{op.start(),op.base(),op.duration(),op.setupDuration(),op.completion(),op.u(),op.v(),op.energy(),op.labor(),op.exposure()})
                    buffer.putLong(Double.doubleToLongBits(value));
                digest.update(buffer.array(),0,buffer.position());
            }
            return digest.digest();
        }catch(NoSuchAlgorithmException error){throw new IllegalStateException(error);}
    }
    public static void observe(Instance in,DynamicParameters p,int[] js,int[] fa,int[] ma,int[] wa,
            DynamicSchedule previous,DynamicSchedule current,boolean prepared) {
        if(!ENABLED)return;
        if(prepared)throw new IllegalStateException("Prepared-prefix accounting outside this audit protocol");
        if(context==null){context=in;parameters=p;}current.validateContext(context,parameters);
        long own=0;
        for(int f=0;f<in.factories();f++) {
            requests++;Key key=key(f,js,fa,ma,wa);int count=recomputed(in,key,previous);own+=count;
            Entry old=table.get(key);
            if(old!=null) {
                hits++;
                if(count>0) {
                    if(!Arrays.equals(old.digest,digest(current.factorySteps(f))))throw new AssertionError("Same physical factory key has different timeline");
                    verified++;additionalHits++;saved+=count;
                }
            } else {
                int operations=current.factorySteps(f).size();table.put(key,new Entry(digest(current.factorySteps(f)),operations));
                cachedIntegers+=key.genes.length;cachedOperations+=operations;
                if(table.size()>CAPACITY) {
                    Map.Entry<Key,Entry> first=table.entrySet().iterator().next();
                    cachedIntegers-=first.getKey().genes.length;cachedOperations-=first.getValue().operations;
                    table.remove(first.getKey());evictions++;
                }
                peakIntegers=Math.max(peakIntegers,cachedIntegers);peakOperations=Math.max(peakOperations,cachedOperations);
            }
        }
        if(own!=current.recomputedOperations())throw new AssertionError("Parent-prefix work accounting differs");
        original+=own;evaluations++;
    }
    public static Map<String,Object> diagnostics() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("enabled",ENABLED);out.put("capacityFactoryEntries",CAPACITY);
        out.put("evaluations",evaluations);out.put("factoryRequests",requests);out.put("wholeFactoryHits",hits);
        out.put("additionalHitsBeyondParent",additionalHits);out.put("originalRecomputedOperations",original);
        out.put("potentialSavedRecomputedOperations",saved);out.put("timelineDigestsVerified",verified);
        out.put("potentialSavedFraction",original==0?0.:(double)saved/original);out.put("evictions",evictions);
        out.put("entries",table.size());out.put("peakStoredKeyIntegers",peakIntegers);out.put("peakStoredTimelineOperations",peakOperations);
        out.put("scope","Observer-only LRU history; all original decodes executed. Raw key integers and timeline operation count are not total memory measurements.");
        return out;
    }
}
