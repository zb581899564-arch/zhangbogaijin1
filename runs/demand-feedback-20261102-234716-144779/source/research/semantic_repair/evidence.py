"""Immutable JSON, durable progress events, and frozen source/binary/input evidence."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import os
import shutil
import time

from .protocol import ROOT, PREVIOUS, make_protocol


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_once(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def status(root, value):
    """Events are authoritative; Windows status readers cannot lose progress."""
    value = {"eventEpoch": time.time(), **value}
    events = root / "status-events"
    events.mkdir(exist_ok=True)
    tag = str(time.time_ns()) + "-" + str(os.getpid())
    write_once(events / (tag + ".json"), value)
    temporary = root / ("status-" + tag + ".pending")
    write_once(temporary, value)
    for attempt in range(10):
        try:
            temporary.replace(root / "status.json")
            return
        except PermissionError:
            if attempt < 9:
                time.sleep(.02)
    # The unique event has already committed. A locked convenience projection
    # must not turn a successful optimizer run into an abandoned owner.
    print("STATUS_PROJECTION_LOCKED see", events, flush=True)
    try:
        temporary.unlink()
    except PermissionError:
        pass


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def manifest_tree(root, folders):
    return {str(path.relative_to(root)): digest(path)
            for folder in folders for path in sorted((root / folder).rglob("*"))
            if path.is_file()}


def _freeze_classpath(engineering, root):
    classpath = (engineering / "classpath.txt").read_text(encoding="utf-8-sig").strip()
    targets, sources = [], []
    (root / "binary").mkdir()
    for index, item in enumerate(classpath.split(os.pathsep)):
        source = Path(item)
        if not source.is_absolute():
            source = engineering / source
        source = source.resolve()
        if not source.exists():
            raise FileNotFoundError(source)
        target = root / "binary" / ("cp-" + str(index) + (source.suffix if source.is_file() else ""))
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
        targets.append(str(target.resolve()))
        sources.append({"source": str(source), "frozen": str(target.relative_to(root))})
    if not targets:
        raise ValueError("Empty engineering classpath")
    (root / "classpath.txt").write_text(os.pathsep.join(targets), encoding="utf-8")
    write_once(root / "classpath-sources.json", sources)


def _freeze_sources(root):
    paths = [p for folder in (ROOT / "src/java", ROOT / "src/algorithms") for p in folder.rglob("*.java")]
    for folder in ("semantic_repair", "dynamic_benchmark", "expansion_screen"):
        paths.extend((ROOT / "research" / folder).glob("*.py"))
    manifest = {}
    for path in sorted(set(paths)):
        relative = path.relative_to(ROOT)
        target = root / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        manifest[str(relative)] = digest(target)
    write_once(root / "source-manifest.json", manifest)


def _accepted_sources(engineering):
    path = engineering / "source-manifest.json"
    if not path.exists():
        raise ValueError("Engineering acceptance must include source-manifest.json")
    manifest = read(path)
    if not manifest or not isinstance(manifest, dict):
        raise ValueError("Engineering source manifest must map repository-relative paths to SHA256")
    for name, expected in manifest.items():
        candidate = (ROOT / name).resolve()
        if not candidate.is_relative_to(ROOT) or digest(candidate) != expected:
            raise ValueError("Source changed after engineering acceptance: " + name)
    return manifest


def prepare(engineering):
    engineering = Path(engineering).resolve()
    acceptance = read(engineering / "acceptance.json")
    if acceptance.get("status") != "passed":
        raise ValueError("Semantic engineering acceptance is not passed")
    accepted_sources = _accepted_sources(engineering)
    root = ROOT / "runs" / datetime.now().strftime("semantic-repair-%Y%m%d-%H%M%S-%f")
    root.mkdir()
    started = time.time()
    write_once(root / "clock.json", {"startedEpoch": started, "wallCapSeconds": 5400})
    previous = read(PREVIOUS / "protocol.json")
    protocol = make_protocol(previous)
    write_once(root / "protocol.json", protocol)
    write_once(root / "historical-input-protocol.json", previous)
    write_once(root / "engineering-acceptance.json", acceptance)
    write_once(root / "engineering-source-manifest.json", accepted_sources)
    for row in protocol["instances"]:
        source = PREVIOUS / "inputs" / row["stem"]
        shutil.copytree(source, root / "inputs" / row["stem"])
    _freeze_classpath(engineering, root)
    _freeze_sources(root)
    manifest = manifest_tree(root, ("binary", "inputs", "source"))
    for name in ("clock.json", "protocol.json", "historical-input-protocol.json", "classpath.txt",
                 "engineering-acceptance.json", "engineering-source-manifest.json"):
        manifest[name] = digest(root / name)
    write_once(root / "frozen-artifacts.json", manifest)
    status(root, {"status": "PREPARED", "completed": 0, "expected": 210,
                  "engineering": str(engineering), "startedEpoch": started})
    return root


def verify_frozen(root):
    """Resume always runs frozen binaries and refuses mutated scientific inputs."""
    for name, expected in read(root / "frozen-artifacts.json").items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or digest(path) != expected:
            raise ValueError("Frozen evidence changed: " + name)
    # Python resumes from its installed package, so verify those executable
    # modules against the archived controller and metric implementation too.
    for name, expected in read(root / "source-manifest.json").items():
        if name.endswith(".py") and digest(ROOT / name) != expected:
            raise ValueError("Python source changed; use the frozen controller: " + name)
