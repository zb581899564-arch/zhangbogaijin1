package org.uma.jmetal.util.research.joint;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Optional bounded immutable diagnostics. No diagnostic objective is ever fed back to the policy. */
final class JointTrace {
    private JointTrace() { }
    static Map<String, Object> begin(BlockContext block, JointPolicy.Mode mode, long version, boolean learned) {
        Map<String, Object> result = new LinkedHashMap<>(); List<Object> parent = new ArrayList<>();
        for (int job : block.parentSequence) parent.add(action(block.assignments[job]));
        result.put("parent", Collections.unmodifiableList(parent)); result.put("blockBegin", block.begin);
        result.put("blockLength", block.length); result.put("mode", mode.name()); result.put("modelVersion", version);
        result.put("learned", learned); result.put("decisions", new ArrayList<Map<String, Object>>()); return result;
    }
    @SuppressWarnings("unchecked")
    static void decision(Map<String, Object> trace, List<JointPolicy.Choice> choices, int chosen) {
        Map<String, Object> step = new LinkedHashMap<>(); List<Map<String, Object>> candidates = new ArrayList<>();
        for (JointPolicy.Choice choice : choices) {
            Map<String, Object> value = new LinkedHashMap<>(); List<Object> witness = new ArrayList<>();
            for (JointAction a : choice.witness) witness.add(action(a));
            value.put("action", action(choice.action)); value.put("witness", Collections.unmodifiableList(witness));
            value.put("exactDelta", choice.delta); value.put("predictedFuture", choice.future); value.put("score", choice.score);
            value.put("afterPartial", numbers(choice.state.partial)); value.put("afterFeatures", numbers(choice.state.features));
            value.put("tailEstimate", numbers(choice.state.tail)); candidates.add(Collections.unmodifiableMap(value));
        }
        step.put("candidates", Collections.unmodifiableList(candidates)); step.put("chosen", chosen);
        ((List<Map<String, Object>>) trace.get("decisions")).add(Collections.unmodifiableMap(step));
    }
    @SuppressWarnings("unchecked")
    static Map<String, Object> finish(Map<String, Object> trace, double[] objectives) {
        trace.put("objectives", numbers(objectives));
        trace.put("decisions", Collections.unmodifiableList(new ArrayList<>((List<Map<String, Object>>) trace.get("decisions"))));
        return Collections.unmodifiableMap(trace);
    }
    static List<Integer> action(JointAction a) {
        List<Integer> result = new ArrayList<>();
        for (int value : a.tuple()) result.add(value); return Collections.unmodifiableList(result);
    }
    static List<Double> numbers(double[] values) {
        List<Double> result = new ArrayList<>();
        for (double value : values) result.add(value); return Collections.unmodifiableList(result);
    }
}
