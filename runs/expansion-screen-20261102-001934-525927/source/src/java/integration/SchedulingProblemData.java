package org.uma.jmetal.util.research;

import org.uma.jmetal.util.research.model.Instance;

/** Shared immutable problem data used by initialization, repair and decoding. */
public interface SchedulingProblemData extends InstanceFileProvider {
    Instance getSchedulingInstance();
}
