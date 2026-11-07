"""Immutable offline H1/H2 and closed-loop descriptive development evidence."""
import csv
from datetime import datetime
import json
from pathlib import Path

import numpy as np

from research.dynamic_benchmark.metrics import hypervolume, igd_plus, nondominated
from research.expansion_screen._metrics import compare
from research.semantic_repair.evidence import read, write_once
from research.semantic_repair.trials import checkpoint, json_lines, normalized_front
from .kernel_metrics import (KERNELS, case_metrics, paired_contrasts, summarize_contrasts,
                             summarize_kernels, validate_pairing)
from .retention import (batch_metrics, encoding, generation_metrics, objective, retention_gate,
                        summarize, validate_generations)


def _require(deadline):
    if deadline is not None:
        deadline.require()


def _csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
                         for key, value in row.items()} for row in rows)


def _phases(protocol):
    phases = protocol.get("analysis_phases", protocol.get("enabled_phases", list(protocol["phases"])))
    if not phases or any(phase not in protocol["phases"] for phase in phases):
        raise ValueError("No complete registered analysis phases")
    return list(phases)


def _load_trial(folder, instance, seed, variant, spec):
    summary = read(folder / "summary.json")
    if summary["status"] != "passed" or summary["seed"] != seed:
        raise ValueError("Failed trial or changed seed")
    if summary["attempted"] != summary["successful"] + summary["failed"]:
        raise ValueError("Broken paid FE accounting")
    if summary["failed"] != summary["timeInterruptedAttempts"]:
        raise ValueError("Genuine evaluation failures remain unresolved")
    for key, target in (("mode", "mode"), ("profile", "semanticProfile")):
        if key in spec and summary[target] != spec[key]:
            raise ValueError("Trial differs from frozen mode/profile")
    seconds = instance["time_seconds"]
    if summary["stopReason"] != "TIME_LIMIT" or abs(summary["timeLimitSeconds"] - seconds) > 1e-9:
        raise ValueError("Trial changed its registered time budget")
    rows = json_lines(folder / "anytime.jsonl")
    if len(rows) != 3:
        raise ValueError("Expected exactly half/T/FE15000 checkpoints")
    final, half, fe = checkpoint(rows, "TIME", seconds), checkpoint(rows, "TIME", seconds / 2), checkpoint(rows, "FE", 15000)
    if fe.get("reached", True) and fe["fe"] != 15000:
        raise ValueError("Fixed-FE checkpoint contains future evaluations")
    lower, scale = (np.asarray(instance["normalization"][key], dtype=float) for key in ("lower", "scale"))
    fronts = {"final": normalized_front(final, seconds, lower, scale, required=True),
              "half": normalized_front(half, seconds / 2, lower, scale, required=True),
              "fe": normalized_front(fe, seconds, lower, scale)}
    solutions = json_lines(folder / "solutions.jsonl")
    if len(solutions) != summary["archiveSize"] or len(solutions) != summary["offlineValidationDecodes"]:
        raise ValueError("Returned archive did not complete offline replay/export")
    for solution in solutions:
        objective(solution)
        encoding(solution)
    trace = json_lines(folder / "mechanism-trace.jsonl")
    generations = validate_generations(trace, seconds)
    if not generations:
        raise ValueError("No complete mechanism generation was captured")
    return {"instance": instance["stem"], "seed": seed, "variant": variant, "summary": summary,
            **fronts, "trace": trace, "generations": generations,
            "finalRow": final, "halfRow": half, "feRow": fe,
            "execution": read(folder / "execution.json") if (folder / "execution.json").exists() else {}}


def _load_runs(root, protocol, deadline):
    runs = []
    for phase in _phases(protocol):
        for instance in protocol["instances"]:
            for seed in protocol["algorithm_seeds"]:
                for variant in protocol["phases"][phase]:
                    _require(deadline)
                    folder = root / "trials" / phase / instance["stem"] / str(seed) / variant
                    runs.append(_load_trial(folder, instance, seed, variant, protocol["variants"][variant]))
    cells = {(row["instance"], row["seed"], row["variant"]) for row in runs}
    if len(cells) != len(runs):
        raise ValueError("Duplicated registered trial cell")
    return runs


def _retention(runs, instances, reference, deadline):
    rows, batches, expected_cases = [], [], set()
    for run in runs:
        _require(deadline)
        identity = {key: run[key] for key in ("instance", "seed", "variant")}
        normalization = instances[run["instance"]]["normalization"]
        for generation in run["generations"]:
            rows.append(identity | generation_metrics(generation, normalization, reference))
            batches.extend(identity | row for row in batch_metrics(generation, normalization, reference))
        for case in run["trace"]:
            if case.get("type") == "kernel-case":
                expected_cases.add((run["instance"], case.get("origin", run["variant"]), case["phase"], case["caseId"]))
    return rows, batches, expected_cases


