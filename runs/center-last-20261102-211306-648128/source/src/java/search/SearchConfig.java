package org.uma.jmetal.util.research.search;

/** Frozen paper settings plus explicit reconstruction choices; zero/NaN selects the chapter default. */
public final class SearchConfig implements java.io.Serializable {
    private static final long serialVersionUID = 1L;
    public int populationSize = 100;
    public int boundarySize = 15;
    public int qIterations;
    public int localProposalCap;
    public double alpha = 1.0;
    public double gamma = 0.8;
    public double exploration = Double.NaN;
    public double randScale = Double.NaN;
    public double factoryCrossover = 0.2;
    public double machineCrossover = Double.NaN;
    public double workerCrossover = 0.3;
    public double factoryMutation = Double.NaN;
    public double machineMutation = Double.NaN;
    public double workerMutation = 0.25;
    /** Explicit chapter4 semantic variants; defaults preserve the archived v2 path. */
    public boolean mergeGlobalLocal;
    public boolean paperResourceOperators;

    public SearchConfig resolved(int chapter) {
        if (chapter != 3 && chapter != 4) throw new IllegalArgumentException("Chapter must be 3 or 4");
        SearchConfig result = new SearchConfig();
        result.populationSize = populationSize; result.boundarySize = boundarySize;
        result.qIterations = qIterations == 0 ? (chapter == 3 ? 40 : 50) : qIterations;
        result.localProposalCap = localProposalCap == 0 ? (chapter == 3 ? 40 : 30) : localProposalCap;
        result.alpha = alpha; result.gamma = gamma;
        result.exploration = defaultValue(exploration, chapter == 3 ? 0.9 : 0.8);
        result.randScale = defaultValue(randScale, chapter == 3 ? 0.4 : 0.6);
        result.factoryCrossover = factoryCrossover;
        result.machineCrossover = defaultValue(machineCrossover, chapter == 3 ? 0.4 : 0.3);
        result.workerCrossover = workerCrossover;
        result.factoryMutation = defaultValue(factoryMutation, chapter == 3 ? 0.06 : 0.08);
        result.machineMutation = defaultValue(machineMutation, chapter == 3 ? 0.1 : 0.15);
        result.workerMutation = workerMutation;
        result.mergeGlobalLocal = mergeGlobalLocal;
        result.paperResourceOperators = paperResourceOperators;
        if (chapter != 4 && (mergeGlobalLocal || paperResourceOperators))
            throw new IllegalArgumentException("S/O semantic variants apply only to chapter4");
        result.validate();
        return result;
    }

    private void validate() {
        if (populationSize < 4 || boundarySize < 1 || 3L * boundarySize >= populationSize
                || qIterations < 1 || localProposalCap < 1) {
            throw new IllegalArgumentException("Positive group, Q and local-search sizes are required");
        }
        for (double value : new double[] {alpha, gamma, exploration, randScale, factoryCrossover,
                machineCrossover, workerCrossover, factoryMutation, machineMutation, workerMutation}) {
            if (!Double.isFinite(value) || value < 0 || value > 1) {
                throw new IllegalArgumentException("Search probabilities/learning parameters must lie in [0,1]");
            }
        }
        if (alpha == 0) throw new IllegalArgumentException("Learning rate must be positive");
    }

    private static double defaultValue(double value, double fallback) { return Double.isNaN(value) ? fallback : value; }
    public String describe(int chapter) { return resolved(chapter).describe(); }
    public String describe() {
        return "population=" + populationSize + ";boundaryEach=" + boundarySize
                + ";central=" + (populationSize - 3 * boundarySize) + ";Q=" + qIterations
                + ";localProposalCap=" + localProposalCap + ";alpha=" + alpha + ";gamma=" + gamma
                + ";exploration=" + exploration + ";randScale=" + randScale
                + ";PC_FA_MA_WA=" + factoryCrossover + "," + machineCrossover + "," + workerCrossover
                + ";PM_FA_MA_WA=" + factoryMutation + "," + machineMutation + "," + workerMutation
                + ";paperProfile=JMS-Table9_or_ESWA-DOE-paragraph;alpha-and-local-cap=EXPLICIT-RECONSTRUCTION"
                + (mergeGlobalLocal || paperResourceOperators ? ";semanticS=" + mergeGlobalLocal + ";semanticO=" + paperResourceOperators : "");
    }
    @Override public String toString() { return describe(); }
}
