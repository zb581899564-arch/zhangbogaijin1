"""Replay selectors only on captured paid pools of a complete semantic-repair campaign."""
from datetime import datetime
import argparse
import csv
import json
from pathlib import Path
from statistics import mean
import time

import numpy as np

from research.dynamic_benchmark.metrics import hypervolume
from .selection import crowded_order, cutoff_tie_size, dominance, pddr, truncate


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path, rows):
    with path.open("x", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def unique_count(candidates, selected):
    return len({tuple(tuple(candidates[i][key]) for key in ("JS", "FA", "MA", "WA")) for i in selected})


def extremes(points, indices):
    return int(np.sum(np.min(points[indices], axis=0) == np.min(points, axis=0)))


def local_encoding_count(candidates, selected):
    keys = []
    for i in selected:
        c = candidates[i]
        keys.append(tuple(tuple((job, c["MA"][k], c["WA"][k]) for k, job in enumerate(c["JS"]) if c["FA"][k] == f)
                          for f in range(max(c["FA"]) + 1)))
    return len(set(keys))


def retention_diagnostics(raw, points, scores, candidates, actual, capacity, selector):
    full = hypervolume(points, [1.5]*3)
    kept = hypervolume(points[actual], [1.5]*3)
    unconstrained = sorted(range(len(points)), key=lambda i: scores[i])[:capacity]
    unconstrained_hv = hypervolume(points[unconstrained], [1.5]*3)
    nd = np.flatnonzero(dominance(raw).sum(axis=0) == 0)
    covered = np.all(raw[actual, None, :] <= raw[None, nd, :], axis=2).any(axis=0)
    lineages = {candidates[i]["lineageId"] for i in actual if candidates[i]["lineageId"] >= 0}
    return {"fullPoolHV": full, "selectionHVLossPercent": None if full <= 1e-12 else 100*(full-kept)/full,
            "ND_records": len(nd), "ND_covered_by_selected_fraction": float(covered.mean()),
            "unconstrainedPDDR_HV": unconstrained_hv if selector == "PDDR" else None,
            "removeQuotaPDDR_gainPercent": None if kept <= 1e-12 or selector != "PDDR" else 100*(unconstrained_hv-kept)/kept,
            "selectedLineages": len(lineages) if lineages else None,
            "selectedFactoryLocalEncodings": local_encoding_count(candidates, actual)}


def review(pool, instance, seed, variant, scale):
    candidates = pool["candidates"]
    raw = np.asarray([c["objectives"] for c in candidates])
    points = raw / np.asarray(scale)
    categories = [c["category"] for c in candidates]
    quotas, capacity, actual = pool.get("quotas"), pool["capacity"], pool["selectedIndices"]
    scores = pddr(raw)
    pddr_selected = truncate(sorted(range(len(points)), key=lambda i: scores[i]), capacity, categories, quotas)
    if pool["fitness"] is not None:
        assert np.allclose(scores, pool["fitness"], rtol=0, atol=1e-12)
        assert pddr_selected == actual
    crowd = truncate(crowded_order(raw), capacity, categories, quotas)
    a, b = hypervolume(points[actual], [1.5]*3), hypervolume(points[crowd], [1.5]*3)
    row = {"instance": instance, "seed": seed, "variant": variant, "generation": pool["generation"],
           "selector": pool["selector"], "poolSize": len(points), "capacity": capacity,
           "constrained": quotas is not None, "actualHV": a, "crowdedHV": b,
           "crowdedChangePercent": None if a <= 1e-12 else 100 * (b-a)/a,
           "actualUnique": unique_count(candidates, actual), "crowdedUnique": unique_count(candidates, crowd),
           "poolUnique": unique_count(candidates, list(range(len(points)))),
           "actualExtremes": extremes(points, actual), "crowdedExtremes": extremes(points, crowd),
           "pddrCutoffTieRecords": cutoff_tie_size(scores, pddr_selected, categories, quotas),
           "sameCapacityAndQuotas": True, "scope": "captured paid pool only; not closed-loop effect"}
    row.update(retention_diagnostics(raw, points, scores, candidates, actual, capacity, pool["selector"]))
    return row


def replay(root):
    started = time.monotonic()
    status, protocol = read(root/"final-status.json"), read(root/"protocol.json")
    if status["status"] != "SEMANTIC_REPAIR_COMPLETE":
        raise ValueError("Require all210 complete; never select from a partial campaign")
    cap = read(root/"clock.json")["startedEpoch"] + 5400
    rows, propagation = [], []
    for instance in protocol["instances"]:
        for seed in protocol["algorithm_seeds"]:
            for variant, spec in protocol["variants"].items():
                if time.time() > cap:
                    raise TimeoutError("Original90-minute cap exceeded during pool replay")
                folder = root/"trials"/spec["phase"]/instance["stem"]/str(seed)/variant
                summary = read(folder/"summary.json")
                audit = summary["semanticAudit"]
                propagation.append({"instance": instance["stem"], "seed": seed, "variant": variant,
                                    **{k:v for k,v in audit.items() if k.startswith("sharedOrigins") or k in ("originsCap", "auditSeconds", "poolExportSeconds")}})
                for line in (folder/"semantic-trace.jsonl").read_text(encoding="utf-8").splitlines():
                    pool = json.loads(line)
                    if pool.get("type") == "pool" and pool["deadlineValid"]:
                        rows.append(review(pool, instance["stem"], seed, variant, instance["normalization"]["scale"]))
    output = root / datetime.now().strftime("pool-replay-%Y%m%d-%H%M%S-%f")
    output.mkdir()
    write_csv(output/"pool-comparisons.csv", rows)
    write_csv(output/"shared-propagation.csv", propagation)
    lines = ["# 同一已付费池的选择重放", "", "全部210次结束后的有界快照诊断，新增调度FE=0。",
             "仅捕获前两次与末次池，不能外推全部代。rank+crowding使用相同容量与相同合作类别配额。",
             "一次离线截断更好不证明闭环替换选择器更好；原NSGA-II记录用于核对其无配额选择的HV一致。", "",
             "|版本|有效池数|截断池数|crowding平均HV变化|实际平均唯一数|重放平均唯一数|平均PDDR边界并列记录|",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for variant in protocol["variants"]:
        group = [r for r in rows if r["variant"] == variant]
        values = [r["crowdedChangePercent"] for r in group if r["crowdedChangePercent"] is not None]
        if group:
            change = f"{mean(values):+.3f}%" if values else "未识别"
            lines.append(f"|{variant}|{len(group)}|{sum(r['poolSize']>r['capacity'] for r in group)}|"
                         f"{change}|{mean(r['actualUnique'] for r in group):.2f}|"
                         f"{mean(r['crowdedUnique'] for r in group):.2f}|{mean(r['pddrCutoffTieRecords'] for r in group):.2f}|")
    lines += ["", "上述平均按捕获池展示，不是独立实例效应或显著性结论。原始每实例/seed/代可在CSV中分层。",
              "CSV另含事后探索性全池HV保留、无配额PDDR和谱系/工厂局部编码指标，不改变预定主分析及阈值。",
              "NSGA行的PDDR并列为反事实参考，移除PDDR配额字段不适用而留空；不得解释为其实际选择规则。",
              "共享传播为直接精确基因型的独立事件计数，不是必须嵌套的漏斗；pbest可在代末之前使用共享成果。",
              "teacherConsumed表示实际被更新核读取，不表示改变了子代或带来因果质量收益。", ""]
    (output/"report.md").write_text("\n".join(lines), encoding="utf-8")
    receipt = {"status":"complete", "sourceCampaign":str(root), "newFE":0, "newOptimizerRuns":0,
               "deadlineValidPools":len(rows), "propagationRuns":len(propagation),
               "offlineSeconds":time.monotonic()-started, "campaignElapsedIncludingReplay":time.time()-read(root/"clock.json")["startedEpoch"]}
    with (output/"receipt.json").open("x",encoding="utf-8") as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
    print(output,flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root",type=Path)
    replay(parser.parse_args().root.resolve())
