package org.uma.jmetal.util.research.joint;

import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.function.BiConsumer;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.DynamicParameters;
import org.uma.jmetal.util.research.model.DynamicPrefix;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.ModelKind;
import org.uma.jmetal.util.research.runtime.SeededRandom;
import org.uma.jmetal.util.research.search.Direction;
import org.uma.jmetal.util.research.search.GlobalUpdatePolicy;
import org.uma.jmetal.util.research.search.ParticleOperators;

/** Finite-block joint generation with four independent, batch-frozen remaining-value heads. */
public final class JointPolicy implements GlobalUpdatePolicy {
    public enum Mode { RANDOM, GREEDY, TAIL, VALUE }
    public static final int BLOCK_LENGTH = 4, CANDIDATE_LIMIT = 6, STARTUP_TRAJECTORIES = 64;
    public static final double GUIDED_PROBABILITY = .25, EPSILON = .1;
    private final Instance in;
    private final DynamicParameters parameters;
    private final ParticleOperators baseline;
    private final Mode mode;
    private final BiConsumer<PermutationSolution<Integer>, DynamicPrefix> preparation;
    private final Runnable checkpoint;
    private JointFeatures features;
    private final Head[] heads = new Head[Direction.values().length];
    private final IdentityHashMap<PermutationSolution<Integer>, Episode> pending = new IdentityHashMap<>();
    private final List<Map<String, Object>> traces = new ArrayList<>();
    private final int traceLimit;
    private double[] scales;
    private Direction active;
    private double[] frozen;
    private long frozenVersion;
    private boolean useValue;
    private long proposals, baselineProposals, guidedProposals, completed, incomplete, noLegalFallbacks;
    private long stepTrials, selectedActions, exploredActions, learnedActions;
    private long proposeNanos, prefixNanos, candidateNanos, featureNanos, featurePrecomputeNanos, predictionNanos, trainingNanos, traceNanos;

