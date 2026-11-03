"""Correct demonstrably stale job-count headers in copied data only."""
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]


def main() -> None:
    changes = []
    for path in sorted((WORKSPACE / "data").glob("chapter*/*.txt")):
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        jobs, stages, factories, _ = map(int, path.stem.split("_"))
        actual = list(map(int, lines[0].split()))
        expected = [factories, stages, jobs]
        if actual == expected:
            continue
        stripped = [line.strip() for line in lines]
        start = stripped.index("standom processing time of each job at each stage:") + 1
        stop = stripped.index("number of workers in each factory:")
        rows = [line for line in stripped[start:stop] if line]
        if actual[:2] != expected[:2] or len(rows) != jobs or any(len(row.split(",")) != stages for row in rows):
            raise ValueError(f"Cannot justify header correction: {path}")
        changes.append({"file": str(path.relative_to(WORKSPACE)), "old": actual,
                        "new": expected, "verified_processing_rows": len(rows),
                        "scope": "header only; numeric processing/resource rows unchanged"})
        lines[0] = f"{factories} {stages} {jobs}\n"
        path.write_text("".join(lines), encoding="utf-8", newline="")
    report = WORKSPACE / "docs" / "data_header_repairs.json"
    if changes:
        report.write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Corrected {len(changes)} copied instance headers; original materials untouched")


if __name__ == "__main__":
    main()