def _kernels(root, protocol, instances, reference, expected_cases):
    path = root / "kernel-results.jsonl"
    if not path.exists():
        return {"status": "NOT_AVAILABLE", "scope": "No kernel result file; no H2 claim"}, [], [], [], [], []
    records = json_lines(path)
    snapshots = {tuple(row[key] for key in ('instance', 'origin', 'phase', 'caseId')): row
                 for row in json_lines(root / 'case-snapshots.jsonl')}
    records = [{**snapshots[tuple(row[key] for key in ('instance', 'origin', 'phase', 'caseId'))], **row}
               for row in records]
    replicates = protocol.get("kernel_replicates", protocol.get("kernel", {}).get("replicates"))
    if replicates is None:
        raise ValueError("Kernel replicate count/list was not frozen")
    groups = validate_pairing(records, replicates, protocol.get("kernel_names", KERNELS),
                              expected_cases if expected_cases else None)
    rows, batches = [], []
    from .retention import normalize
    for identity, group in groups.items():
        archive = nondominated(normalize(group[0]['reference'], instances[identity[0]]['normalization']))
        prepared = (archive, hypervolume(archive, reference))
        rows.extend(case_metrics(row, instances[row['instance']]['normalization'], reference, prepared)
                    for row in group)
        for name in protocol['kernel_names']:
            paid = [row for row in group if row['kernel'] == name]
            children = [row['child'] for row in paid]
            trial = paid[0] | {'children': children,
                              'generationNanos': sum(row['generationNanos'] for row in paid),
                              'evaluationNanos': sum(row['evaluationNanos'] for row in paid)}
            batch = case_metrics(trial, instances[identity[0]]['normalization'], reference, prepared)
            batches.append({key: batch[key] for key in ('instance', 'origin', 'phase', 'caseId', 'kernel',
                             'referenceHV', 'paidBatchSize', 'batchDeltaHV', 'generationEvaluationSeconds')})
    pairs = paired_contrasts(rows)
    return ({"status": "COMPLETE_MATCHED_MATRIX", "cases": len(groups), "evaluations": len(rows),
             "replicates": replicates, "scope": "Matched snapshots; GLOBAL principal, PERSONAL auxiliary"},
            rows, summarize_kernels(rows), pairs, summarize_contrasts(pairs), batches)


def _metrics(runs, protocol, reference):
    references = {instance["stem"]: nondominated(np.concatenate(
        [run["final"] for run in runs if run["instance"] == instance["stem"]])) for instance in protocol["instances"]}
    rows, costs = [], []
    for run in runs:
        record = {key: run[key] for key in ("instance", "seed", "variant")}
        record.update({"hv": {str(point): hypervolume(run["final"], [point] * 3) for point in (1.25, 1.5, 2.)},
                       "igdplus": igd_plus(run["final"], references[run["instance"]]),
                       "hv_half": hypervolume(run["half"], reference),
                       "hv_fe15000": hypervolume(run["fe"], reference) if run["fe"] is not None else None})
        rows.append(record)
        cost = {key: run[key] for key in ("instance", "seed", "variant")}
        for key, value in run["summary"].items():
            if isinstance(value, dict):
                cost.update({key + "." + inner: item for inner, item in value.items()
                             if isinstance(item, (int, float, str, bool)) or item is None})
            elif isinstance(value, (int, float, str, bool)) or value is None:
                cost["summary." + key] = value
        cost.update({"execution." + key: value for key, value in run["execution"].items()
                     if isinstance(value, (int, float, str, bool)) or value is None})
        cost.update({"HV_1.5": record["hv"]["1.5"], "IGDplus": record["igdplus"],
                     "HV_half": record["hv_half"], "HV_FE15000": record["hv_fe15000"]})
        costs.append(cost)
    return rows, costs, references


