package research.dynamic;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.cooperation.JointFamilyBridgeProbe;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.runtime.SeededRandom;

/** Known paid imports and unscored genotype fixtures only. Calling evaluate is a hard error. */
public final class JointFamilyAuditRun {
    private JointFamilyAuditRun() { }
    public static void main(String[] args) throws Exception {
        Path input = Paths.get(args[0]), out = Paths.get(args[3]); Files.createDirectories(out);
        System.setProperty("dhfsp.dataDir", input.getParent().toString()); System.setProperty("dhfsp.setupFile", args[1]); System.setProperty("dhfsp.standbyPower", "1");
        String[] d = input.getFileName().toString().replace(".txt", "").split("_");
        EDHHFSPW raw = new EDHHFSPW(Integer.parseInt(d[0]), Integer.parseInt(d[1]), Integer.parseInt(d[2]), Integer.parseInt(d[3])) {
            @Override public void evaluate(PermutationSolution<Integer> ignored) { throw new AssertionError("Unscored fixture attempted evaluation"); }
        };
        Instance instance = raw.getSchedulingInstance();
        if (!instance.satisfiesDualResourceCondition()) throw new IllegalArgumentException("Unqualified instance");
        SeededRandom.reset(14770003); List<PermutationSolution<Integer>> points = new ArrayList<>();
        for (String line : Files.readAllLines(Paths.get(args[2]), StandardCharsets.UTF_8)) {
            String[] f = line.split("\t"); PermutationSolution<Integer> point = raw.createSolution();
            ProbeData.fill(point, f, 1, -1, null); String[] values = f[0].split(",");
            for (int k = 0; k < 3; k++) point.setObjective(k, Double.parseDouble(values[k])); points.add(point);
        }
        Map<String,Object> evidence = new JointFamilyBridgeProbe(instance, points).run();
        evidence.putAll(NeutralProbeSupport.row("status", "COMPLETE", "knownPaidSources", points.size(), "newSearchFE", 0,
            "decoderCalls", 0, "defaultMainlineChanged", false, "goalAchieved", false));
        NeutralProbeSupport.append(out.resolve("receipt.jsonl"), evidence);
        NeutralProbeSupport.append(out.resolve("loaded-identity.jsonl"), ClassResolutionProbe.capture("research.dynamic.JointFamilyAuditRun",
            "org.uma.jmetal.util.research.cooperation.JointFamilyBridgeProbe", "org.uma.jmetal.util.research.cooperation.FamilyContexts",
            "org.uma.jmetal.util.research.cooperation.CooperationSupport", "org.uma.jmetal.util.research.modelglobal.PaMixingMove",
            "org.uma.jmetal.util.research.modelglobal.TypedScheduleGenome", "org.uma.jmetal.util.research.modelglobal.FirstStageCatalog"));
    }
}
