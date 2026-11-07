package org.uma.jmetal.util.research.classic;

/** Registered discrete adaptations; settings differ only in mutation intensity. */
public final class ClassicConfig implements java.io.Serializable {
    private static final long serialVersionUID = 1L;
    public static final int POPULATION = 100;
    public final String mode;
    public final int settingIndex;
    public final double crossoverProbability = .9;
    public final double mutationScale;
    public final int neighborhoodSize = 20, replacementLimit = 2;
    public final double neighborhoodProbability = .9;
    public final int localInterval = 50, localProposalCap = 30;

    public ClassicConfig(String mode, int settingIndex) {
        if (!isMode(mode)) throw new IllegalArgumentException("Unknown classic mode: " + mode);
        if (settingIndex < 0 || settingIndex > 2) throw new IllegalArgumentException("Classic setting must be 0, 1 or 2");
        this.mode = mode; this.settingIndex = settingIndex;
        mutationScale = settingIndex == 0 ? 1 : settingIndex == 1 ? .5 : 2;
    }

    public static boolean isMode(String mode) {
        return "NSGA2_4V".equals(mode) || "SPEA2_4V".equals(mode)
                || "MOEAD_4V".equals(mode) || "NSGA2_VNS_4V".equals(mode);
    }

    public String describe() {
        return "mode=" + mode + ";setting=" + settingIndex + ";population=100;SPEA2Archive=100"
                + ";PC=" + crossoverProbability + ";mutationScale=" + mutationScale
                + ";variation=OX_JS+job-aligned-uniform_FA_MA_WA"
                + ";mutation=per-JS-position-swap-and-per-job-per-resource-resample,p=min(1,scale/jobs)"
                + ";repair=shared-deterministic;all-proposals=guarded-paid"
                + ";SPEA2Distance=frozen-mean-normalized-objective-Euclidean;k=floor(sqrt(union-size)),self-excluded"
                + ";MOEAD=normalized-Tchebycheff;weights=100-deterministic-maximin-H30-simplex"
                + ";neighbors=20;delta=.9;maxReplacement=2;zeroWeight=1e-6"
                + ";SPEA2-and-MOEAD-scale=initial-100-absolute-mean-frozen,zero-to-1;ideal=own-paid-minimum"
                + ";VNS=chapter4-ordinary-inter+intra,CENTER,support-null,every-50-global-offspring"
                + ";localProposalCap=30-intra-only;inter=additional-paid-proposals"
                + ";selectionTie=stable-index;NSGATournamentTie=seeded-random;NSGACrowding=retain-union-front,constant-objective-interior-zero"
                + ";sources=10.1109/4235.996017,TIK103,10.1109/TEVC.2007.892759"
                + ";status=explicit-discrete-adaptation,not-author-score-reproduction";
    }
}
