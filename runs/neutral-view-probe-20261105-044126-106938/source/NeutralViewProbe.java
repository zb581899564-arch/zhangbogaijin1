package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.mechanism.*;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.SearchConfig;

/** Fixed actual QGS inputs, unchanged generation kernels, and three equivalent donor views. */
public final class NeutralViewProbe {
    private NeutralViewProbe() { }
    private static final String[] METHODS = {"QGS_RAW", "QGS_RANDOM", "QGS_ALIGNED",
            "CLASSIC_RAW", "CLASSIC_RANDOM", "CLASSIC_ALIGNED"};

    private static final class Probe implements Algorithm<Object> {
        private static final long serialVersionUID = 1L;
        final Instance in; final DynamicParameters params; final DynamicEvaluation decoder;
        final RunContext<PermutationSolution<Integer>> context; final Path output;
        final List<String> lines; final int reps; final long seed;
        long viewQA, childQA, reproducibilityChecks, qaNanos, repairEdits;

        Probe(Instance in, DynamicParameters params, DynamicEvaluation decoder,
                RunContext<PermutationSolution<Integer>> context, Path output, List<String> lines, int reps, long seed) {
            this.in=in; this.params=params; this.decoder=decoder; this.context=context;
            this.output=output; this.lines=lines; this.reps=reps; this.seed=seed;
        }

        public void run() {
            SearchConfig cfg = new SearchConfig(); cfg.paperResourceOperators=true; cfg.mergeGlobalLocal=true;
            KernelVariants kernels = new KernelVariants(in, cfg, context::checkpoint);
            int index = 0;
            for (String line : lines) {
                String[] fields = line.split("\t", -1);
                if (fields.length!=18 || !fields[1].equals("-1") || !fields[2].equals("-"))
                    throw new AssertionError("Expected an unrestricted captured parent");
                List<PermutationSolution<Integer>> source = load(fields);
                String[] keys = source.stream().map(ProbeData::key).toArray(String[]::new);
                checkEquivalentSelf(source.get(0));
                for (int rep = 0; rep < reps; rep++) for (int turn = 0; turn < METHODS.length; turn++) {
                    String method = METHODS[(turn + rep + index) % METHODS.length];
                    long constructionSeed = NeutralProbeSupport.mixed(seed + index*1009L + rep);
                    propose(kernels, source, fields[0], rep, constructionSeed, method);
                    for (int t=0; t<3; t++) if (!keys[t].equals(ProbeData.key(source.get(t))))
                        throw new AssertionError("Proposal mutated an input");
                }
                index++;
            }
        }

        private List<PermutationSolution<Integer>> load(String[] fields) {
            List<PermutationSolution<Integer>> source = new ArrayList<>();
            for (int t=0; t<3; t++) {
                PermutationSolution<Integer> value = context.problem().createSolution();
                ProbeData.fill(value, fields, 3+t*5, -1, null);
                if (SchedulingEncoding.repair(value,in)!=0) throw new AssertionError("Illegal captured input");
                context.problem().evaluate(value); ProbeData.expected(value,fields[7+t*5]); source.add(value);
            }
            return source;
        }

        private void checkEquivalentSelf(PermutationSolution<Integer> parent) {
            PermutationSolution<Integer> shuffled = NeutralInterleavings.view(parent,parent,in,new Random(17),false);
            PermutationSolution<Integer> aligned = NeutralInterleavings.view(shuffled,parent,in,new Random(0),true);
            if (!ProbeData.key(parent).equals(ProbeData.key(aligned)))
                throw new AssertionError("Identical physical parent did not normalize to the recipient");
            checkView(parent,shuffled); checkView(parent,aligned);
        }

