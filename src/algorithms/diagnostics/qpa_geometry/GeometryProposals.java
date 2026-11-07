package org.uma.jmetal.util.research.modelglobal;

import java.io.*;
import java.nio.ByteBuffer;
import java.security.*;
import java.util.*;

/** Unscored joint integer proposals, one call per logged case; no fitness values are calculated. */
final class GeometryProposals {
    private final GeometryWorld world;
    private final List<int[]> pairs;
    long constructions;
    GeometryProposals(GeometryWorld context,List<int[]> selected) {world=context;pairs=selected;}

    void write(String population,String variant,GeometryPopulation value,List<int[]> masks,long referenceSeed,BufferedWriter writer) throws Exception {
        Random reference=new Random(referenceSeed);
        for (int pair=0;pair<pairs.size();pair++) {
            int a=pairs.get(pair)[0],b=pairs.get(pair)[1];
            for (int index=0;index<masks.size();index++) {
                int[] mask=masks.get(index);int ref=mask[reference.nextInt(mask.length)];
                DirectJointMove position=DirectJointMove.apply(world.catalog,value.points.get(a).genome,value.points.get(b).genome,mask,ref,DirectJointMove.Kind.POSITION);constructions++;
                DirectJointMove order=DirectJointMove.apply(world.catalog,value.points.get(a).genome,value.points.get(b).genome,mask,-1,DirectJointMove.Kind.ORDER);constructions++;
                PaMixingMove pa=PaMixingMove.apply(world.catalog,value.reencoded.get(a),value.reencoded.get(b),mask);constructions++;
                if (position.emptyFactoryFallback!=order.emptyFactoryFallback||position.emptyFactoryFallback!=pa.fallback)
                    throw new AssertionError("Copied FMW fallback differs between equal masks/views");
                row(writer,population,variant,pair,index,"POSITION",ref,position.genome.toVectors(),position.emptyFactoryFallback);
                row(writer,population,variant,pair,index,"ORDER",-1,order.genome.toVectors(),order.emptyFactoryFallback);
                row(writer,population,variant,pair,index,"PA",-1,pa.genome.toVectors(),pa.fallback);
            }
        }
    }

    private void row(BufferedWriter writer,String population,String variant,int pair,int mask,String kind,int reference,FourVectors value,boolean fallback) throws Exception {
        writer.write(population+"\t"+variant+"\t"+pair+"\t"+mask+"\t"+kind+"\t"+reference+"\t"+hash(physical(value,world.in.factories()))+"\t"+fallback);writer.newLine();
    }

    static int[] physical(FourVectors vectors,int factories) {
        int[] js=vectors.jobs(),fa=vectors.factories(),ma=vectors.machines(),wa=vectors.workers();
        int[] result=new int[2+2*factories+3*js.length];int at=0;result[at++]=js.length;result[at++]=factories;
        for (int f=0;f<factories;f++) {
            int count=0;for (int ff:fa) if(ff==f)count++;
            result[at++]=f;result[at++]=count;
            for (int p=0;p<js.length;p++) if (fa[p]==f) {result[at++]=js[p];result[at++]=ma[p];result[at++]=wa[p];}
        }
        if (at!=result.length) throw new AssertionError("Physical key size mismatch");return result;
    }

    private static String hash(int[] integers) throws NoSuchAlgorithmException {
        ByteBuffer bytes=ByteBuffer.allocate(integers.length*4);for (int value:integers)bytes.putInt(value);
        StringBuilder hex=new StringBuilder();for (byte value:MessageDigest.getInstance("SHA-256").digest(bytes.array()))
            hex.append(Character.forDigit((value>>>4)&15,16)).append(Character.forDigit(value&15,16));return hex.toString();
    }
}
