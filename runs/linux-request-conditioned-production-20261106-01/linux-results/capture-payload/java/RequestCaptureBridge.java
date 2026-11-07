package org.uma.jmetal.util.research.search;

import java.util.Map;
import research.dynamic.ClassResolutionProbe;
import research.dynamic.DynamicJson;

/** Read-only access to package-private run state; never advances search or RNG. */
public final class RequestCaptureBridge {
    private RequestCaptureBridge() { }

    public static long currentFE() {
        return GomRunScope.require().run.budget().successful();
    }

    public static double[][] archive() {
        return GomRunScope.require().archive();
    }

    public static Map<String, Object> loadedClasses(boolean includeCapture) throws Exception {
        String[] names = {
            "org.uma.jmetal.util.research.cooperation.CooperationSupport",
            "org.uma.jmetal.util.research.cooperation.FactoryPool",
            "org.uma.jmetal.util.research.cooperation.FactoryRecord",
            "org.uma.jmetal.util.research.cooperation.FamilyContexts",
            "org.uma.jmetal.util.research.cooperation.CooperationEvidence",
            "org.uma.jmetal.util.research.search.CanonicalHmopso",
            "org.uma.jmetal.util.research.search.DonorCapture",
            "org.uma.jmetal.util.research.search.SearchState",
            "org.uma.jmetal.util.research.search.GomRunScope",
            "org.uma.jmetal.util.research.search.GomRecords",
            "org.uma.jmetal.util.research.modelglobal.PaInternalArchive",
            "org.uma.jmetal.util.research.runtime.RunContext",
            "org.uma.jmetal.util.research.runtime.BudgetedProblem",
            "org.uma.jmetal.util.research.DynamicEvaluation",
            "research.dynamic.DynamicJson", "research.dynamic.ClassResolutionProbe"
        };
        Map<String, Object> result = ClassResolutionProbe.capture(names);
        if (includeCapture) result.putAll(ClassResolutionProbe.capture(
            "org.uma.jmetal.util.research.cooperation.RequestCapture",
            "org.uma.jmetal.util.research.search.RequestCaptureBridge"));
        return result;
    }

    /** Class-resource identity only; does not construct a run or evaluate a solution. */
    public static void main(String[] args) throws Exception {
        System.out.println(DynamicJson.encode(loadedClasses(args.length == 0)));
    }
}
