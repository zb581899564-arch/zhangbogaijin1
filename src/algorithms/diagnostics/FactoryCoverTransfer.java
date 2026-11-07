package research.dynamic;

/** Assignment-only augmenting transfer. Every auxiliary job moves to its own target factory. */
final class FactoryCoverTransfer {
    private FactoryCoverTransfer() { }
    static int apply(int[][] genes,int[][] target,boolean[] committed,int job,int factories) {
        int[] counts=new int[factories];for(int[] value:genes)counts[value[0]]++;
        assign(genes,target,job,counts);int auxiliary=0;
        while(true) {
            int missing=-1;for(int f=0;f<factories;f++)if(counts[f]==0){missing=f;break;}
            if(missing<0)return auxiliary;
            int donor=-1;
            for(int j=0;j<genes.length;j++)if(!committed[j]&&target[j][0]==missing&&genes[j][0]!=missing){donor=j;break;}
            if(donor<0)throw new IllegalArgumentException("No compatible target cover transfer");
            assign(genes,target,donor,counts);auxiliary++;
            if(auxiliary>genes.length)throw new AssertionError("Cover transfer did not terminate");
        }
    }
    private static void assign(int[][] genes,int[][] target,int job,int[] counts) {
        counts[genes[job][0]]--;counts[target[job][0]]++;genes[job]=target[job].clone();
    }
}
