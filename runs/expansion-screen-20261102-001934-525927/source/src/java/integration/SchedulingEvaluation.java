package org.uma.jmetal.util.research;

import java.io.IOException;
import java.nio.file.Paths;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.Decoder;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.model.InstanceLoader;
import org.uma.jmetal.util.research.model.Schedule;
import org.uma.jmetal.util.research.model.SetupTimes;
import org.uma.jmetal.util.research.model.Validator;

/** Explicit data provenance, canonical decoding and the physical three-objective contract. */
public final class SchedulingEvaluation {
    private SchedulingEvaluation() { }

    public static Instance load(String file, int chapter, int jobs, int stages) throws IOException {
        String standby = System.getProperty("dhfsp.standbyPower");
        if (standby == null) throw new IllegalArgumentException("Specify dhfsp.standbyPower and record its source");
        double power = Double.parseDouble(standby);
        if (chapter == 3) return InstanceLoader.loadChapter3(Paths.get(file), power);
        String setupFile = System.getProperty("dhfsp.setupFile");
        if (setupFile == null) throw new IllegalArgumentException(
                "Chapter4 requires independent dhfsp.setupFile with provenance; no processing-time proxy is allowed");
        return InstanceLoader.loadChapter4(Paths.get(file), SetupTimes.fromFile(Paths.get(setupFile), jobs, stages), power);
    }

    @SuppressWarnings("unchecked")
    public static void evaluate(PermutationSolution<Integer> solution, Instance in) {
        int repaired = SchedulingEncoding.repair(solution, in);
        Schedule schedule = Decoder.decode(in, SchedulingEncoding.integers(solution.getVariables()),
                SchedulingEncoding.integers(solution.getVariablesid()),
                SchedulingEncoding.integers((List<Integer>) solution.getAttribute("machine")),
                SchedulingEncoding.integers(solution.getVariablesworker()));
        if (Boolean.getBoolean("dhfsp.validateEveryEvaluation")) Validator.validate(in, schedule);
        double[] objectives = schedule.objectives();
        if (solution.getNumberOfObjectives() != 3) throw new IllegalArgumentException("Expected physical objectives only");
        for (int i = 0; i < 3; i++) solution.setObjective(i, objectives[i]);
        solution.setAttribute(SchedulingMetadata.KEY, new SchedulingMetadata(
                schedule.factoryMakespan(), schedule.factoryEnergy(), schedule.factoryCost()));
        solution.setAttribute(SchedulingMetadata.SCHEDULE_KEY, schedule);
        solution.setAttribute("dhfsp.repairs", repaired);
        solution.setAttribute("dhfsp.modelProvenance", in.provenance());
    }
}
