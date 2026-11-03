package research.dynamic;

import java.lang.reflect.Array;
import java.util.Iterator;
import java.util.Map;

/** Small dependency-free JSON output for the bounded diagnostic records. */
public final class DynamicJson {
    private DynamicJson() { }
    public static String encode(Object value) {
        if (value == null) return "null";
        if (value instanceof Number) {
            if (!Double.isFinite(((Number) value).doubleValue())) throw new IllegalArgumentException("Non-finite JSON number");
            return value.toString();
        }
        if (value instanceof Boolean) return value.toString();
        if (value instanceof Map) {
            StringBuilder s = new StringBuilder("{");
            for (Object raw : ((Map<?, ?>) value).entrySet()) {
                Map.Entry<?, ?> e = (Map.Entry<?, ?>) raw;
                if (s.length() > 1) s.append(',');
                s.append(encode(e.getKey().toString())).append(':').append(encode(e.getValue()));
            }
            return s.append('}').toString();
        }
        if (value instanceof Iterable) {
            StringBuilder s = new StringBuilder("[");
            for (Object x : (Iterable<?>) value) { if (s.length() > 1) s.append(','); s.append(encode(x)); }
            return s.append(']').toString();
        }
        if (value.getClass().isArray()) {
            StringBuilder s = new StringBuilder("[");
            for (int i = 0; i < Array.getLength(value); i++) { if (i > 0) s.append(','); s.append(encode(Array.get(value, i))); }
            return s.append(']').toString();
        }
        StringBuilder s = new StringBuilder("\"");
        for (char c : value.toString().toCharArray()) {
            if (c == '\\' || c == '"') s.append('\\').append(c);
            else if (c < 32) s.append(String.format("\\u%04x", (int) c));
            else s.append(c);
        }
        return s.append('"').toString();
    }
}
