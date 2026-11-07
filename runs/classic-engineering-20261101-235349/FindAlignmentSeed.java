package org.uma.jmetal.util.research.classic;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.joint.JointCheckProblem;
import org.uma.jmetal.util.research.runtime.SeededRandom;
public final class FindAlignmentSeed {
 public static void main(String[] args) {
  SeededRandom.reset(1); JointCheckProblem fixture=new JointCheckProblem(6);
  PermutationSolution<Integer> a=fixture.createSolution(), b=fixture.createSolution();
  for(int p=0;p<6;p++){set(a,p,p,fixture);set(b,p,5-p,fixture);}
  for(int seed=1;seed<1000;seed++){
   SeededRandom.reset(seed); PermutationSolution<Integer> c=new ClassicVariation(fixture.instance,new ClassicConfig("NSGA2_4V",1),()->{}).child(a,b);
   SchedulingEncoding.repair(c,fixture.instance); boolean equal=true, mixed=!c.getVariables().equals(a.getVariables())&&!c.getVariables().equals(b.getVariables());
   for(int p=0;p<6;p++){int j=c.getVariableValue(p),f=j%3; equal &=c.getVariableValueid(p)==f&&SchedulingEncoding.machineIntegers(c)[p]==j/3%fixture.instance.machines(f,0)&&c.getVariableValueworker(p)==j/3%fixture.instance.workers(f,0);}
   if(equal&&mixed){System.out.println("seed="+seed+" JS="+c.getVariables());return;}
  }
 }
 @SuppressWarnings("unchecked") static void set(PermutationSolution<Integer> s,int p,int j,JointCheckProblem f){int fac=j%3;s.setVariableValue(p,j);s.setVariableValueid(p,fac);((List<Integer>)s.getAttribute("machine")).set(p,j/3%f.instance.machines(fac,0));s.setVariableValueworker(p,j/3%f.instance.workers(fac,0));}
}
