package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.modelglobal.PaInternalArchive;

/** Separates pass-local acceptance history from the never-reset public paid union. */
final class PostLocalArchives {
    final GomRunScope scope;
    private final PostLocalEvidence evidence;
    private final boolean nativeObserver;
    private PaInternalArchive internal;
    private long paid;
    PostLocalArchives(GomRunScope value,PostLocalEvidence sink,PostLocalData data,boolean nativeMode) {
        scope=value;evidence=sink;nativeObserver=nativeMode;
        for(double[] p:data.background)scope.archive.offer(p);
        double[][] originalA0=scope.archive();
        List<PostLocalData.Member> imports=new ArrayList<>(data.parents);imports.addAll(data.children);
        for(PostLocalData.Member member:imports) {
            PermutationSolution<Integer> point=member.particle.current;
            scope.archive.offer(point.getObjectives());
            // Negative provenance means paid in the source run, never this probe's FE.
            scope.registry.put(point,-Math.max(1L,member.sourcePaidBy),GomRecords.rawHash(point));
        }
        if(!Arrays.deepEquals(originalA0,scope.archive()))throw new IllegalArgumentException("A0 does not cover all imported P/C points");
    }
    void begin(List<double[]> independentA0) {
        internal=new PaInternalArchive();
        if(independentA0==null)for(double[] p:scope.archive())internal.offer(p);
        else for(double[] p:independentA0)internal.offer(p);
    }
    void observed(PermutationSolution<Integer> point,long fe) {
        if(internal==null)throw new AssertionError("Paid observation before pass archive creation");
        String hash=GomRecords.rawHash(point);PaInternalArchive.Flags privateFlags,publicFlags;
        if(nativeObserver) {
            scope.observed(point,fe,hash);publicFlags=scope.lastFlags;privateFlags=internal.offer(point.getObjectives());
            if(!flags(privateFlags).equals(flags(publicFlags)))throw new AssertionError("RAW native/private archive bridge differs");
        } else {
            publicFlags=scope.archive.offer(point.getObjectives());privateFlags=internal.offer(point.getObjectives());
            scope.lastFlags=privateFlags;scope.lastPaid=point;scope.registry.put(point,fe,hash);
            evidence.record(GomRecords.row("kind","paid","fe",fe,"objectives",point.getObjectives().clone(),"rawHash",hash,
                "dominated",privateFlags.dominated,"equal",privateFlags.equal,"fresh",privateFlags.fresh,
                "before",privateFlags.before,"after",privateFlags.after));
        }
        paid++;
        evidence.record(GomRecords.row("kind","paidDetail","fe",fe,"raw",GomRecords.raw(point),"rawHash",hash,
            "privateFlags",flags(privateFlags),"publicFlags",flags(publicFlags),"acceptanceArchive",nativeObserver?"NATIVE_PUBLIC":"PRIVATE_PASS"));
    }
    double[][] internal(){return internal==null?new double[0][]:internal.snapshot();}
    Map<String,Object> receipt() {
        return GomRecords.row("successfulObserved",paid,"importedAlreadyPaid",200,"resultBasis","A0 plus P100 plus C100 plus every successful probe evaluation",
            "nativeObserver",nativeObserver,"publicArchive",scope.archive(),"lastInternalArchive",internal());
    }
    private static Map<String,Object> flags(PaInternalArchive.Flags f) {
        return GomRecords.row("dominated",f.dominated,"equal",f.equal,"fresh",f.fresh,"before",f.before,"after",f.after);
    }
}
