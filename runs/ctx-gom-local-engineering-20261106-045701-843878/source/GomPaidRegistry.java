package org.uma.jmetal.util.research.search;

import java.lang.ref.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Read-only point identity bookkeeping without retaining500k schedule graphs or modifying attributes. */
final class GomPaidRegistry {
    private final ReferenceQueue<PermutationSolution<Integer>> queue = new ReferenceQueue<>();
    private final Map<Key,Long> values = new HashMap<>();
    private static final class Key extends WeakReference<PermutationSolution<Integer>> {
        final int hash;
        Key(PermutationSolution<Integer> p, ReferenceQueue<PermutationSolution<Integer>> q) { super(p,q); hash = System.identityHashCode(p); }
        public int hashCode() { return hash; }
        public boolean equals(Object other) { return this == other || other instanceof Key && get() != null && get() == ((Key)other).get(); }
    }
    void put(PermutationSolution<Integer> p, long fe) {
        Reference<?> dead; while ((dead = queue.poll()) != null) values.remove(dead);
        values.put(new Key(p,queue), fe);
    }
    long fee(PermutationSolution<Integer> p) {
        Long value = values.get(new Key(p,null));
        if (value == null) throw new AssertionError("Working source was not observed as paid"); return value;
    }
}
