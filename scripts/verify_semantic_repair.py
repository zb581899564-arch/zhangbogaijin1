"""Bounded engineering acceptance of S/O and actual new entrypoints; no quality-based selection."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

import psutil

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def run(build, folder, stem, spec, fe=20000, seconds="Infinity", frozen=False):
    previous = ROOT / "runs/expansion-screen-20261102-001934-525927"
    inputs = previous / "inputs" / stem
    folder.mkdir(parents=True)
    cp = ((previous if frozen else build) / "classpath.txt").read_text(encoding="utf-8")
    command = ["java", "-Xms32m", "-Xmx768m", "-cp", cp, "research.dynamic.DynamicRun",
               str(inputs / (stem + ".txt")), str(inputs / "RECONSTRUCTED-setup.txt"),
               str(inputs / "fatigue-input.txt"), str(folder), spec["mode"], str(fe),
               "4242421", str(seconds), "1.0", "true", "false", "0", "true", "SCREEN", "0"]
    if not frozen:
        command += [spec["profile"], "true"]
    (folder / "command.json").write_text(json.dumps(command, ensure_ascii=False), encoding="utf-8")
    peak = 0
    with (folder / "run.log").open("x", encoding="utf-8") as stream:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        started = time.monotonic()
        while process.poll() is None:
            if time.monotonic() - started > 180:
                process.kill(); process.wait(); raise TimeoutError("Owned engineering JVM timeout; evidence preserved")
            try:
                peak = max(peak, psutil.Process(process.pid).memory_info().rss)
            except psutil.NoSuchProcess:
                pass
            time.sleep(.05)
    if process.returncode:
        raise RuntimeError((folder / "run.log").read_text(encoding="utf-8", errors="replace")[-3000:])
    summary = read(folder / "summary.json")
    assert summary["status"] == "passed" and summary["failed"] == summary["timeInterruptedAttempts"]
    assert summary["archiveSize"] == summary["offlineValidationDecodes"]
    if seconds == "Infinity":
        assert summary["attempted"] == summary["successful"] == fe
    if not frozen:
        from research.semantic_repair.diagnostics import validate_trace
        trace = [json.loads(line) for line in (folder / "semantic-trace.jsonl").read_text(encoding="utf-8").splitlines()]
        validate_trace(trace, summary["semanticAudit"], summary)
        validate_pool_scores(trace)
    return {"instance": stem, "mode": spec["mode"], "profile": spec["profile"], "FE": summary["successful"],
            "seconds": seconds, "peakRssBytes": peak, "archiveReplay": summary["offlineValidationDecodes"]}


def validate_pool_scores(trace):
    import numpy as np
    for row in trace[1:]:
        if row["selector"] != "PDDR":
            continue
        points = np.asarray([c["objectives"] for c in row["candidates"]])
        dominates = np.all(points[:, None, :] <= points[None, :, :], axis=2) & np.any(points[:, None, :] < points[None, :, :], axis=2)
        scores = dominates.sum(axis=0) + 1 / (dominates.sum(axis=1) + 1)
        assert np.allclose(scores, row["fitness"], rtol=0, atol=1e-12)
        order = sorted(range(len(points)), key=lambda i: scores[i])
        if row["quotas"] is not None:
            used, chosen = [0] * 5, []
            for index in order:
                category = row["candidates"][index]["category"]
                if used[category] < row["quotas"][category]:
                    used[category] += 1; chosen.append(index)
            order = chosen
        assert order[:row["capacity"]] == row["selectedIndices"]


def verify(build):
    from research.semantic_repair.protocol import VARIANTS
    build = Path(build).resolve()
    result, fingerprints = [], []
    for label in ["V2", "S_ONLY", "O_ONLY", "SO", "NSGA2_CONTROL"]:
        folder = build / "initialization" / label
        result.append(run(build, folder, "20_2_3_1", VARIANTS[label], fe=100))
        fingerprints.append((folder / "solutions.jsonl").read_bytes())
    assert all(value == fingerprints[0] for value in fingerprints)
    print("COMMON_INITIALIZATION_ARCHIVE_PASS", flush=True)
    for stem in ["20_2_3_1", "200_8_5_1"]:
        for label, spec in VARIANTS.items():
            folder = build / "integration" / stem / label
            result.append(run(build, folder, stem, spec))
            summary = read(folder / "summary.json")
            if spec["profile"] in ["S", "SO"]:
                trace = [json.loads(line) for line in (folder / "semantic-trace.jsonl").read_text().splitlines()]
                assert len(trace) > 1 and all(len(row["candidates"]) == 200 for row in trace[1:])
            if label in ["V2", "NSGA2_CONTROL"]:
                old = build / "legacy-control" / stem / label
                run(build, old, stem, spec, frozen=True)
                assert (old / "solutions.jsonl").read_bytes() == (folder / "solutions.jsonl").read_bytes()
            print("SEMANTIC_REAL_FE_PASS", stem, label, flush=True)
    for label, spec in VARIANTS.items():
        result.append(run(build, build / "time-interruption" / label, "20_2_3_1", spec,
                          fe=9223372036854775807, seconds=.3))
    manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for source in [ROOT / "src/java", ROOT / "src/algorithms"] for p in source.rglob("*.java")}
    (build / "source-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    acceptance = {"status": "passed", "scope": "semantic-repair engineering; no quality selection",
                  "finished": datetime.now().isoformat(), "realEntryChecks": result,
                  "v2AndNSGAArchivesMatchFrozenAtFE20000": True,
                  "commonInitializationArchive": "five free modes at100FE identical; not all paid individual vectors exported",
                  "allCapturedPDDRScoresAndIndicesReplayed": True,
                  "checks": ["SelectionSemanticsChecks", "ResourceSemanticsChecks", "SemanticAuditChecks", "RuntimeChecks", "AnytimeChecks", "SearchChecks4"],
                  "unifiedDiagnostics": True, "parametersSelectedByQuality": False}
    (build / "acceptance.json").write_text(json.dumps(acceptance, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SEMANTIC_ENGINEERING_ACCEPTED", build, flush=True)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    verify(sys.argv[1])
