"""Verify the center-reference goal from raw checkpoints, class bytes and paid traces."""
from datetime import datetime
import math
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

import numpy as np

from reverse_ledger_analysis import archive_admissions
from run_center_entry_cross_replay import ANCHOR, END_FE, ENTRY_FE, ROOT, file_sha, ledger
from run_center_propagation_trace import analyze as propagation_counts
from run_dynamic_reverse_ledger_audit import trial_folder
from run_long_budget_bridge import execute, hypervolume, nondominated, objectives, read, rows, verify_frozen, write_once


FROZEN = ROOT / "runs/night-research-H1-20261103-010138-848045"
U = ROOT / "runs/center-entry-cross-20261103-233434-666587"
S = ROOT / "runs/center-reference-followup-20261103-234300-358382"
PROP = ROOT / "runs/center-propagation-20261103-234421-798860"
CELLS = ("SS", "SU", "US", "UU")


def check_recorded_classes(path):
    identities = {}
    for r in read(path)["classes"]:
        location = Path(url2pathname(urlparse(r["codeSource"]).path))
        name = r["name"]
        relative = name.replace(".", "/") + ".class"
        if location.is_dir():
            assert file_sha(location / relative) == r["sha256"], name
        else:
            import zipfile
            from hashlib import sha256
            with zipfile.ZipFile(location) as jar:
                assert sha256(jar.read(relative)).hexdigest() == r["sha256"], name
        identities[name] = r["sha256"]
    return identities


def verify_runtime(root):
    verify_frozen(FROZEN)
    for r in read(ANCHOR / "dependencies.json"):
        if r["kind"] == "jar":
            assert file_sha(Path(r["path"])) == r["sha256"]
    base = check_recorded_classes(trial_folder(ANCHOR, "SPECIAL") / "class-origins.json")
    for label in ("SPECIAL", "UNIFORM"):
        actual = check_recorded_classes(trial_folder(PROP, label) / "class-origins.json")
        changed = [k.rsplit(".", 1)[-1] for k in base if base[k] != actual[k]]
        assert set(changed) == {"LongBudgetRun", "CanonicalHmopso", "CooperationSupport"}
    cp = (S / "classpath.txt").read_text(encoding="utf-8-sig").strip()
    for rel, sha in read(S / "class-hashes.json").items():
        assert file_sha(S / "classes" / rel) == sha
    # Load from the exact reciprocal classpath in a fresh JVM; this is a zero-evaluation check.
    source = root / "CenterClassCheck.java"
    source.write_text("""import java.nio.file.*;
public class CenterClassCheck {
  public static void main(String[] args) throws Exception {
    Path overlay = Paths.get(args[0]).toRealPath(), base = Paths.get(args[1]).toRealPath();
    String p = "org.uma.jmetal.util.research.search.";
    for (String c : new String[] {p+"CenterReferenceProbe",p+"CenterRoleSwapProbe",p+"CenterCrossSearch",p+"LocalSearch","research.dynamic.CenterCrossRun"}) {
      Class<?> k=Class.forName(c,false,CenterClassCheck.class.getClassLoader());
      Path where=Paths.get(k.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
      if (!where.equals(c.endsWith("Probe") ? overlay : base)) throw new AssertionError(c+" "+where);
      System.out.println(c+" "+where);
    }
    System.out.println(System.getProperty("java.runtime.version"));
  }
}
""", encoding="utf-8")
    execute(["java", "-cp", cp, str(source), str(S / "classes"), str(U / "classes")], root / "effective-classpath.log")
    checks = ("org.uma.jmetal.util.research.modelchecks.DynamicCoreChecks", "research.RuntimeChecks",
              "research.dynamic.DynamicRuntimeChecks", "org.uma.jmetal.util.research.runtime.AnytimeChecks")
    for check in checks:
        execute(["java", "-cp", cp, check], root / (check.rsplit(".", 1)[-1] + ".log"))
    return list(checks)


