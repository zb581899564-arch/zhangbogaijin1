package research.dynamic;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.uma.jmetal.util.research.model.DynamicParameters;
import org.uma.jmetal.util.research.model.Instance;

/** Only beta changes; h0, accumulation, recovery, factory policy and physical instance remain explicit. */
public final class FactorBeta0Parameters {
    private FactorBeta0Parameters() { }
    static DynamicParameters make(Instance in, DynamicParameters original) {
        double[][][][] values = new double[4][in.factories()][in.stages()][];
        for (int f = 0; f < in.factories(); f++) for (int k = 0; k < in.stages(); k++) {
            for (int v = 0; v < 4; v++) values[v][f][k] = new double[in.workers(f, k)];
            for (int w = 0; w < in.workers(f, k); w++) {
                values[0][f][k][w] = original.alpha(f, k, w);
                values[1][f][k][w] = original.mu(f, k, w);
                values[2][f][k][w] = 0.;values[3][f][k][w] = original.h0(f, k, w);
            }
        }
        return new DynamicParameters(values[0], values[1], values[2], values[3], original.source() + "; paired schedule-factor beta0");
    }
    static Map<String,Object> contract(Instance in, DynamicParameters original, DynamicParameters zero) {
        List<Map<String,Object>> fields = new ArrayList<>();
        for (int f = 0; f < in.factories(); f++) for (int k = 0; k < in.stages(); k++) for (int w = 0; w < in.workers(f, k); w++) {
            if (original.alpha(f,k,w) != zero.alpha(f,k,w) || original.mu(f,k,w) != zero.mu(f,k,w)
                    || original.h0(f,k,w) != zero.h0(f,k,w) || zero.beta(f,k,w) != 0.) throw new AssertionError("beta0 changed unrelated parameters");
            fields.add(NeutralProbeSupport.row("factory",f,"stage",k,"worker",w,"alpha",zero.alpha(f,k,w),
                "mu",zero.mu(f,k,w),"h0",zero.h0(f,k,w),"originalBeta",original.beta(f,k,w),"counterfactualBeta",zero.beta(f,k,w)));
        }
        return NeutralProbeSupport.row("status","PASS","originalSource",original.source(),"counterfactualSource",zero.source(),
            "onlyBetaChanged",true,"workers",fields,"policy","Same dynamic append/FAM decoder; not static insertion policy");
    }
}
