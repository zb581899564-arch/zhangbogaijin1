package org.uma.jmetal.util.research.cooperation;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.atomic.AtomicLong;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.joint.JointCheckProblem;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.Direction;

/** Scientific invariants on synthetic fixtures; no optimizer or research matrix. */
public final class NightCooperationChecks {
    private static int syntheticDecoderCalls;
    private NightCooperationChecks() { }

    public static void main(String[] args) {
        for (String mode : new String[] {"ELITE", "RANDOM"})
            for (int successes : new int[] {0, 3, 5}) renewal(mode, successes);
        wholeFactoryAndMosaic(); samplingAndPaidDuplicates();
        System.out.println("NIGHT_COOPERATION_CHECKS_PASS renewal generation1/2; novel free donor; exactly one draw; "
                + "five independent replacements; partial0/3/5 ledger; whole-factory timeline; job-aligned mosaic; "
                + "six shared source draws; role/random controls; duplicate proposal charged; optimizerFE=0; "
                + "syntheticDecoderCalls=" + syntheticDecoderCalls);
    }

    @SuppressWarnings("unchecked")
    private static void renewal(String mode, int successes) {
        SeededRandom.reset(4412);
        JointCheckProblem raw = new JointCheckProblem(12);
        FamilyContexts contexts = new FamilyContexts(raw.instance);
        List<PermutationSolution<Integer>> population = new ArrayList<>();
        for (int i = 0; i < 100; i++) {
            PermutationSolution<Integer> value = raw.createSolution();
            // The first three jobs keep every factory nonempty. Codes change remaining jobs.
            int code = i < 20 ? i / 5 : i == 20 ? 0 : i - 17;
            assignCode(value, raw.instance, code); contexts.initialize(value, i);
            for (int k = 0; k < 3; k++) value.setObjective(k, i == 21 ? 1 : 100 + i);
            population.add(value);
        }
        List<String> before = states(population); int[][] previous = new int[4][];
        for (int family = 0; family < 4; family++) previous[family] = contexts.assignment(family);
        AtomicLong successful = new AtomicLong(100); // Simulated callback ledger, not optimizer evaluations.
        ContextRenewal renewal = new ContextRenewal(mode, successful::get, () -> .25);
        SeededRandom.reset(101011);
        require(renewal.prepare(population, contexts, 1).isEmpty(), "Generation1 refreshed");
        require(SeededRandom.current().nextLong() == new Random(101011).nextLong(), "Generation1 consumed RNG");
        require(states(population).equals(before), "Generation1 changed population");
        for (int family = 0; family < 4; family++) require(Arrays.equals(previous[family], contexts.assignment(family)), "Generation1 changed FA");

        Random oracle = new Random(88771); int ordinal = oracle.nextInt(79); long next = oracle.nextLong();
        SeededRandom.reset(88771);
        Map<Integer, PermutationSolution<Integer>> children = renewal.prepare(population, contexts, 2);
        require(SeededRandom.current().nextLong() == next, "Renewal controls did not consume exactly one common draw");
        require(renewal.family() == 0 && children.size() == 5, "Generation2 did not replace family0 five times");
        Map<String, Object> event = renewal.trace().get(1);
        require(number(event, "candidateCount") == 79 && number(event, "randomCandidateOrdinal") == ordinal, "Matched old/free contexts were not excluded");
        int donorIndex = mode.equals("ELITE") ? 21 : 21 + ordinal;
        require(number(event, "donorPopulationIndex") == donorIndex && FamilyContexts.family(population.get(donorIndex)) == -1,
                "Renewal source was not the expected current free particle");
        List<Integer> ranked = (List<Integer>) event.get("rankedCandidateOrdinals");
        require(ranked.size() == 79 && ranked.get(0) == 0, "Both controls must rank the same dominant-source fixture");
        int[] selectedFA = FamilyContexts.byJob(population.get(donorIndex));
        for (int[] old : previous) require(!Arrays.equals(old, selectedFA), "Donor copied an old family FA");
        require(states(population).equals(before), "Prepare mutated a parent/free particle");
        for (int family = 1; family < 4; family++) require(Arrays.equals(previous[family], contexts.assignment(family)), "Other family context changed");
        for (int i = 0; i < 5; i++) {
            PermutationSolution<Integer> child = children.get(i);
            require(child != null && child != population.get(i), "Replacement aliases parent");
            require(FamilyContexts.family(child) == 0 && Arrays.equals(FamilyContexts.byJob(child), selectedFA), "Replacement has wrong FA/family");
            legal(child, raw.instance);
            if (i < successes) { successful.incrementAndGet(); renewal.evaluated(child); }
        }
        require(states(population).equals(before), "Reset callback mutated original population");
        Map<String, Object> summary = renewal.summary(), ledger = renewal.trace().get(1);
        require(number(summary, "paidResetEvaluations") == successes && number(summary, "pendingResetEvaluations") == 5 - successes,
                "Partial renewal costs/pending count wrong");
        require(number(ledger, "endFE") - number(ledger, "startFE") == successes
                && number(ledger, "successfulResetEvaluations") == successes && number(ledger, "expectedResetEvaluations") == 5,
                "Renewal event hid charged reevaluations");
        require(Boolean.valueOf(successes == 5).equals(ledger.get("complete"))
                && number(summary, "eventsCompleted") == (successes == 5 ? 1 : 0), "Partial renewal incorrectly completed");
    }

