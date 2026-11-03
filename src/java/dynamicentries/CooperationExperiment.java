package research.dynamic;

/** Exact opt-in experiment names; experiment factors cannot silently combine. */
final class CooperationExperiment {
    final String ordinaryMode, renewal, transfer;
    private CooperationExperiment(String ordinaryMode, String renewal, String transfer) {
        this.ordinaryMode = ordinaryMode; this.renewal = renewal; this.transfer = transfer;
    }
    static CooperationExperiment parse(String mode) {
        for (String renewal : new String[] {"ELITE", "RANDOM"}) {
            String suffix = "_CONTEXT_" + renewal;
            if (!mode.endsWith(suffix)) continue;
            String base = mode.substring(0, mode.length() - suffix.length());
            if (!base.equals("SHARE_JOB_ALIGNED") && !base.equals("SYNC_JOB_ALIGNED"))
                throw new IllegalArgumentException("Context renewal requires SYNC/SHARE JOB_ALIGNED");
            return new CooperationExperiment(base, renewal, "NONE");
        }
        for (String transfer : new String[] {"PACKET_ROLE", "MOSAIC_ROLE", "PACKET_RANDOM", "MOSAIC_RANDOM"}) {
            String suffix = "_" + transfer;
            if (!mode.endsWith(suffix)) continue;
            String base = mode.substring(0, mode.length() - suffix.length());
            if (!base.equals("SHARE_JOB_ALIGNED")) throw new IllegalArgumentException("Factory transfer requires SHARE_JOB_ALIGNED");
            return new CooperationExperiment(base, "NONE", transfer);
        }
        return new CooperationExperiment(mode, "NONE", "NONE");
    }
}
