package org.uma.jmetal.util.research.runtime;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import org.uma.jmetal.solution.Solution;

/** Copies the entire serializable solution graph, including auxiliary vectors and attributes. */
final class SolutionSnapshots {
    private SolutionSnapshots() { }

    @SuppressWarnings("unchecked")
    static <S extends Solution<?>> S copy(S solution) {
        try {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            try (ObjectOutputStream output = new ObjectOutputStream(bytes)) {
                output.writeObject(solution);
            }
            try (ObjectInputStream input = new ObjectInputStream(
                    new ByteArrayInputStream(bytes.toByteArray()))) {
                return (S) input.readObject();
            }
        } catch (IOException | ClassNotFoundException exception) {
            throw new IllegalStateException("An independent archive requires a serializable solution graph",
                    exception);
        }
    }
}
