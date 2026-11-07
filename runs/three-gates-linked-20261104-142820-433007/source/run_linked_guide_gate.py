"""One preregistered generator hypothesis, one ordinary control, and matched deep-LS baselines."""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np

from run_dynamic_deep_roles import BRIDGE, ledger
from run_dynamic_reverse_ledger_audit import SEED, POINTS
from run_long_budget_bridge import ROOT, controller_lock, execute, hypervolume, igd_plus, nondominated, read, rows, write_once
from run_pddr_role_budget import frozen_classpath
from run_paired_qgs_guidance import replace


ANCHOR = ROOT / "runs/pddr-role-budget-20261104-095957/DEEP"
REVERSE = ROOT / "runs/dynamic-reverse-ledger-20261103-231754-095093"
ORDER = ("BASE", "RANDOM", "LINKED", "NSGA")


def protocol(root):
    write_once(root / "protocol.json", {
        "instance": "20_2_3_1", "seed": SEED, "order": ORDER, "actualFEPerArm": 500000,
        "ledger": str(ANCHOR / "ledger.csv"), "timePrimarySeconds": 4, "auxTimeSeconds": [1, 2, 6, 8, 10, 12],
        "candidate": "After each unchanged QGS JS swap-prefix, copy donor FA/MA/WA jointly for exactly "
                     "the jobs touched by applied swaps, gated by the existing PC_FA=0.2. Preserve "
                     "initial job/resource swap, personal then global guidance, mutation probabilities, "
                     "fixed-family restore, repair, Q settings, four roles, sharing, PDDR and LS ledger.",
        "ordinaryControl": "Identical joint operator and number of selected jobs, but choose a uniform random "
                           "job set independently of the moved set. Both arms compute the same shuffle.",
        "scope": "One generator change, not four-matrix crossover novelty or fatigue-specificity evidence. "
                 "Vector-coupling oracle was an attribution probe and supplies no donor to this search.",
        "gate1": "Actionable coupling hypothesis; originality and fatigue-specific value remain unproven. "
                 "Do not claim conventional synchronous crossover as the paper contribution.",
        "gate2": {"minimumHVgainOverBASEandRANDOMpct": 1, "primaryFE": 500000,
                  "referenceChecks": [1.25, 1.5, 2], "sameTimeHVmustNotRegressAgainstEither": 4,
                  "pooledIGDPlusMustNotRegressAgainstEither": True,
                  "required": "Actual intervention, zero failures, equal physical ledger, original BASE objective "
                              "trajectory and final genomes unchanged, same initialization. No quota/seed retry."},
        "gate3Conditional": {"instances": ["20_2_3_1", "100_2_3_1"],
                             "seeds": [8117003, 8117029, 8117051], "arms": ORDER,
                             "actualFE": 500000, "decision": "Only run if gate2 passes; require each-instance "
                             "median >=1% over BASE, 2/3 positive seeds, no >1% median NSGA deficit, "
                             "and no material same-time or IGD+ regression."},
        "normalization": read(REVERSE / "protocol.json")["normalization"],
        "witness": "Read-only all-proposal dominance/pbest-history counters, survivor branch counts and "
                   "later-generation archive admissions. Propagation is not causal credit. All observation cost paid in time."})


