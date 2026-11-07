"""Zero-FE immediate role-flow and first-admission analysis; no new performance gate."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, write_once, controller_lock
from pa_role_flow import engineering_flow, caller, exposure
from pa_role_frontiers import audit_source
from research.semantic_repair.evidence import digest

ENGINE = ROOT / "runs/pa-population-engineering-20261105-164116-698339"
SOURCES = (("pa-capability-pilot-20261105-175700-160861", "FE100K"),
           ("pa-base-qualification-20261105-180835-751659", "FE500K"))


def verify_boundaries():
    for jobs in (20, 100):
        s = 2 * jobs - 1
        for slot, role in ((0, "MAKESPAN"), (14, "MAKESPAN"), (15, "CENTER"), (69, "CENTER"),
                           (70, "ENERGY"), (84, "ENERGY"), (85, "WORKER_COST"), (99, "WORKER_COST")):
            assert caller(101 + slot * s, jobs) == caller(100 + (slot + 1) * s, jobs) == role
        for endpoint in (1, 2, 100, 101, 100 + 100 * s, 101 + 100 * s, 100000, 500000):
            assert sum(exposure(endpoint, jobs).values()) == endpoint


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        verify_boundaries()
        root = ROOT / "runs" / datetime.now().strftime("pa-role-supply-audit-%Y%m%d-%H%M%S-%f")
        root.mkdir()
        print("PA_ROLE_SUPPLY_AUDIT_ROOT", root, flush=True)
        write_once(root / "protocol.json", {"sources": SOURCES, "engineering": str(ENGINE),
            "newSearchFE": 0, "decoderCalls": 0,
            "question": "Separate immediate accepted cross-role state reads from first-paid-admission role of terminal points",
            "performanceSampling": "All registered endpoints, both PA arms, both instances and seeds, both completed budgets",
            "engineeringSampling": "Only two independent main fixtures; cutoff prefixes excluded from summaries",
            "roleFormula": "FE<=100:INITIAL; else slot=floor((FE-101)/(2N-1))mod100;15M55C15E15W",
            "metrics": "HV/IGD+ and bidirectional C with original common scales/reference; omission is retrospective deletion, not algorithm ablation",
            "interpretation": "First caller not ultimate origin; state read not causal benefit; no contribution veto or revival of stopped versions",
            "defaultMainlineChanged": False, "goalAchieved": False})
        folder = root / "source"
        folder.mkdir()
        dependencies = ("run_pa_role_supply_audit.py", "pa_role_flow.py", "pa_role_frontiers.py",
                        "pa_population_replay.py", "pa_population_state_checks.py", "pa_population_model_checks.py",
                        "pa_model_audit_analysis.py")
        for name in dependencies:
            shutil.copy2(Path(__file__).with_name(name), folder / name)
        write_once(root / "source-identities.json", {p.name: digest(p) for p in folder.iterdir()})
        identities = {}
        try:
            flows = [engineering_flow(ENGINE, stem, identities) for stem in ("20_8_5_1", "100_2_3_1")]
            print("ROLE_FLOW_RECONSTRUCTED", [(r["stem"], r["checkedCallerFormulaSteps"]) for r in flows], flush=True)
            partitions = [audit_source(ROOT / "runs" / name, phase, identities) for name, phase in SOURCES]
            assert all(digest(Path(path)) == expected for path, expected in identities.items())
            write_once(root / "input-identities.json", identities)
            write_once(root / "analysis.json", {"engineeringFlows": flows, "performancePartitions": partitions,
                "newSearchFE": 0, "decoderCalls": 0, "consumedInputsUnchanged": True,
                "causalRoleBenefitProved": False, "goalAchieved": False})
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error),
                "newSearchFE": 0, "decoderCalls": 0})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", "engineeringMainLogs": 2,
            "endpointFrontsRead": 48, "rolePartitions": 16, "newSearchFE": 0, "decoderCalls": 0, "goalAchieved": False})
        print("PA_ROLE_SUPPLY_AUDIT_COMPLETE newSearchFE0 decoderCalls0", flush=True)


if __name__ == "__main__":
    main()
