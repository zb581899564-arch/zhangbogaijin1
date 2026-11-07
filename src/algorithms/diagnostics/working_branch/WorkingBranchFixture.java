package research.dynamic;

import java.nio.file.*;
import java.util.*;
import org.uma.jmetal.util.research.modelglobal.*;
import org.uma.jmetal.util.research.search.Direction;

/** Pure acceptance/archive/input checks; no decoder or problem evaluation calls. */
public final class WorkingBranchFixture {
    private static void require(boolean ok){if(!ok)throw new AssertionError("Working-branch fixture");}
    public static void main(String[] args)throws Exception {
        FirstStageCatalog catalog=new FirstStageCatalog(WorkingBranchRun.problem(Paths.get(args[0]),args[1]).getSchedulingInstance());
        WorkingBranchData data=new WorkingBranchData(Paths.get(args[2]),catalog);
        PaInternalArchive a=new PaInternalArchive();a.offer(new double[]{0,0,0});
        PaInternalArchive.Flags dominated=a.offer(new double[]{1,1,1});
        require(dominated.dominated);
        require(!WorkingBranchRules.keep(Direction.MAKESPAN,new double[]{1,0,0},new double[]{1,1,1},dominated));
        require(WorkingBranchRules.keep(Direction.CENTER,new double[]{1,1,1},new double[]{2,2,2},dominated));
        require(!WorkingBranchRules.keep(Direction.CENTER,new double[]{2,1,1},new double[]{1,2,2},a.offer(new double[]{2,1,1})));
        int checks=0;
        for(WorkingBranchData.Case c:data.cases) {
            PaInternalArchive left=data.archive(c),right=data.archive(c);int old=right.snapshot().length;
            left.offer(new double[]{-1,-1,-1});require(right.snapshot().length==old);require(left.snapshot().length==1);
            for(String label:new String[]{"P","Q","R"}) {
                CounterfactualInputs.Entry e=data.seed(c,label);
                require(!WorkingBranchRules.fresh(e.expected,data.archives.get(c.context)));checks++;
            }
        }
        require(checks==36);System.out.println("WORKING_BRANCH_FIXTURE_PASSED seeds=36 evaluations=0 decoderCalls=0");
    }
}
