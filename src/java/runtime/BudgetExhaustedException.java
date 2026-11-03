package org.uma.jmetal.util.research.runtime;

/** Control flow raised before an evaluation that would exceed its FE budget. */
public final class BudgetExhaustedException extends RuntimeException {
    private static final long serialVersionUID = 1L;
    private final EvaluationBudget budget;

    BudgetExhaustedException(EvaluationBudget budget) {
        super("Evaluation budget exhausted: " + budget.attempted() + "/" + budget.limit());
        this.budget = budget;
    }

    boolean belongsTo(EvaluationBudget expected) { return budget == expected; }
}
