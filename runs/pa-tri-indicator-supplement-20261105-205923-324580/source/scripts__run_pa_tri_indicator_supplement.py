"""Zero-search-FE joint metric supplement, leaving all frozen experiments intact."""
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from datetime import datetime
from pathlib import Path
import shutil

from run_long_budget_bridge import ROOT, write_once, controller_lock
from pa_tri_indicator_analysis import analyze_source, render_report
from research.semantic_repair.evidence import digest

SOURCES = (("pa-capability-pilot-20261105-175700-160861", "FE100K"),
           ("pa-base-qualification-20261105-180835-751659", "FE500K"))


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        root = ROOT / "runs" / datetime.now().strftime("pa-tri-indicator-supplement-%Y%m%d-%H%M%S-%f")
        root.mkdir()
        print("PA_TRI_INDICATOR_ROOT", root, flush=True)
        write_once(root / "protocol.json", {"kind": "Posthoc reporting supplement, not a replacement gate",
            "sources": SOURCES, "sampling": "All registered terminal fronts, 6arms x 2instances x 2seeds per source",
            "metrics": ["HV", "IGDplus", "C(A,B)", "C(B,A)"],
            "coverage": "Objective-deduplicated raw vectors, exact weak minimization dominance, equality included; no epsilon",
            "primary": "PA_JOINT", "HV_IGDplus": "Reuse original common normalization/reference construction; recompute to check identity",
            "aggregation": "Paired seed effects and median within instance; no weighted score, majority vote, new pass gate or statistical inference",
            "defaultMainlineChanged": False, "newSearchFE": 0, "decoderCalls": 0})
        snapshot = root / "source"
        snapshot.mkdir()
        code = (Path(__file__), Path(__file__).with_name("pa_tri_indicator_analysis.py"),
                ROOT / "research/dynamic_benchmark/tri_indicators.py",
                ROOT / "research/dynamic_benchmark/check_tri_indicators.py",
                ROOT / "research/dynamic_benchmark/metrics.py", ROOT / "research/expansion_audit/metrics.py")
        for path in code:
            name = str(path.relative_to(ROOT)).replace("\\", "__").replace("/", "__")
            shutil.copy2(path, snapshot / name)
        write_once(root / "code-identity.json", {str(p.relative_to(ROOT)): digest(p) for p in code})
        identities = {}
        try:
            sources = [analyze_source(ROOT / "runs" / name, phase, identities) for name, phase in SOURCES]
            if any(digest(Path(path)) != expected for path, expected in identities.items()):
                raise ValueError("Read-only input identity changed during analysis")
            write_once(root / "input-identities.json", identities)
            result = {"sources": sources, "newSearchFE": 0, "decoderCalls": 0,
                "frozenHV_IGDplusRecomputedConsistent": True, "consumedInputsUnchanged": True,
                "originalGatesRejudged": False, "goalAchieved": False}
            write_once(root / "analysis.json", result)
            (root / "report.md").write_text(render_report(result), encoding="utf-8")
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error),
                "newSearchFE": 0, "decoderCalls": 0})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", "newSearchFE": 0, "decoderCalls": 0,
            "fronts": 48, "pairedComparisons": 40, "goalAchieved": False})
        print("PA_TRI_INDICATOR_COMPLETE fronts48 pairs40 newSearchFE0 decoderCalls0", flush=True)


if __name__ == "__main__":
    main()
