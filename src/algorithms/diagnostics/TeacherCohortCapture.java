package org.uma.jmetal.util.research.search;

import java.util.*;
import java.util.function.Supplier;
import org.uma.jmetal.solution.PermutationSolution;

/** First action2 batch at/after step24, eight free parents per role, with exact paid background. */
public final class TeacherCohortCapture {
    private static final boolean ENABLED=Boolean.getBoolean("research.teacherCohort.capture");
    private static final int STEP_FLOOR=Integer.getInteger("research.teacherCohort.stepFloor",24);
    private static Supplier<List<PermutationSolution<Integer>>> archive;
    private static final Map<Direction,Map<String,Object>> cohorts=new EnumMap<>(Direction.class);
    private static final IdentityHashMap<PermutationSolution<Integer>,Integer> positions=new IdentityHashMap<>();
    private static final IdentityHashMap<PermutationSolution<Integer>,List<Map<String,Object>>> histories=new IdentityHashMap<>();
    private static List<Map<String,Object>> active;
    private static int generation;
    private static long paid;
    private TeacherCohortCapture() { }
    public static void configure(Supplier<List<PermutationSolution<Integer>>> known) {archive=known;}
    public static void paid(long value) {paid=value;}
    static void generationStarted() {if(ENABLED)generation++;}
    static void begin(Direction role,int step,int action,List<Particle> group,List<PermutationSolution<Integer>> guides) {
        if(!ENABLED)return;active=null;positions.clear();histories.clear();
        if(generation!=1||step<STEP_FLOOR||action!=2||cohorts.containsKey(role))return;
        List<Particle> free=new ArrayList<>();for(Particle p:group)if(p.current.getAttribute("cooperation.family")==null)free.add(p);
        if(free.size()<8)throw new AssertionError("Too few free parents in frozen role");
        for(int i=0;i<8;i++) {
            Particle p=free.get(i*free.size()/8);positions.put(p.current,i);
            List<Map<String,Object>> history=new ArrayList<>();for(PermutationSolution<Integer>s:p.personalArchive())history.add(encoding(s));
            histories.put(p.current,history);
        }
        Map<String,Object> c=new LinkedHashMap<>();c.put("role",role.name());c.put("step",step);c.put("action",action);c.put("paidFE",paid);
        List<Map<String,Object>> library=new ArrayList<>();for(PermutationSolution<Integer>s:guides)library.add(encoding(s));c.put("guideLibrary",library);
        List<double[]> background=new ArrayList<>();for(PermutationSolution<Integer>s:archive.get())background.add(s.getObjectives().clone());
        c.put("background",background);active=new ArrayList<>();c.put("parents",active);cohorts.put(role,c);
        List<double[]> reference=new ArrayList<>();for(Particle p:group)reference.add(p.current.getObjectives().clone());c.put("groupReference",reference);
    }
    static void proposal(PermutationSolution<Integer> parent,PermutationSolution<Integer> personal,PermutationSolution<Integer> leader,boolean composed) {
        if(!ENABLED||active==null||!positions.containsKey(parent))return;
        if(composed)throw new AssertionError("Free parent unexpectedly composed");
        Map<String,Object> row=new LinkedHashMap<>();row.put("parentIndex",positions.get(parent));row.put("parent",encoding(parent));
        row.put("personal",encoding(personal));row.put("nativeLeader",encoding(leader));active.add(row);
        row.put("personalHistory",histories.get(parent));
    }
    private static Map<String,Object> encoding(PermutationSolution<Integer>s) {
        Map<String,Object> r=new LinkedHashMap<>();r.put("JS",new ArrayList<>(s.getVariables()));r.put("FA",new ArrayList<>(s.getVariablesid()));
        r.put("MA",new ArrayList<>((List<?>)s.getAttribute("machine")));r.put("WA",new ArrayList<>(s.getVariablesworker()));
        r.put("objectives",s.getObjectives().clone());return r;
    }
    public static Map<String,Object> finish() {
        Map<String,Object> out=new LinkedHashMap<>();out.put("enabled",ENABLED);out.put("rolesCaptured",cohorts.size());
        for(Map<String,Object> c:cohorts.values())if(((List<?>)c.get("parents")).size()!=8)throw new AssertionError("Incomplete cohort");
        out.put("cohorts",new ArrayList<>(cohorts.values()));return out;
    }
}
