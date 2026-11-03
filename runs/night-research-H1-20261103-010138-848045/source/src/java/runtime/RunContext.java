package org.uma.jmetal.util.research.runtime;

import java.util.List;
import java.util.Objects;
import org.uma.jmetal.algorithm.Algorithm;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.Solution;

/** Owns one guarded run; start a separate JVM for every chapter/instance/seed configuration. */
public final class RunContext<S extends Solution<?>> {
    private final EvaluationBudget budget;
    private final ThreeObjectiveArchive<S> archive = new ThreeObjectiveArchive<>();
    private final BudgetedProblem<S> problem;
    private final long seed;
    private final RunClock clock;
    private String stopReason = "NOT_STARTED";
    private boolean started;

    public RunContext(Problem<S> delegate, long feLimit, long seed) {
        this(delegate, feLimit, seed, Double.POSITIVE_INFINITY);
    }

    public RunContext(Problem<S> delegate, long feLimit, long seed, double seconds) {
        this.seed = seed;
        clock = new RunClock(seconds);
        budget = new EvaluationBudget(feLimit);
        problem = new BudgetedProblem<>(delegate, budget, archive, clock);
        SeededRandom.reset(seed);
    }

    public BudgetedProblem<S> problem() { return problem; }
    public EvaluationBudget budget() { return budget; }
    public long seed() { return seed; }
    public void checkpoint() { budget.requireOwner(); clock.checkpoint(); }
    public RunClock clock() { return clock; }
    public String stopReason() { return stopReason; }
    public List<S> result() { budget.requireOwner(); return archive.snapshot(); }

    public void run(Algorithm<?> algorithm) {
        budget.requireOwner();
        Objects.requireNonNull(algorithm, "algorithm");
        if (started) { throw new IllegalStateException("A run context may execute once only"); }
        started = true;
        clock.start();
        if (budget.remaining() == 0) { stopReason = "FE_LIMIT"; clock.stop(); return; }
        try {
            clock.checkpoint();
            algorithm.run();
            stopReason = "ALGORITHM_RETURNED";
        } catch (BudgetExhaustedException exhausted) {
            if (!exhausted.belongsTo(budget)) { throw exhausted; }
            stopReason = "FE_LIMIT";
            // The current swarm may be half evaluated. Return only independent archive snapshots.
        } catch (TimeBudgetExceededException exhausted) {
            if (!exhausted.belongsTo(clock)) throw exhausted;
            stopReason = "TIME_LIMIT";
        } catch (RuntimeException | Error failure) {
            stopReason = "FAILED";
            throw failure;
        } finally {
            clock.stop();
        }
    }
}
