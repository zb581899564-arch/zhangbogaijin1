"""Resolve expected class bytes from the declared ordered classpath, not an older harness."""
import hashlib
import os
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile

from research.semantic_repair.evidence import digest


def resolve_class(classpath, name):
    resource = name.replace(".", "/") + ".class"
    for raw in classpath.split(os.pathsep):
        entry = Path(raw)
        if entry.is_dir():
            candidate = entry / resource
            if candidate.is_file():
                return {"entry": str(entry.resolve()), "classFile": str(candidate.resolve()), "sha256": digest(candidate)}
        elif entry.is_file() and entry.suffix.lower() in (".jar", ".zip"):
            with ZipFile(entry) as archive:
                if resource in archive.namelist():
                    return {"entry": str(entry.resolve()), "resource": resource,
                            "sha256": hashlib.sha256(archive.read(resource)).hexdigest()}
    raise FileNotFoundError("Class missing from frozen classpath: " + name)


def file_url(value):
    parsed = urlsplit(value)
    if parsed.scheme != "file": raise ValueError("Not a local class source: " + value)
    path = unquote(parsed.path)
    if os.name == "nt" and len(path) > 2 and path[0] == "/" and path[2] == ":": path = path[1:]
    return Path(path).resolve()


def verify_capture(capture, classpath):
    checked = {}
    for name, actual in capture.items():
        if not isinstance(actual, dict) or "sha256" not in actual: continue
        expected = resolve_class(classpath, name)
        if actual["sha256"] != expected["sha256"]:
            raise ValueError("Loaded class bytes differ from declared classpath: " + name)
        if file_url(actual["codeSource"]) != Path(expected["entry"]).resolve():
            raise ValueError("Loaded class source differs from declared classpath: " + name)
        checked[name] = expected
    if not checked: raise ValueError("No recorded classes")
    return checked
