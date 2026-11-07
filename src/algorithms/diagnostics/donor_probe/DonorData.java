package org.uma.jmetal.util.research.search;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.modelglobal.*;

/** Explicit TSV interchange; loading and deduplication never evaluate a candidate. */
final class DonorData {
    static final class Entry {
        String source;int family;long paidBy;Direction role;PermutationSolution<Integer> point;TypedScheduleGenome genes;String physical;
    }
    final List<Entry> receivers=new ArrayList<>(),external=new ArrayList<>(),imported=new ArrayList<>();
    final List<double[]> background=new ArrayList<>();
    final Map<String,Integer> counts=new TreeMap<>();
    DonorData(Path directory,Problem<PermutationSolution<Integer>> raw,Instance in,long viewSeed)throws IOException {
        FirstStageCatalog catalog=new FirstStageCatalog(in);Set<String> initial=new HashSet<>();
        Map<String,Entry> unique=new LinkedHashMap<>();
        for(String line:Files.readAllLines(directory.resolve("points.tsv"),StandardCharsets.UTF_8)) {
            String[] f=line.split("\t");Entry e=new Entry();e.source=f[0];e.paidBy=Long.parseLong(f[2]);e.role=Direction.valueOf(f[3]);e.family=Integer.parseInt(f[4]);
            int[] js=ints(f[6]),fa=ints(f[7]),ma=ints(f[8]),wa=ints(f[9]);
            PermutationSolution<Integer> p=raw.createSolution();
            @SuppressWarnings("unchecked") List<Integer> machines=(List<Integer>)p.getAttribute("machine");
            for(int i=0;i<js.length;i++){p.setVariableValue(i,js[i]);p.setVariableValueid(i,fa[i]);p.setVariableValueworker(i,wa[i]);machines.set(i,ma[i]);}
            String[] objectives=f[5].split(",");for(int i=0;i<3;i++)p.setObjective(i,Double.parseDouble(objectives[i]));
            p.setAttribute("cooperation.family",e.family);
            if(e.family>=0){int[] fixed=new int[js.length];for(int i=0;i<js.length;i++)fixed[js[i]]=fa[i];p.setAttribute("cooperation.fixedFactoryByJob",fixed);}
            if(SchedulingEncoding.repair(p,in)!=0)throw new AssertionError("Imported point needed repair");
            e.point=p;e.physical=physical(p,in.factories());imported.add(e);
            counts.put(e.source+"/raw/"+e.family,counts.getOrDefault(e.source+"/raw/"+e.family,0)+1);
            String key=e.family+"/"+e.physical;
            if(e.source.equals("P")){receivers.add(e);initial.add(key);continue;}
            if(initial.contains(key))continue;
            Entry old=unique.get(key);
            if(old==null)unique.put(key,e);else if(!old.source.contains(e.source))old.source="GS";
        }
        if(receivers.size()!=100)throw new AssertionError("100 imported receivers required");
        for(Entry e:unique.values()) {
            TypedScheduleGenome before=TypedScheduleGenome.fromVectors(catalog,GomRecords.vectors(e.point));
            e.genes=FactoryKeyReencoder.apply(catalog,before,new Random(viewSeed^(0x9e3779b97f4a7c15L*e.paidBy)));
            PermutationSolution<Integer> view=GomRecords.copy(e.point,e.genes);
            if(!physical(view,in.factories()).equals(e.physical))throw new AssertionError("External view changed physical chain");
            external.add(e);counts.put(e.source+"/unique/"+e.family,counts.getOrDefault(e.source+"/unique/"+e.family,0)+1);
        }
        for(String line:Files.readAllLines(directory.resolve("background.tsv"),StandardCharsets.UTF_8)) {
            String[] f=line.split("\t");background.add(new double[]{Double.parseDouble(f[0]),Double.parseDouble(f[1]),Double.parseDouble(f[2])});
        }
    }
    List<Entry> compatible(int family,String mode,int[] fixed,FirstStageCatalog catalog) {
        List<Entry> result=new ArrayList<>();
        for(Entry e:external)if(e.family==family&&(mode.equals("UNION")||mode.equals("G")&&e.source.contains("G")||mode.equals("S")&&e.source.contains("S"))) {
            if(family>=0){int[] a=e.genes.allocations();for(int j=0;j<a.length;j++)if(catalog.factory(a[j])!=fixed[j])throw new AssertionError("Fixed FA differs");}
            result.add(e);
        }
        return result;
    }
    static int[] ints(String s){String[] f=s.split(",");int[] a=new int[f.length];for(int i=0;i<a.length;i++)a[i]=Integer.parseInt(f[i]);return a;}
    static String physical(PermutationSolution<Integer> p,int factories) {
        FourVectors v=GomRecords.vectors(p);int[] js=v.jobs(),fa=v.factories(),ma=v.machines(),wa=v.workers();StringBuilder key=new StringBuilder();
        for(int f=0;f<factories;f++){key.append('|');for(int i=0;i<js.length;i++)if(fa[i]==f)key.append(js[i]).append(':').append(ma[i]).append(':').append(wa[i]).append(';');}
        return key.toString();
    }
}
