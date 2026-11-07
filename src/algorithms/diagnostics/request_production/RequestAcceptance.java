package org.uma.jmetal.util.research.search;

import java.util.*;
import org.uma.jmetal.util.research.modelglobal.PaInternalArchive;

/** The only experimental treatment: production acceptance after an ordinary paid GOM move. */
final class RequestAcceptance {
    static final Set<String> ARMS = new LinkedHashSet<>(Arrays.asList("ROLE", "REQUEST", "ORDINARY", "SHUFFLED"));
    private final String arm;
    private final RequestSpec target;
    private final Map<String,Long> counts = new LinkedHashMap<>();

    RequestAcceptance(String mode, RequestSpec effective) {
        if (!ARMS.contains(mode)) throw new IllegalArgumentException("Unknown arm " + mode);
        arm = mode; target = effective;
    }

    Decision decide(Direction role, double[] child, double[] parent, double[] childFactory,
            double[] parentFactory, PaInternalArchive.Flags flags) {
        boolean original = role == Direction.CENTER
            ? PaInternalArchive.weaklyDominates(child, parent) || !flags.dominated
            : child[role.objective()] < parent[role.objective()];
        double candidateViolation = target.violation(childFactory), parentViolation = target.violation(parentFactory);
        boolean keep;
        String reason;
        if (arm.equals("ROLE")) { keep = original; reason = "ORIGINAL_ROLE"; }
        else if (candidateViolation < parentViolation) { keep = true; reason = "LOWER_VIOLATION"; }
        else if (candidateViolation > parentViolation) { keep = false; reason = "HIGHER_VIOLATION"; }
        else if (arm.equals("ORDINARY")) {
            keep = target.score(child) < target.score(parent); reason = "EQUAL_VIOLATION_WEIGHTED";
        } else { keep = original; reason = "EQUAL_VIOLATION_ROLE"; }
        count(reason); count("proposed." + role.name());
        if (keep) count("accepted." + role.name());
        if (keep != original) count("changedVersusOriginalRole");
        if (candidateViolation == 0) count("candidateFeasible");
        return new Decision(keep, original, reason, parentViolation, candidateViolation);
    }

    private void count(String key) { counts.put(key, counts.getOrDefault(key, 0L) + 1); }
    Map<String,Long> receipt() { return new LinkedHashMap<>(counts); }

    static final class Decision {
        final boolean keep, original;
        final String reason;
        final double parentViolation, childViolation;
        Decision(boolean accepted, boolean baseline, String why, double before, double after) {
            keep = accepted; original = baseline; reason = why; parentViolation = before; childViolation = after;
        }
        Map<String,Object> record() {
            return GomRecords.row("accepted", keep, "originalRoleWouldAccept", original, "acceptanceReason", reason,
                "parentViolation", parentViolation, "candidateViolation", childViolation);
        }
    }
}