    private static void assignCode(PermutationSolution<Integer> value, Instance in, int code) {
        int[] assignment = new int[in.jobs()]; assignment[0] = 0; assignment[1] = 1; assignment[2] = 2;
        for (int job = 3; job < assignment.length; job++) { assignment[job] = code % 3; code /= 3; }
        List<Integer> machines = machines(value);
        for (int p = 0; p < in.jobs(); p++) {
            int job = value.getVariableValue(p), factory = assignment[job]; value.setVariableValueid(p, factory);
            machines.set(p, (job + 1) % in.machines(factory, 0)); value.setVariableValueworker(p, (job + 2) % in.workers(factory, 0));
        }
    }

    private static void wholeFactoryAndMosaic() {
        SeededRandom.reset(7321); JointCheckProblem raw = new JointCheckProblem(12);
        PermutationSolution<Integer> parent = baseGenome(raw); decode(parent, raw.instance, raw.parameters);
        PermutationSolution<Integer> a = sourceVariant(parent, 0), b = sourceVariant(parent, 1), c = sourceVariant(parent, 2);
        DynamicSchedule sa = decode(a, raw.instance, raw.parameters), sb = decode(b, raw.instance, raw.parameters), sc = decode(c, raw.instance, raw.parameters);
        FactoryRecord ra = new FactoryRecord(sa, 1, 11, 1, "synthetic-source", "MAKESPAN", true);
        FactoryRecord rb = new FactoryRecord(sb, 1, 12, 1, "synthetic-source", "ENERGY", true);
        FactoryRecord rc = new FactoryRecord(sc, 1, 13, 1, "synthetic-source", "WORKER_COST", true);
        String parentBefore = state(parent), sourceA = state(a), sourceB = state(b), sourceC = state(c);
        PermutationSolution<Integer> packet = TransferEncoding.build(parent, 1, ra, ra, ra);
        PermutationSolution<Integer> mosaic = TransferEncoding.build(parent, 1, ra, rb, rc);
        require(Arrays.equals(FamilyContexts.byJob(parent), FamilyContexts.byJob(packet))
                && Arrays.equals(FamilyContexts.byJob(parent), FamilyContexts.byJob(mosaic)), "Transfer changed FA");
        assertOtherPositions(parent, packet, 1); assertOtherPositions(parent, mosaic, 1);
        assertLocalComponents(packet, 1, ra, ra, ra); assertLocalComponents(mosaic, 1, ra, rb, rc);
        require(!state(packet).equals(state(mosaic)), "Mosaic fixture was trivial");
        legal(packet, raw.instance); legal(mosaic, raw.instance);
        DynamicSchedule actual = decode(packet, raw.instance, raw.parameters); decode(mosaic, raw.instance, raw.parameters);
        sameFactoryTimeline(sa, actual, 1);
        bits(new double[] {sa.factoryMakespan()[1], sa.factoryEnergy()[1], sa.factoryCost()[1]},
                new double[] {actual.factoryMakespan()[1], actual.factoryEnergy()[1], actual.factoryCost()[1]});
        DynamicSchedule before = schedule(parent);
        sameFactoryTimeline(before, actual, 0); sameFactoryTimeline(before, actual, 2);
        require(state(parent).equals(parentBefore) && state(a).equals(sourceA) && state(b).equals(sourceB) && state(c).equals(sourceC), "Transfer mutated source or parent");
    }

