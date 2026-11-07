package org.uma.jmetal.util.research.search;

import java.util.*;

/** Scheduling only: each physical role keeps one Q-table/state for exactly qIterations updates. */
public final class QgsEpochSchedule {
    static final class Agent {
        final QTable table;
        List<Particle> current;
        int observation=1;
        Agent(List<Particle> group,SearchConfig config) {
            current=group;table=new QTable(3,config.alpha,config.gamma);
        }
    }
    interface Step {void update(Agent agent,Direction role,int step);}
    private QgsEpochSchedule() { }
    static boolean fresh() {return Boolean.getBoolean("research.qgs.fresh");}
    static Map<Direction,List<Particle>> run(Map<Direction,List<Particle>> groups,Direction[] order,SearchConfig config,Step step) {
        return run(System.getProperty("research.qgs.layout","SERIAL"),groups,order,config,step);
    }
    static Map<Direction,List<Particle>> run(String layout,Map<Direction,List<Particle>> groups,Direction[] order,SearchConfig config,Step step) {
        Map<Direction,Agent> agents=new EnumMap<>(Direction.class);
        for(Direction d:order)agents.put(d,new Agent(groups.get(d),config));
        GlobalFlowTrace.epochStarted();
        if(layout.equals("SERIAL")) {
            for(Direction d:order)for(int i=0;i<config.qIterations;i++)step.update(agents.get(d),d,i);
        } else if(layout.equals("SWEEP")) {
            for(int i=0;i<config.qIterations;i++)for(Direction d:order)step.update(agents.get(d),d,i);
        } else throw new IllegalArgumentException("Unknown QGS layout "+layout);
        Map<Direction,List<Particle>> result=new EnumMap<>(Direction.class);
        for(Direction d:order)result.put(d,agents.get(d).current);
        return result;
    }
}
