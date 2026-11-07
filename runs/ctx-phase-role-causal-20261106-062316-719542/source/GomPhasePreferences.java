package org.uma.jmetal.util.research.search;

/** One registered-cycle intervention; physical decomposition and all other cycles stay original. */
public final class GomPhasePreferences {
    private static final String GLOBAL=level("research.ctxPhase.global");
    private static final String LOCAL=level("research.ctxPhase.local");
    private GomPhasePreferences() { }
    private static String level(String key) {
        String value=System.getProperty(key,"ROLE");
        if(!value.equals("ROLE")&&!value.equals("CENTER"))throw new IllegalArgumentException(key);
        return value;
    }
    private static boolean active() { return GomRunScope.require().completedPasses==9; }
    static Direction global(Direction original) { return active()&&GLOBAL.equals("CENTER")?Direction.CENTER:original; }
    static Direction local(Direction original) { return active()&&LOCAL.equals("CENTER")?Direction.CENTER:original; }
}
