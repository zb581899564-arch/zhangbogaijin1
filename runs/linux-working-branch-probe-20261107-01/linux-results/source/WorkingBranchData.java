package research.dynamic;

import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.search.Direction;

/** Immutable paid seeds, donor snapshots, request archives and explicit proposal indices. */
final class WorkingBranchData {
    static final class Case {
        final String id,context; final Direction role; final int slot;
        Case(String[] f){id=f[0];context=f[1];role=Direction.valueOf(f[2]);slot=Integer.parseInt(f[3]);}
    }
    static final class Move {
        final int branch,step,node,donor; final int[] mask;
        Move(String[] f){branch=Integer.parseInt(f[1]);step=Integer.parseInt(f[2]);node=Integer.parseInt(f[3]);
            donor=Integer.parseInt(f[4]);mask=ints(f[5]);}
    }
    final FirstStageCatalog catalog;
    final List<Case> cases=new ArrayList<>();
    final Map<String,CounterfactualInputs.Entry> seeds=new LinkedHashMap<>();
    final Map<String,Map<Integer,TypedScheduleGenome>> donors=new LinkedHashMap<>();
    final Map<String,List<double[]>> archives=new LinkedHashMap<>();
    final Map<String,Map<Integer,List<Move>>> plans=new LinkedHashMap<>();

    WorkingBranchData(Path folder,FirstStageCatalog c)throws Exception {
        catalog=c;
        for(String line:lines(folder.resolve("seeds.tsv"))) {
            CounterfactualInputs.Entry e=new CounterfactualInputs.Entry(line,c);
            if(seeds.put(e.id,e)!=null || e.expected.length!=3)throw new AssertionError("Seed identity");
        }
        for(String line:lines(folder.resolve("cases.tsv")))cases.add(new Case(line.split("\t")));
        for(String line:lines(folder.resolve("donors.tsv"))) {
            String[] f=line.split("\t");donors.computeIfAbsent(f[0],k->new LinkedHashMap<>())
                .put(Integer.parseInt(f[1]),TypedScheduleGenome.of(c,ints(f[2]),doubles(f[3])));
        }
        for(String line:lines(folder.resolve("archives.tsv"))) {
            String[] f=line.split("\t");archives.computeIfAbsent(f[0],k->new ArrayList<>()).add(doubles(f[1]));
        }
        for(String line:lines(folder.resolve("schedule.tsv"))) {
            String[] f=line.split("\t");Move m=new Move(f);
            plans.computeIfAbsent(f[0],k->new LinkedHashMap<>()).computeIfAbsent(m.branch,k->new ArrayList<>()).add(m);
        }
        validate();
    }
    private void validate() {
        if(cases.size()!=12 || seeds.size()!=36 || donors.size()!=3)throw new AssertionError("Frozen input counts");
        for(Case c:cases) {
            if(donors.get(c.context).size()!=80)throw new AssertionError("free80 required");
            for(String label:new String[]{"P","Q","R"})seed(c,label);
            for(int branch=0;branch<2;branch++) {
                List<Move> list=plans.get(c.id).get(branch);int size=branch==0?31:15;
                if(list.size()!=size)throw new AssertionError("Frozen prefix length");
                Set<Integer> nodes=new HashSet<>();
                for(int i=0;i<size;i++) {
                    Move m=list.get(i);
                    if(m.step!=i || m.donor==c.slot || !donors.get(c.context).containsKey(m.donor)
                        || !nodes.add(m.node) || m.mask.length<1 || m.mask.length>catalog.jobs())throw new AssertionError("Invalid plan");
                }
            }
        }
    }
    CounterfactualInputs.Entry seed(Case c,String label) {
        CounterfactualInputs.Entry e=seeds.get(c.id+"-"+label);if(e==null)throw new AssertionError("Missing seed");return e;
    }
    TypedScheduleGenome genome(CounterfactualInputs.Entry e){return TypedScheduleGenome.of(catalog,e.resources,e.keys);}
    PaInternalArchive archive(Case c) {
        PaInternalArchive a=new PaInternalArchive();for(double[] p:archives.get(c.context))a.offer(p);return a;
    }
    CounterfactualInputs.Entry entry(String id,TypedScheduleGenome genes) {
        return entry(id,genes,new double[0]);
    }
    CounterfactualInputs.Entry entry(String id,TypedScheduleGenome genes,double[] expected) {
        FourVectors v=genes.toVectors();String line=id+"\t1\t"+csv(genes.allocations())+"\t"+csv(genes.priorities())+
            "\t"+csv(v.jobs())+"\t"+csv(v.factories())+"\t"+csv(v.machines())+"\t"+csv(v.workers())+"\t"+csv(expected);
        return new CounterfactualInputs.Entry(line,catalog);
    }
    private static List<String> lines(Path path)throws Exception{return Files.readAllLines(path,StandardCharsets.UTF_8);}
    private static int[] ints(String s){return Arrays.stream(s.split(",")).mapToInt(Integer::parseInt).toArray();}
    private static double[] doubles(String s){return Arrays.stream(s.split(",")).mapToDouble(Double::parseDouble).toArray();}
    private static String csv(int[] a){StringJoiner j=new StringJoiner(",");for(int v:a)j.add(Integer.toString(v));return j.toString();}
    private static String csv(double[] a){StringJoiner j=new StringJoiner(",");for(double v:a)j.add(Double.toString(v));return j.toString();}
}
