package org.uma.jmetal.util.research.cooperation;

import java.io.*;
import java.nio.*;
import java.security.*;
import java.util.*;
import org.uma.jmetal.util.research.model.*;
import research.dynamic.DynamicJson;

/** Offline records retain operation summation order, rather than rounded factory totals. */
final class FactoryValueRecords {
    final Map<String,FactoryRecord[]> points = new LinkedHashMap<>();
    final IdentityHashMap<FactoryRecord,String> ids = new IdentityHashMap<>();
    private final Map<String,String> physicalTimelines = new HashMap<>();
    long repeatedChains;

    void add(String id, DynamicSchedule schedule, BufferedWriter output, int factories) throws Exception {
        FactoryRecord[] parts = new FactoryRecord[factories];
        for (int f=0; f<factories; f++) {
            FactoryRecord record = new FactoryRecord(schedule,f); parts[f]=record;
            String rid=id+"#"+f; ids.put(record,rid);
            List<Double> energy=new ArrayList<>(),labor=new ArrayList<>();
            MessageDigest digest=MessageDigest.getInstance("SHA-256"); ByteBuffer bytes=ByteBuffer.allocate(120);
            for (DynamicStep op:schedule.steps()) if (op.factory()==f) {
                energy.add(op.energy()); labor.add(op.labor()); bytes.clear();
                bytes.putInt(op.job()).putInt(op.factory()).putInt(op.stage()).putInt(op.machine()).putInt(op.worker());
                for (double v:new double[]{op.start(),op.base(),op.duration(),op.setupDuration(),op.completion(),
                        op.u(),op.v(),op.energy(),op.labor(),op.exposure()}) bytes.putLong(Double.doubleToLongBits(v));
                digest.update(bytes.array(),0,bytes.position());
            }
            StringBuilder hex=new StringBuilder(); for (byte b:digest.digest()) hex.append(String.format("%02x",b&255));
            String physical=f+":"+Arrays.toString(record.jobs)+Arrays.toString(record.machines)+Arrays.toString(record.workers);
            String previous=physicalTimelines.putIfAbsent(physical,hex.toString());
            if (previous!=null) { repeatedChains++; if (!previous.equals(hex.toString())) throw new AssertionError("Factory context timeline differs"); }
            Map<String,Object> row=new LinkedHashMap<>(); row.put("id",rid); row.put("factory",f);
            row.put("jobs",record.jobs); row.put("machines",record.machines); row.put("workers",record.workers);
            row.put("objectives",record.objectives); row.put("energy",energy); row.put("labor",labor); row.put("timelineSHA256",hex.toString());
            output.write(DynamicJson.encode(row)); output.newLine();
        }
        points.put(id,parts);
    }

    String key(String schema, String point, int factory, int jobs) {
        FactoryRecord[] parts=points.get(point); int[] assignment=new int[jobs];
        for (int f=0; f<parts.length; f++) for (int job:parts[f].jobs) assignment[job]=f;
        int[] set=parts[factory].jobs.clone(); Arrays.sort(set);
        return factory+":"+Arrays.toString(schema.equals("JOBSET")?set:assignment);
    }

    String physical(String point) {
        StringBuilder value=new StringBuilder();
        for (FactoryRecord r:points.get(point)) value.append(Arrays.toString(r.jobs)).append(Arrays.toString(r.machines)).append(Arrays.toString(r.workers));
        return value.toString();
    }
}
