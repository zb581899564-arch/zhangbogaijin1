package org.uma.jmetal.util.research.modelglobal;

import java.util.*;
import research.dynamic.DynamicJson;

/** Actual frozen QPA and PA models evaluated on unscored, physically identical carriers. */
final class GeometryPopulation {
    final List<QpaIndividual> points;
    final List<TypedScheduleGenome> reencoded=new ArrayList<>();
    final QpaLinkageModel qpa;
    final double[][] paMatrix;
    final List<int[]> paSubsets;

    GeometryPopulation(List<QpaIndividual> input,GeometryWorld world,long noiseSeed) {
        if (input.size()!=100) throw new AssertionError("Expected100 model carriers");points=input;
        qpa=new QpaLinkageModel(points,world.evaluation);int n=world.in.jobs();Random random=new Random(noiseSeed);
        int[][] assignments=new int[100][n];double[][] keys=new double[100][];
        for (int i=0;i<100;i++) {
            TypedScheduleGenome source=TypedScheduleGenome.fromVectors(world.catalog,points.get(i).genome.toVectors());
            TypedScheduleGenome value=FactoryKeyReencoder.apply(world.catalog,source,random);reencoded.add(value);
            int[] resources=value.allocations();keys[i]=value.priorities();
            for (int j=0;j<n;j++) assignments[i][j]=world.catalog.factory(resources[j]);
        }
        paMatrix=new PaDependencyModel(assignments,keys,world.in.factories()).matrix();paSubsets=new LinkageHierarchy(paMatrix).subsets();
    }

    void samePhysicalAndPA(GeometryPopulation original,GeometryWorld world) {
        for (int i=0;i<100;i++) {
            if (!Arrays.equals(GeometryProposals.physical(points.get(i).genome.toVectors(),world.in.factories()),
                    GeometryProposals.physical(original.points.get(i).genome.toVectors(),world.in.factories())))
                throw new AssertionError("Input physical factory chains changed");
            if (!Arrays.equals(points.get(i).objectives(),original.points.get(i).objectives())) throw new AssertionError("Known objectives changed");
            if (!Arrays.equals(reencoded.get(i).allocations(),original.reencoded.get(i).allocations())
                    ||!Arrays.equals(reencoded.get(i).priorities(),original.reencoded.get(i).priorities()))
                throw new AssertionError("PA same-stream reencoding not invariant");
        }
        if (!Arrays.deepEquals(paMatrix,original.paMatrix)||!equalSubsets(paSubsets,original.paSubsets))
            throw new AssertionError("PA model/FOS not invariant");
    }

    private static boolean equalSubsets(List<int[]> a,List<int[]> b) {
        if (a.size()!=b.size()) return false;
        for (int i=0;i<a.size();i++) if (!Arrays.equals(a.get(i),b.get(i))) return false;return true;
    }

    String json(String population,String variant) {
        Map<String,Object> row=new LinkedHashMap<>();row.put("population",population);row.put("variant",variant);
        row.put("qpaAffinity",qpa.affinity);row.put("qpaFullSubsets",qpa.fullSubsets);row.put("qpaActiveSubsets",qpa.activeSubsets);
        row.put("paAffinity",paMatrix);row.put("paSubsets",paSubsets);
        List<Map<String,Object>> genes=new ArrayList<>();
        for (TypedScheduleGenome value:reencoded) {
            Map<String,Object> point=new LinkedHashMap<>();point.put("resources",value.allocations());point.put("keys",value.priorities());genes.add(point);
        }
        row.put("paGenes",genes);return DynamicJson.encode(row);
    }
}
