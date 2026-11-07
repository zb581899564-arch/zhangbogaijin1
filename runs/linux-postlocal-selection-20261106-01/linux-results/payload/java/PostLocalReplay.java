package org.uma.jmetal.util.research.search;

import java.io.*;
import java.nio.file.Path;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.RunContext;

/** Mature-state timing-of-selection probe; it never replaces the default algorithm. */
public final class PostLocalReplay implements Algorithm<Object> {
    private static final long serialVersionUID=1L;
    public static final long POLISH_SEED_XOR=0L,RAW_FIRST_SEED_XOR=0L,
        RAW_SECOND_SEED_XOR=0x9e3779b97f4a7c15L,FINAL_SEED_XOR=0x51d0a7e3L;
    private final PostLocalData data;
    private final Instance instance;
    private final String mode;
    private final long seed;
    private final Path output;
    private final PostLocalEvidence evidence;
    private final GomRunScope scope;
    private final PostLocalArchives archives;
    private final PostLocalPass passes;
    private final PostLocalSelection selection=new PostLocalSelection();
    private List<PostLocalData.Member> finalPopulation;

    public PostLocalReplay(RunContext<PermutationSolution<Integer>> run,Problem<PermutationSolution<Integer>> raw,
            Instance input,Path imported,Path out,String arm,long randomSeed)throws IOException {
        instance=input;output=out;mode=arm;seed=randomSeed;
        boolean nativeObserver=Boolean.getBoolean("research.postlocal.nativeObserver");
        if(nativeObserver&&!mode.equals("RAW_ROLE"))throw new IllegalArgumentException("Native observer bridge requires RAW_ROLE");
        data=new PostLocalData(imported,raw,instance);evidence=new PostLocalEvidence(output,instance.factories());
        scope=new GomRunScope(run,evidence,phase->{});archives=new PostLocalArchives(scope,evidence,data,nativeObserver);
        passes=new PostLocalPass(run,instance,scope,archives,evidence);
        PostLocalEvidence.write(output.resolve("imports.json"),GomRecords.row("parents",PostLocalData.records(data.parents),
            "children",PostLocalData.records(data.children),"A0",data.background,"initialPublicArchive",scope.archive(),
            "registryProvenance","Imported source fees are negative; positive registry fees belong to this probe"));
        FirstStageCatalog catalog=new FirstStageCatalog(instance);List<int[]> tuples=new ArrayList<>();
        for(int index=0;index<catalog.size();index++)tuples.add(catalog.tuple(index));
        PostLocalEvidence.write(output.resolve("catalog.json"),GomRecords.row("jobs",instance.jobs(),"factories",instance.factories(),"tuples",tuples));
    }
    public void observed(PermutationSolution<Integer> point,long fe){archives.observed(point,fe);}
    public Map<String,Object> validateImports(DynamicParameters params) {
        long start=System.nanoTime(),count=0;
        if(Boolean.getBoolean("research.postlocal.importQA")) {
            List<PostLocalData.Member> all=new ArrayList<>(data.parents);all.addAll(data.children);
            for(PostLocalData.Member member:all) {
                FourVectors v=GomRecords.vectors(member.particle.current);
                DynamicSchedule full=DynamicDecoder.full(instance,params,v.jobs(),v.factories(),v.machines(),v.workers(),()->{});
                DynamicValidator.validate(instance,params,full);
                if(!Arrays.equals(full.objectives(),member.particle.current.getObjectives()))throw new AssertionError("Imported objectives disagree");count++;
            }
        }
        return GomRecords.row("fullDecodes",count,"offlineSeconds",(System.nanoTime()-start)/1e9);
    }
    public void run() {
        List<PostLocalData.Member> selected;
        if(mode.equals("RAW_ROLE")) {
            selected=select(data.parents,data.children);
            selected=passes.execute("RAW_1",selected,seed^RAW_FIRST_SEED_XOR,null);
            selected=passes.execute("RAW_2",selected,seed^RAW_SECOND_SEED_XOR,null);
        } else {
            List<PostLocalData.Member> parents=passes.execute("P_POLISH",data.parents,seed^POLISH_SEED_XOR,data.background);
            List<PostLocalData.Member> children=passes.execute("C_POLISH",data.children,seed^POLISH_SEED_XOR,data.background);
            selected=select(parents,children);
        }
        finalPopulation=passes.execute("FINAL",selected,seed^FINAL_SEED_XOR,null);
    }
    private List<PostLocalData.Member> select(List<PostLocalData.Member> parents,List<PostLocalData.Member> children) {
        List<PostLocalData.Member> selected=selection.select(parents,children);
        evidence.record(GomRecords.row("kind","selection","mode",mode,"groups",selection.groups,"afterPopulation",PostLocalData.records(selected)));
        try{PostLocalEvidence.write(output.resolve("selection.json"),GomRecords.row("mode",mode,"policy",GlobalGroupPolicy.diagnostics(),
            "groups",selection.groups,"afterPopulation",PostLocalData.records(selected)));
            PostLocalEvidence.write(output.resolve("selected.json"),PostLocalData.records(selected));}
        catch(IOException error){throw new UncheckedIOException(error);}return selected;
    }
    public Map<String,Object> finish()throws IOException {
        Map<String,Object> receipt=GomRecords.row("passes",passes.receipts,"native",scope.diagnostics(),"allPaid",archives.receipt(),
            "evidence",evidence.receipt(),"selectionComplete",!selection.groups.isEmpty(),"finalPopulationComplete",finalPopulation!=null);
        try {
            PostLocalEvidence.write(output.resolve("after.json"),finalPopulation==null?passes.latestPopulation():PostLocalData.records(finalPopulation));
            PostLocalEvidence.write(output.resolve("front.json"),scope.archive());
            PostLocalEvidence.write(output.resolve("passes.json"),passes.receipts);
            PostLocalEvidence.write(output.resolve("probe.json"),receipt);
        } finally {evidence.close();}
        return receipt;
    }
    public static void write(Path path,Object value)throws IOException{PostLocalEvidence.write(path,value);}
    public static long passBudget(Instance instance){return PostLocalPass.budget(instance);}
    public Object getResult(){return scope.archive();}
    public String getName(){return "MATURE_POSTLOCAL_SELECTION_"+mode;}
    public String getDescription(){return "Equal three-native-pass timing-of-selection probe, with unchanged local role semantics";}
}
