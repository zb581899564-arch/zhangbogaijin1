import java.nio.file.Paths;
import org.uma.jmetal.util.research.search.CriticalSlotAudit;
public class FailureCheck {public static void main(String[] args) {CriticalSlotAudit.failureEvidence(Paths.get(args[0]),"fixture",0,0,0);}}
