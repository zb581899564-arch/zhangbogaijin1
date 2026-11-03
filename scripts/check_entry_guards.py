"""Check missing-data rejection, ESWA eligibility and disabled historical entry points."""
from datetime import datetime
import json
import subprocess
import sys
from baseline_build import WORKSPACE, build


def main() -> None:
    output = WORKSPACE / "runs" / datetime.now().strftime("entry-guards-%Y%m%d-%H%M%S-%f")
    output.mkdir()
    runner = str(WORKSPACE / "scripts/run_baseline.py")
    common = [sys.executable, runner, "--chapter", "4", "--fe", "1", "--standby-power", "1", "--skip-build"]
    cases = [
        ("missing-setup", common, "requires --setup-file", False),
        ("eq8-rejection", common + ["--instance", "100_2_4_1.txt", "--reconstruct-setup-seed", "314159"], "violates ESWA Eq(8)", False),
        ("eq8-explicit-diagnostic", common + ["--instance", "100_2_4_1.txt", "--reconstruct-setup-seed", "314159",
                                              "--diagnostic-model-exception"], "NORMALIZED_RUN_PASS", True),
    ]
    classpath = build(4, output, skip_maven=True)
    cases.append(("legacy-batch-disabled", ["java", "-cp", classpath,
                                            "org.uma.jmetal.runner.lc_psode.ALLAlgorithmRun"],
                  "legacy batch bypasses", False))
    for name, command, expected, success in cases:
        result = subprocess.run(command, cwd=WORKSPACE, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=60)
        log = result.stdout + result.stderr
        (output / f"{name}.log").write_text(log, encoding="utf-8")
        if (result.returncode == 0) != success or expected not in log:
            raise AssertionError(f"Unexpected guard behavior: {output / (name + '.log')}")
        print("PASS", name)
    (output / "status.json").write_text(json.dumps({"status":"passed","guards":len(cases)}, indent=2), encoding="utf-8")
    print("Artifacts:", output)


if __name__ == "__main__":
    main()
