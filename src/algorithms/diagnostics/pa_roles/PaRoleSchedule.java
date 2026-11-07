package org.uma.jmetal.util.research.modelglobal;

import java.util.*;
import java.util.function.Consumer;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.search.Direction;
import org.uma.jmetal.util.research.search.ParetoTools;

/** Role labels and receiver traversal are separate factors; population storage never moves. */
public final class PaRoleSchedule {
    public static final class Plan {
        public final Direction[] roles;
        public final int[] visit;
        Plan(Direction[] targets,int[] order) { roles=targets;visit=order; }
    }
    private static final String MODE=System.getProperty("research.paRole.mode","NATIVE");
    private static final Random PRIVATE=new Random(Long.getLong("research.paRole.seed",15530003L));
    private static Consumer<Map<String,Object>> observer=unused -> { };
    private static int generation;
    private static int[] traversal;
    private PaRoleSchedule() { }

    public static void observe(Consumer<Map<String,Object>> listener) { observer=Objects.requireNonNull(listener); }

    public static Plan make(List<PaIndividual> population,String mode,Random noise) {
        if(population.size()!=100)throw new IllegalArgumentException("100 members required");
        Direction[] roles=new Direction[100];int[] visit=new int[100];
        for(int i=0;i<100;i++){roles[i]=population.get(i).role;visit[i]=i;}
        if(mode.equals("NATIVE"))return new Plan(roles,visit);
        if(!Arrays.asList("TASK_ONLY","ORDER_ONLY","FULL","RANDOM","CENTER_MATCHED").contains(mode))
            throw new IllegalArgumentException("Unknown role mode: "+mode);
        List<Integer> grouped;
        if(mode.equals("RANDOM")) {
            grouped=new ArrayList<>();for(int i=0;i<100;i++)grouped.add(i);Collections.shuffle(grouped,noise);
        } else grouped=ranked(population);
        for(int at=0;at<100;at++) {
            int slot=grouped.get(at);
            if(!mode.equals("ORDER_ONLY"))roles[slot]=mode.equals("CENTER_MATCHED")?Direction.CENTER:at<15?Direction.MAKESPAN:at<70?Direction.CENTER:at<85?Direction.ENERGY:Direction.WORKER_COST;
            if(!mode.equals("TASK_ONLY"))visit[at]=slot;
        }
        return new Plan(roles,visit);
    }

    private static List<Integer> ranked(List<PaIndividual> population) {
        Map<Direction,List<Integer>> groups=new EnumMap<>(Direction.class);List<Integer> remaining=new ArrayList<>();
        for(int i=0;i<100;i++)remaining.add(i);
        for(Direction d:Arrays.asList(Direction.MAKESPAN,Direction.ENERGY,Direction.WORKER_COST,Direction.CENTER)) {
            List<PermutationSolution<Integer>> points=new ArrayList<>();for(int i:remaining)points.add(population.get(i).point);
            List<Integer> selected=new ArrayList<>();int count=d==Direction.CENTER?remaining.size():15;
            List<Integer> order=ParetoTools.order(points,d);for(int at=0;at<count;at++)selected.add(remaining.get(order.get(at)));
            groups.put(d,selected);remaining.removeAll(selected);
        }
        List<Integer> result=new ArrayList<>();for(Direction d:Direction.values())result.addAll(groups.get(d));return result;
    }

    public static void before(int number,List<PaIndividual> population) {
        if(number!=generation+1)throw new AssertionError("Role generation out of sequence");
        List<Map<String,Object>> before=records(population);Plan plan=make(population,MODE,PRIVATE);
        for(int i=0;i<100;i++) {
            PaIndividual old=population.get(i);
            if(old.role==plan.roles[i])continue;
            PaIndividual next=new PaIndividual(old.id,old.paidFE,plan.roles[i],old.genome,old.point);
            if(old.genome!=next.genome||old.point!=next.point||!Arrays.equals(old.objectives(),next.objectives())||!Objects.equals(old.hash,next.hash))
                throw new AssertionError("Role metadata changed physical state");
            population.set(i,next);
        }
        generation=number;traversal=plan.visit;
        Map<String,Object> event=new LinkedHashMap<>();event.put("generation",number);event.put("mode",MODE);
        event.put("before",before);event.put("after",records(population));event.put("visit",traversal);observer.accept(event);
    }

    public static int[] order(int number) {
        if(number!=generation||traversal==null)throw new AssertionError("Missing role plan");return traversal.clone();
    }

    private static List<Map<String,Object>> records(List<PaIndividual> population) {
        List<Map<String,Object>> result=new ArrayList<>();
        for(PaIndividual p:population) {
            Map<String,Object> row=new LinkedHashMap<>();row.put("id",p.id);row.put("paidFE",p.paidFE);row.put("role",p.role.name());
            row.put("hash",p.hash);row.put("objectives",p.objectives());
            if(Boolean.parseBoolean(System.getProperty("research.paRole.fullTrace","true"))) {row.put("resources",p.genome.allocations());row.put("keys",p.genome.priorities());}
            result.add(row);
        }
        return result;
    }
}
