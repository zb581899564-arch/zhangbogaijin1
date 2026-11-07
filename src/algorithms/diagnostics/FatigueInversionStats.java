package org.uma.jmetal.util.research.model;

import java.util.*;

/** Offline local derivatives and explicitly labelled single-transition counterfactuals. */
public final class FatigueInversionStats {
    private static final double MARGIN=1e-8;
    private FatigueInversionStats() { }

    public static Map<String,Object> analyze(Instance in,DynamicParameters p,DynamicSchedule schedule) {
        List<Map<String,Object>> events=new ArrayList<>();double[] completion=new double[in.jobs()];
        DynamicStageState state=null;int f=-1,k=-1;long previews=0,negativeFirst=0,negativeLater=0,negativeTerminal=0,legalWitnesses=0;
        double maxLambda=0,maxFirst=0,maxTerminal=0;
        for(DynamicStep step:schedule.steps()) {
            if(step.factory()!=f || step.stage()!=k) {
                if(step.factory()!=f)Arrays.fill(completion,0);
                f=step.factory();k=step.stage();state=new DynamicStageState(in,p,f,k);
            }
            double ready=completion[step.job()];
            DynamicStep replay=state.preview(in,p,step.job(),step.machine(),step.worker(),ready);previews++;
            sameStep(step,replay);
            int w=step.worker();double mu=p.mu(f,k,w),lambda=step.base()*p.beta(f,k,w)*mu*step.u();
            boolean terminal=Double.compare(step.completion(),schedule.objectives()[0])==0;
            maxLambda=Math.max(maxLambda,lambda);if(k==0)maxFirst=Math.max(maxFirst,lambda);
            if(terminal)maxTerminal=Math.max(maxTerminal,lambda);
            if(lambda>1+MARGIN) {
                if(k==0)negativeFirst++;else negativeLater++;if(terminal)negativeTerminal++;
                double delta=Math.log(lambda)/(2*mu);
                DynamicStep delayed=DynamicPhysics.transition(in,p,step.job(),f,k,step.machine(),w,step.start()+delta,
                        state.machineEnd[step.machine()],state.machineUsed[step.machine()],state.workerEnd[w],state.workerFatigue[w]);previews++;
                double decrease=step.completion()-delayed.completion();
                if(decrease < -64*Math.ulp(step.completion()))throw new AssertionError("Negative derivative contradicts local physics");
                List<Map<String,Object>> compatible=new ArrayList<>();
                if(k==0)for(int m=0;m<in.machines(f,k);m++) {
                    if(m==step.machine() || !sameMachine(in,f,k,m,step.machine()))continue;
                    if(Math.max(ready,Math.max(state.machineEnd[m],state.workerEnd[w]))<=step.start())continue;
                    DynamicStep alternative=state.preview(in,p,step.job(),m,w,ready);previews++;
                    double gain=step.completion()-alternative.completion();
                    boolean material=gain>=.001*step.duration();if(material)legalWitnesses++;
                    compatible.add(row("machine",m,"start",alternative.start(),"completion",alternative.completion(),
                            "completionDecrease",gain,"materialLocalDecrease",material,
                            "energyChange",alternative.energy()-step.energy(),"laborChange",alternative.labor()-step.labor()));
                }
                events.add(row("job",step.job(),"factory",f,"stage",k,"machine",step.machine(),"worker",w,
                        "start",step.start(),"completion",step.completion(),"base",step.base(),"duration",step.duration(),
                        "startFatigue",step.u(),"beta",p.beta(f,k,w),"mu",mu,"lambda",lambda,"startDerivative",1-lambda,
                        "makespanTerminal",terminal,"hypotheticalHalfOptimalWait",delta,"hypotheticalCompletionDecrease",decrease,
                        "compatibleLaterMachinePreviews",compatible));
            }
            state.accept(step);completion[step.job()]=step.completion();
        }
        return row("operations",schedule.steps().size(),"negativeFirstStage",negativeFirst,"negativeLaterStage",negativeLater,
                "negativeMakespanTerminal",negativeTerminal,"maxLambda",maxLambda,"maxFirstStageLambda",maxFirst,
                "maxTerminalLambda",maxTerminal,"materialCompatibleMachineWitnesses",legalWitnesses,
                "offlineTransitionPreviews",previews,"events",events);
    }

    public static void analyticChecks() {
        for(double[] fixture:new double[][]{{4,1,.5,1},{4,1,.1,.5},{4,0,.5,1},{4,1,0,1}}) {
            double b=fixture[0],beta=fixture[1],mu=fixture[2],u=fixture[3],h=1e-6;
            double plus=h+b*(1+beta*u*Math.exp(-mu*h));
            double minus=-h+b*(1+beta*u*Math.exp(mu*h));
            if(Math.abs((plus-minus)/(2*h)-(1-b*beta*mu*u))>1e-7)throw new AssertionError("Derivative fixture failed");
        }
    }
    private static boolean sameMachine(Instance in,int f,int k,int a,int b) {
        return in.speed(f,k,a)==in.speed(f,k,b)&&in.power(f,k,a)==in.power(f,k,b)&&in.standby(f,k,a)==in.standby(f,k,b);
    }
    private static void sameStep(DynamicStep a,DynamicStep b) {
        if(a.job()!=b.job()||a.factory()!=b.factory()||a.stage()!=b.stage()||a.machine()!=b.machine()||a.worker()!=b.worker()
                ||!Arrays.equals(values(a),values(b)))throw new AssertionError("Replay transition differs");
    }
    private static double[] values(DynamicStep s) {
        return new double[]{s.start(),s.base(),s.duration(),s.setupDuration(),s.completion(),s.u(),s.v(),s.energy(),s.labor(),s.exposure()};
    }
    private static Map<String,Object> row(Object...fields) {
        Map<String,Object> out=new LinkedHashMap<>();for(int i=0;i<fields.length;i+=2)out.put((String)fields[i],fields[i+1]);return out;
    }
}