    @SuppressWarnings("unchecked")
    private static PermutationSolution<Integer> sourceVariant(PermutationSolution<Integer> parent, int variant) {
        PermutationSolution<Integer> value = (PermutationSolution<Integer>) parent.copy();
        int[][] orders = {{10, 7, 4, 1}, {4, 7, 10, 1}, {7, 1, 10, 4}};
        int at = 0;
        for (int p = 0; p < 12; p++) if (value.getVariableValueid(p) == 1) {
            int job = orders[variant][at++], ordinal = (job - 1) / 3;
            value.setVariableValue(p, job); machines(value).set(p, (ordinal + (variant == 1 ? 2 : 0)) % 3);
            value.setVariableValueworker(p, variant == 2 ? 1 - ordinal % 2 : ordinal % 2);
        }
        return value;
    }

    private static void assertLocalComponents(PermutationSolution<Integer> value, int factory,
            FactoryRecord sequence, FactoryRecord machineSource, FactoryRecord workerSource) {
        int at = 0;
        for (int p = 0; p < value.getNumberOfVariables(); p++) if (value.getVariableValueid(p) == factory) {
            int job = value.getVariableValue(p);
            require(job == sequence.jobs[at++], "Local sequence donor order lost");
            require(machines(value).get(p) == resourceForJob(machineSource, job, true), "Machine copied by position instead of job");
            require(value.getVariableValueworker(p) == resourceForJob(workerSource, job, false), "Worker copied by position instead of job");
        }
        require(at == sequence.jobs.length, "Local job set changed");
    }
    private static int resourceForJob(FactoryRecord source, int job, boolean machine) {
        for (int i = 0; i < source.jobs.length; i++) if (source.jobs[i] == job) return machine ? source.machines[i] : source.workers[i];
        throw new AssertionError("Mosaic donor omitted job");
    }

    @SuppressWarnings("unchecked")
    private static void samplingAndPaidDuplicates() {
        SeededRandom.reset(90210); JointCheckProblem raw = new JointCheckProblem(12);
        Instance in = powerTradeoff(raw.instance); DynamicParameters params = DynamicParameters.uniform(in, 0, 0, 0, 0);
        PermutationSolution<Integer> parent = baseGenome(raw); DynamicSchedule slow = decode(parent, in, params);
        PermutationSolution<Integer> fastGenome = (PermutationSolution<Integer>) parent.copy();
        for (int p = 0; p < 12; p++) if (fastGenome.getVariableValueid(p) == 1) machines(fastGenome).set(p, 1);
        DynamicSchedule fast = decode(fastGenome, in, params);
        require(slow.factoryMakespan()[1] > slow.factoryMakespan()[0] && slow.factoryMakespan()[1] > slow.factoryMakespan()[2], "Target factory fixture not unique");
        FactoryPool[] pools = new FactoryPool[3];
        for (int f = 0; f < 3; f++) { pools[f] = new FactoryPool(); pools[f].offer(new FactoryRecord(slow, f, 101, 1, "synthetic-source", "MAKESPAN", true)); }
        pools[1].offer(new FactoryRecord(fast, 1, 102, 1, "synthetic-source", "ENERGY", true));
        require(pools[1].size() == 2 && fast.factoryMakespan()[1] < slow.factoryMakespan()[1]
                && fast.factoryEnergy()[1] > slow.factoryEnergy()[1], "Real decoded source pair must be nondominated");
        String frozenParent = state(parent), frozenPool = poolState(pools);
        long commonNext = 0;
        for (String mode : new String[] {"PACKET_ROLE", "MOSAIC_ROLE", "PACKET_RANDOM", "MOSAIC_RANDOM"}) {
            AtomicLong successes = new AtomicLong(500);
            FactoryTransfer transfer = new FactoryTransfer(mode, successes::get, () -> .25, 1);
            SeededRandom.reset(90210); Random oracle = new Random(90210);
            for (int i = 0; i < 3; i++) require(transfer.propose(parent, Direction.MAKESPAN, 0, pools, 2) == null, "Transfer ran before scheduled opportunity");
            require(number(transfer.summary(), "sourceRandomDraws") == 0, "Unscheduled transfer consumed source draws");
            PermutationSolution<Integer> child = transfer.propose(parent, Direction.MAKESPAN, 0, pools, 2);
            int[][] expected = new int[3][2];
            for (int component = 0; component < 3; component++) for (int side = 0; side < 2; side++) expected[component][side] = oracle.nextInt(2);
            long next = oracle.nextLong(); require(SeededRandom.current().nextLong() == next, "Transfer did not consume exactly six common draws");
            if (commonNext == 0) commonNext = next; else require(commonNext == next, "PACKET/MOSAIC altered source RNG budget");
            require(child != null && child != parent && successes.get() == 500
                    && number(transfer.summary(), "paidTransfers") == 0 && number(transfer.summary(), "pendingTransfers") == 1,
                    "Proposed duplicate was treated as free/paid early or replaced with fallback");
            if (mode.equals("PACKET_RANDOM")) require(sameGenome(parent, child), "Fixed duplicate fixture silently fell back to another operator");
            decode(child, in, params); successes.incrementAndGet(); transfer.evaluated(child);
            require(number(transfer.summary(), "paidTransfers") == 1 && number(transfer.summary(), "pendingTransfers") == 0
                    && number(transfer.summary(), "sourceRandomDraws") == 6, "Actual callback did not charge exactly one transfer");
            Map<String, Object> event = transfer.trace().get(1);
            require(number(event, "factory") == 1 && number(event, "paidFE") - number(event, "proposalFE") == 1, "Transfer target or fee contract changed");
            List<Map<String, Object>> pairs = (List<Map<String, Object>>) event.get("sampledPairs");
            for (int component = 0; component < 3; component++) {
                Map<String, Object> pair = pairs.get(component);
                require(number(pair, "firstOrdinal") == expected[component][0] && number(pair, "secondOrdinal") == expected[component][1], "Source pairs differ across controls");
                boolean selectsSecond = mode.endsWith("ROLE") && expected[component][0] == 0 && expected[component][1] == 1;
                require(Boolean.valueOf(selectsSecond).equals(pair.get("selectedSecond")), "Role versus uniform-first source policy wrong");
            }
            require(state(parent).equals(frozenParent) && poolState(pools).equals(frozenPool), "Sampling/evaluation mutated frozen parent or pools");
        }
    }

