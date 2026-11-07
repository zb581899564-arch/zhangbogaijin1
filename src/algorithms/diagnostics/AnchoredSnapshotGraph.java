package org.uma.jmetal.util.research.runtime;

import java.io.*;
import java.util.*;
import org.uma.jmetal.solution.Solution;
import org.uma.jmetal.util.research.SchedulingMetadata;
import org.uma.jmetal.util.research.model.*;

/** Isolated serializer: only audited, exact final immutable classes may retain their identity. */
final class AnchoredSnapshotGraph {
    private static final Set<Class<?>> IMMUTABLE = Collections.unmodifiableSet(new HashSet<Class<?>>(
            Arrays.<Class<?>>asList(Instance.class, DynamicParameters.class, DynamicSchedule.class,
                    DynamicStep.class, SchedulingMetadata.class)));
    private AnchoredSnapshotGraph() { }

    static Set<Class<?>> immutableTypes() { return IMMUTABLE; }

    @SuppressWarnings("unchecked")
    static <S extends Solution<?>> S copy(S solution) {
        List<Object> anchors = new ArrayList<>();
        try {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            try (Writing output = new Writing(bytes, anchors)) { output.writeObject(solution); }
            SnapshotCopyMetrics.serialized(bytes.size(), anchors.size());
            try (Reading input = new Reading(new ByteArrayInputStream(bytes.toByteArray()), anchors)) {
                return (S) input.readObject();
            }
        } catch (IOException | ClassNotFoundException error) {
            throw new IllegalStateException("An independent archive requires a serializable solution graph", error);
        }
    }

    private static final class Handle implements Serializable {
        private static final long serialVersionUID = 1L;
        private final int index;
        Handle(int index) { this.index = index; }
    }

    private static final class Writing extends ObjectOutputStream {
        private final List<Object> anchors;
        private final IdentityHashMap<Object, Handle> references = new IdentityHashMap<>();
        Writing(OutputStream output, List<Object> anchors) throws IOException {
            super(output); this.anchors = anchors; enableReplaceObject(true);
        }
        @Override protected Object replaceObject(Object value) {
            if (value == null || !IMMUTABLE.contains(value.getClass())) return value;
            Handle handle = references.get(value);
            if (handle == null) {
                handle = new Handle(anchors.size()); anchors.add(value); references.put(value, handle);
            }
            return handle;
        }
    }

    private static final class Reading extends ObjectInputStream {
        private final List<Object> anchors;
        Reading(InputStream input, List<Object> anchors) throws IOException {
            super(input); this.anchors = anchors; enableResolveObject(true);
        }
        @Override protected Object resolveObject(Object value) throws IOException {
            if (value != null && value.getClass() == Handle.class) {
                int index = ((Handle) value).index;
                if (index < 0 || index >= anchors.size()) throw new InvalidObjectException("Invalid snapshot anchor");
                return anchors.get(index);
            }
            return value;
        }
    }
}
