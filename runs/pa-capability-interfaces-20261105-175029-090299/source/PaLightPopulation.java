package research.dynamic;

import java.util.*;
import org.uma.jmetal.util.research.modelglobal.*;

/** Fee counters only; never reads state hashes or modifies learned subsets. */
final class PaLightPopulation implements PaPopulation.Observer {
    final Map<String,Long> fees = new LinkedHashMap<>();
    private void count(String key) { fees.put(key, fees.getOrDefault(key,0L)+1); }
    public void initial(int slot, PaIndividual point, PaInternalArchive.Flags flags) { count("initialization.evaluations"); }
    public void reencoded(int generation, int slot, PaIndividual before, PaIndividual after) { count("neutralReencodings"); }
    public void model(int generation, List<PaIndividual> population, double[][] dependency, List<int[]> subsets, long nanos) {
        count("modelBuilds"); fees.put("modelNanos", fees.getOrDefault("modelNanos",0L)+nanos);
    }
    public void step(int generation,int slot,int step,int subset,int donorSlot,PaIndividual parent,PaIndividual donor,
            PaIndividual child,boolean fallback,PaInternalArchive.Flags flags,boolean accepted) {
        count("global.evaluations"); if (fallback) count("emptyFactoryFallbacks"); if (accepted) count("acceptedMixingSteps");
    }
    public void programEnd(int generation,int slot,PaIndividual result) { count("completePrograms"); }
    public void generationEnd(int generation,List<PaIndividual> population) { count("completeGenerations"); }
}
