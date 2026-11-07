package research.dynamic;

import java.io.InputStream;
import java.security.MessageDigest;
import java.util.*;

/** Resolve requested local classes without initializing search state or evaluating a solution. */
public final class ClassResolutionProbe {
    private ClassResolutionProbe() { }
    public static Map<String,Object> capture(String... names) throws Exception {
        Map<String,Object> out=new LinkedHashMap<>();out.put("javaVersion",System.getProperty("java.version"));
        for(String name:names) {
            Class<?> type=Class.forName(name,false,ClassResolutionProbe.class.getClassLoader());
            String path="/"+name.replace('.','/')+".class";
            java.net.URL resource=type.getResource(path);
            if(resource==null)throw new IllegalStateException("Missing class resource: "+name);
            MessageDigest digest=MessageDigest.getInstance("SHA-256");
            try(InputStream stream=resource.openStream()) {
                byte[] buffer=new byte[8192];int count;
                while((count=stream.read(buffer))!=-1)digest.update(buffer,0,count);
            }
            StringBuilder hex=new StringBuilder();for(byte b:digest.digest())hex.append(String.format("%02x",b&255));
            Map<String,Object> item=new LinkedHashMap<>();item.put("resource",resource.toString());
            item.put("codeSource",type.getProtectionDomain().getCodeSource().getLocation().toString());
            item.put("sha256",hex.toString());out.put(name,item);
        }
        return out;
    }
    public static void main(String[] args) throws Exception {System.out.println(DynamicJson.encode(capture(args)));}
}
