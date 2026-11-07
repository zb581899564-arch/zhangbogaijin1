package research.dynamic;

import java.io.InputStream;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.util.research.search.ReverseAudit;

/** Actual class loader/code source and bytecode digest, separate from dependency file digests. */
final class ReverseClassOrigins {
    private ReverseClassOrigins() {}
    static void write(Path out) throws Exception {
        String prefix = "org.uma.jmetal.util.research.";
        String[] relative = {"search.CanonicalHmopso", "search.LocalSearch", "search.SearchState", "search.Direction",
                "search.Particle", "search.ParetoTools", "search.QTable", "search.SurvivorSelection", "search.QgsLocalLedger",
                "search.ReverseAudit", "search.DeepLocalVisits", "classic.ClassicAlgorithm", "classic.ClassicVariation",
                "classic.NsgaSelection", "cooperation.CooperationSupport", "cooperation.FamilyContexts",
                "cooperation.FactoryPool", "cooperation.ReversePoolSnapshots", "mechanism.JobAlignedPolicy",
                "runtime.RunContext", "runtime.SeededRandom", "runtime.BudgetedProblem",
                "DynamicEvaluation", "model.DynamicDecoder", "model.DynamicPhysics"};
        List<Map<String, Object>> classes = new ArrayList<>();
        classes.add(origin(LongBudgetRun.class.getName()));
        classes.add(origin(AnytimeRecorder.class.getName()));
        classes.add(origin("org.uma.jmetal.problem.multiobjective.dfsp.EDHHFSPW"));
        classes.add(origin("org.uma.jmetal.solution.impl.DefaultIntegerPermutationSolution"));
        for (String name : relative) classes.add(origin(prefix + name));
        Map<String, Object> row = ReverseAudit.row("javaRuntime", System.getProperty("java.runtime.version"),
                "javaVendor", System.getProperty("java.vendor"), "classPath", System.getProperty("java.class.path"),
                "classes", classes);
        Files.write(out.resolve("class-origins.json"), DynamicJson.encode(row).getBytes(StandardCharsets.UTF_8));
    }
    private static Map<String, Object> origin(String name) throws Exception {
        Class<?> clazz = Class.forName(name, false, LongBudgetRun.class.getClassLoader());
        URL source = clazz.getProtectionDomain().getCodeSource().getLocation();
        URL resource = clazz.getResource("/" + name.replace('.', '/') + ".class");
        if (resource == null || (!resource.toString().startsWith(source.toString())
                && !resource.toString().startsWith("jar:" + source + "!/")))
            throw new IllegalStateException("Class resource does not match its CodeSource: " + name);
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream stream = resource.openStream()) {
            byte[] buffer = new byte[8192];
            for (int n; (n = stream.read(buffer)) != -1;) digest.update(buffer, 0, n);
        }
        StringBuilder hash = new StringBuilder();
        for (byte b : digest.digest()) hash.append(String.format("%02x", b & 0xff));
        return ReverseAudit.row("name", name, "codeSource", source.toString(),
                "resource", resource.toString(), "sha256", hash.toString());
    }
}
