package org.uma.jmetal.util.research.runtime;

import java.util.Objects;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.Solution;

/** The single evaluation boundary shared by initialization, global search and local search. */
public final class BudgetedProblem<S extends Solution<?>> implements Problem<S> {
    private static final long serialVersionUID = 1L;
    private final Problem<S> delegate;
    private final EvaluationBudget budget;
    private final ThreeObjectiveArchive<S> archive;
    private final RunClock clock;
    private EvaluationObserver observer;
    private EvaluationAudit<S> audit;

    public void setObserver(EvaluationObserver value) { observer = value; }
    public void setAudit(EvaluationAudit<S> value) { audit = value; }

    public BudgetedProblem(Problem<S> delegate, EvaluationBudget budget, ThreeObjectiveArchive<S> archive) {
        this(delegate, budget, archive, null);
    }

    BudgetedProblem(Problem<S> delegate, EvaluationBudget budget, ThreeObjectiveArchive<S> archive, RunClock clock) {
        this.delegate = Objects.requireNonNull(delegate, "problem");
        this.budget = Objects.requireNonNull(budget, "budget");
        this.archive = Objects.requireNonNull(archive, "archive");
        this.clock = clock;
        if (delegate.getNumberOfObjectives() != 3) {
            throw new IllegalArgumentException("Budgeted problem requires the three-objective contract");
        }
    }

    @Override public void evaluate(S solution) {
        Objects.requireNonNull(solution, "solution");
        checkpoint();
        budget.acquire();
        boolean changed;
        try {
            delegate.evaluate(solution);
            if (clock != null) clock.checkpoint();
            changed = archive.addEvaluated(solution);
        } catch (TimeBudgetExceededException exception) {
            budget.failure(); budget.timeInterrupted();
            throw exception;
        } catch (RuntimeException | Error exception) {
            budget.failure();
            throw exception;
        }
        budget.success();
        if (observer != null) observer.completedSolution(solution, budget.successful(), clock == null ? 0 : clock.elapsedSeconds(), changed, archive);
        if (audit != null) audit.completed(solution, budget.successful(), clock == null ? 0 : clock.elapsedSeconds(), changed);
    }

    /** Outside evaluation only: do not check remaining FE inside the last acquired decode. */
    public void checkpoint() {
        budget.requireOwner();
        if (budget.remaining() == 0) throw new BudgetExhaustedException(budget);
        if (clock != null) clock.checkpoint();
    }
    @Override public S createSolution() { checkpoint(); return delegate.createSolution(); }
    @Override public int getNumberOfVariables() { return delegate.getNumberOfVariables(); }
    @Override public int getNumberOfObjectives() { return delegate.getNumberOfObjectives(); }
    @Override public int getNumberOfConstraints() { return delegate.getNumberOfConstraints(); }
    @Override public String getName() { return delegate.getName(); }
}