    private static Instance powerTradeoff(Instance base) {
        int factories = base.factories(), stages = base.stages();
        double[][] processing = new double[12][2], setup = new double[12][2];
        for (int j = 0; j < 12; j++) processing[j] = new double[] {30, 1};
        double[][][] speeds = new double[factories][stages][], powers = new double[factories][stages][], standby = new double[factories][stages][];
        double[][][] efficiencies = new double[factories][stages][], wages = new double[factories][stages][];
        for (int f = 0; f < factories; f++) for (int k = 0; k < stages; k++) {
            speeds[f][k] = new double[base.machines(f, k)]; powers[f][k] = new double[base.machines(f, k)]; standby[f][k] = new double[base.machines(f, k)];
            for (int m = 0; m < speeds[f][k].length; m++) { speeds[f][k][m] = base.speed(f, k, m); powers[f][k][m] = base.power(f, k, m); standby[f][k][m] = 1; }
            efficiencies[f][k] = new double[base.workers(f, k)]; wages[f][k] = new double[base.workers(f, k)];
            for (int w = 0; w < efficiencies[f][k].length; w++) { efficiencies[f][k][w] = base.efficiency(f, k, w); wages[f][k][w] = base.cost(f, k, w); }
        }
        speeds[1][0] = new double[] {.5, 2, 3}; powers[1][0] = new double[] {1, 10, 20};
        return new Instance("night-paid-source-tradeoff", ModelKind.CHAPTER4_DUAL_RESOURCE, processing, setup,
                speeds, powers, standby, efficiencies, wages, "SYNTHETIC real-decoded speed/power tradeoff; not research performance");
    }

