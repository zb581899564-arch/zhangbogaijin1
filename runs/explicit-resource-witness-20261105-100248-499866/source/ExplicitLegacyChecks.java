package org.uma.jmetal.util.research.model;

/** Test-only bridge: a changed binding must not be mislabeled as an old-policy schedule. */
public final class ExplicitLegacyChecks {
    private ExplicitLegacyChecks() { }

    public static void requireRejection(Instance instance, DynamicParameters parameters, ExplicitSchedule value) {
        DynamicSchedule mislabeled = new DynamicSchedule(instance, parameters, value.js(), value.fa(),
                value.ma(), value.wa(), value.steps(), 0, value.steps().size());
        try {
            DynamicValidator.validate(instance, parameters, mislabeled);
        } catch (IllegalStateException expected) {
            if (!expected.getMessage().contains("Wrong operation order or resource binding")) throw expected;
            return;
        }
        throw new AssertionError("Different binding was accepted as original policy");
    }
}
