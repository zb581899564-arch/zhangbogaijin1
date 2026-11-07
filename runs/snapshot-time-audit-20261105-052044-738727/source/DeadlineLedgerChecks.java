package org.uma.jmetal.util.research.search;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Zero-evaluation fixtures for deadlines in global, inter and intra phases; strict mode remains strict. */
public final class DeadlineLedgerChecks {
    private DeadlineLedgerChecks() { }
    public static void main(String[] args) throws Exception {
        Path out=Paths.get(args[0]);Files.createDirectories(out);
        Path expected=out.resolve("expected.csv");
        Files.write(expected,Arrays.asList("visit,group,round,factory,paid,restarts","1,1,-1,-1,2,0","1,1,0,0,3,0"),StandardCharsets.UTF_8);
        System.setProperty("research.qgsAudit.mode","replay");System.setProperty("research.qgsAudit.ledger",expected.toString());
        for(String phase:Arrays.asList("GLOBAL","INTER","INTRA","STRICT")) {
            QgsLocalLedger.resetForProbe();final boolean[] deadline={false};QgsLocalLedger.allowDeadlinePrefix(()->deadline[0]);
            QgsLocalLedger ledger=QgsLocalLedger.instance();boolean rejected=false;
            if(phase.equals("GLOBAL"))deadline[0]=true;
            else {
                QgsLocalLedger.Slot inter=ledger.inter(1);inter.paid=phase.equals("INTRA")?2:1;
                deadline[0]=!phase.equals("STRICT")&&!phase.equals("INTRA");
                try {ledger.end(inter);}catch(IllegalStateException error){rejected=true;}
                if(phase.equals("INTRA")) {
                    QgsLocalLedger.Slot intra=ledger.round(1,0,0);intra.paid=1;deadline[0]=true;ledger.end(intra);
                }
            }
            if(phase.equals("STRICT")) {if(!rejected)throw new AssertionError("Strict unspent quota not rejected");continue;}
            if(rejected)throw new AssertionError("Deadline prefix rejected");
            Path folder=out.resolve(phase);Files.createDirectory(folder);QgsLocalLedger.finish(folder);
            List<String> actual=Files.readAllLines(folder.resolve("local-ledger.csv"),StandardCharsets.UTF_8);
            int expectedSize=phase.equals("GLOBAL")?1:phase.equals("INTER")?2:3;
            if(actual.size()!=expectedSize)throw new AssertionError("Wrong deadline ledger prefix");
            if(phase.equals("INTER")&&!actual.get(1).equals("1,1,-1,-1,1,0"))throw new AssertionError("Inter paid count lost");
            if(phase.equals("INTRA")&&!actual.get(2).equals("1,1,0,0,1,0"))throw new AssertionError("Intra paid count lost");
        }
        Files.write(out.resolve("acceptance.json"),Collections.singletonList("{\"status\":\"PASS\",\"searchFE\":0,\"forcedPhases\":[\"GLOBAL\",\"INTER\",\"INTRA\"],\"strictQuotaRejection\":true}"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        System.out.println("DEADLINE_LEDGER_PASS");
    }
}
