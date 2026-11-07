"""Linux-only independent post-local probe audit; numpy and the standard library only."""
import argparse
import json
from pathlib import Path
import platform
import time

from audit_campaign import engineering, science
from audit_core import read_json, require
from audit_inputs import verify_input
from audit_receipt import check_receipt
from audit_replay import Replay


def audit_one(folder, input_directory, cache):
    catalog = read_json(folder / "catalog.json")
    require(len(catalog["tuples"]) == len({tuple(v) for v in catalog["tuples"]}), "Catalog tuple IDs alias")
    key = str(input_directory), json.dumps(catalog, sort_keys=True)
    if key not in cache:
        cache[key] = verify_input(input_directory, catalog)
    replay = Replay(folder, catalog, cache[key]).run()
    result = check_receipt(replay)
    result["instance"] = cache[key]["metadata"]["instance"]
    result["label"] = folder.name
    return result


def campaign(args):
    plan, cache, rows, sections = read_json(args.root / "protocol.json"), {}, [], {}
    stages = ("engineering", "science") if args.stage == "all" else (args.stage,)
    for stage in stages:
        stage_rows = []
        for path in sorted((args.root / stage).glob("*/*/*/receipt.json")):
            folder = path.parent
            stem, seed = folder.parent.parent.name, folder.parent.name
            result = audit_one(folder, args.input / stem / seed, cache)
            result["stage"] = stage
            stage_rows.append(result)
            print("POSTLOCAL_AUDIT_RUN", stage, stem, seed, folder.name, result["successfulFE"], flush=True)
        checker = engineering if stage == "engineering" else science
        sections[stage] = checker(args.root, plan, stage_rows)
        rows.extend(stage_rows)
    if args.stage == "all":
        require(sum(row["attemptedFE"] for row in rows) == plan["totalPlannedAttemptedFE"],
                "Campaign total attempted FE differs from frozen protocol")
    return dict(passed=True, stages=sections, trajectories=rows, inputContexts=len(cache),
                newSearchFE=0, newDecoderCalls=0, performanceProved=False,
                physicalObjectivesIndependentlyDecoded=False,
                scope="Engineering and causal evidence only; no quality or innovation conclusion")


def main():
    require(platform.system() == "Linux", "Run evidence replay/audit only on Linux; Windows is edit-only")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--stage", choices=("engineering", "science", "all"), default="all")
    parser.add_argument("--run", type=Path, help="Audit one preserved trajectory; --input is its direct input directory")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    args.input = args.input or args.root / "inputs"
    started = time.perf_counter()
    result = audit_one(args.run, args.input, {}) if args.run else campaign(args)
    result["offlineSeconds"] = time.perf_counter() - started
    output = args.output
    if output is None and not args.run:
        prefix = "independent-final-audit" if args.stage == "all" else args.stage + "-independent-audit"
        output = args.root / (prefix + ".json")
    if output:
        with output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps(dict(passed=True, output=str(output) if output else None,
                          offlineSeconds=result["offlineSeconds"], newSearchFE=0, newDecoderCalls=0)), flush=True)


if __name__ == "__main__":
    main()
