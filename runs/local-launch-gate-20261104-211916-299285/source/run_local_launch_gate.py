"""One architecture hypothesis: where unchanged local search starts after QGS."""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np

from run_dynamic_deep_roles import BRIDGE, ledger
from run_dynamic_reverse_ledger_audit import POINTS, SEED
from run_long_budget_bridge import ROOT, read, rows, write_once, execute, hypervolume, igd_plus, nondominated, controller_lock
from run_pddr_role_budget import frozen_classpath
from run_paired_qgs_guidance import replace

ANCHOR = ROOT / "runs/pddr-role-budget-20261104-095957/DEEP"
ORDER = ("CURRENT", "POOLED_ELITE", "OWN_HISTORY", "NSGA")


def build(root):
    cp = frozen_classpath(); src, classes = root / "source", root / "classes"
    src.mkdir(); classes.mkdir()
    canonical = (ROOT / "runs/dynamic-deep-local-20261103-184901-271850/source/CanonicalHmopso.java").read_text(encoding="utf-8")
    canonical = replace(canonical, "                    offspring.add(local.improve(particle, preference, reference));",
                        "                    Particle launched = LocalLaunch.choose(particle, preference, reference);\n"
                        "                    offspring.add(local.improve(launched, preference, reference));")
    (src / "CanonicalHmopso.java").write_text(canonical, encoding="utf-8")
    shutil.copy2(ROOT / "src/algorithms/diagnostics/LocalLaunch.java", src)
    entry = (ROOT / "src/algorithms/diagnostics/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry = replace(entry, "        obs.write(out);", "        obs.write(out);\n"
                    "        append(out.resolve(\"launch.jsonl\"), org.uma.jmetal.util.research.search.LocalLaunch.diagnostics());")
    (src / "PddrIsolationRun.java").write_text(entry, encoding="utf-8")
    shutil.copy2(Path(__file__), src)
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", cp, "-d", str(classes),
             *map(str, src.glob("*.java"))], root / "compile.log")
    write_once(root / "class-hashes.json", {p.relative_to(classes).as_posix(): sha256(p.read_bytes()).hexdigest() for p in classes.rglob("*.class")})
    (root / "classpath.txt").write_text(f"{classes};{cp}", encoding="utf-8")
    return f"{classes};{cp}"


def run(root, cp, arm):
    out = root / arm; out.mkdir(); inp = root / "inputs"
    cmd = ["java", "-Xms32m", "-Xmx2g", f"-Dresearch.launch.mode={arm if arm != 'NSGA' else 'CURRENT'}", "-cp", cp,
           "research.dynamic.PddrIsolationRun", str(inp / "20_2_3_1.txt"), str(inp / "RECONSTRUCTED-setup.txt"),
           str(inp / "fatigue-input.txt"), str(out), "NSGA2_4V" if arm == "NSGA" else "SHARE_JOB_ALIGNED",
           "LINEAR", str(root / "ledger.csv"), "500000", str(SEED), *map(str, POINTS)]
    write_once(out / "command.json", cmd); print("LAUNCH_ARM", arm, flush=True)
    started = time.monotonic()
    with (out / "run.log").open("x", encoding="utf-8") as log:
        code = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=300).returncode
    write_once(out / "process.json", {"returnCode": code, "wallSeconds": time.monotonic() - started})
    if code: raise RuntimeError((out / "run.log").read_text(encoding="utf-8")[-2500:])
    receipt, = rows(out / "run-receipt.jsonl")
    assert receipt["attempted"] == receipt["successful"] == receipt["decoder"]["dynamic.evaluations"] == 500000
    assert receipt["failed"] == 0
    assert [x[:-1] for x in ledger(out)] == [x[:-1] for x in ledger(ANCHOR / "SPECIAL-LINEAR")]
    assert (out / "initial-population.jsonl").read_bytes() == (ANCHOR / "SPECIAL-LINEAR/initial-population.jsonl").read_bytes()
    if arm in ("CURRENT", "NSGA"):
        prior = ANCHOR / ("SPECIAL-LINEAR" if arm == "CURRENT" else "NSGA-LINEAR")
        assert (out / "solutions.jsonl").read_bytes() == (prior / "solutions.jsonl").read_bytes()
        assert [x["front"] for x in rows(out / "anytime.jsonl")] == [x["front"] for x in rows(prior / "anytime.jsonl")]
    write_once(out / "verified.json", {"FE": 500000, "failures": 0, "physicalLedgerMatches": True,
                                      "initializationMatches": True, "trajectoryMatchesWhenUnchanged": arm in ("CURRENT", "NSGA")})


