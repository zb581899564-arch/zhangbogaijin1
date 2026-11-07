package org.uma.jmetal.util.research.modelglobal;

import java.nio.ByteBuffer;
import java.security.MessageDigest;
import java.util.Arrays;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.search.Direction;

/** Immutable direct-genome state; the paid evaluator alone creates the associated solution copy. */
public final class QpaIndividual {
    private static final boolean TRACE = Boolean.parseBoolean(System.getProperty("research.pa.traceIdentity", "true"));
    public final long id, paidFE;
    public final Direction role;
    public final DirectScheduleGenome genome;
    public final String hash;
    final PermutationSolution<Integer> point;
    private final double[] objectives;

    QpaIndividual(long state, long paid, Direction preference, DirectScheduleGenome genes, PermutationSolution<Integer> value) {
        id = state; paidFE = paid; role = preference; genome = genes; point = value;
        objectives = value.getObjectives().clone(); hash = TRACE ? identity() : null;
    }
    public double[] objectives() { return objectives.clone(); }

    /** Engineering-only assertion that neither shared lists nor cached source encodings were mutated. */
    public void verifyStoredView() {
        FourVectors vectors = genome.toVectors();
        if (!Arrays.equals(vectors.jobs(), SchedulingEncoding.integers(point.getVariables()))
                || !Arrays.equals(vectors.factories(), SchedulingEncoding.integers(point.getVariablesid()))
                || !Arrays.equals(vectors.machines(), SchedulingEncoding.machineIntegers(point))
                || !Arrays.equals(vectors.workers(), SchedulingEncoding.integers(point.getVariablesworker()))
                || !Arrays.equals(objectives, point.getObjectives())) throw new AssertionError("Stored direct state mutated");
    }

    private String identity() {
        try {
            int[] resources = genome.resources(), positions = genome.positions();
            ByteBuffer data = ByteBuffer.allocate(4 + 8 * resources.length + 24);
            data.putInt(resources.length); for (int value : resources) data.putInt(value);
            for (int value : positions) data.putInt(value); for (double value : objectives) data.putDouble(value);
            StringBuilder result = new StringBuilder(64);
            for (byte value : MessageDigest.getInstance("SHA-256").digest(data.array()))
                result.append(Character.forDigit((value >>> 4) & 15, 16)).append(Character.forDigit(value & 15, 16));
            return result.toString();
        } catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
}
