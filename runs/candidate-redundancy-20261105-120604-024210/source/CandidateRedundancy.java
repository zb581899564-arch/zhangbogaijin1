package org.uma.jmetal.util.research.search;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.research.DynamicEvaluation;
import org.uma.jmetal.util.research.model.DynamicParameters;
import org.uma.jmetal.util.research.model.DynamicSchedule;
import org.uma.jmetal.util.research.model.Instance;

/** Read-only, full-history physical duplicate audit. Every original evaluation still executes and is paid. */
public final class CandidateRedundancy {
    private static final Map<CandidatePhysicalKey,Entry> HISTORY = new HashMap<>();
    private static final IdentityHashMap<PermutationSolution<Integer>,Proposal> PENDING = new IdentityHashMap<>();
    private static final CandidateRedundancyStats STATS = new CandidateRedundancyStats();
    private static final CandidateTimelineDigest DIGEST = new CandidateTimelineDigest();
    private static final List<Map<String,Object>> SAMPLES = new ArrayList<>();
    private static Instance instance;
    private static DynamicParameters parameters;
    private static Active active;
    private static long paid, verified, storedIntegers, observeNanos;
    private CandidateRedundancy() { }

    public static void configure(Instance in, DynamicParameters params) { instance = in; parameters = params; }

    static void intra(PermutationSolution<Integer> parent, PermutationSolution<Integer> child,
            Instance in, int factory, int operator) {
        Proposal proposal = new Proposal(CandidatePhysicalKey.of(parent, in.factories()), factory, operator,
                EmptyNeighborhoodCertificate.positions(parent, factory).size(),
                EmptyNeighborhoodCertificate.empty(in, parent, factory, operator));
        if (PENDING.put(child, proposal) != null) throw new AssertionError("Unpaid proposal overwritten");
    }
    static void enter(PermutationSolution<Integer> candidate, String stage, Direction role) {
        if (active != null) throw new AssertionError("Nested paid evaluation");
        active = new Active(candidate, stage, role == null ? "NONE" : role.name(), PENDING.remove(candidate));
    }
    static void exit() { active = null; }

    public static void paid(Solution<?> value, long fe, boolean archiveChanged) {
        long started = System.nanoTime();
        if (fe != paid + 1) throw new AssertionError("Noncontiguous paid observations");
        PermutationSolution<?> point = (PermutationSolution<?>) value;
        if (active != null && active.candidate != value) throw new AssertionError("Observer lost guarded candidate");
        DynamicSchedule schedule = (DynamicSchedule) value.getAttribute(DynamicEvaluation.KEY);
        schedule.validateContext(instance, parameters);
        CandidatePhysicalKey key = CandidatePhysicalKey.of(point, instance.factories());
        byte[] timeline = DIGEST.of(schedule, instance.factories());
        Entry previous = HISTORY.get(key); boolean duplicate = previous != null;
        if (duplicate) {
            if (!Arrays.equals(previous.objectives, value.getObjectives()) || !Arrays.equals(previous.timeline, timeline))
                throw new AssertionError("Equal whole physical keys have unequal objectives or complete timelines");
            verified++;
        } else { HISTORY.put(key, new Entry(value.getObjectives().clone(), timeline, fe)); storedIntegers += key.genes.length; }
        Proposal proposal = active == null ? null : active.proposal;
        boolean identity = proposal != null && proposal.parent.equals(key);
        boolean empty = proposal != null && proposal.empty;
        if (empty && !identity) throw new AssertionError("Empty-neighborhood certificate contradicted actual paid proposal");
        String stage = active == null ? (fe <= 100 ? "initialization" : "global") : active.stage;
        String role = active == null ? "CLASSIC" : active.role;
        int operator = proposal == null ? -1 : proposal.operator, jobs = proposal == null ? -1 : proposal.jobs;
        STATS.record(stage, role, operator, jobs, duplicate, identity, empty, archiveChanged);
        if (fe % 997 == 1) sample(fe, stage, role, proposal, previous, duplicate, identity, empty);
        paid++; observeNanos += System.nanoTime() - started;
    }

    private static void sample(long fe, String stage, String role, Proposal proposal, Entry previous,
            boolean duplicate, boolean identity, boolean empty) {
        Map<String,Object> out = new LinkedHashMap<>();out.put("paidFE", fe);out.put("stage", stage);out.put("role", role);
        out.put("operator", proposal == null ? -1 : proposal.operator);out.put("factory", proposal == null ? -1 : proposal.factory);
        out.put("factoryJobs", proposal == null ? -1 : proposal.jobs);out.put("historyDuplicate", duplicate);
        out.put("previousPaidFE", previous == null ? null : previous.fe);out.put("parentIdentity", identity);
        out.put("certifiedEmptyNeighborhood", empty);SAMPLES.add(out);
    }

    public static Map<String,Object> diagnostics() {
        Map<String,Object> out = STATS.snapshot();out.put("paidObservations", paid);out.put("uniqueWholePhysicalKeys", HISTORY.size());
        out.put("duplicateTimelineDigestsVerified", verified);out.put("storedKeyIntegers", storedIntegers);
        out.put("pendingUnpaidProposals", PENDING.size());out.put("activeEvaluationCleared", active == null);
        out.put("observerNanosPaidCallbackOnly", observeNanos);out.put("samples", SAMPLES);
        out.put("scope", "Full100k history, exact integer equality after hash, immutable context; observation only, not a cache or free rejection");
        return out;
    }

    private static final class Entry {
        final double[] objectives; final byte[] timeline; final long fe;
        Entry(double[] point, byte[] digest, long birth) { objectives = point; timeline = digest; fe = birth; }
    }
    private static final class Proposal {
        final CandidatePhysicalKey parent; final int factory, operator, jobs; final boolean empty;
        Proposal(CandidatePhysicalKey key, int f, int op, int n, boolean certificate) {
            parent = key; factory = f; operator = op; jobs = n; empty = certificate;
        }
    }
    private static final class Active {
        final PermutationSolution<Integer> candidate; final String stage, role; final Proposal proposal;
        Active(PermutationSolution<Integer> point, String s, String r, Proposal p) { candidate = point;stage = s;role = r;proposal = p; }
    }
}