def analyze(root):
    norm = read(root / "protocol.json")["normalization"]
    normalize = lambda p: (np.asarray(p) - norm["lower"]) / norm["scale"]
    curves = {a: rows(root / a / "anytime.jsonl") for a in ORDER}
    timed = {a: rows(root / a / "time.jsonl") for a in ORDER}
    hv = lambda r, ref=1.5: float(hypervolume(normalize(r["front"]), (ref,) * 3))
    empirical = nondominated(np.vstack([normalize(curves[a][-1]["front"]) for a in ORDER]))
    terminal = {a: {"HV": hv(curves[a][-1]), "IGDplus": float(igd_plus(normalize(curves[a][-1]["front"]), empirical)),
                   "launch": rows(root / a / "launch.jsonl")[0]} for a in ORDER}
    effects = {str(ref): {a: 100 * (hv(curves["OWN_HISTORY"][-1], ref) / hv(curves[a][-1], ref) - 1)
                         for a in ("CURRENT", "POOLED_ELITE", "NSGA")} for ref in (1.25, 1.5, 2)}
    eligible = effects["1.5"]["CURRENT"] >= 1 and effects["1.5"]["POOLED_ELITE"] > 0 and effects["1.5"]["NSGA"] >= -1
    output = {"terminal": terminal, "ownEffectsPct": effects, "gate": "SMALL_FRESH_SCREEN" if eligible else "STOP_THIS_LAUNCH_RULE",
              "FECurve": [{"fe": x["fe"], "HV": {a: hv(curves[a][i]) for a in ORDER}} for i, x in enumerate(curves["CURRENT"])],
              "timeCurve": [{"seconds": x["checkpoint"], "HV": {a: hv(timed[a][i]) for a in ORDER},
                             "FE": {a: timed[a][i]["fe"] for a in ORDER}} for i, x in enumerate(timed["CURRENT"])]}
    write_once(root / "comparison.json", output)
    return output


def main():
    root = ROOT / "runs" / datetime.now().strftime("local-launch-gate-%Y%m%d-%H%M%S-%f")
    root.mkdir(); print("LAUNCH_ROOT", root, flush=True)
    start, completed = time.monotonic(), []
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            write_once(root / "protocol.json", {"instance": "20_2_3_1", "seed": SEED, "actualFEPerArm": 500000,
                "order": ORDER, "evidence": "role-relay-probe-20261104-205118-226005: four SPECIAL relay tasks failed; "
                        "ordinary elite restarts, not role labels, showed a CENTER signal. Test local launch origin.",
                "scope": "Only free particles change local start, 20 fixed-family particles and sharing stay. "
                         "Existing personal history vs original QGS current, with pooled paid-elite ordinary control. "
                         "Same strict role comparison, no new neighborhood/acceptance/Q rule or budget changes.",
                "gate": "OWN_HISTORY >=1% terminal HV over CURRENT, positive vs POOLED_ELITE, no worse than -1% "
                        "vs matched NSGA. Otherwise end this rule; no alternate thresholds or seeds to rescue.",
                "normalization": read(ROOT / "runs/dynamic-reverse-ledger-20261103-231754-095093/protocol.json")["normalization"]})
            shutil.copytree(BRIDGE / "inputs", root / "inputs"); shutil.copy2(ANCHOR / "ledger.csv", root / "ledger.csv")
            cp = build(root)
            for arm in ORDER: run(root, cp, arm); completed.append(arm)
            result = analyze(root)
    except BaseException as exc:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "completed": completed, "error": str(exc)})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "completed": completed, "FE": 2000000,
                                      "wallSeconds": time.monotonic() - start, "gate": result["gate"]})
    print("LAUNCH_COMPLETE", result, flush=True)


if __name__ == "__main__":
    main()