        private void propose(KernelVariants kernels, List<PermutationSolution<Integer>> source,
                String id, int rep, long constructionSeed, String method) {
            String kind=method.substring(method.indexOf('_')+1);
            String kernel=method.startsWith("QGS") ? KernelVariants.JOB_ALIGNED : KernelVariants.CLASSIC_GLOBAL;
            List<PermutationSolution<Integer>> donors=new ArrayList<>(); long start=System.nanoTime();
            for (int t=1; t<3; t++) donors.add(kind.equals("RAW") ? source.get(t)
                    : NeutralInterleavings.view(source.get(t),source.get(0),in,
                            new Random(NeutralProbeSupport.mixed(constructionSeed+t*7919L)),kind.equals("ALIGNED")));
            long preparation=System.nanoTime()-start;
            if (!kind.equals("RAW")) for (int t=1; t<3; t++) checkView(source.get(t),donors.get(t-1));
            String personalKey=ProbeData.key(donors.get(0)), globalKey=ProbeData.key(donors.get(1));
            SeededRandom.reset(constructionSeed); start=System.nanoTime();
            PermutationSolution<Integer> child=kernels.child(kernel,source.get(0),donors.get(0),donors.get(1));
            int repaired=SchedulingEncoding.repair(child,in); repairEdits+=repaired;
            long generation=System.nanoTime()-start;
            if (!personalKey.equals(ProbeData.key(donors.get(0))) || !globalKey.equals(ProbeData.key(donors.get(1))))
                throw new AssertionError("Kernel mutated a neutral donor");
            if (kind.equals("RAW")) {
                long qaStart=System.nanoTime(); SeededRandom.reset(constructionSeed);
                PermutationSolution<Integer> repeated=kernels.child(kernel,source.get(0),source.get(1),source.get(2));
                SchedulingEncoding.repair(repeated,in);
                if (!ProbeData.key(child).equals(ProbeData.key(repeated))) throw new AssertionError("Raw kernel differs");
                reproducibilityChecks++; qaNanos+=System.nanoTime()-qaStart;
            }
            start=System.nanoTime(); context.problem().evaluate(child); long evaluation=System.nanoTime()-start;
            long qaStart=System.nanoTime();
            NeutralProbeSupport.sameTimeline((DynamicSchedule)child.getAttribute(DynamicEvaluation.KEY),
                    NeutralProbeSupport.full(in,params,child)); childQA++; qaNanos+=System.nanoTime()-qaStart;
            int[] personalPath=NeutralInterleavings.path(source.get(0),donors.get(0),in);
            int[] globalPath=NeutralInterleavings.path(source.get(0),donors.get(1),in);
            NeutralProbeSupport.append(output.resolve("outcomes.jsonl"),NeutralProbeSupport.row(
                    "case",id,"rep",rep,"method",method,"seed",constructionSeed,"child",ProbeData.encoding(child),
                    "physicalKey",NeutralInterleavings.physicalKey(child,in),"personalInputPath",personalPath,
                    "globalInputPath",globalPath,"preparationSeconds",preparation/1e9,"generationSeconds",generation/1e9,
                    "evaluationSeconds",evaluation/1e9,"commonRepairEdits",repaired,"paidFE",context.budget().successful()));
        }

        private void checkView(PermutationSolution<Integer> original, PermutationSolution<Integer> view) {
            long start=System.nanoTime();
            if (SchedulingEncoding.repair(view,in)!=0) throw new AssertionError("Neutral view needed repair");
            NeutralProbeSupport.sameTimeline((DynamicSchedule)original.getAttribute(DynamicEvaluation.KEY),
                    NeutralProbeSupport.full(in,params,view)); viewQA++; qaNanos+=System.nanoTime()-start;
        }
        public Object getResult(){return null;}
        public String getName(){return "NEUTRAL_DONOR_VIEW_PROBE";}
        public String getDescription(){return getName();}
    }

    public static void main(String[] args) throws Exception {
        Path input=Paths.get(args[0]), output=Paths.get(args[4]); Files.createDirectories(output);
        System.setProperty("dhfsp.dataDir",input.getParent().toString());
        System.setProperty("dhfsp.setupFile",args[1]); System.setProperty("dhfsp.standbyPower","1");
        String[] d=input.getFileName().toString().replace(".txt","").split("_");
        EDHHFSPW source=new EDHHFSPW(Integer.parseInt(d[0]),Integer.parseInt(d[1]),Integer.parseInt(d[2]),Integer.parseInt(d[3]));
        Instance in=source.getSchedulingInstance(); DynamicParameters params=DynamicInputs.fatigue(in,Paths.get(args[2]));
        DynamicEvaluation decoder=new DynamicEvaluation(source,in,params,true);
        List<String> lines=Files.readAllLines(Paths.get(args[3]),StandardCharsets.UTF_8);
        int reps=Integer.parseInt(args[5]); long seed=Long.parseLong(args[6]), planned=lines.size()*(3L+METHODS.length*reps);
        RunContext<PermutationSolution<Integer>> ctx=new RunContext<>(decoder,planned,seed); decoder.setCheckpoint(ctx::checkpoint);
        Probe probe=new Probe(in,params,decoder,ctx,output,lines,reps,seed);
        try { ctx.run(probe); } catch(RuntimeException|Error failure) {
            NeutralProbeSupport.append(output.resolve("failure.jsonl"),NeutralProbeSupport.row("attempted",ctx.budget().attempted(),
                    "successful",ctx.budget().successful(),"failed",ctx.budget().failed(),"error",failure.toString())); throw failure;
        }
        if (ctx.budget().successful()!=planned || ctx.budget().failed()!=0) throw new AssertionError("Incomplete neutral probe");
        NeutralProbeSupport.append(output.resolve("receipt.jsonl"),NeutralProbeSupport.row("successfulFE",planned,
                "failedFE",0,"inputReplayFE",lines.size()*3,"candidateFE",probe.childQA,"viewFullTimelineQA",probe.viewQA,
                "candidateFullTimelineQA",probe.childQA,"rawConstructionReproducibilityChecks",probe.reproducibilityChecks,
                "offlineQASeconds",probe.qaNanos/1e9,"contextSecondsIncludingQA",ctx.clock().elapsedSeconds(),
                "finalCommonRepairEdits",probe.repairEdits,"classIdentity",ClassResolutionProbe.capture(
                        "org.uma.jmetal.util.research.mechanism.JobAlignedPaperKernel",
                        "org.uma.jmetal.util.research.mechanism.JobAlignedResources",
                        "org.uma.jmetal.util.research.classic.ClassicKernelBridge",
                        "org.uma.jmetal.util.research.model.DynamicDecoder")));
        System.out.println("NEUTRAL_VIEW_PASS cases="+lines.size()+" paid="+planned);
    }
}