def verify_template(run, entries, rng):
    protocol = read(U / "protocol.json")["normalization"]
    lower, scale = np.asarray(protocol["lower"]), np.asarray(protocol["scale"])
    ledger_reference = (U / "shared-center-ledger.csv").read_bytes()
    assert (run / "shared-center-ledger.csv").read_bytes() == ledger_reference
    assert read(run / "status.json")["status"] == "COMPLETE"
    bank = file_sha(entries[rng] / "rng-slots.bin")
    backgrounds = [rows(folder / "entry.jsonl")[0]["background"] for folder in entries.values()]
    background = nondominated(backgrounds[0] + backgrounds[1])
    results = read(run / "factorial.json")
    for cell in CELLS:
        folder = run / cell
        receipt, = rows(folder / "run-receipt.jsonl")
        check = read(folder / "validation.json")
        actual = ledger(folder)
        limit = END_FE - ENTRY_FE
        assert receipt["attempted"] == receipt["successful"] == receipt["decoder"]["dynamic.evaluations"] == limit
        assert receipt["stopReason"] == "FE_LIMIT" and receipt["failed"] == 0 and receipt["seed"] == 8111009
        assert len(actual) == check["ledgerSlots"] == 1705 and sum(s[4] for s in actual) == limit
        assert check["inputs"]["rngBank"] == bank
        assert all(check["inputs"][key] == file_sha(entries[source] / "entry.bin")
                   for key, source in zip(("entrants", "reference"), cell))
        admitted = rows(folder / "admissions.jsonl")
        endpoints = rows(folder / "endpoints.jsonl")
        assert len(endpoints) == 55
        assert objectives(nondominated([x["objectives"] for x in admitted])) == objectives(
            x["objectives"] for x in rows(folder / "solutions.jsonl"))
        for result in results:
            ref, fe = result["reference"], result["phaseFE"]
            hv = lambda f: float(hypervolume((np.asarray(f) - lower) / scale, (ref,) * 3))
            for kind, cohort, index in (("retained", endpoints, "paid"), ("discoveries", admitted, "FE")):
                pts = np.asarray([x["objectives"] for x in cohort if x[index] <= fe])
                assert math.isclose(hv(np.vstack((background, pts))) - hv(background),
                                    result["gains"][kind][cell], abs_tol=1e-12)
    trace, = rows(run / (rng * 2) / "center-trace.jsonl")
    control, = rows(entries[rng] / "center-trace.jsonl")
    assert trace["paidSHA256"] == control["paidSHA256"]
    return results


def main():
    root = ROOT / "runs" / datetime.now().strftime("center-goal-verification-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    print("CENTER_GOAL_VERIFY_ROOT", root, flush=True)
    checks = verify_runtime(root)
    entries = {k: Path(p) for k, p in read(U / "reused-captures.json").items()}
    u, s = verify_template(U, entries, "U"), verify_template(S, entries, "S")
    direction_pass = all(value > 1e-12 for record in u + s if record["equivalentRunFE"] == END_FE
                         for value in record["effects"]["retained"]["referenceConditional"].values())
    assert direction_pass == read(S / "template-and-blocks.json")["bothTemplatesBothEntrantsRetainedSign"]
    assert not direction_pass
    assert read(PROP / "status.json")["status"] == "COMPLETE"
    for label in ("SPECIAL", "UNIFORM"):
        folder = trial_folder(PROP, label)
        receipt, = rows(folder / "run-receipt.jsonl")
        assert receipt["attempted"] == receipt["successful"] == 447916 and receipt["failed"] == 0
        assert propagation_counts(folder, 447916) == read(PROP / "propagation.json")[label]
        assert archive_admissions(folder) == [a for a in archive_admissions(trial_folder(ANCHOR, label)) if a[0] <= 447916]
    write_once(root / "receipt.json", {
        "status": "VERIFIED", "checks": checks, "templatesRecalculated": 2, "crossedArmsRecalculated": 8,
        "propagationArmsRecalculated": 2, "referenceDirectionGate": direction_pass,
        "newAlgorithmSearchFE": 0, "candidateFrozen": False, "smallScreenStarted": False,
    })
    print("CENTER_GOAL_VERIFY_COMPLETE", root, flush=True)


if __name__ == "__main__":
    main()
