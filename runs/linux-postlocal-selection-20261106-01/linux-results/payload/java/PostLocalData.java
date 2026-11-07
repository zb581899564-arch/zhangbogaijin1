package org.uma.jmetal.util.research.search;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.problem.Problem;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.Instance;
import org.uma.jmetal.util.research.modelglobal.FourVectors;

/** Strict already-paid interchange; importing never evaluates a schedule. */
final class PostLocalData {
    static final class Member {
        final String origin;
        final int index, family;
        final long sourcePaidBy;
        final Direction role;
        final Particle particle;
        Member(String source, int slot, long fee, Direction direction, int context, Particle value) {
            origin=source; index=slot; sourcePaidBy=fee; role=direction; family=context; particle=value;
        }
        Member with(Particle value) { return new Member(origin,index,sourcePaidBy,role,family,value); }
        Map<String,Object> record() {
            return GomRecords.row("origin",origin,"sourceIndex",index,"sourcePaidByFE",sourcePaidBy,
                "role",role.name(),"family",family,"raw",GomRecords.raw(particle.current));
        }
    }
    final List<Member> parents=new ArrayList<>(), children=new ArrayList<>();
    final List<double[]> background=new ArrayList<>();
    private final Map<Integer,int[]> familyAssignments=new HashMap<>();

    PostLocalData(Path directory, Problem<PermutationSolution<Integer>> raw, Instance instance) throws IOException {
        Map<Integer,Member> p=new TreeMap<>(), c=new TreeMap<>();
        for(String line:Files.readAllLines(directory.resolve("points.tsv"),StandardCharsets.UTF_8)) {
            String[] fields=line.split("\t",-1);
            if(fields.length!=10)throw new IllegalArgumentException("points.tsv requires exactly ten columns without header");
            Member member=read(fields,raw,instance);
            Map<Integer,Member> target=member.origin.equals("P")?p:c;
            if(target.put(member.index,member)!=null)throw new IllegalArgumentException("Duplicate source/index");
        }
        if(p.size()!=100||c.size()!=100)throw new IllegalArgumentException("Exactly P100+C100 are required");
        for(int index=0;index<100;index++) {
            Member a=p.get(index),b=c.get(index);
            if(a==null||b==null||a.role!=b.role||a.family!=b.family)throw new IllegalArgumentException("P/C index-role-family mismatch");
            if(index>0&&a.role.ordinal()<parents.get(index-1).role.ordinal())throw new IllegalArgumentException("P role order changed");
            parents.add(a);children.add(b);
        }
        validateQuotas(parents);
        for(String line:Files.readAllLines(directory.resolve("background.tsv"),StandardCharsets.UTF_8)) {
            String[] fields=line.split("\t",-1);
            if(fields.length!=3)throw new IllegalArgumentException("background.tsv requires three columns");
            background.add(objectives(String.join(",",fields)));
        }
        if(background.isEmpty())throw new IllegalArgumentException("A0 must be nonempty");
    }
    private Member read(String[] f,Problem<PermutationSolution<Integer>> raw,Instance in) {
        if(!f[0].equals("P")&&!f[0].equals("C"))throw new IllegalArgumentException("Unknown imported source");
        int index=Integer.parseInt(f[1]),family=Integer.parseInt(f[4]);long fee=Long.parseLong(f[2]);
        if(index<0||index>=100||fee<0||family< -1||family>3)throw new IllegalArgumentException("Invalid imported metadata");
        Direction role=Direction.valueOf(f[3]);double[] objective=objectives(f[5]);
        int[][] vectors={ints(f[6]),ints(f[7]),ints(f[8]),ints(f[9])};
        for(int[] v:vectors)if(v.length!=in.jobs())throw new IllegalArgumentException("Imported vector length differs");
        boolean[] seen=new boolean[in.jobs()];int[] fixed=new int[in.jobs()];
        PermutationSolution<Integer> point=raw.createSolution();
        @SuppressWarnings("unchecked") List<Integer> machines=(List<Integer>)point.getAttribute("machine");
        for(int i=0;i<in.jobs();i++) {
            int job=vectors[0][i];
            if(job<0||job>=in.jobs()||seen[job])throw new IllegalArgumentException("Invalid job permutation");
            seen[job]=true;fixed[job]=vectors[1][i];point.setVariableValue(i,job);
            point.setVariableValueid(i,vectors[1][i]);machines.set(i,vectors[2][i]);point.setVariableValueworker(i,vectors[3][i]);
        }
        for(int k=0;k<3;k++)point.setObjective(k,objective[k]);
        point.setAttribute("cooperation.family",family);
        if(family>=0) {
            int[] previous=familyAssignments.putIfAbsent(family,fixed.clone());
            if(previous!=null&&!Arrays.equals(previous,fixed))throw new IllegalArgumentException("Fixed family FA differs");
            point.setAttribute("cooperation.fixedFactoryByJob",fixed);
        }
        if(SchedulingEncoding.repair(point,in)!=0)throw new AssertionError("Imported schedule needed repair");
        return new Member(f[0],index,fee,role,family,new Particle(point));
    }
    private static void validateQuotas(List<Member> points) {
        int[] families=new int[5];Set<Direction> roles=EnumSet.noneOf(Direction.class);
        for(Member point:points){families[point.family+1]++;roles.add(point.role);}
        if(!Arrays.equals(families,new int[]{80,5,5,5,5})||roles.size()!=4)throw new IllegalArgumentException("Expected free80 and four fixed5 families across four roles");
    }
    private static int[] ints(String text) {
        String[] values=text.split(",",-1);int[] result=new int[values.length];
        for(int i=0;i<result.length;i++)result[i]=Integer.parseInt(values[i]);return result;
    }
    private static double[] objectives(String text) {
        String[] values=text.split(",",-1);if(values.length!=3)throw new IllegalArgumentException("Three objectives required");
        double[] result=new double[3];
        for(int i=0;i<3;i++){result[i]=Double.parseDouble(values[i]);if(!Double.isFinite(result[i]))throw new IllegalArgumentException("Nonfinite objective");}
        return result;
    }
    static List<Map<String,Object>> records(List<Member> points) {
        List<Map<String,Object>> result=new ArrayList<>();
        for(int i=0;i<points.size();i++){Map<String,Object> row=points.get(i).record();row.put("slot",i);result.add(row);}return result;
    }
    static String physical(PermutationSolution<Integer> point,int factories) {
        FourVectors v=GomRecords.vectors(point);int[] js=v.jobs(),fa=v.factories(),ma=v.machines(),wa=v.workers();
        StringBuilder key=new StringBuilder();
        for(int f=0;f<factories;f++){key.append('|');for(int i=0;i<js.length;i++)if(fa[i]==f)key.append(js[i]).append(':').append(ma[i]).append(':').append(wa[i]).append(';');}
        return key.toString();
    }
}
