package research.dynamic;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.*;
import org.uma.jmetal.util.research.search.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;

/** Charged finite-domain diagnostic. Never feeds an oracle point into a production run. */
public final class FamilySupportRun implements Algorithm<Void> {
    private final RunContext<PermutationSolution<Integer>> run;
    private final Instance instance;
    private final Path cases;
    private final BufferedWriter output;
    private final PilotPhysics physics;
    private final GomPrefixDigest digest = new GomPrefixDigest();
    private long written;

    private FamilySupportRun(RunContext<PermutationSolution<Integer>> context, Instance in,
            DynamicParameters params, Path input, BufferedWriter writer) {
        run = context; instance = in; cases = input; output = writer; physics = new PilotPhysics(in, params);
    }

    @SuppressWarnings("unchecked")
    private PermutationSolution<Integer> point(String[] row) {
        int[][] v = new int[4][];
        for (int k = 0; k < 4; k++) {
            v[k] = RequestInputs.ints(row[k + 3]);
            if (v[k].length != instance.jobs()) throw new IllegalArgumentException("Incomplete genome");
        }
        PermutationSolution<Integer> p = run.problem().createSolution();
        List<Integer> machines = (List<Integer>) p.getAttribute("machine");
        for (int i = 0; i < v[0].length; i++) {
            p.setVariableValue(i, v[0][i]); p.setVariableValueid(i, v[1][i]);
            machines.set(i, v[2][i]); p.setVariableValueworker(i, v[3][i]);
        }
        if (SchedulingEncoding.repair(p, instance) != 0) throw new AssertionError("Oracle input required repair");
        return p;
    }

    @Override public void run() {
        try (BufferedReader input = Files.newBufferedReader(cases, StandardCharsets.UTF_8)) {
            String line;
            while ((line = input.readLine()) != null) {
                String[] fields = line.split("\t", -1);
                if (fields.length != 7) throw new IllegalArgumentException("Expected id,factory,localId,JS,FA,MA,WA");
                PermutationSolution<Integer> p = point(fields);
                run.problem().evaluate(p); long fe = run.budget().successful();
                // QA only: one separately reported full decode; no candidate generation or selection.
                physics.check(p); digest.update(p, fe);
                DynamicSchedule s = (DynamicSchedule) p.getAttribute(DynamicEvaluation.KEY);
                Map<String,Object> record = GomRecords.raw(p);
                record.putAll(GomRecords.row("id", fields[0], "factory", Integer.parseInt(fields[1]),
                    "localId", Integer.parseInt(fields[2]), "fe", fe,
                    "factoryMakespan", s.factoryMakespan(), "factoryEnergy", s.factoryEnergy(),
                    "factoryCost", s.factoryCost()));
                output.write(DynamicJson.encode(record)); output.newLine(); output.flush(); written++;
            }
        } catch (IOException error) { throw new UncheckedIOException(error); }
    }

    @Override public Void getResult() { return null; }
    @Override public String getName() { return "FINITE_FAMILY_SUPPORT_ORACLE"; }
    @Override public String getDescription() { return "Frozen enumeration, every full candidate charged"; }

    public static void main(String[] args) throws Exception {
        if (args.length != 7) throw new IllegalArgumentException("INPUT SETUP FATIGUE CASES OUT FE_LIMIT SEED");
        Path input = Paths.get(args[0]), out = Paths.get(args[4]); Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir", input.getParent().toString());
        System.setProperty("dhfsp.setupFile", args[1]); System.setProperty("dhfsp.standbyPower", "1");
        String[] n = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(n[0]), Integer.parseInt(n[1]), Integer.parseInt(n[2]), Integer.parseInt(n[3]));
        Instance in = raw.getSchedulingInstance();
        if (!in.satisfiesDualResourceCondition()) throw new IllegalArgumentException("Unqualified instance");
        DynamicParameters params = DynamicInputs.fatigue(in, Paths.get(args[2]));
        DynamicEvaluation decoder = new DynamicEvaluation(raw, in, params, true);
        long limit = Long.parseLong(args[5]);
        RunContext<PermutationSolution<Integer>> context = new RunContext<>(PilotPhysics.delegate(decoder), limit, Long.parseLong(args[6]));
        decoder.setCheckpoint(context::checkpoint); Throwable failure = null;
        try (BufferedWriter writer = Files.newBufferedWriter(out.resolve("paid.jsonl"), StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW)) {
            FamilySupportRun algorithm = new FamilySupportRun(context, in, params, Paths.get(args[3]), writer);
            try { context.run(algorithm); } catch (RuntimeException | Error error) { failure = error; }
            finally { decoder.clearPrepared(); }
            Map<String,Object> receipt = GomRecords.row("attempted", context.budget().attempted(),
                "successful", context.budget().successful(), "failed", context.budget().failed(),
                "limit", limit, "written", algorithm.written, "stopReason", context.stopReason(),
                "secondsIncludesQA", context.clock().elapsedSeconds(), "physicsQA", algorithm.physics.receipt(),
                "paidSHA256", algorithm.digest.snapshot(), "error", failure == null ? null : failure.toString(),
                "decoder", decoder.diagnostics(), "frontier", context.result().stream().map(GomRecords::raw).toArray(),
                "loaded", ClassResolutionProbe.capture("research.dynamic.FamilySupportRun", "research.dynamic.PilotPhysics",
                    "org.uma.jmetal.util.research.DynamicEvaluation", "org.uma.jmetal.util.research.model.DynamicDecoder",
                    "org.uma.jmetal.util.research.model.DynamicSchedule", "org.uma.jmetal.util.research.runtime.BudgetedProblem"));
            Files.write(out.resolve("receipt.json"), (DynamicJson.encode(receipt) + "\n").getBytes(StandardCharsets.UTF_8), StandardOpenOption.CREATE_NEW);
        }
        if (failure != null) throw new IllegalStateException("Failure evidence preserved", failure);
        System.out.println("FAMILY_SUPPORT_PAID " + context.budget().successful());
    }
}
