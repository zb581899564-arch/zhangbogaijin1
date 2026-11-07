package org.uma.jmetal.util.research.search;

import java.io.InputStream;
import java.security.MessageDigest;
import java.util.*;

/** Read the bytes of the actual JVM-resolved classes after the search has stopped. */
public final class RuntimeClassIdentity {
    private RuntimeClassIdentity() { }
    public static Map<String,Object> capture() throws Exception {
        String[] names={"org.uma.jmetal.util.research.search.CanonicalHmopso",
            "org.uma.jmetal.util.research.search.GlobalGroupPolicy","org.uma.jmetal.util.research.search.SearchState",
            "org.uma.jmetal.util.research.search.LocalSearch","org.uma.jmetal.util.research.search.LocalPddrKernel",
            "org.uma.jmetal.util.research.search.Particle","org.uma.jmetal.util.research.cooperation.CooperationSupport",
            "org.uma.jmetal.util.research.runtime.RunContext","org.uma.jmetal.util.research.runtime.BudgetedProblem",
            "research.dynamic.PddrIsolationRun"};
        Map<String,Object> result=new LinkedHashMap<>();
        result.put("javaVersion",System.getProperty("java.version"));
        for(String name:names) {
            Class<?> type=Class.forName(name);String resource="/"+name.replace('.','/')+".class";
            MessageDigest digest=MessageDigest.getInstance("SHA-256");
            try(InputStream in=type.getResourceAsStream(resource)) {
                if(in==null)throw new IllegalStateException("Missing loaded class resource "+name);
                byte[] buffer=new byte[8192];int n;
                while((n=in.read(buffer))!=-1)digest.update(buffer,0,n);
            }
            StringBuilder hex=new StringBuilder();for(byte b:digest.digest())hex.append(String.format("%02x",b&255));
            Map<String,Object> row=new LinkedHashMap<>();row.put("resource",type.getResource(resource).toString());
            row.put("codeSource",type.getProtectionDomain().getCodeSource().getLocation().toString());row.put("sha256",hex.toString());
            result.put(name,row);
        }
        return result;
    }
}
