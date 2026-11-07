package org.uma.jmetal.util.research.modelglobal;

import java.util.*;
import org.uma.jmetal.util.research.search.Direction;
import static org.uma.jmetal.util.research.modelglobal.PaDonorChannelLog.*;

/** Diagnostic direct-channel ablation. Working acceptance and model samples stay original. */
final class PaDonorRollback {
    enum Mode { LIVE, REVERT_BRIDGE, REVERT_COMMON }
    private final Mode mode = Mode.valueOf(System.getProperty("research.pa.donorMode","LIVE"));
    private final List<PaIndividual> previous = new ArrayList<>();
    private final List<String> latest = new ArrayList<>();
    private final PaPaidEvaluation evaluation;
    private final PaDonorChannelLog log = new PaDonorChannelLog();
    private final Map<String,Long> counts = new LinkedHashMap<>();
    private PaIndividual pendingLive, pendingPrevious, pendingChosen;
    private String pendingCategory;
    private int pendingSlot, pendingDonorSlot;
    private boolean pendingRevert;

    PaDonorRollback(PaPaidEvaluation value) { evaluation = value; }
    private void count(String key) { counts.put(key,counts.getOrDefault(key,0L)+1); }
    void initial(PaIndividual point, PaInternalArchive.Flags flags) {
        int slot = previous.size(); previous.add(point); latest.add("INITIAL");
        if (log.enabled()) {
            Map<String,Object> record = row("kind","initial","slot",slot,"state",state(point,true));
            flags(record,flags); log.emit(record);
        }
    }
    void reencoded(int generation, int slot, PaIndividual before, PaIndividual after) {
        PaIndividual oldPrevious = previous.get(slot), alias;
        if (oldPrevious == before) alias = after;
        else {
            long seed = evaluation.channelSeed() ^ (0x6a09e667f3bcc909L + 0x9e3779b97f4a7c15L*generation + 0x632be59bd9b4e019L*slot);
            alias = evaluation.reencode(oldPrevious,new Random(seed)); count("channel.shadowNeutralAliases");
        }
        previous.set(slot,alias);
        if (log.enabled()) log.emit(row("kind","reencode","generation",generation,"slot",slot,
            "beforeId",before.id,"after",state(after,true),"beforePreviousId",oldPrevious.id,"previous",state(alias,true)));
    }
    PaIndividual donor(int slot, int donorSlot, PaIndividual parent, PaIndividual live) {
        if (slot == donorSlot) throw new IllegalStateException("Self donor");
        String category = latest.get(donorSlot);
        boolean cross = live.role != parent.role && live.role != Direction.CENTER;
        if (cross && !category.equals("INITIAL")) count("channel.eligible."+category);
        boolean revert = cross && ((mode == Mode.REVERT_BRIDGE && category.equals("BRIDGE"))
            || (mode == Mode.REVERT_COMMON && category.equals("COMMON")));
        PaIndividual chosen = revert ? previous.get(donorSlot) : live;
        if (chosen.role != live.role) throw new IllegalStateException("Role changed by donor view");
        count("channel.reads"); if (revert) count("channel.reverted."+category);
        pendingLive=live; pendingPrevious=previous.get(donorSlot); pendingChosen=chosen;
        pendingSlot=slot; pendingDonorSlot=donorSlot; pendingCategory=category; pendingRevert=revert;
        return chosen;
    }
    void evaluated(int generation, int slot, int step, int subsetIndex, int[] subset,
            PaIndividual parent, PaIndividual donor, PaIndividual child, boolean fallback,
            PaInternalArchive.Flags flags, boolean accepted) {
        if (slot != pendingSlot || donor != pendingChosen) throw new IllegalStateException("Channel evidence mismatch");
        boolean center = PaInternalArchive.weaklyDominates(child.objectives(),parent.objectives()) || !flags.dominated;
        if (log.enabled()) {
            Map<String,Object> record = row("kind","paid","generation",generation,"slot",slot,"step",step,
                "subsetIndex",subsetIndex,"subset",subset,"donorSlot",pendingDonorSlot,"parentId",parent.id,
                "liveId",pendingLive.id,"previousId",pendingPrevious.id,"donorId",donor.id,
                "category",pendingCategory,"mode",mode.name(),"reverted",pendingRevert,
                "fallback",fallback,"accepted",accepted,"state",state(child,false));
            flags(record,flags); log.emit(record);
        }
        if (accepted) {
            String category = parent.role != Direction.CENTER && !center ? "BRIDGE" : "COMMON";
            previous.set(slot,parent); latest.set(slot,category); count("channel.accepted."+category);
        }
    }
    Map<String,Object> finish() {
        log.close(); Map<String,Object> result = new LinkedHashMap<>();
        result.putAll(counts); result.put("channel.mode",mode.name());
        result.put("channel.workingAcceptanceUnchanged",true); return result;
    }
}
