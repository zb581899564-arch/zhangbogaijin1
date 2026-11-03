"""Export a reviewable source delta against preserved original chapter projects."""
import argparse
import difflib
import json
from pathlib import Path
import re

WORKSPACE = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="normalized-v2")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.label):
        parser.error("Label must be a simple directory name")
    output = WORKSPACE / "docs/patches" / args.label
    output.mkdir(exist_ok=False)
    report = []
    for chapter in (3, 4):
        original = next((WORKSPACE.parent / "李明哲-毕业材料").glob(f"{chapter+1}.*代码")) / "jMetal-jmetal-DHHFSP"
        baseline = WORKSPACE / "baselines" / f"chapter{chapter}"
        changed, patch = [], []
        for path in sorted(baseline.rglob("*")):
            if not path.is_file() or "target" in path.parts or path.suffix not in (".java", ".xml"):
                continue
            relative = path.relative_to(baseline)
            source = original / relative
            before = source.read_text(encoding="utf-8").splitlines(keepends=True) if source.exists() else []
            after = path.read_text(encoding="utf-8").splitlines(keepends=True)
            if before != after:
                changed.append(relative.as_posix())
                patch.extend(difflib.unified_diff(before, after,
                             fromfile="original/" + relative.as_posix(), tofile=f"chapter{chapter}/" + relative.as_posix()))
        (output / f"chapter{chapter}.patch").write_text("".join(patch), encoding="utf-8")
        report.append({"chapter":chapter,"original":str(original),"changed":changed})
        print(f"chapter{chapter}: {len(changed)} changed/new source and POM files")
    (output / "manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")


if __name__ == "__main__":
    main()
