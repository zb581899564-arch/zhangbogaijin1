package org.uma.jmetal.util.research.search;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.solution.PermutationSolution;
import research.dynamic.DynamicJson;

/** A lossless native event sink with explicit pass labels and neutral-view checks. */
final class PostLocalEvidence implements GomRunScope.Evidence, AutoCloseable {
    private final BufferedWriter writer;
    private final int factories;
    private long sequence, validatedViews;
    String phase="PREPARE";
    PostLocalEvidence(Path directory,int factoryCount)throws IOException {
        factories=factoryCount;
        writer=Files.newBufferedWriter(directory.resolve("events.jsonl"),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
    public void record(Map<String,Object> event) {
        Map<String,Object> row=new LinkedHashMap<>(event);row.put("phase",phase);row.put("sequence",++sequence);
        if("paid".equals(row.get("kind")))row.put("acceptanceArchive",Boolean.getBoolean("research.postlocal.nativeObserver")?"NATIVE_PUBLIC":"PRIVATE_PASS");
        try{writer.write(DynamicJson.encode(row));writer.newLine();}catch(IOException error){throw new UncheckedIOException(error);}
    }
    public void view(PermutationSolution<Integer> before,PermutationSolution<Integer> after) {
        if(!PostLocalData.physical(before,factories).equals(PostLocalData.physical(after,factories)))throw new AssertionError("Neutral GOM view changed a physical factory chain");
        if(!Arrays.equals(before.getObjectives(),after.getObjectives()))throw new AssertionError("Neutral view changed objectives");
        validatedViews++;
    }
    Map<String,Object> receipt(){return GomRecords.row("events",sequence,"validatedViews",validatedViews);}
    public void close()throws IOException{writer.close();}
    static void write(Path path,Object value)throws IOException {
        Files.write(path,DynamicJson.encode(value).getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);
    }
}
