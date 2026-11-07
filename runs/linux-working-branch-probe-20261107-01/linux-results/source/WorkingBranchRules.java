package research.dynamic;

import java.util.*;
import org.uma.jmetal.util.research.modelglobal.PaInternalArchive;
import org.uma.jmetal.util.research.search.Direction;

/** Exact native GOM formula, including weak equality for CENTER and strict boundary improvement. */
final class WorkingBranchRules {
    private WorkingBranchRules() { }
    static boolean keep(Direction role,double[] child,double[] parent,PaInternalArchive.Flags flags) {
        return role==Direction.CENTER ? PaInternalArchive.weaklyDominates(child,parent)||!flags.dominated
                : child[role.objective()]<parent[role.objective()];
    }
    static boolean commit(Direction role,double[] child,double[] parent,List<double[]> base) {
        if(role!=Direction.CENTER)return child[role.objective()]<parent[role.objective()];
        if(PaInternalArchive.weaklyDominates(child,parent))return true;
        for(double[] p:base)if(PaInternalArchive.dominates(p,child))return false;return true;
    }
    static boolean fresh(double[] child,List<double[]> base) {
        for(double[] p:base)if(PaInternalArchive.weaklyDominates(p,child))return false;return true;
    }
}