def _comparisons(records, protocol):
    index = {(row["instance"], row["seed"], row["variant"]): row for row in records}
    labels = {row["variant"] for row in records}
    seeds, instances = protocol["algorithm_seeds"], [row["stem"] for row in protocol["instances"]]
    candidates = (("SO", "NSGA"), ("SHARE", "NSGA"), ("SHARE", "SO"),
                  ("SO_PARENT", "SO"), ("SHARE_PARENT", "SHARE"),
                  ("SO_PARENT", "NSGA"), ("SHARE_PARENT", "NSGA"))
    output = {}
    for candidate, control in candidates:
        if candidate not in labels or control not in labels:
            continue
        common = (index, candidate, control, instances, seeds)
        output[candidate + "__vs__" + control] = {
            "T": {str(point): compare(*common, str(point), win_seeds=len(seeds) // 2 + 1) for point in (1.25, 1.5, 2.)},
            "halfTime": compare(*common, field="hv_half", win_seeds=len(seeds) // 2 + 1),
            "FE15000": {"allInstances": compare(*common, field="hv_fe15000", win_seeds=len(seeds) // 2 + 1),
                        "completePairsOnly": compare(*common, field="hv_fe15000", available_only=True,
                                                      win_seeds=len(seeds) // 2 + 1)}}
    return output


def _report(output, audit, gate, comparisons, kernel_status):
    lines = ["# 有界搜索机制验证：开发证据", "",
             "H1分开衡量代初P在G/L形成前的精英丢失、G/L池内保留及实际闭环结果。",
             "P∪G∪L相对G∪L的HV增量仅为离线oracle，不表示PARENT闭环收益。", "",
             f"完整运行 {audit['runs']}；有效完整代快照 {audit['validGenerationSnapshots']}；"
             f"排除partial快照 {audit['partialGenerationSnapshots']}。", "",
             "分支gate：" + gate["status"] + "，triggered=" + str(gate["triggered"]) + "。", "",
             "|比较|同T平均HV变化%|同FE15000平均HV变化%|", "|---|---:|---:|"]
    for label, result in comparisons.items():
        time = result["T"]["1.5"]["mean_effect_percent"]
        fe = result["FE15000"]["allInstances"]["mean_effect_percent"]
        values = ["未识别" if value is None else f"{value:.4f}" for value in (time, fe)]
        lines.append("|" + label + "|" + "|".join(values) + "|")
    lines.extend(["", "H2：" + kernel_status["status"] + "。按instance/origin/phase及相同case×rep配对。",
                  "四核使用相同父本/引导/固定reference；CLASSIC_GLOBAL为主普通控制，CLASSIC_PERSONAL为辅助。",
                  "NSGA快照的personal为parentA自身，global为真实parentB；自交辅助与真实第二亲控制分别解释。",
                  "candidate与paid-batch增量分开；生成及评价费用单列。不能以不同闭环轨迹的入档率推断核的固有因果。", "",
                  "global direction×step的HV趋势为同代固定P下的观察，不能跨不同父本轨迹作因果结论。",
                  "IGD+参考为本次已登记分析阶段全部方法/seed的截止有效T档案ND并集；近似、离线且不反馈搜索。",
                  "若父代分支未触发，应依controller分支回执记SKIPPED，而非缺失实验。",
                  "本报告不评判ESWA资格，不判定整框架方向死亡，也不将离线oracle当闭环效果。", ""])
    with (output / "report.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))


def analyse(root, protocol, deadline=None):
    root = Path(root)
    instances = {row["stem"]: row for row in protocol["instances"]}
    reference = protocol.get("metrics", {}).get("primary_reference", [1.5] * 3)
    runs = _load_runs(root, protocol, deadline)
    h1, batches, cases = _retention(runs, instances, reference, deadline)
    gate = retention_gate(h1, protocol["instances"])
    kernel_status, kernels, kernel_summary, pairs, pair_summary, kernel_batches = _kernels(root, protocol, instances, reference, cases)
    metrics, costs, references = _metrics(runs, protocol, reference)
    comparisons = _comparisons(metrics, protocol)
    audit = {"status": "COMPLETE_REGISTERED_PHASES", "runs": len(runs), "analysisPhases": _phases(protocol),
             "validGenerationSnapshots": len(h1),
             "partialGenerationSnapshots": sum(row.get("type") == "generation" and row.get("complete") is False
                                                for run in runs for row in run["trace"]),
             "deadlineInvalidGenerationSnapshots": sum(not row["deadlineValid"] for run in runs for row in run["generations"]),
             "kernel": kernel_status, "fixedFEReached": sum(run["fe"] is not None for run in runs),
             "offlineAnalysisExtraFE": 0, "scope": "Bounded development evidence, no publication or scale-up verdict"}
    _require(deadline)
    output = root / "analysis" / datetime.now().strftime("analysis-%Y%m%d-%H%M%S-%f")
    output.mkdir(parents=True, exist_ok=False)
    for name, rows in (("retention-generations", h1), ("global-batch-trends", batches),
                       ("kernel-metrics", kernels), ("kernel-summary", kernel_summary),
                       ("kernel-pairs", pairs), ("kernel-pair-summary", pair_summary), ("run-metrics", costs)):
        _csv(output / (name + ".csv"), rows)
    _csv(output / 'kernel-paid-batches.csv', kernel_batches)
    for name, value in (("audit", audit), ("retention-gate", gate), ("records", metrics),
                        ("closedloop-effects", comparisons), ("kernel-status", kernel_status),
                        ("retention-run-summary", summarize(h1, ("instance", "seed", "variant"))),
                        ("analysis-inputs", {"phases": _phases(protocol), "referencePoint": reference,
                                             "kernelCasesObserved": len(cases), "normalizations": {
                                                 name: spec["normalization"] for name, spec in instances.items()}})):
        write_once(output / (name + ".json"), value)
    for instance, front in references.items():
        write_once(output / (instance + "-reference.json"), front.tolist())
    _report(output, audit, gate, comparisons, kernel_status)
    return output


def analyze(root, protocol=None, deadline=None):
    return analyse(root, read(Path(root) / "protocol.json") if protocol is None else protocol, deadline)