def build(root):
    cp = frozen_classpath()
    src, classes = root / "source", root / "classes"
    src.mkdir(); classes.mkdir()
    for name in ("LinkedGuideKernel", "BundleWitness"):
        shutil.copy2(ROOT / f"src/algorithms/diagnostics/{name}.java", src)
    # Shadow only this isolated classpath. BASE delegates the previously frozen kernel unchanged.
    policy = (ROOT / "src/algorithms/mechanism/JobAlignedPolicy.java").read_text(encoding="utf-8")
    policy = replace(policy, "    private long proposals;", "    private long proposals;\n"
                     "    private final LinkedGuideKernel linked;\n"
                     "    private static LinkedGuideKernel active;\n"
                     "    public static java.util.Map<String,Object> bundleDiagnostics() {\n"
                     "        return active == null ? new java.util.LinkedHashMap<>() : active.diagnostics();\n    }")
    policy = replace(policy, "        kernel = new JobAlignedPaperKernel(instance, resolved);",
                     "        kernel = new JobAlignedPaperKernel(instance, resolved);\n"
                     "        String mode = System.getProperty(\"research.bundle.mode\", \"BASE\");\n"
                     "        if (!mode.equals(\"BASE\") && !mode.equals(\"LINKED\") && !mode.equals(\"RANDOM\"))\n"
                     "            throw new IllegalArgumentException(\"Unknown bundle arm\");\n"
                     "        linked = mode.equals(\"BASE\") ? null : new LinkedGuideKernel(instance, resolved, mode.equals(\"RANDOM\"));\n"
                     "        active = linked;")
    policy = replace(policy, "kernel.child(parent, personal, leader)",
                     "linked == null ? kernel.child(parent, personal, leader) : linked.child(parent, personal, leader)")
    (src / "JobAlignedPolicy.java").write_text(policy, encoding="utf-8")
    body = (ROOT / "runs/dynamic-deep-local-20261103-184901-271850/source/CanonicalHmopso.java").read_text(encoding="utf-8")
    body = replace(body, "            if (support != null) support.beginGeneration();",
                   "            BundleWitness.begin();\n            if (support != null) support.beginGeneration();")
    body = replace(body, "            result.add(particle.descend(child));",
                   "            Particle nextParticle = particle.descend(child);\n"
                   "            BundleWitness.paid(particle, nextParticle, preference);\n            result.add(nextParticle);")
    body = replace(body, "                population = selected.survivors();",
                   "                population = selected.survivors();\n"
                   "                BundleWitness.selected(globalSnapshots, offspring, population);")
    (src / "CanonicalHmopso.java").write_text(body, encoding="utf-8")
    state = (REVERSE / "source/SearchState.java").read_text(encoding="utf-8")
    state = replace(state, "        problem.evaluate(candidate);",
                    "        candidate.setAttribute(\"bundle.stage\", stage);\n        problem.evaluate(candidate);")
    (src / "SearchState.java").write_text(state, encoding="utf-8")
    entry = (ROOT / "src/algorithms/diagnostics/PddrIsolationRun.java").read_text(encoding="utf-8")
    entry = replace(entry, "            completed(paid, seconds, changed, archive);",
                    "            org.uma.jmetal.util.research.search.BundleWitness.archiveAdmission(s.getAttribute(\"bundle.stage\"), changed);\n"
                    "            completed(paid, seconds, changed, archive);")
    entry = replace(entry, "        obs.write(out);", "        obs.write(out);\n"
                    "        append(out.resolve(\"bundle-witness.jsonl\"), org.uma.jmetal.util.research.search.BundleWitness.report());\n"
                    "        append(out.resolve(\"bundle-intervention.jsonl\"), org.uma.jmetal.util.research.mechanism.JobAlignedPolicy.bundleDiagnostics());")
    (src / "PddrIsolationRun.java").write_text(entry, encoding="utf-8")
    shutil.copy2(Path(__file__), src)
    execute(["javac", "-encoding", "UTF-8", "--release", "8", "-cp", cp, "-d", str(classes),
             *map(str, src.glob("*.java"))], root / "compile.log")
    full = f"{classes};{cp}"
    (root / "classpath.txt").write_text(full, encoding="utf-8")
    write_once(root / "class-hashes.json", {p.relative_to(classes).as_posix(): sha256(p.read_bytes()).hexdigest()
                                          for p in classes.rglob("*.class")})
    execute(["java", "-version"], root / "jdk.log")
    execute(["java", "-cp", full, "org.uma.jmetal.util.research.mechanism.JobAlignedPolicyChecks"], root / "base-kernel-checks.log")
    return full


def run_arm(root, cp, arm):
    out = root / arm; out.mkdir()
    inputs = root / "inputs"
    cmd = ["java", "-Xms32m", "-Xmx2g", f"-Dresearch.bundle.mode={arm if arm != 'NSGA' else 'BASE'}",
           "-cp", cp, "research.dynamic.PddrIsolationRun", str(inputs / "20_2_3_1.txt"),
           str(inputs / "RECONSTRUCTED-setup.txt"), str(inputs / "fatigue-input.txt"), str(out),
           "NSGA2_4V" if arm == "NSGA" else "SHARE_JOB_ALIGNED", "LINEAR", str(root / "ledger.csv"),
           "500000", str(SEED), *map(str, POINTS)]
    write_once(out / "command.json", cmd)
    print("ARM", arm, flush=True)
    start = time.monotonic()
    with (out / "run.log").open("x", encoding="utf-8") as log:
        proc = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=300)
    write_once(out / "process.json", {"wallSeconds": time.monotonic() - start, "returnCode": proc.returncode})
    if proc.returncode: raise RuntimeError((out / "run.log").read_text(encoding="utf-8")[-2500:])
    receipt, = rows(out / "run-receipt.jsonl")
    assert receipt["attempted"] == receipt["successful"] == receipt["decoder"]["dynamic.evaluations"] == 500000
    assert receipt["failed"] == 0 and receipt["stopReason"] == "FE_LIMIT"
    assert [s[:-1] for s in ledger(out)] == [s[:-1] for s in ledger(ANCHOR / "SPECIAL-LINEAR")]
    assert (out / "initial-population.jsonl").read_bytes() == (ANCHOR / "SPECIAL-LINEAR/initial-population.jsonl").read_bytes()
    assert read(out / "summary.json")["offlineValidationDecodes"] == len(rows(out / "solutions.jsonl"))
    if arm in ("BASE", "NSGA"):
        prior = ANCHOR / ("SPECIAL-LINEAR" if arm == "BASE" else "NSGA-LINEAR")
        assert (out / "solutions.jsonl").read_bytes() == (prior / "solutions.jsonl").read_bytes()
        assert [r["front"] for r in rows(out / "anytime.jsonl")] == [r["front"] for r in rows(prior / "anytime.jsonl")]
    write_once(out / "verified.json", {"sameInitial": True, "samePhysicalLedger": True, "zeroFailures": True,
                                      "baseTrajectoryUnchanged": arm in ("BASE", "NSGA")})
    return receipt


