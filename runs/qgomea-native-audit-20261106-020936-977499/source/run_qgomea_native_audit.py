"""Execute unmodified pinned author functions in isolated Julia and compare independent integer mathematics."""
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess

from run_long_budget_bridge import ROOT, read, write_once, controller_lock
from qgomea_reference_math import make_cases, verify_native
from research.semantic_repair.evidence import digest

NATIVE = ROOT / "research/gomea_reference_audit/private-qgomea-native-20261106"


def native_command(root):
    source = NATIVE / "repository/src/approaches/qGOMEA/qGOMEA.jl"
    driver = root / "source/q_native_primitives.jl"
    executable = NATIVE / "runtime/julia-1.3.0/bin/julia.exe"
    return [str(executable), "--startup-file=no", "--history-file=no", "--color=no", str(driver),
            str(source), str(root / "cases.tsv"), str(root / "native-results.tsv"), str(root / "native-lifecycle.tsv")]


def run_native(root):
    command = native_command(root)
    write_once(root / "command.json", command)
    env = os.environ.copy()
    env.update({"JULIA_DEPOT_PATH": str(NATIVE / "depot"), "JULIA_LOAD_PATH": str(NATIVE / "packages") + ";@stdlib",
                "JULIA_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"})
    with (root / "native.log").open("w", encoding="utf-8") as log:
        subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=300, check=True)


def main():
    with controller_lock(ROOT / "research/night_research", "dispatch.lock"):
        root = ROOT / "runs" / datetime.now().strftime("qgomea-native-audit-%Y%m%d-%H%M%S-%f")
        root.mkdir(); source = root / "source"; source.mkdir()
        write_once(root / "protocol.json", {
            "version": "QGOMEA_NATIVE_INTEGER_AND_LIFECYCLE_AUDIT-v1", "registered": "2026-11-06",
            "nativeCommit": "5eda0bad76d1cb109a45d61d40aad5b93c367496", "qBlob": "04de5ea6258a1a7071e08b73c822db1cac6009d2",
            "runtime": "OfficialWindowsJulia1.3.0; StaticArrays0.12.1exactpinnedroot and allselectedfilesverified; projectprivateenvironment",
            "cases": "Allparent/donorpermutations,n2..4,allnonemptymasks/allreferences; n1 plus200 fixedrandom/boundarycases n5/8/20/100.19081total",
            "checks": "Unmodifiednativeposition/order/sequential/inverse versus independent integerformulas; synchronousparents,FOSfilter,FI,eqflag,andrawouterbudgetprobe",
            "rawLimitProbe": "OriginaloptimizeusesunseededMersenneTwister; illustrativeactualcallcount only, not deterministicperformanceclaim",
            "stopping": "Anyunexpected mismatch stops mathematicalacceptance. ActualcanonicalUPGMAmismatch recorded as source-identityboundary, not fixed or hidden. No dynamicsearch/performance arm",
            "newDynamicSearchFE": 0, "dynamicDecoderCalls": 0, "goalAchieved": False})
        for name in (Path(__file__).name, "qgomea_reference_math.py"):
            shutil.copy2(Path(__file__).with_name(name), source / name)
        for path in (ROOT / "src/algorithms/diagnostics/qgomea_reference").glob("*.jl"):
            shutil.copy2(path, source / path.name)
        write_once(root / "source-hashes.json", {p.name: digest(p) for p in source.iterdir()})
        write_once(root / "native-input-hashes.json", {str(p): digest(p) for p in (NATIVE / "repository").rglob("*.jl")})
        print("QGOMEA_NATIVE_AUDIT_ROOT", root, flush=True)
        try:
            cases = make_cases(root / "cases.tsv")
            run_native(root)
            result = verify_native(root / "cases.tsv", root / "native-results.tsv")
            values = dict(line.split("\t", 1) for line in (root / "native-lifecycle.tsv").read_text().splitlines())
            assert values["version"] == "1.3.0" and float(values["activeFOSLargestForN6"]) < 5
            canonical = float(values["UPGMA_actual"]) == float(values["UPGMA_expected"])
            write_once(root / "analysis.json", {**result, "nativeLifecycle": values,
                       "nativePrimitiveMathematicsPassed": True, "nativeCanonicalUPGMAEqualsMathematics": canonical,
                       "qGomeaReadyForPerformance": False, "sourceChanges": 0, "goalAchieved": False})
        except BaseException as error:
            write_once(root / "status.json", {"status": "INCOMPLETE_RETAINED", "error": repr(error),
                                               "newDynamicSearchFE": 0, "dynamicDecoderCalls": 0})
            raise
        write_once(root / "status.json", {"status": "COMPLETE", "cases": cases,
                   "primitiveMathematicsPassed": True, "canonicalUPGMAMatch": canonical,
                   "newDynamicSearchFE": 0, "dynamicDecoderCalls": 0, "goalAchieved": False})
        print("QGOMEA_NATIVE_AUDIT_COMPLETE", root, result, values, flush=True)


if __name__ == "__main__":
    main()
