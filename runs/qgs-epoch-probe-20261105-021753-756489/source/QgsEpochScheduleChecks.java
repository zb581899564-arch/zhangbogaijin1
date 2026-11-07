package org.uma.jmetal.util.research.search;

import java.util.*;

/** Verify Q-state lifetime and visit order with no scheduling-model evaluations. */
public final class QgsEpochScheduleChecks {
    private QgsEpochScheduleChecks() { }
    public static void main(String[] args) {
        Map<Direction,List<Particle>> groups=new EnumMap<>(Direction.class);
        for(Direction d:Direction.values())groups.put(d,Collections.emptyList());
        SearchConfig config=new SearchConfig();config.qIterations=50;
        Map<String,List<String>> visits=new LinkedHashMap<>();Map<String,Map<Direction,double[][]>> tables=new LinkedHashMap<>();
        for(String layout:new String[]{"SERIAL","SWEEP"}) {
            Map<Direction,Integer> count=new EnumMap<>(Direction.class);Map<Direction,QgsEpochSchedule.Agent> identities=new EnumMap<>(Direction.class);
            List<String> sequence=new ArrayList<>();
            QgsEpochSchedule.run(layout,groups,Direction.values(),config,(agent,role,step)->{
                if(step!=count.getOrDefault(role,0))throw new AssertionError("Role update counter reset or skipped");
                if(identities.containsKey(role)&&identities.get(role)!=agent)throw new AssertionError("Q agent reset within epoch");
                identities.put(role,agent);agent.table.update(agent.observation,step%3,role.id()+step/100.,step%2);
                agent.observation=step%2;count.put(role,step+1);sequence.add(role+":"+step);
            });
            Map<Direction,double[][]> values=new EnumMap<>(Direction.class);
            for(Direction d:Direction.values()) {
                if(count.get(d)!=50)throw new AssertionError("Wrong number of role updates");values.put(d,identities.get(d).table.snapshot());
            }
            if(new HashSet<>(identities.values()).size()!=4)throw new AssertionError("Q agents shared across roles");
            visits.put(layout,sequence);tables.put(layout,values);
        }
        for(Direction d:Direction.values())if(!Arrays.deepEquals(tables.get("SERIAL").get(d),tables.get("SWEEP").get(d)))throw new AssertionError("Per-role Q learning changed");
        if(!visits.get("SERIAL").get(1).equals("MAKESPAN:1")||!visits.get("SWEEP").get(1).equals("CENTER:0"))throw new AssertionError("Incorrect visit order");
        System.out.println("QGS_EPOCH_SCHEDULE_CHECKS_PASS 4 persistent agents x50 steps, zero decoder calls");
    }
}
