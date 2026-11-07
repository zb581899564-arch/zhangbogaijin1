"""Readable complete-method tables from a finished screen; no search or new decisions."""
import argparse
import csv
from statistics import mean, stdev

from research.dynamic_benchmark.io import csv_write
from .execution import read, write
from ._metrics import compare


def _load(root):
    if read(root / "final-status.json")["status"] != "SCREEN_COMPLETE":
        raise ValueError("Require a complete screen")
    source = root / "analysis" / "initial"
    policy = read(root / "protocol.json")
    records = read(source / "records.json")
    decision = read(source / "decision.json")
    instances = [item["stem"] for item in policy["instances"]]
    seeds, variants = policy["algorithm_seeds"], policy["variants"]
    index = {(r["instance"], r["seed"], r["variant"]): r for r in records}
    expected = {(i, s, v) for i in instances for s in seeds for v in variants}
    if len(records) != len(index) or set(index) != expected:
        raise ValueError("Incomplete or duplicate record matrix")
    external = decision["external_selection"]["selected"]
    with (source / "run-metrics.csv").open(encoding="utf-8-sig", newline="") as stream:
        costs = list(csv.DictReader(stream))
    return source, instances, seeds, variants, index, external, costs


def _variant_summary(index, variant, external, instances, seeds, costs):
    comparisons = {name: compare(index, variant, comparator, instances, seeds)
                   for name, comparator in [("baseline", "BASELINE"), ("external", external)]}
    fe = compare(index, variant, external, instances, seeds, field="hv_fe15000", available_only=True)
    half = compare(index, variant, external, instances, seeds, field="hv_half")
    cost = [row for row in costs if row["variant"] == variant]
    paid = sum(int(row["successful"]) for row in cost)
    seconds = sum(float(row["searchSeconds"]) for row in cost)
    row = {"variant": variant, "successfulFE": paid, "searchSeconds": seconds,
           "successfulFEPerSecond": paid / seconds,
           "FE15000_complete_pairs": fe["complete_pair_instances"],
           "FE15000_vs_C_mean_percent": fe["mean_effect_percent"],
           "FE15000_vs_C_median_percent": fe["median_effect_percent"],
           "halfTime_vs_C_mean_percent": half["mean_effect_percent"],
           "halfTime_vs_C_median_percent": half["median_effect_percent"]}
    for name, comparison in comparisons.items():
        for key in ["mean_effect_percent", "median_effect_percent", "practical_wins", "practical_losses"]:
            row[name + "_" + key] = comparison[key]
    return row


def _instance_mean(index, instance, variant, seeds):
    cells = [index[instance, seed, variant] for seed in seeds]
    values = [cell["hv"]["1.5"] for cell in cells]
    return {"instance": instance, "variant": variant, "seeds": len(cells),
            "meanHV": mean(values), "sdHV": stdev(values),
            "meanIGDplus": mean(cell["igdplus"] for cell in cells),
            "meanHV_reference125": mean(cell["hv"]["1.25"] for cell in cells),
            "meanHV_reference2": mean(cell["hv"]["2.0"] for cell in cells)}


def _markdown(summaries, means, instances, variants, external):
    lines = ["# 九版本完整比较", "", "本表由已结束的270次主轮记录派生，未重跑或重判标准。",
             "先取每实例5 seed均值，再汇总6实例的相对变化；HV参考点1.5。C*=" + external + "。",
             "实质胜/负按冻结的1%与至少3/5 seed同向规则。", "",
             "|版本|对A0平均|对A0中位数|对A0实质胜/负|对C*平均|对C*中位数|成功FE/s|",
             "|---|---:|---:|---|---:|---:|---:|"]
    for row in summaries:
        lines.append(f"|{row['variant']}|{row['baseline_mean_effect_percent']:+.3f}%|"
                     f"{row['baseline_median_effect_percent']:+.3f}%|"
                     f"{row['baseline_practical_wins']}/{row['baseline_practical_losses']}|"
                     f"{row['external_mean_effect_percent']:+.3f}%|"
                     f"{row['external_median_effect_percent']:+.3f}%|{row['successfulFEPerSecond']:.1f}|")
    lines += ["", "## 各实例HV均值", "", "|实例|" + "|".join(variants) + "|",
              "|---|" + "|".join(["---:"] * len(variants)) + "|"]
    for instance in instances:
        values = [next(row["meanHV"] for row in means if row["instance"] == instance and row["variant"] == variant)
                  for variant in variants]
        lines.append("|" + instance + "|" + "|".join(f"{value:.6f}" for value in values) + "|")
    lines += ["", "全部均值、标准差和敏感性数据见instance-means.csv；同FE及半程诊断见variant-summary.csv。",
              "成功FE/s为各方法总成功FE除以总搜索时间，不解释为质量或机制的因果效应。",
              "脚本仅做事后表格导出，搜索源码版本及冻结判定器保持不变。", ""]
    return "\n".join(lines)


def summarize(root):
    source, instances, seeds, variants, index, external, costs = _load(root)
    summaries = [_variant_summary(index, v, external, instances, seeds, costs) for v in variants]
    means = [_instance_mean(index, i, v, seeds) for v in variants for i in instances]
    output = source / "supplement"
    output.mkdir()  # Preserve any previous postprocessing evidence.
    csv_write(output / "variant-summary.csv", summaries)
    csv_write(output / "instance-means.csv", means)
    markdown = _markdown(summaries, means, instances, variants, external)
    (output / "method-matrix.md").write_text(markdown, encoding="utf-8")
    write(output / "receipt.json", {"status": "complete", "records": len(index),
          "variantRows": len(summaries), "instanceRows": len(means), "lockedExternal": external,
          "source": "analysis/initial/records.json", "newEvaluations": 0, "decisionChanged": False}, once=True)
    return output


if __name__ == "__main__":
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    print(summarize(parser.parse_args().root.resolve()))
