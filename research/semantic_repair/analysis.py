"""All-seven-version offline reference and immutable descriptive result artifacts."""
from datetime import datetime
import csv
import numpy as np

from research.dynamic_benchmark.metrics import hypervolume, igd_plus, nondominated
from .evidence import read, write_once
from .metrics import comparisons
from .protocol import PHASES, REFERENCES, jobs, trial_folder
from .trials import load_trial


def csv_write(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _load_runs(root, protocol, deadline):
    instances = {row["stem"]: row for row in protocol["instances"]}
    runs = []
    for phase in PHASES:
        for job in jobs(protocol, phase):
            if deadline:
                deadline.require()
            folder = trial_folder(root, job)
            runs.append(load_trial(folder, instances[job["instance"]], job["seed"],
                                   job["variant"], protocol["variants"][job["variant"]]))
    if len(runs) != protocol["runs"]:
        raise ValueError("All210 cells are required for the predeclared reference")
    return runs


def cost_row(run):
    summary = run["summary"]
    audit, decoder = summary["semanticAudit"], summary.get("decoder", {})
    row = {key: run[key] for key in ("instance", "seed", "variant")}
    row.update({"attempted": summary["attempted"], "successful": summary["successful"],
                "deadlineValidFE": run["finalRow"]["fe"], "halfTimeFE": run["halfRow"]["fe"],
                "searchSeconds": summary["searchSeconds"],
                "overshootSeconds": summary["deadlineOvershootSeconds"],
                "interruptedAttempts": summary["timeInterruptedAttempts"],
                "archiveSize": summary["archiveSize"],
                "offlineValidationDecodes": summary["offlineValidationDecodes"],
                "fixedFEReached": run["fe"] is not None,
                "decodeSeconds": decoder.get("dynamic.decodeNanos", 0) / 1e9,
                "semanticProfile": summary["semanticProfile"], "classicSetting": summary["classicSetting"],
                "cooperationSeconds": summary.get("cooperation", {}).get("cooperationSeconds", 0),
                "poolExportSeconds": summary.get("poolExportSeconds", audit.get("poolExportSeconds", 0)),
                "processWallSeconds": (run.get("execution") or {}).get("processWallSeconds"),
                "controllerValidationSeconds": (run.get("execution") or {}).get("controllerValidationSeconds"),
                "traceRows": run["traceSummary"]["rows"],
                "deadlineValidPools": run["traceSummary"]["deadlineValidPools"],
                "deadlineInvalidPools": run["traceSummary"]["deadlineInvalidPools"]})
    for key, value in audit.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            row["semanticAudit." + key] = value
    paid, different = audit.get("globalSampledPaid", 0), audit.get("globalSampledDifferent", 0)
    row["sampledDifferentFraction"] = different / paid if paid else None
    seconds = summary["searchSeconds"]
    row["auditFractionOfSearch"] = audit.get("auditSeconds", 0) / seconds if seconds else None
    return row


def _records(runs, reference_fronts, deadline):
    records, costs = [], []
    for run in runs:
        if deadline:
            deadline.require()
        record = {key: run[key] for key in ("instance", "seed", "variant")}
        record.update({"hv": {str(point): hypervolume(run["final"], [point] * 3) for point in REFERENCES},
                       "igdplus": igd_plus(run["final"], reference_fronts[run["instance"]]),
                       "hv_half": hypervolume(run["half"], [1.5] * 3),
                       "hv_fe15000": None if run["fe"] is None else hypervolume(run["fe"], [1.5] * 3)})
        records.append(record)
        cost = cost_row(run)
        cost.update({"HV_" + key: value for key, value in record["hv"].items()})
        cost.update({"IGDplus": record["igdplus"], "HV_half": record["hv_half"],
                     "HV_FE15000": record["hv_fe15000"]})
        for point in REFERENCES:
            cost["outside_" + str(point)] = int(np.any(run["final"] >= point, axis=1).sum())
        costs.append(cost)
    return records, costs


def _report(output, result, audit):
    rows = ["# 基线语义修复：同期210次受限诊断", "",
            "SO为事前固定修正基线；NSGA2_CONTROL固定setting0。六开发实例各五seed，seed是实例内重复。", "",
            "仅报告修复、组织和共享效应；未调用旧270次判灯器，不构成正式扩量资格或论文优势结论。", "",
            "|比较|平均HV效应%|中位%|实质胜/负|最差%|去最佳实例平均%|", "|---|---:|---:|---:|---:|---:|"]
    for label, item in result["comparisons"].items():
        metric = item["final"]["1.5"]
        fields = [metric[key] for key in ("mean_effect_percent", "median_effect_percent")]
        fields += [str(metric["practical_wins"]) + "/" + str(metric["practical_losses"])]
        fields += [metric[key] for key in ("worst_effect_percent", "mean_after_removing_best_instance_percent")]
        values = ["未定" if value is None else f"{value:.4f}" if isinstance(value, float) else str(value)
                  for value in fields]
        rows.append("|" + label + "|" + "|".join(values) + "|")
    inter = result["factorial_interactions"]["1.5"]
    rows.extend(["", "交互为每实例/seed的HV_SO−HV_S−HV_O+HV_V2；百分比使用同一V2分母。",
                 "实例交互平均百分比：" + str(inter["mean_interaction_percent"]) + "。", "",
                 "IGD+经验参考为本轮每实例全部7版本×5seed的T点有效ND并集，仅供离线指标，不进入搜索。",
                 "FE15000仅诊断，未达点保持删失；complete_pairs_only表限于两方各5seed均达点的实例。",
                 "实质胜要求实例均值≥1%且至少3/5配对seed同向；没有p值门槛。",
                 "95%探索性区间按实例重采样；不能视为新实例泛化证据。", "",
                 "全部实际费用、导出QA与删失见audit.json/run-metrics.csv；诊断unique origin计数只表示直接传播使用，不能解释为后代因果贡献。",
                 "auditSeconds为搜索内有界记录费用并计入T；poolExportSeconds为搜索后物化编码/JSON费用，单列且计入campaign总时限。",
                 "有效运行：" + str(audit["runs"]) + "；达到FE15000：" + str(audit["fixedFEReached"]) + "。", ""])
    with (output / "report.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(rows))


def analyze(root, deadline=None):
    protocol = read(root / "protocol.json")
    # Full matrix validation happens before creating any result directory.
    runs = _load_runs(root, protocol, deadline)
    output = root / "analysis" / datetime.now().strftime("analysis-%Y%m%d-%H%M%S-%f")
    output.mkdir(parents=True, exist_ok=False)
    references = {}
    for instance in protocol["instances"]:
        if deadline:
            deadline.require()
        stem = instance["stem"]
        references[stem] = nondominated(np.concatenate([run["final"] for run in runs if run["instance"] == stem]))
        write_once(output / (stem + "-reference.json"), references[stem].tolist())
    records, costs = _records(runs, references, deadline)
    write_once(output / "records.json", records)
    csv_write(output / "run-metrics.csv", costs)
    result = comparisons(records, protocol)
    write_once(output / "effects.json", result)
    semantic = [{key: run[key] for key in ("instance", "seed", "variant")}
                | {"semanticAudit": run["summary"]["semanticAudit"],
                   "traceTypes": run["traceSummary"]["types"]}
                for run in runs]
    write_once(output / "semantic-audit.json", semantic)
    audit = {"status": "passed", "runs": len(runs), "expected": protocol["runs"],
             "genuineFailures": 0, "attempted": sum(row["attempted"] for row in costs),
             "successful": sum(row["successful"] for row in costs),
             "timeInterruptedAttempts": sum(row["interruptedAttempts"] for row in costs),
             "offlineValidationDecodes": sum(row["offlineValidationDecodes"] for row in costs),
             "poolExportSeconds": sum(row["poolExportSeconds"] for row in costs),
             "processWallSecondsKnown": sum(row["processWallSeconds"] for row in costs if row["processWallSeconds"] is not None),
             "missingProcessWallReceipts": sum(row["processWallSeconds"] is None for row in costs),
             "controllerValidationSecondsKnown": sum(row["controllerValidationSeconds"] for row in costs if row["controllerValidationSeconds"] is not None),
             "maxOvershootSeconds": max(row["overshootSeconds"] for row in costs),
             "fixedFEReached": sum(row["fixedFEReached"] for row in costs),
             "scope": "Correctness and descriptive development results; no traffic light or scale-up authorization"}
    if deadline:
        deadline.require()
        audit.update({"campaignWallSeconds": deadline.elapsed(), "campaignRemainingSeconds": deadline.remaining()})
    write_once(output / "audit.json", audit)
    _report(output, result, audit)
    print("SEMANTIC_ANALYSIS", output, flush=True)
    return output
