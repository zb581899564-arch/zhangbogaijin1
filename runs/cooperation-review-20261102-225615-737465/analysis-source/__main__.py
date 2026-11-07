"""Write a new historical review directory; all experiment roots remain read-only."""
import argparse
from datetime import datetime
from pathlib import Path
import shutil
from .composition import review_compositions
from .effects import CAMPAIGNS, historical_effects
from .report import report
from .storage import Sources, csv_write, json_write


def inventory(root):
    return {str(path.relative_to(root)): (stat.st_size, stat.st_mtime_ns)
            for path in root.rglob("*") if path.is_file() for stat in [path.stat()]}


def main():
    project = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve() if args.output else project / "runs" / datetime.now().strftime("cooperation-review-%Y%m%d-%H%M%S-%f")
    runs = (project / "runs").resolve()
    if output.parent != runs or not output.name.startswith("cooperation-review-"):
        raise ValueError("Output must be an independent runs/cooperation-review-* directory")
    roots = [project / "runs" / name for name, _ in CAMPAIGNS]
    before = {root.name: inventory(root) for root in roots}
    sources = Sources()
    for name in ("README.md", "AGENTS.md", "docs/实验比较协议.md", "docs/模型合同.md", "docs/动态模型合同-v1.md", "docs/整厂共享组合的性质与边界.md"):
        sources.text(project / name)
    seeds, instances, overall, propagation = historical_effects(project, sources)
    tables = review_compositions(project, sources)
    unchanged = all(before[root.name] == inventory(root) for root in roots)
    if not unchanged:
        raise ValueError("An historical root changed during review")
    receipt = {"status": "HISTORICAL_REVIEW_COMPLETE", "newSearchFE": 0, "newDecodeFE": 0,
        "optimizerStarted": False, "historicalRootsUnchanged": unchanged,
        "historicalRoots": [root.name for root in roots],
        "historicalRootFileCounts": {name: len(files) for name, files in before.items()},
        "sourceCheck": "bytes and mtime_ns before/after; no content hash assertion",
        "effectAggregation": "five seed candidate/control HV means, then instance effect, six instances equally",
        "independentCampaignReplicatesClaimed": False,
        "samplePolicy": "first16+last16 paid assemblies per run; not random or representative",
        "demandFeedbackGate": "INSUFFICIENT_LOCAL_POOL_AND_OBJECTIVE_EVIDENCE",
        "finalHVAttribution": "NOT_IDENTIFIED", "output": str(output)}
    output.mkdir(exist_ok=False)
    for stem, rows in {"effects-seeds": seeds, "effects-instances": instances,
                       "effects-summary": overall, "propagation-runs": propagation, **tables}.items():
        csv_write(output / (stem + ".csv"), rows)
    csv_write(output / "sources.csv", sources.unchanged())
    json_write(output / "receipt.json", receipt)
    report(output, project, overall, instances, tables, receipt)
    snapshot = output / "analysis-source"
    snapshot.mkdir()
    for path in Path(__file__).parent.glob("*.py"):
        shutil.copy2(path, snapshot / path.name)
    print(output)


if __name__ == "__main__":
    main()
