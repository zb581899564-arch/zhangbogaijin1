"""Copy source-only chapter baselines without touching the original materials."""
from pathlib import Path
import json
import shutil

WORKSPACE = Path(__file__).resolve().parents[1]
MATERIALS = WORKSPACE.parent / "李明哲-毕业材料"
MODULES = ("jmetal-core", "jmetal-problem", "jmetal-algorithm", "jmetal-exec", "tool")


def copy_chapter(chapter: int) -> dict:
    source = MATERIALS / f"{chapter + 1}.第{'三' if chapter == 3 else '四'}章代码"
    project = source / "jMetal-jmetal-DHHFSP"
    target = WORKSPACE / "baselines" / f"chapter{chapter}"
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite working baseline: {target}")
    target.mkdir(parents=True)
    copied = []
    candidates = [project / "pom.xml", project / "README.md"]
    candidates.extend(project.glob("LICENSE*"))
    for module in MODULES:
        candidates.append(project / module / "pom.xml")
        candidates.extend((project / module / "src").rglob("*.java"))
    for path in candidates:
        if path.is_file():
            relative = path.relative_to(project)
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            copied.append(str(relative).replace("\\", "/"))
    data_dir = WORKSPACE / "data" / f"chapter{chapter}"
    data_dir.mkdir(parents=True, exist_ok=True)
    instances = sorted(p for p in (source / "EADHFSP").glob("*.txt") if not p.name.startswith("._"))
    for instance in instances:
        shutil.copy2(instance, data_dir / instance.name)
    return {"chapter": chapter, "source": str(project), "copy": str(target),
            "copied_files": copied, "instances": [p.name for p in instances],
            "excluded": ["target", "old experiment results", "IDE metadata", "unrelated benchmark resources"]}


def main() -> None:
    manifest = {"date": "2026-10-31", "chapters": [copy_chapter(3), copy_chapter(4)]}
    path = WORKSPACE / "docs" / "baseline_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    for chapter in manifest["chapters"]:
        print(f"Chapter {chapter['chapter']}: {len(chapter['copied_files'])} source files, "
              f"{len(chapter['instances'])} instances")


if __name__ == "__main__":
    main()
