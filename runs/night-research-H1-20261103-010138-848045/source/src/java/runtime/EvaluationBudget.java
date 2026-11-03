package org.uma.jmetal.util.research.runtime;

/** Counts decoder attempts, including attempts that throw or produce invalid objectives. */
public final class EvaluationBudget {
    private final long limit;
    private final Thread owner;
    private long attempted;
    private long successful;
    private long failed;
    private long timeInterrupted;

    public EvaluationBudget(long limit) {
        if (limit < 0) { throw new IllegalArgumentException("FE limit must be nonnegative"); }
        this.limit = limit;
        owner = Thread.currentThread();
    }

    void acquire() {
        requireOwner();
        if (attempted == limit) { throw new BudgetExhaustedException(this); }
        attempted++;
    }

    void success() { requireOwner(); successful++; }
    void failure() { requireOwner(); failed++; }
    void timeInterrupted() { requireOwner(); timeInterrupted++; }

    public long limit() { return limit; }
    public long attempted() { requireOwner(); return attempted; }
    public long successful() { requireOwner(); return successful; }
    public long failed() { requireOwner(); return failed; }
    public long timeInterruptedAttempts() { requireOwner(); return timeInterrupted; }
    public long remaining() { requireOwner(); return limit - attempted; }

    void requireOwner() {
        if (Thread.currentThread() != owner) {
            throw new IllegalStateException("This FE budget supports its creating thread only");
        }
    }
}
