package org.uma.jmetal.util.research.runtime;

import java.io.Serializable;
import java.lang.reflect.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.model.*;

/** Mutability, graph-alias and immutable-type fixtures for the isolated serialization experiment. */
final class SnapshotContractData {
    private SnapshotContractData() { }
    static final class Payload implements Serializable {
        private static final long serialVersionUID = 1L;
        int[] array = {3, 5, 7};
        List<Object> list = new ArrayList<>();
        Payload cycle;
        Object root;
        Payload(Object root) { this.root=root; cycle=this; list.add(array); list.add(this); }
    }

    static List<String> auditImmutableClasses() {
        List<String> audited = new ArrayList<>();
        for (Class<?> type : AnchoredSnapshotGraph.immutableTypes()) {
            if (!Modifier.isFinal(type.getModifiers())) throw new AssertionError("Mutable subclass risk: "+type);
            for (Field f : type.getDeclaredFields()) if (!Modifier.isStatic(f.getModifiers())
                    && (!Modifier.isFinal(f.getModifiers()) || !Modifier.isPrivate(f.getModifiers())))
                throw new AssertionError("Exposed or nonfinal field: "+f);
            for (Method m : type.getDeclaredMethods()) if (Arrays.asList(
                    "readObject","readResolve","writeObject","writeReplace").contains(m.getName()))
                throw new AssertionError("Custom serialization requires a separate audit: "+m);
            audited.add(type.getName());
        }
        Collections.sort(audited); return audited;
    }

    static void installGraph(PermutationSolution<Integer> s, DynamicPrefix prefix) {
        Payload value = new Payload(s); s.setAttribute("snapshot.payload", value);
        s.setAttribute("snapshot.alias", value.array); s.setAttribute("snapshot.mapCycle", s.getAttributes());
        s.setAttribute("snapshot.mutablePrefix", prefix);
    }

    static void independent(PermutationSolution<Integer> source, PermutationSolution<Integer> copy) {
        if (source==copy || source.getAttributes()==copy.getAttributes()
                || source.getObjectives()==copy.getObjectives() || source.getVariables()==copy.getVariables()
                || source.getVariablesid()==copy.getVariablesid() || source.getVariablesworker()==copy.getVariablesworker()
                || source.getAttribute("machine")==copy.getAttribute("machine"))
            throw new AssertionError("Mutable solution storage was shared");
        Payload old=(Payload)source.getAttribute("snapshot.payload"), value=(Payload)copy.getAttribute("snapshot.payload");
        if (old==value || old.array==value.array || old.list==value.list || value.cycle!=value
                || value.root!=copy || value.list.get(0)!=value.array || value.list.get(1)!=value
                || copy.getAttribute("snapshot.alias")!=value.array
                || copy.getAttribute("snapshot.mapCycle")!=copy.getAttributes())
            throw new AssertionError("Mutable alias or cycle contract was lost");
        if (copy.getAttribute("worker")!=copy.getVariablesworker()
                || copy.getAttribute("machine")!=copy.getVariablesmachine())
            throw new AssertionError("Auxiliary vector alias differs");
        if (source.getAttribute("snapshot.mutablePrefix")==copy.getAttribute("snapshot.mutablePrefix"))
            throw new AssertionError("Mutable prefix shared");
    }

    static String key(PermutationSolution<Integer> s) {
        return s.getVariables()+"|"+s.getVariablesid()+"|"+s.getAttribute("machine")+"|"
                +s.getVariablesworker()+"|"+Arrays.toString(s.getObjectives());
    }

    @SuppressWarnings("unchecked")
    static void mutate(PermutationSolution<Integer> s) {
        s.getVariables().set(0, -1); s.getVariablesid().set(0, -1);
        ((List<Integer>)s.getAttribute("machine")).set(0, -1); s.getVariablesworker().set(0, -1);
        s.getObjectives()[0]=-1; ((Payload)s.getAttribute("snapshot.payload")).array[0]=-99;
        ((Payload)s.getAttribute("snapshot.payload")).list.clear(); s.setAttribute("snapshot.new",new int[]{9});
    }
}
