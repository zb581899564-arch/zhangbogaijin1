package org.uma.jmetal.util.research.search;

import java.lang.ref.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Read-only paid identities, including core-created copies. Retains hashes, never schedule graphs. */
final class GomPaidRegistry {
    private final ReferenceQueue<PermutationSolution<Integer>> queue = new ReferenceQueue<>();
    private final Map<Key,Long> values = new HashMap<>();
    private final Map<String,Long> contents = new HashMap<>();
    long recoveredCopies;
    private static final class Key extends WeakReference<PermutationSolution<Integer>> {
        final int hash;
        Key(PermutationSolution<Integer> p, ReferenceQueue<PermutationSolution<Integer>> q) { super(p,q); hash = System.identityHashCode(p); }
        public int hashCode() { return hash; }
        public boolean equals(Object other) { return this == other || other instanceof Key && get() != null && get() == ((Key)other).get(); }
    }
    void put(PermutationSolution<Integer> p, long fe, String hash) {
        Reference<?> dead; while ((dead = queue.poll()) != null) values.remove(dead);
        values.put(new Key(p,queue), fe);
        contents.putIfAbsent(hash,fe);
    }
    long fee(PermutationSolution<Integer> p) {
        Long value = values.get(new Key(p,null));
        if (value == null) {
            value = contents.get(GomRecords.rawHash(p));
            if (value == null) throw new AssertionError("Working source has no exactly matching paid content");
            values.put(new Key(p,queue),value); recoveredCopies++;
        }
        return value;
    }
}
