"""Small paid role-continuation screen before any new optimizer mechanism is implemented."""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import shutil
import time

from role_relay_plan import inputs, cases, encoded, ANCHOR, ROLES, STEPS
from role_relay_analysis import analyze
from run_dynamic_deep_roles import BRIDGE
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, controller_lock
from run_pddr_role_budget import frozen_classpath


def main():
    root = ROOT / "runs" / datetime.now().strftime("role-relay-probe-%Y%m%d-%H%M%S-%f")
    root.mkdir(); print("RELAY_ROOT", root, flush=True)
    started = time.monotonic()
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            snapshots, references, background, origins = inputs()
            plan = cases(snapshots)
            write_once(root / "protocol.json", {"instance": "20_2_3_1", "paidSnapshotFE": 5100,
                "sourceOrigins": origins, "roles": ROLES, "freeSamplesPerSource": 8, "cohorts": ["S", "U"],
                "sampling": "Evenly spaced by original free-particle index within each role, alternating TRAIN/HOLDOUT.",
                "continuation": "Unchanged deep LocalSearch with natural slots; repeat visits only if the visit "
                                "returns before the common budget. Four recipient preferences; common 200-point "
                                "frozen paid reference, new personal history, no inherited Q state or family.",
                "actualFEPerTrial": STEPS + 1, "trialCount": len(plan), "maxPaidFE": len(plan) * (STEPS + 1),
                "baseline": "All known paid archive points up to FE5100 in S and U plus all source reference "
                            "solutions are in A0 before any continuation. Already-good donor copies earn zero gain.",
                "ordinaryControls": ["SELF same-source role", "ELITE by target objective or PDDR", "uniform RANDOM"],
                "gate": "Select best off-diagonal source on TRAIN only, test its four HOLDOUT parents per target. "
                        "At least two SPECIAL target tasks must beat SELF/ELITE/RANDOM in mean heldout batch "
                        "new HV to warrant an isolated closed-loop proposal; no tuning the threshold after results.",
                "limits": "Association of source role and solution quality remains; no novelty claim or full-cost "
                          "efficacy from this screen. Uniform cohort is a diagnostic, not a weak final benchmark.",
                "normalization": read(ANCHOR / "protocol.json")["normalization"]})
            write_once(root / "parents.json", snapshots); write_once(root / "cases.json", plan)
            write_once(root / "background.json", background)
            parent = {p["id"]: p for p in snapshots}
            (root / "reference.tsv").write_text("\n".join("\t".join(encoded(r)) for r in references) + "\n", encoding="utf-8")
            (root / "cases.tsv").write_text("\n".join("\t".join(map(str, [c["id"], c["target"], c["seed"],
                c["continuationFE"], *encoded(parent[c["parent"]])])) for c in plan) + "\n", encoding="utf-8")
            cp = frozen_classpath(); classes, src = root / "classes", root / "source"
            classes.mkdir(); src.mkdir()
            java = shutil.copy2(ROOT / "src/algorithms/diagnostics/RoleRelayProbe.java", src)
            for file in (Path(__file__), Path(__file__).with_name("role_relay_plan.py"), Path(__file__).with_name("role_relay_analysis.py")):
                shutil.copy2(file, src)
            execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", cp, "-d", str(classes), str(java)], root / "compile.log")
            write_once(root / "class-hashes.json", {p.relative_to(classes).as_posix(): sha256(p.read_bytes()).hexdigest()
                                                  for p in classes.rglob("*.class")})
            cp = f"{classes};{cp}"
            (root / "classpath.txt").write_text(cp, encoding="utf-8")
            cmd = ["java", "-Xms32m", "-Xmx2g", "-cp", cp, "org.uma.jmetal.util.research.search.RoleRelayProbe",
                   str(BRIDGE / "inputs/20_2_3_1.txt"), str(BRIDGE / "inputs/RECONSTRUCTED-setup.txt"),
                   str(BRIDGE / "inputs/fatigue-input.txt"), str(root / "reference.tsv"), str(root / "cases.tsv"), str(root)]
            write_once(root / "command.json", cmd)
            execute(cmd, root / "run.log")
            result = analyze(root)
            receipt, = rows(root / "receipt.jsonl")
            assert receipt["successful"] == len(plan) * (STEPS + 1) and receipt["failed"] == 0
    except BaseException as exc:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": str(exc)})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "receipt": receipt, "gate": result["gate"],
                                      "wallSeconds": time.monotonic() - started})
    print("RELAY_COMPLETE", result["gate"], result["heldout"], flush=True)


if __name__ == "__main__":
    main()
