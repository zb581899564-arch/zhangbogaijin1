package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.classic.*;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.runtime.RunContext;
import org.uma.jmetal.util.research.search.*;

/** All algorithm-specific construction happens inside RunContext's clock. */
final class PaCapabilitySearch implements Algorithm<Object> {
    private static final long serialVersionUID = 1L;
    private final String arm;
    private final RunContext<PermutationSolution<Integer>> run;
    private final Instance instance;
    private final DynamicParameters fatigue;
    private final DynamicEvaluation decoder;
    private DynamicSearch frozen;
    private PlainNsgaAlgorithm plain;
    private PaLightPopulation counts;
    private PaPopulation population;

    PaCapabilitySearch(String label, RunContext<PermutationSolution<Integer>> context, Instance value, DynamicParameters params, DynamicEvaluation evaluation) {
        arm = label; run = context; instance = value; fatigue = params; decoder = evaluation;
    }
    public void run() {
        if (arm.startsWith("PA_")) { pa(); return; }
        if (arm.equals("NSGA2_PLAIN")) {
            plain = new PlainNsgaAlgorithm(run.problem(),instance,new ClassicConfig("NSGA2_4V",0),run::checkpoint); plain.run(); return;
        }
        String mode = arm.equals("FULL_SHARED_DEEP") ? "SHARE_JOB_ALIGNED" : arm.equals("LI_RECON_DEEP") ? "BASELINE" : "NSGA2_4V";
        if(arm.equals("FULL_SHARED_DEEP") && Boolean.getBoolean("research.pa.sourceUniform")) mode += "_UNIFORM";
        SearchConfig cfg = new SearchConfig();
        cfg.mergeGlobalLocal = cfg.paperResourceOperators = !DynamicSearch.isClassic(mode) && !Boolean.getBoolean("research.li.v2");
        frozen = DynamicSearch.create(mode,instance,fatigue,decoder,run,cfg,false,0,0); frozen.algorithm.run();
    }
    private void pa() {
        PaPaidEvaluation.Checks noSearchQA = new PaPaidEvaluation.Checks() {
            public void paid(PermutationSolution<Integer> point,long fe) { }
            public void neutral(PermutationSolution<Integer> before,PermutationSolution<Integer> after) { }
        };
        PaPaidEvaluation evaluation = new PaPaidEvaluation(run,instance,noSearchQA); counts = new PaLightPopulation();
        PaSubsetPolicy policy = arm.equals("PA_RELABEL") ? PaSubsetPolicy.relabel(run.seed() ^ 0x51a7c3L) : PaSubsetPolicy.identity();
        population = new PaPopulation(evaluation,counts,policy);
        String supplied = System.getProperty("research.pa.sourceTSV");
        if (supplied != null) {
            try {
                for (String line : Files.readAllLines(Paths.get(supplied),StandardCharsets.UTF_8)) {
                    String[] f=line.split("\t"), text=f[3].split(","); double[] expected=new double[3];
                    for(int k=0;k<3;k++)expected[k]=Double.parseDouble(text[k]);
                    FourVectors genes=new FourVectors(ProbeData.integers(f[4]),ProbeData.integers(f[5]),ProbeData.integers(f[6]),ProbeData.integers(f[7]));
                    population.addInitial(evaluation.initial(genes,Direction.valueOf(f[1]),expected));
                }
            } catch (java.io.IOException e) { throw new java.io.UncheckedIOException(e); }
        } else {
            PaInitialBridge initial = new PaInitialBridge(instance);
            for(int i=0;i<100;i++) {
                Direction role=i<15?Direction.MAKESPAN:i<70?Direction.CENTER:i<85?Direction.ENERGY:Direction.WORKER_COST;
                population.addInitial(evaluation.randomInitial(i,role,initial));
            }
        }
        population.evolve();
    }
    Map<String,Object> diagnostics() {
        if (frozen != null) return new LinkedHashMap<>(frozen.diagnostics()); if (plain != null) return plain.diagnostics();
        Map<String,Object> result = new LinkedHashMap<>(); if(counts!=null)result.putAll(counts.fees);
        if(population!=null) { result.put("completeGenerations",population.completedGenerations); result.putAll(population.borrowedDiagnostics()); } return result;
    }
    public Object getResult() { return null; }
    public String getName() { return arm; }
    public String getDescription() { return "Explicit ordinary joint-adapted/no-LS or frozen full/Li/deep NSGA control; not author results reproduction"; }
}
