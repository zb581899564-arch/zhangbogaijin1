package org.uma.jmetal.util.research.modelglobal;

import java.nio.ByteBuffer;
import java.security.MessageDigest;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.search.Direction;

/** Immutable search state; only the evaluator may create a modified solution copy. */
public final class PaIndividual {
    private static final boolean TRACE_IDENTITY = Boolean.parseBoolean(System.getProperty("research.pa.traceIdentity", "true"));
    public final long id, paidFE;
    public final Direction role;
    public final TypedScheduleGenome genome;
    public final String hash;
    final PermutationSolution<Integer> point;
    private final double[] objectives;

    PaIndividual(long stateId, long paid, Direction preference, TypedScheduleGenome genes, PermutationSolution<Integer> value) {
        id = stateId; paidFE = paid; role = preference; genome = genes; point = value;
        objectives = value.getObjectives().clone(); hash = TRACE_IDENTITY ? identity(genes, objectives) : null;
    }

    public double[] objectives() { return objectives.clone(); }

    private static String identity(TypedScheduleGenome genome, double[] objectives) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            int[] resources = genome.allocations(); double[] keys = genome.priorities();
            ByteBuffer bytes = ByteBuffer.allocate(4 + 4 * resources.length + 8 * keys.length + 24);
            bytes.putInt(resources.length); for (int id : resources) bytes.putInt(id);
            for (double key : keys) bytes.putDouble(key); for (double value : objectives) bytes.putDouble(value);
            StringBuilder text = new StringBuilder();
            for (byte b : digest.digest(bytes.array())) text.append(Character.forDigit((b >>> 4) & 15, 16)).append(Character.forDigit(b & 15, 16));
            return text.toString();
        } catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
