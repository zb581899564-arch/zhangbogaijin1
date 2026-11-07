package org.uma.jmetal.util.research.search;

import java.util.*;

/** Diagnostic fixed-FA subproblem only. Default OFF preserves every original mutation. */
public final class FixedFAMutationMask {
    private static final boolean ENABLED=Boolean.getBoolean("research.fixedFA.enabled");
    private static long aligned,classic;
    private FixedFAMutationMask() { }
    public static boolean skipAligned() {if(ENABLED)aligned++;return ENABLED;}
    public static boolean skipClassic() {if(ENABLED)classic++;return ENABLED;}
    public static Map<String,Object> diagnostics() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("enabled",ENABLED);
        out.put("alignedFactoryMutationsSkipped",aligned);out.put("classicFactoryMutationsSkipped",classic);
        out.put("scope","Only factory-mutation bodies masked; original trigger draws and non-FA operators remain.");return out;
    }
}