    public JointPolicy(Instance in, DynamicParameters parameters, ParticleOperators baseline, Mode mode,
            BiConsumer<PermutationSolution<Integer>, DynamicPrefix> preparation, Runnable checkpoint) {
        this(in, parameters, baseline, mode, preparation, checkpoint, 0);
    }
    public JointPolicy(Instance in, DynamicParameters parameters, ParticleOperators baseline, Mode mode,
            BiConsumer<PermutationSolution<Integer>, DynamicPrefix> preparation, Runnable checkpoint, int traceLimit) {
        if (in.kind() != ModelKind.CHAPTER4_DUAL_RESOURCE || parameters == null || baseline == null
                || mode == null || preparation == null || checkpoint == null || traceLimit < 0) {
            throw new IllegalArgumentException("JointPolicy requires a dynamic chapter4 problem and valid callbacks");
        }
        this.in = in; this.parameters = parameters; this.baseline = baseline; this.mode = mode;
        this.preparation = preparation; this.checkpoint = checkpoint; this.traceLimit = traceLimit;
        for (int i = 0; i < heads.length; i++) heads[i] = new Head();
    }
    @Override public void initialized(List<PermutationSolution<Integer>> population) {
        if (scales != null || population.isEmpty()) throw new IllegalStateException("Initialize once from a nonempty evaluated population");
        scales = new double[3];
        for (PermutationSolution<Integer> solution : population) for (int q = 0; q < 3; q++) {
            double value = solution.getObjective(q);
            if (!Double.isFinite(value) || value < 0) throw new IllegalArgumentException("Non-finite or negative initialization objective");
            scales[q] += value / population.size();
        }
        for (int q = 0; q < 3; q++) if (!(scales[q] > 0)) scales[q] = 1;
        if (mode == Mode.TAIL || mode == Mode.VALUE || traceLimit > 0) {
            long start = System.nanoTime();
            try { features = new JointFeatures(in, parameters, checkpoint); }
            finally { featurePrecomputeNanos += System.nanoTime() - start; }
        }
    }
    @Override public void beginBatch(Direction direction) {
        if (scales == null || active != null) throw new IllegalStateException("Batch requires initialized, inactive policy");
        active = direction; Head head = head(direction);
        frozen = head.coefficients == null ? null : head.coefficients.clone(); frozenVersion = head.version;
        useValue = mode == Mode.VALUE && head.completed >= STARTUP_TRAJECTORIES && frozen != null;
    }
    @Override public PermutationSolution<Integer> propose(PermutationSolution<Integer> parent,
            PermutationSolution<Integer> personal, PermutationSolution<Integer> leader, Direction direction) {
        requireBatch(direction); checkpoint.run(); proposals++; long start = System.nanoTime();
        try {
            if (SeededRandom.current().nextDouble() >= GUIDED_PROBABILITY) {
                baselineProposals++; return baseline.update(parent, personal, leader);
            }
            return guided(parent, personal, leader, direction);
        } finally { proposeNanos += System.nanoTime() - start; }
    }
    /** Package-local direct path used only by focused contract checks, never to create free training data. */
    PermutationSolution<Integer> guided(PermutationSolution<Integer> parent,
            PermutationSolution<Integer> personal, PermutationSolution<Integer> leader, Direction direction) {
        requireBatch(direction); guidedProposals++; Random random = SeededRandom.current();
        int length = Math.min(BLOCK_LENGTH, in.jobs()), begin = random.nextInt(in.jobs() - length + 1);
        BlockContext block = new BlockContext(in, parent, begin, length);
        long start = System.nanoTime(); DynamicPrefix prefix = new DynamicPrefix(in, parameters);
        try { block.restorePrefix(prefix, checkpoint); } finally { prefixNanos += System.nanoTime() - start; }
        boolean capture = traceLimit > traces.size() + pending.size();
        Episode episode = new Episode(direction, capture ? JointTrace.begin(block, mode, frozenVersion, useValue) : null);
        if (episode.trace != null) {
            episode.trace.put("direction", direction.name()); episode.trace.put("scales", JointTrace.numbers(scales));
        }
        @SuppressWarnings("unchecked")
        PermutationSolution<Integer>[] teachers = new PermutationSolution[] {parent, personal, leader};
        while (block.remainingCount() > 0) {
            checkpoint.run(); start = System.nanoTime();
            List<JointAction> actions = JointCandidates.propose(block, teachers, random);
            if (actions.isEmpty()) {
                noLegalFallbacks++;
                // A compatible witness is a construction invariant, so this is a programming error.
                throw new IllegalStateException("No legal candidate despite compatible completion witness");
            }
            List<Choice> choices = score(actions, block, prefix, direction, capture);
            int chosen = choose(choices, random); Choice choice = choices.get(chosen);
            candidateNanos += System.nanoTime() - start;
            if (episode.trace != null) {
                start = System.nanoTime(); JointTrace.decision(episode.trace, choices, chosen);
                traceNanos += System.nanoTime() - start;
            }
            block.commit(choice.action, choice.witness); prefix = choice.after; selectedActions++;
            if (mode == Mode.VALUE) episode.states.add(new Afterstate(choice.state.features, scalar(choice.state.partial, direction)));
            if (useValue) learnedActions++;
        }
        checkpoint.run(); PermutationSolution<Integer> child = block.child(parent);
        pending.put(child, episode); preparation.accept(child, prefix);
        return child;
    }
    private List<Choice> score(List<JointAction> actions, BlockContext block, DynamicPrefix prefix, Direction direction, boolean capture) {
        List<Choice> choices = new ArrayList<>(); double before = scalar(prefix.partialObjectives(), direction);
        for (JointAction action : actions) {
            checkpoint.run(); DynamicPrefix after = prefix.copy(); BlockContext.append(after, action); stepTrials++;
            List<JointAction> witness = block.afterWitness(action); long start = System.nanoTime();
            JointFeatures.State state;
            if (mode == Mode.RANDOM && !capture || mode == Mode.GREEDY && !capture) {
                state = new JointFeatures.State(null, after.partialObjectives(), null);
            } else {
                state = features.summarize(after, block.projected(action, witness), block.future(witness),
                        block.remainingCount() - 1, scales);
            }
            featureNanos += System.nanoTime() - start;
            double delta = scalar(state.partial, direction) - before; start = System.nanoTime();
            double future = mode == Mode.GREEDY || mode == Mode.RANDOM ? 0
                    : useValue ? LinearValueModel.predict(frozen, state.features) : scalar(state.tail, direction);
            predictionNanos += System.nanoTime() - start;
            choices.add(new Choice(action, witness, after, state, delta, future));
        }
        return choices;
    }
    private int choose(List<Choice> choices, Random random) {
        if (mode == Mode.RANDOM) return random.nextInt(choices.size());
        if (random.nextDouble() < EPSILON) { exploredActions++; return random.nextInt(choices.size()); }
        List<Integer> tied = new ArrayList<>(); double best = Double.POSITIVE_INFINITY;
        for (int i = 0; i < choices.size(); i++) {
            double score = choices.get(i).score;
            if (!Double.isFinite(score)) throw new IllegalStateException("Non-finite action score");
            if (score < best) { best = score; tied.clear(); tied.add(i); }
            else if (score == best) tied.add(i);
        }
        return tied.get(random.nextInt(tied.size()));
    }
    @Override public void evaluated(PermutationSolution<Integer> child, Direction direction) {
        requireBatch(direction); Episode episode = pending.remove(child); if (episode == null) return;
        if (episode.direction != direction) throw new IllegalStateException("Direction changed during trajectory");
        double[] objectives = new double[3];
        for (int q = 0; q < 3; q++) {
            objectives[q] = child.getObjective(q);
            if (!Double.isFinite(objectives[q])) throw new IllegalStateException("Incomplete trajectory has no real objective label");
        }
        completed++; Head head = head(direction); head.completed++;
        if (mode == Mode.VALUE) {
            double total = scalar(objectives, direction), weight = 1.0 / episode.states.size();
            for (Afterstate state : episode.states) {
                double target = total - state.partial;
                if (target < -1e-9 * Math.max(1, Math.abs(total))) throw new IllegalStateException("Final objective precedes its physical prefix");
                head.samples.add(new LinearValueModel.Sample(state.features, Math.max(0, target), weight));
            }
            head.labelledStates += episode.states.size(); head.labelledTrajectories++;
            head.cohortTrajectories++;
        }
        if (episode.trace != null) {
            long start = System.nanoTime(); traces.add(JointTrace.finish(episode.trace, objectives));
            traceNanos += System.nanoTime() - start;
        }
    }
    @Override public void endBatch(Direction direction) {
        requireBatch(direction); Head head = head(direction);
        incomplete += pending.size(); pending.clear();
        try {
            if (mode == Mode.VALUE && head.cohortTrajectories >= STARTUP_TRAJECTORIES) {
                long start = System.nanoTime();
                try {
                    double[] fitted = LinearValueModel.fit(head.samples, JointFeatures.DIMENSION, checkpoint);
                    head.coefficients = fitted; head.version++; head.updates++; head.fittedStates += head.samples.size();
                    double totalWeight = 0;
                    for (LinearValueModel.Sample sample : head.samples) totalWeight += sample.weight;
                    head.fittedTrajectoryWeight += totalWeight;
                    head.samples.clear(); head.cohortTrajectories = 0;
                } finally { trainingNanos += System.nanoTime() - start; }
            }
        } finally { active = null; frozen = null; useValue = false; }
    }
    private void requireBatch(Direction direction) {
        if (direction == null || active != direction) throw new IllegalStateException("Joint policy used outside its frozen direction batch");
    }
    private Head head(Direction direction) { return heads[direction.ordinal()]; }
    private double scalar(double[] values, Direction direction) {
        if (direction.objective() >= 0) return values[direction.objective()] / scales[direction.objective()];
        double sum = 0; for (int q = 0; q < 3; q++) sum += values[q] / scales[q] / 3; return sum;
    }
    public List<Map<String, Object>> trajectories() { return Collections.unmodifiableList(new ArrayList<>(traces)); }
    public Map<String, Object> diagnostics() {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("mode", mode.name()); result.put("blockLength", BLOCK_LENGTH); result.put("candidateLimit", CANDIDATE_LIMIT);
        result.put("guidedProbability", GUIDED_PROBABILITY); result.put("epsilon", EPSILON); result.put("featureCount", JointFeatures.DIMENSION);
        result.put("startupTrajectoriesPerDirection", STARTUP_TRAJECTORIES); result.put("ridge", LinearValueModel.RIDGE);
        result.put("trainingWindow", "consecutive completed batches under one head version until at least 64 trajectories; clear after fit");
        result.put("scales", scales == null ? Collections.emptyList() : JointTrace.numbers(scales));
        result.put("proposals", proposals); result.put("baselineProposals", baselineProposals); result.put("guidedProposals", guidedProposals);
        result.put("completedTrajectories", completed); result.put("incompleteTrajectories", incomplete); result.put("pendingTrajectories", pending.size());
        result.put("noLegalFallbacks", noLegalFallbacks); result.put("candidateStepTrials", stepTrials); result.put("selectedActions", selectedActions);
        result.put("epsilonActions", exploredActions); result.put("learnedActions", learnedActions);
        result.put("proposeNanos", proposeNanos); result.put("prefixRestoreNanos", prefixNanos); result.put("candidateNanos", candidateNanos);
        result.put("featureNanos", featureNanos); result.put("predictionNanos", predictionNanos); result.put("trainingNanos", trainingNanos);
        result.put("featurePrecomputeNanos", featurePrecomputeNanos);
        result.put("traceLimit", traceLimit); result.put("traceCount", traces.size()); result.put("traceNanos", traceNanos);
        Map<String, Object> directions = new LinkedHashMap<>();
        for (Direction direction : Direction.values()) {
            Head h = head(direction); Map<String, Object> d = new LinkedHashMap<>();
            d.put("completedTrajectories", h.completed); d.put("labelledTrajectories", h.labelledTrajectories);
            d.put("labelledStates", h.labelledStates); d.put("modelVersion", h.version); d.put("updates", h.updates);
            d.put("fittedStates", h.fittedStates); d.put("fittedTrajectoryWeight", h.fittedTrajectoryWeight);
            d.put("pendingFittingTrajectories", h.cohortTrajectories); d.put("pendingFittingStates", h.samples.size());
            directions.put(direction.name(), Collections.unmodifiableMap(d));
        }
        result.put("perDirection", Collections.unmodifiableMap(directions)); return Collections.unmodifiableMap(result);
    }
    static final class Choice {
        final JointAction action; final List<JointAction> witness; final DynamicPrefix after;
        final JointFeatures.State state; final double delta, future, score;
        Choice(JointAction action, List<JointAction> witness, DynamicPrefix after, JointFeatures.State state, double delta, double future) {
            this.action = action; this.witness = witness; this.after = after; this.state = state;
            this.delta = delta; this.future = future; score = delta + future;
        }
    }
    private static final class Afterstate {
        final double[] features; final double partial;
        Afterstate(double[] features, double partial) { this.features = features; this.partial = partial; }
    }
    private static final class Episode {
        final Direction direction; final List<Afterstate> states = new ArrayList<>(); final Map<String, Object> trace;
        Episode(Direction direction, Map<String, Object> trace) { this.direction = direction; this.trace = trace; }
    }
    private static final class Head {
        double[] coefficients; long completed, labelledTrajectories, labelledStates, version, updates, fittedStates, cohortTrajectories;
        double fittedTrajectoryWeight; final List<LinearValueModel.Sample> samples = new ArrayList<>();
    }
}