    private static PermutationSolution<Integer> baseGenome(JointCheckProblem raw) {
        PermutationSolution<Integer> value = raw.createSolution();
        for (int p = 0; p < 12; p++) { value.setVariableValue(p, p); value.setVariableValueid(p, p % 3); machines(value).set(p, 0); value.setVariableValueworker(p, 0); }
        return value;
    }
    private static DynamicSchedule decode(PermutationSolution<Integer> value, Instance in, DynamicParameters parameters) {
        syntheticDecoderCalls++;
        DynamicSchedule schedule = DynamicDecoder.full(in, parameters, SchedulingEncoding.integers(value.getVariables()),
                SchedulingEncoding.integers(value.getVariablesid()), SchedulingEncoding.machineIntegers(value), SchedulingEncoding.integers(value.getVariablesworker()), null);
        DynamicValidator.validate(in, parameters, schedule);
        for (int k = 0; k < 3; k++) value.setObjective(k, schedule.objectives()[k]); value.setAttribute(DynamicEvaluation.KEY, schedule);
        return schedule;
    }
    private static void sameFactoryTimeline(DynamicSchedule source, DynamicSchedule actual, int factory) {
        List<DynamicStep> left = new ArrayList<>(), right = new ArrayList<>();
        for (DynamicStep step : source.steps()) if (step.factory() == factory) left.add(step);
        for (DynamicStep step : actual.steps()) if (step.factory() == factory) right.add(step);
        require(left.size() == right.size(), "Factory operation count changed");
        for (int i = 0; i < left.size(); i++) {
            DynamicStep a = left.get(i), b = right.get(i);
            require(a.job() == b.job() && a.stage() == b.stage() && a.machine() == b.machine() && a.worker() == b.worker(), "Factory bindings changed");
            bits(new double[] {a.start(), a.base(), a.duration(), a.setupDuration(), a.completion(), a.u(), a.v(), a.energy(), a.labor(), a.exposure()},
                    new double[] {b.start(), b.base(), b.duration(), b.setupDuration(), b.completion(), b.u(), b.v(), b.energy(), b.labor(), b.exposure()});
        }
    }
    private static void assertOtherPositions(PermutationSolution<Integer> parent, PermutationSolution<Integer> child, int factory) {
        for (int p = 0; p < parent.getNumberOfVariables(); p++) if (parent.getVariableValueid(p) != factory)
            require(parent.getVariableValue(p).equals(child.getVariableValue(p)) && parent.getVariableValueid(p).equals(child.getVariableValueid(p))
                    && machines(parent).get(p).equals(machines(child).get(p)) && parent.getVariableValueworker(p).equals(child.getVariableValueworker(p)), "Transfer changed another factory's encoding");
    }
    private static void legal(PermutationSolution<Integer> value, Instance in) {
        int[] js = SchedulingEncoding.integers(value.getVariables()), counts = new int[in.factories()]; Arrays.sort(js);
        for (int p = 0; p < in.jobs(); p++) {
            require(js[p] == p, "Child job permutation changed"); int f = value.getVariableValueid(p); require(f >= 0 && f < counts.length, "Invalid child FA"); counts[f]++;
            require(machines(value).get(p) >= 0 && machines(value).get(p) < in.machines(f, 0)
                    && value.getVariableValueworker(p) >= 0 && value.getVariableValueworker(p) < in.workers(f, 0), "Invalid renewed MA/WA");
        }
        for (int count : counts) require(count > 0, "Renewal emptied factory");
    }
    private static List<String> states(List<PermutationSolution<Integer>> values) { List<String> result = new ArrayList<>(); for (PermutationSolution<Integer> value : values) result.add(state(value)); return result; }
    private static boolean sameGenome(PermutationSolution<Integer> a, PermutationSolution<Integer> b) {
        return a.getVariables().equals(b.getVariables()) && a.getVariablesid().equals(b.getVariablesid()) && machines(a).equals(machines(b)) && a.getVariablesworker().equals(b.getVariablesworker());
    }
    private static String state(PermutationSolution<Integer> value) {
        return value.getVariables().toString() + value.getVariablesid() + machines(value) + value.getVariablesworker()
                + Arrays.toString(value.getObjectives()) + value.getAttribute(FamilyContexts.FAMILY) + Arrays.toString((int[]) value.getAttribute(FamilyContexts.FIXED));
    }
    private static String poolState(FactoryPool[] pools) { StringBuilder out = new StringBuilder(); for (FactoryPool pool : pools) for (FactoryRecord r : pool.records()) out.append(Arrays.toString(r.jobs)).append(Arrays.toString(r.machines)).append(Arrays.toString(r.workers)).append(Arrays.toString(r.objectives)).append(r.paidFE); return out.toString(); }
    @SuppressWarnings("unchecked") private static List<Integer> machines(PermutationSolution<Integer> value) { return (List<Integer>) value.getAttribute("machine"); }
    private static DynamicSchedule schedule(PermutationSolution<Integer> value) { return (DynamicSchedule) value.getAttribute(DynamicEvaluation.KEY); }
    private static long number(Map<String, Object> values, String key) { return ((Number) values.get(key)).longValue(); }
    private static void bits(double[] a, double[] b) { require(Arrays.equals(a, b), "Exact factory timeline/objectives changed"); }
    private static void require(boolean ok, String message) { if (!ok) throw new AssertionError(message); }
}
