package research.dynamic;

import java.util.*;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.*;
import org.uma.jmetal.util.research.modelglobal.*;

/** Independent Java encoding check for a frozen, Python-built four-atom matrix. */
final class CounterfactualInputs {
    private CounterfactualInputs() { }

    static final class Entry {
        final String id;
        final int mask;
        final int[] resources;
        final double[] keys, expected;
        final FourVectors vectors;

        Entry(String line, FirstStageCatalog catalog) {
            String[] fields = line.split("\t", -1);
            if (fields.length != 9) throw new IllegalArgumentException("Expected nine TSV columns");
            id = fields[0]; mask = Integer.parseInt(fields[1]);
            resources = ints(fields[2]); keys = doubles(fields[3]); expected = doubles(fields[8]);
            if (mask < 0 || mask > 15) throw new IllegalArgumentException("Invalid atom mask");
            vectors = TypedScheduleGenome.of(catalog, resources, keys).toVectors();
            int[][] actual = {vectors.jobs(), vectors.factories(), vectors.machines(), vectors.workers()};
            for (int k = 0; k < 4; k++)
                if (!Arrays.equals(actual[k], ints(fields[4 + k])))
                    throw new AssertionError("Python/Java encoding differs: " + id + " mask " + mask);
        }
    }

    private static int[] ints(String text) {
        return Arrays.stream(text.split(",")).mapToInt(Integer::parseInt).toArray();
    }
    private static double[] doubles(String text) {
        return text.isEmpty() ? new double[0] : Arrays.stream(text.split(",")).mapToDouble(Double::parseDouble).toArray();
    }

    @SuppressWarnings("unchecked")
    static PermutationSolution<Integer> point(Problem<PermutationSolution<Integer>> problem, Entry e) {
        PermutationSolution<Integer> p = problem.createSolution();
        List<Integer> machines = (List<Integer>) p.getAttribute("machine");
        int[] js=e.vectors.jobs(), fa=e.vectors.factories(), ma=e.vectors.machines(), wa=e.vectors.workers();
        for (int i=0; i<js.length; i++) {
            p.setVariableValue(i,js[i]); p.setVariableValueid(i,fa[i]);
            machines.set(i,ma[i]); p.setVariableValueworker(i,wa[i]);
        }
        return p;
    }

    static Map<String,Object> record(Entry e, DynamicSchedule s, long number) {
        Map<String,Object> row=new LinkedHashMap<>();
        row.put("id",e.id); row.put("mask",e.mask); row.put("number",number);
        row.put("resources",e.resources); row.put("keys",e.keys);
        row.put("JS",s.js()); row.put("FA",s.fa()); row.put("MA",s.ma()); row.put("WA",s.wa());
        row.put("objectives",s.objectives()); row.put("factoryMakespan",s.factoryMakespan());
        row.put("factoryEnergy",s.factoryEnergy()); row.put("factoryCost",s.factoryCost());
        row.put("recomputedOperations",s.recomputedOperations()); row.put("reusedOperations",s.reusedOperations());
        List<Object[]> steps=new ArrayList<>();
        for (DynamicStep step:s.steps()) steps.add(new Object[]{step.job(),step.factory(),step.stage(),
            step.machine(),step.worker(),step.start(),step.base(),step.duration(),step.setupDuration(),
            step.completion(),step.u(),step.v(),step.energy(),step.labor(),step.exposure()});
        row.put("steps",steps);
        return row;
    }
}
