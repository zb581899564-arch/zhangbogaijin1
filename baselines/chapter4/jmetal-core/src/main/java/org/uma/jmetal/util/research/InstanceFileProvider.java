package org.uma.jmetal.util.research;

/** Associates an encoded solution with the exact instance loaded by its problem. */
public interface InstanceFileProvider {
    String getInstanceFile();
    int getWorkerVectorLength();
}
