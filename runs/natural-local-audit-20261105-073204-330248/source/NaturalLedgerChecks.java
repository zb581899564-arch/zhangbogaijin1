package org.uma.jmetal.util.research.search;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Natural slots have no forced replay quota; partial global/inter/intra prefixes must still be recorded. */
public final class NaturalLedgerChecks {
    private NaturalLedgerChecks() { }
    public static void main(String[] args) throws Exception {
        Path out=Paths.get(args[0]);Files.createDirectories(out);System.setProperty("research.qgsAudit.mode","record");
        for(String phase:Arrays.asList("GLOBAL","INTER","INTRA")) {
            QgsLocalLedger.resetForProbe();QgsLocalLedger.allowDeadlinePrefix(()->false);QgsLocalLedger ledger=QgsLocalLedger.instance();
            if(!phase.equals("GLOBAL")) {
                QgsLocalLedger.Slot inter=ledger.inter(Direction.MAKESPAN.id());
                if(inter.fixed||inter.limit!=Integer.MAX_VALUE)throw new AssertionError("Natural inter received a fixed quota");
                inter.paid=phase.equals("INTRA")?2:1;ledger.end(inter);
                if(phase.equals("INTRA")) {
                    QgsLocalLedger.Slot intra=ledger.round(Direction.MAKESPAN.id(),0,0);
                    if(intra.fixed||intra.limit!=Integer.MAX_VALUE)throw new AssertionError("Natural intra received a fixed quota");
                    intra.paid=3;ledger.end(intra);
                }
            }
            Path folder=out.resolve(phase);Files.createDirectory(folder);QgsLocalLedger.finish(folder);
            List<String> rows=Files.readAllLines(folder.resolve("local-ledger.csv"),StandardCharsets.UTF_8);
            if(rows.size()!=(phase.equals("GLOBAL")?1:phase.equals("INTER")?2:3))throw new AssertionError("Wrong natural ledger prefix");
            for(String row:rows.subList(1,rows.size()))if(Integer.parseInt(row.split(",")[5])!=0)throw new AssertionError("Natural slot forced a restart");
        }
        Files.write(out.resolve("acceptance.json"),Collections.singletonList("{\"status\":\"PASS\",\"searchFE\":0,\"decodes\":0,\"naturalPrefixes\":[\"GLOBAL\",\"INTER\",\"INTRA\"]}"),
            StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
}