def analyze(root):
    norm = read(root / "protocol.json")["normalization"]
    scale, lower = np.asarray(norm["scale"]), np.asarray(norm["lower"])
    normed = lambda p: (np.asarray(p) - lower) / scale
    all_fe = {a: rows(root / a / "anytime.jsonl") for a in ORDER}
    all_time = {a: rows(root / a / "time.jsonl") for a in ORDER}
    hv = lambda r, ref=1.5: float(hypervolume(normed(r["front"]), (ref,) * 3))
    ref = nondominated(np.vstack([normed(all_fe[a][-1]["front"]) for a in ORDER]))
    terminal = {a: {"hv": hv(all_fe[a][-1]), "igdPlus": float(igd_plus(normed(all_fe[a][-1]["front"]), ref))} for a in ORDER}
    effects = {str(r): {a: 100 * (hv(all_fe["LINKED"][-1], r) / hv(all_fe[a][-1], r) - 1)
                       for a in ("BASE", "RANDOM", "NSGA")} for r in (1.25, 1.5, 2)}
    primary_time = {a: hv(next(r for r in all_time[a] if abs(r["checkpoint"] - 4) < 1e-9)) for a in ORDER}
    gains_pass = all(effects["1.5"][a] >= 1 for a in ("BASE", "RANDOM"))
    sign_pass = all(effects[str(r)][a] > 0 for r in (1.25, 2) for a in ("BASE", "RANDOM"))
    time_pass = all(primary_time["LINKED"] >= primary_time[a] for a in ("BASE", "RANDOM"))
    igd_pass = all(terminal["LINKED"]["igdPlus"] <= terminal[a]["igdPlus"] for a in ("BASE", "RANDOM"))
    result = {"terminal": terminal, "candidateEffectsPct": effects, "same4SecondsHV": primary_time,
              "paidFECurves": [{"fe": x, "HV": {a: hv(all_fe[a][i]) for a in ORDER}} for i, x in enumerate(POINTS)],
              "sameTimeCurves": [{"seconds": r["checkpoint"], "arms": {a: {"fe": all_time[a][i]["fe"],
                                  "hv": hv(all_time[a][i])} for a in ORDER}} for i, r in enumerate(all_time["BASE"])],
              "checks": {"terminalGain": gains_pass, "referenceDirection": sign_pass,
                         "sameTime": time_pass, "IGDplus": igd_pass},
              "gate2": "PASS" if gains_pass and sign_pass and time_pass and igd_pass else "STOP",
              "gate3": "CONDITIONAL_READY" if gains_pass and sign_pass and time_pass and igd_pass else "NOT_TRIGGERED"}
    write_once(root / "comparison.json", result)
    return result


def main():
    root = ROOT / "runs" / datetime.now().strftime("three-gates-linked-%Y%m%d-%H%M%S-%f")
    root.mkdir(); print("LINKED_GATE_ROOT", root, flush=True)
    start, complete = time.monotonic(), []
    try:
        with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
            protocol(root)
            shutil.copytree(BRIDGE / "inputs", root / "inputs")
            shutil.copy2(ANCHOR / "ledger.csv", root / "ledger.csv")
            cp = build(root)
            for arm in ORDER:
                run_arm(root, cp, arm); complete.append(arm)
            result = analyze(root)
    except BaseException as exc:
        write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "completed": complete, "error": str(exc)})
        raise
    write_once(root / "status.json", {"status": "COMPLETE", "completed": complete, "paidSearchFE": 2000000,
                                      "wallSeconds": time.monotonic() - start, "gate2": result["gate2"],
                                      "gate3": result["gate3"]})
    print("LINKED_GATE_COMPLETE", result, flush=True)


if __name__ == "__main__":
    main()
