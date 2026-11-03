package org.uma.jmetal.util.research.joint;

/** A complete first-stage action. Resource identifiers are local to its factory. */
public final class JointAction {
    private final int job, factory, machine, worker;
    public JointAction(int job, int factory, int machine, int worker) {
        this.job = job; this.factory = factory; this.machine = machine; this.worker = worker;
    }
    public int job() { return job; }
    public int factory() { return factory; }
    public int machine() { return machine; }
    public int worker() { return worker; }
    public int[] tuple() { return new int[] {job, factory, machine, worker}; }
    @Override public boolean equals(Object value) {
        if (!(value instanceof JointAction)) return false;
        JointAction a = (JointAction) value;
        return job == a.job && factory == a.factory && machine == a.machine && worker == a.worker;
    }
    @Override public int hashCode() { return (((job * 31) + factory) * 31 + machine) * 31 + worker; }
    @Override public String toString() { return job + ":" + factory + ":" + machine + ":" + worker; }
}
