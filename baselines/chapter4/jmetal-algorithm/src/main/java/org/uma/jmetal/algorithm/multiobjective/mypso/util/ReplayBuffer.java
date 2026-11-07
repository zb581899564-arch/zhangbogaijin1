package org.uma.jmetal.algorithm.multiobjective.mypso.util;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public class ReplayBuffer {
    public List<Experience> buffer;
    private int maxSize;

    public ReplayBuffer(int maxSize) {
        this.buffer = new ArrayList<>();
        this.maxSize = maxSize;
    }

    public void add(Experience experience) {
        if (buffer.size() >= maxSize) {
            buffer.remove(0);
        }
        buffer.add(experience);
    }

    public List<Experience> sample(int batchSize) {
        Random random = org.uma.jmetal.util.research.runtime.SeededRandom.current();
        List<Experience> batch = new ArrayList<>(batchSize);
        for (int i = 0; i < batchSize; i++) {
            int index = random.nextInt(buffer.size());
            batch.add(buffer.get(index));
        }
        return batch;
    }
}