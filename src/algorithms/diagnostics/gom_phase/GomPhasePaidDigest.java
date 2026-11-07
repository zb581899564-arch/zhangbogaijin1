package org.uma.jmetal.util.research.search;

import java.security.*;
import org.uma.jmetal.solution.PermutationSolution;

/** Independent cloneable diagnostic digest, later checked against the unchanged common digest. */
final class GomPhasePaidDigest {
    private final MessageDigest digest;
    GomPhasePaidDigest() {
        try { digest=MessageDigest.getInstance("SHA-256"); }
        catch(NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
    void update(PermutationSolution<Integer> point,long fe) { digest.update(GomRecords.paidBytes(point,fe)); }
    String snapshot() {
        try {
            StringBuilder value=new StringBuilder(64);
            for(byte b:((MessageDigest)digest.clone()).digest())value.append(Character.forDigit((b>>>4)&15,16)).append(Character.forDigit(b&15,16));
            return value.toString();
        } catch(CloneNotSupportedException error) { throw new IllegalStateException(error); }
    }
}
