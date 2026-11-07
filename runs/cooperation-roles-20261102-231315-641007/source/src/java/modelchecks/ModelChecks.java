package org.uma.jmetal.util.research.modelchecks;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;
import java.util.stream.Stream;
import org.uma.jmetal.util.research.model.*;

/** Executable checks with independent arithmetic anchors and complete resource timelines. */
public final class ModelChecks {
    private ModelChecks() { }
    public static void main(String[] args) throws Exception {
        handCalculation(); paperExamples(); rejects(); serialization();
        if (args.length == 2) {
            checkDirectory(Paths.get(args[0]), false);
            checkDirectory(Paths.get(args[1]), true);
        } else if (args.length != 0) throw new IllegalArgumentException("Expected zero arguments or chapter3-dir chapter4-dir");
        System.out.println("MODEL_CHECKS_PASS (reconstruction checks; no optimization-performance claim)");
    }
    private static void handCalculation() {
        double[][][] speed = {{{2,2}},{{1,1}}}, power = {{{5,5}},{{3,7}}}, standby = {{{1,1}},{{1,1}}};
        Instance in = new Instance("hand-calculation", ModelKind.CHAPTER4_DUAL_RESOURCE,
                new double[][]{{12},{6},{8}}, new double[][]{{2},{1},{2}}, speed, power, standby,
                new double[][][]{{{2}},{{1}}}, new double[][][]{{{20}},{{10}}}, "independent synthetic arithmetic oracle");
        Schedule schedule = Decoder.decode(in, new int[]{0,1,2}, new int[]{0,0,1}, new int[]{0,1,0}, new int[]{0,0,0});
        assertObjectives(schedule, new double[]{10,60,220}); Validator.validate(in, schedule);
        close(find(schedule,1,0).start(),4); // two machines share one worker: worker stays for the whole AT
        if (schedule.objectives().length != 3 || schedule.criticalFactory(0,true) != 1) fail("Typed objective metadata");
    }
    private static void paperExamples() {
        Instance c3 = PaperExamples.chapter3(1);
        int[] js3 = {2,1,0,3,4}, fa3 = {0,0,1,1,0}, ma3 = {0,1,0,0,0}, wa3 = {1,2,0,0,1,2};
        Schedule plain3 = Decoder.decode(c3,js3,fa3,ma3,wa3,false), shifted3 = Decoder.decode(c3,js3,fa3,ma3,wa3);
        close(find(plain3,2,0).duration(), 7/.8); // J3 factory1 M1 W2: 7/(1*.8)
        close(plain3.objectives()[0], 95.0/6.0); // factory1 last J5: 13.75+3/(1.2*1.2)
        Validator.validate(c3,plain3); Validator.validate(c3,shifted3); monotone(plain3,shifted3);
        if (!(shifted3.objectives()[1] < plain3.objectives()[1] && shifted3.objectives()[2] < plain3.objectives()[2])) fail("JMS shift must reduce idle energy/labor span");
        Instance c4 = PaperExamples.chapter4(1);
        int[] js4 = {5,9,4,3,6,1,7,2,0,8}, fa4 = {1,0,1,0,0,0,1,1,1,0};
        int[] ma4 = {1,1,1,0,0,2,0,0,1,1}, wa4 = {1,1,0,1,0,1,0,1,1,0};
        Schedule plain4 = Decoder.decode(c4,js4,fa4,ma4,wa4,false), shifted4 = Decoder.decode(c4,js4,fa4,ma4,wa4);
        close(find(plain4,5,0).duration(), 8/(1.1*1.2)+2/1.2);
        close(find(plain4,5,0).setupDuration(), 2/1.2);
        Validator.validate(c4,plain4); Validator.validate(c4,shifted4); monotone(plain4,shifted4);
        close(plain4.objectives()[2],shifted4.objectives()[2]); // active-work cost is invariant under a pure shift
        System.out.println("JMS paper vectors plain="+Arrays.toString(plain3.objectives())+" shifted="+Arrays.toString(shifted3.objectives()));
        System.out.println("ESWA paper vectors plain="+Arrays.toString(plain4.objectives())+" shifted="+Arrays.toString(shifted4.objectives()));
    }
    private static void rejects() throws Exception {
        try { Decoder.decode(PaperExamples.chapter4(1), new int[10],new int[10],new int[10],new int[20]); fail("Must reject invalid encoding"); }
        catch (IllegalArgumentException expected) { }
        try { InstanceLoader.loadChapter4(Paths.get("absent.txt"), null, 1); fail("Must reject absent SUT"); }
        catch (IllegalArgumentException expected) { }
        try { Decoder.decode(PaperExamples.chapter3(1),new int[]{2,1,0,3,4},new int[]{0,0,1,1,0},
                new int[]{0,1,0,1,0},new int[]{1,2,0,0,1,2}); fail("JMS Fig2 left raw MA is infeasible and must not be silently repaired"); }
        catch (IllegalArgumentException expected) { }
    }
    private static void serialization() throws Exception {
        Instance original = PaperExamples.chapter4(1);
        java.io.ByteArrayOutputStream buffer = new java.io.ByteArrayOutputStream();
        try(java.io.ObjectOutputStream out = new java.io.ObjectOutputStream(buffer)) { out.writeObject(original); }
        Instance restored;
        try(java.io.ObjectInputStream in = new java.io.ObjectInputStream(new java.io.ByteArrayInputStream(buffer.toByteArray()))) { restored=(Instance)in.readObject(); }
        close(original.duration(5,1,0,1,1),restored.duration(5,1,0,1,1));
    }
    private static void checkDirectory(Path directory, boolean chapter4) throws Exception {
        List<Path> files = new ArrayList<Path>();
        try (Stream<Path> stream = Files.list(directory)) { stream.filter(p -> p.toString().endsWith(".txt")).sorted().forEach(files::add); }
        for (Path file : files) {
            String[] dimensions = Files.readAllLines(file).get(0).trim().split("\\s+");
            SetupTimes sut = chapter4 ? SetupTimes.generatedSupplement(Integer.parseInt(dimensions[2]),Integer.parseInt(dimensions[1]),314159) : null;
            Instance in = chapter4 ? InstanceLoader.loadChapter4(file,sut,1) : InstanceLoader.loadChapter3(file,1);
            if (!in.satisfiesDualResourceCondition()) System.out.println("PAPER_CONDITION_8_WARNING "+file);
            Random random = new Random(271828);
            for (int repetition = 0; repetition < 3; repetition++) checkEncoding(in, random);
        }
        System.out.println(directory+": "+files.size()+" instances x 3 encodings; chapter4 SUT is seeded reconstructed supplement, not author data");
    }
    private static void checkEncoding(Instance in, Random random) {
        int n = in.jobs(); int[] js = new int[n],fa = new int[n],ma = new int[n];
        for (int p = 0; p < n; p++) js[p] = p;
        shuffle(js,random);
        for (int p = 0; p < n; p++) { fa[p] = p < in.factories() ? p : random.nextInt(in.factories()); ma[p] = random.nextInt(in.machines(fa[p],0)); }
        int total = 0;
        for (int f = 0; f < in.factories(); f++) for (int k = 0; k < in.stages(); k++) total += in.machines(f,k);
        int[] wa = new int[in.kind() == ModelKind.CHAPTER4_DUAL_RESOURCE ? n : total];
        if (in.kind() == ModelKind.CHAPTER4_DUAL_RESOURCE) {
            for (int p = 0; p < n; p++) wa[p] = random.nextInt(in.workers(fa[p],0));
        } else {
            int offset = 0;
            for (int f = 0; f < in.factories(); f++) {
                int[] workers = new int[in.workers(f,0)];
                for (int w = 0; w < workers.length; w++) workers[w] = w;
                shuffle(workers,random); System.arraycopy(workers,0,wa,offset,workers.length); offset += workers.length;
            }
        }
        Schedule plain = Decoder.decode(in,js,fa,ma,wa,false), shifted = Decoder.decode(in,js,fa,ma,wa);
        Validator.validate(in,plain); Validator.validate(in,shifted); monotone(plain,shifted);
        assertObjectives(shifted, Decoder.decode(in,js,fa,ma,wa).objectives());
    }
    private static void shuffle(int[] v, Random r) { for (int i=v.length-1;i>0;i--) { int j=r.nextInt(i+1),t=v[i];v[i]=v[j];v[j]=t; } }
    private static Operation find(Schedule s,int j,int k) { for(Operation op:s.operations()) if(op.job()==j&&op.stage()==k)return op; throw new AssertionError("Missing operation"); }
    private static void monotone(Schedule a,Schedule b) { for(int i=0;i<3;i++) if(b.objectives()[i]>a.objectives()[i]+1e-6)fail("Shift worsened objective"); close(a.objectives()[0],b.objectives()[0]); }
    private static void assertObjectives(Schedule schedule,double[] expected) { for(int i=0;i<3;i++)close(schedule.objectives()[i],expected[i]); }
    private static void close(double actual,double expected) { if(Math.abs(actual-expected)>1e-6*Math.max(1,Math.abs(expected)))fail("Expected "+expected+", got "+actual); }
    private static void fail(String message) { throw new AssertionError(message); }
}
