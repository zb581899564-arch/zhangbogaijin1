package research.dynamic;

import java.util.Arrays;
import java.util.List;
import org.uma.jmetal.solution.PermutationSolution;
import org.uma.jmetal.util.research.SchedulingEncoding;
import org.uma.jmetal.util.research.model.Instance;

/** Necessary physical-contract checks; no schedule/objective calls and no source mutation. */
final class LinkageGenomeChecks {
    private LinkageGenomeChecks() { }
    static long check(Instance in, PermutationSolution<Integer> parent, PermutationSolution<Integer> donor) {
        int n = in.jobs();int[] all = new int[n];for (int j = 0; j < n; j++) all[j] = j;
        String before = ProbeData.key(parent), other = ProbeData.key(donor);long checked = 0;
        int[][] subsets = {new int[0], all, new int[]{0}, new int[]{n - 1}, Arrays.copyOf(all, n / 2)};
        PermutationSolution<Integer> neutralParent = LinkageGenome.neutral(parent, in.factories());
        PermutationSolution<Integer> neutralDonor = LinkageGenome.neutral(donor, in.factories());
        for (int[] subset : subsets) {
            LinkageGenome.Proposal a = LinkageGenome.donate(parent, donor, subset, in.factories());
            LinkageGenome.Proposal b = LinkageGenome.donate(neutralParent, neutralDonor, subset, in.factories());
            if (a.fallback != b.fallback || !LinkageGenome.physical(a.point, in.factories()).equals(LinkageGenome.physical(b.point, in.factories())))
                throw new AssertionError("Donation depends on neutral global interleaving");
            if (SchedulingEncoding.repair(a.point, in) != 0 || SchedulingEncoding.repair(b.point, in) != 0)
                throw new AssertionError("Tuple donation requires repair");
            if (subset.length == 0 && !LinkageGenome.physical(a.point, in.factories()).equals(LinkageGenome.physical(parent, in.factories())))
                throw new AssertionError("Empty donation does not preserve physical parent");
            if (subset.length == n && !LinkageGenome.physical(a.point, in.factories()).equals(LinkageGenome.physical(donor, in.factories())))
                throw new AssertionError("Full donation does not reproduce donor");
            checked++;
        }
        if (!before.equals(ProbeData.key(parent)) || !other.equals(ProbeData.key(donor))) throw new AssertionError("Donation mutated input");
        checkEmptyFactory(in, parent);return checked + 1;
    }
    private static void checkEmptyFactory(Instance in, PermutationSolution<Integer> template) {
        PermutationSolution<Integer> parent = LinkageGenome.copy(template), donor = LinkageGenome.copy(template);
        @SuppressWarnings("unchecked") List<Integer> pm = (List<Integer>)parent.getAttribute("machine");
        @SuppressWarnings("unchecked") List<Integer> dm = (List<Integer>)donor.getAttribute("machine");
        for (int j = 0; j < in.jobs(); j++) {
            int factory = j == 0 ? 0 : 1 + (j - 1) % (in.factories() - 1);
            parent.setVariableValue(j, j);parent.setVariableValueid(j, factory);pm.set(j, 0);parent.setVariableValueworker(j, 0);
            donor.setVariableValue(j, j);donor.setVariableValueid(j, j == 0 ? 1 : j == 1 ? 0 : factory);dm.set(j, 0);donor.setVariableValueworker(j, 0);
        }
        LinkageGenome.Proposal child = LinkageGenome.donate(parent, donor, new int[]{0}, in.factories());
        if (!child.fallback || !ProbeData.key(child.point).equals(ProbeData.key(parent))) throw new AssertionError("Empty-factory fallback differs");
    }
}
