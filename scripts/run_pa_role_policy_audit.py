"""Follow-up zero-FE mechanism audit after role-supply observations; no thresholds."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, read, write_once, controller_lock
from pa_role_policy_audit import audit_policies, check_policy_fixtures
from research.semantic_repair.evidence import digest

ENGINE = ROOT / "runs/pa-population-engineering-20261105-164116-698339"
SUPPLY = ROOT / "runs/pa-role-supply-audit-20261105-211430-755571"


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        assert read(SUPPLY / "status.json")["status"] == "COMPLETE"
        check_policy_fixtures()
        root = ROOT / "runs" / datetime.now().strftime("pa-role-policy-audit-%Y%m%d-%H%M%S-%f")
        root.mkdir()
        print("PA_ROLE_POLICY_AUDIT_ROOT", root, flush=True)
        write_once(root / "protocol.json", {"kind": "Exploratory follow-up after completed role-supply audit",
            "previous": str(SUPPLY), "source": str(ENGINE), "sampling": "Both complete engineering mains; no cutoff duplication",
            "question": "Does specialist-only acceptance produce actual cross-role intermediate states, and which terminal objective vectors were never live?",
            "counterfactualScope": "Same paid parent/child and old archive flags; one decision only, not alternate search trajectory",
            "routeDefinition": "Immediate donor is a specialist-only accepted state, allowing physical-neutral reencoding aliases; receiver differs in role and candidate changes physical schedule",
            "limits": "Engineering fixtures only; no general performance inference, automatic new rule or contribution veto",
            "newSearchFE": 0, "decoderCalls": 0, "defaultMainlineChanged": False})
        source_dir = root / "source"
        source_dir.mkdir()
        for name in ("run_pa_role_policy_audit.py", "pa_role_policy_audit.py", "pa_population_replay.py",
                     "pa_population_state_checks.py", "pa_population_model_checks.py", "pa_model_audit_analysis.py"):
            shutil.copy2(Path(__file__).with_name(name), source_dir / name)
        write_once(root / "code-identities.json", {p.name: digest(p) for p in source_dir.iterdir()})
        identities = {}
        try:
            results = [audit_policies(ENGINE, stem, identities) for stem in ("20_8_5_1", "100_2_3_1")]
            assert all(digest(Path(path)) == value for path, value in identities.items())
            write_once(root / "input-identities.json", identities)
            write_once(root / "analysis.json", {"instances": results, "newSearchFE": 0, "decoderCalls": 0,
                "paidSequencesReconstructedEqual": True, "consumedInputsUnchanged": True,
                "causalBenefitProved": False, "goalAchieved": False})
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error),
                "newSearchFE": 0, "decoderCalls": 0})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", "newSearchFE": 0, "decoderCalls": 0,
            "independentPolicyFixtures": 5, "observedPaidSteps": 47600, "goalAchieved": False})
        print("PA_ROLE_POLICY_AUDIT_COMPLETE", [(r["stem"], len(r["terminalRouteExamples"]), r["terminalObjectivesNeverResident"]) for r in results], flush=True)


if __name__ == "__main__":
    main()
