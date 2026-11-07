import java.nio.file.*;
public class CenterClassCheck {
  public static void main(String[] args) throws Exception {
    Path overlay = Paths.get(args[0]).toRealPath(), base = Paths.get(args[1]).toRealPath();
    String p = "org.uma.jmetal.util.research.search.";
    for (String c : new String[] {p+"CenterReferenceProbe",p+"CenterRoleSwapProbe",p+"CenterCrossSearch",p+"LocalSearch","research.dynamic.CenterCrossRun"}) {
      Class<?> k=Class.forName(c,false,CenterClassCheck.class.getClassLoader());
      Path where=Paths.get(k.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
      if (!where.equals(c.endsWith("Probe") ? overlay : base)) throw new AssertionError(c+" "+where);
      System.out.println(c+" "+where);
    }
    System.out.println(System.getProperty("java.runtime.version"));
  }
}
