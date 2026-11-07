package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.modelglobal.NeutralInitialView;

/** Frozen light entry plus a read-only post-initialization paid trace digest. */
public final class QpaInitialViewRun {
    private QpaInitialViewRun() { }
    public static void main(String[] args) throws Exception {
        PddrPaidDigest suffix=new PddrPaidDigest();long[] count={0};Throwable failure=null;
        NeutralInitialView.observer((point,fe)->{if(fe>100){suffix.update(fe,point);count[0]++;}});
        try {QpaCapabilityRun.main(args);}catch(Exception|Error error){failure=error;throw error;}
        finally {
            Map<String,Object> row=new LinkedHashMap<>();row.put("intervention",NeutralInitialView.diagnostics());
            row.put("suffixPaidRows",count[0]);row.put("suffixPaidSHA256",suffix.finish());row.put("error",failure==null?null:failure.toString());
            row.put("identity",ClassResolutionProbe.capture("research.dynamic.QpaInitialViewRun",
                "org.uma.jmetal.util.research.modelglobal.NeutralInitialView","org.uma.jmetal.util.research.modelglobal.QpaPaidEvaluation",
                "org.uma.jmetal.util.research.modelglobal.PaPaidEvaluation","org.uma.jmetal.util.research.modelglobal.FactoryKeyReencoder"));
            Files.write(Paths.get(args[3]).resolve("initial-view-identity.json"),DynamicJson.encode(row).getBytes(java.nio.charset.StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
        }
    }
}
